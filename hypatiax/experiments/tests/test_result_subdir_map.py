from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE = ROOT / ".github" / "scripts" / "result_subdir_map.py"
SPEC = importlib.util.spec_from_file_location("result_subdir_map", MODULE)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)



def test_exp1_provenance_has_an_isolated_result_directory():
    assert mod.resolve_result_subdir("exp1-provenance") == (
        "comparison_results/noise-noiseless/noiseless/defi/exp1-provenance"
    )


def test_exp1_provenance_is_one_fixed_five_seed_experiment():
    workflow = (ROOT / ".github/workflows/ci_runner_repro.yml").read_text()
    assert "- exp1-provenance" in workflow
    assert '"exp1-provenance":    5' in workflow
    assert 'required_seeds = ["42", "99", "123", "777", "2024"]' in workflow
    assert '"exp1-provenance":   [f"{d}_seed{s}" for s in SEEDS for d in DEFI_TASKS]' in workflow
    assert 'if [[ "${EXP}" == "exp1b_seeds" || "${EXP}" == "exp1-provenance" ]]' in workflow
    assert 'exp1-provenance shard and write provenance manifest' in workflow
    assert 'Aggregate and gate exp1-provenance five-seed run' in workflow
    assert 'validated_shard_count' in workflow
    assert 'expected_cases_per_seed' in workflow
    assert "run-${{ github.run_id }}-attempt-${{ github.run_attempt }}" in workflow
    assert workflow.count("github.event.inputs.experiment != 'exp1-provenance'") == 2
    assert "(github.event.inputs.experiment == 'exp1-provenance' || github.event.inputs.clean_llm_rerun == 'true') && 'false'" in workflow
    assert 'expected_domains = {"amm"' in workflow
    assert "result_sha256" in workflow and "protocol_config_sha256" in workflow
    assert '"expected_nshards": 5' in workflow
    assert "runtime_package_versions" in workflow
    assert "expected_tasks = {f\"{domain}_seed{seed}\" for domain in expected_domains}" in workflow
    assert "shards used different runtime package versions" in workflow
    protocol = (ROOT / "config/exp1_provenance.yaml").read_text()
    assert "id: exp1-provenance" in protocol
    assert "ordered: [42, 99, 123, 777, 2024]" in protocol
    assert "nshards: 5" in protocol
    assert "case_count_per_seed: 74" in protocol
    assert "total_expected_case_records: 370" in protocol
    assert "append_workflow_run_id_and_attempt: true" in protocol
    assert "artifact_retention_days: 90" in protocol
    assert "retention-days: ${{ github.event.inputs.experiment == 'exp1-provenance' && 90 || 30 }}" in workflow


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
    for step in ("exp2_feynman", "exp2_feynman_pca_4060", "exp2_feynman_extrap", "exp2", "exp2_five", "extrap"):
        start = runner.index(f'run {step} "')
        next_run = runner.find("\nrun ", start + 1)
        block = runner[start: next_run if next_run >= 0 else len(runner)]
        assert "exited non-zero — continuing" not in block, step
    start = runner.index("\nrun audit_nb06_fixc3_rerun")
    end = runner.find("\nrun ", start + 1)
    block = runner[start: end if end >= 0 else len(runner)]
    assert "exited non-zero — continuing" not in block
    assert "exp1_pca worker(s) failed" in runner

def test_pipeline_forwards_force_rerun_to_runner():
    validate = (ROOT / ".github/workflows/ci_pipeline_validate.yml").read_text()
    assert 'FORCE_RERUN: ${{ github.event.inputs.force_rerun || \'false\' }}' in validate
    assert '--field force_rerun="${FORCE_RERUN}"' in validate

def test_exp1b_pca_fails_closed_on_missing_required_inputs_and_outputs():
    runner = (ROOT / "run_all.sh").read_text()
    start = runner.index('run exp1b_pca "')
    end = runner.find("\nrun ", start + 1)
    block = runner[start: end if end >= 0 else len(runner)]
    assert "set -euo pipefail" in block
    assert "portfolio_variance_v3c2.py skipped" in block
    assert "::error::split_protocol_disclosure.json not found" in block
    assert "::error::exp1b_pca_summary.json not found" in block
    assert "HYPATIAX_RESULTS_DIR=" in block

