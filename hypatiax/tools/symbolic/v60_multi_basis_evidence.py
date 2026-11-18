"""Independent integrity verification for native V60 multi-basis fold evidence.

The verifier reconstructs each fold's joint least-squares fit and held-out
metrics from the supplied training arrays. It does not select or rank groups.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

import numpy as np

from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression


def _canonical_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def verify_native_multi_basis_validation_evidence(
    validation_audit: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
    X_train: Any,
    y_train: Any,
    *,
    variable_names: Sequence[str],
    max_groups: int = 100,
    max_search_attempts: int = 100,
    rtol: float = 1e-8,
    atol: float = 1e-10,
) -> dict[str, Any]:
    """Recompute fold-local joint fits and metrics; fail closed per group."""
    for name, value in (("max_groups", max_groups), ("max_search_attempts", max_search_attempts)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    if not np.isfinite(rtol) or not np.isfinite(atol) or rtol < 0 or atol < 0:
        raise ValueError("comparison tolerances must be finite and non-negative")
    if validation_audit.get("schema") != "v60_native_multi_basis_validation_v1":
        raise ValueError("unsupported multi-basis validation schema")
    if validation_audit.get("selection_performed") is not False:
        raise ValueError("validation audit must explicitly declare selection_performed=false")
    if validation_audit.get("far_or_evaluation_data_used") is not False:
        raise ValueError("validation audit must explicitly exclude far/evaluation data")

    X = np.asarray(X_train, dtype=float)
    y = np.asarray(y_train, dtype=float)
    if X.ndim != 2 or X.shape[1] != len(variable_names):
        raise ValueError("training features must align with variable_names")
    if y.ndim not in (1, 2) or y.size != X.shape[0]:
        raise ValueError("training targets must contain one value per feature row")
    y = y.reshape(-1)
    if not np.all(np.isfinite(X)) or not np.all(np.isfinite(y)):
        raise ValueError("training data must be finite")
    if not isinstance(validation_audit.get("candidate_group_validation"), list):
        raise ValueError("candidate_group_validation must be a list")

    proposal_by_id: dict[str, Mapping[str, Any]] = {}
    for candidate in candidates:
        cid = candidate.get("candidate_id")
        if not isinstance(cid, str) or not cid or cid in proposal_by_id:
            raise ValueError("candidate IDs must be unique non-empty strings")
        proposal_by_id[cid] = candidate

    groups = validation_audit["candidate_group_validation"]
    cap = min(len(groups), max_groups, max_search_attempts)
    verified: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_group_ids: set[str] = set()

    for record in groups[:cap]:
        group_id = record.get("candidate_group_id")
        ids = record.get("basis_candidate_ids")
        expressions = record.get("basis_expressions")
        try:
            if record.get("validation_status") != "validated":
                raise ValueError("only completed validated groups can be verified")
            if not isinstance(group_id, str) or not group_id or group_id in seen_group_ids:
                raise ValueError("candidate group IDs must be unique non-empty strings")
            seen_group_ids.add(group_id)
            if not isinstance(ids, list) or not 2 <= len(ids) <= 3 or len(set(ids)) != len(ids):
                raise ValueError("basis candidate IDs must be a unique list of two or three IDs")
            if not isinstance(expressions, list) or len(expressions) != len(ids):
                raise ValueError("basis expressions must align with basis IDs")
            expected_id = "v60mb_" + sha256(
                json.dumps(ids, separators=(",", ":")).encode("utf-8")
            ).hexdigest()[:20]
            if group_id != expected_id:
                raise ValueError("candidate group ID does not match ordered basis IDs")

            expected_lineage = []
            for cid, expression in zip(ids, expressions):
                candidate = proposal_by_id.get(cid)
                if candidate is None:
                    raise ValueError(f"unknown basis candidate ID: {cid}")
                if (candidate.get("normalized_expression") or candidate.get("expression")) != expression:
                    raise ValueError("basis candidate expression does not match normalized proposal")
                records = candidate.get("producer_provenance", [])
                if not isinstance(records, (list, tuple)):
                    raise ValueError("candidate producer provenance must be a list")
                expected_lineage.extend(dict(item) for item in records if isinstance(item, Mapping))
            if record.get("source_provenance", []) != expected_lineage:
                raise ValueError("producer lineage does not match normalized basis proposals")

            folds = record.get("folds")
            if not isinstance(folds, list) or len(folds) < 2 or record.get("fold_count") != len(folds):
                raise ValueError("fold evidence is incomplete")
            if len(folds) != validation_audit.get("fold_count"):
                raise ValueError("group fold count does not match validation audit")
            if record.get("split_strategy") != validation_audit.get("split_strategy"):
                raise ValueError("group split strategy does not match validation audit")

            import sympy as sp
            symbols = [sp.Symbol(name, real=True) for name in variable_names]
            basis_columns = []
            for expression in expressions:
                parsed = parse_sympy_expression(expression, list(variable_names))
                fn = sp.lambdify(symbols, parsed, modules="numpy")
                values = np.asarray(fn(*[X[:, j] for j in range(X.shape[1])]), dtype=float)
                if values.ndim == 0:
                    values = np.full(X.shape[0], float(values))
                values = values.reshape(-1)
                if values.size != y.size or not np.all(np.isfinite(values)):
                    raise ValueError("basis expression produced invalid training values")
                basis_columns.append(values)

            validation_seen: list[int] = []
            verified_folds = []
            for expected_fold_index, fold in enumerate(folds):
                if fold.get("fold") != expected_fold_index:
                    raise ValueError("fold IDs must be contiguous and ordered")
                raw_train_idx = fold.get("training_row_indices")
                raw_valid_idx = fold.get("validation_row_indices")
                if not isinstance(raw_train_idx, list) or not isinstance(raw_valid_idx, list):
                    raise ValueError("fold row indices must be lists of integers")
                if any(isinstance(index, bool) or not isinstance(index, int) for index in raw_train_idx + raw_valid_idx):
                    raise ValueError("fold row indices must be integers, not booleans or floats")
                train_idx = np.asarray(raw_train_idx, dtype=int)
                valid_idx = np.asarray(raw_valid_idx, dtype=int)
                if train_idx.ndim != 1 or valid_idx.ndim != 1 or not train_idx.size or not valid_idx.size:
                    raise ValueError("fold row indices must be non-empty one-dimensional lists")
                if len(set(train_idx.tolist())) != train_idx.size or len(set(valid_idx.tolist())) != valid_idx.size:
                    raise ValueError("fold row indices must be unique")
                if np.any(train_idx < 0) or np.any(valid_idx < 0) or np.any(train_idx >= len(y)) or np.any(valid_idx >= len(y)):
                    raise ValueError("fold row index is outside the supplied training arrays")
                if set(train_idx.tolist()).intersection(valid_idx.tolist()):
                    raise ValueError("fold training and validation rows overlap")
                if fold.get("training_row_count") != int(train_idx.size) or fold.get("validation_row_count") != int(valid_idx.size):
                    raise ValueError("fold row counts do not match row-index evidence")
                validation_seen.extend(valid_idx.tolist())

                train_design = np.column_stack([column[train_idx] for column in basis_columns] + [np.ones(train_idx.size)])
                valid_design = np.column_stack([column[valid_idx] for column in basis_columns] + [np.ones(valid_idx.size)])
                coefficients, _, rank, singular = np.linalg.lstsq(train_design, y[train_idx], rcond=None)
                predictions = valid_design @ coefficients
                residual = y[valid_idx] - predictions
                rmse = float(np.sqrt(np.mean(np.square(residual))))
                train_std = float(np.std(y[train_idx]))
                valid_var = float(np.sum(np.square(y[valid_idx] - np.mean(y[valid_idx]))))
                nrmse = rmse / train_std if train_std > 0 else None
                r2 = 1.0 - float(np.sum(np.square(residual))) / valid_var if valid_var > 0 else None
                supplied_coeff = fold.get("coefficients", {})
                supplied_vector = np.asarray(
                    list(supplied_coeff.get("basis", [])) + [supplied_coeff.get("intercept")],
                    dtype=float,
                )
                if supplied_vector.shape != coefficients.shape or not np.allclose(supplied_vector, coefficients, rtol=rtol, atol=atol):
                    raise ValueError(f"fold {expected_fold_index} coefficients do not reproduce")
                for key, actual in (("validation_rmse", rmse), ("validation_nrmse", nrmse), ("validation_r2", r2)):
                    supplied = fold.get(key)
                    if actual is None:
                        if supplied is not None:
                            raise ValueError(f"fold {expected_fold_index} {key} nullability mismatch")
                    elif supplied is None or not np.isclose(float(supplied), actual, rtol=rtol, atol=atol):
                        raise ValueError(f"fold {expected_fold_index} {key} does not reproduce")
                if fold.get("training_rank") != int(rank):
                    raise ValueError(f"fold {expected_fold_index} design rank does not reproduce")
                condition = float(singular[0] / singular[-1]) if len(singular) and singular[-1] > 0 else None
                supplied_condition = fold.get("design_condition_number")
                if condition is None:
                    if supplied_condition is not None:
                        raise ValueError("fold condition-number nullability mismatch")
                elif supplied_condition is None or not np.isclose(float(supplied_condition), condition, rtol=rtol, atol=atol):
                    raise ValueError(f"fold {expected_fold_index} condition number does not reproduce")
                verified_folds.append({
                    "fold": expected_fold_index,
                    "training_row_indices": train_idx.tolist(),
                    "validation_row_indices": valid_idx.tolist(),
                    "recomputed_rmse": rmse,
                    "recomputed_nrmse": nrmse,
                    "recomputed_r2": r2,
                    "recomputed_coefficients": [float(v) for v in coefficients],
                    "recomputed_rank": int(rank),
                    "recomputed_condition_number": condition,
                })

            if len(set(validation_seen)) != len(validation_seen):
                raise ValueError("validation rows are repeated across folds")
            rmse_values = [item["recomputed_rmse"] for item in verified_folds]
            nrmse_values = [item["recomputed_nrmse"] for item in verified_folds]
            aggregate_values = {
                "validation_rmse_mean": float(np.mean(rmse_values)),
                "validation_rmse_std": float(np.std(rmse_values)),
                "validation_nrmse_mean": float(np.mean(nrmse_values)) if all(v is not None for v in nrmse_values) else None,
                "validation_nrmse_std": float(np.std(nrmse_values)) if all(v is not None for v in nrmse_values) else None,
            }
            for key, actual in aggregate_values.items():
                supplied = record.get(key)
                if actual is None:
                    if supplied is not None:
                        raise ValueError(f"{key} nullability mismatch")
                elif supplied is None or not np.isclose(float(supplied), actual, rtol=rtol, atol=atol):
                    raise ValueError(f"{key} does not reproduce")
            evidence_payload = {
                "candidate_group_id": group_id,
                "basis_candidate_ids": ids,
                "basis_expressions": expressions,
                "source_provenance": expected_lineage,
                "folds": verified_folds,
                "aggregates": aggregate_values,
                "training_row_count": int(len(y)),
                "variable_names": list(variable_names),
                "split_strategy": record.get("split_strategy"),
            }
            verified.append({
                "candidate_group_id": group_id,
                "basis_candidate_ids": list(ids),
                "basis_expressions": list(expressions),
                "source_provenance": expected_lineage,
                "verified_fold_count": len(verified_folds),
                "objective_evidence": aggregate_values,
                "verified_folds": verified_folds,
                "evidence_fingerprint": _canonical_digest(evidence_payload),
                "verification_status": "verified",
            })
        except Exception as exc:
            rejected.append({
                "candidate_group_id": group_id,
                "verification_status": "rejected",
                "reason": f"{type(exc).__name__}: {exc}",
            })

    return {
        "schema": "v60_native_multi_basis_evidence_verification_v1",
        "verification_status": "completed" if not rejected and len(verified) == len(groups) else "partial_or_rejected",
        "input_group_count": len(groups),
        "attempted_group_count": min(len(groups), max_groups, max_search_attempts),
        "verified_group_count": len(verified),
        "rejected_group_count": len(rejected),
        "budget_truncated_count": len(groups) - min(len(groups), max_groups, max_search_attempts),
        "selection_performed": False,
        "far_or_evaluation_data_used": False,
        "verified_candidate_groups": verified,
        "rejected_candidate_groups": rejected,
    }


__all__ = ["verify_native_multi_basis_validation_evidence"]
