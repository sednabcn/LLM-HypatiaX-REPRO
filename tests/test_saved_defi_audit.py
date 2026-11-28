"""Integration coverage for post-hoc audits of committed DeFi 40/60 outputs."""
from __future__ import annotations

from pathlib import Path

from hypatiax.experiments.audit.saved_results import audit_saved_files


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "hypatiax" / "data" / "results" / "comparison_results" / "noise-noiseless"
SEEDS = (42, 99, 123, 777, 2024)


def _random_files() -> list[Path]:
    directory = RESULTS / "noiseless" / "defi_random_4060"
    return [
        directory / "hypatiax_defi_benchmark_v3c_4060_results.json",
        *[
            directory / f"hypatiax_defi_benchmark_v3c_4060_results_seed{seed}.json"
            for seed in SEEDS if seed != 42
        ],
    ]


def _pca_files() -> list[Path]:
    directory = RESULTS / "15_pca"
    return [
        directory / f"hypatiax_defi_benchmark_pca_results_seed{seed}.json"
        for seed in SEEDS
    ]


def test_saved_random_4060_results_are_audited_without_rerun():
    report = audit_saved_files(
        _random_files(),
        experiment_id="exp1_4060_seeds",
        split_protocol="random_40_60",
    )
    assert report["case_count"] == 370
    assert report["coverage"]["formula_present"] == 370
    assert report["coverage"]["ground_truth_present"] == 370
    assert sum(report["symbolic_status_counts"].values()) == 370


def test_saved_pca_4060_results_are_audited_without_rerun():
    report = audit_saved_files(
        _pca_files(),
        experiment_id="exp1b_pca",
        split_protocol="pca_40_60",
    )
    assert report["case_count"] == 370
    assert report["coverage"]["formula_present"] == 370
    assert report["coverage"]["ground_truth_present"] == 370
    assert sum(report["symbolic_status_counts"].values()) == 370


def test_audit_does_not_use_predictive_metrics_as_symbolic_evidence():
    records = [{
        "equation_id": "example",
        "seed": 1,
        "results": {
            "hybrid": {
                "formula": "def formula(x):\n    return x",
                "test_r2": 1.0,
            }
        },
        "formula_context": {
            "variable_names": ["x"],
            "ground_truth_expression": "x + 1",
            "constants": {},
        },
    }]
    from hypatiax.experiments.audit.saved_results import audit_saved_records

    report = audit_saved_records(
        records,
        experiment_id="test",
        split_protocol="test",
    )
    case = report["cases"][0]
    assert case["symbolic_audit"]["status"] == "not_symbolically_equivalent"
    assert case["symbolic_audit"]["symbolically_equivalent"] is False
