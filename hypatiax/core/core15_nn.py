"""Experimental scaffolding; NOT a manuscript-faithful Core-15 NN.

This file currently wraps sklearn MLPRegressor and supplies a symmetric
training-only PCA edge split. Neither matches the Core-15 manuscript
specification: a three-residual-block PyTorch MLP, plus an LLM-formula probe
on the upper 20% of training rows ordered by the first PCA projection.
Do not use these helpers to claim that the Core-15 NN or Stage-3 probe is
implemented.

The current HybridDiscoverySystem v50_2 benchmark path preserves the raw LLM
candidate metadata, but does not produce the manuscript's residual-NN and
blended query predictions. The Phase-3 adapter therefore rejects the
NN-dependent gates rather than silently substituting PySR predictions or
running a no-op ablation. Integration also requires the unspecified residual
block widths/training stopping rule and a frozen training-only degradation
threshold; do not invent these protocol choices.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler


@dataclass
class Core15NN:
    """Small deterministic MLP with train-fitted input/output scaling."""

    seed: int = 42
    hidden_layer_sizes: tuple[int, ...] = (128, 64, 32)
    max_iter: int = 1000
    learning_rate_init: float = 0.003

    def __post_init__(self):
        self.x_scaler = StandardScaler()
        self.y_scaler = StandardScaler()
        self.model = MLPRegressor(
            hidden_layer_sizes=self.hidden_layer_sizes,
            activation="relu",
            solver="adam",
            learning_rate_init=self.learning_rate_init,
            max_iter=self.max_iter,
            early_stopping=False,
            random_state=int(self.seed),
            shuffle=True,
        )
        self.fitted = False

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float).reshape(-1)
        if X.ndim != 2 or X.shape[0] != y.size or X.shape[0] < 8:
            raise ValueError("Core15NN requires aligned 2-D X/y with at least 8 rows")
        if not np.isfinite(X).all() or not np.isfinite(y).all():
            raise ValueError("Core15NN training data must be finite")
        xs = self.x_scaler.fit_transform(X)
        ys = self.y_scaler.fit_transform(y.reshape(-1, 1)).ravel()
        self.model.fit(xs, ys)
        self.fitted = True
        return self

    def predict(self, X):
        if not self.fitted:
            raise RuntimeError("Core15NN must be fitted before predict")
        X = np.asarray(X, dtype=float)
        if X.ndim != 2 or X.shape[1] != self.x_scaler.n_features_in_:
            raise ValueError("Core15NN prediction feature shape mismatch")
        pred = self.model.predict(self.x_scaler.transform(X))
        result = self.y_scaler.inverse_transform(pred.reshape(-1, 1)).ravel()
        if not np.isfinite(result).all():
            raise FloatingPointError("Core15NN produced non-finite predictions")
        return result


def training_edge_indices(X, edge_fraction=0.15):
    """Return deterministic central-fit and symmetric edge-probe row indices.

    Rows are ordered by their first PCA score; PCA is fitted only on X (training
    covariates). No target values or held-out data participate in the split.
    """
    from sklearn.decomposition import PCA

    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or X.shape[0] < 12 or not np.isfinite(X).all():
        raise ValueError("edge probe needs at least 12 finite training rows")
    if not isinstance(edge_fraction, (int, float)) or not 0.0 < edge_fraction < 0.5:
        raise ValueError("edge_fraction must be between 0 and 0.5")
    score = PCA(n_components=1, svd_solver="full").fit_transform(
        StandardScaler().fit_transform(X)
    ).ravel()
    order = np.argsort(score, kind="mergesort")
    n_edge = max(2, int(math.ceil(len(order) * float(edge_fraction) / 2.0)))
    edge = np.concatenate((order[:n_edge], order[-n_edge:]))
    mask = np.ones(len(order), dtype=bool)
    mask[edge] = False
    core = np.flatnonzero(mask)
    if core.size < 8:
        raise ValueError("edge fraction leaves too few central training rows")
    return core, np.sort(edge)


def blend_predictions(llm_predictions, nn_predictions, p_ood, alpha=0.3):
    """Apply the manuscript's per-query LLM/NN blend, with strict validation."""
    llm = np.asarray(llm_predictions, dtype=float).reshape(-1)
    nn = np.asarray(nn_predictions, dtype=float).reshape(-1)
    p = np.asarray(p_ood, dtype=float).reshape(-1)
    if llm.size == 0 or llm.shape != nn.shape or llm.shape != p.shape:
        raise ValueError("LLM, NN and OOD arrays must have identical non-empty shapes")
    if not (np.isfinite(llm).all() and np.isfinite(nn).all()
            and np.isfinite(p).all() and np.all((p >= 0) & (p <= 1))):
        raise ValueError("blend inputs must be finite and OOD probabilities in [0, 1]")
    if not isinstance(alpha, (int, float)) or not math.isfinite(alpha) or not 0 <= alpha <= 1:
        raise ValueError("alpha must be finite and in [0, 1]")
    w_llm = float(alpha) + (1.0 - float(alpha)) * p
    w_nn = 1.0 - w_llm
    return {
        "predictions": w_llm * llm + w_nn * nn,
        "llm_weights": w_llm,
        "nn_weights": w_nn,
    }
