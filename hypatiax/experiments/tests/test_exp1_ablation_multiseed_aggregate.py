"""Offline tests for the repeated-measures Exp1 five-seed aggregator."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/ci/aggregate_exp1_ablation_multiseed.py"
SPEC = importlib.util.spec_from_file_location("exp1_ablation_multiseed", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _fixtures():
    results, provenance = {}, {}
    for seed in MODULE.SEEDS:
        rows = {}
        for eq_id in range(MODULE.EQUATIONS):
            arms = {}
            for arm_index, arm in enumerate(MODULE.ARMS):
                far = 0.5 + (seed % 10) / 100 + eq_id / 1000 + arm_index / 100
                arms[arm] = {
                    "completed": True, "success": True,
                    "fit_status": "success", "evaluation_status": "success",
                    "test_r2": 0.9 + arm_index / 100,
                    "extrap_r2_far": far, "total_time_s": 10 + arm_index,
                }
            rows[str(eq_id)] = {"name": f"equation_{eq_id}", "domain": "test", **arms}
        results[seed] = rows
        provenance[seed] = {
            "seed": seed, "benchmark_script_sha256": "a" * 64,
            "source_revision": "deadbeef",
        }
    return results, provenance


def test_summary_preserves_repeated_measure_structure():
    results, provenance = _fixtures()
    summary, records = MODULE.build_summary(results, provenance)
    assert summary["n_equation_families"] == 15
    assert summary["n_equation_seed_units"] == 75
    assert summary["n_arm_records"] == 225
    assert len(records) == 225
    assert summary["methodology"]["inferential_tests"] == "none across seeds; descriptive mean and sample SD only"
    assert len(summary["seed_level_summary"]) == 5
    assert summary["seed_level_summary"]["42"]["paired_far_r2_delta"]["hypatia_vs_pysr"]["n_equations"] == 15


def test_summary_rejects_mixed_source_revisions():
    results, provenance = _fixtures()
    provenance[2024]["source_revision"] = "different"
    try:
        MODULE.build_summary(results, provenance)
    except ValueError as exc:
        assert "source revisions differ" in str(exc)
    else:
        raise AssertionError("mixed source revisions must be rejected")


def test_summary_preserves_failed_evaluations_as_missing_metrics():
    results, provenance = _fixtures()
    row = results[42]["0"]["hypatia"]
    row["success"] = False
    row["evaluation_status"] = "failed"
    summary, records = MODULE.build_summary(results, provenance)
    assert summary["seed_level_summary"]["42"]["arms"]["hypatia"]["far_r2_n"] == 14
    failed = [r for r in records if r["seed"] == 42 and r["equation_id"] == 0 and r["arm"] == "hypatia"]
    assert len(failed) == 1 and failed[0]["extrap_r2_far"] is None
