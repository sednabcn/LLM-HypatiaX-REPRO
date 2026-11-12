"""Shared Core-295 scalar-equation adapter for the frozen Core-15 ablation engine.

This module is imported only when the shard driver is explicitly executed.
It never evaluates arbitrary Python source: canonical_expression is parsed by
the repository's restricted symbolic parser and lambdified by SymPy.
"""
from __future__ import annotations

import hashlib
import os
from typing import Any

import numpy as np

from hypatiax.experiments.benchmarks.core295_catalogue import equations_from_manifest

METHOD = "catalogue_expression_v1"
SEED_POLICY = "sha256_run_equation_v1"
PARAMETER_SAMPLING = "independent_uniform_over_declared_ranges"
SAMPLING_SEMANTICS = "all_declared_variables_are_independent_inputs"
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
    variables, ranges = entry.get("variables"), entry.get("input_ranges")
    if not isinstance(variables, dict) or not variables or not isinstance(independent, list):
        raise ValueError("variables and explicit independent_variables are required")
    if set(independent) != set(variables):
        raise ValueError("shared adapter only supports records where every declared symbol is an independent input; fixed parameters/constants need a specialized generator")
    if model.get("fixed_parameters") or model.get("physical_constants") or model.get("state_variables") or model.get("dependent_variables"):
        raise ValueError("shared adapter cannot sample fixed parameters, constants, dependent variables, or dynamic states")
    if not isinstance(ranges, dict) or set(ranges) != set(independent):
        raise ValueError("input_ranges must cover exactly the independent input variables")
    for variable in variables:
        bounds = ranges[variable]
        if not isinstance(bounds, dict):
            raise ValueError(f"{variable}: range record must be an object")
        for kind in ("train", "extrapolation"):
            interval = bounds.get(kind)
            if (not isinstance(interval, list) or len(interval) != 2
                    or any(isinstance(x, bool) or not isinstance(x, (int, float)) for x in interval)
                    or not np.isfinite(interval).all() or float(interval[0]) >= float(interval[1])):
                raise ValueError(f"{variable}: {kind} must be a finite increasing [low, high] pair")


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
    dataset_hashes = {
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
            result = exp1.run_condition(equation, arm, seed=seed)
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
