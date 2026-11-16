"""Feynman mechanics integration for reusable extrapolation-horizon tools."""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import numpy as np
from .extrapolation_horizon import generate_horizon_scenarios, score_predictions

_EQUATIONS = {
    "I.12.1": {
        "name": "newton_gravity", "features": ("m1", "m2", "r"),
        "formula": "G*m1*m2/r**2", "constants": {"G": 6.674e-11},
        "truth": lambda X: 6.674e-11 * X[:, 0] * X[:, 1] / np.square(X[:, 2]),
        "valid": lambda X: np.all(X > 0.0, axis=1),
        "directions": ((1, 1, -1), (1, -1, 1), (-1, 1, 1)),
    },
    "FEY_MECH_KE": {
        "name": "kinetic_energy", "features": ("m", "v"),
        "formula": "0.5*m*v**2", "constants": {},
        "truth": lambda X: 0.5 * X[:, 0] * np.square(X[:, 1]),
        "valid": lambda X: np.all(X > 0.0, axis=1),
        "directions": ((1, 1), (-1, 1), (1, -1)),
    },
    "I.18.4": {
        "name": "reduced_mass", "features": ("m1", "m2"),
        "formula": "m1*m2/(m1+m2)", "constants": {},
        "truth": lambda X: X[:, 0] * X[:, 1] / (X[:, 0] + X[:, 1]),
        "valid": lambda X: np.all(X > 0.0, axis=1),
        "directions": ((1, 1), (1, -1), (-1, 1)),
    },
}


def evaluate_feynman_horizon_curves(
    equation_id: str,
    X_train,
    y_train,
    predictors: Mapping[str, Callable],
    distances: Sequence[float] = (0.25, 0.5, 1.0, 2.0, 4.0),
    n_points: int = 120,
    interval_predictors: Mapping[str, Callable] | None = None,
) -> list[dict]:
    """Evaluate already-fitted predictors; no fitting, tuning, or LLM calls."""
    if equation_id not in _EQUATIONS:
        raise ValueError(f"Unsupported Feynman equation_id: {equation_id!r}")
    if not predictors:
        raise ValueError("predictors must contain at least one named callable.")
    spec = _EQUATIONS[equation_id]
    X = np.asarray(X_train, dtype=float)
    y = np.asarray(y_train, dtype=float).reshape(-1)
    if X.ndim != 2 or X.shape[1] != len(spec["features"]) or len(X) != len(y):
        raise ValueError(f"{equation_id} requires X_train with {len(spec['features'])} columns and matching y_train.")
    if len(X) == 0 or not np.isfinite(X).all() or not np.isfinite(y).all():
        raise ValueError("Training arrays must be non-empty and finite.")
    if not np.all(spec["valid"](X)):
        raise ValueError(f"{equation_id} training features violate the positive physical domain.")

    scenarios = generate_horizon_scenarios(
        X, distances=distances, strategy="both",
        feature_names=spec["features"], n_points=n_points,
    )
    scenarios += generate_horizon_scenarios(
        X, distances=distances, strategy="combinations",
        feature_names=spec["features"], directions=spec["directions"],
        n_points=n_points,
    )
    intervals = interval_predictors or {}
    records = []
    for method, predict_fn in predictors.items():
        if not callable(predict_fn):
            raise TypeError(f"Predictor for {method!r} is not callable.")
        try:
            train_pred = np.asarray(predict_fn(X), dtype=float).reshape(-1)
            if train_pred.shape != y.shape or not np.isfinite(train_pred).all():
                raise ValueError("training predictions have invalid shape or non-finite values")
            train_status = "available"
        except Exception as exc:
            train_pred = None
            train_status = f"unavailable:{type(exc).__name__}:{exc}"

        for scenario in scenarios:
            points = np.asarray(scenario["X_test"], dtype=float)
            valid = spec["valid"](points)
            valid_points = points[valid]
            evaluation = {k: v for k, v in scenario.items() if k != "X_test"}
            evaluation.update({
                "n_generated": int(len(points)),
                "n_domain_valid": int(len(valid_points)),
                "domain_valid_fraction": float(np.mean(valid)),
            })
            record = {
                "schema_version": "1.0",
                "equation": equation_id,
                "equation_name": spec["name"],
                "base_function": {"family": spec["name"], "formula": spec["formula"], "constants": spec["constants"]},
                "method": str(method),
                "evaluation": evaluation,
                "provenance": {
                    "training_reference": "caller-supplied exact training split",
                    "model_retrained": False,
                    "training_predictions_status": train_status,
                },
            }
            if len(valid_points) < 2:
                record["metrics"] = {}
                record["diagnostics"] = {
                    "far_prediction_status": "insufficient_domain_valid_points",
                    "domain_status": "fewer_than_two_valid_points",
                }
                records.append(record)
                continue
            try:
                truth = spec["truth"](valid_points)
                pred = np.asarray(predict_fn(valid_points), dtype=float).reshape(-1)
                lower = upper = None
                interval_fn = intervals.get(method)
                if interval_fn is not None:
                    bounds = interval_fn(valid_points)
                    if not isinstance(bounds, (tuple, list)) or len(bounds) != 2:
                        raise ValueError("interval predictor must return (lower, upper)")
                    lower, upper = bounds
                scored = score_predictions(truth, pred, y, train_pred, lower, upper)
                record["metrics"] = scored["metrics"]
                record["diagnostics"] = {
                    **scored["diagnostics"],
                    "domain_status": "partially_truncated" if not np.all(valid) else "fully_valid",
                }
            except Exception as exc:
                record["metrics"] = {}
                record["diagnostics"] = {
                    "far_prediction_status": "evaluation_failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "domain_status": "partially_truncated" if not np.all(valid) else "fully_valid",
                }
            records.append(record)
    return records


__all__ = ["evaluate_feynman_horizon_curves"]
