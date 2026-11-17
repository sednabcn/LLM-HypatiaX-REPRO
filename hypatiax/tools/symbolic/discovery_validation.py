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
    ) -> CandidateRecord:
        """Parse and validate a candidate; no training or far target data accepted."""
        if not isinstance(problem, DiscoveryProblem):
            raise TypeError("problem must be a DiscoveryProblem")
        outcomes: list[ConstraintOutcome] = []
        rejection_reasons: list[str] = []
        normalized = expression.strip() if isinstance(expression, str) else ""

        try:
            import sympy as sp

            parsed = parse_sympy_expression(normalized, list(problem.variable_names))
            if parsed is None or parsed.has(sp.zoo, sp.nan, sp.oo, -sp.oo):
                raise ValueError("expression contains a non-finite symbolic value")
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
        import sympy as sp

        supported = {
            "positive_output", "nonnegative_output", "finite_output",
            "even_in", "odd_in",
        }
        if spec.kind not in supported:
            return "unknown", f"unsupported declared constraint kind: {spec.kind}", {}
        if not all(
            name in problem.variable_domains
            and "minimum" in problem.variable_domains[name]
            and "maximum" in problem.variable_domains[name]
            for name in problem.variable_names
        ):
            return "unknown", "complete finite variable bounds are required for sampling", {}

        axes = []
        for name in problem.variable_names:
            bounds = problem.variable_domains[name]
            low, high = float(bounds["minimum"]), float(bounds["maximum"])
            if not math.isfinite(low) or not math.isfinite(high) or low > high:
                return "unknown", f"invalid finite bounds for variable {name}", {}
            axes.append((low, (low + high) / 2.0, high))
        points = list(itertools.product(*axes))
        if len(points) > self.sample_limit:
            stride = max(1, math.ceil(len(points) / self.sample_limit))
            points = points[::stride][:self.sample_limit]

        symbols = {
            name: sp.Symbol(name, real=True) for name in problem.variable_names
        }
        fn = sp.lambdify(
            [symbols[name] for name in problem.variable_names],
            expression, modules=["math"],
        )
        values = []
        for point in points:
            try:
                value = float(fn(*point))
            except Exception:
                value = float("nan")
            values.append(value)

        finite = all(math.isfinite(value) for value in values)
        if spec.kind == "finite_output":
            passed = finite
        elif not finite:
            passed = False
        elif spec.kind == "positive_output":
            passed = all(value > self.tolerance for value in values)
        elif spec.kind == "nonnegative_output":
            passed = all(value >= -self.tolerance for value in values)
        else:
            variable = spec.parameters.get("variable")
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
                    left = float(fn(*point))
                    right = float(fn(*mirrored))
                except Exception:
                    return "unknown", "symmetry evaluation failed on mirrored domain", {}
                expected = right if spec.kind == "even_in" else -right
                comparisons.append(
                    math.isfinite(left) and math.isfinite(right)
                    and abs(left - expected) <= self.tolerance * max(1.0, abs(left), abs(expected))
                )
            passed = all(comparisons)
        evidence = {
            "sample_count": len(points),
            "finite_sample_count": sum(math.isfinite(value) for value in values),
            "sample_min": min(values) if finite and values else None,
            "sample_max": max(values) if finite and values else None,
            "sampling": "deterministic_cartesian_bounds_grid",
        }
        return (
            ("pass", "declared constraint passed on deterministic domain samples", evidence)
            if passed else
            ("fail", "declared constraint failed on deterministic domain samples", evidence)
        )


__all__ = ["CandidateValidator", "CandidateValidationError"]
