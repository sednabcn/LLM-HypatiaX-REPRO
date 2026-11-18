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
