"""Regression tests for the isolated exp1b_pca five-seed runner."""

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[3]


def test_exp1b_pca_runner_is_standalone_and_shell_valid():
    run_all = (ROOT / "run_all.sh").read_text(encoding="utf-8")
    helper = ROOT / "scripts/ci/run_exp1b_pca.sh"
    assert 'run exp1b_pca "FIX-C3 DeFi seed sweep with PCA 40/60 split (five isolated seeds)" bash "${REPO_ROOT}/scripts/ci/run_exp1b_pca.sh"' in run_all
    checked = subprocess.run(["bash", "-n", str(helper)], capture_output=True, text=True)
    assert checked.returncode == 0, checked.stderr
    assert "bash -c" not in run_all[run_all.index('run exp1b_pca "'):run_all.index("\\nrun ", run_all.index('run exp1b_pca "'))]


def test_exp1b_pca_runs_all_five_seeds_with_fresh_rng_and_isolated_outputs():
    helper = (ROOT / "scripts/ci/run_exp1b_pca.sh").read_text(encoding="utf-8")
    for seed in (42, 99, 123, 777, 2024):
        assert str(seed) in helper
    for variable in ("DEFI_SEEDS", "PYSR_SEED", "EXPERIMENT_SEED", "NN_SEED", "HYPATIAX_ENGINE_SEED"):
        assert variable in helper
    for inherited_filter in ("TASK_IDS", "SHARD_IDS", "DOMAIN_FILTER", "DEFI_TASK_FILTER",
                             "ONE_EQUATION", "CASE_RANGE_START", "CASE_RANGE_END"):
        assert inherited_filter + '=""' in helper
    assert "--output-dir" in helper and "--force-fresh" in helper
    assert "seed${seed}" in helper
    assert "exp1b_pca_seed_outputs.py" in helper


def test_exp1b_pca_validator_requires_complete_seed_case_sets_and_provenance():
    helper = (ROOT / "scripts/ci/exp1b_pca_seed_outputs.py").read_text(encoding="utf-8")
    assert "SEEDS = (42, 99, 123, 777, 2024)" in helper
    assert "EXPECTED_CASES = 74" in helper
    assert "observed != {seed}" in helper
    assert "len(set(equation_ids))" not in helper  # validation uses the normalized equation_ids list
    assert "len(set(equation_ids)) != EXPECTED_CASES" in helper
    assert "expected_case_records" in helper
    assert "validated_case_records" in helper
    assert "source_files" in helper


def test_exp1b_pca_skip_guard_requires_all_five_seed_results_and_summaries():
    workflow = (ROOT / ".github/workflows/ci_runner_repro.yml").read_text()
    guard = workflow.split("- name: Check if exp1b_pca results already exist", 1)[1].split(
        "- name: Set up Python", 1
    )[0]
    for seed in (42, 99, 123, 777, 2024):
        assert f"hypatiax_defi_benchmark_pca_results_seed{seed}.json" in guard
    assert "split_protocol_disclosure.json" in guard
    assert "exp1b_pca_summary.json" in guard
    assert "MISSING=()" in guard
    assert '[[ ! -s "${FILE}" ]]' in guard
