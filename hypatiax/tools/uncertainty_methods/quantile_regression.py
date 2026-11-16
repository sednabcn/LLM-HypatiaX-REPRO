"""Explicit quantile-regression uncertainty adapter.

Each requested quantile has its own caller-provided estimator factory. Fitting
occurs only when fit() is explicitly called. Quantile bounds are not calibrated
unless a separate calibration procedure establishes that property.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

import numpy as np

from .base import UncertaintyEstimate, UncertaintyMethod
from .registry import UNCERTAINTY_METHODS


class QuantileRegressionUncertainty(UncertaintyMethod):
    """Fit and combine quantile-specific regressors under one shared contract.

    estimator_factories maps quantile levels in (0, 1) to fresh factories.
    Each produced estimator must expose fit(X, y) and predict(X). The caller
    configures each estimator's quantile objective/loss in its factory.
    """

    name = "quantile_regression"
    version = "1.0"
    capabilities = frozenset({
        "conditional_quantiles", "quantile_crossing_diagnostics",
        "central_quantile_intervals", "point_median_when_available",
    })

    def __init__(self, estimator_factories: Mapping[float, Callable[[], Any]], fit_kwargs: dict[str, Any] | None = None):
        if not isinstance(estimator_factories, Mapping) or len(estimator_factories) < 2:
            raise ValueError("estimator_factories must map at least two quantile levels to factories.")
        normalized: dict[float, Callable[[], Any]] = {}
        for raw_level, factory in estimator_factories.items():
            level = float(raw_level)
            if not 0.0 < level < 1.0:
                raise ValueError(f"Quantile level must be strictly between 0 and 1: {level}.")
            if level in normalized:
                raise ValueError(f"Duplicate quantile level: {level}.")
            if not callable(factory):
                raise TypeError(f"Factory for quantile {level} must be callable.")
            normalized[level] = factory
        self.quantile_levels = tuple(sorted(normalized))
        self.estimator_factories = normalized
        self.fit_kwargs = dict(fit_kwargs or {})
        self.models_: dict[float, Any] = {}
        self._fitted = False
        self._n_features: int | None = None
        self._n_train: int | None = None

    def fit(self, X_train: Any, y_train: Any, **kwargs: Any) -> "QuantileRegressionUncertainty":
        """Explicitly fit one fresh estimator for each configured quantile."""
        X = np.asarray(X_train, dtype=float)
        y = np.asarray(y_train, dtype=float).reshape(-1)
        if X.ndim != 2 or X.shape[0] < 2 or X.shape[1] < 1:
            raise ValueError("X_train must be a 2D array with at least two rows and one feature.")
        if not np.isfinite(X).all() or y.size != X.shape[0] or not np.isfinite(y).all():
            raise ValueError("X_train and aligned y_train must contain only finite values.")
        fit_options = dict(self.fit_kwargs)
        fit_options.update(kwargs)
        fitted: dict[float, Any] = {}
        seen_ids: set[int] = set()
        for level in self.quantile_levels:
            model = self.estimator_factories[level]()
            if id(model) in seen_ids:
                raise ValueError("Each quantile factory must return a fresh estimator instance.")
            seen_ids.add(id(model))
            if not callable(getattr(model, "fit", None)) or not callable(getattr(model, "predict", None)):
                raise TypeError(f"Estimator for quantile {level} must expose fit(X, y) and predict(X).")
            model.fit(X, y, **fit_options)
            fitted[level] = model
        self.models_ = fitted
        self._n_features = int(X.shape[1])
        self._n_train = int(X.shape[0])
        self._fitted = True
        return self

    def _predict_quantiles(self, X: Any) -> tuple[np.ndarray, np.ndarray]:
        if not self._fitted:
            raise RuntimeError("Call fit() explicitly before estimate().")
        inputs = np.asarray(X, dtype=float)
        if inputs.ndim != 2 or inputs.shape[1] != self._n_features or not np.isfinite(inputs).all():
            raise ValueError(f"X must be finite, 2D, and have {self._n_features} features.")
        columns = []
        for level in self.quantile_levels:
            values = np.asarray(self.models_[level].predict(inputs), dtype=float).reshape(-1)
            if values.size != inputs.shape[0] or not np.isfinite(values).all():
                raise ValueError(f"Quantile {level} estimator returned non-finite or misaligned predictions.")
            columns.append(values)
        return inputs, np.column_stack(columns)

    def estimate(self, X: Any, nominal_coverage: float = 0.95, **kwargs: Any) -> UncertaintyEstimate:
        """Return quantile predictions and central bounds when exact levels exist."""
        coverage = float(nominal_coverage)
        if not 0.0 < coverage < 1.0:
            raise ValueError("nominal_coverage must be strictly between 0 and 1.")
        inputs, values = self._predict_quantiles(X)
        quantiles = {level: values[:, index] for index, level in enumerate(self.quantile_levels)}
        alpha = (1.0 - coverage) / 2.0
        lower_level, upper_level = alpha, 1.0 - alpha
        # Arithmetic such as (1 - 0.9) / 2 can produce 0.04999999999999999,
        # which must still match a configured 0.05 quantile.
        level_tolerance = 1e-12

        def configured_level(target: float) -> float | None:
            match = min(self.quantile_levels, key=lambda level: abs(level - target))
            return match if abs(match - target) <= level_tolerance else None

        matched_lower = configured_level(lower_level)
        matched_upper = configured_level(upper_level)
        has_interval = matched_lower is not None and matched_upper is not None
        lower = quantiles[matched_lower] if has_interval else None
        upper = quantiles[matched_upper] if has_interval else None
        crossing_matrix = np.diff(values, axis=1) < 0
        crossing_rows = np.any(crossing_matrix, axis=1)
        crossing_count = int(np.count_nonzero(crossing_rows))
        median = quantiles.get(0.5)
        return UncertaintyEstimate(
            mean=median,
            lower=lower,
            upper=upper,
            quantiles=quantiles,
            components={"quantile_predictions": values},
            diagnostics={
                "quantile_levels": list(self.quantile_levels),
                "crossing_count": crossing_count,
                "crossing_rate": float(np.mean(crossing_rows)) if len(crossing_rows) else 0.0,
                "crossing_pair_counts": {
                    f"{left:g}:{right:g}": int(np.count_nonzero(values[:, i] > values[:, i + 1]))
                    for i, (left, right) in enumerate(zip(self.quantile_levels[:-1], self.quantile_levels[1:]))
                },
                "central_interval_available": has_interval,
                "required_interval_levels": [lower_level, upper_level],
            },
            metadata={
                "interval_kind": "central_conditional_quantile_interval" if has_interval else None,
                "nominal_coverage": coverage,
                "interval_calibrated": False,
                "quantile_crossing_policy": "reported_not_rearranged",
                "point_estimate": "conditional_median" if median is not None else None,
                "not_a_calibrated_prediction_interval": True,
            },
        )

    def diagnostics(self, X: Any = None) -> dict[str, Any]:
        return {
            "fitted": self._fitted,
            "quantile_levels": list(self.quantile_levels),
            "training_sample_count": self._n_train,
            "training_feature_count": self._n_features,
            "fitted_estimator_count": len(self.models_),
        }

    def metadata(self) -> dict[str, Any]:
        return {
            "method": self.name,
            "version": self.version,
            "capabilities": sorted(self.capabilities),
            "quantile_levels": list(self.quantile_levels),
            "fit_behavior": "explicit_fit_trains_one_estimator_per_quantile",
            "quantile_objective_configuration": "caller_supplied_factory",
            "crossing_policy": "diagnose_only_no_implicit_rearrangement",
            "interval_semantics": "central_conditional_quantile_interval_not_calibrated",
        }


if "quantile_regression" not in UNCERTAINTY_METHODS.names():
    UNCERTAINTY_METHODS.register("quantile_regression", QuantileRegressionUncertainty)


__all__ = ["QuantileRegressionUncertainty"]
