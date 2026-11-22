"""Focused offline regressions for the Exp1 DeFi hybrid route."""

import sys
from types import SimpleNamespace

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
    monkeypatch.setattr(bench, "_eval_formula_r2", lambda *a, **k: (0.8, True))
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
    assert result["ood_covariate_protocol"] == {
        "density_fit_rows": "X_train", "query_rows": "X_test",
        "query_labels_used": False, "access_mode": "query_time_covariate_access",
    }


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



def test_exp1_provider_failure_after_request_entry_keeps_attempt_provenance(monkeypatch):
    class FakeAnthropic:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    def fail_request(*args, **kwargs):
        raise RuntimeError("simulated provider timeout")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "offline-test-key")
    monkeypatch.setenv("LLM_METHOD_TIMEOUT", "17")
    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=FakeAnthropic))
    monkeypatch.setitem(
        sys.modules,
        "hypatiax.core.llm_call",
        SimpleNamespace(
            create_message=fail_request,
            last_call_info=lambda: {
                "temperature_requested": 0.25, "temperature_sent": False
            },
        ),
    )

    result = bench._generate_llm_formula("fixture", "defi", ["x"], {})

    assert result["llm_called"] is True
    assert result["bypass_kind"] == "none"
    assert result["llm_source"] == "v3c_builtin_failed"
    assert result["timeout_s"] == 17.0
    assert result["temperature_requested"] == 0.25
    assert result["temperature_sent"] is False
    assert "simulated provider timeout" in result["error"]


def test_exp1_split_metadata_discloses_row_index_fallback():
    X = np.ones((100, 1), dtype=float)
    y = np.arange(100, dtype=float)
    _, _, _, _, audit = bench._aggressive_split(
        X, y, {"split_var_idx": 0, "split_type": "high"}, return_metadata=True
    )

    assert audit["requested_method"] == "primary_feature_percentile"
    assert audit["realized_method"] == "row_index_fallback"
    assert audit["fallback_used"] is True
    assert audit["fallback_reason"] == "percentile_partition_has_fewer_than_20_rows"
    assert audit["train_size"] == 40
    assert audit["test_size"] == 60



def test_exp1_nn_validation_is_training_only_and_deterministic():
    rng = np.random.RandomState(19)
    X_train = np.linspace(-2.0, 2.0, 48).reshape(-1, 1)
    y_train = np.sin(X_train[:, 0]) + 0.05 * rng.normal(size=len(X_train))
    X_test_a = np.linspace(3.0, 4.0, 12).reshape(-1, 1)
    X_test_b = np.linspace(30.0, 40.0, 12).reshape(-1, 1)
    y_test = np.linspace(-1.0, 1.0, 12)

    first = bench._train_and_eval_nn(
        X_train, y_train, X_test_a, y_test,
        epochs=80, hidden=[16, 8], seed=123, max_time_s=30,
        augment=False, patience=8,
    )
    second = bench._train_and_eval_nn(
        X_train, y_train, X_test_b, y_test,
        epochs=80, hidden=[16, 8], seed=123, max_time_s=30,
        augment=False, patience=8,
    )

    assert first["success"] is True
    assert first["best_epoch"] is not None
    assert first["epochs_completed"] >= first["best_epoch"]
    assert first["validation_loss"] >= 0.0
    assert first["y_pred_train"].shape == y_train.shape
    assert first["y_pred_test"].shape == y_test.shape
    # Changing only the held-out extrapolation partition cannot change
    # validation-driven model selection or training predictions.
    assert first["best_epoch"] == second["best_epoch"]
    assert first["validation_loss"] == second["validation_loss"]
    np.testing.assert_allclose(first["y_pred_train"], second["y_pred_train"])


