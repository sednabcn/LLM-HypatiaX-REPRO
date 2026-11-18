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
    if len(set(names)) != len(names):
        raise ValueError("variable_names must be unique")
    # PySR's printable equations use Julia-style '^' for powers; the
    # restricted Python AST parser requires '**'. No other syntax is rewritten.
    expression = str(expression).replace("^", "**")
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




@dataclass(frozen=True)
class FoldFeaturePlan:
    """Immutable engineered-feature schema selected from one fold's fit rows."""

    raw_feature_names: tuple[str, ...]
    geometric_mean_pairs: tuple[tuple[str, str], ...] = ()
    ratio_pairs: tuple[tuple[str, str], ...] = ()
    version: str = "1.0"

    @property
    def output_feature_names(self) -> tuple[str, ...]:
        raw = self.raw_feature_names
        geometric = tuple(f"gm_{left}_{right}" for left, right in self.geometric_mean_pairs)
        ratios = tuple(f"ratio_{left}_{right}" for left, right in self.ratio_pairs)
        return raw + geometric + ratios

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "raw_feature_names": list(self.raw_feature_names),
            "geometric_mean_pairs": [list(pair) for pair in self.geometric_mean_pairs],
            "ratio_pairs": [list(pair) for pair in self.ratio_pairs],
            "output_feature_names": list(self.output_feature_names),
            "selection_scope": "fold_fitting_rows_only",
        }


