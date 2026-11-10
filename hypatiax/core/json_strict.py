"""Strict-JSON writing: RFC 8259 has no NaN/Infinity, so non-finite floats become null.

The kind is kept in a sibling key, e.g. extrap_r2_far = null plus
extrap_r2_far_nonfinite = "-inf" ("nan", "+inf"). With r2_canonical's policy, a null RMSE
next to a -inf R2 means non-finite predictions; a finite RMSE means the catastrophic
floor (R2 < -100). Scoring happens in memory, so this only changes what is written.
"""
from __future__ import annotations

import json as _json
import math
from typing import Any

try:
    import numpy as _np
    _FLOATS: tuple = (float, _np.floating)
except ImportError:  # pragma: no cover
    _FLOATS = (float,)


def _kind(x: float) -> str:
    return "nan" if math.isnan(x) else ("+inf" if x > 0 else "-inf")


def sanitize(obj: Any, mark: bool = True) -> Any:
    if isinstance(obj, dict):
        out: dict = {}
        for k, v in obj.items():
            if isinstance(v, _FLOATS) and not math.isfinite(float(v)):
                out[k] = None
                if mark and isinstance(k, str):
                    out[f"{k}_nonfinite"] = _kind(float(v))
            else:
                out[k] = sanitize(v, mark)
        return out
    if isinstance(obj, (list, tuple)):
        return [sanitize(v, mark) for v in obj]
    if isinstance(obj, _FLOATS) and not math.isfinite(float(obj)):
        return None
    return obj


class _StrictJSON:
    """Drop-in for the json module: dump/dumps write strict JSON, everything else delegates."""

    def __getattr__(self, name: str):
        return getattr(_json, name)

    @staticmethod
    def dumps(obj, **kw):
        kw.pop("allow_nan", None)
        return _json.dumps(sanitize(obj), allow_nan=False, **kw)

    @staticmethod
    def dump(obj, fp, **kw):
        # serialize fully first, so a failure can never leave a truncated file
        fp.write(_StrictJSON.dumps(obj, **kw))


strict_json = _StrictJSON()
