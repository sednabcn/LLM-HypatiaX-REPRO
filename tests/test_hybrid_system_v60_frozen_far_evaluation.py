import copy
from hashlib import sha256
import json

import numpy as np
import pytest

from hypatiax.tools.symbolic.v60_frozen_far_evaluation import (
    evaluate_selected_native_candidate_on_far_set,
)


def _inputs():
    candidate = {
        "candidate_id": "candidate-x",
        "expression": "x",
        "normalized_expression": "x",
        "producer_provenance": [],
    }
    objective = {
        "candidate_id": "candidate-x",
        "expression": "x",
    }
    objective_fingerprint = sha256(
        json.dumps(objective, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    objective["objective_evidence_sha256"] = objective_fingerprint
    selection = {
        "schema": "v60_native_objective_selection_v1",
        "selection_status": "selected",
        "selection_performed": True,
        "far_or_evaluation_data_used": False,
        "selected_candidate_id": "candidate-x",
        "selected_expression": "x",
        "selected_objective_evidence_sha256": objective_fingerprint,
        "pareto_candidate_ids": ["candidate-x"],
        "objective_evidence": [objective],
    }
    return selection, [candidate]


def test_evaluates_only_the_frozen_selected_candidate():
    selection, candidates = _inputs()
    result = evaluate_selected_native_candidate_on_far_set(
        selection, candidates,
        np.array([[0.0], [1.0], [2.0], [3.0]]), np.array([1.0, 3.0, 5.0, 7.0]),
        np.array([[4.0], [5.0]]), np.array([9.0, 11.0]),
        variable_names=["x"],
    )
    assert result["evaluation_status"] == "completed"
    assert result["selected_candidate_id"] == "candidate-x"
    assert result["far_metrics"]["rmse"] == pytest.approx(0.0)
    assert result["selection_changed"] is False
    assert result["candidate_ranking_performed"] is False
    assert result["selection_snapshot_sha256"]


def test_rejects_unselected_or_far_contaminated_selection():
    selection, candidates = _inputs()
    selection["far_or_evaluation_data_used"] = True
    with pytest.raises(ValueError, match="far/evaluation data"):
        evaluate_selected_native_candidate_on_far_set(
            selection, candidates, [[0.0], [1.0], [2.0]], [1.0, 3.0, 5.0],
            [[4.0]], [9.0], variable_names=["x"],
        )


def test_rejects_candidate_expression_mismatch():
    selection, candidates = _inputs()
    candidates[0]["normalized_expression"] = "x + 1"
    with pytest.raises(ValueError, match="does not match frozen selection"):
        evaluate_selected_native_candidate_on_far_set(
            selection, candidates, [[0.0], [1.0], [2.0]], [1.0, 3.0, 5.0],
            [[4.0]], [9.0], variable_names=["x"],
        )


def test_rejects_nonfinite_far_rows_without_dropping_them():
    selection, candidates = _inputs()
    with pytest.raises(ValueError, match="finite"):
        evaluate_selected_native_candidate_on_far_set(
            selection, candidates, [[0.0], [1.0], [2.0]], [1.0, 3.0, 5.0],
            [[4.0], [float("nan")]], [9.0, 11.0], variable_names=["x"],
        )


def test_selection_audit_is_not_mutated():
    selection, candidates = _inputs()
    before = copy.deepcopy(selection)
    evaluate_selected_native_candidate_on_far_set(
        selection, candidates, [[0.0], [1.0], [2.0]], [1.0, 3.0, 5.0],
        [[4.0]], [9.0], variable_names=["x"],
    )
    assert selection == before
