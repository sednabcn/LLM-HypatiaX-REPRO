from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE = ROOT / ".github" / "scripts" / "result_subdir_map.py"
SPEC = importlib.util.spec_from_file_location("result_subdir_map", MODULE)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_exp1b_uses_the_canonical_deFi_benchmark_directory():
    assert mod.resolve_result_subdir("exp1b") == (
        "comparison_results/noise-noiseless/15"
    )


def test_exp1b_pca_uses_the_pca_portfolio_directory():
    assert mod.resolve_result_subdir("exp1b_pca") == (
        "comparison_results/noise-noiseless/15_pca"
    )


def test_noise_sweep_maps_to_single_canonical_directory():
    assert mod.resolve_result_subdir("suppB") == (
        "comparison_results/feynman-tests/noise-sweep"
    )


def test_unknown_experiment_does_not_guess_a_directory():
    assert mod.resolve_result_subdir("not-an-experiment") == ""


def test_exp1b_runner_propagates_errors_and_rejects_missing_artifacts():
    runner = ROOT / "run_all.sh"
    source = runner.read_text()
    start = source.index('run exp1b "')
    end = source.index('run portfolio "', start)
    block = source[start:end]
    assert "set -euo pipefail" in block
    assert "exp1b portfolio artifact missing or empty" in block
    assert "WARNING: portfolio_variance_v3c2.py exited non-zero" not in block
    assert "--resume" not in block
    assert 'HYPATIAX_RESULTS_DIR=' in block


def test_pipeline_noise_schedule_defaults_match_runner():
    runner = (ROOT / "run_all.sh").read_text()
    expected = "0.0,0.05,0.1,0.5,1.0"
    assert f'NOISE_LEVELS="${{NOISE_LEVELS:-{expected}}}"' in runner
    for workflow in (
        ROOT / ".github/workflows/ci_runner_repro.yml",
        ROOT / ".github/workflows/ci_pipeline_check.yml",
        ROOT / ".github/workflows/ci_pipeline_validate.yml",
    ):
        text = workflow.read_text()
        assert expected in text
        assert "0.0,0.5,1.0,5.0,10.0" not in text


def test_exp1b_contract_requires_seed_outputs_and_shared_baseline():
    runner = (ROOT / ".github/workflows/ci_runner_repro.yml").read_text()
    checker = (ROOT / ".github/workflows/ci_pipeline_check.yml").read_text()
    assert "PYSR_SEED=" in (ROOT / "run_all.sh").read_text()
    assert "portfolio_variance_defi_seed_sweep_seed" in runner
    assert "REPLACE: refreshing tracked exp1b per-seed portfolio artifact" in runner
    assert "hypatiax_defi_benchmark_v3_results.json" in checker
    assert "contract_missing" in checker
    assert "portfolio_variance_defi_seed_sweep_seed{seed}.json" in checker


def test_pipeline_self_dispatch_preserves_fail_closed_default():
    validate = (ROOT / ".github/workflows/ci_pipeline_validate.yml").read_text()
    assert "FAIL_ON_INCOMPLETE: ${{ github.event.inputs.fail_on_incomplete || 'true' }}" in validate
    assert "--field fail_on_incomplete=\"${{ github.event.inputs.fail_on_incomplete || 'true' }}\"" in validate


def test_required_run_all_benchmark_domains_do_not_swallow_failures():
    runner = (ROOT / "run_all.sh").read_text()
    for step in ("exp2_feynman", "exp2_feynman_pca_4060", "exp2_feynman_extrap", "exp2", "exp2_five", "extrap", "fixc3_rerun"):
        start = runner.index(f'run {step} "')
        next_run = runner.find("\nrun ", start + 1)
        block = runner[start: next_run if next_run >= 0 else len(runner)]
        assert "exited non-zero — continuing" not in block, step
    assert "exp1_pca worker(s) failed" in runner
