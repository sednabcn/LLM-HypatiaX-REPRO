"""Offline integrity tests for versioned discovery-report worker envelopes."""
import copy

import pytest

from hypatiax.tools.symbolic.discovery_contracts import CandidateRecord, DiscoveryReport
from hypatiax.tools.symbolic.discovery_report_integrity import (
    ENVELOPE_SCHEMA,
    seal_discovery_report,
    verify_discovery_report_envelope,
)


def _envelope():
    candidate = CandidateRecord(
        expression="x",
        normalized_expression="x",
        source="domain_template",
        search_strategy="native_template",
        seed=7,
        eligible=True,
    )
    report = DiscoveryReport(
        status="provisional",
        candidates=(candidate,),
        selected_candidate_id=candidate.candidate_id,
        pareto_candidate_ids=(candidate.candidate_id,),
        provenance={"engine_version": "6.0.0"},
        far_evaluation={},
    )
    return seal_discovery_report(report)


def test_seal_and_verify_round_trip():
    envelope = _envelope()
    assert envelope["envelope_schema"] == ENVELOPE_SCHEMA
    assert verify_discovery_report_envelope(envelope)["status"] == "provisional"


def test_worker_verifier_detects_payload_tampering():
    envelope = _envelope()
    tampered = copy.deepcopy(envelope)
    tampered["report"]["status"] = "accepted"
    with pytest.raises(ValueError, match="integrity"):
        verify_discovery_report_envelope(tampered)


def test_worker_verifier_rejects_far_evaluation_contamination():
    envelope = _envelope()
    payload = copy.deepcopy(envelope["report"])
    payload["far_evaluation_used_for_selection"] = True
    unsigned = {"envelope_schema": envelope["envelope_schema"], "report": payload}
    from hashlib import sha256
    import json
    envelope["report"] = payload
    envelope["integrity_sha256"] = sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    with pytest.raises(ValueError, match="contamination"):
        verify_discovery_report_envelope(envelope)


def test_worker_verifier_rejects_unknown_envelope_fields():
    envelope = _envelope()
    envelope["extra"] = "not allowed"
    with pytest.raises(ValueError, match="unknown fields"):
        verify_discovery_report_envelope(envelope)


def _multi_basis_audit():
    from hashlib import sha256
    import json

    group_id = "v60mb_" + sha256(json.dumps(["x-id", "y-id"], separators=(",", ":")).encode()).hexdigest()[:20]
    folds = [
        {"fold": 0, "training_row_indices": [2, 3], "validation_row_indices": [0],
         "recomputed_rmse": 0.09, "recomputed_nrmse": None, "recomputed_r2": None,
         "recomputed_coefficients": [1.0, 1.0, 0.0], "recomputed_condition_number": 1.0},
        {"fold": 1, "training_row_indices": [0, 1], "validation_row_indices": [2],
         "recomputed_rmse": 0.11, "recomputed_nrmse": None, "recomputed_r2": None,
         "recomputed_coefficients": [1.0, 1.0, 0.0], "recomputed_condition_number": 1.0},
    ]
    aggregates = {
        "validation_rmse_mean": 0.1, "validation_rmse_std": 0.01,
        "validation_nrmse_mean": None, "validation_nrmse_std": None,
    }
    snapshot = {
        "folds": folds, "aggregates": aggregates, "training_row_count": 4,
        "variable_names": ["x", "y"], "split_strategy": "kfold",
    }
    fingerprint_payload = {
        "candidate_group_id": group_id, "basis_candidate_ids": ["x-id", "y-id"],
        "basis_expressions": ["x", "y"], "source_provenance": [],
        "folds": folds, "aggregates": aggregates, "training_row_count": 4,
        "variable_names": ["x", "y"], "split_strategy": "kfold",
    }
    digest = lambda value: sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    objective = {
        "candidate_group_id": group_id, "basis_candidate_ids": ["x-id", "y-id"],
        "basis_expressions": ["x", "y"], "source_provenance": [],
        "evidence_fingerprint": digest(fingerprint_payload), "verified_evidence_snapshot": snapshot,
        "fold_count": 2, "mean_validation_rmse": 0.1, "std_validation_rmse": 0.01,
        "mean_validation_nrmse": None, "std_validation_nrmse": None,
        "symbolic_complexity": 2, "objective_source": "independently_verified_training_only_joint_fold_evidence",
        "primary_error_objective": "mean_validation_rmse",
        "objectives": {"mean_validation_rmse": 0.1, "std_validation_rmse": 0.01, "symbolic_complexity": 2},
    }
    objective["objective_evidence_sha256"] = digest(objective)
    return {
        "schema": "v60_native_multi_basis_objective_selection_v1", "selection_status": "selected",
        "selection_method": "verified_joint_basis_training_evidence_pareto_then_deterministic_tiebreak",
        "primary_error_objective": "mean_validation_rmse",
        "objective_directions": {"mean_validation_rmse": "minimize", "std_validation_rmse": "minimize", "symbolic_complexity": "minimize"},
        "selection_performed": True, "far_or_evaluation_data_used": False,
        "objective_evidence": [objective], "pareto_candidate_group_ids": [group_id],
        "selected_candidate_group_id": group_id, "selected_basis_candidate_ids": ["x-id", "y-id"],
        "selected_basis_expressions": ["x", "y"],
        "selected_objective_evidence_sha256": objective["objective_evidence_sha256"],
    }


