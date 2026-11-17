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
    assert diagnostics[method]["error_pct_status"] == "zero_training_rmse"


def test_defi_formula_with_nonzero_training_error_has_defined_ratio():
    X_train = np.array([[0.0], [1.0], [2.0], [3.0]])
    y_train = X_train[:, 0] + 1.0
    X_far = np.array([[4.0], [5.0], [6.0]])
    y_far = X_far[:, 0] + 1.0
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
    assert rmse[method] == pytest.approx(0.2)
    assert error_pct[method] == pytest.approx(100.0)
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



def test_retained_final_predictor_overrides_conflicting_formula_training_predictions():
    X_train = np.array([[0.0], [1.0], [2.0], [3.0]])
    # Keep a nonzero training RMSE so the ratio is mathematically defined;
    # the far-region predictions remain exact.
    y_train = np.array([1.1, 2.1, 3.1, 4.1])
    X_far = np.array([[4.0], [5.0], [6.0]])
    y_far = np.array([5.0, 6.0, 7.0])

    # The retained method is exact on the far partition. The deliberately
    # conflicting precomputed array represents only a symbolic base formula.
    result = SimpleNamespace(
        success=True,
        formula="def formula(x):\n    return x + 100\n",
        _predict_fn=lambda X: np.asarray(X, dtype=float)[:, 0] + 1.0,
    )
    diagnostics = {}

    _, rmse, error_pct = compute_extrap_r2_far(
        {"hybrid": result},
        X_far,
        y_far,
        ["x"],
        y_train=y_train,
        y_pred_train={"hybrid": np.full(len(y_train), 101.0)},
        X_train_predictor=X_train,
        verbose=False,
        diagnostics=diagnostics,
    )

    assert rmse["hybrid"] == pytest.approx(0.0)
    assert error_pct["hybrid"] == pytest.approx(0.0)
    assert diagnostics["hybrid"]["predictor_route"] == "retained_final_predictor"
    assert diagnostics["hybrid"]["training_prediction_route"] == "retained_final_predictor"
    assert diagnostics["hybrid"]["error_pct_route_consistent"] is True



def test_training_prediction_failure_preserves_independent_far_metrics():
    X_train = np.array([[0.0], [1.0], [2.0], [3.0]])
    X_far = np.array([[4.0], [5.0], [6.0]])
    y_far = np.array([5.0, 6.0, 7.0])

    def predictor(X):
        values = np.asarray(X, dtype=float)
        if values[0, 0] < 4.0:
            raise RuntimeError("synthetic training prediction failure")
        return values[:, 0] + 1.0

    result = SimpleNamespace(success=True, formula="N/A", _predict_fn=predictor)
    diagnostics = {}
    _, rmse, error_pct = compute_extrap_r2_far(
        {"hybrid": result},
        X_far,
        y_far,
        ["x"],
        y_train=np.array([1.0, 2.0, 3.0, 4.0]),
        X_train_predictor=X_train,
        verbose=False,
        diagnostics=diagnostics,
    )

    assert rmse["hybrid"] == pytest.approx(0.0)
    assert error_pct["hybrid"] is None
    assert diagnostics["hybrid"]["error_pct_status"] == "training_prediction_error"
    assert diagnostics["hybrid"]["predictor_route"] == "retained_final_predictor"
    assert diagnostics["hybrid"]["training_prediction_route"] == "retained_final_predictor"
    assert diagnostics["hybrid"]["error_pct_route_consistent"] is True
    assert "synthetic training prediction failure" in diagnostics["hybrid"]["error_pct_reason"]



