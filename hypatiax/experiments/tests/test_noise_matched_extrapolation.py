"""Offline tests for package-level noise-matched extrapolation."""

import numpy as np
import pytest

from hypatiax.experiments.evaluation import add_noise_matched_extrapolation


def test_noise_scale_seed_streams_and_clean_data_immutability():
    X_near = np.arange(3).reshape(-1, 1)
    X_far = np.arange(2).reshape(-1, 1)
    y_near = np.array([10.0, 20.0, 30.0])
    y_far = np.array([40.0, 50.0])
    clean_near, clean_far = y_near.copy(), y_far.copy()
    reference = np.array([1.0, 2.0, 3.0, 4.0])
    seed, level = 42, 0.05

    result = add_noise_matched_extrapolation(
        {"near": (X_near, y_near), "far": (X_far, y_far)},
        seed=seed, noise_level=level, reference_y=reference,
    )

    scale = level * np.std(reference)
    expected_near = clean_near + np.random.RandomState(seed + 1999).normal(
        0.0, scale, size=len(clean_near)
    )
    expected_far = clean_far + np.random.RandomState(seed + 2000).normal(
        0.0, scale, size=len(clean_far)
    )
    np.testing.assert_array_equal(result["near"][0], X_near)
    np.testing.assert_array_equal(result["far"][0], X_far)
    np.testing.assert_allclose(result["near"][1], expected_near, rtol=0, atol=0)
    np.testing.assert_allclose(result["far"][1], expected_far, rtol=0, atol=0)
    np.testing.assert_array_equal(y_near, clean_near)
    np.testing.assert_array_equal(y_far, clean_far)


def test_noise_streams_are_reproducible_and_independent():
    parts = {
        "near": (np.arange(8), np.ones(8)),
        "far": (np.arange(8), np.ones(8)),
    }
    first = add_noise_matched_extrapolation(parts, 7, 0.05, np.arange(1.0, 9.0))
    second = add_noise_matched_extrapolation(parts, 7, 0.05, np.arange(1.0, 9.0))
    np.testing.assert_array_equal(first["near"][1], second["near"][1])
    np.testing.assert_array_equal(first["far"][1], second["far"][1])
    assert not np.array_equal(first["near"][1], first["far"][1])


@pytest.mark.parametrize("level", [-0.1, float("nan"), float("inf")])
def test_invalid_noise_level_rejected(level):
    with pytest.raises(ValueError, match="noise_level"):
        add_noise_matched_extrapolation({}, 1, level, [1.0, 2.0])


def test_invalid_reference_targets_rejected():
    with pytest.raises(ValueError, match="reference_y"):
        add_noise_matched_extrapolation({}, 1, 0.05, [])
    with pytest.raises(ValueError, match="reference_y"):
        add_noise_matched_extrapolation({}, 1, 0.05, [1.0, np.nan])
