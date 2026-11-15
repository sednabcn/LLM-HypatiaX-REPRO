"""Single-equation pilot comparing zero-shot and data-informed LLM-only prompts.

No PySR, optimizer, coefficient fitter, or ground-truth formula is used.
Only the generated final formula is scored on untouched test/extrapolation rows.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from hypatiax.experiments.benchmarks import exp1_four_way_matched as driver
from hypatiax.core.base_pure_llm import baseline_pure_llm_defi_discovery as pure_llm


CASE_ID = int(os.environ.get("LLM_PILOT_CASE_ID", "3"))
N_EXAMPLES = 12
MODEL = os.environ.get("HYPATIAX_LLM_MODEL", "").strip() or pure_llm.resolve_model()[0]
TEMPERATURE = 0.25


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compact_stats(X, y, names):
    result = {"n": int(len(y)), "features": {}, "target": {}}
    for i, name in enumerate(names):
        values = np.asarray(X[:, i], dtype=float)
        result["features"][name] = {
            "min": float(np.min(values)), "max": float(np.max(values)),
            "mean": float(np.mean(values)), "std": float(np.std(values)),
            "q10": float(np.quantile(values, .1)),
            "q25": float(np.quantile(values, .25)),
            "median": float(np.quantile(values, .5)),
            "q75": float(np.quantile(values, .75)),
            "q90": float(np.quantile(values, .9)),
        }
        correlation = float(np.corrcoef(values, y)[0, 1])
        result["features"][name]["target_correlation"] = correlation if np.isfinite(correlation) else None
    result["target"] = {
        "min": float(np.min(y)), "max": float(np.max(y)),
        "mean": float(np.mean(y)), "std": float(np.std(y)),
        "q10": float(np.quantile(y, .1)),
        "q25": float(np.quantile(y, .25)),
        "median": float(np.quantile(y, .5)),
        "q75": float(np.quantile(y, .75)),
        "q90": float(np.quantile(y, .9)),
    }
    return result


def fixed_examples(X, y, names):
    order = np.argsort(X[:, 0], kind="stable")
    indices = np.linspace(0, len(order) - 1, min(N_EXAMPLES, len(order)), dtype=int)
    rows = []
    for idx in order[indices]:
        rows.append({
            "inputs": {name: float(X[idx, j]) for j, name in enumerate(names)},
            "output": float(y[idx]),
        })
    return rows


def prompt_for(eq, names, mode, X_train, y_train, examples, feedback=None, previous_formula=None):
    base = f"""You are discovering a mathematical relationship from a benchmark task.
Task: {eq['name']}
Domain: {eq['domain']}
Declared input variables (and the ONLY allowed function parameters): {names}
Information regime: {mode}

Infer a formula from ONLY the task description and the training-only information
below. Do not use external tools, fitting code, optimization, symbolic regression,
or hidden benchmark knowledge. Return a numeric literal for every coefficient.
The Python function signature must exactly match the declared inputs in order.
Do not add coefficient parameters, defaults, *args, or **kwargs.
Do not mention or request test or extrapolation data.

Return exactly these sections:
FORMULA:
one-line mathematical formula
LATEX:
LaTeX formula
PYTHON:
def formula({', '.join(names)}):
    return <numpy-compatible expression>
