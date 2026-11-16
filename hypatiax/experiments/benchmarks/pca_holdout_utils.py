"""Small, testable helpers for reconstructing the exact PCA holdout predictor."""
from __future__ import annotations

import numpy as np


def compose_hybrid_predictor(decision, formula_predictor=None,
                             nn_predictor=None, blend_weights=None):
    """Compose the exact route selected on training data for external inference.

    Returns None when the selected route cannot be reproduced. It never
    fabricates predictions from summary metrics.
    """
    route = str(decision or "").strip().lower()

    def checked(predictor, X, label):
        if not callable(predictor):
            raise ValueError(f"{label} predictor is unavailable")
        values = np.asarray(predictor(X), dtype=float).reshape(-1)
        if values.shape[0] != np.asarray(X).shape[0] or not np.isfinite(values).all():
            raise ValueError(f"{label} predictor returned invalid values")
        return values

    if route in {"llm", "fitted_llm"}:
        if not callable(formula_predictor):
            return None

        def predict(X):
            return checked(formula_predictor, X, "formula")
        return predict

    if route == "nn":
        if not callable(nn_predictor):
            return None

        def predict(X):
            return checked(nn_predictor, X, "neural network")
        return predict

    if route == "ensemble":
        if not callable(formula_predictor) or not callable(nn_predictor):
            return None
        if not isinstance(blend_weights, dict):
            return None
        try:
            w_formula = float(blend_weights["llm"])
            w_nn = float(blend_weights["nn"])
        except (KeyError, TypeError, ValueError):
            return None
        if (
            not np.isfinite([w_formula, w_nn]).all()
            or w_formula < 0.0
            or w_nn < 0.0
            or not np.isclose(w_formula + w_nn, 1.0, rtol=0.0, atol=1e-8)
        ):
            return None

        def predict(X):
            formula_values = checked(formula_predictor, X, "formula")
            nn_values = checked(nn_predictor, X, "neural network")
            if formula_values.shape != nn_values.shape:
                raise ValueError("formula and neural network prediction shapes differ")
            return w_formula * formula_values + w_nn * nn_values
        return predict

    return None
