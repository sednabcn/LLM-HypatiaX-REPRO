"""Offline tests for independent V60 joint-basis evidence verification."""
import copy
import numpy as np

from hypatiax.tools.symbolic.v60_multi_basis_fitting import fit_native_multi_basis_candidates
from hypatiax.tools.symbolic.v60_multi_basis_validation import validate_native_multi_basis_candidates
from hypatiax.tools.symbolic.v60_multi_basis_evidence import verify_native_multi_basis_validation_evidence


def _fixture():
    X = np.asarray([[1., 2.], [2., 1.], [3., 2.], [4., 3.], [5., 4.], [6., 5.], [7., 3.], [8., 4.]])
    y = 2.0 * X[:, 0] - 0.5 * X[:, 1] + 7.0
    candidates = [
        {"candidate_id": "x-id", "normalized_expression": "x", "producer_provenance": [{"source": "template", "seed": 3}]},
        {"candidate_id": "y-id", "normalized_expression": "y", "producer_provenance": [{"source": "template", "seed": 3}]},
    ]
    fitted = fit_native_multi_basis_candidates(
        candidates, X, y, variable_names=("x", "y"), max_candidates=10,
        max_search_attempts=10,
    )
    validation = validate_native_multi_basis_candidates(
        fitted["fitted_candidate_groups"], candidates, X, y,
        variable_names=("x", "y"), split_protocol={"strategy": "kfold", "n_splits": 3},
        max_candidates=10, max_search_attempts=10,
    )
    return X, y, candidates, validation


def test_independent_verifier_recomputes_fold_evidence():
    X, y, candidates, validation = _fixture()
    audit = verify_native_multi_basis_validation_evidence(
        validation, candidates, X, y, variable_names=("x", "y"),
    )
    assert audit["verified_group_count"] == 1
    assert audit["rejected_group_count"] == 0
    assert audit["verified_candidate_groups"][0]["evidence_fingerprint"]
    assert audit["selection_performed"] is False
    assert audit["far_or_evaluation_data_used"] is False


def test_tampered_fold_metric_is_rejected():
    X, y, candidates, validation = _fixture()
    tampered = copy.deepcopy(validation)
    tampered["candidate_group_validation"][0]["folds"][0]["validation_rmse"] += 0.1
    audit = verify_native_multi_basis_validation_evidence(
        tampered, candidates, X, y, variable_names=("x", "y"),
    )
    assert audit["verified_group_count"] == 0
    assert audit["rejected_group_count"] == 1


def test_tampered_coefficients_are_rejected():
    X, y, candidates, validation = _fixture()
    tampered = copy.deepcopy(validation)
    tampered["candidate_group_validation"][0]["folds"][0]["coefficients"]["basis"][0] += 1.0
    audit = verify_native_multi_basis_validation_evidence(
        tampered, candidates, X, y, variable_names=("x", "y"),
    )
    assert audit["verified_group_count"] == 0


def test_far_evaluation_claim_fails_closed():
    X, y, candidates, validation = _fixture()
    tampered = dict(validation, far_or_evaluation_data_used=True)
    try:
        verify_native_multi_basis_validation_evidence(
            tampered, candidates, X, y, variable_names=("x", "y"),
        )
    except ValueError as exc:
        assert "exclude far/evaluation" in str(exc)
    else:
        raise AssertionError("far/evaluation data must be rejected")
