"""Strict-JSON writing: non-finite floats become null with an adjacent kind marker."""
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
        # Reserve all caller-supplied keys so generated markers never overwrite them,
        # even when the colliding key appears later in insertion order.
        reserved = set(obj)
        for k, v in obj.items():
            if isinstance(v, _FLOATS) and not math.isfinite(float(v)):
                out[k] = None
                if mark and isinstance(k, str):
                    marker = f"{k}_nonfinite"
                    if marker in reserved:
                        base = marker
                        suffix = 1
                        while f"{base}__{suffix}" in reserved or f"{base}__{suffix}" in out:
                            suffix += 1
                        marker = f"{base}__{suffix}"
                    out[marker] = _kind(float(v))
            else:
                out[k] = sanitize(v, mark)
        return out
    if isinstance(obj, (list, tuple)):
        return [sanitize(v, mark) for v in obj]
    if isinstance(obj, _FLOATS) and not math.isfinite(float(obj)):
        return None
    return obj


class _StrictJSON:
    """Drop-in for the json module: dump/dumps write strict JSON, other attributes delegate."""

    def __getattr__(self, name: str):
        return getattr(_json, name)

    @staticmethod
    def dumps(obj, **kw):
        kw.pop("allow_nan", None)
        return _json.dumps(sanitize(obj), allow_nan=False, **kw)

    @staticmethod
    def dump(obj, fp, **kw):
        # Serialize fully first so failures cannot leave a truncated file.
        fp.write(_StrictJSON.dumps(obj, **kw))


strict_json = _StrictJSON()
