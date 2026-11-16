"""Regression contracts for the shared Exp2 far-extrapolation scorer.

These tests are offline: they exercise only deterministic formula evaluation and
metric reporting, without loading benchmark backends or calling an LLM.
"""
from types import SimpleNamespace

import numpy as np
import pytest

from hypatiax.experiments.benchmarks.extrap_r2_far import (
    _runner_eval_formula,
    compute_extrap_r2_far,
)


def test_runner_formula_evaluator_imports_regex_and_scores_expression():
    X = np.array([[1.0], [2.0], [3.0]])
    predicted = _runner_eval_formula("x + 1", X, ["x"])
    np.testing.assert_allclose(predicted, [2.0, 3.0, 4.0])


def test_far_rmse_is_preserved_when_far_r2_is_catastrophic():
    X_far = np.array([[1.0], [2.0], [3.0]])
    y_far = np.array([1.0, 2.0, 3.0])
    result = SimpleNamespace(success=True, formula="1000 * x")

    r2, rmse, error_pct = compute_extrap_r2_far(
        {"symbolic": result},
        X_far,
        y_far,
        ["x"],
    )

    assert r2["symbolic"] is None
    assert rmse["symbolic"] == pytest.approx(
        np.sqrt(np.mean((y_far - 1000.0 * X_far[:, 0]) ** 2))
    )
    assert error_pct["symbolic"] is None