def test_exp1_nn_timeout_is_not_reported_as_success():
    X_train = np.linspace(0.0, 1.0, 24).reshape(-1, 1)
    y_train = X_train[:, 0] ** 2
    X_test = np.linspace(2.0, 3.0, 8).reshape(-1, 1)
    y_test = X_test[:, 0] ** 2

    result = bench._train_and_eval_nn(
        X_train, y_train, X_test, y_test,
        epochs=20, hidden=[8], seed=7, max_time_s=-1,
        augment=False,
    )

    assert result["timed_out"] is True
    assert result["success"] is False
    assert result["failure_reason"] == "training_wall_clock_timeout"
    assert result["y_pred_train"] is None
    assert result["y_pred_test"] is None


def test_exp1_hybrid_reuses_valid_standalone_nn_for_fallback(monkeypatch):
    _common(monkeypatch, "fitted_llm")
    Xtr, ytr, Xte, yte = _inputs()

    def eval_formula(code, X, y, constants=None):
        return (0.8, True) if len(y) == len(ytr) else (float("nan"), False)

    nn_result = {
        "train_r2": 0.65, "test_r2": 0.25, "success": True,
        "y_pred_train": np.full(len(ytr), 0.4),
        "y_pred_test": np.full(len(yte), 0.4),
    }
    monkeypatch.setattr(bench, "_eval_formula_r2", eval_formula)
    monkeypatch.setattr(
        bench, "_train_and_eval_nn",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("unexpected NN retraining")),
    )

    result = bench._hybrid_predict_and_eval(
        "fixture", "defi", Xtr, ytr, Xte, yte, ["x"], {},
        nn_result=nn_result,
    )

    assert result["train_r2"] == 0.65
    assert result["test_r2"] == 0.25
    assert result["route_execution_status"] == "nn_fallback_executed"
    assert result["nn_rerun_time_s"] == 0.0


def test_exp1_hybrid_rejects_invalid_nn_fallback_predictions(monkeypatch):
    _common(monkeypatch, "fitted_llm")
    Xtr, ytr, Xte, yte = _inputs()

    def eval_formula(code, X, y, constants=None):
        return (0.8, True) if len(y) == len(ytr) else (float("nan"), False)

    invalid_nn = {
        "train_r2": 0.65, "test_r2": 0.25, "success": True,
        "y_pred_train": np.full(len(ytr) - 1, 0.4),
        "y_pred_test": np.full(len(yte), 0.4),
    }
    monkeypatch.setattr(bench, "_eval_formula_r2", eval_formula)
    monkeypatch.setattr(bench, "_train_and_eval_nn", lambda *a, **k: invalid_nn)

    result = bench._hybrid_predict_and_eval(
        "fixture", "defi", Xtr, ytr, Xte, yte, ["x"], {},
        nn_result=invalid_nn,
    )

    assert result["route_execution_status"] == "nn_fallback_failed"
    assert result["success"] is False
    assert np.isnan(result["train_r2"])
    assert np.isnan(result["test_r2"])



def test_exp1_nn_reports_training_edge_ridge_and_abstention_diagnostics():
    X_train = np.geomspace(1.0, 4.0, 48).reshape(-1, 1)
    y_train = 3.0 * X_train[:, 0] ** 1.7
    X_test = np.geomspace(5.0, 8.0, 12).reshape(-1, 1)
    y_test = 3.0 * X_test[:, 0] ** 1.7

    result = bench._train_and_eval_nn(
        X_train, y_train, X_test, y_test,
        epochs=40, hidden=[8], seed=123, max_time_s=30,
        augment=False, patience=6,
    )

    assert result["success"] is True
    assert result["ridge_eligible"] is True
    assert np.isfinite(result["ridge_edge_r2"])
    assert np.isfinite(result["nn_edge_r2"])
    assert result["selected_model"] in {"nn", "log_ridge", "training_mean"}
    assert isinstance(result["abstained"], bool)
    assert np.isfinite(result["y_pred_test"]).all()