def test_exp1b_pca_analysis_uses_the_actual_pca_benchmark_file():
    runner = (ROOT / "run_all.sh").read_text()
    analyzer = (ROOT / "hypatiax/experiments/benchmarks/portfolio_variance_v3c2.py").read_text()
    assert 'HYPATIAX_V3C3_RESULTS=' in runner
    assert "'HYPATIAX_V3C3_RESULTS'" in analyzer

def test_pipeline_check_defaults_to_fail_closed():
    check = (ROOT / ".github/workflows/ci_pipeline_check.yml").read_text()
    assert "FAIL_ON_INCOMPLETE: ${{ github.event.inputs.fail_on_incomplete || 'true' }}" in check


def test_required_exp1_pca_and_five_system_steps_fail_on_missing_outputs():
    runner = (ROOT / "run_all.sh").read_text()
    for step in ("exp1_pca", "exp1_five"):
        start = runner.index(f'run {step} "')
        end = runner.find("\nrun ", start + 1)
        block = runner[start: end if end >= 0 else len(runner)]
        assert "set -euo pipefail" in block
    assert "::error::exp1_pca produced no result JSON" in runner
    assert "::error::split_protocol_disclosure.json not found" in runner
    assert "::error::exp1_pca_summary.json not found" in runner
    assert "::error::exp1_five_results.json not produced" in runner
    assert "::error::performance/extrapolation sub-table source JSON missing" in runner
    assert "statistical_analysis.py exited non-zero" not in runner

def test_contract_gate_triggers_for_runner_changes_on_push_and_pull_request():
    workflow = (ROOT / ".github/workflows/ci_r2_policy.yml").read_text()
    for trigger in ("push:", "pull_request:"):
        start = workflow.index(trigger)
        end = workflow.find("\n  workflow_dispatch:", start)
        block = workflow[start: end if end >= 0 else len(workflow)]
        for path in (
            '"run_all.sh"',
            '".github/workflows/ci_runner_repro.yml"',
            '"config/exp1_provenance.yaml"',
            '".github/scripts/result_subdir_map.py"',
            '".github/workflows/ci_pipeline_check.yml"',
            '".github/workflows/ci_pipeline_validate.yml"',
        ):
            assert path in block, (trigger, path)

def test_workflow_cleanup_retains_history_for_90_days_by_default():
    cleanup = (ROOT / ".github/workflows/clean-old-workflows.yml").read_text()
    assert "default: '2160'" in cleanup
    assert "HOURS_THRESHOLD: ${{ github.event.inputs.hours_threshold || '2160' }}" in cleanup
    assert "const rawHours = process.env.HOURS_THRESHOLD || '2160'" in cleanup
    assert "const KEEP_HOURS = Number(rawHours)" in cleanup

def test_required_portfolio_ablation_instability_and_extrapolation_outputs_fail_closed():
    runner = (ROOT / "run_all.sh").read_text()
    assert "::error::required portfolio artifact" in runner
    assert "::error::required ablation artifact" in runner
    assert "::error::[instability]" in runner
    assert "::error::exp2_feynman_extrap produced no protocol_core_extrap_" in runner
    assert "::error::benchmark_results_extrap.json not found" in runner
    assert "merge_extrap_into_benchmark.py exited non-zero — ablation_paired.json may be incomplete" in runner


def test_ground_truth_leak_guard_fails_closed_when_any_target_is_missing():
    runner = (ROOT / "run_all.sh").read_text()
    start = runner.index('run gt_leak_guard "')
    end = runner.find("\nrun ", start + 1)
    block = runner[start: end if end >= 0 else len(runner)]
    assert block.count("Required gt_leak_guard target missing") == 3
    assert "Required gt_leak_guard target missing: hybrid_system_nn_defi_domain.py" in block
    assert "_FAIL=1" in block


