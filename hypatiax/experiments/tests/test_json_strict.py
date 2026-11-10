import io
import json
import math

import numpy as np

from hypatiax.core.json_strict import sanitize, strict_json


def _strict_loads(s):
    def boom(c):
        raise ValueError(c)
    return json.loads(s, parse_constant=boom)


def test_nonfinite_becomes_null_with_kind_marker():
    row = {"r2": float("-inf"), "rmse": float("nan"), "x": float("inf"), "ok": 0.5}
    out = _strict_loads(strict_json.dumps(row))
    assert out["r2"] is None and out["r2_nonfinite"] == "-inf"
    assert out["rmse"] is None and out["rmse_nonfinite"] == "nan"
    assert out["x"] is None and out["x_nonfinite"] == "+inf"
    assert out["ok"] == 0.5 and "ok_nonfinite" not in out


def test_nested_lists_and_numpy_floats():
    obj = {"0": {"hypatia": {"extrap_r2_far": np.float64("-inf"), "k": np.float32("nan")}},
           "v": [1.0, float("-inf")]}
    out = _strict_loads(strict_json.dumps(obj))
    assert out["0"]["hypatia"]["extrap_r2_far"] is None
    assert out["0"]["hypatia"]["extrap_r2_far_nonfinite"] == "-inf"
    assert out["0"]["hypatia"]["k_nonfinite"] == "nan"
    assert out["v"] == [1.0, None]


def test_marker_collision_preserves_input_and_adds_unambiguous_marker():
    row = {"score": float("-inf"), "score_nonfinite": "caller-value"}
    out = sanitize(row)
    assert out["score"] is None
    assert out["score_nonfinite"] == "caller-value"
    assert out["score_nonfinite__1"] == "-inf"


def test_dump_writes_nothing_on_failure_and_ignores_allow_nan():
    buf = io.StringIO()
    strict_json.dump({"a": float("-inf")}, buf, allow_nan=True, indent=2)
    assert "Infinity" not in buf.getvalue() and "NaN" not in buf.getvalue()
    buf2 = io.StringIO()
    try:
        strict_json.dump({"a": object()}, buf2)
    except TypeError:
        pass
    assert buf2.getvalue() == ""


def test_other_json_attributes_delegate():
    assert strict_json.loads("[1, 2]") == [1, 2]
    assert strict_json.JSONDecodeError is json.JSONDecodeError


def test_input_not_mutated():
    row = {"r2": float("-inf")}
    sanitize(row)
    assert math.isinf(row["r2"]) and "r2_nonfinite" not in row
