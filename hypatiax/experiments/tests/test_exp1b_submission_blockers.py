"""Offline contract tests for exp1b's Portfolio-filtered multi-seed protocol."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "run_all.sh"
BENCHMARK = ROOT / "hypatiax/experiments/benchmarks/portfolio_variance_v3c2.py"


def test_exp1b_benchmark_uses_its_declared_portfolio_case_filter():
    source = RUNNER.read_text()
    start = source.index('run exp1b "')
    end = source.index('\nrun portfolio "', start)
    block = source[start:end]

    assert 'DEFI_TASK_FILTER=\\"Portfolio\\"' in block
    assert 'DEFI_SEEDS=\\"\\${_SHARD_SEEDS}\\"' in block
    assert 'PYSR_SEED=\\"\\${_SEEDS[0]}\\"' in block


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


def test_exp1b_workflow_restores_canonical_seed_and_publishes_shard_copy():
    workflow = (ROOT / ".github/workflows/ci_runner_repro.yml").read_text()
    assert 'exp1b isolated benchmark:' in workflow
    assert 'hypatiax_defi_benchmark_v3_results_seed${_seed}_shard${SHARD_INDEX}.json' in workflow
    assert 'git checkout -- "${_canonical}"' in workflow
    assert 'portfolio_variance_defi_seed_sweep_seed${_seed}_shard${SHARD_INDEX}.json' in workflow
    assert 'if [[ "$fname" == "portfolio_variance_defi_seed_sweep_seed${_seed}_shard${SHARD_INDEX}.json" ]]; then' in workflow
    assert 'REPLACE: refreshing tracked exp1b per-seed portfolio artifact' not in workflow
