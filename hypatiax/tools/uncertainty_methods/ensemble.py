"""Ensemble disagreement estimator for already-fitted prediction members.

This adapter never trains or refits its members. Its intervals summarize
between-member spread and are not calibrated prediction intervals.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from .base import UncertaintyEstimate, UncertaintyMethod
from .registry import UNCERTAINTY_METHODS


class EnsembleUncertainty(UncertaintyMethod):
    """Summarize predictions from two or more caller-supplied fitted members.

    Members must expose predict(X) or be callable. fit() validates and records
    the training-data shape only; it deliberately never calls member.fit().
    """

    name = "ensemble_disagreement"
    version = "1.0"
    capabilities = frozenset({
        "point_mean", "member_disagreement", "predictive_samples",
        "empirical_member_spread",
    })

    def __init__(self, members: Sequence[Any], member_names: Sequence[str] | None = None):
        if isinstance(members, (str, bytes)) or not isinstance(members, Sequence):
            raise TypeError("members must be a sequence of fitted predictors.")
        if len(members) < 2:
            raise ValueError("At least two fitted members are required.")
        if any(not (callable(member) or callable(getattr(member, "predict", None))) for member in members):
            raise TypeError("Each member must be callable or expose predict(X).")
        if member_names is not None and len(member_names) != len(members):
            raise ValueError("member_names must have one name per member.")
        self.members = tuple(members)
        self.member_names = tuple(member_names) if member_names is not None else tuple(
            f"member_{index}" for index in range(len(members))
        )
        self._fitted = False
        self._n_features: int | None = None
        self._n_train: int | None = None

    def fit(self, X_train: Any, y_train: Any, **kwargs: Any) -> "EnsembleUncertainty":
        """Validate training provenance without fitting supplied predictors."""
        X = np.asarray(X_train)
        y = np.asarray(y_train, dtype=float).reshape(-1)
        if X.ndim != 2 or X.shape[0] < 1:
            raise ValueError("X_train must be a non-empty 2D array.")
        if y.size != X.shape[0] or not np.isfinite(y).all():
            raise ValueError("y_train must be finite and aligned with X_train.")
        self._n_features = int(X.shape[1])
        self._n_train = int(X.shape[0])
        self._fitted = True
        return self

    def _member_predictions(self, X: Any) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("Call fit() to validate training data before estimate().")
        inputs = np.asarray(X)
        if inputs.ndim != 2 or inputs.shape[1] != self._n_features:
            raise ValueError(f"X must be 2D with {self._n_features} features.")
        predictions = []
        for name, member in zip(self.member_names, self.members):
            predictor = getattr(member, "predict", None)
            raw = predictor(inputs) if callable(predictor) else member(inputs)
            values = np.asarray(raw, dtype=float).reshape(-1)
            if values.size != inputs.shape[0] or not np.isfinite(values).all():
                raise ValueError(f"{name} returned non-finite or misaligned predictions.")
            predictions.append(values)
        return np.stack(predictions, axis=1)

    def estimate(
        self, X: Any, nominal_coverage: float = 0.95, **kwargs: Any
    ) -> UncertaintyEstimate:
        """Return ensemble mean, sample spread, member draws, and spread bounds."""
        coverage = float(nominal_coverage)
        if not 0.0 < coverage < 1.0:
            raise ValueError("nominal_coverage must be strictly between 0 and 1.")
        predictions = self._member_predictions(X)
        alpha = (1.0 - coverage) / 2.0
        lower, upper = np.quantile(predictions, [alpha, 1.0 - alpha], axis=1)
        return UncertaintyEstimate(
            mean=np.mean(predictions, axis=1),
            scale=np.std(predictions, axis=1, ddof=1),
            lower=lower,
            upper=upper,
            samples=predictions,
            components={"member_predictions": predictions},
            diagnostics={
                "member_count": len(self.members),
                "spread_semantics": "empirical_between_member_spread",
                "interval_calibrated": False,
            },
            metadata={
                "interval_kind": "empirical_member_spread",
                "nominal_coverage": coverage,
                "not_a_calibrated_prediction_interval": True,
            },
        )

    def diagnostics(self, X: Any) -> dict[str, Any]:
        return {
            "member_count": len(self.members),
            "fitted": self._fitted,
            "training_sample_count": self._n_train,
            "training_feature_count": self._n_features,
        }

    def metadata(self) -> dict[str, Any]:
        return {
            "method": self.name,
            "version": self.version,
            "capabilities": sorted(self.capabilities),
            "member_names": list(self.member_names),
            "member_training": "caller_supplied_pre_fitted",
            "fit_behavior": "validates_data_only_never_trains_members",
            "uncertainty_semantics": "between_member_disagreement",
            "interval_semantics": "empirical_member_spread_not_calibrated",
        }


if "ensemble" not in UNCERTAINTY_METHODS.names():
    UNCERTAINTY_METHODS.register("ensemble", EnsembleUncertainty)


__all__ = ["EnsembleUncertainty"]
