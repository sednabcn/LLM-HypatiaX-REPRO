"""Offline tests for recovery of already-completed Exp1 ablation workers."""
import json
from pathlib import Path

import pytest

from scripts.ci.validate_exp1_ablation_artifacts import SHARDS, validate_artifacts

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/ci_runner_repro.yml"


def _record(*, hypatia_llm_called=True, nollm_llm_called=False):
    return {
        "pysr_only": {"completed": True},
        "hypatia": {"completed": True, "llm_called": hypatia_llm_called},
        "hypatia_nollm": {"completed": True, "llm_called": nollm_llm_called},
    }


def _make_artifacts(root: Path):
    assignments = {
        0: (0, 1, 2),
        1: (12, 13, 14),
        2: (3, 4, 5),
        3: (6, 7, 8),
        4: (9, 10, 11),
    }
    for shard, task in SHARDS.items():
        folder = root / f"results-exp1_ablation-shard{shard}"
        folder.mkdir(parents=True)
        payload = {str(eq_id): _record() for eq_id in assignments[shard]}
        (folder / f"exp1_ablation_checkpoint_shard{shard}.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )


def test_recovery_validator_accepts_exact_complete_five_shard_set(tmp_path):
    _make_artifacts(tmp_path)
    errors, warnings, manifest = validate_artifacts(tmp_path)
    assert errors == []
    assert warnings == []
    assert manifest["expected_shards"] == 5
    assert sorted(
        eq_id
        for shard in manifest["shards"]
        for eq_id in shard["assigned_equation_ids"]
    ) == list(range(15))


def test_recovery_validator_rejects_missing_shard_without_filling_from_master(tmp_path):
    _make_artifacts(tmp_path)
    (tmp_path / "results-exp1_ablation-shard4" /
     "exp1_ablation_checkpoint_shard4.json").unlink()
    errors, _, _ = validate_artifacts(tmp_path)
    assert any("shard4" in error for error in errors)


def test_recovery_validator_rejects_incomplete_or_cross_shard_checkpoint(tmp_path):
    _make_artifacts(tmp_path)
    path = tmp_path / "results-exp1_ablation-shard4" / "exp1_ablation_checkpoint_shard4.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["9"]["hypatia_nollm"]["completed"] = False
    payload["0"] = _record()
    path.write_text(json.dumps(payload), encoding="utf-8")
    errors, _, _ = validate_artifacts(tmp_path)
    assert any("missing/incomplete arm" in error for error in errors)
    assert any("other shards" in error for error in errors)


def test_recovery_dispatch_is_aggregate_only_and_downloads_source_run_artifacts():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "exp1_ablation_recovery_aggregate:" in workflow
    job = workflow.split("exp1_ablation_recovery_aggregate:", 1)[1].split(
        "exp1_provenance_aggregate:", 1
    )[0]
    assert "github.event.inputs.aggregate_run_id != ''" in job
    assert "actions/download-artifact@v4" in job
    assert "run-id: ${{ github.event.inputs.aggregate_run_id }}" in job
    assert "validate_exp1_ablation_artifacts.py" in job
    assert "bash run_all.sh --step exp1_ablation_aggregate" in job
    assert "needs.worker.result" not in job
    assert "PYSR_SEED: \"42\"" in job
