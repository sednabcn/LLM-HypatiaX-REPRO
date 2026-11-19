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
from hypatiax.tools.uncertainty import SplitConformalRegressor


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
            or model.get("symbolic_complexity") != winner["complexity"]):
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


def _predict_verified_native_model(model: Mapping[str, Any], features: np.ndarray) -> np.ndarray:
    """Predict from a previously verified frozen V60 model record."""
    names = list(model["variable_names"])
    import sympy as sp
    symbols = [sp.Symbol(name, real=True) for name in names]
    basis_values = []
    for expression in model["basis_expressions"]:
        parsed = parse_sympy_expression(expression, names)
        function = sp.lambdify(symbols, parsed, modules="numpy")
        values = np.asarray(
            function(*[features[:, index] for index in range(features.shape[1])]),
            dtype=np.float64,
        )
        if values.ndim == 0:
            values = np.full(features.shape[0], float(values), dtype=np.float64)
        values = values.reshape(-1)
        if values.size != features.shape[0] or not np.all(np.isfinite(values)):
            raise ValueError("frozen selected basis produced non-finite or misaligned predictions")
        basis_values.append(values)
    design = np.column_stack((*basis_values, np.ones(features.shape[0], dtype=np.float64)))
    predictions = design @ np.asarray(model["coefficients"], dtype=np.float64)
    if not np.all(np.isfinite(predictions)):
        raise ValueError("frozen selected model produced non-finite predictions")
    return predictions


def calibrate_frozen_native_v60_model(
    final_model_audit: Mapping[str, Any],
    X_calibration: Any,
    y_calibration: Any,
    *,
    variable_names: Sequence[str],
    nominal_coverage: float = 0.95,
    calibration_provenance: Mapping[str, Any],
) -> dict[str, Any]:
    """Calibrate intervals on a caller-attested disjoint calibration split.

    Calibration is post-selection and never changes or re-ranks the frozen
    model. The caller must attest that the calibration rows are disjoint from
    training and that calibration/future observations are exchangeable.
    """
    model = verify_final_model_audit(final_model_audit)
    names = tuple(variable_names)
    if names != tuple(model["variable_names"]):
        raise ValueError("calibration variable_names must exactly match the frozen model order")
    if not isinstance(calibration_provenance, Mapping):
        raise TypeError("calibration_provenance must be a mapping")
    training_split_id = calibration_provenance.get("training_split_id")
    calibration_split_id = calibration_provenance.get("calibration_split_id")
    if (not isinstance(training_split_id, str) or not training_split_id.strip()
            or not isinstance(calibration_split_id, str) or not calibration_split_id.strip()):
        raise ValueError("training_split_id and calibration_split_id must be non-empty strings")
    if training_split_id == calibration_split_id:
        raise ValueError("calibration split must be distinct from the training split")
    if calibration_provenance.get("disjoint_from_training") is not True:
        raise ValueError("caller must attest disjoint_from_training=true")
    if calibration_provenance.get("exchangeability_assumed") is not True:
        raise ValueError("caller must attest exchangeability_assumed=true")

    features = _array(X_calibration, "X_calibration", len(names))
    truth = _targets(y_calibration, features.shape[0], "y_calibration")
    predictions = _predict_verified_native_model(model, features)
    calibrator = SplitConformalRegressor(nominal_coverage).fit(truth, predictions)
    radius = calibrator.quantile()
    rank = int(math.ceil((truth.size + 1) * calibrator.nominal_coverage))
    minimum_n = int(math.ceil(calibrator.nominal_coverage / (1.0 - calibrator.nominal_coverage)))
    digest = sha256()
    for array in (features, truth):
        contiguous = np.ascontiguousarray(array, dtype=np.float64)
        digest.update(json.dumps(list(contiguous.shape)).encode("ascii"))
        digest.update(contiguous.tobytes())
    finite_radius = math.isfinite(radius)
    return {
        "schema": "v60_native_split_conformal_calibration_v1",
        "calibration_status": "calibrated" if finite_radius else "insufficient_calibration_size",
        "selected_model_sha256": final_model_audit["selected_model_sha256"],
        "calibration_set_sha256": digest.hexdigest(),
        "calibration_row_count": int(truth.size),
        "nominal_coverage": calibrator.nominal_coverage,
        "finite_sample_quantile_rank": rank,
        "minimum_calibration_size_for_finite_radius": minimum_n,
        "interval_radius": float(radius) if finite_radius else None,
        "calibration_metadata": calibrator.calibration_metadata,
        "calibration_provenance": {
            "training_split_id": training_split_id,
            "calibration_split_id": calibration_split_id,
            "disjoint_from_training": True,
            "exchangeability_assumed": True,
            "verification": "caller_attested_not_independently_verified",
        },
        "coverage_claim": "finite_sample_marginal_coverage_under_exchangeability",
        "extra_domain_or_distribution_shift_guarantee": False,
        "selection_changed": False,
        "selection_performed": False,
        "far_or_evaluation_data_used": False,
    }


