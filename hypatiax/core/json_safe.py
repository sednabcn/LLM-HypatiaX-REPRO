import math

_ENC = {"nan": "NaN", "inf": "Infinity", "-inf": "-Infinity"}
_DEC = {"NaN": float("nan"), "Infinity": float("inf"), "-Infinity": float("-inf")}

def clean(o):
    """Encode non-finite floats as strings so output is strict JSON and lossless."""
    if isinstance(o, float):
        if math.isnan(o):
            return _ENC["nan"]
        if math.isinf(o):
            return _ENC["inf"] if o > 0 else _ENC["-inf"]
        return o
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    return o

def restore(o):
    """Inverse of clean(), for readers."""
    if isinstance(o, str) and o in _DEC:
        return _DEC[o]
    if isinstance(o, dict):
        return {k: restore(v) for k, v in o.items()}
    if isinstance(o, list):
        return [restore(v) for v in o]
    return o
