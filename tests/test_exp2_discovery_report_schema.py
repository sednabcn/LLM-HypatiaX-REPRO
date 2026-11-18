"""Offline contract tests for serialized Exp2 discovery reports."""
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "ci" / "validate_exp2_extrap_worker.py"
SPEC = importlib.util.spec_from_file_location("exp2_worker_validator", VALIDATOR_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)


def _valid_report():
    candidate = {
        "candidate_id": "candidate-1",
        "expression": "2.0*x",
        "normalized_expression": "2.0*x",
        "source": "pysr_search",
        "search_strategy": "baseline",
        "seed": 42,
        "constraint_outcomes": [
            {
                "constraint_id": "finite",
                "status": "pass",
                "severity": "hard",
                "reason": "",
                "evidence": {"sample_count": 16},
            }
        ],
        "metrics": {"training_validation": {"fold_metrics": []}},
        "rejection_reasons": [],
        "eligible": True,
    }
    return {
        "schema_version": "1.0",
        "status": "accepted",
        "candidates": [candidate],
        "selected_candidate_id": "candidate-1",
        "pareto_candidate_ids": ["candidate-1"],
        "failure_reasons": [],
        "provenance": {"selection_data_scope": "training_region_only"},
        "far_evaluation": {},
        "far_evaluation_used_for_selection": False,
    }


def test_valid_serialized_discovery_report_is_preserved():
    report = _valid_report()
    extracted = VALIDATOR._discovery_report_from_result(
        {"metadata": {"discovery_report": report}}
    )
    assert extracted == report


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda report: report.update(schema_version="2.0"), "unsupported.*schema_version"),
        (lambda report: report.update(status="success"), "unsupported.*status"),
        (lambda report: report.update(far_evaluation_used_for_selection=True), "far evaluation"),
        (lambda report: report.update(selected_candidate_id="missing"), "selected candidate"),
        (lambda report: report.update(pareto_candidate_ids=["missing"]), "Pareto IDs"),
        (lambda report: report["candidates"][0].update(seed=True), "seed must be an integer"),
        (lambda report: report["candidates"][0].update(eligible="yes"), "eligible must be boolean"),
        (lambda report: report["candidates"][0]["constraint_outcomes"][0].update(status="unknown-ish"), "unsupported status"),
        (lambda report: report["candidates"][0].update(rejection_reasons=[1]), "rejection_reasons"),
    ],
)
def test_invalid_discovery_report_is_rejected(mutate, message):
    report = _valid_report()
    mutate(report)
    with pytest.raises(ValueError, match=message):
        VALIDATOR._discovery_report_from_result({"discovery_report": report})


def test_legacy_result_without_typed_report_remains_supported():
    assert VALIDATOR._discovery_report_from_result({"success": True}) is None


def test_duplicate_candidate_ids_are_rejected():
    report = _valid_report()
    report["candidates"].append(dict(report["candidates"][0]))
    with pytest.raises(ValueError, match="unique candidate IDs"):
        VALIDATOR._discovery_report_from_result({"discovery_report": report})
