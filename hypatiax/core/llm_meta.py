"""Pull the LLM provenance the engine records out of a discover() result."""
from __future__ import annotations

import math


def _num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) and v >= 0 else None


def llm_meta(res) -> dict:
    """llm_time_s / llm_expression / llm_confidence from res['llm_info'] (first LLM attempt).

    Falls back to 0.0 / None when the engine reported nothing, as the rows did before.
    """
    info = (res or {}).get("llm_info") or {}
    if not isinstance(info, dict):
        info = {}
    t = _num(info.get("llm_time"))
    expr = info.get("llm_best_expression")
    return {
        "llm_time_s": t if t is not None else 0.0,
        "llm_expression": str(expr) if expr not in (None, "") else None,
        "llm_confidence": _num(info.get("llm_confidence")),
    }
