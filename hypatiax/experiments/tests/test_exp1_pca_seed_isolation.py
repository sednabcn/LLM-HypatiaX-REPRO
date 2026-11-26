"""Offline regression tests for isolated Exp1 PCA seed workers and Julia bootstrap."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/ci_runner_repro.yml"
sys.path.insert(0, str(ROOT))
from scripts.ci.aggregate_exp1_pca_seeds import aggregate_seed_artifacts


def _write_seed_result(path: Path, seed: int) -> None:
    rows = [
        {"equation_id": f"case-{i:02d}", "seed": seed,
         "split_protocol": {"name": "pca_40_60_pc1", "train_size": 80, "test_size": 120, "test_fraction": 0.6}}
        for i in range(74)
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows), encoding="utf-8")


def test_pca_seed_aggregate_requires_all_five_seed_stamped_74_case_results(tmp_path):
    artifacts, output = tmp_path / "artifacts", tmp_path / "canonical"
    for shard, seed in {0: 42, 1: 99, 2: 123, 3: 777, 4: 2024}.items():
        _write_seed_result(artifacts / f"results-exp1_pca-shard{shard}" / f"hypatiax_defi_benchmark_pca_results_seed{seed}.json", seed)
    manifest = aggregate_seed_artifacts(artifacts, output, run_id="1234", commit="abc")
    assert manifest["validated_seeds"] == [42, 99, 123, 777, 2024]
    assert manifest["validated_case_records"] == 370
    assert len(list(output.glob("hypatiax_defi_benchmark_pca_results_seed*.json"))) == 5
    assert json.loads((output / "pca_seed_aggregate_manifest.json").read_text())["status"] == "passed"


def test_pca_seed_aggregate_rejects_missing_worker_without_partial_promotion(tmp_path):
    artifacts, output = tmp_path / "artifacts", tmp_path / "canonical"
    for shard, seed in {0: 42, 1: 99, 2: 123, 3: 777}.items():
        _write_seed_result(artifacts / f"results-exp1_pca-shard{shard}" / f"hypatiax_defi_benchmark_pca_results_seed{seed}.json", seed)
    try:
        aggregate_seed_artifacts(artifacts, output)
    except ValueError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("aggregate accepted an incomplete four-worker set")
    assert not list(output.glob("*.json"))


def test_pca_workers_use_private_staging_and_only_aggregate_job_commits_results():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    expected_dest = '_DEST_PCA="' + "$" + "{RESULTS_DIR}/" + "$" + "{RESULT_SUBDIR}/_worker_shards/shard" + "$" + '{SHARD_INDEX}"'
    assert expected_dest in workflow
    assert "format('{0}/{1}/_worker_shards/shard{2}/'" in workflow
    commit = workflow.split("- name: Commit and push shard results to repo", 1)[1].split("- name: Verify results committed to repo", 1)[0]
    verify = workflow.split("- name: Verify results committed to repo", 1)[1].split("protocol30_aggregate:", 1)[0]
    assert "needs.plan.outputs.exp_id != 'exp1_pca_seeds'" in commit
    assert "needs.plan.outputs.exp_id != 'exp1_pca_seeds'" in verify
    aggregate = workflow.split("exp1_pca_seed_aggregate:", 1)[1].split("protocol30_aggregate:", 1)[0]
    assert "needs.worker.result == 'success'" in aggregate
    assert "pattern: results-exp1_pca-shard*" in aggregate
    assert "aggregate_exp1_pca_seeds.py" in aggregate
    assert "pca_seed_aggregate_manifest.json" in aggregate


def test_pythoncall_cache_probe_does_not_start_julia_before_julia_setup():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    probe = workflow.split("- name: Validate and activate shared Python environment", 1)[1].split("- name: Set up Julia 1.11", 1)[0]
    assert "importlib.util.find_spec('pysr')" in probe
    assert "import pysr" not in probe
    assert "PythonCall" in probe
    warmup = workflow.split("- name: Precompile Julia / SymbolicRegression (if needed)", 1)[1].split("- name: Verify Julia threads", 1)[0]
    assert "from juliacall import Main as jl" in warmup
    assert "using PythonCall" in warmup
    assert '("exp1_ablation", "exp1_pca", "exp1_pca_seeds")' in warmup
    assert "refusing to start shards" in warmup
