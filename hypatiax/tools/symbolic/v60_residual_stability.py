"""V60 training-only residual diagnostics and fold coefficient stability.

Diagnostics are reconstructed from the supplied training arrays and the
already-recorded fold-local affine coefficients. This module has no far/test
data input and never ranks, filters, or selects candidates.
"""
from __future__ import annotations

import math
from time import monotonic
from typing import Any, Mapping, Sequence

import numpy as np

from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be finite")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _correlation(left: np.ndarray, right: np.ndarray) -> float | None:
    if left.size < 2 or right.size != left.size:
        return None
    if float(np.std(left)) == 0.0 or float(np.std(right)) == 0.0:
        return None
    value = float(np.corrcoef(left, right)[0, 1])
    return value if math.isfinite(value) else None


def _residual_summary(residual: np.ndarray, predictions: np.ndarray,
                      row_indices: np.ndarray) -> dict[str, Any]:
    residual = np.asarray(residual, dtype=float).reshape(-1)
    predictions = np.asarray(predictions, dtype=float).reshape(-1)
    if residual.size == 0 or predictions.size != residual.size:
        raise ValueError("residual and prediction rows must be non-empty and aligned")
    if not np.all(np.isfinite(residual)) or not np.all(np.isfinite(predictions)):
        raise ValueError("residual diagnostics require finite values")
    ordered = np.argsort(row_indices)
    ordered_residual = residual[ordered]
    lag1 = _correlation(ordered_residual[:-1], ordered_residual[1:])
    rmse = float(np.sqrt(np.mean(np.square(residual))))
    std = float(np.std(residual))
    return {
        "row_count": int(residual.size),
        "residual_mean": float(np.mean(residual)),
        "residual_std": std,
        "residual_rmse": rmse,
        "residual_mae": float(np.mean(np.abs(residual))),
        "residual_bias_over_rmse": float(np.mean(residual) / rmse) if rmse > 0 else 0.0,
        "residual_lag1_correlation_by_row_order": lag1,
        "abs_residual_vs_abs_prediction_correlation": _correlation(
            np.abs(residual), np.abs(predictions)
        ),
        "positive_residual_fraction": float(np.mean(residual > 0)),
        "zero_residual_fraction": float(np.mean(residual == 0)),
    }


