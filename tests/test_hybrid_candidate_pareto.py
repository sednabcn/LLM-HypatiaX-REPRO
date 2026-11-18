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
            "1.0*gm_x_z",
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


def test_candidate_inner_target_std_scaling_is_refit_and_inverted_per_fold():
    x = np.linspace(1.0, 10.0, 36)
    X = x.reshape(-1, 1)
    y = 3e-8 * x
    folds = make_training_folds(
        len(y), n_splits=3, n_repeats=1,
        validation_fraction=0.2, seed=47,
    )

    summary = evaluate_hybrid_candidate_on_training_folds(
        "1.0*x",
        ["x"],
        ["x"],
        X,
        y,
        folds,
        minimum_valid_folds=3,
    )

    assert summary.valid_fold_count == 3
    assert summary.failed_fold_count == 0
    assert summary.mean_rmse < 1e-12


def _pareto_candidate(nested_evidence=None):
    from hypatiax.tools.symbolic.discovery_contracts import CandidateRecord

    metrics = {
        "training_validation": {
            "fold_metrics": [
                {"normalized_rmse": 0.1},
                {"normalized_rmse": 0.12},
            ],
            "expression_stability": {"status": "measured", "expression_count": 2, "dominant_fraction": 1.0},
        }
    }
    if nested_evidence is not None:
        metrics["nested_structure_evidence"] = nested_evidence
    return CandidateRecord(
        expression="x + 1.0",
        source="pysr_search",
        search_strategy="test",
        seed=7,
        metrics=metrics,
        eligible=True,
    )


def test_pareto_can_require_candidate_specific_nested_structure_evidence():
    from hypatiax.tools.symbolic.pareto_discovery import select_pareto_discovery_report

    report = select_pareto_discovery_report(
        [_pareto_candidate()],
        variable_names=["x"],
        minimum_valid_folds=2,
        require_nested_structure_evidence=True,
    )

    assert report.selected_candidate_id is None
    assert report.status == "insufficient_validation_evidence"
    audit = report.candidates[0].metrics["pareto_selection"]
    assert audit["nested_structure_evidence_required"] is True
    assert audit["nested_structure_evidence_passed"] is False


def test_pareto_accepts_unique_recurrent_nested_structure_crosswalk():
    from hypatiax.tools.symbolic.pareto_discovery import select_pareto_discovery_report

    nested = {
        "status": "matched_candidate_structure",
        "candidate_specific_nested_evidence": True,
        "far_test_data_used": False,
        "structure_id": "abc123",
        "recurrence_count": 2,
        "recurrence_fraction": 1.0,
    }
    report = select_pareto_discovery_report(
        [_pareto_candidate(nested)],
        variable_names=["x"],
        minimum_valid_folds=2,
        require_nested_structure_evidence=True,
    )

    assert report.selected_candidate_id == report.candidates[0].candidate_id
    audit = report.candidates[0].metrics["pareto_selection"]
    assert audit["nested_structure_evidence_passed"] is True
    assert report.provenance["nested_structure_evidence_required"] is True



class _FakeDiscoveryDeadline:
    def __init__(self, expired=False):
        self.is_expired = expired

    def expired(self):
        return self.is_expired


def test_fixed_candidate_fold_validation_does_not_start_after_deadline():
    from hypatiax.tools.symbolic.training_validation import (
        evaluate_candidate_on_training_folds,
    )

    X = np.arange(40, dtype=float).reshape(20, 2)
    y = X[:, 0]
    folds = make_training_folds(
        len(y), n_splits=2, n_repeats=1, validation_fraction=0.2, seed=53
    )
    deadline = _FakeDiscoveryDeadline(expired=True)
    calls = []

    with pytest.raises(TimeoutError, match="expired before fixed-candidate"):
        evaluate_candidate_on_training_folds(
            "x", lambda X_fit, y_fit, X_valid: calls.append(True),
            X, y, folds, minimum_valid_folds=2, budget_runtime=deadline,
        )
    assert calls == []


def test_fixed_candidate_fold_result_returned_after_deadline_is_rejected():
    from hypatiax.tools.symbolic.training_validation import (
        evaluate_candidate_on_training_folds,
    )

    X = np.arange(40, dtype=float).reshape(20, 2)
    y = X[:, 0]
    folds = make_training_folds(
        len(y), n_splits=2, n_repeats=1, validation_fraction=0.2, seed=59
    )
    deadline = _FakeDiscoveryDeadline()
    calls = []

    def late_predictor(X_fit, y_fit, X_valid):
        calls.append("predict")
        deadline.is_expired = True
        return np.zeros(len(X_valid), dtype=float)

    with pytest.raises(TimeoutError, match="returned after discovery"):
        evaluate_candidate_on_training_folds(
            "x", late_predictor, X, y, folds,
            minimum_valid_folds=2, budget_runtime=deadline,
        )
    assert calls == ["predict"]
