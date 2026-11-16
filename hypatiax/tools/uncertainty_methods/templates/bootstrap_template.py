"""Study template: bootstrap prediction variability (not implemented)."""
from __future__ import annotations
from typing import Any, Callable
from ..base import UncertaintyEstimate, UncertaintyMethod


class BootstrapTemplate(UncertaintyMethod):
    name = "bootstrap_template"
    version = "0.0"
    capabilities = frozenset({"replicate_predictions", "quantiles"})

    def __init__(self, estimator_factory: Callable, resampling: str,
                 n_replicates: int = 500, random_state: int | None = None,
                 block_size: int | None = None):
        self.estimator_factory = estimator_factory
        self.resampling = resampling
        self.n_replicates = int(n_replicates)
        self.random_state = random_state
        self.block_size = block_size

    def fit(self, X_train, y_train, **kwargs):
        # TODO: implement pairs/residual/wild/block/parametric resampling;
        # match the resampling unit to data dependence and retain failed fits.
        raise NotImplementedError("Generate bootstrap replicate estimators.")

    def estimate(self, X, nominal_coverage=0.95, **kwargs) -> UncertaintyEstimate:
        # TODO: collect replicate predictions and label whether they represent
        # fitted-function variability or include future observation noise.
        raise NotImplementedError("Predict with each bootstrap replicate.")

    def metadata(self):
        return {**super().metadata(), "resampling": self.resampling,
                "n_replicates": self.n_replicates,
                "random_state": self.random_state, "block_size": self.block_size}