class FoldFeaturePipeline:
    """Fit raw transforms and optional GM/ratio feature selection per fold.

    The plan is learned exclusively from X_fit.  Validation rows are only
    transformed with the frozen plan.  This is a fold-local analogue of the
    repository's engineered input columns, not a claim that every domain
    heuristic or operator-selection branch in SymbolicEngine is reproduced.
    """

    def __init__(
        self,
        feature_names: list[str] | tuple[str, ...],
        *,
        include_geometric_means: bool = False,
        include_ratios: bool = False,
        max_ratio_features: int = 10,
        preprocessor: FoldFeaturePreprocessor | None = None,
    ) -> None:
        names = tuple(str(name) for name in feature_names)
        if not names or any(not name for name in names) or len(set(names)) != len(names):
            raise ValueError("feature_names must be non-empty and unique")
        if max_ratio_features < 0:
            raise ValueError("max_ratio_features must be >= 0")
        self.feature_names = names
        self.include_geometric_means = bool(include_geometric_means)
        self.include_ratios = bool(include_ratios)
        self.max_ratio_features = int(max_ratio_features)
        self.preprocessor = preprocessor or FoldFeaturePreprocessor(names)
        if self.preprocessor.get_feature_names_out() != names:
            raise ValueError("preprocessor feature schema must match feature_names")
        self._fitted = False

    def fit(self, X_fit: np.ndarray) -> "FoldFeaturePipeline":
        X = np.asarray(X_fit, dtype=float)
        if X.ndim != 2 or X.shape[1] != len(self.feature_names) or X.shape[0] < 2:
            raise ValueError("X_fit shape must match feature_names and contain >=2 rows")
        if not np.all(np.isfinite(X)):
            raise ValueError("X_fit must contain only finite values")

        base = self.preprocessor.fit_transform(X)
        positive_indices = [
            index for index in range(base.shape[1])
            if bool(np.all(base[:, index] > 0.0))
        ]
        gm_pairs: list[tuple[str, str]] = []
        if self.include_geometric_means:
            for offset, left_index in enumerate(positive_indices):
                for right_index in positive_indices[offset + 1:]:
                    gm_pairs.append((
                        self.feature_names[left_index],
                        self.feature_names[right_index],
                    ))

        ratio_candidates: list[tuple[float, str, str]] = []
        if self.include_ratios:
            for numerator in positive_indices:
                for denominator in positive_indices:
                    if numerator == denominator:
                        continue
                    ratio = base[:, numerator] / (base[:, denominator] + 1e-300)
                    if not np.all(np.isfinite(ratio)):
                        continue
                    ratio_candidates.append((
                        float(np.std(ratio)),
                        self.feature_names[numerator],
                        self.feature_names[denominator],
                    ))
        ratio_candidates.sort(key=lambda item: (-item[0], item[1], item[2]))
        ratio_pairs = tuple(
            (left, right)
            for _, left, right in ratio_candidates[:self.max_ratio_features]
        )
        self.plan_ = FoldFeaturePlan(
            raw_feature_names=self.feature_names,
            geometric_mean_pairs=tuple(gm_pairs),
            ratio_pairs=ratio_pairs,
        )
        self._fitted = True
        # Validate the fitting transform using the exact schema now frozen.
        self.transform(X)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("FoldFeaturePipeline must be fitted before transform")
        base = self.preprocessor.transform(X)
        columns = [base]
        index_by_name = {name: index for index, name in enumerate(self.feature_names)}

        for left, right in self.plan_.geometric_mean_pairs:
            left_values = base[:, index_by_name[left]]
            right_values = base[:, index_by_name[right]]
            if np.any(left_values <= 0.0) or np.any(right_values <= 0.0):
                raise ValueError(
                    f"geometric-mean feature {left!r}/{right!r} left its positive domain"
                )
            values = np.sqrt(left_values * right_values)
            if not np.all(np.isfinite(values)):
                raise ValueError("geometric-mean feature produced non-finite values")
            columns.append(values.reshape(-1, 1))

        for numerator, denominator in self.plan_.ratio_pairs:
            numerator_values = base[:, index_by_name[numerator]]
            denominator_values = base[:, index_by_name[denominator]]
            if np.any(numerator_values <= 0.0) or np.any(denominator_values <= 0.0):
                raise ValueError(
                    f"ratio feature {numerator!r}/{denominator!r} left its positive domain"
                )
            values = numerator_values / (denominator_values + 1e-300)
            if not np.all(np.isfinite(values)):
                raise ValueError("ratio feature produced non-finite values")
            columns.append(values.reshape(-1, 1))

        result = np.column_stack(columns) if len(columns) > 1 else base
        if result.shape[1] != len(self.plan_.output_feature_names):
            raise RuntimeError("fold feature plan and transformed matrix schema diverged")
        return result

    def fit_transform(self, X_fit: np.ndarray) -> np.ndarray:
        return self.fit(X_fit).transform(X_fit)

    def get_feature_names_out(self) -> tuple[str, ...]:
        if not self._fitted:
            raise RuntimeError("FoldFeaturePipeline must be fitted before feature names are available")
        return self.plan_.output_feature_names


    def check_candidate_schema(
        self, candidate_variable_names: list[str] | tuple[str, ...]
    ) -> dict:
        """Require exact candidate-variable order before any fold prediction."""
        if not self._fitted:
            raise RuntimeError("FoldFeaturePipeline must be fitted before schema checks")
        supplied = tuple(str(name) for name in candidate_variable_names)
        expected = self.plan_.output_feature_names
        return {
            "status": "compatible" if supplied == expected else "ineligible_feature_schema_mismatch",
            "compatible": supplied == expected,
            "expected_feature_names": list(expected),
            "candidate_variable_names": list(supplied),
            "missing_features": [name for name in supplied if name not in expected],
            "unavailable_features": [name for name in expected if name not in supplied],
            "order_matches": supplied == expected,
        }

    def audit_state(self) -> dict:
        if not self._fitted:
            raise RuntimeError("FoldFeaturePipeline is not fitted")
        return {
            "feature_plan": self.plan_.to_dict(),
            "preprocessing": self.preprocessor.audit_state(),
            "fit_scope": "fold_fitting_rows_only",
            "validation_used_for_plan_selection": False,
        }


