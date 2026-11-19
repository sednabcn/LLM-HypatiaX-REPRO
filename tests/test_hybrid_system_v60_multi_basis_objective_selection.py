"""Offline regression tests for V60 joint-basis evidence Pareto selection."""
import copy

import numpy as np

from hypatiax.tools.symbolic.v60_multi_basis_fitting import fit_native_multi_basis_candidates
from hypatiax.tools.symbolic.v60_multi_basis_validation import validate_native_multi_basis_candidates
from hypatiax.tools.symbolic.v60_multi_basis_evidence import verify_native_multi_basis_validation_evidence
from hypatiax.tools.symbolic.v60_multi_basis_objective_selection import (
    select_native_multi_basis_candidates_from_verified_evidence,
)


def _fixture():
    X = np.asarray([
        [1., 2.], [2., 1.], [3., 2.], [4., 3.],
        [5., 4.], [6., 5.], [7., 3.], [8., 4.],
    ])
    y = 2.0 * X[:, 0] - 0.5 * X[:, 1] + 7.0
    candidates = [
        {"candidate_id": "x-id", "normalized_expression": "x",
         "producer_provenance": [{"source": "template", "search_strategy": "template", "seed": 3, "original_expression": "x"}]},
        {"candidate_id": "y-id", "normalized_expression": "y",
         "producer_provenance": [{"source": "template", "search_strategy": "template", "seed": 3, "original_expression": "y"}]},
    ]
    fit = fit_native_multi_basis_candidates(
        candidates, X, y, variable_names=("x", "y"),
        max_candidates=10, max_search_attempts=10, max_basis_terms=2,
    )
    validation = validate_native_multi_basis_candidates(
        fit["fitted_candidate_groups"], candidates, X, y,
        variable_names=("x", "y"),
        split_protocol={"strategy": "kfold", "n_splits": 3},
        max_candidates=10, max_search_attempts=10,
    )
    evidence = verify_native_multi_basis_validation_evidence(
        validation, candidates, X, y, variable_names=("x", "y"),
    )
    gate = {
        "gate_status": "completed", "training_or_far_data_used": False,
        "candidate_gates": [
            {"native_candidate_id": item["candidate_id"], "eligible": True, "gate_execution": "completed"}
            for item in candidates
        ],
    }
    return candidates, gate, fit, validation, evidence


def _select(fixture):
    candidates, gate, fit, validation, evidence = fixture
    return select_native_multi_basis_candidates_from_verified_evidence(
        candidates, gate, fit, validation, evidence, variable_names=("x", "y"),
    )


def test_selects_only_independently_verified_joint_groups():
    fixture = _fixture()
    audit = _select(fixture)
    assert audit["selection_status"] == "selected"
    assert audit["selected_basis_candidate_ids"] == ["x-id", "y-id"]
    assert audit["selection_performed"] is True
    assert audit["far_or_evaluation_data_used"] is False
    assert audit["objective_evidence"][0]["evidence_fingerprint"]


def test_tampered_verified_objective_is_rejected():
    fixture = list(_fixture())
    fixture[4] = copy.deepcopy(fixture[4])
    fixture[4]["verified_candidate_groups"][0]["objective_evidence"]["validation_rmse_mean"] += 1.0
    audit = _select(tuple(fixture))
    assert audit["selection_status"] == "no_credible_candidate"
    assert audit["rejected_group_count"] == 1


def test_gate_ineligible_basis_prevents_group_selection():
    fixture = list(_fixture())
    fixture[1] = copy.deepcopy(fixture[1])
    fixture[1]["candidate_gates"][0]["eligible"] = False
    audit = _select(tuple(fixture))
    assert audit["selection_status"] == "no_credible_candidate"


def test_float_row_indices_fail_closed_even_if_verifier_artifact_is_forged():
    fixture = list(_fixture())
    fixture[3] = copy.deepcopy(fixture[3])
    fixture[3]["candidate_group_validation"][0]["folds"][0]["training_row_indices"][0] = 0.0
    # The selector must reject the altered validation record against the
    # verifier's independently recorded integer row-index evidence.
    audit = _select(tuple(fixture))
    assert audit["selection_status"] == "no_credible_candidate"
