"""Offline tests for package-level noise-matched extrapolation."""
import numpy as np
import pytest
from hypatiax.experiments.evaluation import add_noise_matched_extrapolation

def test_noise_scale_seed_streams_and_clean_data_immutability():
    xn, xf = np.arange(3).reshape(-1, 1), np.arange(2).reshape(-1, 1)
    yn, yf = np.array([10., 20., 30.]), np.array([40., 50.])
    yn0, yf0 = yn.copy(), yf.copy()
    ref, seed, level = np.array([1., 2., 3., 4.]), 42, 0.05
    out = add_noise_matched_extrapolation({"near": (xn, yn), "far": (xf, yf)}, seed, level, ref)
    scale = level * np.std(ref)
    en = yn0 + np.random.RandomState(seed + 1999).normal(0., scale, len(yn0))
    ef = yf0 + np.random.RandomState(seed + 2000).normal(0., scale, len(yf0))
    np.testing.assert_array_equal(out["near"][0], xn)
    np.testing.assert_array_equal(out["far"][0], xf)
    np.testing.assert_allclose(out["near"][1], en, rtol=0, atol=0)
    np.testing.assert_allclose(out["far"][1], ef, rtol=0, atol=0)
    np.testing.assert_array_equal(yn, yn0)
    np.testing.assert_array_equal(yf, yf0)

def test_noise_streams_are_reproducible_and_independent():
    parts = {"near": (np.arange(8), np.ones(8)), "far": (np.arange(8), np.ones(8))}
    a = add_noise_matched_extrapolation(parts, 7, .05, np.arange(1., 9.))
    b = add_noise_matched_extrapolation(parts, 7, .05, np.arange(1., 9.))
    np.testing.assert_array_equal(a["near"][1], b["near"][1])
    np.testing.assert_array_equal(a["far"][1], b["far"][1])
    assert not np.array_equal(a["near"][1], a["far"][1])

@pytest.mark.parametrize("level", [-.1, float("nan"), float("inf")])
def test_invalid_noise_level_rejected(level):
    with pytest.raises(ValueError, match="noise_level"):
        add_noise_matched_extrapolation({}, 1, level, [1., 2.])

def test_invalid_reference_targets_rejected():
    with pytest.raises(ValueError, match="reference_y"):
        add_noise_matched_extrapolation({}, 1, .05, [])
    with pytest.raises(ValueError, match="reference_y"):
        add_noise_matched_extrapolation({}, 1, .05, [1., np.nan])
