"""Shared comparison protocol and leakage checks for uncertainty methods."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np


DEFAULT_SPLIT_ROLES = ("train", "validation", "calibration", "test")
DEFAULT_POINT_METRICS = ("mae", "rmse", "bias", "r2")
DEFAULT_INTERVAL_METRICS = (
    "empirical_coverage", "mean_interval_width", "interval_score",
    "absolute_coverage_gap",
)


@dataclass(frozen=True)
class ComparisonProtocol:
    """Declarative, method-independent settings for a fair comparison.

    This object describes a protocol; it does not split data, fit models,
    calibrate intervals, or launch evaluations.
    """

    split_roles: tuple[str, ...] = DEFAULT_SPLIT_ROLES
    evaluation_domains: tuple[str, ...] = ("in_domain", "boundary", "extra_domain")
    nominal_coverages: tuple[float, ...] = (0.80, 0.90, 0.95)
    point_metrics: tuple[str, ...] = DEFAULT_POINT_METRICS
    interval_metrics: tuple[str, ...] = DEFAULT_INTERVAL_METRICS
    seeds: tuple[int, ...] = (17, 29, 43, 71, 101)
    split_strategy: str = "random"
    primary_selection_metric: str = "validation_rmse"
    notes: Mapping[str, str] = field(default_factory=dict)

    def validate(self) -> "ComparisonProtocol":
        if len(set(self.split_roles)) != len(self.split_roles) or not self.split_roles:
            raise ValueError("split_roles must be non-empty and unique.")
        if "train" not in self.split_roles or "test" not in self.split_roles:
            raise ValueError("split_roles must include train and test.")
        if not self.evaluation_domains or len(set(self.evaluation_domains)) != len(self.evaluation_domains):
            raise ValueError("evaluation_domains must be non-empty and unique.")
        if not self.nominal_coverages or any(not 0 < x < 1 for x in self.nominal_coverages):
            raise ValueError("nominal_coverages must be strictly between 0 and 1.")
        if len(set(self.nominal_coverages)) != len(self.nominal_coverages):
            raise ValueError("nominal_coverages must be unique.")
        if not self.seeds or len(set(self.seeds)) != len(self.seeds):
            raise ValueError("seeds must be non-empty and unique.")
        if not self.split_strategy.strip() or not self.primary_selection_metric.strip():
            raise ValueError("split_strategy and primary_selection_metric are required.")
        return self


def validate_split_indices(
    split_indices: Mapping[str, Sequence[int]],
    n_samples: int,
    required_roles: Sequence[str] = ("train", "test"),
) -> dict[str, np.ndarray]:
    """Validate explicit row-index splits and return normalized integer arrays.

    Every supplied role must be non-empty, unique, in bounds, and disjoint
    from every other role. Use group/time-aware splitters upstream when rows
    are dependent; this helper checks row overlap, not group leakage.
    """
    if n_samples < 1:
        raise ValueError("n_samples must be positive.")
    missing = [role for role in required_roles if role not in split_indices]
    if missing:
        raise ValueError(f"Missing required split roles: {missing}.")
    normalized: dict[str, np.ndarray] = {}
    owner: dict[int, str] = {}
    for role, indices in split_indices.items():
        raw = np.asarray(indices)
        if raw.ndim != 1 or raw.size == 0:
            raise ValueError(f"Split '{role}' must be a non-empty 1D index sequence.")
        if not np.issubdtype(raw.dtype, np.integer):
            if not np.issubdtype(raw.dtype, np.number) or not np.isfinite(raw).all() or not np.equal(raw, np.floor(raw)).all():
                raise ValueError(f"Split '{role}' indices must be integers.")
        values = raw.astype(int)
        if np.any(values < 0) or np.any(values >= n_samples):
            raise ValueError(f"Split '{role}' contains indices outside [0, {n_samples}).")
        if np.unique(values).size != values.size:
            raise ValueError(f"Split '{role}' contains duplicate indices.")
        for index in values.tolist():
            if index in owner:
                raise ValueError(f"Data leakage: index {index} appears in '{owner[index]}' and '{role}'.")
            owner[index] = role
        normalized[str(role)] = values
    return normalized


__all__ = [
    "ComparisonProtocol", "validate_split_indices",
    "DEFAULT_SPLIT_ROLES", "DEFAULT_POINT_METRICS", "DEFAULT_INTERVAL_METRICS",
]
