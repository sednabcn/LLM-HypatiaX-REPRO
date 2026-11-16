"""Study template: Bayesian regression uncertainty (not implemented)."""
from __future__ import annotations
from typing import Any
from ..base import UncertaintyEstimate, UncertaintyMethod


class BayesianTemplate(UncertaintyMethod):
    name = "bayesian_template"
    version = "0.0"
    capabilities = frozenset({"posterior_samples", "predictive_mean", "intervals"})

    def __init__(self, prior_spec: Any, likelihood_spec: Any, inference_backend: str):
        self.prior_spec = prior_spec
        self.likelihood_spec = likelihood_spec
        self.inference_backend = inference_backend

    def fit(self, X_train, y_train, **kwargs):
        # TODO: validate data, define likelihood/prior, run inference, retain
        # convergence diagnostics and training provenance.
        raise NotImplementedError("Choose and implement a Bayesian inference backend.")

    def estimate(self, X, nominal_coverage=0.95, **kwargs) -> UncertaintyEstimate:
        # TODO: distinguish latent-function posterior from observation-
        # predictive draws (include observation noise only in the latter).
        raise NotImplementedError("Generate posterior or posterior-predictive draws.")

    def metadata(self):
        return {**super().metadata(), "prior": str(self.prior_spec),
                "likelihood": str(self.likelihood_spec),
                "inference_backend": self.inference_backend,
                "interval_semantics": "must_be_declared"}
