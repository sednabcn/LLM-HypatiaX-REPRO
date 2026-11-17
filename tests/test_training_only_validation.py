"""Offline regression coverage for training-only repeated validation."""
import numpy as np
import pytest

from hypatiax.tools.symbolic.training_validation import (
    evaluate_candidate_on_training_folds,
    evaluate_symbolic_candidate_on_training_folds,
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
        assert len(validation) == 4


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


def test_symbolic_candidate_refits_float_coefficients_inside_each_fold():
    X = np.linspace(1.0, 10.0, 40).reshape(-1, 1)
    y = 3.0 * X[:, 0]
    folds = make_training_folds(40, n_splits=4, n_repeats=2, seed=11)
    summary = evaluate_symbolic_candidate_on_training_folds(
        "2.0*x", ["x"], X, y, folds, max_nfev=100
    )
    assert summary.valid_fold_count == len(folds)
    assert summary.failed_fold_count == 0
    assert summary.mean_rmse < 1e-5
    assert all(item.fitted_expression is not None for item in summary.fold_metrics)


def test_symbolic_refit_uses_restricted_expression_parser():
    X = np.arange(20, dtype=float).reshape(-1, 1)
    y = X[:, 0]
    folds = make_training_folds(20, n_splits=2, n_repeats=1, seed=3)
    with pytest.raises(ValueError):
        evaluate_symbolic_candidate_on_training_folds(
            "__import__('os')", ["x"], X, y, folds
        )


def test_fold_fitted_expressions_can_be_summarized_for_stability():
    X = np.linspace(1.0, 8.0, 24).reshape(-1, 1)
    y = 4.0 * X[:, 0]
    folds = make_training_folds(24, n_splits=3, n_repeats=2, seed=5)
    summary = evaluate_symbolic_candidate_on_training_folds(
        "1.0*x", ["x"], X, y, folds
    )
    stability = expression_stability([
        item.fitted_expression for item in summary.fold_metrics
        if item.fitted_expression is not None
    ])
    assert stability["status"] == "measured"
    assert stability["expression_count"] == len(folds)


def test_fold_preprocessor_learns_log_flags_and_scales_from_fit_rows_only():
    from hypatiax.tools.symbolic.training_validation import FoldFeaturePreprocessor

    X_fit = np.array([
        [1e2, 2.0],
        [1e3, 4.0],
        [1e4, 6.0],
        [1e5, 8.0],
    ])
    preprocessor = FoldFeaturePreprocessor(["wide", "ordinary"])
    X_fit_transformed = preprocessor.fit_transform(X_fit)
    state_before = preprocessor.audit_state()

    # The validation extreme is transformed with frozen fitting-row state.
    X_validation = preprocessor.transform(np.array([[1e12, 10.0]]))
    state_after = preprocessor.audit_state()

    assert state_before == state_after
    assert state_before["fit_scope"] == "fold_fitting_rows_only"
    assert state_before["signed_log_columns"] == ["wide"]
    assert X_fit_transformed.shape == X_fit.shape
    assert X_validation.shape == (1, 2)


def test_fold_preprocessor_preserves_deterministic_raw_feature_schema():
    from hypatiax.tools.symbolic.training_validation import FoldFeaturePreprocessor

    X_fit = np.array([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]])
    first = FoldFeaturePreprocessor(["mass", "distance"])
    second = FoldFeaturePreprocessor(["mass", "distance"])

    first_out = first.fit_transform(X_fit)
    second_out = second.fit_transform(X_fit)

    assert first.get_feature_names_out() == ("mass", "distance")
    assert first.get_feature_names_out() == second.get_feature_names_out()
    np.testing.assert_allclose(first_out, second_out)


def test_fold_preprocessor_rejects_schema_mismatch_and_unfitted_transform():
    from hypatiax.tools.symbolic.training_validation import FoldFeaturePreprocessor

    preprocessor = FoldFeaturePreprocessor(["x"])
    with pytest.raises(RuntimeError, match="must be fitted"):
        preprocessor.transform(np.ones((2, 1)))
    preprocessor.fit(np.array([[1.0], [2.0]]))
    with pytest.raises(ValueError, match="feature schema"):
        preprocessor.transform(np.ones((2, 2)))
