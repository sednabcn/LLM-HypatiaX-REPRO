"""Option 3, Phase 1: regression tests for the recovery evaluator (report s2.2).

Point RECOVERY_EVAL at the real R^2 / recovery function as  module:function
(signature assumed: fn(y_true, y_pred) -> float).  Find it with:
    grep -rn "ss_tot" hypatiax/ scripts/ --include=*.py
Degenerate-target rule (DECIDED, rule A): a constant or near-constant target has an
UNDEFINED R^2 (NaN) and is NEVER counted as recovered, even for an exact prediction.
Write this rule into the paper's recovery definition (and Supplement A).
"""
import importlib, math, os
import numpy as np
import pytest

PRIMARY, STRICT = 0.99, 0.999999


def _fn():
    spec = os.environ.get("RECOVERY_EVAL", "").strip()
    if ":" not in spec:
        pytest.fail("RECOVERY_EVAL not set (module:function). A gate that cannot run must not pass.")
    mod, name = spec.split(":", 1)
    return getattr(importlib.import_module(mod), name)


def _r2(y, p):
    v = _fn()(np.asarray(y, float), np.asarray(p, float))
    return float(v) if v is not None else float("nan")


def rec(r, thr):
    return math.isfinite(r) and r >= thr


rng = np.random.default_rng(0)
Y = rng.normal(size=200)


def test_perfect_fit_is_recovered():
    assert rec(_r2(Y, Y), STRICT)


def test_mean_predictor_is_not_recovered():
    assert not rec(_r2(Y, np.full_like(Y, Y.mean())), PRIMARY)


@pytest.mark.parametrize("scale", [1e-12, 1e-9, 1e-6, 1.0, 1e6])
def test_scale_invariance_of_exact_fit(scale):
    # an absolute fixed-threshold variance guard fails this for small scales
    assert rec(_r2(Y * scale, Y * scale), STRICT), f"exact fit not recovered at scale {scale}"


@pytest.mark.parametrize("scale", [1e-12, 1e-6, 1.0])
def test_scale_invariance_of_bad_fit(scale):
    bad = Y[::-1] * scale
    assert not rec(_r2(Y * scale, bad), PRIMARY), f"bad fit counted as recovered at scale {scale}"


def test_near_constant_target_exact_fit_is_undefined_not_recovered():
    # rule A: spread is negligible relative to magnitude -> degenerate -> never recovered
    y = 5.0 + 1e-12 * rng.normal(size=200)
    assert not rec(_r2(y, y), PRIMARY), "degenerate target must never count as recovered"


def test_near_constant_target_wrong_fit():
    y = 5.0 + 1e-12 * rng.normal(size=200)
    assert not rec(_r2(y, y + 1.0), PRIMARY)


def test_constant_target_exact_fit_is_undefined_not_recovered():
    y = np.full(50, 3.0)
    r = _r2(y, y)
    assert math.isnan(r), "rule A: R^2 on a constant target is undefined (NaN)"
    assert not rec(r, PRIMARY)


def test_constant_target_wrong_fit_not_recovered():
    y = np.full(50, 3.0)
    assert not rec(_r2(y, y + 0.5), PRIMARY)


def test_nan_prediction_never_recovered():
    p = Y.copy()
    p[3] = np.nan
    assert not rec(_r2(Y, p), PRIMARY)


def test_inf_prediction_never_recovered():
    p = Y.copy()
    p[3] = np.inf
    assert not rec(_r2(Y, p), PRIMARY)