def test_exp1_options_delta_predictions_are_clipped_to_semantic_bounds(monkeypatch):
    _common(monkeypatch, "nn")
    Xtr, ytr, Xte, yte = _inputs()
    ytr = np.linspace(0.1, 0.9, len(ytr))
    yte = np.linspace(0.1, 0.9, len(yte))
    nn_result = {
        "train_r2": -1.0, "test_r2": -1.0, "success": True,
        "y_pred_train": np.linspace(-2.0, 2.0, len(ytr)),
        "y_pred_test": np.linspace(-3.0, 3.0, len(yte)),
    }
    monkeypatch.setattr(
        bench, "_generate_llm_formula",
        lambda *a, **k: {"python_code": None, "llm_called": False},
    )

    result = bench._hybrid_predict_and_eval(
        "Options Delta rate of change", "derivatives",
        Xtr, ytr, Xte, yte, ["moneyness"], {}, nn_result=nn_result,
    )

    assert nn_result["physical_bounds_applied"] == [0.0, 1.0]
    assert np.min(nn_result["y_pred_train"]) >= 0.0
    assert np.max(nn_result["y_pred_train"]) <= 1.0
    assert np.min(nn_result["y_pred_test"]) >= 0.0
    assert np.max(nn_result["y_pred_test"]) <= 1.0
    assert result["physical_bounds_applied"] == [0.0, 1.0]

def test_exp1_nn_default_augmentation_reuses_transformed_validation_features():
    # Exercise the production default (augment=True) with two input columns,
    # including the ratio features. The edge-validation matrix must be
    # transformed exactly once and retain the scaler's fitted feature width.
    x0 = np.geomspace(1.0, 4.0, 48)
    x1 = np.geomspace(2.0, 5.0, 48)
    X_train = np.column_stack([x0, x1])
    y_train = 2.0 * x0 ** 1.3 * x1 ** 0.7
    xt0 = np.geomspace(5.0, 8.0, 12)
    xt1 = np.geomspace(6.0, 9.0, 12)
    X_test = np.column_stack([xt0, xt1])
    y_test = 2.0 * xt0 ** 1.3 * xt1 ** 0.7

    result = bench._train_and_eval_nn(
        X_train, y_train, X_test, y_test,
        epochs=30, hidden=[8], seed=123, max_time_s=30,
        patience=6,
    )

    assert result["success"] is True, result["failure_reason"]
    assert result["failure_reason"] is None
    assert np.isfinite(result["nn_edge_r2"])
    assert result["y_pred_train"].shape == y_train.shape
    assert result["y_pred_test"].shape == y_test.shape
    assert np.isfinite(result["y_pred_train"]).all()
    assert np.isfinite(result["y_pred_test"]).all()


def test_exp1_directional_validation_matches_benchmark_split_direction():
    X = np.column_stack([np.arange(50, dtype=float), np.arange(50, dtype=float)[::-1]])
    y = X[:, 0] ** 2
    high = bench._train_and_eval_nn(
        X, y, X[:10], y[:10], epochs=2, hidden=[4], seed=9,
        max_time_s=30, augment=False, patience=2,
        split_metadata={"split_var_idx": 0, "split_type": "high"},
    )
    low = bench._train_and_eval_nn(
        X, y, X[:10], y[:10], epochs=2, hidden=[4], seed=9,
        max_time_s=30, augment=False, patience=2,
        split_metadata={"split_var_idx": 0, "split_type": "low"},
    )
    # Different one-sided validation tails must produce distinct checkpoints
    # or validation losses; held-out X/y are not involved in either split.
    assert high["best_epoch"] is not None
    assert low["best_epoch"] is not None
    assert high["validation_loss"] != low["validation_loss"]


