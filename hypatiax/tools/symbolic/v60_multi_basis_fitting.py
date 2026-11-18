"""Bounded native V60 joint fitting over small symbolic basis groups.

This stage fits additive linear combinations of already-normalized candidate
bases using training observations only. It is an audit artifact: it does not
rank candidates, alter the native selector, or inspect far/evaluation data.
"""
from __future__ import annotations

from hashlib import sha256
from itertools import combinations
import json
from time import monotonic
from typing import Any, Mapping, Sequence

import numpy as np

from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression


def fit_native_multi_basis_candidates(
    candidates: Sequence[Mapping[str, Any]], X: Any, y: Any, *,
    variable_names: Sequence[str], max_candidates: int,
    max_search_attempts: int, max_basis_terms: int = 2,
    max_wall_time_seconds: float | None = None,
) -> dict[str, Any]:
    """Jointly fit bounded additive groups of 2..max_basis_terms basis functions.

    The candidate-group budget counts attempted groups, not individual terms.
    Every basis is evaluated on every training row; non-finite or misaligned
    values reject the entire group. The intercept is fitted jointly with all
    basis coefficients using deterministic least squares.
    """
    for name, value in (
        ("max_candidates", max_candidates),
        ("max_search_attempts", max_search_attempts),
        ("max_basis_terms", max_basis_terms),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < (2 if name == "max_basis_terms" else 0):
            raise ValueError(f"{name} must be an integer >= {2 if name == 'max_basis_terms' else 0}")
    if max_wall_time_seconds is not None and (
        isinstance(max_wall_time_seconds, bool)
        or not isinstance(max_wall_time_seconds, (int, float))
        or max_wall_time_seconds <= 0
    ):
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

    usable = []
    seen_ids = set()
    for item in candidates[:max_candidates]:
        candidate_id = item.get("candidate_id")
        expression = item.get("normalized_expression") or item.get("expression")
        if isinstance(candidate_id, str) and candidate_id and candidate_id not in seen_ids and isinstance(expression, str) and expression.strip():
            seen_ids.add(candidate_id)
            usable.append((candidate_id, expression, item.get("producer_provenance", [])))

    started = monotonic()
    attempted = 0
    fitted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    timed_out = False
    basis_cache: dict[str, np.ndarray] = {}
    group_limit = min(max_search_attempts, max_candidates)
    stop = False

    for term_count in range(2, min(max_basis_terms, len(usable)) + 1):
        for group in combinations(usable, term_count):
            if attempted >= group_limit:
                stop = True
                break
            if max_wall_time_seconds is not None and monotonic() - started >= max_wall_time_seconds:
                timed_out = True
                stop = True
                break
            attempted += 1
            ids = [entry[0] for entry in group]
            expressions = [entry[1] for entry in group]
            group_id = "v60mb_" + sha256(
                json.dumps(ids, separators=(",", ":")).encode("utf-8")
            ).hexdigest()[:20]
            lineage = [
                dict(record)
                for _, _, records in group
                for record in records
                if isinstance(records, (list, tuple)) and isinstance(record, Mapping)
            ]
            try:
                import sympy as sp
                columns = []
                for expression in expressions:
                    if expression not in basis_cache:
                        parsed = parse_sympy_expression(expression, list(variable_names))
                        symbols = [sp.Symbol(name, real=True) for name in variable_names]
                        function = sp.lambdify(symbols, parsed, modules="numpy")
                        values = np.asarray(
                            function(*[features[:, col] for col in range(features.shape[1])]),
                            dtype=float,
                        )
                        if values.ndim == 0:
                            values = np.full(features.shape[0], float(values))
                        values = values.reshape(-1)
                        if values.size != targets.size or not np.all(np.isfinite(values)):
                            raise ValueError(f"basis {expression!r} produced invalid training values")
                        basis_cache[expression] = values
                    columns.append(basis_cache[expression])
                design = np.column_stack((*columns, np.ones(targets.size, dtype=float)))
                coefficients, _, rank, singular_values = np.linalg.lstsq(design, targets, rcond=None)
                predictions = design @ coefficients
                if not np.all(np.isfinite(coefficients)) or not np.all(np.isfinite(predictions)):
                    raise ValueError("joint fit produced non-finite coefficients or predictions")
                residual = targets - predictions
                rmse = float(np.sqrt(np.mean(np.square(residual))))
                target_std = float(np.std(targets))
                target_var = float(np.sum(np.square(targets - np.mean(targets))))
                nrmse = rmse / target_std if target_std > 0 else None
                r2 = 1.0 - float(np.sum(np.square(residual))) / target_var if target_var > 0 else None
                terms = [
                    {"candidate_id": candidate_id, "expression": expression, "coefficient": float(coefficients[index])}
                    for index, (candidate_id, expression, _) in enumerate(group)
                ]
                fitted.append({
                    "candidate_group_id": group_id,
                    "basis_candidate_ids": ids,
                    "basis_expressions": expressions,
                    "fitted_terms": terms,
                    "intercept": float(coefficients[-1]),
                    "fitted_expression": " + ".join(
                        f"({term['coefficient']:.17g})*({term['expression']})" for term in terms
                    ) + f" + ({float(coefficients[-1]):.17g})",
                    "source_provenance": lineage,
                    "fit_status": "fitted",
                    "fit_method": "training_only_joint_multi_basis_least_squares",
                    "training_row_count": int(targets.size),
                    "training_rmse": rmse,
                    "training_nrmse": nrmse,
                    "training_r2": r2,
                    "training_rank": int(rank),
                    "basis_term_count": term_count,
                    "design_condition_number": (
                        float(singular_values[0] / singular_values[-1])
                        if len(singular_values) and singular_values[-1] > 0 else None
                    ),
                })
            except Exception as exc:
                rejected.append({
                    "candidate_group_id": group_id,
                    "basis_candidate_ids": ids,
                    "basis_expressions": expressions,
                    "source_provenance": lineage,
                    "fit_status": "rejected",
                    "reason": f"{type(exc).__name__}: {exc}",
                })
        if stop:
            break

    total_possible = sum(
        1 for size in range(2, min(max_basis_terms, len(usable)) + 1)
        for _ in combinations(range(len(usable)), size)
    )
    return {
        "schema": "v60_native_multi_basis_fits_v1",
        "input_candidate_count": len(candidates),
        "usable_candidate_count": len(usable),
        "attempted_group_count": attempted,
        "fitted_group_count": len(fitted),
        "rejected_group_count": len(rejected),
        "budget_truncated_group_count": max(0, total_possible - attempted),
        "timed_out": timed_out,
        "max_basis_terms": max_basis_terms,
        "training_row_count": int(targets.size),
        "fit_method": "training_only_joint_multi_basis_least_squares",
        "selection_performed": False,
        "far_or_evaluation_data_used": False,
        "fitted_candidate_groups": fitted,
        "rejected_candidate_groups": rejected,
    }


__all__ = ["fit_native_multi_basis_candidates"]
