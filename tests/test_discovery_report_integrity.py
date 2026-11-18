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
        "candidate_group_id": "v60mb_group", "basis_candidate_ids": ["x-id", "y-id"],
        "basis_expressions": ["x", "y"], "source_provenance": [],
        "folds": folds, "aggregates": aggregates, "training_row_count": 4,
        "variable_names": ["x", "y"], "split_strategy": "kfold",
    }
    digest = lambda value: sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    objective = {
        "candidate_group_id": "v60mb_group", "basis_candidate_ids": ["x-id", "y-id"],
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
        "objective_evidence": [objective], "pareto_candidate_group_ids": ["v60mb_group"],
        "selected_candidate_group_id": "v60mb_group", "selected_basis_candidate_ids": ["x-id", "y-id"],
        "selected_basis_expressions": ["x", "y"],
        "selected_objective_evidence_sha256": objective["objective_evidence_sha256"],
    }


def test_worker_verifier_accepts_embedded_multi_basis_selection():
    payload = copy.deepcopy(_envelope()["report"])
    payload["provenance"]["native_multi_basis_selection"] = _multi_basis_audit()
    verified = verify_discovery_report_envelope(seal_discovery_report(payload))
    assert verified["provenance"]["native_multi_basis_selection"]["selected_candidate_group_id"] == "v60mb_group"


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
    with pytest.raises(ValueError, match="fold-evidence fingerprint"):
        verify_discovery_report_envelope(seal_discovery_report(payload))
