"""Frozen production handoff for a finalized native V60 symbolic model.

The model is selected and refit using training-only evidence before this module
is called. This boundary verifies the immutable model digest, evaluates only
that frozen model on optional far data, and never reranks or retries candidates.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
from typing import Any, Mapping, Sequence

import numpy as np

from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression


def _canonical_digest(value: Mapping[str, Any]) -> str:
    payload = json.dumps(dict(value), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(payload.encode("utf-8")).hexdigest()


def _array(value: Any, label: str, width: int) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.ndim != 2 or result.shape[1] != width or result.shape[0] == 0:
        raise ValueError(f"{label} must be a non-empty 2-D array with {width} columns")
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{label} must contain only finite values")
    return result


def _targets(value: Any, rows: int, label: str) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.ndim not in (1, 2) or result.size != rows:
        raise ValueError(f"{label} must contain exactly one target per feature row")
    result = result.reshape(-1)
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{label} must contain only finite values")
    return result


def verify_final_model_audit(audit: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the stage-18 model envelope and return a detached model record."""
    if not isinstance(audit, Mapping) or audit.get("schema") != "v60_native_final_model_v1":
        raise ValueError("unsupported native V60 final-model audit")
    if audit.get("execution_status") != "selected" or audit.get("selection_performed") is not True:
        raise ValueError("a completed native V60 final-model selection is required")
    if audit.get("far_or_evaluation_data_used") is not False:
        raise ValueError("final model must certify training-only selection")
    model = audit.get("selected_model")
    if not isinstance(model, Mapping):
        raise ValueError("selected_model must be a mapping")
    supplied = audit.get("selected_model_sha256")
    if not isinstance(supplied, str) or len(supplied) != 64:
        raise ValueError("selected model digest is missing or malformed")
    if _canonical_digest(model) != supplied:
        raise ValueError("selected native V60 model digest verification failed")
    expressions = model.get("basis_expressions")
    ids = model.get("basis_candidate_ids")
    coefficients = model.get("coefficients")
    names = model.get("variable_names")
    if (
        not isinstance(expressions, list) or not 1 <= len(expressions) <= 3
        or not isinstance(ids, list) or len(ids) != len(expressions)
        or not isinstance(coefficients, list) or len(coefficients) != len(expressions) + 1
    ):
        raise ValueError("selected model basis lineage and coefficient dimensions do not align")
    if any(not isinstance(item, str) or not item for item in ids) or len(ids) != len(set(ids)):
        raise ValueError("selected model basis IDs must be unique non-empty strings")
    if (not isinstance(names, list) or not names
            or any(not isinstance(item, str) or not item for item in names)
            or len(names) != len(set(names))):
        raise ValueError("selected model variable_names must be unique non-empty strings")
    numeric_coefficients = []
    for value in coefficients:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError("selected model coefficients must be finite")
        numeric_coefficients.append(float(value))
    if any(not isinstance(item, str) or not item for item in expressions):
        raise ValueError("selected model expressions must be non-empty strings")
    for expression in expressions:
        parse_sympy_expression(expression, names)
    expected_formula = " + ".join(
        [f"({coefficient:.17g})*({expression})"
         for coefficient, expression in zip(numeric_coefficients[:-1], expressions)]
        + [f"({numeric_coefficients[-1]:.17g})"]
    )
    if model.get("fitted_expression") != expected_formula:
        raise ValueError("selected model fitted expression does not reproduce from its bases and coefficients")
    return json.loads(json.dumps(dict(model), sort_keys=True, separators=(",", ":"), allow_nan=False))


