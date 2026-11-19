"""Bounded native V60 candidate fitting on training observations only.

Each normalized structural expression receives a two-parameter affine
calibration y ~= scale * expression(X) + offset. This stage never receives
validation folds, far/evaluation data, credentials, or external producers.
Training metrics are audit evidence only; this module does not select a winner.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numbers
import time
from typing import Any, Mapping, Sequence

import numpy as np

from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression


@dataclass(frozen=True)
class CandidateFitRecord:
    candidate_id: str
    expression: str
    status: str
    fitted_expression: str | None
    scale: float | None
    offset: float | None
    training_rmse: float | None
    training_r2: float | None
    training_row_count: int
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "expression": self.expression,
            "status": self.status,
            "fitted_expression": self.fitted_expression,
            "scale": self.scale,
            "offset": self.offset,
            "training_rmse": self.training_rmse,
            "training_r2": self.training_r2,
            "training_row_count": self.training_row_count,
            "reason": self.reason,
            "evidence_scope": "training_only_resubstitution",
        }


@dataclass(frozen=True)
class CandidateFittingResult:
    records: tuple[CandidateFitRecord, ...]
    input_candidate_count: int
    attempted_count: int
    budget_truncated_count: int
    deadline_exhausted: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "records": [record.to_dict() for record in self.records],
            "input_candidate_count": self.input_candidate_count,
            "attempted_count": self.attempted_count,
            "budget_truncated_count": self.budget_truncated_count,
            "deadline_exhausted": self.deadline_exhausted,
            "selection_performed": False,
            "evidence_scope": "training_only_resubstitution",
        }


def fit_native_candidates(
    candidates: Sequence[Mapping[str, Any]],
    X: Any,
    y: Any,
    *,
    variable_names: Sequence[str],
    max_candidates: int,
    max_search_attempts: int,
    max_wall_time_seconds: float | None = None,
) -> CandidateFittingResult:
    """Evaluate and affine-calibrate a bounded candidate prefix on training data.

    A candidate is rejected if its expression fails restricted parsing,
    produces non-real/non-finite values, or cannot be calibrated. No rows are
    silently dropped: every accepted fit uses the complete supplied training
    matrix and target vector.
    """
    if not isinstance(max_candidates, int) or isinstance(max_candidates, bool) or max_candidates < 0:
        raise ValueError("max_candidates must be a non-negative integer")
    if not isinstance(max_search_attempts, int) or isinstance(max_search_attempts, bool) or max_search_attempts < 0:
        raise ValueError("max_search_attempts must be a non-negative integer")
    if max_wall_time_seconds is not None:
        if (isinstance(max_wall_time_seconds, bool)
                or not isinstance(max_wall_time_seconds, numbers.Real)
                or not math.isfinite(float(max_wall_time_seconds))
                or max_wall_time_seconds <= 0):
            raise ValueError("max_wall_time_seconds must be finite and > 0 or None")
    if not isinstance(candidates, Sequence):
        raise TypeError("candidates must be a finite sequence")

    features = np.asarray(X, dtype=float)
    targets = np.asarray(y, dtype=float).reshape(-1)
    names = tuple(variable_names)
    if features.ndim != 2 or features.shape[1] != len(names):
        raise ValueError("X must be 2-D and match variable_names")
    if targets.size != features.shape[0] or not features.shape[0]:
        raise ValueError("y must contain exactly one target per non-empty X row")
    if not np.all(np.isfinite(features)) or not np.all(np.isfinite(targets)):
        raise ValueError("training data must be finite")

    cap = min(len(candidates), max_candidates, max_search_attempts)
    deadline = (time.monotonic() + max_wall_time_seconds
                if max_wall_time_seconds is not None else None)
    records: list[CandidateFitRecord] = []
    attempted = 0
    deadline_exhausted = False

    for candidate in candidates[:cap]:
        if deadline is not None and time.monotonic() >= deadline:
            deadline_exhausted = True
            break
        attempted += 1
        candidate_id_value = candidate.get("candidate_id") if isinstance(candidate, Mapping) else None
        expression_value = (
            (candidate.get("normalized_expression") or candidate.get("expression"))
            if isinstance(candidate, Mapping) else None
        )
        candidate_id = candidate_id_value if isinstance(candidate_id_value, str) else ""
        expression = expression_value if isinstance(expression_value, str) else ""
        try:
            if not candidate_id.strip() or not expression.strip():
                raise ValueError("candidate_id and expression must be non-empty strings")
            import sympy as sp
            parsed = parse_sympy_expression(expression, list(names))
            symbols = [sp.Symbol(name) for name in names]
            evaluator = sp.lambdify(symbols, parsed, modules="numpy")
            with np.errstate(all="ignore"):
                raw = np.asarray(evaluator(*[features[:, index] for index in range(len(names))]))
            if np.iscomplexobj(raw):
                raise ValueError("candidate produced complex predictions")
            raw = np.asarray(raw, dtype=float)
            if raw.ndim == 0:
                raw = np.full(targets.shape, float(raw))
            raw = raw.reshape(-1)
            if raw.size != targets.size or not np.all(np.isfinite(raw)):
                raise ValueError("candidate must produce one finite prediction per training row")

            design = np.column_stack((raw, np.ones(raw.size, dtype=float)))
            coefficients, _, _, _ = np.linalg.lstsq(design, targets, rcond=None)
            scale, offset = float(coefficients[0]), float(coefficients[1])
            prediction = design @ coefficients
            residual = targets - prediction
            rmse = float(np.sqrt(np.mean(np.square(residual))))
            total = float(np.sum(np.square(targets - np.mean(targets))))
            r2 = (float(1.0 - np.sum(np.square(residual)) / total)
                  if total > 0 else None)
            fitted = f"({scale:.17g})*({expression})+({offset:.17g})"
            records.append(CandidateFitRecord(
                candidate_id, expression, "fitted", fitted, scale, offset,
                rmse, r2, int(targets.size),
            ))
        except Exception as exc:
            records.append(CandidateFitRecord(
                candidate_id, expression, "rejected", None, None, None,
                None, None, int(targets.size),
                f"{type(exc).__name__}: {exc}"[:300],
            ))

    truncated = len(candidates) - attempted
    return CandidateFittingResult(
        tuple(records), len(candidates), attempted, truncated, deadline_exhausted
    )


__all__ = ["CandidateFitRecord", "CandidateFittingResult", "fit_native_candidates"]