def verify_native_v60_calibration_audit(
    final_model_audit: Mapping[str, Any],
    calibration_audit: Mapping[str, Any],
) -> dict[str, Any]:
    """Verify calibration provenance and finite-sample metadata against a frozen model."""
    verify_final_model_audit(final_model_audit)
    if not isinstance(calibration_audit, Mapping) or calibration_audit.get("schema") != "v60_native_split_conformal_calibration_v1":
        raise ValueError("unsupported native V60 calibration audit")
    if calibration_audit.get("selected_model_sha256") != final_model_audit.get("selected_model_sha256"):
        raise ValueError("calibration audit belongs to a different frozen model")
    digest = calibration_audit.get("calibration_set_sha256")
    if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise ValueError("calibration set digest must be a lowercase SHA-256 value")
    count = calibration_audit.get("calibration_row_count")
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("calibration row count must be a positive integer")
    coverage = calibration_audit.get("nominal_coverage")
    if isinstance(coverage, bool) or not isinstance(coverage, (int, float)):
        raise ValueError("calibration nominal coverage must be numeric")
    level = SplitConformalRegressor._validate_coverage(coverage)
    expected_rank = int(math.ceil((count + 1) * level))
    expected_minimum = int(math.ceil(level / (1.0 - level)))
    if calibration_audit.get("finite_sample_quantile_rank") != expected_rank:
        raise ValueError("calibration finite-sample quantile rank does not reproduce")
    if calibration_audit.get("minimum_calibration_size_for_finite_radius") != expected_minimum:
        raise ValueError("calibration minimum finite-radius sample size does not reproduce")
    expected_status = "calibrated" if expected_rank <= count else "insufficient_calibration_size"
    if calibration_audit.get("calibration_status") != expected_status:
        raise ValueError("calibration status does not match its finite-sample rank")
    radius = calibration_audit.get("interval_radius")
    if expected_status == "calibrated":
        if isinstance(radius, bool) or not isinstance(radius, (int, float)) or not math.isfinite(float(radius)) or float(radius) < 0:
            raise ValueError("calibrated interval radius must be finite and non-negative")
    elif radius is not None:
        raise ValueError("insufficient calibration size cannot publish a finite interval radius")
    expected_metadata = {
        "method": "split_conformal_absolute_residual",
        "calibration_n": count,
        "nominal_coverage": level,
        "calibration_score": "absolute_residual",
        "coverage_assumption": "exchangeability_of_calibration_and_evaluation_observations",
        "extra_domain_guarantee": False,
    }
    if calibration_audit.get("calibration_metadata") != expected_metadata:
        raise ValueError("calibration metadata does not match the split-conformal contract")
    provenance = calibration_audit.get("calibration_provenance")
    if not isinstance(provenance, Mapping):
        raise ValueError("calibration provenance must be a mapping")
    training_id, calibration_id = provenance.get("training_split_id"), provenance.get("calibration_split_id")
    if (not isinstance(training_id, str) or not training_id.strip()
            or not isinstance(calibration_id, str) or not calibration_id.strip()
            or training_id == calibration_id):
        raise ValueError("calibration provenance must identify distinct non-empty splits")
    if provenance.get("disjoint_from_training") is not True or provenance.get("exchangeability_assumed") is not True:
        raise ValueError("calibration provenance must retain both caller attestations")
    if provenance.get("verification") != "caller_attested_not_independently_verified":
        raise ValueError("calibration provenance verification scope is invalid")
    if calibration_audit.get("coverage_claim") != "finite_sample_marginal_coverage_under_exchangeability":
        raise ValueError("calibration coverage claim is unsupported")
    for key in ("extra_domain_or_distribution_shift_guarantee", "selection_changed", "selection_performed", "far_or_evaluation_data_used"):
        if calibration_audit.get(key) is not False:
            raise ValueError(f"calibration audit {key} must be false")
    return dict(calibration_audit)


