"""Offline contract checks for uncertainty estimators and calibrators."""
import numpy as np
import pytest

from hypatiax.tools.uncertainty_methods import (
    CalibrationMethod,
    UncertaintyEstimate,
    UncertaintyMethod,
    validate_calibration_method_contract,
    validate_uncertainty_method_contract,
)


class DemoEstimator(UncertaintyMethod):
    name = "demo"
    version = "1.0"
    capabilities = frozenset({"mean", "prediction_interval"})

    def fit(self, X_train, y_train, **kwargs):
        return self

    def estimate(self, X, nominal_coverage=0.95, **kwargs):
        return UncertaintyEstimate(
            mean=np.zeros(len(X)),
            lower=np.full(len(X), -1.0),
            upper=np.full(len(X), 1.0),
        )

    def diagnostics(self, X):
        return {"n_features": int(np.asarray(X).shape[1])}


class DemoCalibrator(CalibrationMethod):
    name = "demo_calibrator"

    def fit(self, y_calibration, estimate, **kwargs):
        return self

    def apply(self, estimate, coverage):
        return UncertaintyEstimate(
            mean=estimate.mean,
            lower=np.asarray(estimate.mean) - 1,
            upper=np.asarray(estimate.mean) + 1,
        )

    def metadata(self):
        return {"guarantee_scope": "unit-test-only"}


def test_estimator_contract_accepts_aligned_estimates():
    method = DemoEstimator()
    X = np.ones((4, 2))
    estimates = {0.9: method.estimate(X, 0.9), 0.95: method.estimate(X, 0.95)}
    result = validate_uncertainty_method_contract(method, X, estimates)
    assert result["status"] == "ok"
    assert result["method"] == "demo"
    assert result["nominal_coverages"] == [0.9, 0.95]
    assert result["diagnostics"]["n_features"] == 2


def test_estimator_contract_rejects_wrong_method_type():
    with pytest.raises(TypeError, match="UncertaintyMethod"):
        validate_uncertainty_method_contract(object(), np.ones((2, 1)), {0.9: UncertaintyEstimate(mean=[1, 2])})


def test_estimator_contract_rejects_bad_coverage_and_shape():
    method = DemoEstimator()
    with pytest.raises(ValueError, match="Invalid nominal coverage"):
        validate_uncertainty_method_contract(method, np.ones((2, 1)), {1.0: UncertaintyEstimate(mean=[1, 2])})
    with pytest.raises(ValueError, match="mean must contain"):
        validate_uncertainty_method_contract(method, np.ones((2, 1)), {0.9: UncertaintyEstimate(mean=[1])})


def test_estimator_contract_rejects_non_mapping_diagnostics():
    class BadDiagnostics(DemoEstimator):
        def diagnostics(self, X):
            return []
    with pytest.raises(TypeError, match="diagnostics"):
        validate_uncertainty_method_contract(
            BadDiagnostics(), np.ones((2, 1)), {0.9: UncertaintyEstimate(mean=[1, 2])}
        )


def test_calibration_contract_accepts_interval_outputs():
    method = DemoCalibrator()
    result = validate_calibration_method_contract(
        method,
        {0.9: UncertaintyEstimate(mean=[1, 2], lower=[0, 1], upper=[2, 3])},
        n_samples=2,
    )
    assert result["status"] == "ok"
    assert result["nominal_coverages"] == [0.9]


def test_calibration_contract_rejects_missing_bounds_and_bad_type():
    method = DemoCalibrator()
    with pytest.raises(ValueError, match="interval bounds"):
        validate_calibration_method_contract(
            method, {0.9: UncertaintyEstimate(mean=[1, 2])}, n_samples=2
        )
    with pytest.raises(TypeError, match="CalibrationMethod"):
        validate_calibration_method_contract(
            object(), {0.9: UncertaintyEstimate(lower=[0], upper=[1])}, n_samples=1
        )


def test_contract_validation_does_not_call_fit_or_estimate():
    class GuardedEstimator(DemoEstimator):
        def fit(self, *args, **kwargs):
            raise AssertionError("fit must not be called")
        def estimate(self, *args, **kwargs):
            raise AssertionError("estimate must not be called")
    validate_uncertainty_method_contract(
        GuardedEstimator(),
        np.ones((2, 1)),
        {0.9: UncertaintyEstimate(mean=[0, 0])},
    )
