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


__all__ = ["ENVELOPE_SCHEMA", "seal_discovery_report", "verify_discovery_report_envelope"]
