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
        "schema_version": "discovery_contract_v1",
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
        (lambda report: report.update(far_evaluation_used_for_selection=True), "far evaluation as unused"),
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


def test_soft_constraint_pareto_report_requires_consistent_audited_objective():
    report = _valid_report()
    report["provenance"].update({
        "selection_policy": "training_only_pareto_v5_soft_constraints",
        "soft_constraint_ids": ["soft_positive"],
        "soft_constraint_aggregation": "unweighted_mean_of_declared_violation_fractions",
        "objectives": ["mean_declared_soft_constraint_violation_fraction_min"],
    })
    candidate = report["candidates"][0]
    candidate["constraint_outcomes"].append({
        "constraint_id": "soft_positive", "status": "fail", "severity": "soft",
        "reason": "one sampled violation",
        "evidence": {"evaluation_count": 4, "violation_count": 1, "violation_fraction": 0.25},
    })
    candidate["metrics"]["training_validation"] = {
        "fold_metrics": [{"normalized_rmse": 0.2}, {"normalized_rmse": 0.3}],
        "expression_stability": {"status": "measured", "expression_count": 2, "dominant_fraction": 1.0},
    }
    candidate["metrics"]["pareto_selection"] = {
        "declared_soft_constraint_ids": ["soft_positive"],
        "mean_soft_constraint_violation_fraction": 0.25,
        "valid_normalized_fold_count": 2,
        "complexity_node_count": 4,
        "expression_stability_fraction": 1.0,
        "eligible_for_pareto": True, "eligibility_reasons": [],
        "objectives": {
            "mean_normalized_rmse": 0.25,
            "worst_normalized_rmse": 0.3,
            "complexity": 4.0,
            "negative_expression_stability": -1.0,
            "mean_soft_constraint_violation_fraction": 0.25,
        },
    }
    report["provenance"]["objectives"] = [
        "mean_normalized_rmse_min", "worst_normalized_rmse_min",
        "symbolic_operation_count_min", "expression_stability_fraction_max",
        "mean_declared_soft_constraint_violation_fraction_min",
    ]
    VALIDATOR._discovery_report_from_result({"discovery_report": report})
    candidate["metrics"]["pareto_selection"]["mean_soft_constraint_violation_fraction"] = 0.5
    with pytest.raises(ValueError, match="aggregate does not match"):
        VALIDATOR._discovery_report_from_result({"discovery_report": report})


def test_soft_constraint_pareto_report_rejects_missing_evidence_without_exclusion():
    report = _valid_report()
    report["provenance"].update({
        "selection_policy": "training_only_pareto_v5_soft_constraints",
        "soft_constraint_ids": ["soft_positive"],
        "soft_constraint_aggregation": "unweighted_mean_of_declared_violation_fractions",
        "objectives": ["mean_declared_soft_constraint_violation_fraction_min"],
    })
    report["candidates"][0]["metrics"]["pareto_selection"] = {
        "declared_soft_constraint_ids": ["soft_positive"],
        "mean_soft_constraint_violation_fraction": None,
        "eligible_for_pareto": True, "eligibility_reasons": [], "objectives": None,
    }
    with pytest.raises(ValueError, match="incomplete evidence lacks exclusion reason"):
        VALIDATOR._discovery_report_from_result({"discovery_report": report})


def _valid_pareto_report():
    report = _valid_report()
    report["provenance"].update({
        "selection_policy": "training_only_pareto_v3_stability",
        "selection_data_scope": "training_region_only",
        "objectives": [
            "mean_normalized_rmse_min",
            "worst_normalized_rmse_min",
            "symbolic_operation_count_min",
            "expression_stability_fraction_max",
        ],
    })
    first = report["candidates"][0]
    first["metrics"]["complexity"] = {"node_count": 4}
    first["metrics"]["training_validation"] = {
        "fold_metrics": [{"normalized_rmse": 0.1}, {"normalized_rmse": 0.3}],
        "expression_stability": {"status": "measured", "expression_count": 2, "dominant_fraction": 1.0},
    }
    first["metrics"]["pareto_selection"] = {
        "valid_normalized_fold_count": 2,
        "complexity_node_count": 4,
        "expression_stability_fraction": 1.0,
        "eligible_for_pareto": True,
        "eligibility_reasons": [],
        "objectives": {
            "mean_normalized_rmse": 0.2,
            "worst_normalized_rmse": 0.3,
            "complexity": 4.0,
            "negative_expression_stability": -1.0,
        },
    }
    second = dict(first)
    second["candidate_id"] = "candidate-2"
    second["metrics"] = {
        "complexity": {"node_count": 6},
        "training_validation": {
            "fold_metrics": [{"normalized_rmse": 0.3}, {"normalized_rmse": 0.5}],
            "expression_stability": {"status": "measured", "expression_count": 2, "dominant_fraction": 0.5},
        },
        "pareto_selection": {
            "valid_normalized_fold_count": 2,
            "complexity_node_count": 6,
            "expression_stability_fraction": 0.5,
            "eligible_for_pareto": True,
            "eligibility_reasons": [],
            "objectives": {
                "mean_normalized_rmse": 0.4,
                "worst_normalized_rmse": 0.5,
                "complexity": 6.0,
                "negative_expression_stability": -0.5,
            },
        }
    }
    report["candidates"].append(second)
    return report


def test_pareto_report_recomputes_front_and_deterministic_selected_candidate():
    report = _valid_pareto_report()
    report["pareto_candidate_ids"] = ["candidate-1"]
    report["selected_candidate_id"] = "candidate-1"
    VALIDATOR._discovery_report_from_result({"discovery_report": report})


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda report: report.update(pareto_candidate_ids=["candidate-1", "candidate-2"]),
            "recomputed objective front",
        ),
        (
            lambda report: report.update(selected_candidate_id="candidate-2"),
            "deterministic Pareto tie-break",
        ),
        (
            lambda report: report["candidates"][0]["metrics"]["pareto_selection"]["objectives"].update(
                mean_normalized_rmse=9.0
            ),
            "recomputed objective front",
        ),
        (
            lambda report: report["candidates"][0]["metrics"]["pareto_selection"].update(
                eligible_for_pareto=False
            ),
            "eligibility flag/reasons",
        ),
        (
            lambda report: report["candidates"][0]["metrics"]["training_validation"]["fold_metrics"][0].update(
                normalized_rmse=0.9
            ),
            "underlying training evidence",
        ),
        (
            lambda report: report["candidates"][0]["metrics"]["training_validation"]["expression_stability"].update(
                dominant_fraction=0.25
            ),
            "stability objective does not match training evidence",
        ),
        (
            lambda report: report["candidates"][0]["metrics"]["complexity"].update(node_count=99),
            "complexity objective does not match supplied complexity evidence",
        ),
    ],
)
def test_pareto_report_rejects_inconsistent_membership_objectives_or_winner(mutate, message):
    report = _valid_pareto_report()
    report["pareto_candidate_ids"] = ["candidate-1"]
    report["selected_candidate_id"] = "candidate-1"
    mutate(report)
    with pytest.raises(ValueError, match=message):
        VALIDATOR._discovery_report_from_result({"discovery_report": report})
