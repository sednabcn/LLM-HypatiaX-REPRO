"""Shared result statuses and lightweight result helpers for formula audits."""
from __future__ import annotations

from typing import Any

EXACT_SYMBOLIC_EQUIVALENT = "exact_symbolic_equivalent"
NOT_SYMBOLICALLY_EQUIVALENT = "not_symbolically_equivalent"
NOT_ASSESSABLE = "not_assessable"
GROUND_TRUTH_MISSING = "ground_truth_missing"
NO_LLM_FORMULA = "no_llm_formula"
VARIABLE_SCHEMA_MISSING = "variable_schema_missing"
NUMERICALLY_AGREE = "numerically_agree"
NUMERICALLY_DISAGREE = "numerically_disagree"


def audit_result(status: str, **fields: Any) -> dict[str, Any]:
    """Build a JSON-serializable audit record with a stable status field."""
    return {"status": status, **fields}