def test_worker_verifier_accepts_embedded_multi_basis_selection():
    payload = copy.deepcopy(_envelope()["report"])
    audit = _multi_basis_audit()
    payload["provenance"]["native_multi_basis_selection"] = audit
    verified = verify_discovery_report_envelope(seal_discovery_report(payload))
    assert verified["provenance"]["native_multi_basis_selection"]["selected_candidate_group_id"] == audit["selected_candidate_group_id"]


def test_worker_verifier_rejects_multi_basis_selected_reference_tampering():
    payload = copy.deepcopy(_envelope()["report"])
    audit = _multi_basis_audit()
    audit["selected_candidate_group_id"] = "missing-group"
    payload["provenance"]["native_multi_basis_selection"] = audit
    with pytest.raises(ValueError, match="deterministic Pareto tie-break"):
        verify_discovery_report_envelope(seal_discovery_report(payload))


def test_worker_verifier_rejects_multi_basis_objective_digest_tampering():
    payload = copy.deepcopy(_envelope()["report"])
    audit = _multi_basis_audit()
    audit["objective_evidence"][0]["mean_validation_rmse"] = 9.0
    payload["provenance"]["native_multi_basis_selection"] = audit
    with pytest.raises(ValueError, match="objective evidence digest"):
        verify_discovery_report_envelope(seal_discovery_report(payload))



def test_worker_verifier_rejects_forged_pareto_membership():
    payload = copy.deepcopy(_envelope()["report"])
    audit = _multi_basis_audit()
    audit["pareto_candidate_group_ids"] = []
    payload["provenance"]["native_multi_basis_selection"] = audit
    with pytest.raises(ValueError, match="Pareto membership/order"):
        verify_discovery_report_envelope(seal_discovery_report(payload))


def test_worker_verifier_rejects_objective_direction_tampering():
    payload = copy.deepcopy(_envelope()["report"])
    audit = _multi_basis_audit()
    audit["objective_directions"]["mean_validation_rmse"] = "maximize"
    payload["provenance"]["native_multi_basis_selection"] = audit
    with pytest.raises(ValueError, match="objective directions"):
        verify_discovery_report_envelope(seal_discovery_report(payload))


def test_worker_verifier_rejects_forged_fold_evidence_fingerprint():
    payload = copy.deepcopy(_envelope()["report"])
    audit = _multi_basis_audit()
    audit["objective_evidence"][0]["verified_evidence_snapshot"]["folds"][0]["recomputed_rmse"] = 7.0
    # Re-seal the objective record so the worker must still detect the independent fold digest mismatch.
    from hashlib import sha256
    import json
    item = audit["objective_evidence"][0]
    unsigned = {key: value for key, value in item.items() if key != "objective_evidence_sha256"}
    item["objective_evidence_sha256"] = sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    payload["provenance"]["native_multi_basis_selection"] = audit
    with pytest.raises(ValueError, match="RMSE aggregates do not reproduce"):
        verify_discovery_report_envelope(seal_discovery_report(payload))



