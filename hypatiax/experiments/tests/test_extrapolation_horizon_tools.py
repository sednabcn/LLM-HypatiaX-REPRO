"""Offline regression tests for the reusable extrapolation-horizon utilities."""
import json

import numpy as np
import pytest

from hypatiax.tools.extrapolation_horizon import (
    generate_horizon_scenarios,
    score_predictions,
    write_results_json,
)


def test_upper_and_lower_horizons_are_scaled_from_training_range():
    X_train = np.array([[1.0], [5.0], [10.0]])
    upper, lower = generate_horizon_scenarios(
        X_train, distances=(1.0,), strategy="both", n_points=2
    )
    assert upper["strategy"] == "both"
    assert upper["X_test"][-1, 0] == pytest.approx(19.0)
    assert lower["X_test"][-1, 0] == pytest.approx(-8.0)


def test_combination_horizon_moves_multiple_features_together():
    X_train = np.array([[1.0, 10.0], [3.0, 20.0], [5.0, 30.0]])
    scenarios = generate_horizon_scenarios(
        X_train,
        distances=(0.5,),
        strategy="combinations",
        feature_names=("mass", "velocity"),
        directions=((1, -1),),
        n_points=2,
    )
    assert scenarios[0]["features_moved"] == ["mass", "velocity"]
    assert scenarios[0]["X_test"][-1, 0] > 5.0
    assert scenarios[0]["X_test"][-1, 1] < 10.0


def test_zero_training_rmse_does_not_hide_other_metrics():
    scored = score_predictions(
        y_true=[2.0, 4.0], y_pred=[2.2, 3.8],
        y_train=[1.0, 2.0], y_pred_train=[1.0, 2.0],
        interval_lower=[1.5, 3.5], interval_upper=[2.5, 4.5],
    )
    assert scored["metrics"]["far_train_rmse_ratio_pct"] is None
    assert scored["diagnostics"]["far_train_rmse_ratio_status"] == "undefined_zero_training_rmse"
    assert scored["metrics"]["normalized_far_rmse"] is not None
    assert scored["metrics"]["interval_coverage"] == 1.0


def test_json_export_is_finite_and_numpy_safe(tmp_path):
    path = write_results_json(
        [{"method": "demo", "metric": np.float64(0.5), "undefined": float("nan")}],
        tmp_path / "results.json",
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["results"][0]["metric"] == 0.5
    assert payload["results"][0]["undefined"] is None


def test_invalid_direction_is_rejected():
    with pytest.raises(ValueError, match="direction"):
        generate_horizon_scenarios(
            [[1.0, 2.0], [2.0, 3.0]],
            strategy="combinations",
            directions=((1, 2),),
        )
