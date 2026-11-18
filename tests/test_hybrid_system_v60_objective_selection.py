"""Offline regression coverage for native V60 objective verification and selection."""
from hypatiax.tools.symbolic.v60_objective_selection import (
    select_native_candidates_from_training_evidence,
)


def _candidate(candidate_id, expression):
    return {
        "candidate_id": candidate_id,
        "expression": expression,
        "normalized_expression": expression,
        "producer_provenance": [{"source": "domain_template", "seed": 7}],
    }


def _fold(index, rmse, nrmse):
    return {
        "fold": index,
        "training_row_indices": [0, 1, 2, 3],
        "validation_row_indices": [4 + index],
        "training_row_count": 4,
        "validation_row_count": 1,
        "validation_rmse": rmse,
        "validation_nrmse": nrmse,
        "coefficients": {"scale": 2.0, "intercept": 1.0},
    }


def _audits(validation_records):
    gates = {
        "gate_status": "completed",
        "training_or_far_data_used": False,
        "candidate_gates": [
            {"native_candidate_id": item["candidate_id"], "eligible": True, "gate_execution": "completed"}
            for item in validation_records
        ],
    }
    validation = {
        "validation_status": "completed",
        "validation_method": "training_only_refit_cross_validation",
        "far_or_evaluation_data_used": False,
        "fold_count": 2,
        "training_row_count": 6,
        "candidate_validation": validation_records,
    }
    return gates, validation


def _record(candidate_id, expression, rmse, nrmse):
    return {
        "candidate_id": candidate_id,
        "expression": expression,
        "validation_status": "validated",
        "fold_count": 2,
        "folds": [_fold(0, rmse, nrmse), _fold(1, rmse, nrmse)],
    }


def test_recomputes_objectives_and_selects_deterministic_pareto_candidate():
    candidates = [_candidate("simple", "x"), _candidate("complex", "x + x*x")]
    records = [_record("simple", "x", 0.2, 0.1), _record("complex", "x + x*x", 0.1, 0.05)]
    gates, validation = _audits(records)
    result = select_native_candidates_from_training_evidence(
        candidates, gates, validation, variable_names=("x",),
    )
    assert result["selection_status"] == "selected"
    assert result["selected_candidate_id"] == "complex"
    assert set(result["pareto_candidate_ids"]) == {"simple", "complex"}
    assert result["selection_performed"] is True
    assert result["far_or_evaluation_data_used"] is False
    assert result["objective_evidence"][0]["objective_evidence_sha256"]


def test_rejects_overlapping_fold_row_evidence():
    candidates = [_candidate("c1", "x")]
    records = [_record("c1", "x", 0.2, 0.1)]
    records[0]["folds"][0]["validation_row_indices"] = [0]
    gates, validation = _audits(records)
    result = select_native_candidates_from_training_evidence(
        candidates, gates, validation, variable_names=("x",),
    )
    assert result["selection_status"] == "no_credible_candidate"
    assert result["rejected_candidates"][0]["candidate_id"] == "c1"


def test_rejects_expression_or_candidate_identity_mismatch():
    candidates = [_candidate("c1", "x")]
    records = [_record("c1", "x + 1", 0.2, 0.1)]
    gates, validation = _audits(records)
    result = select_native_candidates_from_training_evidence(
        candidates, gates, validation, variable_names=("x",),
    )
    assert result["selection_status"] == "no_credible_candidate"
    assert "does not match" in result["rejected_candidates"][0]["reason"]


def test_uses_rmse_when_any_fold_has_undefined_normalized_error():
    candidates = [_candidate("c1", "x")]
    records = [_record("c1", "x", 0.2, None)]
    gates, validation = _audits(records)
    result = select_native_candidates_from_training_evidence(
        candidates, gates, validation, variable_names=("x",),
    )
    assert result["primary_error_objective"] == "mean_validation_rmse"
    assert result["selection_status"] == "selected"


def test_ineligible_candidate_cannot_enter_selection():
    candidates = [_candidate("c1", "x")]
    records = [_record("c1", "x", 0.2, 0.1)]
    gates, validation = _audits(records)
    gates["candidate_gates"][0]["eligible"] = False
    result = select_native_candidates_from_training_evidence(
        candidates, gates, validation, variable_names=("x",),
    )
    assert result["selection_status"] == "no_credible_candidate"
    assert result["selected_candidate_id"] is None


def test_incomplete_validation_is_not_selected():
    candidates = [_candidate("c1", "x")]
    gates, validation = _audits([])
    validation["validation_status"] = "budget_limited"
    result = select_native_candidates_from_training_evidence(
        candidates, gates, validation, variable_names=("x",),
    )
    assert result["selection_status"] == "insufficient_validation_evidence"
    assert result["selected_candidate_id"] is None
