"""Deterministic training-region validation for symbolic candidates.

This module deliberately accepts only the observed training arrays.  There is
no far/test-data parameter or selector hook in this API.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


@dataclass(frozen=True)
class TrainingFold:
    """One internal split, indexed relative to the supplied training arrays."""

    repeat: int
    fold: int
    train_indices: tuple[int, ...]
    validation_indices: tuple[int, ...]


@dataclass(frozen=True)
class FoldMetric:
    """Metrics for one candidate on one held-out training fold."""

    repeat: int
    fold: int
    rmse: float
    normalized_rmse: float | None
    validation_size: int
    fitted_expression: str | None = None


@dataclass(frozen=True)
class CandidateValidationSummary:
    """Aggregated internal-validation evidence; not a final test result."""

    expression: str
    fold_metrics: tuple[FoldMetric, ...]
    mean_rmse: float
    rmse_std: float
    worst_fold_rmse: float
    mean_normalized_rmse: float | None
    valid_fold_count: int
    failed_fold_count: int

    def to_dict(self) -> dict:
        return {
            "expression": self.expression,
            "fold_metrics": [
                {
                    "repeat": item.repeat,
                    "fold": item.fold,
                    "rmse": item.rmse,
                    "normalized_rmse": item.normalized_rmse,
                    "validation_size": item.validation_size,
                    "fitted_expression": item.fitted_expression,
                }
                for item in self.fold_metrics
            ],
            "mean_rmse": self.mean_rmse,
            "rmse_std": self.rmse_std,
            "worst_fold_rmse": self.worst_fold_rmse,
            "mean_normalized_rmse": self.mean_normalized_rmse,
            "valid_fold_count": self.valid_fold_count,
            "failed_fold_count": self.failed_fold_count,
            "selection_data_scope": "training_region_only",
            "expression_stability": expression_stability([
                item.fitted_expression for item in self.fold_metrics
                if item.fitted_expression is not None
            ]),
        }


def make_training_folds(
    n_samples: int,
    *,
    n_splits: int = 5,
    n_repeats: int = 3,
    validation_fraction: float = 0.2,
    seed: int = 42,
    strategy: str = "repeated_random",
) -> tuple[TrainingFold, ...]:
    """Create deterministic repeated holdouts or contiguous blocked holdouts.

    The returned indices refer only to the caller-supplied training arrays.
    Blocked folds hold out contiguous ranges and train on the complement.
    """
    if n_samples < 4:
        raise ValueError("at least 4 training samples are required")
    if n_splits < 2 or n_repeats < 1:
        raise ValueError("n_splits must be >= 2 and n_repeats must be >= 1")
    if not 0.0 < validation_fraction < 0.5:
        raise ValueError("validation_fraction must be between 0 and 0.5")
    if strategy not in {"repeated_random", "blocked"}:
        raise ValueError("strategy must be 'repeated_random' or 'blocked'")
    if strategy == "blocked" and n_repeats != 1:
        raise ValueError("blocked strategy requires n_repeats=1; repeated blocked folds would be duplicates")

    validation_size = max(1, int(round(n_samples * validation_fraction)))
    if n_samples - validation_size < 2:
        raise ValueError("each fold must retain at least two fitting samples")

    folds: list[TrainingFold] = []
    all_indices = np.arange(n_samples)
    rng = np.random.default_rng(seed)

    for repeat in range(n_repeats):
        if strategy == "repeated_random":
            for fold_index in range(n_splits):
                validation = np.sort(
                    rng.choice(all_indices, size=validation_size, replace=False)
                )
                train = np.setdiff1d(all_indices, validation, assume_unique=True)
                folds.append(TrainingFold(
                    repeat, fold_index,
                    tuple(int(i) for i in train),
                    tuple(int(i) for i in validation),
                ))
        else:
            # One deterministic contiguous partition; blocked mode is not
            # repeated because repeating identical ranges adds no evidence.
            starts = np.linspace(
                0, n_samples - validation_size, n_splits, dtype=int
            )
            if np.unique(starts).size != n_splits:
                raise ValueError("blocked split requires distinct contiguous validation windows")
            for fold_index, start_value in enumerate(starts):
                start = int(start_value)
                stop = start + validation_size
                if n_samples - validation_size < 2:
                    raise ValueError("blocked split produced an invalid fold")
                validation = all_indices[start:stop]
                train = np.concatenate((all_indices[:start], all_indices[stop:]))
                folds.append(TrainingFold(
                    repeat, fold_index,
                    tuple(int(i) for i in train),
                    tuple(int(i) for i in validation),
                ))
    return tuple(folds)


def evaluate_candidate_on_training_folds(
    expression: str,
    predictor: Callable[[np.ndarray, np.ndarray, np.ndarray], np.ndarray],
    X_train: np.ndarray,
    y_train: np.ndarray,
    folds: tuple[TrainingFold, ...],
    *,
    minimum_valid_folds: int = 2,
) -> CandidateValidationSummary:
    """Evaluate a fixed candidate on internal validation folds only.

    The predictor receives (X_fit, y_fit, X_validation) for one fold. It must
    fit all candidate parameters using only X_fit/y_fit and return predictions
    for X_validation. No far/test array can be supplied through this interface.
    """
    X = np.asarray(X_train, dtype=float)
    y = np.asarray(y_train, dtype=float).reshape(-1)
    if X.ndim != 2 or X.shape[0] != y.shape[0]:
        raise ValueError("X_train must be 2D and aligned with y_train")
    if not expression or not expression.strip():
        raise ValueError("expression must be non-empty")
    if minimum_valid_folds < 1:
        raise ValueError("minimum_valid_folds must be >= 1")
    if not folds:
        raise ValueError("at least one training fold is required")
    if not np.all(np.isfinite(X)) or not np.all(np.isfinite(y)):
        raise ValueError("training arrays must contain only finite values")

    metrics: list[FoldMetric] = []
    failures = 0
    for fold in folds:
        train_idx = np.asarray(fold.train_indices, dtype=int)
        valid_idx = np.asarray(fold.validation_indices, dtype=int)
        if (train_idx.size < 2 or valid_idx.size < 1
                or np.any(train_idx < 0) or np.any(valid_idx < 0)
                or np.any(train_idx >= len(y)) or np.any(valid_idx >= len(y))):
            raise ValueError("fold indices are invalid for supplied training arrays")
        if np.unique(train_idx).size != train_idx.size or np.unique(valid_idx).size != valid_idx.size:
            raise ValueError("fold indices must not contain duplicates")
        combined = np.concatenate((train_idx, valid_idx))
        if np.intersect1d(train_idx, valid_idx).size:
            raise ValueError("training and validation indices overlap")
        if combined.size != len(y) or not np.array_equal(np.sort(combined), np.arange(len(y))):
            raise ValueError("each fold must partition all supplied training rows")

        truth = y[valid_idx]
        try:
            prediction_result = predictor(X[train_idx], y[train_idx], X[valid_idx])
            fitted_expression = None
            if isinstance(prediction_result, tuple) and len(prediction_result) == 2:
                prediction_result, fitted_expression = prediction_result
            prediction = np.asarray(prediction_result, dtype=float).reshape(-1)
            if prediction.shape != truth.shape or not np.all(np.isfinite(prediction)):
                raise ValueError("predictor returned invalid or non-finite values")
            rmse = float(np.sqrt(np.mean(np.square(truth - prediction))))
            scale = float(np.std(y[train_idx]))
            nrmse = rmse / scale if np.isfinite(scale) and scale > 0 else None
            metrics.append(FoldMetric(
                fold.repeat, fold.fold, rmse, nrmse, int(valid_idx.size),
                str(fitted_expression) if fitted_expression is not None else None
            ))
        except Exception:
            failures += 1

    if len(metrics) < minimum_valid_folds:
        raise ValueError(
            f"insufficient valid training folds: {len(metrics)} < {minimum_valid_folds}"
        )

    rmses = np.asarray([item.rmse for item in metrics], dtype=float)
    normalized = [item.normalized_rmse for item in metrics]
    normalized_values = [value for value in normalized if value is not None]
    return CandidateValidationSummary(
        expression=expression,
        fold_metrics=tuple(metrics),
        mean_rmse=float(np.mean(rmses)),
        rmse_std=float(np.std(rmses)),
        worst_fold_rmse=float(np.max(rmses)),
        mean_normalized_rmse=(
            float(np.mean(normalized_values)) if normalized_values else None
        ),
        valid_fold_count=len(metrics),
        failed_fold_count=failures,
    )




def make_symbolic_refit_predictor(
    expression: str,
    variable_names: list[str] | tuple[str, ...],
    *,
    max_nfev: int = 500,
) -> Callable[[np.ndarray, np.ndarray, np.ndarray], tuple[np.ndarray, str]]:
    """Build a restricted symbolic predictor that refits float coefficients per fold.

    Only numeric floating-point coefficient literals are optimized; integer
    powers and integer constants remain structural. Every invocation starts
    from the original coefficients and estimates them using X_fit/y_fit only.
    This is coefficient refitting, not a fresh symbolic-structure search.
    """
    if max_nfev < 1:
        raise ValueError("max_nfev must be >= 1")
    import sympy as sp
    from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression

    names = tuple(variable_names)
    if not names or len(set(names)) != len(names):
        raise ValueError("variable_names must be non-empty and unique")
    parsed = parse_sympy_expression(expression, list(names))
    symbols = [sp.Symbol(name, real=True) for name in names]
    exponent_literals = {
        power.exp for power in parsed.atoms(sp.Pow)
        if isinstance(power.exp, sp.Float)
    }
    coefficients = sorted(
        parsed.atoms(sp.Float) - exponent_literals,
        key=lambda value: (float(value), str(value)),
    )
    coefficient_symbols = sp.symbols(f"_coef0:{len(coefficients)}") if coefficients else ()
    parameterized = parsed.xreplace(dict(zip(coefficients, coefficient_symbols)))
    initial = np.asarray([float(value) for value in coefficients], dtype=float)

    def _evaluate(matrix: np.ndarray, params: np.ndarray) -> np.ndarray:
        expr = parameterized.xreplace(dict(zip(coefficient_symbols, params)))
        fn = sp.lambdify(symbols, expr, modules="numpy")
        with np.errstate(all="ignore"):
            values = np.asarray(fn(*[matrix[:, index] for index in range(len(names))]), dtype=float)
        if values.ndim == 0:
            values = np.full(matrix.shape[0], float(values))
        return values.reshape(-1)

    def _predict(
        X_fit: np.ndarray, y_fit: np.ndarray, X_validation: np.ndarray
    ) -> tuple[np.ndarray, str]:
        Xf = np.asarray(X_fit, dtype=float)
        yf = np.asarray(y_fit, dtype=float).reshape(-1)
        Xv = np.asarray(X_validation, dtype=float)
        if (Xf.ndim != 2 or Xv.ndim != 2 or Xf.shape[1] != len(names)
                or Xv.shape[1] != len(names) or Xf.shape[0] != yf.size):
            raise ValueError("fold arrays do not match the declared symbolic variables")
        if not np.all(np.isfinite(Xf)) or not np.all(np.isfinite(yf)) or not np.all(np.isfinite(Xv)):
            raise ValueError("fold arrays must be finite")

        fitted = initial.copy()
        if coefficients:
            from scipy.optimize import least_squares

            def residual(params: np.ndarray) -> np.ndarray:
                predicted = _evaluate(Xf, params)
                if predicted.shape != yf.shape or not np.all(np.isfinite(predicted)):
                    return np.full(yf.shape, 1e100, dtype=float)
                return predicted - yf

            optimized = least_squares(
                residual, initial.copy(), max_nfev=max_nfev,
                method="trf", loss="linear",
            )
            if not optimized.success or not np.all(np.isfinite(optimized.x)):
                raise ValueError("fold-local coefficient refit did not converge")
            fitted = optimized.x
        predictions = _evaluate(Xv, fitted)
        if predictions.shape != (Xv.shape[0],) or not np.all(np.isfinite(predictions)):
            raise ValueError("refitted symbolic candidate produced invalid predictions")
        fitted_expr = str(parameterized.xreplace(dict(zip(coefficient_symbols, fitted))))
        return predictions, fitted_expr

    return _predict


def evaluate_symbolic_candidate_on_training_folds(
    expression: str,
    variable_names: list[str] | tuple[str, ...],
    X_train: np.ndarray,
    y_train: np.ndarray,
    folds: tuple[TrainingFold, ...],
    *,
    minimum_valid_folds: int = 2,
    max_nfev: int = 500,
) -> CandidateValidationSummary:
    """Refit numeric coefficients inside each training fold, then score its holdout."""
    predictor = make_symbolic_refit_predictor(
        expression, variable_names, max_nfev=max_nfev
    )
    return evaluate_candidate_on_training_folds(
        expression, predictor, X_train, y_train, folds,
        minimum_valid_folds=minimum_valid_folds,
    )


def expression_stability(expressions: list[str] | tuple[str, ...]) -> dict:
    """Report exact normalized-string recurrence across folds/seeds.

    This conservative first version does not claim symbolic equivalence:
    algebraically equivalent but differently written forms remain distinct.
    """
    if not expressions:
        return {
            "status": "insufficient_evidence",
            "expression_count": 0,
            "unique_expression_count": 0,
            "dominant_expression": None,
            "dominant_fraction": None,
            "normalization": "whitespace_and_power_operator_only",
        }
    normalized = [
        "".join(str(item).split()).replace("^", "**")
        for item in expressions
    ]
    counts: dict[str, int] = {}
    for item in normalized:
        counts[item] = counts.get(item, 0) + 1
    dominant, count = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[0]
    return {
        "status": "measured",
        "expression_count": len(normalized),
        "unique_expression_count": len(counts),
        "dominant_expression": dominant,
        "dominant_fraction": count / len(normalized),
        "normalization": "whitespace_and_power_operator_only",
    }



class FoldFeaturePreprocessor:
    """Fit deterministic per-column transforms on one fold's fitting rows only.

    This adapter handles raw input columns only. It does not create the
    symbolic engine's data-selected ratio/geometric-mean features, infer target
    transforms, or inspect validation rows during fit.
    """

    def __init__(
        self,
        feature_names: list[str] | tuple[str, ...],
        *,
        log_range_threshold: float = 4.0,
        log_magnitude_threshold: float = 1e5,
        scale_low: float = 1e-6,
        scale_high: float = 1e6,
    ) -> None:
        self.feature_names = tuple(str(name) for name in feature_names)
        if not self.feature_names or any(not name for name in self.feature_names):
            raise ValueError("feature_names must be non-empty")
        if len(set(self.feature_names)) != len(self.feature_names):
            raise ValueError("feature_names must be unique")
        if log_range_threshold <= 0 or log_magnitude_threshold <= 0:
            raise ValueError("log thresholds must be positive")
        if not 0 < scale_low < scale_high:
            raise ValueError("scale thresholds must satisfy 0 < low < high")
        self.log_range_threshold = float(log_range_threshold)
        self.log_magnitude_threshold = float(log_magnitude_threshold)
        self.scale_low = float(scale_low)
        self.scale_high = float(scale_high)
        self._fitted = False

    @staticmethod
    def _signed_log10(values: np.ndarray) -> np.ndarray:
        return np.sign(values) * np.log10(np.abs(values) + 1.0)

    def fit(self, X_fit: np.ndarray) -> "FoldFeaturePreprocessor":
        """Learn log flags and scale factors from X_fit only."""
        X = np.asarray(X_fit, dtype=float)
        if X.ndim != 2 or X.shape[1] != len(self.feature_names) or X.shape[0] < 2:
            raise ValueError("X_fit shape must match feature_names and contain >=2 rows")
        if not np.all(np.isfinite(X)):
            raise ValueError("X_fit must contain only finite values")

        log_flags: list[bool] = []
        for column in range(X.shape[1]):
            nonzero = np.abs(X[:, column][X[:, column] != 0])
            use_log = False
            if nonzero.size >= 2:
                span = float(np.log10(nonzero.max()) - np.log10(nonzero.min()))
                median_abs = float(np.median(nonzero))
                use_log = (
                    span > self.log_range_threshold
                    or median_abs > self.log_magnitude_threshold
                )
            log_flags.append(bool(use_log))

        transformed = X.copy()
        for index, use_log in enumerate(log_flags):
            if use_log:
                transformed[:, index] = self._signed_log10(transformed[:, index])

        scales = np.ones(X.shape[1], dtype=float)
        for index in range(X.shape[1]):
            column_scale = max(
                abs(float(np.mean(transformed[:, index]))),
                float(np.std(transformed[:, index])),
            )
            if column_scale > 0 and (
                column_scale < self.scale_low or column_scale > self.scale_high
            ):
                scales[index] = column_scale

        self.log_flags_ = tuple(log_flags)
        self.scales_ = scales
        self.n_features_in_ = int(X.shape[1])
        self._fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Apply frozen fold parameters without updating learned state."""
        if not self._fitted:
            raise RuntimeError("FoldFeaturePreprocessor must be fitted before transform")
        values = np.asarray(X, dtype=float)
        if values.ndim != 2 or values.shape[1] != self.n_features_in_:
            raise ValueError("X shape does not match the fitted feature schema")
        if not np.all(np.isfinite(values)):
            raise ValueError("X must contain only finite values")
        result = values.copy()
        for index, use_log in enumerate(self.log_flags_):
            if use_log:
                result[:, index] = self._signed_log10(result[:, index])
        result = result / self.scales_[np.newaxis, :]
        if not np.all(np.isfinite(result)):
            raise ValueError("fold preprocessing produced non-finite features")
        return result

    def fit_transform(self, X_fit: np.ndarray) -> np.ndarray:
        """Fit on the supplied fitting rows and transform those same rows."""
        return self.fit(X_fit).transform(X_fit)

    def get_feature_names_out(self) -> tuple[str, ...]:
        """Return the unchanged raw-column schema used by this adapter."""
        return self.feature_names

    def audit_state(self) -> dict:
        """Return JSON-friendly learned parameters for fold-level provenance."""
        if not self._fitted:
            raise RuntimeError("FoldFeaturePreprocessor is not fitted")
        return {
            "feature_names": list(self.feature_names),
            "signed_log_columns": [
                name for name, enabled in zip(self.feature_names, self.log_flags_)
                if enabled
            ],
            "column_scales": {
                name: float(scale)
                for name, scale in zip(self.feature_names, self.scales_)
            },
            "fit_scope": "fold_fitting_rows_only",
            "engineered_features": "not_generated",
            "target_transform": "not_applied",
        }



__all__ = [
    "FoldFeaturePreprocessor",
    "TrainingFold",
    "FoldMetric",
    "CandidateValidationSummary",
    "make_training_folds",
    "evaluate_candidate_on_training_folds",
    "make_symbolic_refit_predictor",
    "evaluate_symbolic_candidate_on_training_folds",
    "expression_stability",
]
