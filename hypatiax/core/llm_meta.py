"""Extract LLM provenance recorded by the discovery engine."""
from __future__ import annotations

import math


def _num(x):
    # bool is an int subclass, but is never a meaningful duration/confidence.
    if isinstance(x, bool):
        return None
    try:
        v = float(x)
    except (TypeError, ValueError, OverflowError):
        return None
    return v if math.isfinite(v) and v >= 0 else None


def llm_meta(res) -> dict:
    """Return llm_time_s / llm_expression / llm_confidence from a discover() result."""
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
