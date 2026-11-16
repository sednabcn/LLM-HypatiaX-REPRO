import numpy as np
import pytest

from hypatiax.tools.uncertainty_methods import (
    BootstrapUncertainty,
    UNCERTAINTY_METHODS,
    validate_uncertainty_method_contract,
)


class MeanRegressor:
    def __init__(self):
        self.fit_calls = 0

    def fit(self, X, y):
        self.fit_calls += 1
        self.mean_ = float(np.mean(y))
        self.coef_ = np.linalg.lstsq(
            np.column_stack([np.ones(len(X)), np.asarray(X)[:, 0]]),
            np.asarray(y), rcond=None,
        )[0]
        return self

    def predict(self, X):
        X = np.asarray(X)
        return self.coef_[0] + self.coef_[1] * X[:, 0]


def factory():
    return MeanRegressor()


@pytest.mark.parametrize("resampling", ["pairs", "residual", "block"])
def test_bootstrap_methods_fit_explicitly_and_return_contract(resampling):
    X = np.arange(30, dtype=float).reshape(-1, 1)
    y = 2.0 * X[:, 0] + np.sin(X[:, 0])
    method = BootstrapUncertainty(
        factory, n_bootstrap=8, resampling=resampling,
        random_state=17, block_size=4 if resampling == "block" else None,
    )
    assert method.models_ == []
    method.fit(X, y)
    assert len(method.models_) == 8
    estimate = method.estimate(X[:5], nominal_coverage=0.9)
    estimate.validate(5)
    assert estimate.mean.shape == (5,)
    assert estimate.samples.shape == (5, 8)
    assert estimate.lower.shape == estimate.upper.shape == (5,)
    assert estimate.metadata["not_a_calibrated_prediction_interval"] is True
    assert validate_uncertainty_method_contract(method, X[:5], estimate) is not None


def test_seed_reproduces_bootstrap_predictions():
    X = np.arange(20, dtype=float).reshape(-1, 1)
    y = X[:, 0] ** 2
    left = BootstrapUncertainty(factory, n_bootstrap=6, random_state=4).fit(X, y)
    right = BootstrapUncertainty(factory, n_bootstrap=6, random_state=4).fit(X, y)
    np.testing.assert_allclose(left.estimate(X).samples, right.estimate(X).samples)
    for a, b in zip(left.resample_indices_, right.resample_indices_):
        np.testing.assert_array_equal(a, b)


def test_factory_is_not_called_until_fit_and_estimate_does_not_refit():
    calls = []
    def counted_factory():
        calls.append("created")
        return MeanRegressor()
    method = BootstrapUncertainty(counted_factory, n_bootstrap=3, random_state=1)
    assert calls == []
    X = np.arange(8, dtype=float).reshape(-1, 1)
    method.fit(X, X[:, 0])
    count_after_fit = len(calls)
    method.estimate(X)
    assert len(calls) == count_after_fit
    assert count_after_fit == 3


def test_invalid_block_size_and_unfitted_estimate():
    with pytest.raises(ValueError):
        BootstrapUncertainty(factory, resampling="block")
    method = BootstrapUncertainty(factory, n_bootstrap=3)
    with pytest.raises(RuntimeError):
        method.estimate(np.ones((2, 1)))
    with pytest.raises(ValueError):
        BootstrapUncertainty(factory, n_bootstrap=3, resampling="block", block_size=9).fit(
            np.ones((4, 1)), np.ones(4)
        )


def test_registry_exposes_bootstrap_factory():
    assert UNCERTAINTY_METHODS.create(
        "bootstrap", estimator_factory=factory, n_bootstrap=3
    ).resampling == "pairs"
