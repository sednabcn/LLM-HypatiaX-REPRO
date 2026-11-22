#!/usr/bin/env python3
"""Leakage-controlled LLM edge-degradation calibration cohort.

Each formula is generated from central training rows only, then scored on
those same core rows and the disjoint, withheld training-edge rows. Equations
are stratified into calibration and independent evaluation cohorts before any
LLM request. This script never changes routing tau.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hypatiax.core.routing import training_edge_split_indices
from hypatiax.experiments.benchmarks import hypatiax_defi_benchmark_v3c as benchmark
from hypatiax.protocols.experiment_protocol_defi import DeFiExperimentProtocol


MODEL = "claude-sonnet-4-6"
PROTOCOL_VERSION = "llm-edge-calibration-v2-diagnostics"
SPLIT_SEED = 20261122
EDGE_FRACTION = 0.15
CALIBRATION_FRACTION = 0.60


def _cohort_assignment(cases: list[dict]) -> dict[str, str]:
    """Deterministic, difficulty-stratified split at the equation level."""
    rng = np.random.RandomState(SPLIT_SEED)
    assigned: dict[str, str] = {}
    for difficulty in sorted({c["difficulty"] for c in cases}):
        group = sorted(c["name"] for c in cases if c["difficulty"] == difficulty)
        order = rng.permutation(len(group))
        n_cal = int(round(len(group) * CALIBRATION_FRACTION))
        n_cal = min(max(n_cal, 1), len(group) - 1)
        for idx in order[:n_cal]:
            assigned[group[int(idx)]] = "calibration"
        for idx in order[n_cal:]:
            assigned[group[int(idx)]] = "evaluation"
    return assigned


def _match_protocol_case(name: str, matches: list[tuple]):
    """Prefer exact descriptions; substring fallback is only for legacy aliases."""
    exact = next((item for item in matches if name.lower() == item[0].lower()), None)
    if exact is not None:
        return exact
    return next((item for item in matches if name.lower() in item[0].lower()), None)


def _array_hash(*arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    for array in arrays:
        values = np.ascontiguousarray(np.asarray(array, dtype="<f8"))
        digest.update(str(values.shape).encode("ascii"))
        digest.update(values.tobytes())
    return digest.hexdigest()


def _json_rows(X: np.ndarray, y: np.ndarray, names: list[str]) -> str:
    rows = []
    for x, target in zip(X, y):
        row = {name: float(format(float(value), ".10g"))
               for name, value in zip(names, x)}
        row["target"] = float(format(float(target), ".10g"))
        rows.append(row)
    return json.dumps(rows, separators=(",", ":"), allow_nan=False)


def _generate_from_core(description: str, domain: str, var_names: list[str],
                        metadata: dict, X_core: np.ndarray, y_core: np.ndarray) -> dict:
    """Exactly one live request; the prompt contains no edge rows or labels."""
    timeout_s = float(os.environ.get("LLM_METHOD_TIMEOUT", "120"))
    if not np.isfinite(timeout_s) or timeout_s <= 0:
        raise ValueError("LLM_METHOD_TIMEOUT must be finite and positive")
    from anthropic import Anthropic
    from hypatiax.core.llm_call import create_message, last_call_info

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"],
                       timeout=timeout_s, max_retries=0)
    variables = ", ".join(var_names)
    constants = metadata.get("constants") or {}
    constants_text = "\n".join(f"{k} = {v}" for k, v in constants.items())
    examples = _json_rows(X_core, y_core, var_names)
    prompt = f"""You are deriving a general mathematical formula from examples.

Quantity: {description}
Domain: {domain}
Variables in positional order: {variables}
Known constants (if any):
{constants_text or "(none)"}

CENTRAL TRAINING EXAMPLES (the complete information available to you):
{examples}

Infer a general mathematical relationship that explains these examples.
Do not memorize or interpolate individual rows. Do not assume access to any
other observations. Return ONLY a Python function named formula accepting
the listed variables as positional numpy-array arguments and returning a
numpy array. Use numpy as np. No imports, markdown, or explanation.

Required signature:
def formula({variables}):
    return <expression>
