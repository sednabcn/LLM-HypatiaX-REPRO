"""Shared interfaces and reporting infrastructure for future uncertainty methods."""
from .base import CalibrationMethod, UncertaintyEstimate, UncertaintyMethod
from .evaluation import evaluate_estimate
from .registry import CALIBRATION_METHODS, UNCERTAINTY_METHODS, MethodRegistry
from .results import RESULT_SCHEMA_VERSION, UncertaintyResult, write_uncertainty_results_json

__all__ = [
    "UncertaintyMethod", "CalibrationMethod", "UncertaintyEstimate",
    "MethodRegistry", "UNCERTAINTY_METHODS", "CALIBRATION_METHODS",
    "evaluate_estimate", "UncertaintyResult", "write_uncertainty_results_json",
    "RESULT_SCHEMA_VERSION",
]
