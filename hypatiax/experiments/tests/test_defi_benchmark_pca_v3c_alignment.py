"""Static regression contracts for the v3c-aligned DeFi PCA benchmark.

These tests intentionally avoid importing the model runner, initializing Torch,
or making any LLM/API calls. They protect the scientific split and v3c parity.
"""
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "hypatiax" / "experiments" / "benchmarks" / "hypatiax_defi_benchmark_pca.py"
V3C_RUNNER = ROOT / "hypatiax" / "experiments" / "benchmarks" / "hypatiax_defi_benchmark_v3c.py"


def _source_and_tree():
    source = RUNNER.read_text(encoding="utf-8")
    return source, ast.parse(source, filename=str(RUNNER))


def _function_names(tree):
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_pca_runner_tracks_every_current_v3c_function_except_outer_split_adapter():
    _, pca_tree = _source_and_tree()
    v3c_source = V3C_RUNNER.read_text(encoding="utf-8")
    v3c_tree = ast.parse(v3c_source, filename=str(V3C_RUNNER))
    assert _function_names(pca_tree) - {"_pca_directed_split_40_60", "_json_default"} == (
        _function_names(v3c_tree) - {"_random_split_80_20"}
    )


def test_pca_runner_carries_current_v3c_validation_and_fallback_components():
    source, tree = _source_and_tree()
    names = _function_names(tree)

    required = {
        "_execute_formula_diagnostic",
        "_formula_pathology_reasons",
        "_is_intractable_case",
        "_normalize_saved_record",
        "_hybrid_component_timing_fields",
        "_validate_result_records",
        "_match_defi_protocol_case",
        "_hybrid_metric_provenance_record",
        "_log_ridge_domain_eligible",
        "_signed_ridge_domain_eligible",
        "_feature_augmentation_schema",
        "_augment_features",
        "_train_and_eval_nn",
        "_hybrid_predict_and_eval",
        "_m5_record_failure",
    }
    assert required <= names
    assert "trust_gate_diagnostics" in source
    assert "nn_prediction_validation" in source
    assert "M5_FAILURES" in source
    assert "ridge_eligible" in source
    assert "selected_predictor_source" in source


def test_pca_outer_split_remains_pc1_40_60_and_is_not_v3c_random_80_20():
    source, tree = _source_and_tree()
    names = _function_names(tree)
    assert "_pca_directed_split_40_60" in names
    assert "_random_split_80_20" not in names
    assert "from hypatiax.tools.utils.pca_split_utils import pca_directed_split" in source

    helper = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_pca_directed_split_40_60"
    )
    calls = [
        node for node in ast.walk(helper)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "pca_directed_split"
    ]
    assert len(calls) == 1
    keywords = {kw.arg: kw.value for kw in calls[0].keywords}
    assert ast.literal_eval(keywords["test_size"]) == 0.6
    assert ast.literal_eval(keywords["return_metadata"]) is True
    assert "split_is_transductive" in source
    assert "validation_split_var_idx" in source
    assert "validation_split_type" in source


def test_pca_runner_uses_shared_v3c_nn_hybrid_arms_not_standalone_llm_arm():
    source, _ = _source_and_tree()
    assert 'case_results["neural_network"]' in source
    assert 'case_results["hybrid"]' in source
    assert 'case_results["pure_llm"]' not in source
    assert "_match_defi_protocol_case(" in source


def test_pca_split_protocol_is_persisted_in_each_record_and_disclosure():
    source, _ = _source_and_tree()
    assert '"name": "pca_40_60_pc1"' in source
    assert '"split_protocol": "pca_40_60_pc1"' in source
    assert '"train_fraction": 0.4' in source
    assert '"test_fraction": 0.6' in source
    assert 'split_protocol_disclosure.json' in source
    assert 'hypatiax_defi_benchmark_pca_checkpoint' in source
    assert 'hypatiax_defi_benchmark_pca_results' in source
    assert 'hypatiax_defi_benchmark_v3_results' not in source



def test_pca_cli_accepts_force_fresh_and_rejects_conflicting_resume_mode():
    source, tree = _source_and_tree()
    main_guard = next(
        node for node in tree.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and any(isinstance(part, ast.Constant) and part.value == "__main__"
                for part in node.test.comparators)
    )
    cli_source = ast.get_source_segment(source, main_guard)
    assert 'add_mutually_exclusive_group()' in cli_source
    assert 'add_argument("--resume"' in cli_source
    assert 'add_argument("--force-fresh"' in cli_source
    # Fresh is already the default run mode; this flag makes that intent explicit
    # for run_all.sh and CI callers without changing checkpoint semantics.
    assert 'if not resume:' in source
    assert 'CHECKPOINT_FILE.unlink()' in source
    assert 'FINAL_OUTPUT.unlink()' in source



def test_pca_json_serializer_is_module_scoped_for_final_disclosure():
    source, tree = _source_and_tree()
    serializer = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_json_default"
    )
    assert serializer.lineno < next(
        node.lineno for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_benchmark"
    )
    assert "default=_json_default" in source
    assert "default=_default" not in source
    assert "split_protocol_disclosure.json" in source
    assert "Not serialisable:" in ast.get_source_segment(source, serializer)