"""
    start = time.monotonic()
    attempted = False
    info = {}
    try:
        attempted = True
        response = create_message(
            client, model=MODEL, max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        info = last_call_info()
        code = response.content[0].text.strip()
        fence = chr(96) * 3
        if fence in code:
            code = "\n".join(line for line in code.splitlines()
                              if not line.strip().startswith(fence)).strip()
        return {
            "formula": code if "def formula" in code else None,
            "llm_called": True,
            "llm_source": "live_anthropic",
            "model": MODEL,
            "temperature_requested": info.get("temperature_requested"),
            "temperature_sent": info.get("temperature_sent", False),
            "generation_time_s": round(time.monotonic() - start, 3),
            "error": None if "def formula" in code else "response_missing_formula_function",
        }
    except Exception as exc:
        try:
            info = last_call_info()
        except Exception:
            pass
        return {
            "formula": None,
            "llm_called": attempted,
            "llm_source": "live_anthropic_failed" if attempted else "not_started",
            "model": MODEL,
            "temperature_requested": info.get("temperature_requested"),
            "temperature_sent": info.get("temperature_sent", False),
            "generation_time_s": round(time.monotonic() - start, 3),
            "error": f"{type(exc).__name__}: {exc}",
        }


def _atomic_save(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({
                "protocol_version": PROTOCOL_VERSION,
                "model": MODEL,
                "split_seed": SPLIT_SEED,
                "edge_fraction": EDGE_FRACTION,
                "calibration_fraction": CALIBRATION_FRACTION,
                "records": records,
            }, handle, indent=2, allow_nan=False)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _bootstrap_interval(values: np.ndarray, statistic: str, seed: int) -> list[float] | None:
    if values.size < 2:
        return None
    rng = np.random.RandomState(seed)
    samples = rng.choice(values, size=(2000, values.size), replace=True)
    if statistic == "median":
        estimates = np.median(samples, axis=1)
    elif statistic == "q90":
        estimates = np.quantile(samples, 0.90, axis=1)
    else:
        raise ValueError(f"unsupported bootstrap statistic: {statistic}")
    bounds = np.quantile(estimates, [0.025, 0.975])
    return [float(bounds[0]), float(bounds[1])]


def _score_predictions(y_true: np.ndarray, y_pred: np.ndarray,
                       reference_scale: float) -> dict:
    """Return transparent fit diagnostics; never clip or discard poor finite fits."""
    y_true = np.asarray(y_true, dtype=float).reshape(-1)
    y_pred = np.asarray(y_pred, dtype=float).reshape(-1)
    if y_true.shape != y_pred.shape:
        return {"ok": False, "failure_reason": "prediction_target_shape_mismatch"}
    if y_true.size < 2:
        return {"ok": False, "failure_reason": "fewer_than_two_targets"}
    if not np.isfinite(y_true).all():
        return {"ok": False, "failure_reason": "nonfinite_targets"}
    if not np.isfinite(y_pred).all():
        return {"ok": False, "failure_reason": "nonfinite_predictions"}
    metrics = benchmark._compute_metrics(y_true, y_pred)
    if not np.isfinite(metrics["r2"]):
        return {"ok": False, "failure_reason": "undefined_r2"}
    scale = float(reference_scale)
    nrmse = float(metrics["rmse"] / scale) if np.isfinite(scale) and scale > 1e-12 else None
    return {
        "ok": True,
        "r2": float(metrics["r2"]),
        "mae": float(metrics["mae"]),
        "rmse": float(metrics["rmse"]),
        "nrmse_core_scale": nrmse,
        "target_min": float(np.min(y_true)),
        "target_max": float(np.max(y_true)),
        "target_std": float(np.std(y_true)),
        "prediction_min": float(np.min(y_pred)),
        "prediction_max": float(np.max(y_pred)),
        "prediction_std": float(np.std(y_pred)),
    }


def _evaluate_formula_pair(formula: str, X_core: np.ndarray, y_core: np.ndarray,
                           X_edge: np.ndarray, y_edge: np.ndarray,
                           constants: dict | None = None) -> dict:
    """Score both disjoint partitions and normalize both errors by core target scale."""
    core_scale = float(np.std(np.asarray(y_core, dtype=float)))
    diagnostics = {}
    for label, X, y in (("core", X_core, y_core), ("edge", X_edge, y_edge)):
        execution = benchmark._execute_formula_diagnostic(
            formula, X, constants=constants
        )
        if not execution.get("ok"):
            diagnostics[label] = {
                "ok": False,
                "failure_reason": execution.get("failure_reason", "unknown_execution_failure"),
                "execution_diagnostics": {
                    key: value for key, value in execution.items()
                    if key not in {"predictions", "ok", "failure_reason"}
                },
                **({"detail": execution["detail"]} if execution.get("detail") else {}),
            }
            continue
        scored = _score_predictions(y, execution["predictions"], core_scale)
        scored["execution_mode"] = execution.get("execution_mode")
        scored["nonfinite_fraction_repaired"] = execution.get("nonfinite_fraction", 0.0)
        diagnostics[label] = scored

    core, edge = diagnostics["core"], diagnostics["edge"]
    if core.get("ok") and edge.get("ok"):
        delta_r2 = float(core["r2"] - edge["r2"])
        core_nrmse, edge_nrmse = (
            core.get("nrmse_core_scale"), edge.get("nrmse_core_scale")
        )
        delta_nrmse = (
            float(edge_nrmse - core_nrmse)
            if core_nrmse is not None and edge_nrmse is not None else None
        )
        return {
            "ok": True, "core": core, "edge": edge,
            "delta_llm": delta_r2, "delta_nrmse_core_scale": delta_nrmse,
        }
    return {
        "ok": False, "core": core, "edge": edge,
        "failure_reason": ";".join(
            f"{part}:{data.get('failure_reason', 'unknown')}"
            for part, data in diagnostics.items() if not data.get("ok")
        ),
    }


def _summarize(records: list[dict]) -> dict:
    summary = {}
    for cohort in ("calibration", "evaluation"):
        cohort_records = [r for r in records if r["cohort"] == cohort]
        valid = [r for r in cohort_records if r.get("status") == "scored"
                 and r.get("delta_llm") is not None]
        deltas = np.asarray([r["delta_llm"] for r in valid], dtype=float)
        nrmse_deltas = np.asarray([
            r["delta_nrmse_core_scale"] for r in valid
            if r.get("delta_nrmse_core_scale") is not None
        ], dtype=float)
        summary[cohort] = {
            "n_equations": len(cohort_records),
            "n_scored": int(deltas.size),
            "n_failed_or_undefined": sum(r.get("status") != "scored" for r in cohort_records),
            "n_finite_r2_below_minus_one_core": sum(
                (r.get("core_diagnostics") or {}).get("r2", 0) < -1 for r in valid
            ),
            "n_finite_r2_below_minus_one_edge": sum(
                (r.get("edge_diagnostics") or {}).get("r2", 0) < -1 for r in valid
            ),
            "delta_mean": float(np.mean(deltas)) if deltas.size else None,
            "delta_median": float(np.median(deltas)) if deltas.size else None,
            "delta_q10": float(np.quantile(deltas, 0.10)) if deltas.size else None,
            "delta_q90": float(np.quantile(deltas, 0.90)) if deltas.size else None,
            "delta_nrmse_core_scale_median": (
                float(np.median(nrmse_deltas)) if nrmse_deltas.size else None
            ),
            "delta_median_bootstrap_95ci": _bootstrap_interval(
                deltas, "median", SPLIT_SEED + (0 if cohort == "calibration" else 1)
            ),
            "delta_q90_bootstrap_95ci": _bootstrap_interval(
                deltas, "q90", SPLIT_SEED + (10 if cohort == "calibration" else 11)
            ),
            "tau_eligible": False,
            "tau_ineligibility_reason": (
                "No predeclared acceptable-fit criterion; diagnostics are descriptive only"
            ),
        }
    return summary


def run(output: Path, max_calls: int, resume: bool = True) -> dict:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is required; no calls were made")
    cases = benchmark._get_test_cases()
    if len(cases) != 74:
        raise RuntimeError(f"Expected canonical 74-case catalogue, found {len(cases)}")
    assignment = _cohort_assignment(cases)
    if set(assignment.values()) != {"calibration", "evaluation"}:
        raise RuntimeError("Both equation-level cohorts must be non-empty")

    records_by_name: dict[str, dict] = {}
    if resume and output.exists():
        saved = json.loads(output.read_text(encoding="utf-8"))
        if saved.get("protocol_version") != PROTOCOL_VERSION:
            raise RuntimeError("Existing output uses a different protocol version")
        records_by_name = {r["equation_id"]: r for r in saved.get("records", [])}

    protocol = DeFiExperimentProtocol()
    calls_made = 0
    for case in cases:
        name = case["name"]
        if name in records_by_name and records_by_name[name].get("status") == "scored":
            continue
        if calls_made >= max_calls:
            break

        cohort = assignment[name]
        result = {
            "equation_id": name,
            "domain": case["domain"],
            "difficulty": case["difficulty"],
            "cohort": cohort,
            "status": "failed",
            "llm_called": False,
            "formula": None,
            "r2_core": None,
            "r2_edge": None,
            "delta_llm": None,
        }
        try:
            matches = protocol.load_test_data(case["domain"], num_samples=case["num_samples"])
            match = _match_protocol_case(name, matches)
            if match is None:
                raise ValueError("protocol_case_not_found")
            description, X_full, y_full, var_names, metadata = match
            metadata = dict(metadata or {})
            X_train, y_train, _, _, outer_split = benchmark._aggressive_split(
                X_full, y_full, case["config"], return_metadata=True
            )
            core_idx, edge_idx = training_edge_split_indices(
                X_train, EDGE_FRACTION
            )
            X_core, y_core = X_train[core_idx], y_train[core_idx]
            X_edge, y_edge = X_train[edge_idx], y_train[edge_idx]
            if len(X_core) < 10 or len(X_edge) < 5:
                raise ValueError("insufficient_core_or_edge_rows")

            # Only core rows are passed to the generation function. Edge labels
            # remain in this process solely for post-generation scoring.
            calls_made += 1  # conservative cap: count each generation attempt, including provider failures
            generated = _generate_from_core(
                description, case["domain"], var_names, metadata, X_core, y_core
            )
            result.update(generated)
            result.update({
                "n_core": int(len(X_core)),
                "n_edge": int(len(X_edge)),
                "core_indices_in_outer_train": core_idx.astype(int).tolist(),
                "edge_indices_in_outer_train": edge_idx.astype(int).tolist(),
                "core_examples_sha256": _array_hash(X_core, y_core),
                "edge_data_sha256": _array_hash(X_edge, y_edge),
                "outer_split": outer_split,
                "edge_split": {
                    "method": "two_tails_training_pca",
                    "fraction": EDGE_FRACTION,
                    "edge_sides": 2,
                },
            })
            formula = result.get("formula")
            if not formula:
                result["status"] = "generation_failed"
            else:
                constants = metadata.get("constants") or {}
                scored = _evaluate_formula_pair(
                    formula, X_core, y_core, X_edge, y_edge, constants=constants
                )
                result["core_diagnostics"] = scored.get("core")
                result["edge_diagnostics"] = scored.get("edge")
                if scored["ok"]:
                    result.update({
                        "status": "scored",
                        "r2_core": scored["core"]["r2"],
                        "r2_edge": scored["edge"]["r2"],
                        "delta_llm": scored["delta_llm"],
                        "delta_nrmse_core_scale": scored["delta_nrmse_core_scale"],
                    })
                else:
                    result["status"] = "score_undefined"
                    result["score_failure_reason"] = scored.get("failure_reason")
                    result["r2_core"] = (
                        scored["core"].get("r2") if scored.get("core", {}).get("ok") else None
                    )
                    result["r2_edge"] = (
                        scored["edge"].get("r2") if scored.get("edge", {}).get("ok") else None
                    )
        except Exception as exc:
            result["status"] = "error"
            result["error"] = f"{type(exc).__name__}: {exc}"
            result["llm_called"] = bool(result.get("llm_called", False))

        records_by_name[name] = result
        records = [records_by_name[k] for k in sorted(records_by_name)]
        _atomic_save(output, records)
        print(f"{name}: {result['status']} ({calls_made}/{max_calls} new API calls)",
              flush=True)

    final_records = [records_by_name[k] for k in sorted(records_by_name)]
    summary = _summarize(final_records)
    print(json.dumps(summary, indent=2))
    return {"records": final_records, "summary": summary}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=Path("hypatiax/data/results/routing_tau_calibration.json"))
    parser.add_argument("--max-calls", type=int, default=74,
                        help="Hard cap on new live LLM requests (default: 74)")
    parser.add_argument("--no-resume", action="store_true",
                        help="Do not reuse prior scored records")
    args = parser.parse_args()
    if not 1 <= args.max_calls <= 74:
        parser.error("--max-calls must be between 1 and 74")
    run(args.output, args.max_calls, resume=not args.no_resume)


if __name__ == "__main__":
    main()
