import numpy as np

from hypatiax.core.r2_canonical import r2_detail, r2_scored


def test_catastrophic_keeps_magnitude_but_scored_stays_minus_inf():
    y = np.linspace(1.0, 2.0, 50)
    p = y + 1e3
    raw, status = r2_detail(y, p)
    assert status == "catastrophic" and raw is not None and raw < -100
    assert r2_scored(y, p)[0] == float("-inf")      # scoring policy unchanged


def test_nonfinite_prediction_has_no_raw_value():
    y = np.linspace(1.0, 2.0, 50)
    p = y.copy(); p[3] = np.nan
    assert r2_detail(y, p) == (None, "nonfinite_pred")


def test_ok_case_matches_scored():
    y = np.linspace(1.0, 2.0, 50)
    p = y + 1e-3
    raw, status = r2_detail(y, p)
    assert status == "ok" and raw == r2_scored(y, p)[0]
