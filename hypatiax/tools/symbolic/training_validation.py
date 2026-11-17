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
            boundaries = np.linspace(0, n_samples, n_splits + 1, dtype=int)
            for fold_index in range(n_splits):
                start, stop = int(boundaries[fold_index]), int(boundaries[fold_index + 1])
                if stop - start < 1 or n_samples - (stop - start) < 2:
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
            prediction = np.asarray(
                predictor(X[train_idx], y[train_idx], X[valid_idx]), dtype=float
            ).reshape(-1)
            if prediction.shape != truth.shape or not np.all(np.isfinite(prediction)):
                raise ValueError("predictor returned invalid or non-finite values")
            rmse = float(np.sqrt(np.mean(np.square(truth - prediction))))
            scale = float(np.std(y[train_idx]))
            nrmse = rmse / scale if np.isfinite(scale) and scale > 0 else None
            metrics.append(FoldMetric(
                fold.repeat, fold.fold, rmse, nrmse, int(valid_idx.size)
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
        " ".join(str(item).replace("^", "**").split())
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


__all__ = [
    "TrainingFold",
    "FoldMetric",
    "CandidateValidationSummary",
    "make_training_folds",
    "evaluate_candidate_on_training_folds",
    "expression_stability",
]
