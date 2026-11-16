"""Reusable, model-agnostic tools for evaluating extrapolation horizons.

The module never fits or retrains estimators. Callers provide an already-fitted
predictor and optionally a prediction-interval function. Distances are measured
in units of each feature's training-range width.

For synthetic equations, y_true_fn can evaluate the known equation at generated
points. For real data, use held-out observations and score_predictions directly.
Never use far test targets to fit, scale, or calibrate the model.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

import numpy as np


def _as_2d_float(values, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim == 1:
        array = array.reshape(-1, 1)
    if array.ndim != 2 or array.shape[0] == 0 or array.shape[1] == 0:
        raise ValueError(f"{name} must be a non-empty 1D or 2D numeric array.")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} contains NaN or infinite values.")
    return array


def generate_horizon_scenarios(
    X_train,
    distances: Sequence[float] = (0.25, 0.5, 1.0, 2.0, 4.0),
    strategy: str = "both",
    feature_indices: Sequence[int] | None = None,
    feature_names: Sequence[str] | None = None,
    n_points: int = 100,
    directions: Sequence[Sequence[float]] | None = None,
    periods: Mapping[int, float] | None = None,
) -> list[dict]:
    """Generate upper/lower or multivariate extrapolation point sets.

    strategy is upper, lower, both, or combinations. Single-feature scenarios
    move one feature beyond its observed boundary and hold others at medians.
    Combination directions are vectors of -1/0/+1, one per feature. Distances
    are multiples of each moved feature's training-range width.

    periods optionally maps feature indices to known positive periods. Period
    distance is reported as metadata; frequency and phase are never inferred.
    """
    X = _as_2d_float(X_train, "X_train")
    n_features = X.shape[1]
    indices = list(range(n_features)) if feature_indices is None else [int(i) for i in feature_indices]
    if not indices or len(set(indices)) != len(indices):
        raise ValueError("feature_indices must be non-empty and unique.")
    if any(i < 0 or i >= n_features for i in indices):
        raise ValueError("feature_indices contains an out-of-range column.")
    names = list(feature_names) if feature_names is not None else [f"x{i}" for i in range(n_features)]
    if len(names) != n_features:
        raise ValueError("feature_names length must match X_train columns.")
    if strategy not in {"upper", "lower", "both", "combinations"}:
        raise ValueError("strategy must be upper, lower, both, or combinations.")
    if not isinstance(n_points, int) or n_points < 1:
        raise ValueError("n_points must be a positive integer.")
    distance_values = [float(v) for v in distances]
    if not distance_values or any(not math.isfinite(v) or v <= 0 for v in distance_values):
        raise ValueError("distances must contain finite positive values.")

    minima, maxima = X.min(axis=0), X.max(axis=0)
    ranges, center = maxima - minima, np.median(X, axis=0)
    if any(ranges[i] <= 0 for i in indices):
        raise ValueError("Selected features must have non-zero training ranges.")

    if strategy == "combinations":
        if not directions:
            raise ValueError("directions are required for combinations strategy.")
        direction_list = [np.asarray(d, dtype=float) for d in directions]
        for direction in direction_list:
            if direction.shape != (n_features,) or not np.isin(direction, [-1, 0, 1]).all():
                raise ValueError("Each direction must contain -1/0/+1 for every feature.")
            if not np.any(direction):
                raise ValueError("A combination direction cannot be all zeros.")
            if any(direction[i] != 0 and i not in indices for i in range(n_features)):
                raise ValueError("A direction moves a feature not listed in feature_indices.")
    else:
        signs = ([1] if strategy == "upper" else [-1] if strategy == "lower" else [1, -1])
        direction_list = []
        for index in indices:
            for sign in signs:
                direction = np.zeros(n_features, dtype=float)
                direction[index] = sign
                direction_list.append(direction)

    scenarios = []
    for direction in direction_list:
        moved = np.flatnonzero(direction)
        for distance in distance_values:
            fractions = np.linspace(0.05, 1.0, n_points)
            points = np.tile(center, (n_points, 1))
            for index in moved:
                sign = direction[index]
                boundary = maxima[index] if sign > 0 else minima[index]
                points[:, index] = boundary + sign * fractions * distance * ranges[index]
            scenario = {
                "strategy": "feature_combination" if strategy == "combinations" else strategy,
                "direction": [int(v) for v in direction],
                "features_moved": [names[i] for i in moved],
                "distance": float(distance),
                "distance_unit": "training_range_width",
                "n_points": int(n_points),
                "X_test": points,
            }
            if periods:
                scenario["distance_in_periods"] = {
                    names[i]: float(distance * ranges[i] / periods[i])
                    for i in moved if i in periods and periods[i] is not None and periods[i] > 0
                }
            scenarios.append(scenario)
    return scenarios


def score_predictions(y_true, y_pred, y_train, y_pred_train=None,
                      interval_lower=None, interval_upper=None) -> dict:
    """Compute far metrics, train-normalized error and optional interval metrics."""
    truth = np.asarray(y_true, dtype=float).reshape(-1)
    pred = np.asarray(y_pred, dtype=float).reshape(-1)
    train = np.asarray(y_train, dtype=float).reshape(-1)
    if truth.shape != pred.shape or truth.size == 0:
        raise ValueError("y_true and y_pred must have the same non-zero shape.")
    if train.size == 0 or not np.isfinite(train).all():
        raise ValueError("y_train must be non-empty and finite.")
    if not np.isfinite(truth).all() or not np.isfinite(pred).all():
        raise ValueError("y_true and y_pred must be finite.")

    residual = pred - truth
    rmse = float(np.sqrt(np.mean(residual ** 2)))
    ss_total = float(np.sum((truth - np.mean(truth)) ** 2))
    train_std = float(np.std(train))
    metrics = {
        "far_r2": None if ss_total <= 0 else float(1.0 - np.sum(residual ** 2) / ss_total),
        "far_rmse": rmse,
        "normalized_far_rmse": None if train_std <= 0 else float(rmse / train_std),
        "far_train_rmse_ratio_pct": None,
    }
    diagnostics = {
        "far_prediction_status": "scored",
        "normalized_error_status": "scored" if train_std > 0 else "undefined_zero_train_target_std",
        "far_train_rmse_ratio_status": "not_available",
        "interval_status": "not_available",
    }
    if y_pred_train is None:
        diagnostics["far_train_rmse_ratio_status"] = "training_predictions_unavailable"
    else:
        train_pred = np.asarray(y_pred_train, dtype=float).reshape(-1)
        if train_pred.shape != train.shape or not np.isfinite(train_pred).all():
            diagnostics["far_train_rmse_ratio_status"] = "invalid_training_predictions"
        else:
            train_rmse = float(np.sqrt(np.mean((train_pred - train) ** 2)))
            if train_rmse <= 0:
                diagnostics["far_train_rmse_ratio_status"] = "undefined_zero_training_rmse"
            else:
                metrics["far_train_rmse_ratio_pct"] = float(100.0 * rmse / train_rmse)
                diagnostics["far_train_rmse_ratio_status"] = "scored"

    if interval_lower is not None or interval_upper is not None:
        if interval_lower is None or interval_upper is None:
            diagnostics["interval_status"] = "incomplete_interval_bounds"
        else:
            lower = np.asarray(interval_lower, dtype=float).reshape(-1)
            upper = np.asarray(interval_upper, dtype=float).reshape(-1)
            if lower.shape != truth.shape or upper.shape != truth.shape:
                diagnostics["interval_status"] = "interval_shape_mismatch"
            elif (not np.isfinite(lower).all() or not np.isfinite(upper).all()
                  or np.any(lower > upper)):
                diagnostics["interval_status"] = "invalid_interval_bounds"
            else:
                width = upper - lower
                metrics.update({
                    "interval_coverage": float(np.mean((truth >= lower) & (truth <= upper))),
                    "mean_interval_width": float(np.mean(width)),
                    "normalized_interval_width": None if train_std <= 0 else float(np.mean(width) / train_std),
                })
                diagnostics["interval_status"] = "scored"
    return {"metrics": metrics, "diagnostics": diagnostics}


def evaluate_horizon_scenarios(
    scenarios: Iterable[dict],
    predict_fn: Callable,
    y_train,
    y_true_fn: Callable,
    train_predictions=None,
    interval_fn: Callable | None = None,
    method: str = "unspecified",
    equation: str = "unspecified",
    base_function: Mapping | None = None,
) -> list[dict]:
    """Evaluate generated scenarios with a fitted predictor; no fitting occurs.

    y_true_fn(X) returns reference targets. interval_fn(X) returns either a
    (lower, upper) pair or a mapping with lower and upper arrays.
    """
    records = []
    for scenario in scenarios:
        X_test = _as_2d_float(scenario["X_test"], "scenario X_test")
        prediction = np.asarray(predict_fn(X_test), dtype=float).reshape(-1)
        truth = np.asarray(y_true_fn(X_test), dtype=float).reshape(-1)
        lower = upper = None
        if interval_fn is not None:
            bounds = interval_fn(X_test)
            if isinstance(bounds, Mapping):
                lower, upper = bounds.get("lower"), bounds.get("upper")
            else:
                if len(bounds) != 2:
                    raise ValueError("interval_fn must return (lower, upper).")
                lower, upper = bounds
        scored = score_predictions(truth, prediction, y_train, train_predictions, lower, upper)
        records.append({
            "schema_version": "1.0",
            "equation": equation,
            "base_function": dict(base_function or {}),
            "method": method,
            "evaluation": {k: v for k, v in scenario.items() if k != "X_test"},
            "metrics": scored["metrics"],
            "diagnostics": scored["diagnostics"],
            "provenance": {
                "n_far": int(len(truth)),
                "training_reference": "training split only",
                "model_retrained": False,
            },
        })
    return records


def _json_safe(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def write_results_json(records: Iterable[Mapping], output_path, indent: int = 2) -> Path:
    """Write JSON records atomically, supporting NumPy values."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    payload = {"schema_version": "1.0", "results": _json_safe(list(records))}
    temporary.write_text(json.dumps(payload, indent=indent, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)
    return path


def plot_horizon_curves(records: Iterable[Mapping], metric: str = "far_r2",
                        output_path=None, title: str | None = None):
    """Plot one distance curve per method; returns the Matplotlib figure."""
    import matplotlib.pyplot as plt  # Optional dependency, loaded only on demand.

    grouped = {}
    for record in records:
        value = record.get("metrics", {}).get(metric)
        distance = record.get("evaluation", {}).get("distance")
        if value is None or distance is None:
            continue
        grouped.setdefault(record.get("method", "unspecified"), []).append((float(distance), float(value)))
    if not grouped:
        raise ValueError(f"No finite values found for metric {metric!r}.")
    figure, axis = plt.subplots()
    for method, points in sorted(grouped.items()):
        points.sort(key=lambda pair: pair[0])
        axis.plot([p[0] for p in points], [p[1] for p in points], marker="o", label=method)
    axis.set_xlabel("Extrapolation distance (training-range widths)")
    axis.set_ylabel(metric.replace("_", " "))
    axis.set_title(title or f"{metric.replace('_', ' ')} vs extrapolation distance")
    axis.grid(True, alpha=0.3)
    axis.legend()
    figure.tight_layout()
    if output_path is not None:
        figure.savefig(output_path, dpi=160, bbox_inches="tight")
    return figure


__all__ = [
    "generate_horizon_scenarios",
    "score_predictions",
    "evaluate_horizon_scenarios",
    "write_results_json",
    "plot_horizon_curves",
]
