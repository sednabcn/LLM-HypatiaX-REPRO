"""Study template: conditional quantile regression (not implemented)."""
from __future__ import annotations
from typing import Sequence
from ..base import UncertaintyEstimate, UncertaintyMethod


class QuantileRegressionTemplate(UncertaintyMethod):
    name = "quantile_regression_template"
    version = "0.0"
    capabilities = frozenset({"quantiles"})

    def __init__(self, estimator_factory, quantile_levels: Sequence[float]):
        levels = tuple(sorted(float(level) for level in quantile_levels))
        if not levels or any(not 0.0 < level < 1.0 for level in levels):
            raise ValueError("quantile_levels must be non-empty and within (0, 1).")
        self.estimator_factory = estimator_factory
        self.quantile_levels = levels

    def fit(self, X_train, y_train, **kwargs):
        # TODO: fit one or more conditional quantile models; retain objective,
        # optimizer, regularization and convergence metadata.
        raise NotImplementedError("Fit conditional quantile estimators.")

    def estimate(self, X, nominal_coverage=0.95, **kwargs) -> UncertaintyEstimate:
        # TODO: predict every configured quantile; diagnose crossing and
        # document any monotonicity correction.
        raise NotImplementedError("Predict configured conditional quantiles.")

    def metadata(self):
        return {**super().metadata(), "quantile_levels": list(self.quantile_levels),
                "crossing_policy": "must_be_declared"}
