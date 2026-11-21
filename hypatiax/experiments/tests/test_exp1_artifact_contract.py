"""Structural artifact-contract tests for exp1's canonical benchmark runner.

These tests are deliberately offline: they inspect the runner's artifact wiring
and do not execute the benchmark, fit models, or call an LLM.
"""

import ast
from pathlib import Path


BENCHMARK = (
    Path(__file__).resolve().parents[1]
    / "benchmarks"
    / "hypatiax_defi_benchmark_v3c.py"
)


def _runner():
    source = BENCHMARK.read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = next(
        item for item in ast.walk(tree)
        if isinstance(item, ast.FunctionDef) and item.name == "run_benchmark"
    )
    return node


def _dict_assignment(function, target_name, key, *, containing_name=None):
    for node in ast.walk(function):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value = node.value
        if not isinstance(value, ast.Dict):
            continue
        for target in targets:
            if not isinstance(target, ast.Subscript):
                continue
            if not isinstance(target.value, ast.Name) or target.value.id != target_name:
                continue
            slice_node = target.slice
            if isinstance(slice_node, ast.Constant) and slice_node.value == key:
                if containing_name is None or _contains_name(value, containing_name):
                    return value
    raise AssertionError(f"missing {target_name}[{key!r}] dictionary assignment")


def _literal_dict_fields(node):
    fields = {}
    for key, value in zip(node.keys, node.values):
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            fields[key.value] = value
    return fields


def _contains_name(node, name):
    return any(
        isinstance(child, ast.Name) and child.id == name
        for child in ast.walk(node)
    )


def test_exp1_runner_passes_attempt_state_into_hybrid_and_persists_failure_provenance():
    runner = _runner()

    hybrid_call = next(
        node for node in ast.walk(runner)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_hybrid_predict_and_eval"
    )
    state_arg = next(
        keyword.value for keyword in hybrid_call.keywords
        if keyword.arg == "llm_attempt_state"
    )
    assert isinstance(state_arg, ast.Name)
    assert state_arg.id == "hybrid_llm_state"

    failure_fields = _literal_dict_fields(
        _dict_assignment(runner, "case_results", "hybrid", containing_name="hybrid_llm_state")
    )
    expected_state_fields = {
        "llm_called": "llm_called",
        "bypass_kind": "bypass_kind",
        "llm_source": "llm_source",
        "llm_timeout_s": "llm_timeout_s",
        "llm_temperature_requested": "llm_temperature_requested",
        "llm_temperature_sent": "llm_temperature_sent",
        "formula": "llm_code",
    }
    for artifact_key, state_key in expected_state_fields.items():
        assert artifact_key in failure_fields
        assert _contains_name(failure_fields[artifact_key], "hybrid_llm_state")
        assert state_key in ast.unparse(failure_fields[artifact_key])

    # The explicit boolean fallback is only for cases with no recorded state;
    # the value itself must be read from the preserved attempt-state mapping.
    assert isinstance(failure_fields["llm_called"], ast.Call)
    assert isinstance(failure_fields["llm_called"].func, ast.Name)
    assert failure_fields["llm_called"].func.id == "bool"


def test_exp1_success_artifact_keeps_ood_scope_and_llm_attempt_metadata():
    runner = _runner()
    success_fields = _literal_dict_fields(
        _dict_assignment(runner, "case_results", "hybrid", containing_name="hy_m")
    )

    required = {
        "ood_diagnostic",
        "ood_covariate_protocol",
        "llm_called",
        "bypass_kind",
        "llm_source",
        "llm_timeout_s",
        "llm_temperature_requested",
        "llm_temperature_sent",
        "formula",
        "llm_train_r2",
    }
    assert required <= success_fields.keys()

    # Keep the explicit distinction: X_test covariates are queried at routing
    # time, while held-out labels are not used for routing.
    source = BENCHMARK.read_text(encoding="utf-8")
    assert '"density_fit_rows": "X_train"' in source
    assert '"query_rows": "X_test"' in source
    assert '"query_labels_used": False' in source
    assert '"access_mode": "query_time_covariate_access"' in source


def test_exp1_case_record_contains_replayable_split_and_array_evidence():
    runner = _runner()
    record = next(
        node.value for node in ast.walk(runner)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "record" for t in node.targets)
        and isinstance(node.value, ast.Dict)
    )
    fields = _literal_dict_fields(record)
    assert "split_protocol" in fields
    assert "formula_context" in fields
    assert "audit_data" in fields
    assert "seed" in fields

    split_fields = _literal_dict_fields(fields["split_protocol"])
    assert split_fields["name"].value == "aggressive_extrapolation_40_60"
    assert "train_size" in split_fields
    assert "test_size" in split_fields

    audit_fields = _literal_dict_fields(fields["audit_data"])
    assert {"X_train", "y_train", "X_test", "y_test"} <= audit_fields.keys()



def test_exp1_hybrid_fallback_train_metric_belongs_to_selected_nn():
    source = BENCHMARK.read_text(encoding="utf-8")
    tree = ast.parse(source)
    hybrid = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "_hybrid_predict_and_eval"
    )
    unparsed = ast.unparse(hybrid)
    assert 'selected_train_r2 = float(nn_m.get("train_r2", float("nan")))' in unparsed
    assert '"train_r2": float(selected_train_r2)' in unparsed
    assert '"test_r2_status"' in unparsed
    assert '"nn_fallback_undefined_test_r2_constant_target"' in unparsed


def test_exp1_llm_prompt_matches_restricted_formula_interpreter():
    source = BENCHMARK.read_text(encoding="utf-8")
    assert "norm_cdf, norm_pdf" in source
    assert "Use supplied constants exactly as given." in source
    assert "Do NOT use imports, np.where, np.dot, np.inf, np.nan" in source
    assert "metadata['ground_truth']" in source
