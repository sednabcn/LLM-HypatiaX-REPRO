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
