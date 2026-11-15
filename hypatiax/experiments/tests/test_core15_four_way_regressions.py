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