def predict_frozen_native_v60_interval(
    final_model_audit: Mapping[str, Any],
    calibration_audit: Mapping[str, Any],
    X: Any,
    *,
    variable_names: Sequence[str],
) -> dict[str, Any]:
    """Return prediction intervals from a matching frozen model/calibration pair."""
    model = verify_final_model_audit(final_model_audit)
    calibration_audit = verify_native_v60_calibration_audit(final_model_audit, calibration_audit)
    if calibration_audit.get("calibration_status") != "calibrated":
        raise ValueError("a finite-radius completed calibration is required")
    radius = float(calibration_audit["interval_radius"])
    level = float(calibration_audit["nominal_coverage"])
    names = tuple(variable_names)
    if names != tuple(model["variable_names"]):
        raise ValueError("prediction variable_names must exactly match the frozen model order")
    features = _array(X, "X", len(names))
    predictions = _predict_verified_native_model(model, features)
    return {
        "schema": "v60_native_split_conformal_prediction_intervals_v1",
        "prediction_status": "completed",
        "selected_model_sha256": final_model_audit["selected_model_sha256"],
        "calibration_set_sha256": calibration_audit["calibration_set_sha256"],
        "nominal_coverage": level,
        "interval_radius": float(radius),
        "prediction": predictions.tolist(),
        "lower": (predictions - float(radius)).tolist(),
        "upper": (predictions + float(radius)).tolist(),
        "interval_kind": "symmetric_split_conformal_prediction_interval",
        "coverage_claim": "finite_sample_marginal_coverage_under_exchangeability",
        "extra_domain_or_distribution_shift_guarantee": False,
        "selection_changed": False,
        "selection_performed": False,
        "evaluation_targets_used": False,
    }


def build_native_v60_result(
    final_model_audit: Mapping[str, Any],
    calibration_audit: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create canonical result fields, optionally carrying verified calibration provenance."""
    model = verify_final_model_audit(final_model_audit)
    calibration = (
        verify_native_v60_calibration_audit(final_model_audit, calibration_audit)
        if calibration_audit is not None else None
    )
    result = {
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
    if calibration is not None:
        result["native_model_calibration"] = calibration
        result["native_model_calibration_status"] = calibration["calibration_status"]
    return result


def calibrate_native_v60_result(
    discovery_result: Mapping[str, Any],
    X_calibration: Any,
    y_calibration: Any,
    *,
    variable_names: Sequence[str],
    calibration_provenance: Mapping[str, Any],
    nominal_coverage: float = 0.95,
) -> dict[str, Any]:
    """Attach post-selection conformal calibration to a native V60 result.

    This helper consumes only an already-finalized result and a caller-supplied
    calibration split. It never refits, re-ranks, or changes the frozen model.
    When a sealed discovery report is present, its calibration provenance is
    updated and resealed in the same operation.
    """
    if not isinstance(discovery_result, Mapping):
        raise TypeError("discovery_result must be a mapping")
    if discovery_result.get("success") is not True:
        raise ValueError("calibration requires a successful native V60 discovery result")
    final_model_audit = discovery_result.get("native_v60_final_model")
    if not isinstance(final_model_audit, Mapping):
        raise ValueError("discovery result does not contain a finalized native V60 model audit")

    calibration = calibrate_frozen_native_v60_model(
        final_model_audit,
        X_calibration,
        y_calibration,
        variable_names=variable_names,
        nominal_coverage=nominal_coverage,
        calibration_provenance=calibration_provenance,
    )
    updated = dict(discovery_result)
    updated.update(build_native_v60_result(final_model_audit, calibration))
    updated["native_v60_final_model"] = dict(final_model_audit)
    updated["native_v60_calibration_audit"] = calibration

    report_envelope = discovery_result.get("discovery_report_envelope")
    if report_envelope is not None:
        if not isinstance(report_envelope, Mapping):
            raise TypeError("discovery_report_envelope must be a mapping")
        from hypatiax.tools.symbolic.discovery_report_integrity import (
            attach_native_v60_calibration_to_report,
        )
        updated["discovery_report_envelope"] = attach_native_v60_calibration_to_report(
            report_envelope, calibration
        )
    return updated


__all__ = [
    "verify_final_model_audit",
    "evaluate_frozen_native_v60_model",
    "calibrate_frozen_native_v60_model",
    "predict_frozen_native_v60_interval",
    "verify_native_v60_calibration_audit",
    "build_native_v60_result",
    "calibrate_native_v60_result",
]
