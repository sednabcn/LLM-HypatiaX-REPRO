"""Offline fail-closed generated-formula gate regression tests."""

import ast
from pathlib import Path

from hypatiax.experiments.audit import validate_generated_formula


def test_exact_formula_is_eligible_only_after_symbolic_identity():
    result = validate_generated_formula(
        "def formula(entry_price, leverage):\n    return entry_price * (1 - 1 / (leverage * 0.8))",
        "entry_price * (1 - 1/(leverage * 0.8))",
        ["entry_price", "leverage"],
    )
    assert result["status"] == "exact_symbolic_equivalent"
    assert result["symbolically_equivalent"] is True
    assert result["eligible_for_exact_match"] is True
    assert result["validation_scope"] == "future_run_offline_gate"


def test_sign_error_is_not_eligible_even_if_formula_is_parseable():
    result = validate_generated_formula(
        "def formula(entry_price, leverage):\n    return entry_price * (1 + 1 / (leverage * 0.8))",
        "entry_price * (1 - 1/(leverage * 0.8))",
        ["entry_price", "leverage"],
    )
    assert result["status"] == "not_symbolically_equivalent"
    assert result["eligible_for_exact_match"] is False


def test_percentage_points_and_fraction_are_not_conflated():
    result = validate_generated_formula(
        "def formula(deposit, pool_total):\n    return deposit / pool_total",
        "deposit / pool_total * 100",
        ["deposit", "pool_total"],
    )
    assert result["status"] == "not_symbolically_equivalent"
    assert result["eligible_for_exact_match"] is False


def test_output_semantics_difference_is_not_eligible():
    result = validate_generated_formula(
        "def formula(principal, apr, n):\n    return principal * ((1 + apr / n) ** n - 1)",
        "principal * (1 + apr/n)**n",
        ["principal", "apr", "n"],
    )
    assert result["status"] == "not_symbolically_equivalent"
    assert result["eligible_for_exact_match"] is False


def test_malformed_or_unsupported_formula_remains_not_assessable():
    result = validate_generated_formula(
        "def formula(x):\n    return eval('x')",
        "x",
        ["x"],
    )
    assert result["status"] == "not_assessable"
    assert result["symbolically_equivalent"] is None
    assert result["eligible_for_exact_match"] is False


def test_missing_variable_schema_fails_before_symbolic_comparison():
    result = validate_generated_formula(
        "def formula(x):\n    return x",
        "x",
        [],
    )
    assert result["status"] == "variable_schema_missing"
    assert result["eligible_for_exact_match"] is False


def test_explicit_aliases_and_source_constants_are_supported():
    result = validate_generated_formula(
        "def formula(price, lev):\n    return price * (1 - 1 / (lev * MMR))",
        "entry_price * (1 - 1 / (leverage * MMR))",
        ["entry_price", "leverage"],
        ground_truth_aliases={"price": "entry_price", "lev": "leverage"},
        constants={"MMR": 0.8},
    )
    assert result["status"] == "exact_symbolic_equivalent"
    assert result["eligible_for_exact_match"] is True



def test_missing_formula_and_ground_truth_are_explicitly_not_assessable():
    no_formula = validate_generated_formula(None, "x", ["x"])
    assert no_formula["status"] == "no_llm_formula"
    assert no_formula["eligible_for_exact_match"] is False

    no_ground_truth = validate_generated_formula(
        "def formula(x):\\n    return x", None, ["x"]
    )
    assert no_ground_truth["status"] == "ground_truth_missing"
    assert no_ground_truth["eligible_for_exact_match"] is False


def test_canonical_4060_path_calls_gate_before_numerical_evaluation_and_persists_result():
    root = Path(__file__).resolve().parents[1]
    source = (
        root / "hypatiax/experiments/benchmarks/"
        "hypatiax_defi_benchmark_v3c_4060.py"
    ).read_text(encoding="utf-8")
    module = ast.parse(source)

    hybrid = next(
        node for node in module.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_hybrid_predict_and_eval"
    )
    calls = [
        node for node in ast.walk(hybrid)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "validate_generated_formula"
    ]
    assert len(calls) == 1

    gate_line = calls[0].lineno
    numerical_lines = [
        node.lineno for node in ast.walk(hybrid)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_eval_formula_r2"
    ]
    assert numerical_lines and gate_line < min(numerical_lines)

    returned_keys = {
        key.value
        for node in ast.walk(hybrid)
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict)
        for key in node.value.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }
    assert "symbolic_validation" in returned_keys

    provenance = next(
        node for node in module.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_hybrid_metric_provenance_record"
    )
    provenance_keys = {
        key.value
        for node in ast.walk(provenance)
        if isinstance(node, ast.Dict)
        for key in node.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }
    assert "symbolic_validation" in provenance_keys