def evaluate_frozen_native_v60_model(
    final_model_audit: Mapping[str, Any],
    X_far: Any,
    y_far: Any,
    *,
    variable_names: Sequence[str],
) -> dict[str, Any]:
    """Evaluate exactly the finalized one-/multi-basis model on a frozen far set."""
    model = verify_final_model_audit(final_model_audit)
    names = tuple(variable_names)
    if not names or len(set(names)) != len(names) or any(not isinstance(n, str) or not n for n in names):
        raise ValueError("variable_names must be unique non-empty strings")
    if names != tuple(model["variable_names"]):
        raise ValueError("far-evaluation variable_names must exactly match the frozen model's declared order")
    far = _array(X_far, "X_far", len(names))
    far_y = _targets(y_far, far.shape[0], "y_far")

    import sympy as sp
    symbols = [sp.Symbol(name, real=True) for name in names]
    basis_values = []
    for expression in model["basis_expressions"]:
        parsed = parse_sympy_expression(expression, list(names))
        fn = sp.lambdify(symbols, parsed, modules="numpy")
        values = np.asarray(fn(*[far[:, i] for i in range(far.shape[1])]), dtype=np.float64)
        if values.ndim == 0:
            values = np.full(far.shape[0], float(values), dtype=np.float64)
        values = values.reshape(-1)
        if values.size != far.shape[0] or not np.all(np.isfinite(values)):
            raise ValueError("frozen selected basis produced non-finite or misaligned far predictions")
        basis_values.append(values)

    design = np.column_stack((*basis_values, np.ones(far.shape[0], dtype=np.float64)))
    coefficients = np.asarray(model["coefficients"], dtype=np.float64)
    prediction = design @ coefficients
    if not np.all(np.isfinite(prediction)):
        raise ValueError("frozen selected model produced non-finite far predictions")
    residual = far_y - prediction
    rmse = float(np.sqrt(np.mean(np.square(residual))))
    train_std = model.get("training_target_std")
    if train_std is None:
        # Stage 18 stores training NRMSE but not target scale. Derive the
        # normalizer from RMSE / NRMSE only when that ratio is well-defined.
        train_rmse = model.get("training_rmse")
        train_nrmse = model.get("training_nrmse")
        train_std = (
            float(train_rmse) / float(train_nrmse)
            if isinstance(train_rmse, (int, float)) and isinstance(train_nrmse, (int, float))
            and float(train_nrmse) > 0 else None
        )
    far_ss = float(np.sum(np.square(far_y - np.mean(far_y))))
    digest = sha256()
    for array in (far, far_y):
        contiguous = np.ascontiguousarray(array, dtype=np.float64)
        digest.update(json.dumps(list(contiguous.shape)).encode("ascii"))
        digest.update(contiguous.tobytes())

    return {
        "schema": "v60_native_frozen_model_evaluation_v1",
        "evaluation_status": "completed",
        "evaluation_scope": "single_frozen_finalized_model",
        "selected_model_sha256": final_model_audit["selected_model_sha256"],
        "far_set_sha256": digest.hexdigest(),
        "far_row_count": int(far.shape[0]),
        "far_metrics": {
            "rmse": rmse,
            "nrmse_by_training_target_std": rmse / float(train_std) if train_std is not None and float(train_std) > 0 else None,
            "mae": float(np.mean(np.abs(residual))),
            "bias": float(np.mean(residual)),
            "r2": 1.0 - float(np.sum(np.square(residual))) / far_ss if far_ss > 0 else None,
        },
        "selection_changed": False,
        "selection_performed": False,
        "far_or_evaluation_data_used_for_selection": False,
        "far_or_evaluation_data_used_for_retry": False,
        "candidate_ranking_performed": False,
    }


def build_native_v60_result(final_model_audit: Mapping[str, Any]) -> dict[str, Any]:
    """Create the canonical outward result fields from a verified final model."""
    model = verify_final_model_audit(final_model_audit)
    return {
        "success": True,
        "formula": model["fitted_expression"],
        "expression": model["fitted_expression"],
        "final_formula": model["fitted_expression"],
        "variable_names": list(model["variable_names"]),
        "r2": model.get("training_r2"),
        "rmse": model.get("training_rmse"),
        "nrmse": model.get("training_nrmse"),
        "strategy": "native_v60",
        "native_model": model,
        "native_model_sha256": final_model_audit["selected_model_sha256"],
    }


__all__ = [
    "verify_final_model_audit",
    "evaluate_frozen_native_v60_model",
    "build_native_v60_result",
]
