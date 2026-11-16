"""Method-independent evaluation of point predictions and supplied intervals."""
import numpy as np
from .base import UncertaintyEstimate


def evaluate_estimate(y_true, estimate: UncertaintyEstimate, nominal_coverage: float = 0.95):
    """Evaluate estimates; never infer intervals from scale or calibrate implicitly."""
    truth = np.asarray(y_true, dtype=float).reshape(-1)
    if truth.size == 0 or not np.isfinite(truth).all():
        raise ValueError("y_true must be a non-empty finite vector.")
    estimate.validate(truth.size)
    result = {"n_evaluated": int(truth.size), "point_metrics": {}, "interval_metrics": {}}
    if estimate.mean is not None:
        residual = truth - estimate.mean
        denominator = float(np.sum((truth - np.mean(truth)) ** 2))
        result["point_metrics"] = {
            "mae": float(np.mean(np.abs(residual))),
            "rmse": float(np.sqrt(np.mean(residual ** 2))),
            "bias": float(np.mean(estimate.mean - truth)),
            "r2": float(1.0 - np.sum(residual ** 2) / denominator) if denominator > 0 else None,
        }
    if estimate.lower is not None:
        level = float(nominal_coverage)
        if not 0.0 < level < 1.0:
            raise ValueError("nominal_coverage must be strictly between 0 and 1.")
        covered = (truth >= estimate.lower) & (truth <= estimate.upper)
        result["interval_metrics"] = {
            "nominal_coverage": level,
            "empirical_coverage": float(np.mean(covered)),
            "mean_interval_width": float(np.mean(estimate.upper - estimate.lower)),
            "n_evaluated": int(truth.size),
            "interval_kind": "prediction_interval",
        }
    return result
