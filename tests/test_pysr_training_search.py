"""Offline contract tests for fresh PySR search per training fold."""
import numpy as np
import pytest

from hypatiax.tools.symbolic.training_validation import make_training_folds
from hypatiax.tools.symbolic.pysr_training_search import (
    evaluate_pysr_search_on_training_folds,
)


class FakePySR:
    def __init__(self, seed):
        self.seed = seed
        self.fitted = False

    def fit(self, X, y):
        self.fitted = True
        self.mean_ = float(np.mean(y))
        return self

    def get_best(self):
        return {"equation": "x0"}

    def predict(self, X):
        assert self.fitted
        return np.full(len(X), self.mean_)


def test_runs_a_fresh_searcher_for_each_training_fold():
    X = np.arange(60, dtype=float).reshape(30, 2)
    y = 2.0 * X[:, 0] + 1.0
    folds = make_training_folds(30, n_splits=3, n_repeats=2, seed=9)
    created = []

    def factory(seed):
        model = FakePySR(seed)
        created.append(model)
        return model

    result = evaluate_pysr_search_on_training_folds(factory, X, y, folds)

    assert len(created) == len(folds)
    assert len({id(model) for model in created}) == len(folds)
    assert len(result.fold_searches) == len(folds)
    assert result.validation.valid_fold_count == len(folds)
    assert all(item["fit_scope"] == "fold_fitting_rows_only" for item in result.fold_searches)
    assert result.to_dict()["far_test_data_used"] is False


def test_rejects_factory_that_reuses_a_fitted_model():
    X = np.arange(40, dtype=float).reshape(20, 2)
    y = X[:, 0]
    folds = make_training_folds(20, n_splits=2, n_repeats=1, seed=4)
    shared = FakePySR(42)

    with pytest.raises(ValueError, match="fresh PySR model"):
        evaluate_pysr_search_on_training_folds(
            lambda seed: shared, X, y, folds, minimum_valid_folds=2
        )


def test_invalid_held_out_predictions_fail_validation():
    class BadPySR(FakePySR):
        def predict(self, X):
            return np.full(len(X), np.nan)

    X = np.arange(40, dtype=float).reshape(20, 2)
    y = X[:, 0]
    folds = make_training_folds(20, n_splits=2, n_repeats=1, seed=4)

    with pytest.raises(ValueError, match="insufficient valid training folds"):
        evaluate_pysr_search_on_training_folds(
            BadPySR, X, y, folds, minimum_valid_folds=2
        )


class FakeDeadline:
    def __init__(self, *, expires_after_fit=False):
        self.is_expired = False
        self.expires_after_fit = expires_after_fit

    def expired(self):
        return self.is_expired

    def mark_fit_complete(self):
        if self.expires_after_fit:
            self.is_expired = True


def test_expired_deadline_prevents_starting_fold_search():
    X = np.arange(40, dtype=float).reshape(20, 2)
    y = X[:, 0]
    folds = make_training_folds(20, n_splits=2, n_repeats=1, seed=4)
    deadline = FakeDeadline()
    deadline.is_expired = True
    created = []

    class MustNotFit(FakePySR):
        def fit(self, X, y):
            created.append(self)
            raise AssertionError("expired fold search must not start")

    with pytest.raises(TimeoutError, match="before fixed-candidate fold evaluation"):
        evaluate_pysr_search_on_training_folds(
            MustNotFit, X, y, folds, minimum_valid_folds=2,
            budget_runtime=deadline,
        )
    assert created == []


def test_fold_result_returned_after_deadline_is_rejected():
    X = np.arange(40, dtype=float).reshape(20, 2)
    y = X[:, 0]
    folds = make_training_folds(20, n_splits=2, n_repeats=1, seed=4)
    deadline = FakeDeadline(expires_after_fit=True)
    calls = []

    class LatePySR(FakePySR):
        def fit(self, X, y):
            calls.append("fit")
            super().fit(X, y)
            deadline.mark_fit_complete()

        def get_best(self):
            calls.append("get_best")
            return super().get_best()

    with pytest.raises(TimeoutError, match="training-fold search returned after"):
        evaluate_pysr_search_on_training_folds(
            LatePySR, X, y, folds, minimum_valid_folds=2,
            budget_runtime=deadline,
        )
    assert calls == ["fit"]



def test_validation_prediction_returned_after_deadline_is_rejected():
    X = np.arange(40, dtype=float).reshape(20, 2)
    y = X[:, 0]
    folds = make_training_folds(20, n_splits=2, n_repeats=1, seed=12)
    deadline = FakeDeadline()
    calls = []

    class LatePredictionPySR(FakePySR):
        def predict(self, X):
            calls.append("predict")
            deadline.is_expired = True
            return super().predict(X)

    with pytest.raises(TimeoutError, match="validation prediction returned after"):
        evaluate_pysr_search_on_training_folds(
            LatePredictionPySR, X, y, folds, minimum_valid_folds=2,
            budget_runtime=deadline,
        )
    assert calls == ["predict"]


def test_expression_extraction_returned_after_deadline_is_rejected():
    X = np.arange(40, dtype=float).reshape(20, 2)
    y = X[:, 0]
    folds = make_training_folds(20, n_splits=2, n_repeats=1, seed=15)
    deadline = FakeDeadline()
    calls = []

    class LateExpressionPySR(FakePySR):
        def get_best(self):
            calls.append("get_best")
            deadline.is_expired = True
            return super().get_best()

    with pytest.raises(TimeoutError, match="expression extraction returned after"):
        evaluate_pysr_search_on_training_folds(
            LateExpressionPySR, X, y, folds, minimum_valid_folds=2,
            budget_runtime=deadline,
        )
    assert calls == ["get_best"]



def test_strategy_selector_propagates_deadline_instead_of_trying_next_strategy():
    from hypatiax.tools.symbolic.pysr_strategy_selection import (
        select_pysr_search_strategy_on_training_folds,
    )

    X = np.arange(40, dtype=float).reshape(20, 2)
    y = X[:, 0]
    folds = make_training_folds(20, n_splits=2, n_repeats=1, seed=18)
    deadline = FakeDeadline()
    later_strategy_calls = []

    class LateStrategyPySR(FakePySR):
        def predict(self, X):
            deadline.is_expired = True
            return super().predict(X)

    def later_factory(seed):
        later_strategy_calls.append(seed)
        return FakePySR(seed)

    with pytest.raises(TimeoutError, match="validation prediction returned after"):
        select_pysr_search_strategy_on_training_folds(
            {"a_late_strategy": LateStrategyPySR, "z_must_not_start": later_factory},
            X, y, folds, minimum_valid_folds=2, budget_runtime=deadline,
        )
    assert later_strategy_calls == []
