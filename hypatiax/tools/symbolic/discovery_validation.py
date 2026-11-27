"""Scientific validation gates for physics-informed symbolic discovery.

The validator only enforces assumptions explicitly present in DiscoveryProblem.
It never infers units, positivity, symmetry, or physical laws from variable names.
"""
from __future__ import annotations

import itertools
import math
from typing import Any, Mapping

from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression

from .discovery_contracts import (
    CandidateRecord,
    ConstraintOutcome,
    ConstraintSpec,
    DiscoveryProblem,
)


class CandidateValidationError(ValueError):
    """Raised when a discovery problem cannot be validated safely."""


class CandidateValidator:
    """Normalize and gate one expression against a declared scientific problem.

    Hard failures make a candidate ineligible. A hard constraint that cannot be
    evaluated is recorded as unknown and also blocks eligibility; callers must
    not silently treat missing scientific evidence as a pass.
    """

    BUILTIN_SYMBOLIC_ID = "builtin.symbolic_validity"
    BUILTIN_DIMENSIONAL_ID = "builtin.dimensional_consistency"
    BUILTIN_DOMAIN_ID = "builtin.declared_domain"

    def __init__(self, *, sample_limit: int = 512, tolerance: float = 1e-9):
        if sample_limit < 1:
            raise ValueError("sample_limit must be >= 1")
        if not math.isfinite(tolerance) or tolerance < 0:
            raise ValueError("tolerance must be finite and >= 0")
        self.sample_limit = sample_limit
        self.tolerance = tolerance

    def validate(
        self,
        problem: DiscoveryProblem,
        expression: str,
        *,
        source: str = "pysr_search",
        search_strategy: str = "default",
        seed: int | None = None,
        candidate_variable_names: list[str] | tuple[str, ...] | None = None,
        feature_substitutions: Mapping[str, str] | None = None,
    ) -> CandidateRecord:
        """Parse and validate a candidate; no training or far target data accepted."""
        if not isinstance(problem, DiscoveryProblem):
            raise TypeError("problem must be a DiscoveryProblem")
        outcomes: list[ConstraintOutcome] = []
        rejection_reasons: list[str] = []
        normalized = expression.strip() if isinstance(expression, str) else ""

        try:
            import sympy as sp

            expression_names = tuple(
                candidate_variable_names or problem.variable_names
            )
            from hypatiax.core.constants import PHYSICAL_CONSTANTS
            parsed = parse_sympy_expression(
                normalized, list(expression_names), constants=PHYSICAL_CONSTANTS
            )
            if parsed is None or parsed.has(sp.zoo, sp.nan, sp.oo, -sp.oo):
                raise ValueError("expression contains a non-finite symbolic value")
            substitutions = dict(feature_substitutions or {})
            unknown_substitutions = set(substitutions) - set(expression_names)
            if unknown_substitutions:
                raise ValueError(
                    f"feature substitutions contain undeclared symbols: {sorted(unknown_substitutions)}"
                )
            if substitutions:
                replacements = {}
                for feature_name, raw_expression in substitutions.items():
                    replacements[sp.Symbol(feature_name, real=True)] = (
                        parse_sympy_expression(
                            raw_expression,
                            list(problem.variable_names),
                            constants=PHYSICAL_CONSTANTS,
                        )
                    )
                parsed = parsed.xreplace(replacements)
                if parsed.free_symbols - {
                    sp.Symbol(name, real=True) for name in problem.variable_names
                }:
                    raise ValueError("expanded expression still contains undeclared symbols")
                normalized = sp.sstr(parsed)
                if len(normalized) > 20000:
                    raise ValueError("expanded physical expression is too long")
            outcomes.append(ConstraintOutcome(
                self.BUILTIN_SYMBOLIC_ID, "pass", "hard",
                "Expression parsed with the restricted mathematical grammar",
                {"free_variables": sorted(str(item) for item in parsed.free_symbols)},
            ))
        except Exception as exc:
            reason = f"symbolic validation failed: {exc}"
            outcomes.append(ConstraintOutcome(
                self.BUILTIN_SYMBOLIC_ID, "fail", "hard", reason
            ))
            rejection_reasons.append(reason)
            return self._record(
                normalized, source, search_strategy, seed, outcomes, rejection_reasons
            )

        self._check_dimensions(problem, normalized, outcomes, rejection_reasons)
        self._check_declared_domain(problem, parsed, outcomes, rejection_reasons)

        eligible = not rejection_reasons and all(
            outcome.status in {"pass", "not_applicable"}
            or outcome.severity == "soft"
            for outcome in outcomes
        )
        return self._record(
            normalized, source, search_strategy, seed, outcomes, rejection_reasons,
            eligible=eligible,
        )

    @staticmethod
    def _record(
        expression: str,
        source: str,
        strategy: str,
        seed: int | None,
        outcomes: list[ConstraintOutcome],
        reasons: list[str],
        *,
        eligible: bool = False,
    ) -> CandidateRecord:
        return CandidateRecord(
            expression=expression or "<invalid>",
            normalized_expression=expression or "<invalid>",
            source=source,
            search_strategy=strategy,
            seed=42 if seed is None else int(seed),
            constraint_outcomes=tuple(outcomes),
            rejection_reasons=tuple(reasons),
            eligible=eligible,
        )

    def _check_dimensions(
        self,
        problem: DiscoveryProblem,
        expression: str,
        outcomes: list[ConstraintOutcome],
        reasons: list[str],
    ) -> None:
        if not problem.variable_units and not problem.target_unit:
            outcomes.append(ConstraintOutcome(
                self.BUILTIN_DIMENSIONAL_ID, "not_applicable", "hard",
                "No units were declared; dimensional consistency was not inferred",
            ))
            return
        if not problem.variable_units:
            reason = "target_unit is declared but variable_units are missing"
            outcomes.append(ConstraintOutcome(
                self.BUILTIN_DIMENSIONAL_ID, "unknown", "hard", reason
            ))
            reasons.append(reason)
            return
        try:
            from pint import UnitRegistry
            from hypatiax.tools.validation.dimensional_validator import DimensionalValidator

            registry = UnitRegistry()
            for name, unit in problem.variable_units.items():
                registry.parse_units(unit or "dimensionless")
            if problem.target_unit:
                expected = registry.parse_units(problem.target_unit)

            report = DimensionalValidator(max_history=0).validate(
                expression,
                dict(problem.variable_units),
                variable_bounds=self._bounds_for_dimensional_validator(problem),
            )
            if not report.get("valid", False):
                reason = "; ".join(report.get("errors", [])) or "dimensional validator rejected expression"
                outcomes.append(ConstraintOutcome(
                    self.BUILTIN_DIMENSIONAL_ID, "fail", "hard", reason,
                    {"errors": report.get("errors", []), "warnings": report.get("warnings", [])},
                ))
                reasons.append(reason)
                return

            inferred = report.get("inferred_output_unit")
            if problem.target_unit and not inferred:
                reason = "dimensional validator did not infer an output unit"
                outcomes.append(ConstraintOutcome(
                    self.BUILTIN_DIMENSIONAL_ID, "unknown", "hard", reason
                ))
                reasons.append(reason)
                return
            if problem.target_unit and inferred:
                actual = registry.parse_units(inferred)
                if not actual.dimensionality == expected.dimensionality:
                    reason = (
                        f"output dimensions {actual.dimensionality} do not match "
                        f"target dimensions {expected.dimensionality}"
                    )
                    outcomes.append(ConstraintOutcome(
                        self.BUILTIN_DIMENSIONAL_ID, "fail", "hard", reason,
                        {"inferred_output_unit": inferred, "target_unit": problem.target_unit},
                    ))
                    reasons.append(reason)
                    return
            outcomes.append(ConstraintOutcome(
                self.BUILTIN_DIMENSIONAL_ID, "pass", "hard",
                "Expression is dimensionally consistent with declared units",
                {"inferred_output_unit": inferred, "target_unit": problem.target_unit},
            ))
        except Exception as exc:
            reason = f"dimensional validation unavailable or inconclusive: {exc}"
            outcomes.append(ConstraintOutcome(
                self.BUILTIN_DIMENSIONAL_ID, "unknown", "hard", reason
            ))
            reasons.append(reason)

    @staticmethod
    def _bounds_for_dimensional_validator(
        problem: DiscoveryProblem,
    ) -> dict[str, tuple[float, float]]:
        bounds: dict[str, tuple[float, float]] = {}
        for name, spec in problem.variable_domains.items():
            if "minimum" in spec and "maximum" in spec:
                bounds[name] = (float(spec["minimum"]), float(spec["maximum"]))
        return bounds

    def _check_declared_domain(
        self,
        problem: DiscoveryProblem,
        expression: Any,
        outcomes: list[ConstraintOutcome],
        reasons: list[str],
    ) -> None:
        if not problem.constraints:
            outcomes.append(ConstraintOutcome(
                self.BUILTIN_DOMAIN_ID, "not_applicable", "hard",
                "No domain constraints were declared; no domain assumptions were inferred",
            ))
            return

        for spec in problem.constraints:
            if spec.kind == "dimensional_consistency":
                dimensional = next(
                    (item for item in outcomes if item.constraint_id == self.BUILTIN_DIMENSIONAL_ID),
                    None,
                )
                if dimensional is None or dimensional.status != "pass":
                    reason = "declared dimensional constraint lacks a passing unit check"
                    outcomes.append(ConstraintOutcome(
                        spec.constraint_id, "unknown", spec.severity, reason,
                        {"builtin_status": dimensional.status if dimensional else "missing"},
                    ))
                    if spec.severity == "hard":
                        reasons.append(f"{spec.constraint_id}: {reason}")
                else:
                    outcomes.append(ConstraintOutcome(
                        spec.constraint_id, "pass", spec.severity,
                        "declared dimensional constraint satisfied by shared unit analysis",
                    ))
                continue
            try:
                status, reason, evidence = self._evaluate_constraint(problem, expression, spec)
            except Exception as exc:
                status, reason, evidence = (
                    "unknown", f"constraint evaluation failed: {exc}", {}
                )
            outcomes.append(ConstraintOutcome(
                spec.constraint_id, status, spec.severity, reason, evidence
            ))
            if spec.severity == "hard" and status in {"fail", "unknown", "not_checked"}:
                reasons.append(f"{spec.constraint_id}: {reason}")

    def _evaluate_constraint(
        self,
        problem: DiscoveryProblem,
        expression: Any,
        spec: ConstraintSpec,
    ) -> tuple[str, str, Mapping[str, Any]]:
        """Evaluate an explicit symbolic or sampled-domain constraint.

        Symbolic requirements are exact AST checks. Numerical checks are
        deterministic screening only; they are not continuous-domain proofs
        and never consume held-out or far-OOD target observations.
        """
        import sympy as sp

        kind = spec.kind
        params = dict(spec.parameters or {})
        free_names = {str(symbol) for symbol in expression.free_symbols}
        function_nodes = [
            node for node in sp.preorder_traversal(expression)
            if isinstance(node, sp.Function)
        ]
        function_names = {node.func.__name__.lower() for node in function_nodes}

        if kind == "required_variables":
            required = tuple(params.get("variables", problem.variable_names))
            if not required or any(name not in problem.variable_names for name in required):
                return "unknown", "required_variables must name declared input variables", {}
            missing = sorted(set(required) - free_names)
            evidence = {
                "required_variables": list(required),
                "present_variables": sorted(set(required) & free_names),
                "missing_variables": missing,
            }
            return (
                ("fail", f"candidate is missing required input variable(s): {missing}", evidence)
                if missing else
                ("pass", "candidate includes every required input variable", evidence)
            )

        if kind == "required_functions":
            required = {str(name).lower() for name in params.get("functions", ())}
            if not required:
                return "unknown", "required_functions needs a non-empty functions list", {}
            missing = sorted(required - function_names)
            evidence = {"required_functions": sorted(required), "observed_functions": sorted(function_names)}
            return (
                ("fail", f"candidate omits required function(s): {missing}", evidence)
                if missing else
                ("pass", "candidate contains all required function families", evidence)
            )

        if kind == "forbidden_functions":
            forbidden = {str(name).lower() for name in params.get("functions", ())}
            if not forbidden:
                return "unknown", "forbidden_functions needs a non-empty functions list", {}
            observed = sorted(forbidden & function_names)
            evidence = {"forbidden_functions": sorted(forbidden), "observed_forbidden_functions": observed}
            return (
                ("fail", f"candidate uses forbidden function(s): {observed}", evidence)
                if observed else
                ("pass", "candidate avoids all forbidden function families", evidence)
            )

        if kind == "variable_in_denominator":
            variable = params.get("variable")
            if variable not in problem.variable_names:
                return "unknown", "variable_in_denominator requires a declared variable", {}
            denominator = sp.denom(sp.together(expression))
            present = str(variable) in {str(symbol) for symbol in denominator.free_symbols}
            evidence = {
                "variable": variable,
                "denominator": sp.sstr(denominator),
                "variable_present_in_denominator": present,
            }
            return (
                ("pass", f"candidate denominator depends on {variable}", evidence)
                if present else
                ("fail", f"candidate denominator does not depend on {variable}", evidence)
            )

        if kind == "no_variable_exponents":
            offenders = [
                sp.sstr(node) for node in sp.preorder_traversal(expression)
                if isinstance(node, sp.Pow) and bool(node.exp.free_symbols)
            ]
            evidence = {"variable_exponent_count": len(offenders), "offending_powers": offenders[:20]}
            return (
                ("fail", "candidate contains variable-dependent exponent(s)", evidence)
                if offenders else
                ("pass", "all candidate exponents are constant", evidence)
            )

        if kind == "required_power":
            variable = params.get("variable")
            exponent = params.get("exponent")
            if variable not in problem.variable_names or isinstance(exponent, bool):
                return "unknown", "required_power needs a declared variable and numeric exponent", {}
            try:
                expected = float(exponent)
            except (TypeError, ValueError, OverflowError):
                return "unknown", "required_power exponent must be finite", {}
            if not math.isfinite(expected):
                return "unknown", "required_power exponent must be finite", {}
            exponent_tolerance = float(params.get("tolerance", 1e-12))
            if not math.isfinite(exponent_tolerance) or exponent_tolerance < 0:
                return "unknown", "required_power tolerance must be finite and non-negative", {}
            expanded_for_power_check = sp.expand(expression, deep=False)
            variable_powers = [
                node for node in sp.preorder_traversal(expanded_for_power_check)
                if isinstance(node, sp.Pow) and str(node.base) == str(variable)
            ]
            if math.isclose(expected, 1.0, rel_tol=0.0, abs_tol=1e-12):
                matches = (
                    [str(variable)] if variable in free_names and all(
                        node.exp.is_number
                        and math.isclose(float(node.exp), 1.0, rel_tol=0.0, abs_tol=1e-12)
                        for node in variable_powers
                    ) else []
                )
            else:
                matches = []
                for node in sp.preorder_traversal(expanded_for_power_check):
                    if not isinstance(node, sp.Pow) or not node.exp.is_number:
                        continue
                    if str(node.base) == str(variable):
                        effective_exponent = float(node.exp)
                    elif expected < 0.0 and str(variable) in {
                        str(symbol) for symbol in node.base.free_symbols
                    }:
                        try:
                            degree = sp.degree(
                                node.base, sp.Symbol(str(variable), real=True)
                            )
                            if degree in (sp.S.NegativeInfinity, sp.S.ComplexInfinity):
                                continue
                            effective_exponent = float(node.exp) * float(degree)
                        except Exception:
                            continue
                    else:
                        continue
                    if math.isclose(
                        effective_exponent, expected,
                        rel_tol=0.0, abs_tol=exponent_tolerance,
                    ):
                        matches.append(sp.sstr(node))
            evidence = {
                "variable": variable, "required_exponent": expected,
                "exponent_tolerance": exponent_tolerance,
                "matching_powers": matches,
            }
            return (
                ("fail", f"candidate does not contain {variable}**{expected:g}", evidence)
                if not matches else
                ("pass", f"candidate contains the required {variable} power", evidence)
            )

        if kind == "no_nested_functions":
            selected = {str(name).lower() for name in params.get("functions", ())}
            nested = []
            for node in function_nodes:
                name = node.func.__name__.lower()
                if name not in selected:
                    continue
                if any(
                    isinstance(child, sp.Function)
                    and child.func.__name__.lower() in selected
                    for arg in node.args for child in sp.preorder_traversal(arg)
                ):
                    nested.append(sp.sstr(node))
            evidence = {"functions_checked": sorted(selected), "nested_function_calls": nested[:20]}
            return (
                ("fail", "candidate contains nested use of a restricted function", evidence)
                if nested else
                ("pass", "candidate has no nested restricted-function calls", evidence)
            )

        if kind == "required_inverse_inside_function":
            variable = params.get("variable")
            function_name = str(params.get("function", "")).lower()
            if variable not in problem.variable_names or not function_name:
                return "unknown", "required_inverse_inside_function needs a declared variable and function", {}
            matches = []
            for node in function_nodes:
                if node.func.__name__.lower() != function_name:
                    continue
                if any(
                    isinstance(child, sp.Pow)
                    and child.exp.is_number
                    and float(child.exp) < 0.0
                    and str(variable) in {str(symbol) for symbol in child.base.free_symbols}
                    for arg in node.args for child in sp.preorder_traversal(arg)
                ):
                    matches.append(sp.sstr(node))
            evidence = {
                "function": function_name, "variable": variable,
                "matching_function_calls": matches,
            }
            return (
                ("fail", f"{function_name} argument must depend on reciprocal {variable}", evidence)
                if not matches else
                ("pass", f"{function_name} contains the required reciprocal dependence", evidence)
            )

        if kind not in {
            "positive_output", "nonnegative_output", "finite_output",
            "finite_output_screen", "positive_output_screen", "nonpositive_output_screen", "even_in", "odd_in", "reciprocal_even_in", "monotone_concave_in",
        }:
            return "unknown", f"unsupported declared constraint kind: {kind}", {}

        if not all(
            name in problem.variable_domains
            and "minimum" in problem.variable_domains[name]
            and "maximum" in problem.variable_domains[name]
            for name in problem.variable_names
        ):
            return "unknown", "complete finite variable bounds are required for sampling", {}

        bounds = {}
        axes = []
        for name in problem.variable_names:
            spec_bounds = problem.variable_domains[name]
            low, high = float(spec_bounds["minimum"]), float(spec_bounds["maximum"])
            if not math.isfinite(low) or not math.isfinite(high) or low > high:
                return "unknown", f"invalid finite bounds for variable {name}", {}
            bounds[name] = (low, high)
            if kind == "finite_output_screen":
                axis = tuple(low + (high - low) * i / 4.0 for i in range(5))
            else:
                axis = (low, (low + high) / 2.0, high)
            axes.append(axis)
        points = list(itertools.product(*axes))
        if len(points) > self.sample_limit:
            stride = max(1, math.ceil(len(points) / self.sample_limit))
            points = points[::stride][:self.sample_limit]

        symbols = {name: sp.Symbol(name, real=True) for name in problem.variable_names}
        fn = sp.lambdify(
            [symbols[name] for name in problem.variable_names],
            expression, modules=[{"sign": lambda value: (value > 0) - (value < 0)}, "math"],
        )

        if kind == "monotone_concave_in":
            variable = params.get("variable")
            if variable not in problem.variable_names:
                return "unknown", "monotone_concave_in requires a declared variable", {}
            index = problem.variable_names.index(variable)
            low, high = bounds[variable]
            other_midpoints = [(lo + hi) / 2.0 for lo, hi in bounds.values()]
            samples = [low + (high - low) * i / 8.0 for i in range(9)]
            values = []
            for value in samples:
                point = list(other_midpoints)
                point[index] = value
                try:
                    values.append(float(fn(*point)))
                except Exception:
                    values.append(float("nan"))
            finite_values = all(math.isfinite(value) for value in values)
            scale = max(1.0, *(abs(value) for value in values if math.isfinite(value)))
            differences = [right - left for left, right in zip(values, values[1:])]
            second_differences = [
                right - 2.0 * middle + left
                for left, middle, right in zip(values, values[1:], values[2:])
            ]
            monotone = finite_values and all(
                difference >= -self.tolerance * scale for difference in differences
            )
            concave = finite_values and all(
                difference <= self.tolerance * scale for difference in second_differences
            )
            passed = monotone and concave
            violations = (
                sum(difference < -self.tolerance * scale for difference in differences)
                + sum(difference > self.tolerance * scale for difference in second_differences)
                + (0 if finite_values else sum(not math.isfinite(value) for value in values))
            )
            evidence = {
                "variable": variable,
                "sample_count": len(values),
                "finite": finite_values,
                "monotone_non_decreasing": monotone,
                "concave_down": concave,
                "first_differences": differences,
                "second_differences": second_differences,
                "violation_count": int(violations),
                "sampling": "deterministic_9_point_training_domain_screen",
                "proof_scope": "finite_sample_shape_screening_only",
                "grid_is_exhaustive": False,
            }
            return (
                ("pass", "candidate passed sampled monotone-concave shape screen", evidence)
                if passed else
                ("fail", "candidate violates sampled monotone-concave shape requirements", evidence)
            )

        if kind == "reciprocal_even_in":
            variable = params.get("variable")
            if variable not in problem.variable_names:
                return "unknown", "reciprocal_even_in requires a declared variable", {}
            low, high = bounds[variable]
            if low <= 0 or high <= 0 or low > 1.0 or high < 1.0:
                return "unknown", "reciprocal symmetry requires a positive domain containing 1", {}
            index = problem.variable_names.index(variable)
            other_midpoints = [(lo + hi) / 2.0 for lo, hi in bounds.values()]
            samples = [low + (high - low) * i / 8.0 for i in range(9)]
            comparisons = []
            for value in samples:
                reciprocal = 1.0 / value
                if reciprocal < low - self.tolerance or reciprocal > high + self.tolerance:
                    continue
                point = list(other_midpoints)
                mirrored = list(other_midpoints)
                point[index] = value
                mirrored[index] = reciprocal
                try:
                    left, right = float(fn(*point)), float(fn(*mirrored))
                except Exception:
                    left = right = float("nan")
                comparisons.append(
                    math.isfinite(left) and math.isfinite(right)
                    and abs(left - right) <= self.tolerance * max(1.0, abs(left), abs(right))
                )
            if not comparisons:
                return "unknown", "no reciprocal pairs were available inside the declared domain", {}
            violations = sum(not item for item in comparisons)
            evidence = {
                "variable": variable, "sample_count": len(comparisons),
                "violation_count": violations,
                "violation_fraction": violations / len(comparisons),
                "sampling": "deterministic_reciprocal_pairs_inside_training_domain",
                "proof_scope": "finite_sample_screening_only",
                "grid_is_exhaustive": False,
            }
            return (
                ("fail", "candidate violates declared reciprocal symmetry on training-domain samples", evidence)
                if violations else
                ("pass", "candidate satisfies reciprocal symmetry on sampled training-domain pairs", evidence)
            )

        values = []
        for point in points:
            try:
                value = float(fn(*point))
            except Exception:
                value = float("nan")
            values.append(value)

        finite = all(math.isfinite(value) for value in values)
        if kind in {"finite_output", "finite_output_screen"}:
            violations = sum(not math.isfinite(value) for value in values)
            passed = violations == 0
        elif kind == "positive_output_screen":
            violations = sum(
                (not math.isfinite(value)) or value <= self.tolerance
                for value in values
            )
            passed = violations == 0
        elif kind == "nonpositive_output_screen":
            violations = sum(
                (not math.isfinite(value)) or value > self.tolerance
                for value in values
            )
            passed = violations == 0
        elif not finite:
            violations = sum(
                (not math.isfinite(value)) or (
                    value <= self.tolerance if kind == "positive_output"
                    else value < -self.tolerance
                )
                for value in values
            )
            passed = False
        elif kind == "positive_output":
            violations = sum(value <= self.tolerance for value in values)
            passed = violations == 0
        elif kind == "nonnegative_output":
            violations = sum(value < -self.tolerance for value in values)
            passed = violations == 0
        else:
            variable = params.get("variable")
            if variable not in problem.variable_names:
                return "unknown", "symmetry constraint requires a declared 'variable' parameter", {}
            index = problem.variable_names.index(variable)
            low, high = axes[index][0], axes[index][-1]
            if abs(low + high) > self.tolerance:
                return "unknown", "symmetry checks require bounds symmetric about zero", {}
            comparisons = []
            for point in points:
                mirrored = list(point)
                mirrored[index] = -mirrored[index]
                try:
                    left, right = float(fn(*point)), float(fn(*mirrored))
                except Exception:
                    left = right = float("nan")
                expected = right if kind == "even_in" else -right
                comparisons.append(
                    math.isfinite(left) and math.isfinite(right)
                    and abs(left - expected) <= self.tolerance * max(1.0, abs(left), abs(expected))
                )
            violations = sum(not item for item in comparisons)
            passed = violations == 0

        evidence = {
            "sample_count": len(points),
            "expected_grid_size": (5 if kind == "finite_output_screen" else 3) ** len(axes),
            "finite_sample_count": sum(math.isfinite(value) for value in values),
            "sample_min": min((value for value in values if math.isfinite(value)), default=None),
            "sample_max": max((value for value in values if math.isfinite(value)), default=None),
            "evaluation_count": len(points),
            "violation_count": int(violations),
            "violation_fraction": float(violations / len(points)) if points else None,
            "sampling": (
                "deterministic_5_point_cartesian_domain_screen"
                if kind == "finite_output_screen"
                else "deterministic_cartesian_bounds_grid"
            ),
            "sampled_screening_status": "pass" if passed else "fail",
            "proof_scope": "finite_sample_screening_only_not_continuous_domain_proof",
            "continuous_domain_proof_established": False,
            "grid_is_exhaustive": True,
        }
        if not passed:
            return "fail", f"declared {kind} constraint failed on deterministic domain samples", evidence
        if kind in {"finite_output_screen", "positive_output_screen", "nonpositive_output_screen"}:
            return "pass", f"candidate passed the sampled {kind} screen", evidence
        return (
            "unknown",
            "deterministic symmetry samples passed, but finite-grid screening does not prove the property over the continuous domain",
            evidence,
        )


__all__ = ["CandidateValidator", "CandidateValidationError"]
