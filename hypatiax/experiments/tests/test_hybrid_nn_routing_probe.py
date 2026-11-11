import numpy as np

from hypatiax.core.generation.hybrid_defi_system import hybrid_system_nn_defi_domain as hybrid
from hypatiax.core.routing import training_edge_split_indices


def test_hybrid_edge_probe_fits_only_central_training_rows(monkeypatch):
    x = np.linspace(-4.0, 4.0, 100).reshape(-1, 1)
    y = x[:, 0] ** 2
    core_idx, edge_idx = training_edge_split_indices(x, edge_fraction=0.15)
    captured = {}

    def fake_train_nn_model(X_fit, y_fit, seed=None):
        captured["X_fit"] = np.asarray(X_fit).copy()
        captured["y_fit"] = np.asarray(y_fit).copy()
        captured["seed"] = seed
        return object(), None, None

    def fake_nn_predict(model, scaler_x, scaler_y, X_eval):
        return np.asarray(X_eval)[:, 0] ** 2

    monkeypatch.setattr(hybrid, "train_nn_model", fake_train_nn_model)
    monkeypatch.setattr(hybrid, "nn_predict", fake_nn_predict)

    result = hybrid._training_only_nn_edge_probe(x, y, seed=123, edge_fraction=0.15)

    assert result["status"] == "ok"
    assert result["n_core"] == len(core_idx)
    assert result["n_edge"] == len(edge_idx)
    assert np.array_equal(captured["X_fit"], x[core_idx])
    assert np.array_equal(captured["y_fit"], y[core_idx])
    assert captured["seed"] == 123
    assert result["delta"] == 0.0


def test_hybrid_edge_probe_rejects_degenerate_covariates():
    x = np.ones((30, 2))
    y = np.arange(30, dtype=float)
    result = hybrid._training_only_nn_edge_probe(x, y, seed=123, edge_fraction=0.15)
    assert result["status"] == "error"
    assert result["delta"] is None
