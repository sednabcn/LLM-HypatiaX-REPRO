"""Study template: ensemble disagreement (not implemented)."""
from __future__ import annotations
from typing import Sequence
from ..base import UncertaintyEstimate, UncertaintyMethod


class EnsembleTemplate(UncertaintyMethod):
    name = "ensemble_template"
    version = "0.0"
    capabilities = frozenset({"member_predictions", "mean", "scale", "quantiles"})

    def __init__(self, members: Sequence):
        self.members = tuple(members)

    def fit(self, X_train, y_train, **kwargs):
        # TODO: validate supplied fitted members and record provenance.
        # Do not silently fit/retrain members in this adapter.
        raise NotImplementedError("Attach and validate already-fitted ensemble members.")

    def estimate(self, X, nominal_coverage=0.95, **kwargs) -> UncertaintyEstimate:
        # TODO: collect finite member predictions; record failures and member
        # count; derive disagreement summaries. Do not label spread a PI.
        raise NotImplementedError("Aggregate member predictions.")

    def metadata(self):
        return {**super().metadata(), "member_count": len(self.members),
                "spread_semantics": "between_member_disagreement"}