def _native_final_model_audit():
    from hashlib import sha256
    import json

    model = {
        "family": "single_basis", "candidate_id": "candidate-x",
        "candidate_group_id": None, "basis_candidate_ids": ["candidate-x"],
        "basis_expressions": ["x"], "variable_names": ["x"],
        "fitted_expression": "(2)*(x) + (1)", "coefficients": [2.0, 1.0],
        "training_row_count": 8, "training_target_std": 4.0,
        "training_rmse": 0.0, "training_nrmse": 0.0, "training_r2": 1.0,
        "training_design_rank": 2, "training_design_condition_number": 3.0,
        "selection_metric": "cv_nrmse", "cross_validation_metric": 0.0,
        "cross_validation_metric_std": 0.0, "symbolic_complexity": 1,
    }
    digest = sha256(json.dumps(model, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return {
        "schema": "v60_native_final_model_v1", "execution_status": "selected",
        "selection_performed": True, "far_or_evaluation_data_used": False,
        "selected_model": model, "selected_model_sha256": digest,
        "objective_metric": "cv_nrmse",
        "candidate_options": [{
            "family": "single_basis", "candidate_id": "candidate-x",
            "expressions": ["x"], "cv_rmse": 0.0, "cv_nrmse": 0.0,
            "cv_rmse_std": 0.0, "cv_nrmse_std": 0.0, "complexity": 1,
        }],
    }


def test_worker_verifier_accepts_semantically_consistent_final_model():
    payload = copy.deepcopy(_envelope()["report"])
    payload["provenance"]["native_final_model"] = _native_final_model_audit()
    verified = verify_discovery_report_envelope(seal_discovery_report(payload))
    assert verified["provenance"]["native_final_model"]["execution_status"] == "selected"

def test_worker_verifier_rejects_rank_deficient_final_model():
    from hashlib import sha256
    import json

    payload = copy.deepcopy(_envelope()["report"])
    audit = _native_final_model_audit()
    audit["selected_model"]["training_design_rank"] = 1
    audit["selected_model_sha256"] = sha256(
        json.dumps(audit["selected_model"], sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    payload["provenance"]["native_final_model"] = audit
    with pytest.raises(ValueError, match="full column rank"):
        verify_discovery_report_envelope(seal_discovery_report(payload))


def test_worker_verifier_rejects_forged_cross_family_finalization_winner():
    payload = copy.deepcopy(_envelope()["report"])
    audit = _native_final_model_audit()
    audit["candidate_options"].append({
        "family": "multi_basis", "candidate_group_id": "group-y",
        "candidate_ids": ["candidate-x", "candidate-y"],
        "expressions": ["x", "x**2"],
        "cv_rmse": 0.0, "cv_nrmse": 0.0,
        "cv_rmse_std": 0.0, "cv_nrmse_std": 0.0, "complexity": 0,
    })
    # A re-sealed report must not be able to retain the old winner after the
    # serialized options now make the multi-basis family the deterministic winner.
    payload["provenance"]["native_final_model"] = audit
    with pytest.raises(ValueError, match="cross-family selection winner"):
        verify_discovery_report_envelope(seal_discovery_report(payload))


def test_worker_verifier_rejects_self_rehashed_formula_mismatch():
    from hashlib import sha256
    import json

    payload = copy.deepcopy(_envelope()["report"])
    audit = _native_final_model_audit()
    audit["selected_model"]["fitted_expression"] = "999*x"
    audit["selected_model_sha256"] = sha256(
        json.dumps(audit["selected_model"], sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    payload["provenance"]["native_final_model"] = audit
    with pytest.raises(ValueError, match="fitted expression does not reproduce"):
        verify_discovery_report_envelope(seal_discovery_report(payload))


def test_worker_verifier_rejects_undeclared_final_model_variable():
    from hashlib import sha256
    import json

    payload = copy.deepcopy(_envelope()["report"])
    audit = _native_final_model_audit()
    audit["selected_model"]["basis_expressions"] = ["z"]
    audit["selected_model"]["fitted_expression"] = "(2)*(z) + (1)"
    audit["selected_model_sha256"] = sha256(
        json.dumps(audit["selected_model"], sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    payload["provenance"]["native_final_model"] = audit
    with pytest.raises((ValueError, TypeError)):
        verify_discovery_report_envelope(seal_discovery_report(payload))


def _native_far_evaluation_audit(model_sha256):
    return {
        "schema": "v60_native_frozen_model_evaluation_v1",
        "evaluation_status": "completed",
        "evaluation_scope": "single_frozen_finalized_model",
        "selected_model_sha256": model_sha256,
        "far_set_sha256": "f" * 64,
        "far_row_count": 3,
        "far_metrics": {
            "rmse": 0.25,
            "nrmse_by_training_target_std": 0.0625,
            "mae": 0.2,
            "bias": -0.01,
            "r2": 0.99,
        },
        "selection_changed": False,
        "selection_performed": False,
        "far_or_evaluation_data_used_for_selection": False,
        "far_or_evaluation_data_used_for_retry": False,
        "candidate_ranking_performed": False,
    }


def test_worker_verifier_accepts_far_evaluation_bound_to_finalized_model():
    payload = copy.deepcopy(_envelope()["report"])
    final_model = _native_final_model_audit()
    payload["provenance"]["native_final_model"] = final_model
    payload["far_evaluation"] = _native_far_evaluation_audit(
        final_model["selected_model_sha256"]
    )
    verified = verify_discovery_report_envelope(seal_discovery_report(payload))
    assert verified["far_evaluation"]["selected_model_sha256"] == final_model["selected_model_sha256"]


def test_worker_verifier_rejects_far_evaluation_for_another_model():
    payload = copy.deepcopy(_envelope()["report"])
    payload["provenance"]["native_final_model"] = _native_final_model_audit()
    payload["far_evaluation"] = _native_far_evaluation_audit("a" * 64)
    with pytest.raises(ValueError, match="does not match the finalized native model"):
        verify_discovery_report_envelope(seal_discovery_report(payload))


def test_worker_verifier_rejects_malformed_far_metrics_and_row_count():
    payload = copy.deepcopy(_envelope()["report"])
    final_model = _native_final_model_audit()
    payload["provenance"]["native_final_model"] = final_model
    far = _native_far_evaluation_audit(final_model["selected_model_sha256"])
    far["far_metrics"]["rmse"] = float("nan")
    payload["far_evaluation"] = far
    with pytest.raises(ValueError, match="rmse must be finite"):
        verify_discovery_report_envelope(seal_discovery_report(payload))

    far = _native_far_evaluation_audit(final_model["selected_model_sha256"])
    far["far_row_count"] = True
    payload["far_evaluation"] = far
    with pytest.raises(ValueError, match="positive integer"):
        verify_discovery_report_envelope(seal_discovery_report(payload))


def test_worker_verifier_rejects_completed_far_evaluation_without_final_model():
    payload = copy.deepcopy(_envelope()["report"])
    payload["far_evaluation"] = _native_far_evaluation_audit("b" * 64)
    with pytest.raises(ValueError, match="requires the selected final-model audit"):
        verify_discovery_report_envelope(seal_discovery_report(payload))



def _reseal_final_model_digest(audit):
    from hashlib import sha256
    import json
    model = audit["selected_model"]
    audit["selected_model_sha256"] = sha256(
        json.dumps(model, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def test_worker_verifier_rejects_training_nrmse_inconsistent_with_rmse_and_target_scale():
    payload = copy.deepcopy(_envelope()["report"])
    audit = _native_final_model_audit()
    audit["selected_model"]["training_nrmse"] = 0.5
    _reseal_final_model_digest(audit)
    payload["provenance"]["native_final_model"] = audit
    with pytest.raises(ValueError, match="training NRMSE does not reproduce"):
        verify_discovery_report_envelope(seal_discovery_report(payload))


def test_worker_verifier_requires_null_training_nrmse_for_zero_variance_target():
    payload = copy.deepcopy(_envelope()["report"])
    audit = _native_final_model_audit()
    audit["selected_model"]["training_target_std"] = 0.0
    audit["selected_model"]["training_nrmse"] = 0.0
    _reseal_final_model_digest(audit)
    payload["provenance"]["native_final_model"] = audit
    with pytest.raises(ValueError, match="must be null for a zero-variance target"):
        verify_discovery_report_envelope(seal_discovery_report(payload))


def test_worker_verifier_rejects_negative_far_nrmse_and_non_hex_digest():
    payload = copy.deepcopy(_envelope()["report"])
    final_model = _native_final_model_audit()
    payload["provenance"]["native_final_model"] = final_model
    far = _native_far_evaluation_audit(final_model["selected_model_sha256"])
    far["far_metrics"]["nrmse_by_training_target_std"] = -0.1
    payload["far_evaluation"] = far
    with pytest.raises(ValueError, match="must be non-negative"):
        verify_discovery_report_envelope(seal_discovery_report(payload))

    far = _native_far_evaluation_audit(final_model["selected_model_sha256"])
    far["far_set_sha256"] = "g" * 64
    payload["far_evaluation"] = far
    with pytest.raises(ValueError, match="valid lowercase SHA-256"):
        verify_discovery_report_envelope(seal_discovery_report(payload))


def test_worker_verifier_rejects_mismatched_candidate_option_nrmse_nullability():
    payload = copy.deepcopy(_envelope()["report"])
    audit = _native_final_model_audit()
    audit["candidate_options"][0]["cv_nrmse_std"] = None
    payload["provenance"]["native_final_model"] = audit
    with pytest.raises(ValueError, match="NRMSE mean/std nullability must match"):
        verify_discovery_report_envelope(seal_discovery_report(payload))


def test_worker_verifier_rejects_unparseable_candidate_option_expression():
    payload = copy.deepcopy(_envelope()["report"])
    audit = _native_final_model_audit()
    audit["candidate_options"][0]["expressions"] = ["z"]
    payload["provenance"]["native_final_model"] = audit
    with pytest.raises((ValueError, TypeError)):
        verify_discovery_report_envelope(seal_discovery_report(payload))


def test_worker_verifier_rejects_single_basis_option_with_group_identity():
    payload = copy.deepcopy(_envelope()["report"])
    audit = _native_final_model_audit()
    audit["candidate_options"][0]["candidate_group_id"] = "unexpected-group"
    payload["provenance"]["native_final_model"] = audit
    with pytest.raises(ValueError, match="single-basis final-model option has invalid identity"):
        verify_discovery_report_envelope(seal_discovery_report(payload))


def test_worker_verifier_rejects_multi_basis_option_with_single_candidate_identity():
    payload = copy.deepcopy(_envelope()["report"])
    audit = _native_final_model_audit()
    audit["candidate_options"].append({
        "family": "multi_basis", "candidate_group_id": "group-y",
        "candidate_ids": ["candidate-x", "candidate-y"],
        "expressions": ["x", "x**2"],
        "cv_rmse": 1.0, "cv_nrmse": 1.0,
        "cv_rmse_std": 0.0, "cv_nrmse_std": 0.0, "complexity": 2,
        "candidate_id": "stray-single-id",
    })
    payload["provenance"]["native_final_model"] = audit
    with pytest.raises(ValueError, match="multi-basis final-model option has invalid basis lineage"):
        verify_discovery_report_envelope(seal_discovery_report(payload))


def test_worker_verifier_rejects_single_basis_model_with_mismatched_basis_identity():
    payload = copy.deepcopy(_envelope()["report"])
    audit = _native_final_model_audit()
    audit["selected_model"]["basis_candidate_ids"] = ["different-candidate"]
    _reseal_final_model_digest(audit)
    payload["provenance"]["native_final_model"] = audit
    with pytest.raises(ValueError, match="single-basis final model identity is inconsistent"):
        verify_discovery_report_envelope(seal_discovery_report(payload))


def test_worker_verifier_rejects_multi_basis_model_with_single_basis_shape():
    payload = copy.deepcopy(_envelope()["report"])
    audit = _native_final_model_audit()
    model = audit["selected_model"]
    model["family"] = "multi_basis"
    model["candidate_id"] = None
    model["candidate_group_id"] = "group-y"
    _reseal_final_model_digest(audit)
    payload["provenance"]["native_final_model"] = audit
    with pytest.raises(ValueError, match="multi-basis final model identity is inconsistent"):
        verify_discovery_report_envelope(seal_discovery_report(payload))
