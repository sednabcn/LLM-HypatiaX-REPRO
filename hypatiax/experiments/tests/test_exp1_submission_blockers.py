"""Offline contract tests for the canonical exp1 DeFi benchmark output."""

import ast
from pathlib import Path


BENCHMARK = (
    Path(__file__).resolve().parents[1]
    / "benchmarks"
    / "hypatiax_defi_benchmark_v3c.py"
)


def _function_source(tree, name):
    node = next(
        item for item in ast.walk(tree)
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        and item.name == name
    )
    return ast.get_source_segment(BENCHMARK.read_text(), node)


def test_exp1_has_no_standalone_pure_llm_comparison_arm():
    source = BENCHMARK.read_text()
    tree = ast.parse(source)
    runner = _function_source(tree, "run_benchmark")
    report = _function_source(tree, "_generate_report")

    assert "PureLLMBaseline" not in runner
    assert 'case_results["pure_llm"]' not in runner
    assert '"pure_llm"' not in report
    # Hybrid still owns an LLM-generated formula internally.
    hybrid = _function_source(tree, "_hybrid_predict_and_eval")
    assert '"llm_code":' in hybrid


def test_hybrid_formula_and_provenance_are_written_to_case_results():
    tree = ast.parse(BENCHMARK.read_text())
    runner = _function_source(tree, "run_benchmark")

    assert '"formula":         hy_m.get("llm_code")' in runner
    assert '"llm_train_r2":    hy_m.get("llm_train_r2")' in runner
    assert '"formula_context": {' in runner
    assert '"llm_model": LLM_MODEL' in runner
    assert '"audit_data": {' in runner
    for field in ("X_train", "y_train", "X_test", "y_test"):
        assert f'"{field}"' in runner
    for field in ("llm_called", "bypass_kind", "llm_source"):
        assert f'"{field}"' in runner


def test_exp1_llm_request_honours_timeout_without_hidden_retries():
    source = BENCHMARK.read_text()
    assert 'os.environ.get("LLM_METHOD_TIMEOUT", "120")' in source
    assert "timeout=timeout_s" in source
    assert "max_retries=0" in source
    assert 'LLM_MODEL = "claude-sonnet-4-6"' in source
    assert "model=LLM_MODEL" in source
    assert 'hy_m.get("llm_timeout_s")' in source
    assert 'temperature_requested": hy_m.get("llm_temperature_requested")' in source
    assert 'temperature_sent": hy_m.get("llm_temperature_sent")' in source


def test_exp1_configuration_matches_the_v3c_primary_feature_split():
    root = Path(__file__).resolve().parents[3]
    for name in ("repro.yaml", "fresh_rerun.yaml"):
        config = (root / "config" / name).read_text()
        assert 'script: "hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py"' in config
        assert 'split: "primary_feature_40_60"' in config


def test_exp1c_is_an_alias_of_the_existing_protocol30_pca_stage():
    root = Path(__file__).resolve().parents[3]
    config = (root / "config" / "fresh_rerun.yaml").read_text()
    assert "    exp1c:" in config
    assert "      alias_of: exp1" in config
    assert "      runner_stage: exp2_protocol30_pca_4060" in config
    assert "      method_ids: [2, 3]" in config
    assert "      verification_status: not_executed" in config


def test_case_record_identifies_the_protocol_split_for_rescoring():
    tree = ast.parse(BENCHMARK.read_text())
    runner = _function_source(tree, "run_benchmark")

    assert '"split_protocol": {' in runner
    assert '"name": "aggressive_extrapolation_40_60"' in runner
    assert '"train_size": int(len(X_tr))' in runner
    assert '"test_size": int(len(X_te))' in runner
