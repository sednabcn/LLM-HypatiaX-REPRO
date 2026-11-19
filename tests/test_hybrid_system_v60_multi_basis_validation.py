"""Offline regression coverage for V60 multi-basis fold validation."""
import numpy as np

from hypatiax.tools.symbolic.v60_multi_basis_fitting import fit_native_multi_basis_candidates
from hypatiax.tools.symbolic.v60_multi_basis_validation import validate_native_multi_basis_candidates


def _candidate(candidate_id, expression):
    return {"candidate_id": candidate_id, "normalized_expression": expression,
            "producer_provenance": [{"source": "test_template", "seed": 3}]}


def _fixture():
    X = np.asarray([[1., 2.], [2., 1.], [3., 2.], [4., 3.], [5., 4.], [6., 5.]])
    y = 2.0 * X[:, 0] - 0.5 * X[:, 1] + 7.0
    candidates = [_candidate("x-id", "x"), _candidate("y-id", "y")]
    fitted = fit_native_multi_basis_candidates(
        candidates, X, y, variable_names=("x", "y"),
        max_candidates=10, max_search_attempts=10,
    )
    return X, y, candidates, fitted["fitted_candidate_groups"]


def test_joint_group_is_refit_independently_in_every_fold():
    X, y, candidates, groups = _fixture()
    audit = validate_native_multi_basis_candidates(
        groups, candidates, X, y, variable_names=("x", "y"),
        split_protocol={"strategy": "kfold", "n_splits": 3},
        max_candidates=10, max_search_attempts=10,
    )
    record = audit["candidate_group_validation"][0]
    assert record["validation_status"] == "validated"
    assert record["fold_count"] == 3
    for fold in record["folds"]:
        assert len(fold["coefficients"]["basis"]) == 2
        assert set(fold["training_row_indices"]).isdisjoint(fold["validation_row_indices"])
    assert record["validation_rmse_mean"] < 1e-10
    assert audit["selection_performed"] is False
    assert audit["far_or_evaluation_data_used"] is False


def test_group_expression_identity_is_verified():
    X, y, candidates, groups = _fixture()
    altered = [dict(groups[0], basis_expressions=["x", "x + y"])]
    audit = validate_native_multi_basis_candidates(
        altered, candidates, X, y, variable_names=("x", "y"),
        max_candidates=10, max_search_attempts=10,
    )
    assert audit["rejected_group_count"] == 1
    assert "lineage" in audit["rejected_candidate_groups"][0]["reason"]


def test_group_budget_is_reported_without_partial_validation():
    X, y, candidates, groups = _fixture()
    duplicated = groups * 3
    audit = validate_native_multi_basis_candidates(
        duplicated, candidates, X, y, variable_names=("x", "y"),
        max_candidates=1, max_search_attempts=1,
    )
    assert audit["attempted_group_count"] == 1
    assert audit["budget_truncated_count"] == len(duplicated) - 1


def test_non_finite_training_data_fails_closed():
    X, y, candidates, groups = _fixture()
    X[0, 0] = np.nan
    try:
        validate_native_multi_basis_candidates(
            groups, candidates, X, y, variable_names=("x", "y"),
            max_candidates=10, max_search_attempts=10,
        )
    except ValueError as exc:
        assert "training data must be finite" in str(exc)
    else:
        raise AssertionError("non-finite training data must be rejected")
