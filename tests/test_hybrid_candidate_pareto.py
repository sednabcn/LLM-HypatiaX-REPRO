"""Regression coverage for fold-local candidate evaluation before Pareto selection."""
import numpy as np
import pytest

from hypatiax.tools.symbolic.hybrid_fold_search import (
    evaluate_hybrid_candidate_on_training_folds,
)
from hypatiax.tools.symbolic.training_validation import make_training_folds


def test_candidate_coefficients_are_refit_with_training_fold_transforms():
    X = np.linspace(0.5, 8.0, 40).reshape(-1, 1)
    y = 3.25 * X[:, 0] - 0.75
    folds = make_training_folds(
        len(y), n_splits=3, n_repeats=1,
        validation_fraction=0.2, seed=19,
    )

    summary = evaluate_hybrid_candidate_on_training_folds(
        "1.0*x - 0.5",
        ["x"],
        ["x"],
        X,
        y,
        folds,
        minimum_valid_folds=3,
    )

    assert summary.valid_fold_count == 3
    assert summary.failed_fold_count == 0
    assert summary.mean_normalized_rmse is not None
    assert summary.mean_normalized_rmse < 1e-5
    assert all(item.fitted_expression for item in summary.fold_metrics)


def test_candidate_fold_preprocessing_learns_extreme_scale_log_from_fit_rows():
    X = np.geomspace(1e6, 1e10, 40).reshape(-1, 1)
    y = 2.0 * np.log10(X[:, 0] + 1.0)
    folds = make_training_folds(
        len(y), n_splits=2, n_repeats=1,
        validation_fraction=0.2, seed=23,
    )

    summary = evaluate_hybrid_candidate_on_training_folds(
        "1.0*x",
        ["x"],
        ["x"],
        X,
        y,
        folds,
        minimum_valid_folds=2,
    )

    assert summary.valid_fold_count == 2
    assert summary.failed_fold_count == 0
    assert summary.mean_normalized_rmse is not None
    assert summary.mean_normalized_rmse < 1e-5


def test_candidate_with_unrecognized_engineered_symbol_fails_closed():
    X = np.column_stack((np.linspace(1, 4, 20), np.linspace(2, 8, 20)))
    y = X[:, 0] + X[:, 1]
    folds = make_training_folds(
        len(y), n_splits=2, n_repeats=1,
        validation_fraction=0.2, seed=29,
    )

    with pytest.raises((ValueError, TypeError)):
        evaluate_hybrid_candidate_on_training_folds(
            "1.0*gm_x_y",
            ["x", "y", "gm_x_z"],
            ["x", "y"],
            X,
            y,
            folds,
            minimum_valid_folds=2,
        )



def test_candidate_with_geometric_mean_feature_is_refit_inside_each_fold():
    a = np.linspace(1.0, 5.0, 40)
    b = np.linspace(2.0, 8.0, 40)
    X = np.column_stack((a, b))
    y = 2.5 * np.sqrt(a * b)
    folds = make_training_folds(
        len(y), n_splits=3, n_repeats=1,
        validation_fraction=0.2, seed=31,
    )

    summary = evaluate_hybrid_candidate_on_training_folds(
        "1.0*gm_a_b",
        ["a", "b", "gm_a_b"],
        ["a", "b"],
        X,
        y,
        folds,
        minimum_valid_folds=3,
    )

    assert summary.valid_fold_count == 3
    assert summary.failed_fold_count == 0
    assert summary.mean_rmse < 1e-7


def test_candidate_with_directed_ratio_feature_is_refit_inside_each_fold():
    a = np.linspace(2.0, 9.0, 40)
    b = np.linspace(1.0, 3.0, 40)
    X = np.column_stack((a, b))
    y = 1.75 * (a / b)
    folds = make_training_folds(
        len(y), n_splits=3, n_repeats=1,
        validation_fraction=0.2, seed=37,
    )

    summary = evaluate_hybrid_candidate_on_training_folds(
        "1.0*ratio_a_b",
        ["a", "b", "ratio_a_b"],
        ["a", "b"],
        X,
        y,
        folds,
        minimum_valid_folds=3,
    )

    assert summary.valid_fold_count == 3
    assert summary.failed_fold_count == 0
    assert summary.mean_rmse < 1e-7


def test_candidate_target_signed_log_is_learned_and_inverted_per_fold():
    x = np.linspace(0.0, 20.0, 40)
    X = x.reshape(-1, 1)
    y = np.power(10.0, 0.2 * x) - 1.0
    folds = make_training_folds(
        len(y), n_splits=3, n_repeats=1,
        validation_fraction=0.2, seed=41,
    )

    summary = evaluate_hybrid_candidate_on_training_folds(
        "0.2*x",
        ["x"],
        ["x"],
        X,
        y,
        folds,
        minimum_valid_folds=3,
    )

    assert summary.valid_fold_count == 3
    assert summary.failed_fold_count == 0
    assert summary.mean_normalized_rmse < 1e-5
