"""Study template: distribution-shift-aware calibration (not implemented)."""
from __future__ import annotations
from typing import Any
from ..base import CalibrationMethod, UncertaintyEstimate


class ShiftAwareCalibrationTemplate(CalibrationMethod):
    name = "shift_aware_calibration_template"

    def __init__(self, shift_type: str, weighting_strategy: str | None = None,
                 min_effective_sample_size: float | None = None):
        self.shift_type = shift_type
        self.weighting_strategy = weighting_strategy
        self.min_effective_sample_size = min_effective_sample_size

    def fit(self, y_calibration: Any, estimate: UncertaintyEstimate, **kwargs):
        # TODO: require disjoint calibration data and specify the shift
        # assumption; estimate weights/support diagnostics from allowed X data.
        # Refuse unsupported regions rather than silently extrapolating weights.
        raise NotImplementedError("Implement calibration for a stated shift model.")

    def apply(self, estimate: UncertaintyEstimate, coverage: float) -> UncertaintyEstimate:
        # TODO: apply the calibrated score/weight procedure; preserve source
        # estimate and attach guarantee scope, ESS, overlap and failure status.
        raise NotImplementedError("Apply shift-aware interval calibration.")

    def metadata(self):
        return {"method": self.name, "shift_type": self.shift_type,
                "weighting_strategy": self.weighting_strategy,
                "min_effective_sample_size": self.min_effective_sample_size,
                "guarantee_scope": "must_be_derived_from_assumptions"}
