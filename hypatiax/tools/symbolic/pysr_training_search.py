"""Fresh PySR symbolic search inside each training-only validation fold."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np

from .training_validation import (
    CandidateValidationSummary,
    TrainingFold,
    evaluate_candidate_on_training_folds,
)


@dataclass(frozen=True)
class PySRFoldSearchSummary:
    """Training-only metrics plus per-fold PySR search provenance."""
    validation: CandidateValidationSummary
    fold_searches: tuple[dict, ...]

    def to_dict(self) -> dict:
        return {
            "validation": self.validation.to_dict(),
            "fold_searches": [dict(item) for item in self.fold_searches],
            "search_scope": "fresh_pysr_search_per_training_fold",
            "far_test_data_used": False,
        }


def _best_expression(model: Any) -> str:
    """Read the selected equation from PySR's public get_best() interface."""
    if not callable(getattr(model, "get_best", None)):
        raise TypeError("PySR model must expose get_best()")
    best = model.get_best()
    if isinstance(best, dict):
        expression = best.get("equation")
    else:
        try:
            expression = best["equation"]
        except (KeyError, TypeError, IndexError):
            expression = getattr(best, "equation", None)
    if expression is None or not str(expression).strip():
        raise ValueError("PySR get_best() returned no equation")
    return str(expression)


def evaluate_pysr_search_on_training_folds(
    searcher_factory: Callable[[int], Any],
    X_train: np.ndarray,
    y_train: np.ndarray,
    folds: tuple[TrainingFold, ...],
    *,
    seed: int = 42,
    minimum_valid_folds: int = 2,
    budget_runtime: Any | None = None,
) -> PySRFoldSearchSummary:
    """Run an independent PySR search and held-out prediction in every fold.

    The factory receives a deterministic fold seed and must return a new,
    unfitted PySRRegressor-compatible instance. All model fitting and
    data-dependent preprocessing must use X_fit/y_fit only. The validation
    partition is passed only to predict() after fitting.
    """
    X = np.asarray(X_train, dtype=float)
    y = np.asarray(y_train, dtype=float).reshape(-1)
    if X.ndim != 2 or X.shape[0] != y.size:
        raise ValueError("X_train must be 2D and aligned with y_train")
    if not np.all(np.isfinite(X)) or not np.all(np.isfinite(y)):
        raise ValueError("training arrays must contain only finite values")
    if not folds:
        raise ValueError("at least one training fold is required")

    audits: list[dict] = []
    retained_models: list[Any] = []
    invocation_index = 0

    def _search_and_predict(
        X_fit: np.ndarray, y_fit: np.ndarray, X_validation: np.ndarray
    ) -> tuple[np.ndarray, str]:
        nonlocal invocation_index
        fold = folds[invocation_index]
        invocation_index += 1
        if budget_runtime is not None and budget_runtime.expired():
            raise TimeoutError("discovery wall-time budget expired before training-fold search")
        fold_seed = int(seed + fold.repeat * 100_003 + fold.fold)
        model = searcher_factory(fold_seed)
        if model is None:
            raise ValueError("searcher_factory returned None")
        if any(model is previous for previous in retained_models):
            raise ValueError("searcher_factory must return a fresh PySR model for every fold")
        retained_models.append(model)
        if not callable(getattr(model, "fit", None)) or not callable(
            getattr(model, "predict", None)
        ):
            raise TypeError("searcher must expose fit(X, y) and predict(X)")
        model.fit(X_fit, y_fit)
        if budget_runtime is not None and budget_runtime.expired():
            raise TimeoutError("training-fold search returned after discovery wall-time deadline")
        expression = _best_expression(model)
        predictions = np.asarray(model.predict(X_validation), dtype=float).reshape(-1)
        if predictions.shape != (X_validation.shape[0],):
            raise ValueError("PySR returned a prediction array with the wrong shape")
        if not np.all(np.isfinite(predictions)):
            raise ValueError("PySR returned non-finite held-out predictions")
        audits.append({
            "repeat": fold.repeat,
            "fold": fold.fold,
            "seed": fold_seed,
            "model_class": type(model).__name__,
            "expression": expression,
            "variable_names": list(getattr(model, "fit_variable_names", []) or []),
            "fit_rows": int(X_fit.shape[0]),
            "validation_rows": int(X_validation.shape[0]),
            "fit_scope": "fold_fitting_rows_only",
        })
        return predictions, expression

    validation = evaluate_candidate_on_training_folds(
        expression="<fresh_pysr_search_per_fold>",
        predictor=_search_and_predict,
        X_train=X,
        y_train=y,
        folds=folds,
        minimum_valid_folds=minimum_valid_folds,
    )
    return PySRFoldSearchSummary(validation=validation, fold_searches=tuple(audits))


__all__ = ["PySRFoldSearchSummary", "evaluate_pysr_search_on_training_folds"]
