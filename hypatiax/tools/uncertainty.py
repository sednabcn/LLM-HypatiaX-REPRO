"""Model-agnostic prediction intervals and split-conformal calibration.

The module consumes predictions from a held-out calibration split and never
fits or changes the predictive model. Split conformal's finite-sample marginal
coverage statement requires exchangeability; it is not guaranteed under
extrapolation or distribution shift.
"""
from __future__ import annotations

import math
from typing import Iterable

import numpy as np


def _vector(values, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=float).reshape(-1)
    if array.size == 0 or not np.isfinite(array).all():
        raise ValueError(f"{name} must be non-empty and finite.")
    return array


class SplitConformalRegressor:
    """Absolute-residual split conformal intervals for arbitrary regressors."""

    def __init__(self, nominal_coverage: float = 0.95):
        self.nominal_coverage = self._validate_coverage(nominal_coverage)
        self._scores: np.ndarray | None = None
        self.n_calibration = 0

    @staticmethod
    def _validate_coverage(coverage: float) -> float:
        value = float(coverage)
        if not math.isfinite(value) or not 0.0 < value < 1.0:
            raise ValueError("coverage must be strictly between 0 and 1.")
        return value

    def fit(self, y_calibration, calibration_predictions):
        """Calibrate using held-out targets and predictions from a frozen model."""
        truth = _vector(y_calibration, "y_calibration")
        pred = _vector(calibration_predictions, "calibration_predictions")
        if truth.shape != pred.shape:
            raise ValueError("Calibration targets and predictions must have equal length.")
        self._scores = np.sort(np.abs(truth - pred))
        self.n_calibration = int(truth.size)
        return self

    def quantile(self, coverage: float | None = None) -> float:
        """Return the finite-sample conformal residual quantile."""
        if self._scores is None:
            raise RuntimeError("Call fit before requesting a conformal quantile.")
        level = self.nominal_coverage if coverage is None else self._validate_coverage(coverage)
        rank = int(math.ceil((self.n_calibration + 1) * level))
        if rank > self.n_calibration:
            return float("inf")
        return float(self._scores[rank - 1])

    def predict_interval(self, predictions, coverage: float | None = None):
        """Return symmetric prediction bounds around point predictions."""
        pred = _vector(predictions, "predictions")
        radius = self.quantile(coverage)
        return pred - radius, pred + radius

    @property
    def calibration_metadata(self) -> dict:
        if self._scores is None:
            raise RuntimeError("Call fit before requesting calibration metadata.")
        return {
            "method": "split_conformal_absolute_residual",
            "calibration_n": self.n_calibration,
            "nominal_coverage": self.nominal_coverage,
            "calibration_score": "absolute_residual",
            "coverage_assumption": "exchangeability_of_calibration_and_evaluation_observations",
            "extra_domain_guarantee": False,
        }


def evaluate_prediction_intervals(
    y_true, lower, upper, nominal_coverage: float, reference_scale: float | None = None
) -> dict:
    """Evaluate supplied prediction bounds; no fitting or calibration occurs."""
    truth = _vector(y_true, "y_true")
    lo = np.asarray(lower, dtype=float).reshape(-1)
    hi = np.asarray(upper, dtype=float).reshape(-1)
    level = SplitConformalRegressor._validate_coverage(nominal_coverage)
    if lo.shape != truth.shape or hi.shape != truth.shape:
        raise ValueError("y_true, lower, and upper must have equal lengths.")
    if np.isnan(lo).any() or np.isnan(hi).any() or np.any(lo > hi):
        raise ValueError("Bounds must be non-NaN and satisfy lower <= upper.")
    widths = hi - lo
    alpha = 1.0 - level
    interval_score = widths.copy()
    below, above = truth < lo, truth > hi
    interval_score[below] += (2.0 / alpha) * (lo[below] - truth[below])
    interval_score[above] += (2.0 / alpha) * (truth[above] - hi[above])
    mean_width = float(np.mean(widths))
    result = {
        "nominal_coverage": level,
        "empirical_coverage": float(np.mean((truth >= lo) & (truth <= hi))),
        "mean_interval_width": mean_width,
        "mean_interval_score": float(np.mean(interval_score)),
        "n_evaluated": int(truth.size),
        "interval_kind": "prediction_interval",
        "absolute_coverage_gap": abs(float(np.mean((truth >= lo) & (truth <= hi))) - level),
    }
    if reference_scale is not None:
        scale = float(reference_scale)
        if not math.isfinite(scale) or scale <= 0:
            raise ValueError("reference_scale must be finite and positive.")
        result["normalized_mean_interval_width"] = mean_width / scale
        result["normalization_reference"] = "caller_supplied_training_scale"
    return result


def evaluate_interval_levels(y_true, intervals: Iterable[dict], reference_scale=None) -> list[dict]:
    """Evaluate multiple nominal levels; each item has coverage, lower, and upper."""
    return [
        evaluate_prediction_intervals(
            y_true, item["lower"], item["upper"], item["coverage"], reference_scale
        )
        for item in intervals
    ]


__all__ = [
    "SplitConformalRegressor",
    "evaluate_prediction_intervals",
    "evaluate_interval_levels",
]
