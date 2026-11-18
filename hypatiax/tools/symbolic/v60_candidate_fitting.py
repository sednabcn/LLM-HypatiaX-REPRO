"""Native V60 training-only affine fitting for normalized candidates.

Each symbolic template is treated as a single basis function and fitted with
an intercept by deterministic least squares. Only the caller-supplied training
arrays are read; no validation/far set, external producer, or model-selection
decision is involved in this stage.
"""
from __future__ import annotations

from time import monotonic
from typing import Any, Mapping, Sequence

import numpy as np

from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression


def fit_native_training_candidates(
    candidates: Sequence[Mapping[str, Any]], X: Any, y: Any, *,
    variable_names: Sequence[str], max_candidates: int,
    max_search_attempts: int, max_wall_time_seconds: float | None = None,
) -> dict[str, Any]:
    """Fit bounded slope * candidate_expression + intercept models.

    Candidate expressions are parsed with the repository restricted parser.
    Each candidate is evaluated over every supplied training row or rejected;
    rows are never silently dropped to improve a fit.
    """
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
    if targets.size != features.shape[0] or targets.ndim not in (1, 2):
        raise ValueError("training targets must contain one value per feature row")
    targets = targets.reshape(-1)
    if not np.all(np.isfinite(features)) or not np.all(np.isfinite(targets)):
        raise ValueError("training data must be finite; rows are never silently excluded")

    input_count = len(candidates)
    cap = min(input_count, max_candidates, max_search_attempts)
    started = monotonic()
    fitted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    timed_out = False
    function_cache: dict[str, Any] = {}

    for candidate in candidates[:cap]:
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
            basis = np.asarray(function(*[features[:, col] for col in range(features.shape[1])]), dtype=float)
            if basis.ndim == 0:
                basis = np.full(features.shape[0], float(basis))
            basis = basis.reshape(-1)
            if basis.size != targets.size or not np.all(np.isfinite(basis)):
                raise ValueError("candidate produced non-finite or misaligned training predictions")

            design = np.column_stack((basis, np.ones(basis.size, dtype=float)))
            coefficients, _, rank, _ = np.linalg.lstsq(design, targets, rcond=None)
            residual = targets - design @ coefficients
            rmse = float(np.sqrt(np.mean(np.square(residual))))
            target_std = float(np.std(targets))
            target_var = float(np.sum(np.square(targets - np.mean(targets))))
            nrmse = rmse / target_std if target_std > 0 else None
            r2 = 1.0 - float(np.sum(np.square(residual))) / target_var if target_var > 0 else None
            slope, intercept = float(coefficients[0]), float(coefficients[1])
            fitted.append({
                "candidate_id": candidate_id, "expression": expression,
                "fitted_expression": f"({slope:.17g})*({expression})+({intercept:.17g})",
                "source_provenance": [dict(item) for item in lineage],
                "fit_status": "fitted",
                "fit_method": "training_only_affine_least_squares",
                "training_row_count": int(targets.size),
                "training_rmse": rmse, "training_nrmse": nrmse, "training_r2": r2,
                "training_rank": int(rank),
                "coefficients": {"scale": slope, "intercept": intercept},
            })
        except Exception as exc:
            rejected.append({
                "candidate_id": candidate_id, "expression": expression,
                "fit_status": "rejected", "reason": f"{type(exc).__name__}: {exc}",
                "source_provenance": [dict(item) for item in lineage] if isinstance(lineage, (list, tuple)) else [],
            })

    return {
        "schema": "v60_native_training_fits_v1",
        "input_candidate_count": input_count,
        "fit_attempt_count": len(fitted) + len(rejected),
        "fitted_candidate_count": len(fitted),
        "rejected_candidate_count": len(rejected),
        "budget_truncated_count": input_count - (len(fitted) + len(rejected)),
        "timed_out": timed_out, "training_row_count": int(targets.size),
        "fit_method": "training_only_affine_least_squares",
        "selection_performed": False,
        "fitted_candidates": fitted, "rejected_candidates": rejected,
    }


__all__ = ["fit_native_training_candidates"]