def diagnose_native_training_residuals(
    candidates: Sequence[Mapping[str, Any]],
    validation_audit: Mapping[str, Any],
    X: Any,
    y: Any,
    *,
    variable_names: Sequence[str],
    max_candidates: int = 100,
    max_search_attempts: int = 100,
    max_wall_time_seconds: float | None = None,
) -> dict[str, Any]:
    """Reconstruct held-out fold residuals and coefficient stability on training rows."""
    for name, value in (("max_candidates", max_candidates),
                        ("max_search_attempts", max_search_attempts)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    if max_wall_time_seconds is not None and (
        isinstance(max_wall_time_seconds, bool)
        or not isinstance(max_wall_time_seconds, (int, float))
        or not math.isfinite(float(max_wall_time_seconds))
        or max_wall_time_seconds <= 0
    ):
        raise ValueError("max_wall_time_seconds must be finite and > 0 or None")
    features = np.asarray(X, dtype=float)
    targets = np.asarray(y, dtype=float)
    if features.ndim != 2 or features.shape[1] != len(variable_names):
        raise ValueError("training features must be 2-D and align with variable_names")
    if targets.size != features.shape[0]:
        raise ValueError("training targets must contain one value per feature row")
    targets = targets.reshape(-1)
    if not np.all(np.isfinite(features)) or not np.all(np.isfinite(targets)):
        raise ValueError("training arrays must be finite; rows are never dropped")
    if validation_audit.get("validation_method") != "training_only_refit_cross_validation":
        raise ValueError("training-only cross-validation evidence is required")
    if validation_audit.get("far_or_evaluation_data_used") is not False:
        raise ValueError("validation evidence must exclude far/evaluation data")
    if validation_audit.get("validation_status") != "completed":
        return {
            "schema": "v60_native_residual_stability_v1",
            "diagnostic_status": "insufficient_validation_evidence",
            "reason": "training validation did not complete",
            "candidate_diagnostics": [], "selection_performed": False,
            "far_or_evaluation_data_used": False,
        }

    proposals: dict[str, Mapping[str, Any]] = {}
    for candidate in candidates:
        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id or candidate_id in proposals:
            raise ValueError("candidate IDs must be unique non-empty strings")
        proposals[candidate_id] = candidate

    records = validation_audit.get("candidate_validation")
    if not isinstance(records, list):
        raise ValueError("candidate_validation must be a list")
    cap = min(len(records), max_candidates, max_search_attempts)
    started = monotonic()
    deadline = started + float(max_wall_time_seconds) if max_wall_time_seconds is not None else None
    diagnostics: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    attempted_count = 0
    timed_out = False
    for record in records[:cap]:
        if deadline is not None and monotonic() >= deadline:
            timed_out = True
            break
        attempted_count += 1
        candidate_id = record.get("candidate_id")
        expression = record.get("expression")
        try:
            proposal = proposals.get(candidate_id)
            if proposal is None or record.get("validation_status") != "validated":
                raise ValueError("validated candidate has no matching normalized proposal")
            normalized = proposal.get("normalized_expression") or proposal.get("expression")
            if expression != normalized:
                raise ValueError("validation expression does not match normalized proposal")
            parsed = parse_sympy_expression(expression, list(variable_names))
            import sympy as sp
            symbols = [sp.Symbol(name, real=True) for name in variable_names]
            function = sp.lambdify(symbols, parsed, modules="numpy")
            basis = np.asarray(function(*[features[:, i] for i in range(features.shape[1])]), dtype=float)
            if basis.ndim == 0:
                basis = np.full(features.shape[0], float(basis))
            basis = basis.reshape(-1)
            if basis.size != targets.size or not np.all(np.isfinite(basis)):
                raise ValueError("candidate basis predictions are non-finite or misaligned")
            folds = record.get("folds")
            expected = validation_audit.get("fold_count")
            if not isinstance(folds, list) or len(folds) != expected or expected < 2:
                raise ValueError("complete fold evidence is required")
            fold_diagnostics = []
            scales, intercepts = [], []
            seen = set()
            for fold in folds:
                if deadline is not None and monotonic() >= deadline:
                    timed_out = True
                    break
                fold_id = fold.get("fold")
                if isinstance(fold_id, bool) or not isinstance(fold_id, int) or fold_id in seen:
                    raise ValueError("fold identifiers must be unique integers")
                seen.add(fold_id)
                indices = fold.get("validation_row_indices")
                train_indices = fold.get("training_row_indices")
                if not isinstance(indices, list) or not indices or not isinstance(train_indices, list):
                    raise ValueError("fold row-index evidence is missing")
                if any(isinstance(i, bool) or not isinstance(i, int) or i < 0 or i >= targets.size for i in indices + train_indices):
                    raise ValueError("fold row index is outside training arrays")
                if set(indices).intersection(train_indices):
                    raise ValueError("fold training and validation rows overlap")
                coeff = fold.get("coefficients", {})
                scale = _finite(coeff.get("scale"), "fold scale")
                intercept = _finite(coeff.get("intercept"), "fold intercept")
                scales.append(scale)
                intercepts.append(intercept)
                row_idx = np.asarray(indices, dtype=int)
                prediction = basis[row_idx] * scale + intercept
                residual = targets[row_idx] - prediction
                fold_diagnostics.append({
                    "fold": fold_id,
                    "validation_row_indices": list(indices),
                    **_residual_summary(residual, prediction, row_idx),
                })
            if timed_out:
                break
            if seen != set(range(expected)):
                raise ValueError("fold identifiers must be contiguous from zero")
            scale_array, intercept_array = np.asarray(scales), np.asarray(intercepts)
            scale_signs = np.sign(scale_array)
            nonzero_signs = scale_signs[scale_signs != 0]
            diagnostics.append({
                "candidate_id": candidate_id,
                "expression": expression,
                "diagnostic_status": "completed",
                "fold_count": len(fold_diagnostics),
                "folds": fold_diagnostics,
                "coefficient_stability": {
                    "scale_mean": float(np.mean(scale_array)),
                    "scale_std": float(np.std(scale_array)),
                    "scale_cv": float(np.std(scale_array) / abs(np.mean(scale_array))) if np.mean(scale_array) != 0 else None,
                    "intercept_mean": float(np.mean(intercept_array)),
                    "intercept_std": float(np.std(intercept_array)),
                    "scale_sign_consistency": (
                        float(max(np.mean(nonzero_signs > 0), np.mean(nonzero_signs < 0)))
                        if nonzero_signs.size else None
                    ),
                    "scale_sign_flip_count": int(np.sum(scale_signs[1:] * scale_signs[:-1] < 0)),
                },
            })
        except Exception as exc:
            rejected.append({
                "candidate_id": str(candidate_id),
                "diagnostic_status": "rejected",
                "reason": f"{type(exc).__name__}: {exc}",
            })

    return {
        "schema": "v60_native_residual_stability_v1",
        "diagnostic_status": (
            "timed_out" if timed_out else
            ("completed" if attempted_count == len(records) else "budget_limited")
        ),
        "timed_out": timed_out,
        "attempted_candidate_count": attempted_count,
        "input_candidate_count": len(records),
        "diagnosed_candidate_count": len(diagnostics),
        "rejected_candidate_count": len(rejected),
        "budget_truncated_count": len(records) - len(diagnostics) - len(rejected),
        "candidate_diagnostics": diagnostics,
        "rejected_candidates": rejected,
        "diagnostic_scope": "training_only_held_out_fold_residuals_and_fold_local_coefficients",
        "selection_performed": False,
        "far_or_evaluation_data_used": False,
    }


__all__ = ["diagnose_native_training_residuals"]
