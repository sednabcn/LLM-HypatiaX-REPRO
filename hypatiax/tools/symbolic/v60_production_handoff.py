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

    # A valid checksum is not evidence that the serialized model metrics or
    # cross-family decision are truthful. Reconstruct those contracts here,
    # before either far evaluation or outward production handoff.
    family = model.get("family")
    candidate_id = model.get("candidate_id")
    group_id = model.get("candidate_group_id")
    if family == "single_basis":
        if len(expressions) != 1 or not isinstance(candidate_id, str) or not candidate_id or group_id is not None or ids != [candidate_id]:
            raise ValueError("single-basis final model identity is inconsistent")
    elif family == "multi_basis":
        if not 2 <= len(expressions) <= 3 or candidate_id is not None or not isinstance(group_id, str) or not group_id:
            raise ValueError("multi-basis final model identity is inconsistent")
    else:
        raise ValueError("selected model family is unsupported")

    row_count = model.get("training_row_count")
    if isinstance(row_count, bool) or not isinstance(row_count, int) or row_count < 1:
        raise ValueError("selected model training row count must be a positive integer")
    for key in ("training_target_std", "training_rmse"):
        value = model.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) < 0:
            raise ValueError(f"selected model {key} must be finite and non-negative")
    for key in ("training_nrmse", "training_r2", "training_design_condition_number"):
        value = model.get(key)
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value))):
            raise ValueError(f"selected model {key} must be finite or null")
    target_std = float(model["training_target_std"])
    training_rmse = float(model["training_rmse"])
    training_nrmse = model.get("training_nrmse")
    if target_std > 0:
        expected_nrmse = training_rmse / target_std
        if training_nrmse is None or float(training_nrmse) < 0 or not math.isclose(float(training_nrmse), expected_nrmse, rel_tol=1e-9, abs_tol=1e-12):
            raise ValueError("selected model training NRMSE does not reproduce from RMSE and target standard deviation")
    elif training_nrmse is not None:
        raise ValueError("selected model training NRMSE must be null for a zero-variance target")
    condition = model.get("training_design_condition_number")
    if condition is not None and float(condition) < 0:
        raise ValueError("selected model design condition number cannot be negative")
    rank = model.get("training_design_rank")
    if isinstance(rank, bool) or not isinstance(rank, int) or rank != len(expressions) + 1:
        raise ValueError("selected model training design must have full column rank")

    metric = model.get("selection_metric")
    if metric not in {"cv_rmse", "cv_nrmse"}:
        raise ValueError("selected model cross-validation objective is unsupported")
    cv_metric = model.get("cross_validation_metric")
    cv_std = model.get("cross_validation_metric_std")
    for label, value in (("cross-validation metric", cv_metric), ("cross-validation metric std", cv_std)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) < 0:
            raise ValueError(f"selected model {label} must be finite and non-negative")
    if metric == "cv_nrmse" and (cv_metric is None or cv_std is None):
        raise ValueError("selected model normalized CV objective cannot be null")

    options = audit.get("candidate_options")
    if not isinstance(options, list) or not 1 <= len(options) <= 2:
        raise ValueError("final-model candidate_options must contain one or two family winners")
    families = []
    for option in options:
        if not isinstance(option, Mapping):
            raise ValueError("final-model candidate option must be a mapping")
        option_family = option.get("family")
        if option_family not in {"single_basis", "multi_basis"} or option_family in families:
            raise ValueError("final-model candidate families must be unique and recognized")
        families.append(option_family)
        for key in ("cv_rmse", "cv_rmse_std"):
            value = option.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) < 0:
                raise ValueError(f"final-model option {key} must be finite and non-negative")
        for key in ("cv_nrmse", "cv_nrmse_std"):
            value = option.get(key)
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) < 0):
                raise ValueError(f"final-model option {key} must be finite, non-negative, or null")
        if (option.get("cv_nrmse") is None) != (option.get("cv_nrmse_std") is None):
            raise ValueError("final-model option NRMSE mean/std nullability must match")
        complexity = option.get("complexity")
        if isinstance(complexity, bool) or not isinstance(complexity, int) or complexity < 0:
            raise ValueError("final-model option complexity must be a non-negative integer")
        option_expressions = option.get("expressions")
        if not isinstance(option_expressions, list) or not 1 <= len(option_expressions) <= 3 or any(not isinstance(item, str) or not item for item in option_expressions):
            raise ValueError("final-model option expressions are invalid")
        option_rank = option.get("training_design_rank")
        if isinstance(option_rank, bool) or not isinstance(option_rank, int) or option_rank != len(option_expressions) + 1:
            raise ValueError("final-model option training design must have full column rank")
        option_condition = option.get("training_design_condition_number")
        if option_condition is not None and (
            isinstance(option_condition, bool) or not isinstance(option_condition, (int, float))
            or not math.isfinite(float(option_condition)) or float(option_condition) < 0
        ):
            raise ValueError("final-model option condition number must be finite, non-negative, or null")
        for expression in option_expressions:
            parse_sympy_expression(expression, names)
        if option_family == "single_basis":
            if (len(option_expressions) != 1 or not isinstance(option.get("candidate_id"), str)
                    or not option.get("candidate_id") or option.get("candidate_group_id") is not None):
                raise ValueError("single-basis candidate option identity is invalid")
        else:
            option_ids = option.get("candidate_ids")
            if (not isinstance(option_ids, list) or len(option_ids) != len(option_expressions)
                    or not 2 <= len(option_ids) <= 3 or len(option_ids) != len(set(option_ids))
                    or any(not isinstance(item, str) or not item for item in option_ids)
                    or option.get("candidate_id") is not None
                    or not isinstance(option.get("candidate_group_id"), str) or not option.get("candidate_group_id")):
                raise ValueError("multi-basis candidate option identity is invalid")

    use_nrmse = all(option.get("cv_nrmse") is not None for option in options)
    expected_metric = "cv_nrmse" if use_nrmse else "cv_rmse"
    expected_variability = "cv_nrmse_std" if use_nrmse else "cv_rmse_std"
    winner = min(options, key=lambda option: (
        float(option[expected_metric]),
        float(option[expected_variability]) if option.get(expected_variability) is not None else float("inf"),
        int(option["complexity"]), option["family"],
    ))
    expected_ids = [winner["candidate_id"]] if winner["family"] == "single_basis" else list(winner["candidate_ids"])
    expected_candidate_id = winner.get("candidate_id") if winner["family"] == "single_basis" else None
    expected_group_id = winner.get("candidate_group_id") if winner["family"] == "multi_basis" else None
    if (audit.get("objective_metric") != expected_metric or metric != expected_metric
            or family != winner["family"] or candidate_id != expected_candidate_id
            or group_id != expected_group_id or ids != expected_ids
            or expressions != winner["expressions"]
            or cv_metric != winner[expected_metric]
            or cv_std != winner.get(expected_variability)
            or model.get("symbolic_complexity") != winner["complexity"]
            or model.get("training_design_rank") != winner.get("training_design_rank")
            or model.get("training_design_condition_number") != winner.get("training_design_condition_number")):
        raise ValueError("selected model does not match the reconstructed cross-family winner")
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
