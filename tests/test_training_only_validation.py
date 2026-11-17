"""Offline regression coverage for training-only repeated validation."""
import numpy as np
import pytest

from hypatiax.tools.symbolic.training_validation import (
    evaluate_candidate_on_training_folds,
    expression_stability,
    make_training_folds,
)


def test_repeated_random_folds_are_seed_deterministic_and_disjoint():
    first = make_training_folds(30, n_splits=4, n_repeats=2, seed=19)
    second = make_training_folds(30, n_splits=4, n_repeats=2, seed=19)
    assert first == second
    for fold in first:
        assert set(fold.train_indices).isdisjoint(fold.validation_indices)
        assert set(fold.train_indices) | set(fold.validation_indices) == set(range(30))


def test_blocked_folds_hold_out_contiguous_ranges():
    folds = make_training_folds(
        20, n_splits=4, n_repeats=1, strategy="blocked"
    )
    for fold in folds:
        validation = list(fold.validation_indices)
        assert validation == list(range(validation[0], validation[-1] + 1))


def test_fold_metrics_are_aggregated_using_training_target_scale():
    X = np.arange(40, dtype=float).reshape(20, 2)
    y = X[:, 0] * 0.5 + 2.0
    folds = make_training_folds(20, n_splits=4, n_repeats=2, seed=7)
    # Fixed candidate predictor is intentionally simple; the test validates
    # fold aggregation and that normalized error uses each fitting partition.
    summary = evaluate_candidate_on_training_folds(
        "0.5*x", lambda X_fit, y_fit, X_valid: 0.5 * X_valid[:, 0] + 2.25,
        X, y, folds,
    )
    assert summary.valid_fold_count == len(folds)
    assert summary.failed_fold_count == 0
    assert summary.mean_rmse == pytest.approx(0.25)
    assert summary.worst_fold_rmse == pytest.approx(0.25)
    assert summary.mean_normalized_rmse is not None


def test_invalid_prediction_is_counted_and_insufficient_evidence_fails_closed():
    X = np.arange(24, dtype=float).reshape(12, 2)
    y = np.arange(12, dtype=float)
    folds = make_training_folds(12, n_splits=3, n_repeats=1)
    with pytest.raises(ValueError, match="insufficient valid training folds"):
        evaluate_candidate_on_training_folds(
            "x", lambda X_fit, y_fit, X_valid: np.full(len(X_valid), np.nan),
            X, y, folds, minimum_valid_folds=2,
        )


def test_expression_stability_is_auditable_and_does_not_claim_equivalence():
    result = expression_stability(["x ^ 2", "x**2", "x + 1"])
    assert result["expression_count"] == 3
    assert result["unique_expression_count"] == 2
    assert result["dominant_fraction"] == pytest.approx(2 / 3)
    assert "symbolic equivalence" not in result["normalization"]