class FoldTargetScaler:
    """Fit the symbolic engine's optional std-only target scale per fold."""

    def __init__(self, *, scale_low: float = 1e-4, scale_high: float = 1e4) -> None:
        if not 0 < scale_low < scale_high:
            raise ValueError("target scale thresholds must satisfy 0 < low < high")
        self.scale_low = float(scale_low)
        self.scale_high = float(scale_high)
        self._fitted = False

    def fit(self, y_fit: np.ndarray) -> "FoldTargetScaler":
        values = np.asarray(y_fit, dtype=float).reshape(-1)
        if values.size < 2 or not np.all(np.isfinite(values)):
            raise ValueError("y_fit must contain at least two finite values")
        std = float(np.std(values))
        self.scale_ = std if std > 0 and (std < self.scale_low or std > self.scale_high) else 1.0
        self._fitted = True
        return self

    def transform(self, y: np.ndarray) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("FoldTargetScaler must be fitted before transform")
        values = np.asarray(y, dtype=float).reshape(-1)
        if not np.all(np.isfinite(values)):
            raise ValueError("target values must be finite")
        result = values / self.scale_
        if not np.all(np.isfinite(result)):
            raise ValueError("target scaling produced non-finite values")
        return result

    def inverse_transform(self, y_scaled: np.ndarray) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("FoldTargetScaler must be fitted before inverse_transform")
        values = np.asarray(y_scaled, dtype=float).reshape(-1)
        if not np.all(np.isfinite(values)):
            raise ValueError("scaled target values must be finite")
        result = values * self.scale_
        if not np.all(np.isfinite(result)):
            raise ValueError("inverse target scaling produced non-finite values")
        return result

    def fit_transform(self, y_fit: np.ndarray) -> np.ndarray:
        return self.fit(y_fit).transform(y_fit)

    def audit_state(self) -> dict:
        if not self._fitted:
            raise RuntimeError("FoldTargetScaler is not fitted")
        return {
            "scale": float(self.scale_),
            "fit_scope": "fold_fitting_targets_only",
            "centering": "none",
        }



def make_fold_preprocessed_symbolic_predictor(
    expression: str,
    candidate_variable_names: list[str] | tuple[str, ...],
    raw_feature_names: list[str] | tuple[str, ...],
    *,
    include_geometric_means: bool = False,
    include_ratios: bool = False,
    max_ratio_features: int = 10,
    max_nfev: int = 500,
) -> Callable[[np.ndarray, np.ndarray, np.ndarray], tuple[np.ndarray, str]]:
    """Create a fold callback with fold-local X features and y scaling.

    Each invocation independently fits feature preprocessing, engineered
    feature selection, and target scaling on that fold's fitting rows only.
    Candidate feature names must exactly match the fold plan in both content
    and order. The fixed symbolic structure is coefficient-refitted per fold;
    this is not a fresh PySR search.
    """
    variable_names = tuple(candidate_variable_names)
    raw_names = tuple(raw_feature_names)
    if not raw_names or len(set(raw_names)) != len(raw_names):
        raise ValueError("raw_feature_names must be non-empty and unique")
    if not variable_names or len(set(variable_names)) != len(variable_names):
        raise ValueError("candidate_variable_names must be non-empty and unique")
    symbolic_predictor = make_symbolic_refit_predictor(
        expression, variable_names, max_nfev=max_nfev
    )

    def _predict(
        X_fit: np.ndarray, y_fit: np.ndarray, X_validation: np.ndarray
    ) -> tuple[np.ndarray, str]:
        pipeline = FoldFeaturePipeline(
            raw_names,
            include_geometric_means=include_geometric_means,
            include_ratios=include_ratios,
            max_ratio_features=max_ratio_features,
        ).fit(X_fit)
        compatibility = pipeline.check_candidate_schema(variable_names)
        if not compatibility["compatible"]:
            raise ValueError(
                "candidate is ineligible for this fold: feature schema mismatch "
                f"(expected={compatibility['expected_feature_names']}, "
                f"candidate={compatibility['candidate_variable_names']})"
            )
        X_fit_fold = pipeline.transform(X_fit)
        X_validation_fold = pipeline.transform(X_validation)
        target_scaler = FoldTargetScaler().fit(y_fit)
        y_fit_scaled = target_scaler.transform(y_fit)
        prediction_scaled, fitted_expression = symbolic_predictor(
            X_fit_fold, y_fit_scaled, X_validation_fold
        )
        prediction = target_scaler.inverse_transform(prediction_scaled)
        return prediction, fitted_expression

    return _predict


