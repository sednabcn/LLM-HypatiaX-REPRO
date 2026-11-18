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
    objective = {
        "candidate_group_id": "v60mb_group",
        "basis_candidate_ids": ["x-id", "y-id"],
        "basis_expressions": ["x", "y"],
        "evidence_fingerprint": "a" * 64,
        "mean_validation_rmse": 0.1,
        "std_validation_rmse": 0.01,
        "symbolic_complexity": 2,
        "primary_error_objective": "mean_validation_rmse",
        "objectives": {
            "mean_validation_rmse": 0.1,
            "std_validation_rmse": 0.01,
            "symbolic_complexity": 2,
        },
    }
    objective["objective_evidence_sha256"] = sha256(
        json.dumps(objective, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    return {
        "schema": "v60_native_multi_basis_objective_selection_v1",
        "selection_status": "selected",
        "selection_performed": True,
        "far_or_evaluation_data_used": False,
        "objective_evidence": [objective],
        "pareto_candidate_group_ids": ["v60mb_group"],
        "selected_candidate_group_id": "v60mb_group",
        "selected_basis_candidate_ids": ["x-id", "y-id"],
        "selected_basis_expressions": ["x", "y"],
        "selected_objective_evidence_sha256": objective["objective_evidence_sha256"],
    }


def test_worker_verifier_accepts_separately_embedded_multi_basis_selection():
    payload = copy.deepcopy(_envelope()["report"])
    payload["provenance"]["native_multi_basis_selection"] = _multi_basis_audit()
    envelope = seal_discovery_report(payload)
    verified = verify_discovery_report_envelope(envelope)
    assert verified["provenance"]["native_multi_basis_selection"]["selected_candidate_group_id"] == "v60mb_group"


def test_worker_verifier_rejects_multi_basis_selection_reference_tampering():
    payload = copy.deepcopy(_envelope()["report"])
    audit = _multi_basis_audit()
    audit["selected_candidate_group_id"] = "missing-group"
    payload["provenance"]["native_multi_basis_selection"] = audit
    envelope = seal_discovery_report(payload)
    with pytest.raises(ValueError, match="selected multi-basis group"):
        verify_discovery_report_envelope(envelope)


def test_worker_verifier_rejects_multi_basis_objective_digest_tampering():
    payload = copy.deepcopy(_envelope()["report"])
    audit = _multi_basis_audit()
    audit["objective_evidence"][0]["mean_validation_rmse"] = 9.0
    payload["provenance"]["native_multi_basis_selection"] = audit
    envelope = seal_discovery_report(payload)
    with pytest.raises(ValueError, match="objective evidence digest"):
        verify_discovery_report_envelope(envelope)
