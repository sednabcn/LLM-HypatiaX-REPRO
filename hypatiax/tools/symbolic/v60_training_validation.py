"""Native V60 bounded cross-validation using training observations only.

Each fold refits the candidate's affine coefficients on that fold's training
partition and scores only its held-in validation partition. No far/evaluation
arrays are accepted by this interface and this stage never ranks or selects.
"""
from __future__ import annotations

from time import monotonic
from typing import Any, Mapping, Sequence

import numpy as np

from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression


def _fold_indices(row_count: int, fold_count: int, strategy: str, seed: int):
    indices = np.arange(row_count)
    if strategy == "kfold":
        indices = np.random.RandomState(seed).permutation(indices)
        partitions = np.array_split(indices, fold_count)
        for fold_index, validation in enumerate(partitions):
            training = np.concatenate([part for i, part in enumerate(partitions) if i != fold_index])
            yield training, validation
        return
    if strategy == "blocked_kfold":
        partitions = np.array_split(indices, fold_count)
        for fold_index, validation in enumerate(partitions):
            training = np.concatenate([part for i, part in enumerate(partitions) if i != fold_index])
            yield training, validation
        return
    if strategy == "time_series":
        initial = max(2, row_count // (fold_count + 1))
        remaining = indices[initial:]
        for validation in np.array_split(remaining, fold_count):
            if validation.size:
                yield indices[:int(validation[0])], validation
        return
    raise ValueError("split_protocol.strategy must be kfold, blocked_kfold, or time_series")


def validate_native_training_candidates(
    candidates: Sequence[Mapping[str, Any]], X: Any, y: Any, *,
    variable_names: Sequence[str], eligible_candidate_ids: Sequence[str],
    split_protocol: Mapping[str, Any] | None = None,
    seed: int = 42, max_candidates: int = 100,
    max_search_attempts: int = 100,
    max_wall_time_seconds: float | None = None,
) -> dict[str, Any]:
    """Produce bounded fold evidence; eligibility is supplied by native gates."""
    if isinstance(max_candidates, bool) or not isinstance(max_candidates, int) or max_candidates < 0:
        raise ValueError("max_candidates must be a non-negative integer")
    if isinstance(max_search_attempts, bool) or not isinstance(max_search_attempts, int) or max_search_attempts < 0:
        raise ValueError("max_search_attempts must be a non-negative integer")
    if max_wall_time_seconds is not None and max_wall_time_seconds <= 0:
        raise ValueError("max_wall_time_seconds must be > 0 or None")

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
            "schema": "v60_native_training_validation_v1",
            "validation_status": "insufficient_rows", "reason": "at least three training rows are required",
            "candidate_count": 0, "validated_candidate_count": 0,
            "fold_count": 0, "selection_performed": False,
            "far_or_evaluation_data_used": False, "candidate_validation": [],
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

    eligible = set(eligible_candidate_ids)
    pool = [item for item in candidates if item.get("candidate_id") in eligible]
    input_count = len(pool)
    cap = min(input_count, max_candidates, max_search_attempts)
    started = monotonic()
    results: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    timed_out = False
    function_cache: dict[str, Any] = {}
    folds = list(_fold_indices(features.shape[0], fold_count, strategy, seed))

    for candidate in pool[:cap]:
        if max_wall_time_seconds is not None and monotonic() - started >= max_wall_time_seconds:
            timed_out = True
            break
        candidate_id = candidate.get("candidate_id")
        expression = candidate.get("normalized_expression") or candidate.get("expression")
        lineage = candidate.get("producer_provenance", [])
        try:
            if not isinstance(candidate_id, str) or not candidate_id:
                raise ValueError("candidate_id must be non-empty")
            if not isinstance(expression, str) or not expression.strip():
                raise ValueError("candidate expression must be non-empty")
            if expression not in function_cache:
                import sympy as sp
                parsed = parse_sympy_expression(expression, list(variable_names))
                symbols = [sp.Symbol(name, real=True) for name in variable_names]
                function_cache[expression] = sp.lambdify(symbols, parsed, modules="numpy")
            function = function_cache[expression]
            basis = np.asarray(function(*[features[:, i] for i in range(features.shape[1])]), dtype=float)
            if basis.ndim == 0:
                basis = np.full(features.shape[0], float(basis))
            basis = basis.reshape(-1)
            if basis.size != targets.size or not np.all(np.isfinite(basis)):
                raise ValueError("candidate produced non-finite or misaligned predictions")

            fold_records = []
            for fold_index, (train_idx, validation_idx) in enumerate(folds):
                if max_wall_time_seconds is not None and monotonic() - started >= max_wall_time_seconds:
                    timed_out = True
                    break
                if train_idx.size < 2 or validation_idx.size == 0:
                    raise ValueError("fold has insufficient training or validation rows")
                train_basis, validation_basis = basis[train_idx], basis[validation_idx]
                design_train = np.column_stack((train_basis, np.ones(train_idx.size)))
                coefficients, _, rank, _ = np.linalg.lstsq(design_train, targets[train_idx], rcond=None)
                predictions = validation_basis * coefficients[0] + coefficients[1]
                residual = targets[validation_idx] - predictions
                rmse = float(np.sqrt(np.mean(np.square(residual))))
                train_std = float(np.std(targets[train_idx]))
                validation_mean = float(np.mean(targets[validation_idx]))
                validation_var = float(np.sum(np.square(targets[validation_idx] - validation_mean)))
                validation_r2 = (
                    1.0 - float(np.sum(np.square(residual))) / validation_var
                    if validation_var > 0 else None
                )
                fold_records.append({
                    "fold": fold_index, "training_row_count": int(train_idx.size),
                    "validation_row_count": int(validation_idx.size),
                    "validation_rmse": rmse,
                    "validation_nrmse": rmse / train_std if train_std > 0 else None,
                    "validation_r2": validation_r2, "training_rank": int(rank),
                    "coefficients": {"scale": float(coefficients[0]), "intercept": float(coefficients[1])},
                })
            if timed_out and len(fold_records) != len(folds):
                break
            rmse_values = [record["validation_rmse"] for record in fold_records]
            nrmse_values = [record["validation_nrmse"] for record in fold_records if record["validation_nrmse"] is not None]
            results.append({
                "candidate_id": candidate_id, "expression": expression,
                "source_provenance": [dict(item) for item in lineage if isinstance(item, Mapping)],
                "validation_status": "validated", "validation_method": "training_only_refit_cross_validation",
                "split_strategy": strategy, "fold_count": len(fold_records),
                "folds": fold_records,
                "validation_rmse_mean": float(np.mean(rmse_values)),
                "validation_rmse_std": float(np.std(rmse_values)),
                "validation_nrmse_mean": float(np.mean(nrmse_values)) if nrmse_values else None,
                "validation_nrmse_std": float(np.std(nrmse_values)) if nrmse_values else None,
                "validation_r2_mean": float(np.mean([r["validation_r2"] for r in fold_records if r["validation_r2"] is not None])) if any(r["validation_r2"] is not None for r in fold_records) else None,
            })
        except Exception as exc:
            rejected.append({
                "candidate_id": candidate_id, "expression": expression,
                "validation_status": "rejected", "reason": f"{type(exc).__name__}: {exc}",
                "source_provenance": [dict(item) for item in lineage if isinstance(item, Mapping)],
            })

    completed = len(results) + len(rejected)
    return {
        "schema": "v60_native_training_validation_v1",
        "validation_status": "timed_out" if timed_out else ("completed" if completed == input_count else "budget_limited"),
        "input_eligible_candidate_count": input_count,
        "validated_candidate_count": len(results), "rejected_candidate_count": len(rejected),
        "validation_attempt_count": completed, "budget_truncated_count": input_count - completed,
        "timed_out": timed_out, "fold_count": fold_count, "split_strategy": strategy,
        "seed": seed, "training_row_count": int(features.shape[0]),
        "validation_method": "training_only_refit_cross_validation",
        "selection_performed": False, "far_or_evaluation_data_used": False,
        "candidate_validation": results, "rejected_candidates": rejected,
    }


__all__ = ["validate_native_training_candidates"]
