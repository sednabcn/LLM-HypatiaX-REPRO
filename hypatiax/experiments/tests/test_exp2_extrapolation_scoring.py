"""Regression contracts for the shared Exp2 far-extrapolation scorer.

These tests are offline: they exercise only deterministic formula evaluation and
metric reporting, without loading benchmark backends or calling an LLM.
"""
from types import SimpleNamespace

import numpy as np
import pytest

from hypatiax.experiments.benchmarks.extrap_r2_far import (
    _runner_eval_formula,
    build_extrap_split,
    compute_extrap_r2_far,
)


def test_runner_formula_evaluator_imports_regex_and_scores_expression():
    X = np.array([[1.0], [2.0], [3.0]])
    predicted = _runner_eval_formula("x + 1", X, ["x"])
    np.testing.assert_allclose(predicted, [2.0, 3.0, 4.0])


def test_far_rmse_is_preserved_when_far_r2_is_catastrophic():
    X_far = np.array([[1.0], [2.0], [3.0]])
    y_far = np.array([1.0, 2.0, 3.0])
    result = SimpleNamespace(success=True, formula="1000 * x")

    r2, rmse, error_pct = compute_extrap_r2_far(
        {"symbolic": result},
        X_far,
        y_far,
        ["x"],
    )

    assert r2["symbolic"] is None
    assert rmse["symbolic"] == pytest.approx(
        np.sqrt(np.mean((y_far - 1000.0 * X_far[:, 0]) ** 2))
    )
    assert error_pct["symbolic"] is None


def test_extrap_split_is_disjoint_and_reports_expected_coverage():
    X = np.arange(200, dtype=float).reshape(-1, 1)
    y = X[:, 0] ** 2
    X_train, y_train, X_far, y_far, metadata = build_extrap_split(
        X, y, train_frac=0.8, multiplier=2.0
    )
    assert len(X_train) == 160
    assert len(X_far) == 40
    assert X_train[:, 0].max() < X_far[:, 0].min()
    assert metadata["extrap_n_train"] == 160
    assert metadata["extrap_n_test"] == 40


@pytest.mark.parametrize(
    "kwargs",
    [
        {"train_frac": 0.0},
        {"train_frac": 1.0},
        {"train_frac": float("nan")},
        {"multiplier": 0.0},
        {"multiplier": -1.0},
    ],
)
def test_extrap_split_rejects_invalid_protocol_parameters(kwargs):
    X = np.arange(20, dtype=float).reshape(-1, 1)
    y = X[:, 0] ** 2
    with pytest.raises(ValueError):
        build_extrap_split(X, y, **kwargs)


def test_extrap_split_rejects_empty_or_too_small_far_region():
    X = np.arange(200, dtype=float).reshape(-1, 1)
    y = X[:, 0] ** 2
    with pytest.raises(ValueError, match="far region"):
        build_extrap_split(X, y, train_frac=0.8, multiplier=0.001)


def test_both_active_feynman_runners_fail_closed_on_invalid_extrapolation_splits():
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    for filename in (
        "run_comparative_suite_benchmark_v2.py",
        "run_comparative_suite_benchmark_pca.py",
    ):
        source = (root / "hypatiax/experiments/benchmarks" / filename).read_text()
        assert "raise RuntimeError(" in source
        assert "refusing an in-sample fallback" in source
        assert "if split < 2 or n - split < 2:" in source
        assert "if len(X_far) < 2:" in source
        assert "rmse_far = _far_rmse(y_far, y_far_pred)" in source
