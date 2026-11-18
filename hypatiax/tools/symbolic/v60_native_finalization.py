"""Native V60 final model refit from independently selected training evidence.

This stage compares only the already-selected single- and joint-basis Pareto
winners using the same declared cross-validation error scale, then refits the
chosen symbolic basis (or bases) on all training rows. It accepts no far-set
data and does not call an LLM or PySR provider.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
from typing import Any, Mapping, Sequence

import numpy as np
import sympy as sp

from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression


def _finite(value: Any, label: str, *, nullable: bool = False) -> float | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def _selected_record(audit: Mapping[str, Any], id_key: str, records_key: str, record_id_key: str):
    selected_id = audit.get(id_key)
    if audit.get("selection_status") != "selected" or not isinstance(selected_id, str):
        return None
    records = audit.get(records_key)
    if not isinstance(records, list):
        raise ValueError(f"{records_key} must be a list")
    matches = [item for item in records if isinstance(item, Mapping) and item.get(record_id_key) == selected_id]
    if len(matches) != 1:
        raise ValueError("selected candidate must resolve to exactly one objective evidence record")
    return matches[0]


def finalize_native_v60_model(
    candidates: Sequence[Mapping[str, Any]],
    single_selection: Mapping[str, Any],
    multi_selection: Mapping[str, Any],
    X_train: Any,
    y_train: Any,
    *,
    variable_names: Sequence[str],
) -> dict[str, Any]:
    """Choose between verified family winners and refit the winner on training rows.

    Cross-family comparison uses CV NRMSE only when both family winners have it;
    otherwise it uses CV RMSE for both. Fold variability, symbolic complexity,
    and family name provide deterministic tie-breaks. The final coefficients
    are refitted on all training rows and are never scored on far/evaluation data.
    """
    X = np.asarray(X_train, dtype=float)
    y = np.asarray(y_train, dtype=float).reshape(-1)
    names = tuple(variable_names)
    if X.ndim != 2 or X.shape[1] != len(names) or X.shape[0] != y.size or not y.size:
        raise ValueError("training arrays must be aligned with the declared variable names")
    if not np.all(np.isfinite(X)) or not np.all(np.isfinite(y)):
        raise ValueError("training arrays must be finite; row dropping is forbidden")

    by_id = {}
    for candidate in candidates:
        cid = candidate.get("candidate_id")
        expr = candidate.get("normalized_expression") or candidate.get("expression")
        if not isinstance(cid, str) or not cid or cid in by_id or not isinstance(expr, str):
            raise ValueError("normalized candidate IDs and expressions must be unique and valid")
        by_id[cid] = candidate

    options: list[dict[str, Any]] = []
    single = _selected_record(single_selection, "selected_candidate_id", "objective_evidence", "candidate_id")
    if single is not None:
        cid = single["candidate_id"]
        proposal = by_id.get(cid)
        if proposal is None or single.get("expression") != (proposal.get("normalized_expression") or proposal.get("expression")):
            raise ValueError("single-basis selected evidence does not match its normalized proposal")
        options.append({
            "family": "single_basis", "candidate_id": cid,
            "expressions": [single["expression"]],
            "cv_rmse": _finite(single.get("mean_validation_rmse"), "single CV RMSE"),
            "cv_nrmse": _finite(single.get("mean_validation_nrmse"), "single CV NRMSE", nullable=True),
            "cv_rmse_std": _finite(single.get("std_validation_rmse"), "single CV RMSE std"),
            "cv_nrmse_std": _finite(single.get("std_validation_nrmse"), "single CV NRMSE std", nullable=True),
            "complexity": int(single.get("complexity", 0)),
        })

    multi = _selected_record(multi_selection, "selected_candidate_group_id", "objective_evidence", "candidate_group_id")
    if multi is not None:
        ids = multi.get("basis_candidate_ids")
        expressions = multi.get("basis_expressions")
        if not isinstance(ids, list) or not isinstance(expressions, list) or len(ids) != len(expressions) or not 2 <= len(ids) <= 3:
            raise ValueError("multi-basis winner must contain two or three aligned bases")
        for cid, expr in zip(ids, expressions):
            proposal = by_id.get(cid)
            if proposal is None or expr != (proposal.get("normalized_expression") or proposal.get("expression")):
                raise ValueError("multi-basis selected evidence does not match normalized candidate lineage")
        options.append({
            "family": "multi_basis", "candidate_group_id": multi["candidate_group_id"],
            "candidate_ids": list(ids), "expressions": list(expressions),
            "cv_rmse": _finite(multi.get("mean_validation_rmse"), "multi CV RMSE"),
            "cv_nrmse": _finite(multi.get("mean_validation_nrmse"), "multi CV NRMSE", nullable=True),
            "cv_rmse_std": _finite(multi.get("std_validation_rmse"), "multi CV RMSE std"),
            "cv_nrmse_std": _finite(multi.get("std_validation_nrmse"), "multi CV NRMSE std", nullable=True),
            "complexity": int(multi.get("symbolic_complexity", 0)),
        })

    if not options:
        return {
            "schema": "v60_native_final_model_v1",
            "execution_status": "no_credible_candidate",
            "selection_performed": False,
            "far_or_evaluation_data_used": False,
            "candidate_options": [],
            "selected_model": None,
        }

    use_nrmse = all(option["cv_nrmse"] is not None for option in options)
    metric = "cv_nrmse" if use_nrmse else "cv_rmse"
    variability = "cv_nrmse_std" if use_nrmse else "cv_rmse_std"
    options.sort(key=lambda item: (
        item[metric], item[variability] if item[variability] is not None else float("inf"),
        item["complexity"], item["family"],
    ))
    winner = options[0]

    symbols = [sp.Symbol(name, real=True) for name in names]
    columns = []
    for expression in winner["expressions"]:
        parsed = parse_sympy_expression(expression, list(names))
        fn = sp.lambdify(symbols, parsed, modules="numpy")
        values = np.asarray(fn(*[X[:, i] for i in range(X.shape[1])]), dtype=float)
        if values.ndim == 0:
            values = np.full(X.shape[0], float(values))
        values = values.reshape(-1)
        if values.size != y.size or not np.all(np.isfinite(values)):
            raise ValueError("selected symbolic basis produced non-finite or misaligned training values")
        columns.append(values)

    design = np.column_stack((*columns, np.ones(y.size, dtype=float)))
    coefficients, _, rank, singular = np.linalg.lstsq(design, y, rcond=None)
    prediction = design @ coefficients
    residual = y - prediction
    rmse = float(np.sqrt(np.mean(np.square(residual))))
    target_std = float(np.std(y))
    nrmse = rmse / target_std if target_std > 0 else None
    target_ss = float(np.sum(np.square(y - np.mean(y))))
    r2 = 1.0 - float(np.sum(np.square(residual))) / target_ss if target_ss > 0 else None
    scale = max(float(singular[0]) if singular.size else 0.0, 1.0)
    condition = float(singular[0] / singular[-1]) if singular.size and singular[-1] > np.finfo(float).eps * scale else None

    terms = [
        f"({float(coef):.17g})*({expr})"
        for coef, expr in zip(coefficients[:-1], winner["expressions"])
    ]
    formula = " + ".join(terms + [f"({float(coefficients[-1]):.17g})"])
    selected = {
        "family": winner["family"],
        "candidate_id": winner.get("candidate_id"),
        "candidate_group_id": winner.get("candidate_group_id"),
        "basis_candidate_ids": winner.get("candidate_ids", [winner.get("candidate_id")]),
        "basis_expressions": list(winner["expressions"]),
        "variable_names": list(names),
        "fitted_expression": formula,
        "coefficients": [float(value) for value in coefficients],
        "training_row_count": int(y.size),
        "training_target_std": target_std,
        "training_rmse": rmse,
        "training_nrmse": nrmse,
        "training_r2": r2,
        "training_design_rank": int(rank),
        "training_design_condition_number": condition,
        "selection_metric": metric,
        "cross_validation_metric": winner[metric],
        "cross_validation_metric_std": winner[variability],
        "symbolic_complexity": winner["complexity"],
    }
    digest_payload = {key: value for key, value in selected.items()}
    return {
        "schema": "v60_native_final_model_v1",
        "execution_status": "selected",
        "selection_performed": True,
        "far_or_evaluation_data_used": False,
        "cross_family_policy": "minimum_common_cv_error_then_fold_variability_then_complexity_then_family",
        "objective_metric": metric,
        "candidate_options": options,
        "selected_model": selected,
        "selected_model_sha256": sha256(json.dumps(digest_payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest(),
    }


__all__ = ["finalize_native_v60_model"]
