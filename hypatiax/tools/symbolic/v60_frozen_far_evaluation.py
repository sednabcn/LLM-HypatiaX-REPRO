"""Frozen post-selection far-set evaluation for the native V60 candidate path.

This module is deliberately separate from discovery, validation, diagnostics,
and selection. It accepts a completed training-only selection audit, refits
only the already-selected expression on all training rows, and evaluates that
frozen candidate once against caller-supplied far observations. Its output is
an endpoint: it cannot revise selection or feed metrics back into search.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

import numpy as np

from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression


def _array(value: Any, label: str, *, width: int | None = None) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.ndim != 2 or (width is not None and result.shape[1] != width):
        raise ValueError(f"{label} must be a 2-D array aligned with variable_names")
    if result.shape[0] == 0 or not np.all(np.isfinite(result)):
        raise ValueError(f"{label} must contain non-empty finite rows")
    return result


def _targets(value: Any, rows: int, label: str) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.ndim not in (1, 2) or result.size != rows:
        raise ValueError(f"{label} must contain exactly one target per feature row")
    result = result.reshape(-1)
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{label} must contain only finite values")
    return result


def _selection_snapshot(selection_audit: Mapping[str, Any]) -> str:
    evidence = selection_audit.get("objective_evidence")
    selected_id = selection_audit.get("selected_candidate_id")
    selected_expression = selection_audit.get("selected_expression")
    selected_hash = selection_audit.get("selected_objective_evidence_sha256")
    if not isinstance(evidence, list):
        raise ValueError("selection audit objective_evidence must be a list")
    selected = [item for item in evidence if isinstance(item, Mapping) and item.get("candidate_id") == selected_id]
    if len(selected) != 1:
        raise ValueError("selection audit must contain exactly one objective record for the selected candidate")
    if selected[0].get("expression") != selected_expression:
        raise ValueError("selected expression does not match frozen objective evidence")
    if selected[0].get("objective_evidence_sha256") != selected_hash:
        raise ValueError("selected objective fingerprint does not match its evidence")
    objective_payload = dict(selected[0])
    objective_payload.pop("objective_evidence_sha256", None)
    objective_canonical = json.dumps(objective_payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if sha256(objective_canonical.encode("utf-8")).hexdigest() != selected_hash:
        raise ValueError("selected objective evidence fingerprint verification failed")
    payload = {
        "schema": selection_audit.get("schema"),
        "selection_status": selection_audit.get("selection_status"),
        "selected_candidate_id": selected_id,
        "selected_expression": selected_expression,
        "selected_objective_evidence_sha256": selected_hash,
        "pareto_candidate_ids": selection_audit.get("pareto_candidate_ids"),
        "objective_evidence": evidence,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(canonical.encode("utf-8")).hexdigest()


def evaluate_selected_native_candidate_on_far_set(
    selection_audit: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
    X_train: Any,
    y_train: Any,
    X_far: Any,
    y_far: Any,
    *,
    variable_names: Sequence[str],
) -> dict[str, Any]:
    """Evaluate exactly the frozen training-selected candidate on a far set.

    The function has no selector, retry, or candidate-ranking callback. It
    verifies the selected identity, refits its affine coefficients on the
    complete training set, then reports far metrics without changing the
    selection audit. Far targets are read only after the selection snapshot
    has been fingerprinted.
    """
    if not isinstance(selection_audit, Mapping):
        raise TypeError("selection_audit must be a mapping")
    if selection_audit.get("schema") != "v60_native_objective_selection_v1":
        raise ValueError("unsupported selection audit schema")
    if selection_audit.get("selection_status") != "selected" or selection_audit.get("selection_performed") is not True:
        raise ValueError("a completed selected-candidate audit is required")
    if selection_audit.get("far_or_evaluation_data_used") is not False:
        raise ValueError("selection audit must certify that far/evaluation data was not used")

    selected_id = selection_audit.get("selected_candidate_id")
    expression = selection_audit.get("selected_expression")
    if not isinstance(selected_id, str) or not selected_id or not isinstance(expression, str) or not expression:
        raise ValueError("selection audit has no valid selected candidate identity")
    selection_fingerprint = _selection_snapshot(selection_audit)

    matches = [item for item in candidates if item.get("candidate_id") == selected_id]
    if len(matches) != 1:
        raise ValueError("candidate pool must contain exactly one selected candidate")
    candidate = matches[0]
    candidate_expression = candidate.get("normalized_expression") or candidate.get("expression")
    if candidate_expression != expression:
        raise ValueError("candidate expression does not match frozen selection")

    names = tuple(variable_names)
    if not names or len(set(names)) != len(names) or any(not isinstance(name, str) or not name for name in names):
        raise ValueError("variable_names must be unique non-empty strings")
    train = _array(X_train, "X_train", width=len(names))
    train_y = _targets(y_train, train.shape[0], "y_train")
    far = _array(X_far, "X_far", width=len(names))
    far_y = _targets(y_far, far.shape[0], "y_far")

    import sympy as sp
    parsed = parse_sympy_expression(expression, list(names))
    symbols = [sp.Symbol(name, real=True) for name in names]
    function = sp.lambdify(symbols, parsed, modules="numpy")

    def predict(features: np.ndarray) -> np.ndarray:
        values = np.asarray(function(*[features[:, index] for index in range(features.shape[1])]), dtype=np.float64)
        if values.ndim == 0:
            values = np.full(features.shape[0], float(values), dtype=np.float64)
        values = values.reshape(-1)
        if values.size != features.shape[0] or not np.all(np.isfinite(values)):
            raise ValueError("selected expression produced non-finite or misaligned predictions")
        return values

    train_basis = predict(train)
    design = np.column_stack((train_basis, np.ones(train_basis.size, dtype=np.float64)))
    coefficients, _, rank, _ = np.linalg.lstsq(design, train_y, rcond=None)
    if not np.all(np.isfinite(coefficients)):
        raise ValueError("training refit produced non-finite coefficients")
    far_prediction = predict(far) * coefficients[0] + coefficients[1]
    if not np.all(np.isfinite(far_prediction)):
        raise ValueError("far predictions are non-finite")
    residual = far_y - far_prediction
    rmse = float(np.sqrt(np.mean(np.square(residual))))
    train_std = float(np.std(train_y))
    far_var = float(np.sum(np.square(far_y - np.mean(far_y))))
    far_r2 = 1.0 - float(np.sum(np.square(residual))) / far_var if far_var > 0 else None

    far_digest = sha256()
    for array in (far, far_y):
        contiguous = np.ascontiguousarray(array, dtype=np.float64)
        far_digest.update(json.dumps(list(contiguous.shape)).encode("ascii"))
        far_digest.update(contiguous.tobytes())

    return {
        "schema": "v60_native_frozen_far_evaluation_v1",
        "evaluation_status": "completed",
        "evaluation_scope": "single_frozen_selected_candidate",
        "selected_candidate_id": selected_id,
        "selected_expression": expression,
        "selection_snapshot_sha256": selection_fingerprint,
        "far_set_sha256": far_digest.hexdigest(),
        "training_refit": {
            "method": "affine_least_squares_on_all_training_rows",
            "training_row_count": int(train.shape[0]),
            "rank": int(rank),
            "coefficients": {"scale": float(coefficients[0]), "intercept": float(coefficients[1])},
        },
        "far_metrics": {
            "far_row_count": int(far.shape[0]),
            "rmse": rmse,
            "nrmse_by_training_target_std": rmse / train_std if train_std > 0 else None,
            "mae": float(np.mean(np.abs(residual))),
            "bias": float(np.mean(residual)),
            "r2": far_r2,
        },
        "selection_changed": False,
        "selection_performed": False,
        "far_or_evaluation_data_used_for_selection": False,
        "far_or_evaluation_data_used_for_retry": False,
        "candidate_ranking_performed": False,
    }


__all__ = ["evaluate_selected_native_candidate_on_far_set"]