def test_exp1_hybrid_abstention_bypasses_ensemble_and_records_zero_nn_weight(monkeypatch):
    _common(monkeypatch, "ensemble")
    Xtr, ytr, Xte, yte = _inputs()
    nn_result = {
        "train_r2": 0.25, "test_r2": 0.15, "success": True,
        "y_pred_train": np.full(len(ytr), 0.4),
        "y_pred_test": np.full(len(yte), 0.4),
        "abstained": True, "selected_model": "log_ridge",
        "nn_edge_r2": -0.2, "ridge_edge_r2": 0.3,
    }
    monkeypatch.setattr(
        bench, "_train_and_eval_nn",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("unexpected retraining")),
    )
    monkeypatch.setattr(
        bench, "_ensemble_llm_nn",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("abstained predictor must not be blended")),
    )
    result = bench._hybrid_predict_and_eval(
        "fixture", "defi", Xtr, ytr, Xte, yte, ["x"], {},
        nn_result=nn_result,
    )
    assert result["train_r2"] == 0.25
    assert result["test_r2"] == 0.15
    assert result["train_r2_source"] == "nn_abstention_log_ridge"
    assert result["route_execution_status"] == "nn_abstention_fallback_executed"
    assert result["blend_weights"]["nn"] == [0.0] * len(yte)
    assert result["blend_weights"]["llm"] == [0.0] * len(yte)
    assert result["blend_weights"]["replacement"] == [1.0] * len(yte)
    assert result["nn_selected_model"] == "log_ridge"


def test_exp1_llm_failure_abstention_fallback_records_zero_nn_weight(monkeypatch):
    _common(monkeypatch, "fitted_llm")
    monkeypatch.setattr(
        bench, "_eval_formula_r2",
        lambda *a, **k: (float("nan"), False),
    )
    Xtr, ytr, Xte, yte = _inputs()
    nn_result = {
        "train_r2": 0.25, "test_r2": 0.15, "success": True,
        "y_pred_train": np.full(len(ytr), 0.4),
        "y_pred_test": np.full(len(yte), 0.4),
        "abstained": True, "selected_model": "log_ridge",
        "nn_edge_r2": -0.2, "ridge_edge_r2": 0.3,
    }

    result = bench._hybrid_predict_and_eval(
        "fixture", "defi", Xtr, ytr, Xte, yte, ["x"], {},
        nn_result=nn_result,
    )

    assert result["route_execution_status"] == "nn_abstention_fallback_executed"
    assert result["nn_abstained"] is True
    assert result["nn_selected_model"] == "log_ridge"
    assert result["blend_weights"]["nn"] == [0.0] * len(yte)
    assert result["blend_weights"]["llm"] == [0.0] * len(yte)
    assert result["blend_weights"]["replacement"] == [1.0] * len(yte)



def test_exp1_nn_route_records_abstention_replacement_status(monkeypatch):
    _common(monkeypatch, "nn")
    Xtr, ytr, Xte, yte = _inputs()
    nn_result = {
        "train_r2": 0.25, "test_r2": 0.15, "success": True,
        "y_pred_train": np.full(len(ytr), 0.4),
        "y_pred_test": np.full(len(yte), 0.4),
        "abstained": True, "selected_model": "training_mean",
        "nn_edge_r2": -0.2, "ridge_edge_r2": float("nan"),
    }
    monkeypatch.setattr(
        bench, "_generate_llm_formula",
        lambda *a, **k: {"python_code": None, "llm_called": False},
    )
    result = bench._hybrid_predict_and_eval(
        "fixture", "defi", Xtr, ytr, Xte, yte, ["x"], {},
        nn_result=nn_result,
    )
    assert result["nn_abstained"] is True
    assert result["nn_selected_model"] == "training_mean"
    assert result["train_r2_source"] == "nn_abstention_training_mean"
    assert result["route_execution_status"] == "nn_abstention_fallback_executed"
    assert result["blend_weights"]["nn"] == [0.0] * len(yte)
    assert result["blend_weights"]["llm"] == [0.0] * len(yte)
    assert result["blend_weights"]["replacement"] == [1.0] * len(yte)
