"""Offline contract tests for exp1b's Portfolio-filtered multi-seed protocol."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "run_all.sh"
BENCHMARK = ROOT / "hypatiax/experiments/benchmarks/portfolio_variance_v3c2.py"
WORKFLOW = ROOT / ".github/workflows/ci_runner_repro.yml"


def test_exp1b_benchmark_uses_its_declared_portfolio_case_filter():
    source = RUNNER.read_text()
    start = source.index('run exp1b "')
    end = source.index('\nrun portfolio "', start)
    block = source[start:end]

    assert 'DEFI_TASK_FILTER="Portfolio"' in block
    assert 'DEFI_SEEDS="' + chr(92) + '$' + '{_SHARD_SEEDS}"' in block
    assert 'PYSR_SEED="' + chr(92) + '$' + '{_SEEDS[0]}"' in block


def test_exp1b_sweep_only_does_not_run_the_seed42_single_case_twice():
    source = BENCHMARK.read_text()
    tree = ast.parse(source)
    nodes = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.If)
        and isinstance(n.test, ast.BoolOp)
        and any(
            isinstance(v, ast.Name) and v.id == "PV_SWEEP_ONLY"
            for v in n.test.values
        )
    ]
    assert nodes
    assert any(
        any(isinstance(call, ast.Call) for call in ast.walk(node))
        and "skipping the separate seed-42 single-case rerun" in ast.get_source_segment(source, node)
        for node in nodes
    )


def test_exp1b_per_seed_rows_preserve_llm_request_and_formula_provenance():
    source = BENCHMARK.read_text()
    for field in (
        "llm_code",
        "llm_called",
        "bypass_kind",
        "llm_source",
        "llm_timeout_s",
        "llm_temperature_requested",
        "llm_temperature_sent",
    ):
        assert f"'{field}'" in source


def test_exp1b_sweep_persists_exact_shared_split_and_formula_context():
    source = BENCHMARK.read_text()
    assert "'formula_context': {" in source
    assert "'llm_model': getattr(_bench, 'LLM_MODEL', None)" in source
    assert "'audit_data': {" in source
    for field in ("X_train", "y_train", "X_test", "y_test"):
        assert f"'{field}'" in source
    assert "'split_details': split_details" in source
    assert "'seeds_run': [int(seed) for seed in SEEDS]" in source


def test_exp1b_default_split_is_not_silently_relabelled_as_pca():
    source = BENCHMARK.read_text()
    assert "PCA_PORTFOLIO_SWEEP = os.environ.get" in source
    assert "if PCA_PORTFOLIO_SWEEP:" in source
    assert "first_feature_percentile_split(X, y, return_metadata=return_metadata)" in source
    assert "'v3c3-pca' if PCA_PORTFOLIO_SWEEP else 'v3c3'" in source


def test_exp1b_workflow_requires_fresh_shard_benchmark_and_portfolio_outputs():
    workflow = WORKFLOW.read_text()
    assert "exp1b fresh benchmark output missing" in workflow
    assert "Never replace it with the old canonical seed file." in workflow
    assert "hypatiax_defi_benchmark_v3_results_seed" + '$' + "{_seed}_shard" + '$' + "{SHARD_INDEX}.json" in workflow
    assert "portfolio_variance_defi_seed_sweep_seed" + '$' + "{_seed}_shard" + '$' + "{SHARD_INDEX}.json" in workflow
    assert "REFRESH: published fresh" in workflow
    assert 'git checkout -- "' + '$' + '{_canonical}"' not in workflow


def test_exp1b_sweep_records_selected_route_and_explicit_nn_seed():
    source = BENCHMARK.read_text()
    assert "nn_seed=nn_seed" in source
    for field in (
        "'nn_seed'", "'test_r2'", "'train_r2_source'",
        "'route_execution_status'", "'nn_abstained'",
        "'nn_selected_model'", "'nn_edge_r2'", "'ridge_edge_r2'",
        "'score_semantics'",
    ):
        assert field in source


def test_exp1b_runtime_output_paths_are_expanded_not_literal_directory_names():
    source = RUNNER.read_text()
    start = source.index('run exp1b "')
    end = source.index('\nrun portfolio "', start)
    block = source[start:end]

    # The command is nested in bash -c "...": escape for the parent shell, but
    # use double quotes in the child so RESULTS_DIR expands at execution time.
    assert 'dest15="' + chr(92) + '$' + '{RESULTS_DIR}/comparison_results/noise-noiseless/15"' in block
    assert '_PVA_DIR="' + chr(92) + '$' + '{RESULTS_DIR}/portfolio_variance_audit"' in block
    assert "dest15='" + chr(92) + '$' + '{RESULTS_DIR}' not in block
    assert "_PVA_DIR='" + chr(92) + '$' + '{RESULTS_DIR}' not in block


def test_exp1b_store_step_requires_fresh_benchmark_and_refreshes_tracked_sweep():
    workflow = WORKFLOW.read_text()
    store_start = workflow.index("- name: Store results in canonical RESULT_SUBDIR")
    store_end = workflow.index("\n      - name:", store_start + 10)
    store = workflow[store_start:store_end]
    pva_start = store.index('PVA_DIR="')
    pva_end = store.index('if [[ "' + '$' + '{EXP:-}" == "exp1b_seeds"', pva_start)
    pva = store[pva_start:pva_end]

    assert "exp1b fresh benchmark output missing" in store
    assert "Never replace it with the old canonical seed file." in store
    assert 'cp -f "' + '$' + '{src}" "' + '$' + '{dest_f}"' in pva
    assert "REFRESH: published fresh" in pva
    assert "SKIP:" not in pva


def test_exp1b_verification_checks_fresh_seed_and_portfolio_provenance():
    workflow = WORKFLOW.read_text()
    start = workflow.index("- name: Verify exp1b output files exist")
    end = workflow.index("\n      - name:", start + 10)
    verify = workflow[start:end]

    for token in (
        r"portfolio_seed(\d+)",
        "portfolio_variance_defi_seed_sweep_seed",
        '"seeds_run"',
        '"nn_seed"',
        '"test_r2"',
        '"far_r2"',
        '"route_execution_status"',
        '"score_semantics"',
        "far_r2 must remain an alias of test_r2",
    ):
        assert token in verify


def test_exp1b_seeds_planner_uses_one_worker_per_configured_seed():
    workflow = WORKFLOW.read_text()
    assert "DEFAULT_SEEDS" in workflow and "99,123,777,2024" in workflow
    assert "N_SHARDS = max(1, len(SEEDS))" in workflow
    assert '"exp1b_seeds":       [f"{d}_seed{s}" for s in SEEDS for d in DEFI_TASKS]' in workflow

def test_exp1b_clears_only_its_own_shard_outputs_before_rerun():
    source = RUNNER.read_text()
    start = source.index('run exp1b "')
    end = source.index('\nrun portfolio "', start)
    block = source[start:end]

    assert '_SHARD=' + chr(92) + chr(36) + '{SHARD_INDEX:-0}' in block
    assert 'rm -f "' + chr(92) + chr(36) + '{_OLD_BENCH_PUBLISH}"' in block
    assert 'rm -f ' + chr(92) + '"' + chr(92) + chr(36) + '{_PV_PUBLISH}' + chr(92) + '"' in block
