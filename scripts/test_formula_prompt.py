#!/usr/bin/env python3
"""Lightweight CLI test for the strict HypatiaX formula prompt.

Offline mode validates the production prompt contract and signature validator.
Live mode makes exactly one LLM request for one Core-15 equation, then scores
that unchanged zero-shot response on train, outer-test, and extrapolation data.
No PySR, fitting, retries, or test-data prompt exposure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _strict_environment() -> None:
    # The prompt test must never silently use a hardcoded or hint-based path.
    os.environ["HYPATIAX_STRICT"] = "1"
    os.environ["HYPATIAX_DISABLE_HARDCODED"] = "1"
    os.environ["HYPATIAX_DISABLE_PROMPT_HINTS"] = "1"
    os.environ["HYPATIAX_ALLOW_LEGACY"] = "0"
    os.environ["NO_LLM_CACHE"] = "1"


def _prompt_contract(case_name: str = "Allometric Scaling",
                     domain: str = "biology",
                     variables: list[str] | None = None) -> dict:
    from hypatiax.core.base_pure_llm.baseline_pure_llm_defi_discovery import (
        PureLLMBaseline,
    )

    names = list(variables or ["M"])
    # Calling the real production prompt builder does not construct an API
    # client and cannot make a network request.
    baseline = PureLLMBaseline.__new__(PureLLMBaseline)
    prompt = baseline._generate_standard_prompt(
        description=case_name,
        domain=domain,
        variable_names=names,
        metadata={},
    )
    required = [
        f"def formula({', '.join(names)}):",
        "function signature must match the declared input variables EXACTLY",
        "Every coefficient or constant not supplied in the task specification must be a numeric literal",
        "Do not infer coefficients from training data or fit any parameters",
        "Do not add parameters",
    ]
    missing = [phrase for phrase in required if phrase not in prompt]
    forbidden = [
        "ground_truth",
        "formula_sympy",
        "formula_latex",
        "0.1 * M ** 0.75",
        "3.5 * M",
    ]
    leaked = [phrase for phrase in forbidden if phrase in prompt]
    if missing or leaked:
        raise AssertionError(
            f"prompt contract failed; missing={missing}, forbidden_content={leaked}"
        )

    good = "def formula(M):\n    return 0.1 * M ** 0.75"
    bad = "def formula(M, a, b):\n    return a * M ** b"
    PureLLMBaseline.validate_formula_signature(good, names)
    try:
        PureLLMBaseline.validate_formula_signature(bad, names)
    except (ValueError, SyntaxError):
        bad_signature_rejected = True
    else:
        bad_signature_rejected = False
    if not bad_signature_rejected:
        raise AssertionError("signature validator accepted undeclared parameters")

    return {
        "status": "passed",
        "api_calls": 0,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "declared_variables": names,
        "checks": {
            "exact_ordered_signature_required": True,
            "numeric_literal_coefficients_required": True,
            "coefficient_fitting_forbidden": True,
            "ground_truth_and_equation_hints_absent": True,
            "valid_signature_accepted": True,
            "undeclared_parameters_rejected": True,
        },
    }


def _evaluate(code: str, X, y, names, driver) -> dict:
    diagnostics: list[str] = []
    prediction = driver.rcsb._runner_eval_formula(
        code, X, names, diagnostics=diagnostics
    )
    if prediction is None:
        raise ValueError("formula evaluation failed: " + "; ".join(diagnostics))
    return driver._metrics(y, prediction)


def _live_test(case_id: int, model: str | None, output: Path | None) -> dict:
    _strict_environment()
    import numpy as np

    from hypatiax.core.base_pure_llm.baseline_pure_llm_defi_discovery import (
        PureLLMBaseline,
    )
    from hypatiax.experiments.benchmarks import exp1_four_way_matched as driver
    from hypatiax.core import llm_call

    if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        raise RuntimeError("ANTHROPIC_API_KEY is missing; live mode will not fall back offline")
    if not 0 <= case_id < len(driver.abl.CORE_15):
        raise ValueError(f"--case-id must be between 0 and {len(driver.abl.CORE_15) - 1}")

    eq = driver.abl.CORE_15[case_id]
    names = list(eq["vars"])
    equation_seed = driver.SEED + driver.abl.EQ_ID[eq["name"]] * 7
    X_train, X_test, y_train, y_test, _, _ = driver.abl.generate_data(
        eq,
        N=driver.N_TRAIN_SOURCE,
        noise_level=driver.NOISE_LEVEL,
        seed=equation_seed,
    )
    extrapolation = {
        regime: driver.abl.generate_extrap_data(
            eq, regime=regime, N=driver.N_EXTRAP, seed=equation_seed
        )
        for regime, _ in driver.abl.EXTRAP_REGIMES
    }

    baseline = PureLLMBaseline(model=model)
    metadata = {
        "equation_name": eq["name"],
        "domain": eq["domain"].lower().replace(" ", "_"),
        "difficulty": eq.get("difficulty", "medium"),
        "benchmark_arm": "strict_zero_shot_prompt_cli_test",
        "information_regime": "zero_shot_task_description_only",
        "training_arrays_used_by_model": False,
    }

    # Exactly one production prompt / shared-wrapper call. X and y are
    # deliberately not passed to generate_formula.
    generated = baseline.generate_formula(
        description=eq["name"],
        domain=eq["domain"].lower().replace(" ", "_"),
        variable_names=names,
        metadata=metadata,
        X=None,
        y=None,
    )
    code = generated.get("python_code", "")
    if not generated.get("llm_called") or not generated.get("llm_attempted"):
        raise RuntimeError("live response lacks confirmed LLM-call provenance")
    if not generated.get("temperature_sent") or generated.get("temperature_requested") != 0.25:
        raise RuntimeError("shared LLM wrapper did not confirm temperature 0.25")
    baseline.validate_formula_signature(code, names)

    metric_results = {}
    metric_errors = {}
    partitions = {
        "train": (X_train, y_train),
        "outer_test": (X_test, y_test),
        **{f"extrapolation_{k}": v for k, v in extrapolation.items()},
    }
    for partition, (X_part, y_part) in partitions.items():
        try:
            metric_results[partition] = _evaluate(
                code, X_part, y_part, names, driver
            )
        except Exception as exc:
            metric_errors[partition] = f"{type(exc).__name__}: {exc}"

    result = {
        "status": "passed" if not metric_errors else "failed",
        "api_calls": 1,
        "equation": eq["name"],
        "case_id": case_id,
        "model": generated.get("model"),
        "temperature_requested": generated.get("temperature_requested"),
        "temperature_sent": generated.get("temperature_sent"),
        "prompt_sha256": generated.get("prompt_sha256"),
        "response_sha256": hashlib.sha256(
            generated.get("raw_response", "").encode("utf-8")
        ).hexdigest(),
        "formula": code,
        "formula_sha256": hashlib.sha256(code.encode("utf-8")).hexdigest(),
        "training_arrays_sent_to_model": False,
        "metrics": metric_results,
        "metric_errors": metric_errors,
        "protocol": {
            "zero_shot_task_description_only": True,
            "test_or_extrapolation_data_sent_to_model": False,
            "ground_truth_formula_sent_to_model": False,
            "fitting_or_optimizer_used": False,
            "pysr_used": False,
            "retry_count": 0,
        },
        "usage": generated.get("usage"),
        "llm_call_info": llm_call.last_call_info(),
    }

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(driver._json_safe(result), indent=2, allow_nan=False),
            encoding="utf-8",
        )
    return driver._json_safe(result)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline contract check and one-call live test of the strict formula prompt."
    )
    parser.add_argument(
        "--mode", choices=("offline", "live", "both"), default="offline",
        help="offline makes zero API calls; live makes exactly one; both runs offline then live",
    )
    parser.add_argument("--case-id", type=int, default=3,
                        help="Core-15 case index (default: 3, Allometric Scaling)")
    parser.add_argument("--model", default=None, help="Optional explicit Anthropic model id")
    parser.add_argument("--output", type=Path, default=Path("prompt_test_result.json"),
                        help="JSON output path for live results")
    args = parser.parse_args()

    report = {}
    if args.mode in ("offline", "both"):
        report["offline"] = _prompt_contract()
        print("OFFLINE PROMPT CONTRACT: PASS (0 API calls)", flush=True)
    if args.mode in ("live", "both"):
        report["live"] = _live_test(args.case_id, args.model, args.output)
        live_status = report["live"].get("status")
        print(f"LIVE PROMPT TEST: {str(live_status).upper()} (1 API call)", flush=True)
        print(f"Live result written to: {args.output}", flush=True)

    print(json.dumps(report, indent=2, allow_nan=False))
    return 1 if report.get("live", {}).get("status") == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