def test_ground_truth_leak_guard_resolves_deep_defi_source_by_explicit_repo_path():
    runner = (ROOT / "run_all.sh").read_text()
    start = runner.index('run gt_leak_guard "')
    end = runner.find("\nrun ", start + 1)
    block = runner[start: end if end >= 0 else len(runner)]
    assert "_T3='${REPO_ROOT}/hypatiax/core/generation/hybrid_defi_system/hybrid_system_nn_defi_domain.py'" in block
    assert "-maxdepth 4" not in block


def test_exp1b_artifact_rescue_moves_do_not_suppress_failures():
    runner = (ROOT / "run_all.sh").read_text()
    for step in ("exp1b", "exp1b_pca"):
        start = runner.index(f'run {step} "')
        end = runner.find("\nrun ", start + 1)
        block = runner[start: end if end >= 0 else len(runner)]
        assert 'mv -v \\"\\$src\\" \\"\\$dst\\" || true' not in block



def test_defi_metric_guard_handles_none_invalid_and_nonfinite_scores():
    import ast
    import math

    source_path = (
        ROOT / "hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    helper = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_finite_metric"
    )
    isolated = ast.Module(body=[helper], type_ignores=[])
    namespace = {"_math": math}
    exec(compile(isolated, str(source_path), "exec"), namespace)
    finite_metric = namespace["_finite_metric"]

    assert finite_metric(None) is None
    assert finite_metric("not-a-score") is None
    assert finite_metric(float("nan")) is None
    assert finite_metric(float("inf")) is None
    assert finite_metric("-inf") is None
    assert finite_metric("0.875") == 0.875
    assert finite_metric(-0.25) == -0.25


def test_defi_case_metrics_use_safe_conversion_and_preserve_failed_arms():
    source = (
        ROOT / "hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py"
    ).read_text(encoding="utf-8")
    start = source.index("# ── Augment with extrapolation gap and stability score")
    end = source.index("# ── Print per-case summary", start)
    block = source[start:end]

    assert "tr_ = _finite_metric(res.get(\"train_r2\"))" in block
    assert "te_ = _finite_metric(res.get(\"test_r2\"))" in block
    assert "np.isnan(tr_)" not in block
    assert "np.isnan(te_)" not in block
    assert 'res["extrapolation_gap"]' in block
    assert 'res["stability_score"]' in block


def test_exp1_optional_analysis_script_does_not_fail_when_absent():
    runner = (ROOT / "run_all.sh").read_text(encoding="utf-8")
    start = runner.index('run exp1 "')
    end = runner.find("\nrun ", start + 1)
    block = runner[start : end if end >= 0 else len(runner)]

    # The exp1 body is embedded in an outer double-quoted bash -c string.
    # Escaping each dollar is required so expansion happens in the inner shell,
    # where ANALYSIS_DIR and _ANALYSIS_SCRIPT are defined.
    assert '_ANALYSIS_SCRIPT="\\${ANALYSIS_DIR}/statistical_analysis.py"' in block
    assert 'if [[ -f "\\${_ANALYSIS_SCRIPT}" ]]' in block
    assert "optional statistical_analysis.py not found" in block
    # Keep the fallback echo single-quoted so the outer bash -c string
    # does not reinterpret words or expand variables from the message.
    assert "echo 'INFO: optional statistical_analysis.py not found; using benchmark JSON/report.'" in block
    assert 'cd "${ANALYSIS_DIR}"' not in block


def test_all_portfolio_seed_parsers_allow_empty_unsharded_task_ids():
    runner = (ROOT / "run_all.sh").read_text()
    safe_parser = "sed -nE 's/^portfolio_seed([0-9]+)$/\\\\1/p'"
    assert runner.count(safe_parser) == 3
    exp1b_start = runner.index('run exp1b "')
    exp1b_end = runner.index('run portfolio "', exp1b_start)
    exp1b = runner[exp1b_start:exp1b_end]
    assert "running full default seed list" in exp1b
    assert "_SHARD_SEEDS='42,99,123,777,2024'" in exp1b
