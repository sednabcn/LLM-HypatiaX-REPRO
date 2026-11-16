"""Explicit bootstrap uncertainty estimator using caller-provided model factories.

Fitting occurs only when fit() is explicitly called. Intervals summarize the
bootstrap distribution of fitted conditional-mean predictions; they are not
automatically calibrated prediction intervals for future observations.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np

from .base import UncertaintyEstimate, UncertaintyMethod
from .registry import UNCERTAINTY_METHODS


class BootstrapUncertainty(UncertaintyMethod):
    """Fit bootstrap replicates using pairs, residual, or moving-block resampling.

    estimator_factory must return a fresh estimator exposing fit(X, y) and
    predict(X). No estimator is created or fitted by construction or estimate().
    Calling fit() explicitly performs n_bootstrap fits (plus one reference fit
    for residual resampling).
    """

    name = "bootstrap"
    version = "1.0"
    capabilities = frozenset({
        "bootstrap_model_uncertainty", "point_mean", "predictive_samples",
        "pairs_resampling", "residual_resampling", "moving_block_resampling",
    })

    def __init__(
        self,
        estimator_factory: Callable[[], Any],
        n_bootstrap: int = 200,
        resampling: str = "pairs",
        random_state: int | None = None,
        block_size: int | None = None,
        fit_kwargs: dict[str, Any] | None = None,
    ):
        if not callable(estimator_factory):
            raise TypeError("estimator_factory must be callable.")
        if isinstance(n_bootstrap, bool) or int(n_bootstrap) < 2:
            raise ValueError("n_bootstrap must be an integer of at least 2.")
        if int(n_bootstrap) != n_bootstrap:
            raise ValueError("n_bootstrap must be an integer.")
        if resampling not in {"pairs", "residual", "block"}:
            raise ValueError("resampling must be 'pairs', 'residual', or 'block'.")
        if resampling == "block":
            if block_size is None or isinstance(block_size, bool) or int(block_size) < 1:
                raise ValueError("block_size must be a positive integer for block resampling.")
        elif block_size is not None:
            raise ValueError("block_size is only valid for block resampling.")
        self.estimator_factory = estimator_factory
        self.n_bootstrap = int(n_bootstrap)
        self.resampling = resampling
        self.random_state = random_state
        self.block_size = int(block_size) if block_size is not None else None
        self.fit_kwargs = dict(fit_kwargs or {})
        self.models_: list[Any] = []
        self.resample_indices_: list[np.ndarray] = []
        self._fitted = False
        self._n_features: int | None = None
        self._n_train: int | None = None
        self._rng: np.random.Generator | None = None

    @staticmethod
    def _new_estimator(factory: Callable[[], Any], seen_ids: set[int]) -> Any:
        model = factory()
        if id(model) in seen_ids:
            raise ValueError("estimator_factory must return a fresh estimator for every replicate.")
        seen_ids.add(id(model))
        if not callable(getattr(model, "fit", None)) or not callable(getattr(model, "predict", None)):
            raise TypeError("Each factory result must expose fit(X, y) and predict(X).")
        return model

    @staticmethod
    def _predictions(model: Any, X: np.ndarray, expected: int, label: str) -> np.ndarray:
        values = np.asarray(model.predict(X), dtype=float).reshape(-1)
        if values.size != expected or not np.isfinite(values).all():
            raise ValueError(f"{label} returned non-finite or misaligned predictions.")
        return values

    def _draw_indices(self, n: int) -> np.ndarray:
        assert self._rng is not None
        if self.resampling == "block":
            size = self.block_size
            assert size is not None
            starts = self._rng.integers(0, n - size + 1, size=int(np.ceil(n / size)))
            indices = np.concatenate([np.arange(start, start + size) for start in starts])
            return indices[:n].astype(int, copy=False)
        return self._rng.integers(0, n, size=n, dtype=int)

    def fit(self, X_train: Any, y_train: Any, **kwargs: Any) -> "BootstrapUncertainty":
        """Explicitly fit bootstrap replicates; no fitting occurs before this call."""
        X = np.asarray(X_train, dtype=float)
        y = np.asarray(y_train, dtype=float).reshape(-1)
        if X.ndim != 2 or X.shape[0] < 2 or X.shape[1] < 1:
            raise ValueError("X_train must be a 2D array with at least two rows and one feature.")
        if not np.isfinite(X).all() or y.size != X.shape[0] or not np.isfinite(y).all():
            raise ValueError("X_train and aligned y_train must contain only finite values.")
        if self.resampling == "block" and self.block_size > X.shape[0]:
            raise ValueError("block_size cannot exceed the number of training rows.")

        self._rng = np.random.default_rng(self.random_state)
        self.models_ = []
        self.resample_indices_ = []
        seen_ids: set[int] = set()
        fit_options = dict(self.fit_kwargs)
        fit_options.update(kwargs)
        reference_predictions = None
        residuals = None

        if self.resampling == "residual":
            reference = self._new_estimator(self.estimator_factory, seen_ids)
            reference.fit(X, y, **fit_options)
            reference_predictions = self._predictions(reference, X, X.shape[0], "Reference estimator")
            residuals = y - reference_predictions
            residuals = residuals - np.mean(residuals)

        for replicate in range(self.n_bootstrap):
            indices = self._draw_indices(X.shape[0])
            if self.resampling == "residual":
                assert reference_predictions is not None and residuals is not None
                sampled_residuals = residuals[self._rng.integers(0, residuals.size, size=residuals.size)]
                X_rep, y_rep = X, reference_predictions + sampled_residuals
            else:
                X_rep, y_rep = X[indices], y[indices]
            model = self._new_estimator(self.estimator_factory, seen_ids)
            model.fit(X_rep, y_rep, **fit_options)
            self.models_.append(model)
            self.resample_indices_.append(indices.copy())

        self._n_features = int(X.shape[1])
        self._n_train = int(X.shape[0])
        self._fitted = True
        return self

    def estimate(
        self, X: Any, nominal_coverage: float = 0.95, **kwargs: Any
    ) -> UncertaintyEstimate:
        """Summarize bootstrap model predictions without fitting or refitting."""
        if not self._fitted:
            raise RuntimeError("Call fit() explicitly before estimate().")
        coverage = float(nominal_coverage)
        if not 0.0 < coverage < 1.0:
            raise ValueError("nominal_coverage must be strictly between 0 and 1.")
        inputs = np.asarray(X, dtype=float)
        if inputs.ndim != 2 or inputs.shape[1] != self._n_features or not np.isfinite(inputs).all():
            raise ValueError(f"X must be finite, 2D, and have {self._n_features} features.")
        draws = np.stack([
            self._predictions(model, inputs, inputs.shape[0], f"Bootstrap replicate {i}")
            for i, model in enumerate(self.models_)
        ], axis=1)
        alpha = (1.0 - coverage) / 2.0
        lower, upper = np.quantile(draws, [alpha, 1.0 - alpha], axis=1)
        return UncertaintyEstimate(
            mean=np.mean(draws, axis=1),
            scale=np.std(draws, axis=1, ddof=1),
            lower=lower,
            upper=upper,
            samples=draws,
            components={"bootstrap_predictions": draws},
            diagnostics={
                "bootstrap_replicates": len(self.models_),
                "resampling": self.resampling,
                "resample_index_count": len(self.resample_indices_),
                "interval_calibrated": False,
            },
            metadata={
                "interval_kind": "bootstrap_model_uncertainty_percentile",
                "interval_semantics": "sampling_uncertainty_of_fitted_conditional_mean",
                "nominal_coverage": coverage,
                "not_a_calibrated_prediction_interval": True,
                "does_not_include_future_observation_noise": True,
            },
        )

    def diagnostics(self, X: Any = None) -> dict[str, Any]:
        return {
            "fitted": self._fitted,
            "bootstrap_replicates": len(self.models_),
            "resampling": self.resampling,
            "block_size": self.block_size,
            "training_sample_count": self._n_train,
            "training_feature_count": self._n_features,
            "random_state": self.random_state,
            "resampling_unit": "rows" if self.resampling != "block" else "contiguous_ordered_rows",
        }

    def metadata(self) -> dict[str, Any]:
        return {
            "method": self.name,
            "version": self.version,
            "capabilities": sorted(self.capabilities),
            "resampling": self.resampling,
            "bootstrap_replicates": self.n_bootstrap,
            "random_state": self.random_state,
            "block_size": self.block_size,
            "fit_behavior": "explicit_fit_trains_bootstrap_replicates",
            "interval_semantics": "bootstrap_sampling_uncertainty_of_conditional_mean_not_predictive_noise",
            "calibrated": False,
        }


if "bootstrap" not in UNCERTAINTY_METHODS.names():
    UNCERTAINTY_METHODS.register("bootstrap", BootstrapUncertainty)


__all__ = ["BootstrapUncertainty"]
