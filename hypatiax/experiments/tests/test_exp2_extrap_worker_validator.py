from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "ci" / "validate_exp2_extrap_worker.py"
SPEC = importlib.util.spec_from_file_location("exp2_extrap_worker_validator", SCRIPT)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)

METHODS = [f"method_{i}" for i in range(1, 7)]


def _report():
    candidate = {
        "candidate_id": "candidate-1",
        "expression": "x",
        "normalized_expression": "x",
        "source": "pysr_search",
        "search_strategy": "offline-test",
        "seed": 42,
        "constraint_outcomes": [],
        "metrics": {"pareto_selection": {
            "eligible_for_pareto": False,
            "eligibility_reasons": ["insufficient_fold_evidence"],
        }},
        "rejection_reasons": ["insufficient_fold_evidence"],
        "eligible": False,
    }
    return {
        "schema_version": "discovery_contract_v1",
        "status": "no_credible_candidate",
        "selected_candidate_id": None,
        "pareto_candidate_ids": [],
        "candidates": [candidate],
        "failure_reasons": ["No eligible candidate."],
        "provenance": {"selection_data_scope": "training_region_only"},
        "far_evaluation": {},
        "far_evaluation_used_for_selection": False,
    }


def _fixture(output_dir: Path, *, include_report: bool = True):
    marker = output_dir / "run-start"
    marker.write_text("start", encoding="utf-8")
    os.utime(marker, (1, 1))
    results = {}
    flat = []
    for method in METHODS:
        result = {"success": True, "formula": "x"}
        if include_report and method == METHODS[0]:
            result["discovery_report"] = _report()
        results[method] = result
        flat.append({
            "domain": "feynman_mechanics",
            "test": "equation_1",
            "method": method,
            "success": True,
            "extrap_r2_far": 0.9,
            "extrap_rmse_far": 0.1,
        })
    protocol = {
        "methods": METHODS,
        "total_tests": 1,
        "tests": [{
            "domain": "feynman_mechanics",
            "description": "equation_1",
            "results": results,
            "extrap_r2_far": {method: 0.9 for method in METHODS},
            "extrap_rmse_far": {method: 0.1 for method in METHODS},
            "extrap_n_train": 20,
            "extrap_n_test": 5,
        }],
    }
    protocol_path = output_dir / "protocol_core_extrap_fixture.json"
    protocol_path.write_text(json.dumps(protocol), encoding="utf-8")
    os.utime(protocol_path, None)
    benchmark_path = output_dir / "benchmark_results_extrap.json"
    benchmark_path.write_text(json.dumps(flat), encoding="utf-8")
    os.utime(benchmark_path, None)
    return marker


def test_worker_persists_complete_discovery_report_and_hashes_sidecar(tmp_path):
    marker = _fixture(tmp_path)
    summary = validator.validate_worker_outputs(tmp_path, marker, ["feynman_mechanics"])
    artifact = summary["discovery_report_artifact"]
    assert artifact["report_count"] == 1
    assert artifact["status"] == "present"
    sidecar = json.loads((tmp_path / artifact["file"]).read_text(encoding="utf-8"))
    assert sidecar["records"][0]["discovery_report"] == _report()
    assert sidecar["records"][0]["method"] == METHODS[0]
    assert sidecar["selection_boundary"]["far_evaluation_used_for_selection"] is False
    assert len(artifact["sha256"]) == 64


def test_worker_writes_explicit_empty_report_artifact_for_legacy_results(tmp_path):
    marker = _fixture(tmp_path, include_report=False)
    summary = validator.validate_worker_outputs(tmp_path, marker, ["feynman_mechanics"])
    artifact = summary["discovery_report_artifact"]
    assert artifact["report_count"] == 0
    assert artifact["status"] == "no_typed_discovery_reports"
    sidecar = json.loads((tmp_path / artifact["file"]).read_text(encoding="utf-8"))
    assert sidecar["records"] == []


def test_worker_rejects_report_that_does_not_seal_far_evaluation(tmp_path):
    marker = _fixture(tmp_path)
    protocol_path = tmp_path / "protocol_core_extrap_fixture.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    protocol["tests"][0]["results"][METHODS[0]]["discovery_report"][
        "far_evaluation_used_for_selection"
    ] = True
    protocol_path.write_text(json.dumps(protocol), encoding="utf-8")
    os.utime(protocol_path, None)
    try:
        validator.validate_worker_outputs(tmp_path, marker, ["feynman_mechanics"])
    except ValueError as exc:
        assert "far evaluation as unused" in str(exc)
    else:
        raise AssertionError("worker accepted a discovery report with a far-selection flag")
