"""Focused offline regressions for the Exp1 DeFi hybrid route."""

import numpy as np

from hypatiax.experiments.benchmarks import hypatiax_defi_benchmark_v3c as bench
from hypatiax.protocols.experiment_protocol_defi import DeFiExperimentProtocol


def _inputs():
    return (
        np.ones((20, 1), dtype=float),
        np.linspace(0.0, 1.0, 20),
        np.ones((10, 1), dtype=float),
        np.linspace(0.0, 1.0, 10),
    )


def _common(monkeypatch, route):
    monkeypatch.setattr(
        bench, "_generate_llm_formula",
        lambda *a, **k: {
            "python_code": "def formula(x):\n    return x",
            "llm_called": True, "bypass_kind": "live",
            "llm_source": "offline_fixture", "timeout_s": 10.0,
            "temperature_requested": 0.25, "temperature_sent": True,
        },
    )
    monkeypatch.setattr(bench, "_formula_has_pathological_behavior", lambda code: False)
    monkeypatch.setattr(bench, "structural_risk_tokens", lambda code: [])
    monkeypatch.setattr(
        bench, "_extrapolation_probe",
        lambda *a, **k: {"status": "ok", "delta": None, "r2_train": 0.8, "r2_edge": 0.8},
    )
    monkeypatch.setattr(bench, "_routing_delta_tau", lambda: None)
    monkeypatch.setattr(
        bench, "kde_ood_probability",
        lambda xtr, xte: {"status": "ok", "p_ood_per_query": [0.5] * len(xte)},
    )
    monkeypatch.setattr(
        bench, "route_decision_from_diagnostics",
        lambda *a, **k: {"decision": route, "route_reason": "offline test route"},
    )
    monkeypatch.setattr(bench, "_execute_formula", lambda code, x, **k: np.full(len(x), 0.5))


def test_exp1_ensemble_training_metric_is_for_the_ensemble(monkeypatch):
    _common(monkeypatch, "ensemble")
    Xtr, ytr, Xte, yte = _inputs()
    monkeypatch.setattr(
        bench, "_train_and_eval_nn",
        lambda *a, **k: {
            "train_r2": 0.7, "test_r2": 0.2, "success": True,
            "y_pred_train": np.full(len(ytr), 0.4),
            "y_pred_test": np.full(len(yte), 0.4),
        },
    )
    monkeypatch.setattr(
        bench, "_ensemble_llm_nn",
        lambda llm_pred_test, **k: np.full(len(llm_pred_test), 0.3),
    )
    monkeypatch.setattr(
        bench, "_compute_metrics",
        lambda y, pred: {"r2": 0.42 if len(y) == len(ytr) else 0.18},
    )

    result = bench._hybrid_predict_and_eval(
        "fixture", "defi", Xtr, ytr, Xte, yte, ["x"], {}
    )

    assert result["train_r2"] == 0.42
    assert result["train_r2_source"] == "ensemble_training_residual_blend"
    assert result["test_r2"] == 0.18
    assert result["route_execution_status"] == "ensemble_executed"
    assert result["success"] is True


def test_exp1_nn_fallback_reports_nn_training_metric(monkeypatch):
    _common(monkeypatch, "fitted_llm")
    Xtr, ytr, Xte, yte = _inputs()

    def eval_formula(code, X, y, constants=None):
        return (0.8, True) if len(y) == len(ytr) else (float("nan"), False)

    monkeypatch.setattr(bench, "_eval_formula_r2", eval_formula)
    monkeypatch.setattr(
        bench, "_train_and_eval_nn",
        lambda *a, **k: {
            "train_r2": 0.65, "test_r2": 0.25, "success": True,
            "y_pred_train": np.full(len(ytr), 0.4),
            "y_pred_test": np.full(len(yte), 0.4),
        },
    )

    result = bench._hybrid_predict_and_eval(
        "fixture", "defi", Xtr, ytr, Xte, yte, ["x"], {}
    )

    assert result["train_r2"] == 0.65
    assert result["train_r2_source"] == "nn_fallback"
    assert result["test_r2"] == 0.25
    assert result["success"] is True


def test_exp1_constant_test_target_is_explicitly_undefined(monkeypatch):
    _common(monkeypatch, "nn")
    Xtr, ytr, Xte, _ = _inputs()
    yte = np.ones(10, dtype=float)
    monkeypatch.setattr(
        bench, "_generate_llm_formula",
        lambda *a, **k: {"python_code": None, "llm_called": False},
    )
    monkeypatch.setattr(
        bench, "_train_and_eval_nn",
        lambda *a, **k: {
            "train_r2": 0.9, "test_r2": float("nan"), "success": True,
            "y_pred_train": np.full(len(ytr), 0.4),
            "y_pred_test": np.full(len(yte), 0.4),
        },
    )

    result = bench._hybrid_predict_and_eval(
        "fixture", "defi", Xtr, ytr, Xte, yte, ["x"], {}
    )

    assert result["test_r2_status"] == "constant_target"
    assert np.isnan(result["test_r2"])
    assert result["success"] is False


def test_exp1_option_protocol_exposes_stochastic_inputs_and_constants():
    cases = {
        row[0]: row for row in DeFiExperimentProtocol()._generate_derivatives_tests(200)
    }

    delta = cases[
        "Options Delta rate of change of option price relative to underlying"
    ]
    assert delta[3] == ["moneyness", "implied_volatility", "time_to_expiry"]
    assert delta[1].shape[1] == 3

    for name in (
        "Black-Scholes Call Price for European call option",
        "Black-Scholes Put Price for European put option",
    ):
        assert cases[name][3] == [
            "spot_price", "implied_volatility", "time_to_expiry"
        ]
        assert cases[name][1].shape[1] == 3
        assert cases[name][4]["constants"] == {
            "strike": 100.0, "risk_free_rate": 0.04
        }

    for name in (
        "Gamma of option rate of change of delta with respect to spot",
        "Vega of option sensitivity of price to implied volatility",
    ):
        assert cases[name][4]["constants"] == {
            "strike": 100.0, "risk_free_rate": 0.04
        }