def evaluate_preprocessed_symbolic_candidate_on_training_folds(
    expression: str,
    candidate_variable_names: list[str] | tuple[str, ...],
    raw_feature_names: list[str] | tuple[str, ...],
    X_train: np.ndarray,
    y_train: np.ndarray,
    folds: tuple[TrainingFold, ...],
    *,
    include_geometric_means: bool = False,
    include_ratios: bool = False,
    max_ratio_features: int = 10,
    minimum_valid_folds: int = 2,
    max_nfev: int = 500,
) -> CandidateValidationSummary:
    """Evaluate a fixed expression with fold-local X plans and target scaling."""
    predictor = make_fold_preprocessed_symbolic_predictor(
        expression,
        candidate_variable_names,
        raw_feature_names,
        include_geometric_means=include_geometric_means,
        include_ratios=include_ratios,
        max_ratio_features=max_ratio_features,
        max_nfev=max_nfev,
    )
    return evaluate_candidate_on_training_folds(
        expression, predictor, X_train, y_train, folds,
        minimum_valid_folds=minimum_valid_folds,
    )



class FoldCandidateFeaturePipeline:
    """Rebuild exactly the feature symbols used by one candidate inside a fold.

    Unlike FoldFeaturePipeline's complete generated schema, this adapter emits
    only the candidate's declared symbols, in the candidate's original order.
    Raw signed-log flags and extreme-column scales are fitted on X_fit only.
    GM and directed-ratio values are then computed from those frozen transformed
    columns. Candidate-selected pairs are not silently replaced by a different
    top-k ratio set in another fold.
    """

    def __init__(
        self,
        raw_feature_names: list[str] | tuple[str, ...],
        candidate_variable_names: list[str] | tuple[str, ...],
    ) -> None:
        self.raw_feature_names = tuple(str(name) for name in raw_feature_names)
        self.candidate_variable_names = tuple(str(name) for name in candidate_variable_names)
        if not self.raw_feature_names or len(set(self.raw_feature_names)) != len(self.raw_feature_names):
            raise ValueError("raw_feature_names must be non-empty and unique")
        if len(set(self.candidate_variable_names)) != len(self.candidate_variable_names):
            raise ValueError("candidate_variable_names must be unique")
        self.preprocessor = FoldFeaturePreprocessor(self.raw_feature_names)
        self._fitted = False

    def fit(self, X_fit: np.ndarray) -> "FoldCandidateFeaturePipeline":
        values = np.asarray(X_fit, dtype=float)
        base = self.preprocessor.fit_transform(values)
        raw_index = {name: index for index, name in enumerate(self.raw_feature_names)}
        engineered: dict[str, tuple[str, int, int]] = {}
        for left_index, left in enumerate(self.raw_feature_names):
            for right_index in range(left_index + 1, len(self.raw_feature_names)):
                right = self.raw_feature_names[right_index]
                engineered[f"gm_{left}_{right}"] = ("gm", left_index, right_index)
            for right_index, right in enumerate(self.raw_feature_names):
                if left_index != right_index:
                    engineered[f"ratio_{left}_{right}"] = ("ratio", left_index, right_index)

        missing = [
            name for name in self.candidate_variable_names
            if name not in raw_index and name not in engineered
        ]
        if missing:
            raise ValueError(f"candidate references unknown engineered feature(s): {missing}")

        self._feature_specs = []
        for name in self.candidate_variable_names:
            if name in raw_index:
                self._feature_specs.append(("raw", raw_index[name], -1))
            else:
                kind, left, right = engineered[name]
                self._feature_specs.append((kind, left, right))
        self.n_features_in_ = int(values.shape[1])
        self._fitted = True
        # Fail on invalid fit-domain features before scoring any validation rows.
        self.transform(values)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("FoldCandidateFeaturePipeline must be fitted first")
        values = self.preprocessor.transform(X)
        columns = []
        for kind, left, right in self._feature_specs:
            if kind == "raw":
                feature = values[:, left]
            elif kind == "gm":
                a, b = values[:, left], values[:, right]
                if np.any(a <= 0.0) or np.any(b <= 0.0):
                    raise ValueError("candidate geometric-mean feature left its positive domain")
                with np.errstate(invalid="ignore", over="ignore"):
                    feature = np.sqrt(a * b)
            else:
                a, b = values[:, left], values[:, right]
                if np.any(a <= 0.0) or np.any(b <= 0.0):
                    raise ValueError("candidate ratio feature left its positive domain")
                with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
                    feature = a / (b + 1e-300)
            if not np.isfinite(feature).all():
                raise FloatingPointError("candidate engineered feature is non-finite")
            columns.append(np.asarray(feature, dtype=float).reshape(-1, 1))
        result = (
            np.column_stack(columns)
            if columns else np.empty((values.shape[0], 0), dtype=float)
        )
        if result.shape != (values.shape[0], len(self.candidate_variable_names)):
            raise RuntimeError("candidate fold feature matrix has an invalid schema")
        return result

    def audit_state(self) -> dict:
        if not self._fitted:
            raise RuntimeError("FoldCandidateFeaturePipeline is not fitted")
        return {
            "raw_feature_names": list(self.raw_feature_names),
            "candidate_variable_names": list(self.candidate_variable_names),
            "feature_specs": [
                {"kind": kind, "left_index": left, "right_index": right}
                for kind, left, right in self._feature_specs
            ],
            "preprocessing": self.preprocessor.audit_state(),
            "fit_scope": "fold_fitting_rows_only",
            "validation_used_for_feature_selection": False,
            "ratio_selection": "candidate_specific_pair_reconstructed_per_fold",
        }


