import numpy as np
import pytest

from hypatiax.tools.uncertainty_methods import (
    QuantileRegressionUncertainty,
    UNCERTAINTY_METHODS,
    validate_uncertainty_method_contract,
)


class QuantileLine:
    def __init__(self, level, crossing=False):
        self.level = level
        self.crossing = crossing
        self.fit_calls = 0

    def fit(self, X, y):
        self.fit_calls += 1
        self.offset_ = float(self.level)
        return self

    def predict(self, X):
        x = np.asarray(X)[:, 0]
        if self.crossing and self.level < 0.5:
            return x + 2.0
        return x + self.offset_


def factories(levels=(0.05, 0.5, 0.95), crossing=False):
    return {
        level: (lambda q=level: QuantileLine(q, crossing=crossing))
        for level in levels
    }


def test_quantile_predictions_and_central_interval_follow_contract():
    X_train = np.arange(10, dtype=float).reshape(-1, 1)
    y_train = X_train[:, 0] * 2
    method = QuantileRegressionUncertainty(factories())
    assert method.models_ == {}
    method.fit(X_train, y_train)
    X = np.array([[1.0], [3.0], [5.0]])
    estimate = method.estimate(X, nominal_coverage=0.9)
    np.testing.assert_allclose(estimate.mean, [1.5, 3.5, 5.5])
    np.testing.assert_allclose(estimate.lower, [1.05, 3.05, 5.05])
    np.testing.assert_allclose(estimate.upper, [1.95, 3.95, 5.95])
    assert set(estimate.quantiles) == {0.05, 0.5, 0.95}
    assert estimate.diagnostics["central_interval_available"] is True
    assert estimate.diagnostics["required_interval_levels"] == pytest.approx([0.05, 0.95])
    report = validate_uncertainty_method_contract(method, X, {0.9: estimate})
    assert report["status"] == "ok"


def test_quantile_crossing_is_reported_not_silently_fixed():
    method = QuantileRegressionUncertainty(factories(crossing=True)).fit(
        np.arange(8, dtype=float).reshape(-1, 1), np.arange(8, dtype=float)
    )
    estimate = method.estimate(np.array([[1.0], [2.0]]), nominal_coverage=0.9)
    assert estimate.diagnostics["crossing_count"] == 2
    assert estimate.diagnostics["crossing_rate"] == 1.0
    assert estimate.metadata["quantile_crossing_policy"] == "reported_not_rearranged"


def test_missing_exact_interval_levels_does_not_invent_bounds():
    method = QuantileRegressionUncertainty(factories(levels=(0.1, 0.5, 0.9))).fit(
        np.arange(8, dtype=float).reshape(-1, 1), np.arange(8, dtype=float)
    )
    estimate = method.estimate(np.array([[1.0]]), nominal_coverage=0.95)
    assert estimate.lower is None and estimate.upper is None
    assert estimate.diagnostics["central_interval_available"] is False


def test_factories_are_not_called_until_fit_and_estimate_does_not_refit():
    created = []
    def make(level):
        def factory():
            created.append(level)
            return QuantileLine(level)
        return factory
    method = QuantileRegressionUncertainty({0.1: make(0.1), 0.5: make(0.5), 0.9: make(0.9)})
    assert created == []
    X = np.arange(6, dtype=float).reshape(-1, 1)
    method.fit(X, X[:, 0])
    assert len(created) == 3
    method.estimate(X)
    assert len(created) == 3


def test_invalid_levels_and_bad_predictions_are_rejected():
    with pytest.raises(ValueError):
        QuantileRegressionUncertainty({0.0: lambda: QuantileLine(0.0), 0.5: lambda: QuantileLine(0.5)})
    method = QuantileRegressionUncertainty({
        0.1: lambda: QuantileLine(0.1),
        0.9: lambda: QuantileLine(0.9),
    }).fit(np.ones((4, 1)), np.ones(4))
    method.models_[0.9].predict = lambda X: np.full(len(X), np.nan)
    with pytest.raises(ValueError, match="non-finite or misaligned"):
        method.estimate(np.ones((2, 1)))


def test_quantile_regression_is_registered():
    method = UNCERTAINTY_METHODS.create("quantile_regression", estimator_factories=factories())
    assert isinstance(method, QuantileRegressionUncertainty)
