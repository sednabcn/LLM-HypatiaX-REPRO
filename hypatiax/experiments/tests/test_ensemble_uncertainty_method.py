import numpy as np
import pytest

from hypatiax.tools.uncertainty_methods import (
    EnsembleUncertainty,
    UNCERTAINTY_METHODS,
    validate_uncertainty_method_contract,
)


class FixedMember:
    def __init__(self, offset):
        self.offset = offset
        self.fit_calls = 0

    def fit(self, X, y):
        self.fit_calls += 1
        return self

    def predict(self, X):
        return np.asarray(X)[:, 0] + self.offset


def test_ensemble_uses_pre_fitted_members_without_training_them():
    members = [FixedMember(-1), FixedMember(1), FixedMember(3)]
    method = EnsembleUncertainty(members)
    X_train = np.arange(12, dtype=float).reshape(6, 2)
    method.fit(X_train, X_train[:, 0])
    X = np.array([[2.0, 0.0], [4.0, 1.0]])
    estimate = method.estimate(X, nominal_coverage=0.8)

    np.testing.assert_allclose(estimate.mean, [3.0, 5.0])
    np.testing.assert_allclose(estimate.scale, [2.0, 2.0])
    assert estimate.samples.shape == (2, 3)
    assert estimate.lower.shape == estimate.upper.shape == (2,)
    assert all(member.fit_calls == 0 for member in members)
    assert estimate.metadata["not_a_calibrated_prediction_interval"] is True


def test_ensemble_outputs_pass_shared_contract():
    method = EnsembleUncertainty([lambda X: X[:, 0], lambda X: X[:, 0] + 1])
    X_train = np.ones((4, 2))
    method.fit(X_train, np.ones(4))
    X = np.ones((3, 2))
    estimate = method.estimate(X)
    report = validate_uncertainty_method_contract(method, X, {0.95: estimate})
    assert report["status"] == "ok"
    assert report["method"] == "ensemble_disagreement"


def test_ensemble_requires_two_members_and_valid_coverage():
    with pytest.raises(ValueError, match="At least two"):
        EnsembleUncertainty([lambda X: X[:, 0]])
    method = EnsembleUncertainty([lambda X: X[:, 0], lambda X: X[:, 0]])
    method.fit(np.ones((2, 1)), np.ones(2))
    with pytest.raises(ValueError, match="nominal_coverage"):
        method.estimate(np.ones((1, 1)), nominal_coverage=1.0)


def test_ensemble_rejects_bad_member_output():
    method = EnsembleUncertainty([lambda X: np.zeros(len(X)), lambda X: np.full(len(X), np.nan)])
    method.fit(np.ones((2, 1)), np.ones(2))
    with pytest.raises(ValueError, match="non-finite or misaligned"):
        method.estimate(np.ones((2, 1)))


def test_ensemble_is_registered():
    assert isinstance(UNCERTAINTY_METHODS.create("ensemble", members=[
        lambda X: X[:, 0], lambda X: X[:, 0] + 1
    ]), EnsembleUncertainty)
