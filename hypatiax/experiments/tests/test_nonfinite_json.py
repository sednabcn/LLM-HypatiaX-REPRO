import io
import json

import pytest

from nonfinite_json import (NEG_INF, add_status, dumps_strict, is_finite_num,
                            load_tolerant, r2_or_neg_inf, sanitize)


def test_inf_becomes_null_with_status():
    row = add_status({"r2": NEG_INF, "rmse": float("inf"), "error": "boom"})
    s = dumps_strict(row)
    d = json.loads(s)
    assert d["r2"] is None and d["rmse"] is None
    assert d["r2_status"] == "failed" and d["rmse_status"] == "failed"
    assert "Infinity" not in s and "NaN" not in s


def test_finite_stays_ok():
    d = json.loads(dumps_strict(add_status({"r2": 0.9, "rmse": 0.1})))
    assert d["r2"] == 0.9 and d["r2_status"] == "ok"


def test_nested_and_nan():
    d = json.loads(dumps_strict({"a": [{"x": float("nan")}], "b": {"y": NEG_INF}}))
    assert d == {"a": [{"x": None}], "b": {"y": None}}


def test_strict_dump_is_valid_json_for_strict_parsers():
    def reject(c):
        raise ValueError(c)
    json.loads(dumps_strict({"r2": NEG_INF}), parse_constant=reject)


def test_reader_handles_old_and_new_files():
    old = load_tolerant(io.StringIO('{"r2": -Infinity, "rmse": Infinity}'))
    assert r2_or_neg_inf(old["r2"]) == NEG_INF
    assert r2_or_neg_inf(old["rmse"]) == NEG_INF
    assert r2_or_neg_inf(None) == NEG_INF
    assert r2_or_neg_inf("-Infinity") == NEG_INF
    assert r2_or_neg_inf("0.5") == 0.5
    assert r2_or_neg_inf(0.25) == 0.25


def test_is_finite_num_does_not_crash_on_none():
    assert not is_finite_num(None)
    assert not is_finite_num(NEG_INF)
    assert not is_finite_num(True)
    assert is_finite_num(0.0)


def test_unsanitized_inf_raises_loudly():
    with pytest.raises(ValueError):
        json.dumps({"r2": NEG_INF}, allow_nan=False)
    assert sanitize({"r2": NEG_INF}) == {"r2": None}
