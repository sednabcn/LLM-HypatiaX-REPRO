"""Versioned discovery-report envelopes for worker boundaries.

The envelope checksum covers the complete report payload. Far-evaluation
metrics may be attached after selection, but are rejected if they claim to
have influenced selection.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
from typing import Any, Mapping

from hypatiax.tools.symbolic.discovery_contracts import DiscoveryReport

ENVELOPE_SCHEMA = "v60_discovery_report_envelope_v1"


def _json_value(value: Any, path: str = "report") -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} contains a non-finite number")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} mapping keys must be strings")
            _json_value(item, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _json_value(item, f"{path}[{index}]")
        return
    raise TypeError(f"{path} contains unsupported type {type(value).__name__}")


def _canonical_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def seal_discovery_report(report: DiscoveryReport | Mapping[str, Any]) -> dict[str, Any]:
    """Create a JSON-safe, checksummed envelope from a typed report or mapping."""
    payload = report.to_dict() if isinstance(report, DiscoveryReport) else dict(report)
    _json_value(payload)
    if payload.get("schema_version") != "1.0":
        raise ValueError("unsupported discovery report schema_version")
    if payload.get("far_evaluation_used_for_selection") is not False:
        raise ValueError("discovery report must explicitly exclude far evaluation from selection")
    far = payload.get("far_evaluation", {})
    if not isinstance(far, Mapping):
        raise TypeError("far_evaluation must be a mapping")
    if far.get("used_for_selection", False) is not False:
        raise ValueError("far evaluation cannot be marked as used for selection")
    envelope = {
        "envelope_schema": ENVELOPE_SCHEMA,
        "report": payload,
    }
    envelope["integrity_sha256"] = _canonical_digest(envelope)
    return envelope


def verify_discovery_report_envelope(envelope: Mapping[str, Any]) -> dict[str, Any]:
    """Strictly verify worker input; return a detached JSON-compatible report."""
    if not isinstance(envelope, Mapping):
        raise TypeError("discovery report envelope must be a mapping")
    if set(envelope) != {"envelope_schema", "report", "integrity_sha256"}:
        raise ValueError("discovery report envelope has missing or unknown fields")
    if envelope.get("envelope_schema") != ENVELOPE_SCHEMA:
        raise ValueError("unsupported discovery report envelope schema")
    supplied = envelope.get("integrity_sha256")
    if not isinstance(supplied, str) or len(supplied) != 64:
        raise ValueError("invalid discovery report integrity digest")
    unsigned = {"envelope_schema": envelope["envelope_schema"], "report": envelope["report"]}
    _json_value(unsigned)
    if _canonical_digest(unsigned) != supplied:
        raise ValueError("discovery report integrity verification failed")
    report = envelope["report"]
    if not isinstance(report, Mapping):
        raise TypeError("discovery report payload must be a mapping")
    required = {
        "schema_version", "status", "selected_candidate_id", "pareto_candidate_ids",
        "candidates", "failure_reasons", "provenance", "far_evaluation",
        "far_evaluation_used_for_selection",
    }
    if set(report) != required:
        raise ValueError("discovery report payload has missing or unknown fields")
    if report["schema_version"] != "1.0":
        raise ValueError("unsupported discovery report schema_version")
    if report["far_evaluation_used_for_selection"] is not False:
        raise ValueError("far evaluation contamination flag must be false")
    if not isinstance(report["far_evaluation"], Mapping):
        raise TypeError("far_evaluation must be a mapping")
    if report["far_evaluation"].get("used_for_selection", False) is not False:
        raise ValueError("far evaluation cannot influence selection")
    candidates = report["candidates"]
    if not isinstance(candidates, list):
        raise TypeError("candidates must be a list")
    candidate_ids = []
    for candidate in candidates:
        if not isinstance(candidate, Mapping) or not isinstance(candidate.get("candidate_id"), str):
            raise TypeError("each candidate must contain a string candidate_id")
        candidate_ids.append(candidate["candidate_id"])
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("candidate IDs must be unique")
    selected = report["selected_candidate_id"]
    if selected is not None and selected not in candidate_ids:
        raise ValueError("selected candidate must exist in report candidates")
    pareto = report["pareto_candidate_ids"]
    if not isinstance(pareto, list) or not set(pareto).issubset(set(candidate_ids)):
        raise ValueError("Pareto IDs must reference report candidates")
    return json.loads(json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


__all__ = ["ENVELOPE_SCHEMA", "seal_discovery_report", "verify_discovery_report_envelope", "build_native_discovery_report"]


def build_native_discovery_report(
    proposals: list[Mapping[str, Any]],
    gate_audit: Mapping[str, Any],
    validation_audit: Mapping[str, Any],
    selection_audit: Mapping[str, Any],
    *,
    run_context: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a versioned report from native V60 evidence without promoting it
    to the V50.2 production result.
    """
    from hypatiax.tools.symbolic.discovery_contracts import CandidateRecord, DiscoveryReport

    gate_by_id = {
        item.get("native_candidate_id"): item
        for item in gate_audit.get("candidate_gates", [])
        if isinstance(item, Mapping)
    }
    validation_by_id = {
        item.get("native_candidate_id"): item
        for item in validation_audit.get("candidate_validation", [])
        if isinstance(item, Mapping)
    }
    objective_by_id = {
        item.get("candidate_id"): item
        for item in selection_audit.get("objective_evidence", [])
        if isinstance(item, Mapping)
    }
    records = []
    native_to_report = {}
    for proposal in proposals:
        native_id = proposal.get("candidate_id")
        lineage = proposal.get("producer_provenance") or [{}]
        producer = lineage[0] if isinstance(lineage, list) else {}
        source = producer.get("source", "unknown")
        if source not in {"llm_proposal", "domain_template", "pysr_search", "residual_search", "unknown"}:
            source = "unknown"
        strategy = producer.get("search_strategy", "native_template")
        seed = producer.get("seed", 0)
        if not isinstance(seed, int) or isinstance(seed, bool):
            seed = 0
        gate = gate_by_id.get(native_id, {})
        validation = validation_by_id.get(native_id, {})
        objective = objective_by_id.get(native_id, {})
        metrics = {}
        if isinstance(validation, Mapping):
            metrics["training_validation"] = dict(validation)
        if isinstance(objective, Mapping):
            metrics["training_objectives"] = dict(objective)
        record = CandidateRecord(
            expression=str(proposal.get("expression") or proposal.get("normalized_expression") or ""),
            normalized_expression=str(proposal.get("normalized_expression") or proposal.get("expression") or ""),
            source=source,
            search_strategy=str(strategy),
            seed=seed,
            metrics=metrics,
            rejection_reasons=tuple(gate.get("rejection_reasons", ())) if isinstance(gate, Mapping) else (),
            eligible=bool(gate.get("eligible", False)) if isinstance(gate, Mapping) else False,
        )
        records.append(record)
        native_to_report[native_id] = record.candidate_id

    selected_native = selection_audit.get("selected_candidate_id")
    selected_report = native_to_report.get(selected_native)
    pareto_report = [
        native_to_report[item]
        for item in selection_audit.get("pareto_candidate_ids", [])
        if item in native_to_report
    ]
    selected = selection_audit.get("selection_status") == "selected" and selected_report is not None
    status = "provisional" if selected else "no_credible_candidate"
    failures = []
    if not selected:
        reason = selection_audit.get("reason") or selection_audit.get("selection_status") or "native selection produced no candidate"
        failures.append(str(reason))
    report = DiscoveryReport(
        status=status,
        candidates=tuple(records),
        selected_candidate_id=selected_report if selected else None,
        pareto_candidate_ids=tuple(pareto_report),
        failure_reasons=tuple(failures),
        provenance={
            "engine_version": "6.0.0",
            "implementation_mode": "native_v60_audit_with_v50_2_compatibility",
            "native_v60_pipeline": False,
            "run_context": dict(run_context),
            "native_selection_status": selection_audit.get("selection_status"),
            "compatibility_baseline": "hybrid_system_v50_2",
        },
        far_evaluation={},
    )
    return seal_discovery_report(report)


__all__ = ["ENVELOPE_SCHEMA", "seal_discovery_report", "verify_discovery_report_envelope", "build_native_discovery_report"]
