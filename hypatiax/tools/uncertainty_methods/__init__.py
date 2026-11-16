"""Shared interfaces and reporting infrastructure for uncertainty methods."""
from .base import CalibrationMethod, UncertaintyEstimate, UncertaintyMethod
from .evaluation import evaluate_estimate
from .registry import CALIBRATION_METHODS, UNCERTAINTY_METHODS, MethodRegistry
from .results import RESULT_SCHEMA_VERSION, UncertaintyResult, write_uncertainty_results_json
from .protocol import ComparisonProtocol, validate_split_indices
from .contracts import validate_calibration_method_contract, validate_uncertainty_method_contract
from .ensemble import EnsembleUncertainty

__all__ = [
    "UncertaintyMethod", "CalibrationMethod", "UncertaintyEstimate",
    "MethodRegistry", "UNCERTAINTY_METHODS", "CALIBRATION_METHODS",
    "evaluate_estimate", "UncertaintyResult", "write_uncertainty_results_json",
    "RESULT_SCHEMA_VERSION",
    "ComparisonProtocol", "validate_split_indices",
    "validate_uncertainty_method_contract", "validate_calibration_method_contract",
    "EnsembleUncertainty",
]
