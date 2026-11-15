"""Regression tests for Core-15 four-way evaluator and budget/accounting fixes."""
import ast
import inspect
import pathlib

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
BASELINE = ROOT / "hypatiax/core/base_pure_llm/baseline_pure_llm_defi_discovery.py"
FOUR_WAY = ROOT / "hypatiax/experiments/benchmarks/exp1_four_way_matched.py"


def _evaluate_function():
    tree = ast.parse(BASELINE.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "PureLLMBaseline")
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "evaluate_function")
    method.decorator_list = []
    namespace = {"np": np, "inspect": inspect}
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(BASELINE), "exec"), namespace)
    return namespace["evaluate_function"]


def test_strict_mode_still_tries_scalar_fallback_after_vectorized_failure(monkeypatch):
    evaluate = _evaluate_function()

    def scalar_only(A, B):
        if np.ndim(A) or np.ndim(B):
            raise TypeError("scalar-only implementation")
        return A + 2 * B

    monkeypatch.setenv("HYPATIAX_STRICT", "1")
    X = np.array([[1.0, 3.0], [2.0, 4.0], [5.0, 6.0]])
    predicted = evaluate(scalar_only, X, ["A", "B"])
    np.testing.assert_allclose(predicted, [7.0, 10.0, 17.0])


def test_required_unmatched_parameter_is_not_filled_with_zero(monkeypatch):
    evaluate = _evaluate_function()

    def under_specified(A, missing):
        return A + missing

    monkeypatch.setenv("HYPATIAX_STRICT", "1")
    with pytest.raises(RuntimeError, match="All evaluation strategies failed"):
        evaluate(under_specified, np.array([[1.0], [2.0]]), ["A"])


def test_core15_pysr_budget_and_failure_denominators_are_explicit():
    source = FOUR_WAY.read_text(encoding="utf-8")
    assert "PYSR_ONLY_FIT_TIMEOUT = max(1, COMMON_WALL_CLOCK - 60)" in source
    assert "timeout_secs=(PYSR_ONLY_FIT_TIMEOUT if condition == \"pysr_only\" else None)" in source
    assert '"n_assigned_equations"' in source
    assert '"n_successful_equations"' in source
    assert '"n_failed_equations"' in source
    assert '"paired_coverage_fraction"' in source
    assert '"comparison_status": "complete" if all_arms_complete else "partial"' in source



def _aggregate_function():
    tree = ast.parse(FOUR_WAY.read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_aggregate")
    namespace = {
        "np": np,
        "METHOD_KEYS": ("hybrid_llm_pysr", "llm_only", "pysr_only", "nn_only"),
    }
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(FOUR_WAY), "exec"), namespace)
    return namespace["_aggregate"]


def test_aggregate_marks_failed_arm_and_paired_coverage_as_partial():
    aggregate = _aggregate_function()
    successful = {
        "success": True,
        "test": {"r2": 0.8, "rmse": 0.2, "mae": 0.1},
        "extrapolation": {
            regime: {"r2": 0.7, "rmse": 0.3, "mae": 0.2}
            for regime in ("near", "medium", "far")
        },
    }
    checkpoint = {
        "0": {
            "name": "toy equation",
            "domain": "test",
            "methods": {
                "hybrid_llm_pysr": dict(successful),
                "llm_only": dict(successful),
                "pysr_only": {"success": False, "error": "PySR fit timed out"},
                "nn_only": dict(successful),
            },
        }
    }
    summary = aggregate(checkpoint)
    assert summary["comparison_status"] == "partial"
    assert summary["method_test_metrics"]["pysr_only"]["_coverage"]["n_failed_equations"] == 1
    assert summary["paired_hybrid_test_comparisons"]["pysr_only"]["r2"]["n_paired_equations"] == 0
    assert summary["paired_hybrid_test_comparisons"]["pysr_only"]["r2"]["comparison_status"] == "partial"
    assert summary["paired_hybrid_test_comparisons"]["llm_only"]["r2"]["paired_coverage_fraction"] == 1.0



def _signature_validator():
    tree = ast.parse(BASELINE.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "PureLLMBaseline")
    method = next(
        n for n in cls.body
        if isinstance(n, ast.FunctionDef) and n.name == "validate_formula_signature"
    )
    method.decorator_list = []
    namespace = {
        "inspect": inspect,
        "parse_formula": lambda _code: (lambda M, a, b: M + a + b),
    }
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(BASELINE), "exec"), namespace)
    return namespace["validate_formula_signature"]


def test_llm_only_rejects_allometric_extra_coefficient_parameters():
    validate = _signature_validator()
    with pytest.raises(
        ValueError,
        match=r"expected parameters \['M'\], got \['M', 'a', 'b'\]",
    ):
        validate("def formula(M, a, b): return a * M**b", ["M"])


def test_llm_prompt_requires_exact_declared_signature_and_numeric_coefficients():
    tree = ast.parse(BASELINE.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "PureLLMBaseline")
    method = next(
        n for n in cls.body
        if isinstance(n, ast.FunctionDef) and n.name == "_generate_standard_prompt"
    )
    namespace = {}
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(BASELINE), "exec"), namespace)
    prompt = namespace["_generate_standard_prompt"](
        object(), "Allometric Scaling", "biology", ["M"], {}
    )
    assert "def formula(M):" in prompt
    assert "match the declared input variables EXACTLY" in prompt
    assert "numeric literals" in prompt
    assert "Do not estimate or fit coefficients from X or y" in prompt
    assert "def formula(param1, param2, ...)" not in prompt
