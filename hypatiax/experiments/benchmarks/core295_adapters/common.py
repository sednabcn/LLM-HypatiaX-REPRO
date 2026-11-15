"""Shared Core-295 scalar-equation adapter for the frozen Core-15 ablation engine.

This module is imported only when the shard driver is explicitly executed.
It never evaluates arbitrary Python source: canonical_expression is parsed by
the repository's restricted symbolic parser and lambdified by SymPy.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any

import numpy as np

from hypatiax.experiments.benchmarks.core295_catalogue import equations_from_manifest

METHOD = "catalogue_expression_fixed_v1"
SEED_POLICY = "sha256_run_equation_v1"
PARAMETER_SAMPLING = "fixed_per_equation_declared_numeric_values"
SAMPLING_SEMANTICS = "independent_inputs_with_fixed_parameters_and_physical_constants"
ARMS = ("pysr_only", "hypatia", "hypatia_nollm")


def _json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        number = float(value)
        return number if np.isfinite(number) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _digest_arrays(*arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    for array in arrays:
        value = np.ascontiguousarray(np.asarray(array, dtype="<f8"))
        digest.update(str(value.shape).encode("ascii"))
        digest.update(value.tobytes())
    return digest.hexdigest()


def _validate_generator(entry: dict, domain: str) -> None:
    if entry.get("domain") != domain:
        raise ValueError(f"adapter {domain} received {entry.get('domain')!r} entry")
    generator = entry.get("generator")
    if not isinstance(generator, dict) or generator.get("status") != "ready":
        raise ValueError("generator.status must be ready")
    expected = {
        "model_class": "explicit_scalar",
        "method": METHOD,
        "seed_policy": SEED_POLICY,
        "parameter_sampling": PARAMETER_SAMPLING,
        "sampling_semantics": SAMPLING_SEMANTICS,
    }
    for key, value in expected.items():
        if generator.get(key) != value:
            raise ValueError(f"generator.{key} must equal {value!r}; generic adapter will not infer it")
    if not isinstance(entry.get("canonical_expression"), str) or not entry["canonical_expression"].strip():
        raise ValueError("canonical_expression is required")
    model = entry.get("model_definition")
    if not isinstance(model, dict) or model.get("model_class") != "explicit_scalar":
        raise ValueError("shared adapter supports only model_definition.model_class=explicit_scalar")
    independent = model.get("independent_variables")
    fixed = model.get("fixed_parameters")
    constants = model.get("physical_constants")
    dependent = model.get("dependent_variables")
    states = model.get("state_variables")
    variables, ranges = entry.get("variables"), entry.get("input_ranges")
    if not isinstance(variables, dict) or not variables:
        raise ValueError("variables must be a non-empty object")
    role_lists = (independent, fixed, constants, dependent, states)
    if any(not isinstance(role, list) for role in role_lists):
        raise ValueError("all model variable roles must be explicit lists")
    roles = [symbol for role in role_lists for symbol in role]
    if len(roles) != len(set(roles)) or set(roles) != set(variables):
        raise ValueError("model variable roles must partition variables exactly")
    if dependent or states:
        raise ValueError("static scalar adapter does not support dependent variables or dynamic states")
    if not isinstance(ranges, dict) or set(ranges) != set(independent) or not independent:
        raise ValueError("input_ranges must cover exactly the independent input variables")
    parameter_values = entry.get("fixed_parameter_values")
    constant_values = entry.get("physical_constant_values")
    if not isinstance(parameter_values, dict) or set(parameter_values) != set(fixed):
        raise ValueError("fixed_parameter_values must provide every fixed parameter")
    if not isinstance(constant_values, dict) or set(constant_values) != set(constants):
        raise ValueError("physical_constant_values must provide every physical constant")
    for field, values in (("fixed_parameter_values", parameter_values),
                          ("physical_constant_values", constant_values)):
        for name, value in values.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
                raise ValueError(f"{field}.{name} must be a finite numeric value")
    if generator.get("parameter_sampling_scope") != "fixed_per_equation":
        raise ValueError("parameter_sampling_scope must be fixed_per_equation")
    if generator.get("constraints_enforced") is not True:
        raise ValueError("generator must explicitly attest that declared constraints are enforced")
    if not isinstance(generator.get("constraint_evidence"), str) or not generator["constraint_evidence"].strip():
        raise ValueError("generator.constraint_evidence is required")
    if generator.get("constraint_enforcement_method") != "rectangular_input_bounds_v1":
        raise ValueError("only constraints implied by rectangular input bounds are supported")
    validity = entry.get("input_validity_bounds")
    if not isinstance(validity, dict) or set(validity) != set(independent):
        raise ValueError("input_validity_bounds must cover every independent input")

    for variable in independent:
        bounds = ranges[variable]
        if not isinstance(bounds, dict):
            raise ValueError(f"{variable}: range record must be an object")
        for kind in ("train", "extrapolation"):
            interval = bounds.get(kind)
            if (not isinstance(interval, list) or len(interval) != 2
                    or any(isinstance(x, bool) or not isinstance(x, (int, float)) for x in interval)
                    or not np.isfinite(interval).all() or float(interval[0]) >= float(interval[1])):
                raise ValueError(f"{variable}: {kind} must be a finite increasing [low, high] pair")
        valid = validity[variable]
        if (not isinstance(valid, list) or len(valid) != 2
                or any(isinstance(x, bool) or not isinstance(x, (int, float)) for x in valid)
                or not np.isfinite(valid).all() or float(valid[0]) >= float(valid[1])):
            raise ValueError(f"{variable}: input validity bounds must be finite increasing [low, high]")
        valid_lo, valid_hi = map(float, valid)
        train_lo, train_hi = map(float, bounds["train"])
        extra_lo, extra_hi = map(float, bounds["extrapolation"])
        generated = [train_lo, train_hi, extra_lo, extra_hi]
        for factor in (1.0, 1.5, 4.0, 6.0):
            generated.append(train_hi * factor)
        if min(generated) < valid_lo or max(generated) > valid_hi:
            raise ValueError(f"{variable}: train, medium, near, or far extrapolation exceeds declared validity bounds")


def run_equation(*, entry: dict, context: dict, domain: str) -> dict:
    """Run the unchanged Core-15 three-arm condition function for one Core-295 row."""
    _validate_generator(entry, domain)
    if not isinstance(context, dict) or not context.get("run_id"):
        raise ValueError("run/shard context is required")
    seed_hex = context.get("seed_material_sha256")
    if not isinstance(seed_hex, str) or len(seed_hex) != 64:
        raise ValueError("driver-provided SHA-256 seed material is required")
    seed = int(seed_hex[:8], 16)

    # The catalogue adapter rejects unsupported syntax and undeclared symbols.
    converted = equations_from_manifest(
        {"catalogue_id": "core295-option2", "entries": [entry]},
        require_complete=False,
    )
    if len(converted) != 1:
        raise ValueError("expected exactly one converted scalar equation")
    equation = converted[0]

    # Reproduce the Core-15 data split/noise/extrapolation functions exactly.
    from hypatiax.experiments.benchmarks import exp1_ablation as exp1
    if equation["name"] in exp1.EQ_ID:
        raise ValueError("Core-295 equation name collides with Core-15 EQ_ID; refusing positional seed mapping")
    train = exp1.generate_data(equation, N=200, noise_level=0.05, seed=seed)
    extrap = {
        regime: exp1.generate_extrap_data(equation, regime=regime, N=100, seed=seed)
        for regime, _ in exp1.EXTRAP_REGIMES
    }
    binding_record = {
        "fixed_parameter_values": entry["fixed_parameter_values"],
        "physical_constant_values": entry["physical_constant_values"],
        "input_validity_bounds": entry["input_validity_bounds"],
    }
    binding_sha256 = hashlib.sha256(
        json.dumps(binding_record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    dataset_hashes = {
        "model_binding_sha256": binding_sha256,
        "train_all": _digest_arrays(train[4], train[5]),
        "train_split": _digest_arrays(train[0], train[2]),
        "ordinary_test_split": _digest_arrays(train[1], train[3]),
        **{regime: _digest_arrays(*arrays) for regime, arrays in extrap.items()},
    }

    results = {}
    for arm in ARMS:
        if arm == "hypatia" and not context.get("allow_live_services"):
            results[arm] = {
                "status": "skipped",
                "payload": {"reason": "live LLM arm requires --allow-live-services"},
            }
            continue
        if arm == "hypatia" and not os.environ.get("ANTHROPIC_API_KEY", "").startswith("sk-"):
            results[arm] = {
                "status": "failed",
                "payload": {"reason": "live LLM arm authorized but ANTHROPIC_API_KEY is unavailable"},
            }
            continue
        try:
            result = exp1.run_condition(
                equation, arm, seed=seed,
                dataset_override={"train": train, "extrapolation": extrap},
            )
            if result.get("timed_out"):
                status = "timeout"
            elif result.get("success") is True:
                status = "success"
            else:
                status = "failed"
            payload = _json_value(result)
            payload["dataset_sha256"] = dataset_hashes
            payload["seed"] = seed
            payload["equation_id"] = entry["equation_id"]
            results[arm] = {"status": status, "payload": payload}
        except TimeoutError as exc:
            results[arm] = {"status": "timeout", "payload": {"error": str(exc)}}
        except Exception as exc:
            results[arm] = {"status": "failed", "payload": {
                "error_type": type(exc).__name__, "error": str(exc),
            }}
    return results
