"""Focused offline regressions for the two hybrid Exp2 error_pct null cases.

No benchmark workers, model fitting, optional ML backends, or LLM calls are
started. These tests exercise the same shared scorer used by the Feynman
runners with deterministic stand-ins for retained hybrid predictors/formulas.
"""
from types import SimpleNamespace

import numpy as np
import pytest

from hypatiax.experiments.benchmarks.exp2_extrapolation_core import (
    compute_extrap_r2_far,
)


def test_llm_nn_retained_predictor_supplies_far_and_exact_train_baseline():
    X_train = np.array([[0.0], [1.0], [2.0], [3.0]])
    y_train = np.array([1.2, 2.2, 3.2, 4.2])
    X_far = np.array([[4.0], [5.0], [6.0]])
    y_far = np.array([5.0, 6.0, 7.0])
    calls = []

    def retained_hybrid_predictor(X):
        X = np.asarray(X, dtype=float)
        calls.append(X.copy())
        return X[:, 0] + 1.0

    result = SimpleNamespace(
        success=True,
        formula="N/A",  # NN/hybrid architecture label is not executable formula
        _predict_fn=retained_hybrid_predictor,
    )
    diagnostics = {}

    r2, rmse, error_pct = compute_extrap_r2_far(
        {"HybridSystemLLMNN all-domains (core)": result},
        X_far,
        y_far,
        ["x"],
        y_train=y_train,
        X_train_predictor=X_train,
        verbose=False,
        diagnostics=diagnostics,
    )

    method = "HybridSystemLLMNN all-domains (core)"
    assert r2[method] is not None
    assert rmse[method] == pytest.approx(0.0)
    # Far RMSE is exactly zero here, so the ratio is valid and zero.
    assert error_pct[method] == pytest.approx(0.0)
    assert diagnostics[method]["error_pct_status"] == "available"
    assert len(calls) == 2
    np.testing.assert_array_equal(calls[0], X_far)
    np.testing.assert_array_equal(calls[1], X_train)


def test_defi_formula_scores_far_region_but_zero_train_rmse_makes_ratio_undefined():
    X_train = np.array([[0.0], [1.0], [2.0], [3.0]])
    y_train = X_train[:, 0] + 1.0
    X_far = np.array([[4.0], [5.0], [6.0]])
    y_far = X_far[:, 0] + 1.1
    result = SimpleNamespace(
        success=True,
        formula="def formula(x):\n    return x + 1\n",
    )
    diagnostics = {}

    r2, rmse, error_pct = compute_extrap_r2_far(
        {"EnhancedHybridSystemDeFi (core)": result},
        X_far,
        y_far,
        ["x"],
        y_train=y_train,
        y_pred_train={"EnhancedHybridSystemDeFi (core)": y_train.copy()},
        verbose=False,
        diagnostics=diagnostics,
    )

    method = "EnhancedHybridSystemDeFi (core)"
    assert r2[method] is not None
    assert rmse[method] == pytest.approx(0.1)
    assert error_pct[method] is None
    assert diagnostics[method]["error_pct_status"] == "zero_or_invalid_training_rmse"


def test_defi_formula_with_nonzero_training_error_has_defined_ratio():
    X_train = np.array([[0.0], [1.0], [2.0], [3.0]])
    y_train = X_train[:, 0] + 1.0
    X_far = np.array([[4.0], [5.0], [6.0]])
    y_far = X_far[:, 0] + 0.8
    result = SimpleNamespace(
        success=True,
        formula="def formula(x):\n    return x + 0.8\n",
    )
    diagnostics = {}

    _, rmse, error_pct = compute_extrap_r2_far(
        {"EnhancedHybridSystemDeFi (core)": result},
        X_far,
        y_far,
        ["x"],
        y_train=y_train,
        y_pred_train={"EnhancedHybridSystemDeFi (core)": X_train[:, 0] + 0.8},
        verbose=False,
        diagnostics=diagnostics,
    )

    method = "EnhancedHybridSystemDeFi (core)"
    assert rmse[method] == pytest.approx(0.0)
    assert error_pct[method] == pytest.approx(0.0)
    assert diagnostics[method]["error_pct_status"] == "available"


def test_defi_without_formula_or_retained_predictor_reports_missing_far_score():
    X_far = np.array([[4.0], [5.0], [6.0]])
    y_far = np.array([5.0, 6.0, 7.0])
    result = SimpleNamespace(success=True, formula="N/A")
    diagnostics = {}

    r2, rmse, error_pct = compute_extrap_r2_far(
        {"EnhancedHybridSystemDeFi (core)": result},
        X_far,
        y_far,
        ["x"],
        y_train=np.array([1.0, 2.0, 3.0]),
        y_pred_train={"EnhancedHybridSystemDeFi (core)": np.array([1.1, 2.1, 3.1])},
        verbose=False,
        diagnostics=diagnostics,
    )

    method = "EnhancedHybridSystemDeFi (core)"
    assert r2[method] is None
    assert rmse[method] is None
    assert error_pct[method] is None
    assert diagnostics[method]["status"] == "formula_missing"
