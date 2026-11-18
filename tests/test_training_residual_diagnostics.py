"""Regression coverage for training-only residual diagnostics."""

import numpy as np
import pytest

from hypatiax.tools.symbolic.training_validation import (
    evaluate_candidate_on_training_folds,
    make_training_folds,
)


def test_fold_residual_diagnostics_are_normalized_on_fit_target_scale():
    X = np.arange(20, dtype=float).reshape(-1, 1)
    y = 2.0 * X[:, 0] + 1.0
    folds = make_training_folds(
        len(y), n_splits=2, n_repeats=1,
        validation_fraction=0.2, seed=7,
    )

    def biased_predictor(X_fit, y_fit, X_validation):
        return 2.0 * X_validation[:, 0] + 3.0

    summary = evaluate_candidate_on_training_folds(
        "2*x + 3", biased_predictor, X, y, folds,
        minimum_valid_folds=2,
    )

    assert summary.valid_fold_count == 2
    serialized = summary.to_dict()["fold_metrics"]
    assert all("normalized_residual_bias" in item for item in serialized)
    for metric in summary.fold_metrics:
        fit_scale = np.std(y[list(next(
            fold.train_indices for fold in folds
            if fold.repeat == metric.repeat and fold.fold == metric.fold
        ))])
        assert metric.normalized_residual_bias == pytest.approx(-2.0 / fit_scale)
        assert metric.normalized_residual_std == pytest.approx(0.0)
        assert metric.max_abs_normalized_residual == pytest.approx(2.0 / fit_scale)


def test_residual_diagnostics_are_unavailable_for_constant_fit_target():
    X = np.arange(8, dtype=float).reshape(-1, 1)
    y = np.ones(8, dtype=float)
    folds = make_training_folds(
        len(y), n_splits=2, n_repeats=1,
        validation_fraction=0.25, seed=3,
    )

    summary = evaluate_candidate_on_training_folds(
        "1", lambda X_fit, y_fit, X_validation: np.ones(len(X_validation)),
        X, y, folds, minimum_valid_folds=2,
    )

    for metric in summary.fold_metrics:
        assert metric.normalized_residual_bias is None
        assert metric.normalized_residual_std is None
        assert metric.max_abs_normalized_residual is None
