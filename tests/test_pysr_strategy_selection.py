"""Offline tests for paired training-only PySR strategy selection."""
import numpy as np

from hypatiax.tools.symbolic.training_validation import make_training_folds
from hypatiax.tools.symbolic.pysr_strategy_selection import (
    select_pysr_search_strategy_on_training_folds,
)


class LinearFakePySR:
    def __init__(self, intercept, seed):
        self.intercept = float(intercept)
        self.seed = seed
        self.fitted = False

    def fit(self, X, y):
        self.fitted = True
        return self

    def get_best(self):
        return {"equation": f"x0 + {self.intercept}"}

    def predict(self, X):
        assert self.fitted
        return X[:, 0] + self.intercept


class InvalidFakePySR(LinearFakePySR):
    def predict(self, X):
        return np.full(len(X), np.nan)


def test_selects_strategy_by_paired_training_fold_nrmse():
    X = np.arange(120, dtype=float).reshape(60, 2) / 10.0
    y = X[:, 0] + 1.0
    folds = make_training_folds(60, n_splits=3, n_repeats=2, seed=17)

    result = select_pysr_search_strategy_on_training_folds(
        {
            "accurate": lambda seed: LinearFakePySR(1.0, seed),
            "poor": lambda seed: LinearFakePySR(8.0, seed),
        },
        X,
        y,
        folds,
        seed=17,
    )

    assert result.status == "selected"
    assert result.selected_strategy == "accurate"
    assert result.ranked_strategies[0].mean_normalized_rmse < (
        result.ranked_strategies[1].mean_normalized_rmse
    )
    audit = result.to_dict()
    assert audit["far_test_data_used"] is False
    assert audit["selected_artifact"] == "search_configuration_only"
    assert audit["final_full_training_search_required"] is True


def test_returns_no_credible_candidate_when_every_strategy_fails():
    X = np.arange(80, dtype=float).reshape(40, 2) / 10.0
    y = X[:, 0] + 1.0
    folds = make_training_folds(40, n_splits=2, n_repeats=1, seed=5)

    result = select_pysr_search_strategy_on_training_folds(
        {"invalid": InvalidFakePySR},
        X,
        y,
        folds,
        minimum_valid_folds=2,
    )

    assert result.status == "NO_CREDIBLE_CANDIDATE"
    assert result.selected_strategy is None
    assert len(result.rejected_strategies) == 1


def test_configured_quality_limit_rejects_all_strategies():
    X = np.arange(80, dtype=float).reshape(40, 2) / 10.0
    y = X[:, 0] + 1.0
    folds = make_training_folds(40, n_splits=2, n_repeats=1, seed=5)

    result = select_pysr_search_strategy_on_training_folds(
        {"poor": lambda seed: LinearFakePySR(9.0, seed)},
        X,
        y,
        folds,
        max_mean_normalized_rmse=0.01,
    )

    assert result.status == "NO_CREDIBLE_CANDIDATE"
    assert result.selected_strategy is None