def test_defi_composite_base_plus_residual_records_benchmark_rmse_mismatch():
    X_train = np.array([[0.0], [1.0], [2.0], [3.0]])
    y_train = X_train[:, 0] + 1.25
    X_far = np.array([[4.0], [5.0], [6.0]])
    y_far = X_far[:, 0] + 1.25

    def base_predictor(X):
        return np.asarray(X, dtype=float)[:, 0] + 1.0

    def residual_predictor(X, base_prediction):
        return np.asarray(base_prediction, dtype=float) + 0.25

    def final_base_plus_residual(X):
        return residual_predictor(X, base_predictor(X))

    # The wrapper's reported benchmark RMSE is deliberately inconsistent
    # with this retained final composite predictor (which has RMSE 0.0).
    result = SimpleNamespace(
        success=True,
        formula="[NN residual correction — final predictor]",
        rmse=0.25,
        _predict_fn=final_base_plus_residual,
    )
    diagnostics = {}
    _, far_rmse, error_pct = compute_extrap_r2_far(
        {"EnhancedHybridSystemDeFi (core)": result},
        X_far,
        y_far,
        ["x"],
        y_train=y_train,
        X_train_predictor=X_train,
        verbose=False,
        diagnostics=diagnostics,
    )

    method_diag = diagnostics["EnhancedHybridSystemDeFi (core)"]
    assert far_rmse["EnhancedHybridSystemDeFi (core)"] == pytest.approx(0.0)
    assert error_pct["EnhancedHybridSystemDeFi (core)"] is None
    assert method_diag["extrap_rmse_train"] == pytest.approx(0.0)
    assert method_diag["benchmark_rmse"] == pytest.approx(0.25)
    assert method_diag["train_rmse_delta"] == pytest.approx(-0.25)
    assert method_diag["train_rmse_consistent"] is False
    assert method_diag["train_rmse_consistency_status"] == "mismatch"


def test_llm_nn_retained_predictor_training_rmse_matches_reported_benchmark_rmse():
    X_train = np.array([[0.0], [1.0], [2.0], [3.0]])
    y_train = X_train[:, 0] + 1.2
    X_far = np.array([[4.0], [5.0], [6.0]])
    y_far = X_far[:, 0] + 1.0
    predictor = lambda X: np.asarray(X, dtype=float)[:, 0] + 1.0
    result = SimpleNamespace(
        success=True,
        formula="N/A",
        rmse=0.2,
        _predict_fn=predictor,
    )
    diagnostics = {}

    compute_extrap_r2_far(
        {"HybridSystemLLMNN all-domains (core)": result},
        X_far,
        y_far,
        ["x"],
        y_train=y_train,
        X_train_predictor=X_train,
        verbose=False,
        diagnostics=diagnostics,
    )

    method_diag = diagnostics["HybridSystemLLMNN all-domains (core)"]
    assert method_diag["extrap_rmse_train"] == pytest.approx(0.2)
    assert method_diag["benchmark_rmse"] == pytest.approx(0.2)
    assert method_diag["train_rmse_delta"] == pytest.approx(0.0)
    assert method_diag["train_rmse_consistent"] is True
    assert method_diag["train_rmse_consistency_status"] == "matches"



def test_exact_predictor_reports_r2_one_rmse_zero_and_undefined_ratio():
    X_train = np.array([[0.0], [1.0], [2.0], [3.0]])
    y_train = X_train[:, 0] + 1.0
    X_far = np.array([[4.0], [5.0], [6.0]])
    y_far = X_far[:, 0] + 1.0
    result = SimpleNamespace(
        success=True,
        formula="def formula(x):\n    return x + 1\n",
    )
    diagnostics = {}

    r2, rmse, error_pct = compute_extrap_r2_far(
        {"exact_symbolic": result},
        X_far,
        y_far,
        ["x"],
        y_train=y_train,
        y_pred_train={"exact_symbolic": y_train.copy()},
        verbose=False,
        diagnostics=diagnostics,
    )

    assert r2["exact_symbolic"] == pytest.approx(1.0)
    assert rmse["exact_symbolic"] == pytest.approx(0.0)
    assert error_pct["exact_symbolic"] is None
    assert diagnostics["exact_symbolic"]["extrap_rmse_train"] == pytest.approx(0.0)
    assert diagnostics["exact_symbolic"]["error_pct_status"] == "zero_training_rmse"
