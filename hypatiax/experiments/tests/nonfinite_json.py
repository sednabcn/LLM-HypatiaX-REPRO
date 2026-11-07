"""Write non-finite floats as null + status; read old and new result files.

In memory: keep -inf/inf (routing and comparisons stay unchanged).
On disk: null plus an *_status field, written with allow_nan=False so any
missed site raises at write time instead of silently emitting -Infinity.
"""
import json
import math

NEG_INF = float("-inf")


def status_of(value):
    """'ok' for finite numbers, 'failed' for None/nan/inf."""
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return "ok"
    return "failed"


def sanitize(obj):
    """Recursively replace non-finite floats with None."""
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    return obj


def add_status(d, fields=("r2", "rmse")):
    """Return a copy of d with <field>_status for each present field.
    Call BEFORE sanitize(), while the original inf/nan is still visible."""
    out = dict(d)
    for f in fields:
        if f in d:
            out[f + "_status"] = status_of(d[f])
    return out


def dump_strict(obj, fp, **kw):
    kw.setdefault("default", str)
    json.dump(sanitize(obj), fp, allow_nan=False, **kw)


def dumps_strict(obj, **kw):
    kw.setdefault("default", str)
    return json.dumps(sanitize(obj), allow_nan=False, **kw)


def load_tolerant(fp):
    """json.load accepts bare -Infinity/Infinity/NaN from old files."""
    return json.load(fp)


def r2_or_neg_inf(value):
    """Reader helper: null, nan, 'Infinity' strings -> -inf; finite -> float."""
    if value is None:
        return NEG_INF
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            return NEG_INF
    try:
        v = float(value)
    except (TypeError, ValueError):
        return NEG_INF
    return v if math.isfinite(v) else NEG_INF


def is_finite_num(value):
    """Safe replacement for np.isfinite(x) when x may be None."""
    return status_of(value) == "ok"