class FoldTargetPreprocessor:
    """Reproduce Hybrid's outer signed-log and inner std target transforms per fold."""

    def __init__(self, *, log_range_threshold: float = 4.0,
                 scale_low: float = 1e-4, scale_high: float = 1e4) -> None:
        if log_range_threshold <= 0 or not 0 < scale_low < scale_high:
            raise ValueError("invalid target preprocessing thresholds")
        self.log_range_threshold = float(log_range_threshold)
        self.scale_low = float(scale_low)
        self.scale_high = float(scale_high)
        self._fitted = False

    @staticmethod
    def _signed_log10(values: np.ndarray) -> np.ndarray:
        return np.sign(values) * np.log10(np.abs(values) + 1.0)

    def fit(self, y_fit: np.ndarray) -> "FoldTargetPreprocessor":
        values = np.asarray(y_fit, dtype=float).reshape(-1)
        if values.size < 2 or not np.isfinite(values).all():
            raise ValueError("y_fit must contain at least two finite observations")
        nonzero = np.abs(values[values != 0.0])
        self.log_enabled_ = bool(
            nonzero.size >= 2
            and np.log10(float(nonzero.max())) - np.log10(float(nonzero.min()))
                > self.log_range_threshold
        )
        outer = self._signed_log10(values) if self.log_enabled_ else values.copy()
        std = float(np.std(outer))
        self.scale_ = std if std > 0.0 and (
            std < self.scale_low or std > self.scale_high
        ) else 1.0
        self._fitted = True
        return self

    def transform(self, y: np.ndarray) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("FoldTargetPreprocessor must be fitted first")
        values = np.asarray(y, dtype=float).reshape(-1)
        if not np.isfinite(values).all():
            raise ValueError("target values must be finite")
        outer = self._signed_log10(values) if self.log_enabled_ else values
        result = outer / self.scale_
        if not np.isfinite(result).all():
            raise FloatingPointError("fold target transform produced non-finite values")
        return result

    def inverse_transform(self, y_fit_space: np.ndarray) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("FoldTargetPreprocessor must be fitted first")
        values = np.asarray(y_fit_space, dtype=float).reshape(-1) * self.scale_
        if not np.isfinite(values).all():
            raise FloatingPointError("fold target inverse scale is non-finite")
        if self.log_enabled_:
            exponent = np.clip(np.abs(values), 0.0, 308.0)
            with np.errstate(over="ignore", invalid="ignore"):
                values = np.sign(values) * (np.power(10.0, exponent) - 1.0)
        if not np.isfinite(values).all():
            raise FloatingPointError("fold target inverse transform is non-finite")
        return values

    def audit_state(self) -> dict:
        if not self._fitted:
            raise RuntimeError("FoldTargetPreprocessor is not fitted")
        return {
            "signed_log10": bool(self.log_enabled_),
            "std_scale": float(self.scale_),
            "fit_scope": "fold_fitting_targets_only",
            "centering": "none",
        }


