"""Bounded fold validation for native V60 joint multi-basis candidate groups.

Each group is independently refitted on each training fold. This stage emits
training-only evidence and never ranks or selects groups.
"""
from __future__ import annotations

from hashlib import sha256
from itertools import combinations
import json
from time import monotonic
from typing import Any, Mapping, Sequence

import numpy as np

from hypatiax.tools.symbolic.v60_training_validation import _fold_indices
from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression


def validate_native_multi_basis_candidates(
    fitted_groups: Sequence[Mapping[str, Any]],
    candidates: Sequence[Mapping[str, Any]],
    X: Any,
    y: Any,
    *,
    variable_names: Sequence[str],
    split_protocol: Mapping[str, Any] | None = None,
    seed: int = 42,
    max_candidates: int = 100,
    max_search_attempts: int = 100,
    max_wall_time_seconds: float | None = None,
) -> dict[str, Any]:
    """Refit bounded fitted groups jointly within each training-only fold."""
    for name, value in (
        ("max_candidates", max_candidates),
        ("max_search_attempts", max_search_attempts),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    if max_wall_time_seconds is not None and (
        isinstance(max_wall_time_seconds, bool)
        or not isinstance(max_wall_time_seconds, (int, float))
        or not np.isfinite(max_wall_time_seconds)
        or max_wall_time_seconds <= 0
    ):
        raise ValueError("max_wall_time_seconds must be finite and > 0 or None")

    features = np.asarray(X, dtype=float)
    targets = np.asarray(y, dtype=float)
    if features.ndim != 2 or features.shape[1] != len(variable_names):
        raise ValueError("training features must be 2-D and align with variable_names")
    if targets.ndim not in (1, 2) or targets.size != features.shape[0]:
        raise ValueError("training targets must contain one value per feature row")
    targets = targets.reshape(-1)
    if not np.all(np.isfinite(features)) or not np.all(np.isfinite(targets)):
        raise ValueError("training data must be finite; rows are never silently excluded")
    if features.shape[0] < 3:
        return {
            "schema": "v60_native_multi_basis_validation_v1",
            "validation_status": "insufficient_rows",
            "reason": "at least three training rows are required",
            "input_group_count": len(fitted_groups),
            "validated_group_count": 0,
            "rejected_group_count": 0,
            "fold_count": 0,
            "selection_performed": False,
            "far_or_evaluation_data_used": False,
            "candidate_group_validation": [],
            "rejected_candidate_groups": [],
        }

    protocol = dict(split_protocol or {})
    raw_folds = protocol.get("n_splits", protocol.get("folds", 5))
    if isinstance(raw_folds, bool) or not isinstance(raw_folds, int):
        raise ValueError("split_protocol n_splits must be an integer")
    fold_count = min(raw_folds, 10, features.shape[0] - 1)
    if fold_count < 2:
        raise ValueError("split_protocol n_splits must be >= 2")
    strategy = protocol.get("strategy", "kfold")
    if strategy not in {"kfold", "blocked_kfold", "time_series"}:
        raise ValueError("unsupported split_protocol strategy")
    if strategy == "time_series" and features.shape[0] - max(2, features.shape[0] // (fold_count + 1)) < fold_count:
        raise ValueError("insufficient rows for requested time_series folds")

    proposal_by_id: dict[str, str] = {}
    for proposal in candidates:
        candidate_id = proposal.get("candidate_id")
        expression = proposal.get("normalized_expression") or proposal.get("expression")
        if not isinstance(candidate_id, str) or not candidate_id or candidate_id in proposal_by_id:
            raise ValueError("normalized candidate IDs must be unique non-empty strings")
        if not isinstance(expression, str) or not expression.strip():
            raise ValueError("normalized candidate expressions must be non-empty strings")
        proposal_by_id[candidate_id] = expression

    cap = min(len(fitted_groups), max_candidates, max_search_attempts)
    started = monotonic()
    folds = list(_fold_indices(features.shape[0], fold_count, strategy, seed))
    validated: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    attempted = 0
    timed_out = False
    seen_group_ids: set[str] = set()

    for group in fitted_groups[:cap]:
        if max_wall_time_seconds is not None and monotonic() - started >= max_wall_time_seconds:
            timed_out = True
            break
        attempted += 1
        group_id = group.get("candidate_group_id")
        ids = group.get("basis_candidate_ids")
        expressions = group.get("basis_expressions")
        try:
            if group.get("fit_status") != "fitted":
                raise ValueError("only successfully fitted candidate groups can be validated")
            if not isinstance(group_id, str) or not group_id or group_id in seen_group_ids:
                raise ValueError("candidate group IDs must be unique non-empty strings")
            seen_group_ids.add(group_id)
            if not isinstance(ids, list) or not 2 <= len(ids) <= 3 or len(set(ids)) != len(ids):
                raise ValueError("basis candidate IDs must be a unique list of two or three IDs")
            if not isinstance(expressions, list) or len(expressions) != len(ids):
                raise ValueError("basis expressions must align with basis candidate IDs")
            expected_group_id = "v60mb_" + sha256(
                json.dumps(ids, separators=(",", ":")).encode("utf-8")
            ).hexdigest()[:20]
            if group_id != expected_group_id:
                raise ValueError("candidate group ID does not match its ordered basis IDs")
            if any(proposal_by_id.get(cid) != expr for cid, expr in zip(ids, expressions)):
                raise ValueError("basis candidate ID/expression lineage does not match normalized proposals")
            expected_lineage = [
                dict(record)
                for candidate in candidates if candidate.get("candidate_id") in ids
                for record in candidate.get("producer_provenance", [])
                if isinstance(record, Mapping)
            ]
            supplied_lineage = group.get("source_provenance", [])
            if supplied_lineage != expected_lineage:
                raise ValueError("candidate group producer lineage does not match normalized proposals")

            import sympy as sp
            symbols = [sp.Symbol(name, real=True) for name in variable_names]
            basis_values = []
            for expression in expressions:
                parsed = parse_sympy_expression(expression, list(variable_names))
                function = sp.lambdify(symbols, parsed, modules="numpy")
                values = np.asarray(
                    function(*[features[:, column] for column in range(features.shape[1])]),
                    dtype=float,
                )
                if values.ndim == 0:
                    values = np.full(features.shape[0], float(values))
                values = values.reshape(-1)
                if values.size != targets.size or not np.all(np.isfinite(values)):
                    raise ValueError(f"basis {expression!r} produced invalid training values")
                basis_values.append(values)

            fold_records = []
            for fold_index, (train_idx, validation_idx) in enumerate(folds):
                if max_wall_time_seconds is not None and monotonic() - started >= max_wall_time_seconds:
                    timed_out = True
                    break
                if train_idx.size < len(ids) + 1 or validation_idx.size == 0:
                    raise ValueError("fold has insufficient rows for joint basis refit")
                train_design = np.column_stack(
                    [values[train_idx] for values in basis_values] + [np.ones(train_idx.size)]
                )
                validation_design = np.column_stack(
                    [values[validation_idx] for values in basis_values] + [np.ones(validation_idx.size)]
                )
                coefficients, _, rank, singular_values = np.linalg.lstsq(
                    train_design, targets[train_idx], rcond=None
                )
                if not np.all(np.isfinite(coefficients)):
                    raise ValueError("fold joint fit produced non-finite coefficients")
                predictions = validation_design @ coefficients
                if not np.all(np.isfinite(predictions)):
                    raise ValueError("fold joint fit produced non-finite validation predictions")
                residual = targets[validation_idx] - predictions
                rmse = float(np.sqrt(np.mean(np.square(residual))))
                train_std = float(np.std(targets[train_idx]))
                validation_mean = float(np.mean(targets[validation_idx]))
                validation_var = float(np.sum(np.square(targets[validation_idx] - validation_mean)))
                fold_records.append({
                    "fold": fold_index,
                    "training_row_indices": [int(index) for index in train_idx],
                    "validation_row_indices": [int(index) for index in validation_idx],
                    "training_row_count": int(train_idx.size),
                    "validation_row_count": int(validation_idx.size),
                    "validation_rmse": rmse,
                    "validation_nrmse": rmse / train_std if train_std > 0 else None,
                    "validation_r2": (
                        1.0 - float(np.sum(np.square(residual))) / validation_var
                        if validation_var > 0 else None
                    ),
                    "training_rank": int(rank),
                    "coefficients": {
                        "basis": [float(value) for value in coefficients[:-1]],
                        "intercept": float(coefficients[-1]),
                    },
                    "design_condition_number": (
                        float(singular_values[0] / singular_values[-1])
                        if len(singular_values) and singular_values[-1] > 0 else None
                    ),
                })
            if timed_out and len(fold_records) != len(folds):
                break

            rmse_values = [record["validation_rmse"] for record in fold_records]
            nrmse_values = [record["validation_nrmse"] for record in fold_records]
            validated.append({
                "candidate_group_id": group_id,
                "basis_candidate_ids": list(ids),
                "basis_expressions": list(expressions),
                "source_provenance": list(group.get("source_provenance", [])),
                "validation_status": "validated",
                "validation_method": "training_only_joint_multi_basis_refit_cross_validation",
                "split_strategy": strategy,
                "fold_count": len(fold_records),
                "folds": fold_records,
                "validation_rmse_mean": float(np.mean(rmse_values)),
                "validation_rmse_std": float(np.std(rmse_values)),
                "validation_nrmse_mean": (
                    float(np.mean(nrmse_values))
                    if all(value is not None for value in nrmse_values) else None
                ),
                "validation_nrmse_std": (
                    float(np.std(nrmse_values))
                    if all(value is not None for value in nrmse_values) else None
                ),
            })
        except Exception as exc:
            rejected.append({
                "candidate_group_id": group_id,
                "basis_candidate_ids": list(ids) if isinstance(ids, list) else [],
                "basis_expressions": list(expressions) if isinstance(expressions, list) else [],
                "validation_status": "rejected",
                "reason": f"{type(exc).__name__}: {exc}",
            })

    return {
        "schema": "v60_native_multi_basis_validation_v1",
        "validation_status": (
            "timed_out" if timed_out else
            ("completed" if attempted == len(fitted_groups) else "budget_limited")
        ),
        "input_group_count": len(fitted_groups),
        "attempted_group_count": attempted,
        "validated_group_count": len(validated),
        "rejected_group_count": len(rejected),
        "budget_truncated_count": len(fitted_groups) - attempted,
        "timed_out": timed_out,
        "fold_count": fold_count,
        "split_strategy": strategy,
        "seed": seed,
        "training_row_count": int(features.shape[0]),
        "validation_method": "training_only_joint_multi_basis_refit_cross_validation",
        "selection_performed": False,
        "far_or_evaluation_data_used": False,
        "candidate_group_validation": validated,
        "rejected_candidate_groups": rejected,
    }


__all__ = ["validate_native_multi_basis_candidates"]
