"""Validation of formula metadata before symbolic or numerical adjudication."""
from __future__ import annotations

import math
from typing import Any

from .audit_schema import audit_result, VARIABLE_SCHEMA_MISSING


def validate_formula_metadata(
    formula_source: str | None,
    variable_names: list[str] | None,
    constants: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate required source/schema metadata without executing formula text."""
    errors: list[str] = []
    if not isinstance(formula_source, str) or not formula_source.strip():
        errors.append("formula_source must be a non-empty string")
    elif len(formula_source) > 20_000:
        errors.append("formula_source exceeds 20000 characters")

    if (not isinstance(variable_names, list) or not variable_names
            or not all(isinstance(name, str) and name.isidentifier() for name in variable_names)):
        errors.append("variable_names must be a non-empty list of identifiers")
    elif len(set(variable_names)) != len(variable_names):
        errors.append("variable_names must be unique")

    if constants is not None:
        if not isinstance(constants, dict):
            errors.append("constants must be a mapping")
        else:
            for name, value in constants.items():
                if (not isinstance(name, str) or not name.isidentifier()
                        or isinstance(value, bool)
                        or not isinstance(value, (int, float))
                        or not math.isfinite(float(value))):
                    errors.append(f"constant {name!r} must have an identifier and finite numeric value")

    if errors:
        return audit_result(VARIABLE_SCHEMA_MISSING, valid=False, errors=errors)
    return audit_result("valid_metadata", valid=True, errors=[])



def validate_generated_formula(
    formula_source: str | None,
    ground_truth: str | None,
    variable_names: list[str] | None,
    ground_truth_aliases: dict[str, str] | None = None,
    constants: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fail-closed, offline gate for a generated formula before exact-match credit.

    Formula text is parsed by the restricted AST-to-SymPy adjudicator and is
    never executed. Only an exact formal identity is eligible for exact-match
    credit. A parse failure, missing schema, or unsupported construct remains
    not assessable; numerical fit and benchmark-domain agreement are not used.
    """
    from .symbolic_audit import audit_formula

    metadata = validate_formula_metadata(formula_source, variable_names, constants)
    if not metadata.get("valid"):
        return {
            "status": metadata["status"],
            "symbolically_equivalent": None,
            "eligible_for_exact_match": False,
            "validation_scope": "future_run_offline_gate",
            "errors": metadata.get("errors", []),
        }

    result = audit_formula(
        formula_source,
        ground_truth,
        variable_names,
        ground_truth_aliases=ground_truth_aliases,
        constants=constants,
    )
    result["eligible_for_exact_match"] = (
        result.get("status") == "exact_symbolic_equivalent"
        and result.get("symbolically_equivalent") is True
    )
    result["validation_scope"] = "future_run_offline_gate"
    return result