def evaluate_engine_candidate_on_training_folds(
    expression: str,
    candidate_variable_names: list[str] | tuple[str, ...],
    raw_feature_names: list[str] | tuple[str, ...],
    X_train: np.ndarray,
    y_train: np.ndarray,
    folds: tuple[TrainingFold, ...],
    *,
    minimum_valid_folds: int = 2,
    max_nfev: int = 500,
) -> CandidateValidationSummary:
    """Evaluate an engine-space candidate with fold-local features and target transforms.

    The expression must be the unannotated PySR fit-space expression, and its
    variable names must be the exact PySR feature schema for that candidate.
    Coefficients are refitted on each fold's fitting partition; validation rows
    are transformed with parameters learned only from that partition.
    """
    names = tuple(candidate_variable_names)
    raw_names = tuple(raw_feature_names)
    import sympy as sp
    from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression

    normalized_expression = str(expression).replace("^", "**")
    parsed = parse_sympy_expression(normalized_expression, list(names))
    used_names = tuple(
        name for name in names
        if sp.Symbol(name, real=True) in parsed.free_symbols
    )
    refit = make_symbolic_refit_predictor(
        normalized_expression, used_names, max_nfev=max_nfev
    )

    def predict(X_fit, y_fit, X_validation):
        feature_pipeline = FoldCandidateFeaturePipeline(raw_names, used_names).fit(X_fit)
        X_fit_features = feature_pipeline.transform(X_fit)
        X_validation_features = feature_pipeline.transform(X_validation)
        target_pipeline = FoldTargetPreprocessor().fit(y_fit)
        y_fit_transformed = target_pipeline.transform(y_fit)
        prediction_transformed, fitted_expression = refit(
            X_fit_features, y_fit_transformed, X_validation_features
        )
        prediction = target_pipeline.inverse_transform(prediction_transformed)
        return prediction, fitted_expression

    return evaluate_candidate_on_training_folds(
        expression, predict, X_train, y_train, tuple(folds),
        minimum_valid_folds=minimum_valid_folds,
    )


__all__ = [
    "FoldFeaturePreprocessor",
    "FoldFeaturePlan",
    "FoldFeaturePipeline",
    "FoldTargetScaler",
    "FoldCandidateFeaturePipeline",
    "FoldTargetPreprocessor",
    "evaluate_engine_candidate_on_training_folds",
    "make_fold_preprocessed_symbolic_predictor",
    "evaluate_preprocessed_symbolic_candidate_on_training_folds",
    "TrainingFold",
    "FoldMetric",
    "CandidateValidationSummary",
    "make_training_folds",
    "evaluate_candidate_on_training_folds",
    "make_symbolic_refit_predictor",
    "evaluate_symbolic_candidate_on_training_folds",
    "expression_stability",
]
