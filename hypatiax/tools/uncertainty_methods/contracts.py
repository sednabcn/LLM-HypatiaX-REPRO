"""Reusable, side-effect-free validation for uncertainty method outputs."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from .base import CalibrationMethod, UncertaintyEstimate, UncertaintyMethod


def validate_uncertainty_method_contract(
    method: UncertaintyMethod,
    X: Any,
    estimates: Mapping[float, UncertaintyEstimate],
) -> dict[str, Any]:
    """Validate already-computed estimates against the shared method contract.

    This function deliberately does not call fit() or estimate(): callers
    control when inference occurs and can pass outputs from offline fixtures,
    cached predictions, or an explicitly authorized run.
    """
    if not isinstance(method, UncertaintyMethod):
        raise TypeError("method must implement UncertaintyMethod.")
    if not isinstance(estimates, Mapping) or not estimates:
        raise ValueError("estimates must be a non-empty coverage-to-estimate mapping.")
    n_samples = _sample_count(X)
    metadata = method.metadata()
    diagnostics = method.diagnostics(X)
    if not isinstance(metadata, Mapping):
        raise TypeError("method.metadata() must return a mapping.")
    if not isinstance(diagnostics, Mapping):
        raise TypeError("method.diagnostics() must return a mapping.")
    if not str(getattr(method, "name", "")).strip():
        raise ValueError("method.name must be non-empty.")
    if not str(getattr(method, "version", "")).strip():
        raise ValueError("method.version must be non-empty.")
    capabilities = getattr(method, "capabilities", None)
    if not isinstance(capabilities, (set, frozenset, tuple, list)):
        raise TypeError("method.capabilities must be a collection of strings.")
    if any(not isinstance(item, str) or not item.strip() for item in capabilities):
        raise ValueError("method.capabilities must contain non-empty strings.")

    checked = {}
    for coverage, estimate in estimates.items():
        level = float(coverage)
        if not 0.0 < level < 1.0:
            raise ValueError(f"Invalid nominal coverage: {level}.")
        if not isinstance(estimate, UncertaintyEstimate):
            raise TypeError(f"Estimate at coverage {level} must be UncertaintyEstimate.")
        estimate.validate(n_samples)
        checked[level] = estimate
    return {
        "status": "ok",
        "method": str(method.name),
        "version": str(method.version),
        "n_samples": n_samples,
        "nominal_coverages": sorted(checked),
        "capabilities": sorted(capabilities),
        "metadata": dict(metadata),
        "diagnostics": dict(diagnostics),
    }


def validate_calibration_method_contract(
    method: CalibrationMethod,
    calibrated_estimates: Mapping[float, UncertaintyEstimate],
    n_samples: int,
) -> dict[str, Any]:
    """Validate already-computed calibration outputs without fitting/applying.

    The caller must separately enforce data-role separation and verify that
    apply() did not mutate its input. This helper validates type, coverage
    keys, output alignment, metadata, and interval structure only.
    """
    if not isinstance(method, CalibrationMethod):
        raise TypeError("method must implement CalibrationMethod.")
    if n_samples < 1:
        raise ValueError("n_samples must be positive.")
    if not isinstance(calibrated_estimates, Mapping) or not calibrated_estimates:
        raise ValueError("calibrated_estimates must be a non-empty mapping.")
    metadata = method.metadata()
    if not isinstance(metadata, Mapping):
        raise TypeError("calibration method metadata() must return a mapping.")
    checked = {}
    for coverage, estimate in calibrated_estimates.items():
        level = float(coverage)
        if not 0.0 < level < 1.0:
            raise ValueError(f"Invalid nominal coverage: {level}.")
        if not isinstance(estimate, UncertaintyEstimate):
            raise TypeError(f"Calibrated output at coverage {level} must be UncertaintyEstimate.")
        estimate.validate(n_samples)
        if estimate.lower is None or estimate.upper is None:
            raise ValueError(f"Calibrated output at coverage {level} must contain interval bounds.")
        checked[level] = estimate
    return {
        "status": "ok",
        "method": str(method.name),
        "n_samples": int(n_samples),
        "nominal_coverages": sorted(checked),
        "metadata": dict(metadata),
    }


def _sample_count(X: Any) -> int:
    try:
        count = len(X)
    except TypeError as exc:
        raise TypeError("X must be a sized evaluation input.") from exc
    if count < 1:
        raise ValueError("X must contain at least one evaluation sample.")
    return int(count)


__all__ = [
    "validate_uncertainty_method_contract",
    "validate_calibration_method_contract",
]
