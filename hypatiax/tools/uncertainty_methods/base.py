"""Shared contracts for model-agnostic uncertainty estimators."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping
import numpy as np


@dataclass
class UncertaintyEstimate:
    """Aligned optional predictions; unsupported quantities remain None."""
    mean: np.ndarray | None = None
    scale: np.ndarray | None = None
    lower: np.ndarray | None = None
    upper: np.ndarray | None = None
    quantiles: Mapping[float, np.ndarray] = field(default_factory=dict)
    samples: np.ndarray | None = None
    components: Mapping[str, Any] = field(default_factory=dict)
    diagnostics: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self, n_samples: int) -> "UncertaintyEstimate":
        if n_samples < 1:
            raise ValueError("n_samples must be positive.")
        for name in ("mean", "scale", "lower", "upper"):
            value = getattr(self, name)
            if value is None:
                continue
            array = np.asarray(value, dtype=float).reshape(-1)
            if array.size != n_samples:
                raise ValueError(f"{name} must contain {n_samples} values.")
            if np.isnan(array).any() or (name not in {"lower", "upper"} and not np.isfinite(array).all()):
                raise ValueError(f"{name} contains invalid values.")
            setattr(self, name, array)
        if self.scale is not None and np.any(self.scale < 0):
            raise ValueError("scale must be non-negative.")
        if (self.lower is None) != (self.upper is None):
            raise ValueError("lower and upper must be supplied together.")
        if self.lower is not None and np.any(self.lower > self.upper):
            raise ValueError("interval bounds must satisfy lower <= upper.")
        checked = {}
        for level, values in self.quantiles.items():
            level = float(level)
            array = np.asarray(values, dtype=float).reshape(-1)
            if not 0.0 < level < 1.0 or array.size != n_samples or not np.isfinite(array).all():
                raise ValueError(f"Invalid quantile output at level {level}.")
            checked[level] = array
        self.quantiles = checked
        if self.samples is not None:
            samples = np.asarray(self.samples, dtype=float)
            if samples.ndim != 2 or samples.shape[0] != n_samples or not np.isfinite(samples).all():
                raise ValueError("samples must be finite with shape (n_samples, n_draws).")
            self.samples = samples
        return self


class UncertaintyMethod(ABC):
    """Estimator contract; fit on training data, estimate on untouched inputs."""
    name = "abstract"
    version = "0"
    capabilities: frozenset[str] = frozenset()

    @abstractmethod
    def fit(self, X_train: Any, y_train: Any, **kwargs: Any) -> "UncertaintyMethod":
        """Fit or attach a method using training data only."""

    @abstractmethod
    def estimate(self, X: Any, nominal_coverage: float = 0.95, **kwargs: Any) -> UncertaintyEstimate:
        """Return one aligned estimate per input row."""

    def diagnostics(self, X: Any) -> Mapping[str, Any]:
        return {}

    def metadata(self) -> Mapping[str, Any]:
        return {"method": self.name, "version": self.version, "capabilities": sorted(self.capabilities)}


class CalibrationMethod(ABC):
    """Separate calibration stage; implementations must not refit predictors."""
    name = "abstract_calibration"

    @abstractmethod
    def fit(self, y_calibration: Any, estimate: UncertaintyEstimate, **kwargs: Any):
        """Calibrate from a disjoint calibration split."""

    @abstractmethod
    def apply(self, estimate: UncertaintyEstimate, coverage: float) -> UncertaintyEstimate:
        """Apply calibration without mutating the source estimate."""

    @abstractmethod
    def metadata(self) -> Mapping[str, Any]:
        """Describe calibration data, assumptions, and guarantee scope."""