VARIABLES:
meanings
ASSUMPTIONS:
assumptions
EXPLANATION:
brief explanation
"""
    if mode == "fewshot_training_examples":
        base += "\nTraining-only input/output examples (12 deterministic rows):\n"
        base += json.dumps(examples, sort_keys=True)
    elif mode == "training_summary_statistics":
        base += "\nTraining-only summary statistics (no raw rows):\n"
        base += json.dumps(compact_stats(X_train, y_train, names), sort_keys=True)
    elif mode == "training_feedback_revision":
        base += "\nTraining-only input/output examples (12 deterministic rows):\n"
        base += json.dumps(examples, sort_keys=True)
        if feedback is not None:
            base += "\nPrevious proposed Python formula (training-only evaluation; revise this formula once):\n"
            base += str(previous_formula or "")
            base += "\nTraining-only error feedback for that formula; revise once:\n"
            base += json.dumps(feedback, sort_keys=True)
            base += "\nReturn a revised final formula. Do not use any held-out data."
    return base


def call_llm(baseline, prompt):
    response = pure_llm._create_message(
        baseline.client,
        model=MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    blocks = [b for b in response.content if getattr(b, "type", None) == "text"]
    if not blocks:
        raise RuntimeError("LLM response contained no text block")
    text = blocks[0].text
    parsed = baseline._parse_response(text)
    code = parsed.get("python", "")
    if not code or code == "N/A":
        raise RuntimeError("LLM response did not contain a Python formula")
    baseline.validate_formula_signature(code, VAR_NAMES)
    from hypatiax.core import llm_call
    call_info = llm_call.last_call_info()
    if not call_info.get("temperature_sent") or call_info.get("temperature_requested") != TEMPERATURE:
        raise RuntimeError(f"shared LLM temperature contract not confirmed: {call_info}")
    return {
        "response_text": text, "response_sha256": sha(text),
        "formula": code, "formula_sha256": sha(code),
        "temperature_requested": call_info.get("temperature_requested"),
        "temperature_sent": call_info.get("temperature_sent"),
        "usage": {
            "input_tokens": getattr(getattr(response, "usage", None), "input_tokens", None),
            "output_tokens": getattr(getattr(response, "usage", None), "output_tokens", None),
        },
    }


def train_feedback(code, X, y, names):
    pred = driver.rcsb._runner_eval_formula(code, X, names)
    yt = np.asarray(y, dtype=float).reshape(-1)
    yp = np.asarray(pred, dtype=float).reshape(-1)
    if yt.shape != yp.shape or not np.isfinite(yp).all():
        raise ValueError("initial formula produced invalid training predictions")
    return {
        "scope": "training_partition_only",
        "n": int(len(yt)),
        "r2": float(r2_score(yt, yp)),
        "rmse": float(np.sqrt(mean_squared_error(yt, yp))),
        "mae": float(mean_absolute_error(yt, yp)),
    }


def score_formula(code, X_test, y_test, extrap, names):
    pred = driver.rcsb._runner_eval_formula(code, X_test, names)
    test = driver._metrics(y_test, pred)
    extra = {}
    failures = {}
    for regime, (X_e, y_e) in extrap.items():
        try:
            extra[regime] = driver._metrics(
                y_e, driver.rcsb._runner_eval_formula(code, X_e, names)
            )
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            extra[regime] = {"success": False, "error": message}
            failures[regime] = message
    return {"test": test, "extrapolation": extra, "success": True,
            "extrapolation_failures": failures}


def main():
    if not os.environ.get("ANTHROPIC_API_KEY", "").startswith("sk-"):
        raise RuntimeError("ANTHROPIC_API_KEY is required; refusing offline or hardcoded fallback")
    if not 0 <= CASE_ID < len(driver.abl.CORE_15):
        raise ValueError(f"case_id must be 0..14, got {CASE_ID}")

    global VAR_NAMES
    eq = driver.abl.CORE_15[CASE_ID]
    VAR_NAMES = list(eq["vars"])
    eq_seed = driver.SEED + driver.abl.EQ_ID[eq["name"]] * 7
    X_train, X_test, y_train, y_test, _, _ = driver.abl.generate_data(
        eq, N=driver.N_TRAIN_SOURCE, noise_level=driver.NOISE_LEVEL, seed=eq_seed
    )
    extrap = {
        regime: driver.abl.generate_extrap_data(eq, regime=regime, N=driver.N_EXTRAP, seed=eq_seed)
        for regime, _ in driver.abl.EXTRAP_REGIMES
    }
    examples = fixed_examples(X_train, y_train, VAR_NAMES)
    baseline = pure_llm.PureLLMBaseline(model=MODEL)
    output = Path(os.environ.get(
        "LLM_PILOT_OUTPUT_DIR",
        str(ROOT / "hypatiax" / "data" / "results" / "data_informed_llm_pilot"
            / f"run-{os.environ.get('GITHUB_RUN_ID', 'local')}-attempt-{os.environ.get('GITHUB_RUN_ATTEMPT', '1')}")
    ))
    output.mkdir(parents=True, exist_ok=True)

    variants = {
        "llm_only_zero_shot": "zero_shot_task_description_only",
        "llm_only_fewshot_train": "fewshot_training_examples",
        "llm_only_train_summary": "training_summary_statistics",
        "llm_only_train_feedback": "training_feedback_revision",
    }
    results = {
        "case_id": CASE_ID, "equation": eq["name"], "domain": eq["domain"],
        "seed": driver.SEED, "noise_level": driver.NOISE_LEVEL,
        "n_train": int(len(X_train)), "n_test": int(len(X_test)),
        "model": MODEL, "temperature": TEMPERATURE,
        "train_data_sha256": driver._array_hash(X_train, y_train),
        "outer_test_sha256": driver._array_hash(X_test, y_test),
        "extrapolation_sha256": {
            regime: driver._array_hash(X_e, y_e) for regime, (X_e, y_e) in extrap.items()
        },
        "variants": {},
    }

    for key, mode in variants.items():
        started = time.monotonic()
        row = {
            "information_regime": mode,
            "training_arrays_exposed_to_model": key != "llm_only_zero_shot",
            "api_calls": 0,
        }
        try:
            if key == "llm_only_zero_shot":
                # Preserve the established strict zero-shot implementation unchanged.
                raw = baseline.generate_formula(
                    description=eq["name"], domain=eq["domain"].lower().replace(" ", "_"),
                    variable_names=VAR_NAMES,
                    metadata={
                        "equation_name": eq["name"],
                        "domain": eq["domain"].lower().replace(" ", "_"),
                        "difficulty": eq.get("difficulty", "medium"),
                        "benchmark_arm": "llm_only_zero_shot_no_pysr_refinement",
                        "information_regime": "zero_shot_task_description_only",
                        "training_arrays_used_by_model": False,
                    },
                    X=None, y=None,
                )
                code = raw.get("python_code", "")
                baseline.validate_formula_signature(code, VAR_NAMES)
                if (not raw.get("llm_called") or not raw.get("temperature_sent")
                        or raw.get("temperature_requested") != TEMPERATURE):
                    raise RuntimeError("zero-shot control did not confirm a live LLM response at the protocol temperature")
                row["response_sha256"] = sha(raw.get("raw_response", ""))
                row["prompt_sha256"] = raw.get("prompt_sha256")
                row["temperature_requested"] = raw.get("temperature_requested")
                row["temperature_sent"] = raw.get("temperature_sent")
                row["usage"] = raw.get("usage")
                row["model"] = raw.get("model")
                row["formula"] = code
                row["formula_sha256"] = sha(code)
                row["api_calls"] = 1
            else:
                prompt = prompt_for(eq, VAR_NAMES, mode, X_train, y_train, examples)
                first = call_llm(baseline, prompt)
                row["prompt_sha256"] = sha(prompt)
                row["first_response_sha256"] = first["response_sha256"]
                row["first_formula"] = first["formula"]
                row["first_usage"] = first["usage"]
                row["first_temperature_requested"] = first["temperature_requested"]
                row["first_temperature_sent"] = first["temperature_sent"]
                row["api_calls"] = 1
                final = first
                if key == "llm_only_train_feedback":
                    feedback = train_feedback(first["formula"], X_train, y_train, VAR_NAMES)
                    revision_prompt = prompt_for(
                        eq, VAR_NAMES, mode, X_train, y_train, examples,
                        feedback=feedback, previous_formula=first["formula"],
                    )
                    final = call_llm(baseline, revision_prompt)
                    row["revision_prompt_sha256"] = sha(revision_prompt)
                    row["training_feedback"] = feedback
                    row["revision_response_sha256"] = final["response_sha256"]
                    row["revision_usage"] = final["usage"]
                    row["revision_temperature_requested"] = final["temperature_requested"]
                    row["revision_temperature_sent"] = final["temperature_sent"]
                    row["api_calls"] = 2
                row["formula"] = final["formula"]
                row["formula_sha256"] = final["formula_sha256"]
                row["usage"] = final["usage"]
                row["temperature_requested"] = final["temperature_requested"]
                row["temperature_sent"] = final["temperature_sent"]

            row["metrics"] = score_formula(row["formula"], X_test, y_test, extrap, VAR_NAMES)
            row["success"] = bool(row["metrics"].get("success", True))
            if row["metrics"].get("extrapolation_failures"):
                row["extrapolation_errors"] = row["metrics"]["extrapolation_failures"]
        except Exception as exc:
            row["success"] = False
            row["error"] = f"{type(exc).__name__}: {exc}"
        row["elapsed_seconds"] = time.monotonic() - started
        results["variants"][key] = row
        print(f"[pilot] {key}: success={row['success']} calls={row['api_calls']} elapsed={row['elapsed_seconds']:.1f}s", flush=True)

    results["protocol"] = {
        "test_and_extrapolation_data_sent_to_llm": False,
        "external_fitting_or_symbolic_regression": False,
        "ground_truth_formula_sent_to_llm": False,
        "signature_contract": "exact declared ordered input signature; coefficients must be numeric literals",
        "scoring": "shared canonical R2/RMSE/MAE; catastrophic R2 below -100 remains failure",
        "fewshot_examples": N_EXAMPLES,
        "feedback_revisions_max": 1,
    }
    (output / "data_informed_llm_pilot_results.json").write_text(
        json.dumps(driver._json_safe(results), indent=2, allow_nan=False), encoding="utf-8"
    )
    (output / "data_informed_llm_pilot_manifest.json").write_text(
        json.dumps(driver._json_safe({
            "experiment": "single-case data-informed LLM-only strategy pilot",
            "case_id": CASE_ID, "equation": eq["name"], "model": MODEL,
            "temperature": TEMPERATURE, "seed": driver.SEED,
            "train_data_sha256": results["train_data_sha256"],
            "outer_test_sha256": results["outer_test_sha256"],
            "extrapolation_sha256": results["extrapolation_sha256"],
            "variants": list(variants),
            "execution_status": "completed",
        }), indent=2, allow_nan=False), encoding="utf-8"
    )
    print(f"[pilot] artifacts: {output}", flush=True)


if __name__ == "__main__":
    main()
