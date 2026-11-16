import numpy as np
import pytest

from hypatiax.tools.uncertainty import (
    SplitConformalRegressor,
    evaluate_interval_levels,
    evaluate_prediction_intervals,
)


def test_split_conformal_uses_finite_sample_rank_and_frozen_predictions():
    calibrator = SplitConformalRegressor(0.8).fit(
        [1.0, 2.0, 3.0, 4.0, 5.0], [0.0, 0.0, 0.0, 0.0, 0.0]
    )
    assert calibrator.quantile() == 4.0
    lower, upper = calibrator.predict_interval([10.0, 20.0])
    np.testing.assert_allclose(lower, [6.0, 16.0])
    np.testing.assert_allclose(upper, [14.0, 24.0])
    assert calibrator.calibration_metadata["extra_domain_guarantee"] is False


def test_small_calibration_set_returns_conservative_infinite_radius():
    calibrator = SplitConformalRegressor(0.95).fit([1.0, 2.0], [1.0, 2.0])
    assert np.isinf(calibrator.quantile())
    lower, upper = calibrator.predict_interval([3.0])
    assert np.isneginf(lower[0]) and np.isposinf(upper[0])


def test_interval_metrics_report_coverage_width_and_score():
    result = evaluate_prediction_intervals(
        [0.0, 1.0, 2.0], [-0.5, 0.5, 1.5], [0.5, 1.5, 2.5], 0.9, 2.0
    )
    assert result["empirical_coverage"] == 1.0
    assert result["mean_interval_width"] == 1.0
    assert result["normalized_mean_interval_width"] == 0.5
    assert result["absolute_coverage_gap"] == pytest.approx(0.1)


def test_interval_metrics_reject_invalid_bounds():
    with pytest.raises(ValueError):
        evaluate_prediction_intervals([1.0], [2.0], [1.0], 0.9)


def test_multiple_nominal_levels_are_scored_independently():
    results = evaluate_interval_levels(
        [0.0, 1.0],
        [
            {"coverage": 0.8, "lower": [-0.1, 0.9], "upper": [0.1, 1.1]},
            {"coverage": 0.95, "lower": [-1.0, 0.0], "upper": [1.0, 2.0]},
        ],
    )
    assert len(results) == 2
    assert results[0]["empirical_coverage"] == 1.0
    assert results[1]["empirical_coverage"] == 1.0
