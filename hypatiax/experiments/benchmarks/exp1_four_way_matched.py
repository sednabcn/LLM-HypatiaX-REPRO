"""
Matched Core-15 four-arm predictive comparison.

Primary arms:
  hybrid_llm_pysr : exp1_ablation.run_condition("hypatia")
  llm_only        : PureLLMBaselineMethod formula, no symbolic refinement
  pysr_only       : exp1_ablation.run_condition("pysr_only")
  nn_only         : ImprovedNNMethod

The data-conditioned arms receive the same equation/seed training arrays.
The LLM-only arm receives those arrays through its wrapper interface, but
PureLLMBaseline intentionally ignores X/y and is therefore a zero-shot,
task-description-conditioned prior-knowledge baseline. The outer test
partition is held back from fitting and is scored using R2, RMSE and MAE.
Near/medium/far extrapolation arrays are also shared across arms.

This script is wired as the primary Core-15 comparison stage in the fresh
rerun launcher. Source changes are not execution authorization; it must be
reviewed before the user starts the experiment.
"""

from __future__ import annotations

import importlib.util
import hashlib
import json
import os
import time
import traceback
from pathlib import Path

import numpy as np

# Enforce the real LLM-backed Hybrid arm before importing the engine modules.
os.environ["HYPATIAX_STRICT"] = "1"
os.environ["HYPATIAX_DISABLE_HARDCODED"] = "1"
os.environ["HYPATIAX_DISABLE_PROMPT_HINTS"] = "1"

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPO = "sednabcn/LLM-HypatiaX-REPRO"


def _load(filename: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, HERE / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


abl = _load("exp1_ablation.py", "matched_four_way_ablation")
rcsb = _load("run_comparative_suite_benchmark_v2.py", "matched_four_way_rcsb")

SEED = int(os.environ.get("PYSR_SEED", os.environ.get("NN_SEED", "42")))
COMMON_WALL_CLOCK = int(os.environ.get("FOUR_WAY_METHOD_TIMEOUT", os.environ.get("METHOD_TIMEOUT", "900")))
# Reserve 60 seconds inside the arm budget for PySR shutdown and result finalization.
# PySR's own timeout must fire before the outer SIGALRM wall-clock guard.
PYSR_ONLY_FIT_TIMEOUT = max(1, COMMON_WALL_CLOCK - 60)
NOISE_LEVEL = float(os.environ.get("FOUR_WAY_NOISE_LEVEL", "0.05"))
N_TRAIN_SOURCE = int(os.environ.get("FOUR_WAY_N_SAMPLES", "200"))
N_EXTRAP = int(os.environ.get("FOUR_WAY_N_EXTRAP", "100"))
OUT_DIR = Path(os.environ.get("FOUR_WAY_OUTPUT_DIR", str(Path(os.environ.get("RESULTS_DIR", str(Path.cwd()))) / "four_way_matched")))
OUT_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_PATH = OUT_DIR / "exp1_four_way_matched_results.json"
CHECKPOINT_PATH = OUT_DIR / "exp1_four_way_matched_checkpoint.json"
MANIFEST_PATH = OUT_DIR / "exp1_four_way_matched_manifest.json"
SUMMARY_PATH = OUT_DIR / "exp1_four_way_matched_summary.json"

METHOD_KEYS = ("hybrid_llm_pysr", "llm_only", "pysr_only", "nn_only")


def _json_safe(value):
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def _metrics(y_true, y_pred):
    yt = np.asarray(y_true, dtype=float).reshape(-1)
    yp = np.asarray(y_pred, dtype=float).reshape(-1)
    if (
        yt.shape != yp.shape or yt.size == 0
        or not np.all(np.isfinite(yt))
        or not np.all(np.isfinite(yp))
    ):
        raise ValueError("target/prediction shape mismatch or non-finite values")
    values = {
        "r2": abl._safe_r2(yt, yp),
        "rmse": abl._safe_rmse(yt, yp),
        "mae": abl._safe_mae(yt, yp),
    }
    if any(value is None or not np.isfinite(float(value)) for value in values.values()):
        raise ValueError("one or more evaluation metrics are undefined or non-finite")
    return {key: float(value) for key, value in values.items()}


def _llm_metric_diagnostics(y_true, y_pred):
    """Explain why an otherwise evaluable LLM formula failed primary scoring."""
    yt = np.asarray(y_true, dtype=float).reshape(-1)
    yp = np.asarray(y_pred, dtype=float).reshape(-1)
    details = {
        "target_shape": list(yt.shape),
        "prediction_shape": list(yp.shape),
        "target_finite_count": int(np.isfinite(yt).sum()),
        "prediction_finite_count": int(np.isfinite(yp).sum()),
        "prediction_total_count": int(yp.size),
    }
    if yp.size and np.isfinite(yp).any():
        finite = yp[np.isfinite(yp)]
        details["prediction_min"] = float(np.min(finite))
        details["prediction_max"] = float(np.max(finite))
    if yt.shape == yp.shape and yt.size and np.isfinite(yt).all() and np.isfinite(yp).all():
        from hypatiax.core.r2_canonical import r2_scored
        scored, status = r2_scored(yt, yp)
        raw, raw_status = r2_scored(yt, yp, floor=None)
        details.update({
            "canonical_r2": float(scored) if np.isfinite(scored) else None,
            "canonical_r2_status": status,
            "unfloored_r2": float(raw) if np.isfinite(raw) else None,
            "unfloored_r2_status": raw_status,
            "rmse": float(np.sqrt(np.mean((yt - yp) ** 2))),
            "mae": float(np.mean(np.abs(yt - yp))),
        })
    return details


def _array_hash(*arrays):
    digest = hashlib.sha256()
    for array in arrays:
        value = np.ascontiguousarray(np.asarray(array, dtype=np.float64))
        digest.update(str(value.shape).encode("ascii"))
        digest.update(value.tobytes())
    return digest.hexdigest()


def _run_fingerprint():
    """Bind resumable results to the exact driver, dependencies, protocol and run settings."""
    source_paths = (
        Path(__file__).resolve(),
        HERE / "exp1_ablation.py",
        HERE / "run_comparative_suite_benchmark_v2.py",
        # Runtime algorithm/evaluation modules imported by the benchmark arms.
        ROOT / "hypatiax" / "safe_formula.py",
        ROOT / "hypatiax" / "core" / "r2_canonical.py",
        ROOT / "hypatiax" / "core" / "base_pure_llm" / "baseline_pure_llm_defi_discovery.py",
        ROOT / "hypatiax" / "core" / "llm_call.py",
        ROOT / "hypatiax" / "core" / "training" / "baseline_neural_network_defi_improved.py",
        ROOT / "hypatiax" / "tools" / "symbolic" / "symbolic_engine.py",
        ROOT / "hypatiax" / "tools" / "symbolic" / "hybrid_system_v50_2.py",
        ROOT / "hypatiax" / "core" / "enforce_flags.py",
    )
    source_hashes = {}
    for path in source_paths:
        if not path.is_file():
            raise RuntimeError(f"Cannot fingerprint required source file: {path}")
        source_hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()

    protocol_path = os.environ.get("REPRO_CFG")
    protocol_hash = None
    if protocol_path:
        resolved_protocol = Path(protocol_path).expanduser().resolve()
        if not resolved_protocol.is_file():
            raise RuntimeError(f"Configured protocol file does not exist: {resolved_protocol}")
    else:
        # PureLLMBaseline.resolve_model() searches these same ancestors for
        # config/repro.yaml when REPRO_CFG is unset. Fingerprint that implicit
        # config too; otherwise editing it could silently change the LLM model
        # while a checkpoint still appears compatible.
        resolved_protocol = next(
            (
                parent / "config" / "repro.yaml"
                for parent in Path(
                    "hypatiax/core/base_pure_llm/baseline_pure_llm_defi_discovery.py"
                ).resolve().parents
                if (parent / "config" / "repro.yaml").is_file()
            ),
            None,
        )
    if resolved_protocol is not None:
        protocol_hash = hashlib.sha256(resolved_protocol.read_bytes()).hexdigest()

    from hypatiax.core.base_pure_llm.baseline_pure_llm_defi_discovery import resolve_model
    pure_llm_model, pure_llm_model_source = resolve_model()
    hybrid_llm_model = (
        os.environ.get("HYPATIAX_LLM_MODEL", "").strip() or "claude-sonnet-4-6"
    )

    # Checkpoint compatibility must include the actual numerical/API runtime,
    # not only source and protocol files: dependency upgrades can change fits,
    # formula evaluation, and API-client behavior without changing either hash.
    from importlib.metadata import version
    import platform
    runtime_versions = {
        package: version(package)
        for package in (
            "numpy", "scipy", "sympy", "pandas", "scikit-learn",
            "torch", "pysr", "anthropic", "PyYAML",
        )
    }

    settings = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "runtime_dependency_versions": runtime_versions,
        "seed": SEED,
        "common_wall_clock_seconds": COMMON_WALL_CLOCK,
        "noise_level": NOISE_LEVEL,
        "n_train_source": N_TRAIN_SOURCE,
        "n_extrapolation": N_EXTRAP,
        # Record effective imported settings, not just environment aliases:
        # exp1_ablation gives N_ITERATIONS precedence over PYSR_NITERATIONS
        # and POPULATIONS precedence over PYSR_POPULATIONS.
        # The Pure LLM and Hybrid arms resolve model IDs through distinct
        # configuration paths; record both effective values and provenance.
        "pure_llm_model_effective": pure_llm_model,
        "pure_llm_model_source": pure_llm_model_source,
        "hybrid_llm_model_effective": hybrid_llm_model,
        "ablation_llm_model_metadata": abl.MODEL_STRING,
        "llm_temperature_effective": 0.25,
        "pysr_niterations_effective": abl.NITERATIONS,
        "pysr_populations_effective": abl.POPULATIONS,
        "hybrid_pysr_timeout_seconds_effective": abl.PYSR_TIMEOUT_SECS,
        "pysr_only_fit_timeout_seconds_effective": PYSR_ONLY_FIT_TIMEOUT,
        "hybrid_max_retries_effective": abl._HYPATIA_MAX_RETRIES,
        "llm_cache_disabled": os.environ.get("NO_LLM_CACHE", "1") == "1",
    }
    payload = {
        "schema": 1,
        "source_sha256": source_hashes,
        "protocol_sha256": protocol_hash,
        "settings": settings,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return {"sha256": hashlib.sha256(encoded).hexdigest(), **payload}


def _failure(method, exc, elapsed):
    return {
        "method": method, "success": False,
        "error": f"{type(exc).__name__}: {exc}",
        "elapsed_s": float(elapsed),
        "test": None, "extrapolation": {},
    }


def _run_symbolic_condition(eq, condition, eq_seed, train_tuple, extrap):
    override = {"train": train_tuple, "extrapolation": extrap}
    started = time.monotonic()
    try:
        row = abl.run_condition(
            eq, condition, seed=SEED, dataset_override=override,
            wall_clock_limit=COMMON_WALL_CLOCK,
            # The raw PySR baseline used to inherit 1,100s internally while
            # the four-way arm was killed at 900s. Align its Julia-side timeout
            # with the arm budget; leave the Hybrid retry profile untouched.
            timeout_secs=(PYSR_ONLY_FIT_TIMEOUT if condition == "pysr_only" else None),
        )
    except Exception as exc:
        return _failure(
            "hybrid_llm_pysr" if condition == "hypatia" else "pysr_only",
            exc, time.monotonic() - started,
        )
    elapsed = time.monotonic() - started
    if condition == "hypatia" and row.get("llm_enabled") is not True:
        return {
            "method": "hybrid_llm_pysr", "success": False,
            "error": "LLM-enabled Hybrid arm was not active",
            "elapsed_s": elapsed, "test": None, "extrapolation": {},
            "diagnostics": row,
        }
    # A configured API key / llm_enabled flag is not proof that an LLM call
    # actually happened: the engine can continue with pure PySR after an LLM
    # proposal failure. Do not score that fallback as the Hybrid treatment.
    if condition == "hypatia" and row.get("llm_called") is not True:
        return {
            "method": "hybrid_llm_pysr", "success": False,
            "error": "Hybrid discovery completed without a successful live LLM response",
            "elapsed_s": elapsed, "test": None, "extrapolation": {},
            "diagnostics": row,
        }
    if condition == "hypatia" and row.get("llm_proposal_generated") is not True:
        return {
            "method": "hybrid_llm_pysr", "success": False,
            "error": "Hybrid discovery completed without a parseable live LLM proposal",
            "elapsed_s": elapsed, "test": None, "extrapolation": {},
            "diagnostics": row,
        }
    if not row.get("success"):
        return {
            "method": "hybrid_llm_pysr" if condition == "hypatia" else "pysr_only",
            "success": False, "error": row.get("error") or row.get("best_expression"),
            "elapsed_s": elapsed, "test": None, "extrapolation": {},
            "diagnostics": row,
        }
    test_values = {
        "r2": row.get("test_r2"),
        "rmse": row.get("test_rmse"),
        "mae": row.get("test_mae"),
    }
    test_metrics_valid = all(
        value is not None and np.isfinite(float(value))
        for value in test_values.values()
    )
    return {
        "method": "hybrid_llm_pysr" if condition == "hypatia" else "pysr_only",
        "success": test_metrics_valid,
        "error": None if test_metrics_valid else "outer test predictor unavailable or metrics undefined",
        "elapsed_s": elapsed,
        "test": {
            **test_values,
            "scope": row.get("test_scope"),
        },
        "extrapolation": {
            regime: {
                "r2": row.get(f"extrap_r2_{regime}"),
                "rmse": row.get(f"extrap_rmse_{regime}"),
                "mae": row.get(f"extrap_mae_{regime}"),
            }
            for regime in ("near", "medium", "far")
        },
        "diagnostics": row,
    }


def _run_llm_only(method, eq, X_train, y_train, X_test, y_test, extrap):
    started = time.monotonic()
    metadata = {
        "equation_name": eq["name"],
        "domain": eq["domain"].lower().replace(" ", "_"),
        "difficulty": eq.get("difficulty", "medium"),
        "benchmark_arm": "llm_only_zero_shot_no_pysr_refinement",
        "information_regime": "zero_shot_task_description_only",
        "training_arrays_used_by_model": False,
    }
    try:
        with abl._Timeout(COMMON_WALL_CLOCK):
            result = method.run(
                description=eq["name"], X=X_train, y=y_train,
                var_names=eq["vars"], metadata=metadata, verbose=False,
            )
    except Exception as exc:
        return _failure("llm_only", exc, time.monotonic() - started)
    elapsed = time.monotonic() - started
    if not result.success:
        return _failure("llm_only", RuntimeError(result.error or "LLM baseline unavailable"), elapsed)
    provenance = dict(result.metadata or {})
    if provenance.get("llm_called") is not True or provenance.get("bypass_kind") != "live":
        return _failure(
            "llm_only",
            RuntimeError("LLM-only arm lacks verified live-API provenance"),
            elapsed,
        )
    if provenance.get("is_hardcoded") is True:
        return _failure("llm_only", RuntimeError("hardcoded formula is forbidden in LLM-only arm"), elapsed)
    code = result.formula_full or result.formula
    y_pred = None
    try:
        y_pred = rcsb._runner_eval_formula(code, X_test, eq["vars"])
        if y_pred is None:
            raise ValueError("LLM formula could not be evaluated on held-out inputs")
        extrap_rows, extrap_errors = {}, {}
        for regime, (X_e, y_e) in extrap.items():
            try:
                pred = rcsb._runner_eval_formula(code, X_e, eq["vars"])
                if pred is None:
                    raise ValueError("formula evaluator returned no predictions")
                extrap_rows[regime] = _metrics(y_e, pred)
            except Exception as regime_exc:
                extrap_rows[regime] = None
                extrap_errors[regime] = f"{type(regime_exc).__name__}: {regime_exc}"
        test_metrics = _metrics(y_test, y_pred)
    except Exception as exc:
        failure = _failure("llm_only", exc, time.monotonic() - started)
        failure["diagnostics"] = {
            "formula": code,
            "formula_hash": result.formula_hash,
            "metadata": dict(result.metadata or {}),
            "failure_stage": "outer_test_formula_evaluation_or_metrics",
            "outer_test_metric_diagnostics": (
                _llm_metric_diagnostics(y_test, y_pred) if y_pred is not None else None
            ),
            "extrapolation_errors": locals().get("extrap_errors", {}),
            "scoring_policy": "canonical R2; catastrophic R2 below -100 remains a failure",
        }
        return failure
    return {
        "method": "llm_only", "success": True, "error": None,
        "elapsed_s": time.monotonic() - started, "test": test_metrics,
        "extrapolation": extrap_rows,
        "diagnostics": {
            "formula": code,
            "formula_hash": result.formula_hash,
            "metadata": dict(result.metadata or {}),
            "extrapolation_errors": extrap_errors,
            "definition": "Zero-shot PureLLMBaseline formula generated from task description/domain/variable names; training arrays are not used for formula generation and are used only for pre-test formula evaluation/eligibility; no PySR refinement",
            "information_regime": "zero_shot_task_description_only",
            "training_arrays_used_by_model": False,
        },
    }


def _run_nn_only(method, eq, X_train, y_train, X_test, y_test, extrap):
    started = time.monotonic()
    metadata = {
        "equation_name": eq["name"],
        "domain": eq["domain"].lower().replace(" ", "_"),
        "difficulty": eq.get("difficulty", "medium"),
        "random_seed": int(SEED + abl.EQ_ID[eq["name"]] * 7),
        "disable_fallback": True,
        "use_all_training_data": True,
        "benchmark_arm": "nn_only",
    }
    try:
        with abl._Timeout(COMMON_WALL_CLOCK):
            result = method.run(
                description=eq["name"], X=X_train, y=y_train,
                var_names=eq["vars"], metadata=metadata, verbose=False,
            )
    except Exception as exc:
        return _failure("nn_only", exc, time.monotonic() - started)
    elapsed = time.monotonic() - started
    predictor = getattr(result, "_predict_fn", None)
    if not result.success or predictor is None:
        return _failure("nn_only", RuntimeError(result.error or "NN predictor unavailable"), elapsed)
    try:
        test_pred = predictor(X_test)
        test_metrics = _metrics(y_test, test_pred)
        extrap_rows, extrap_errors = {}, {}
        for regime, (X_e, y_e) in extrap.items():
            try:
                extrap_rows[regime] = _metrics(y_e, predictor(X_e))
            except Exception as regime_exc:
                extrap_rows[regime] = None
                extrap_errors[regime] = f"{type(regime_exc).__name__}: {regime_exc}"
        return {
            "method": "nn_only", "success": True, "error": None,
            "elapsed_s": time.monotonic() - started, "test": test_metrics,
            "extrapolation": extrap_rows,
            "diagnostics": {
                "extrapolation_errors": extrap_errors,
                "architecture": result.formula,
                "metadata": dict(result.metadata or {}),
                "headline_training_metric_not_used": True,
                "fallbacks_disabled": True,
                "all_shared_training_rows_used": True,
                "internal_heldout_metric": "not_applicable",
            },
        }
    except Exception as exc:
        return _failure("nn_only", exc, time.monotonic() - started)


def _aggregate(checkpoint):
    """Descriptive paired summaries; equation is the independent comparison unit."""
    def _valid_metric(row, metric):
        value = (row or {}).get(metric) if isinstance(row, dict) else None
        try:
            value = float(value)
        except (TypeError, ValueError):
            return None
        return value if np.isfinite(value) else None

    methods = {key: {} for key in METHOD_KEYS}
    method_extrapolation = {key: {} for key in METHOD_KEYS}
    for key in METHOD_KEYS:
        equation_rows = [
            entry for entry in checkpoint.values()
            if isinstance(entry, dict) and isinstance(entry.get("methods"), dict)
        ]
        rows = [entry.get("methods", {}).get(key, {}) for entry in equation_rows]
        failures = {}
        for row in rows:
            if row.get("success") is not True:
                reason = str(row.get("error") or "unspecified failure")
                failures[reason] = failures.get(reason, 0) + 1
        methods[key]["_coverage"] = {
            "n_assigned_equations": len(equation_rows),
            "n_successful_equations": sum(row.get("success") is True for row in rows),
            "n_failed_equations": sum(row.get("success") is not True for row in rows),
            "failure_reasons": failures,
        }
        for metric in ("r2", "rmse", "mae"):
            vals = [
                value for row in rows
                if row.get("success")
                for value in [_valid_metric(row.get("test"), metric)]
                if value is not None
            ]
            methods[key][metric] = {
                "n_equations": len(vals),
                "mean": float(np.mean(vals)) if vals else None,
                "median": float(np.median(vals)) if vals else None,
            }
        for regime in ("near", "medium", "far"):
            method_extrapolation[key][regime] = {}
            for metric in ("r2", "rmse", "mae"):
                vals = [
                    value for row in rows
                    if row.get("success")
                    for value in [_valid_metric((row.get("extrapolation") or {}).get(regime), metric)]
                    if value is not None
                ]
                method_extrapolation[key][regime][metric] = {
                    "n_equations": len(vals),
                    "mean": float(np.mean(vals)) if vals else None,
                    "median": float(np.median(vals)) if vals else None,
                }

    def _paired(competitor, metric, regime=None):
        differences, per_equation = [], []
        for entry in checkpoint.values():
            if not isinstance(entry, dict):
                continue
            arms = entry.get("methods", {})
            hybrid, other = arms.get("hybrid_llm_pysr", {}), arms.get(competitor, {})
            if not (hybrid.get("success") and other.get("success")):
                continue
            hrow = (hybrid.get("extrapolation") or {}).get(regime) if regime else hybrid.get("test")
            orow = (other.get("extrapolation") or {}).get(regime) if regime else other.get("test")
            hv, ov = _valid_metric(hrow, metric), _valid_metric(orow, metric)
            if hv is None or ov is None:
                continue
            delta = hv - ov if metric == "r2" else ov - hv
            differences.append(delta)
            per_equation.append({
                "equation": entry.get("name"),
                "domain": entry.get("domain"),
                "difference_favoring_hybrid": delta,
            })
        n = len(differences)
        mean = float(np.mean(differences)) if n else None
        sd = float(np.std(differences, ddof=1)) if n > 1 else None
        ci = None
        if n > 1:
            try:
                from scipy.stats import t as student_t
                critical = float(student_t.ppf(0.975, df=n - 1))
                half = critical * sd / np.sqrt(n)
                ci = [mean - half, mean + half]
            except Exception:
                ci = None
        tol = 1e-12
        total_equations = sum(
            isinstance(entry, dict) and isinstance(entry.get("methods"), dict)
            for entry in checkpoint.values()
        )
        return {
            "comparison_status": "complete" if n == total_equations else "partial",
            "n_total_equations": total_equations,
            "n_paired_equations": n,
            "paired_coverage_fraction": (n / total_equations) if total_equations else None,
            "mean_paired_difference_favoring_hybrid": mean,
            "sd_paired_difference": sd,
            "descriptive_95pct_t_interval": ci,
            "hybrid_wins": sum(v > tol for v in differences),
            "ties": sum(abs(v) <= tol for v in differences),
            "hybrid_losses": sum(v < -tol for v in differences),
            "per_equation": per_equation,
            "direction": "positive favors Hybrid",
        }

    paired_test, paired_extrapolation = {}, {}
    for competitor in ("llm_only", "pysr_only", "nn_only"):
        paired_test[competitor] = {
            metric: _paired(competitor, metric)
            for metric in ("r2", "rmse", "mae")
        }
        paired_extrapolation[competitor] = {
            regime: {
                metric: _paired(competitor, metric, regime=regime)
                for metric in ("r2", "rmse", "mae")
            }
            for regime in ("near", "medium", "far")
        }
    total_equations = sum(
        isinstance(entry, dict) and isinstance(entry.get("methods"), dict)
        for entry in checkpoint.values()
    )
    all_arms_complete = all(
        methods[key]["_coverage"]["n_successful_equations"] == total_equations
        for key in METHOD_KEYS
    )
    return {
        "comparison_status": "complete" if all_arms_complete else "partial",
        "all_arms_successful": all_arms_complete,
        "n_total_equations": total_equations,
        "independent_unit": "equation (paired within equation; not individual generated samples)",
        "method_test_metrics": methods,
        "paired_hybrid_comparisons": paired_test,
        "paired_hybrid_test_comparisons": paired_test,
        "method_extrapolation_metrics": method_extrapolation,
        "paired_hybrid_extrapolation_comparisons": paired_extrapolation,
        "interpretation": (
            "Descriptive paired summaries only; do not infer universal Hybrid superiority. "
            "Each metric/regime reports its own available-equation denominator; missing or "
            "failed extrapolation predictions are excluded from that metric's denominator."
        ),
    }

def run():
    if not os.environ.get("ANTHROPIC_API_KEY", "").startswith("sk-"):
        raise RuntimeError("ANTHROPIC_API_KEY is required for a genuine four-arm run; refusing silent Hybrid downgrade")
    run_fingerprint = _run_fingerprint()
    checkpoint = {}
    if CHECKPOINT_PATH.exists() and os.environ.get("CLEAR_CHECKPOINT") == "1":
        backup_dir = OUT_DIR / "checkpoint_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"exp1_four_way_matched_checkpoint_{int(time.time())}.json"
        backup_path.write_bytes(CHECKPOINT_PATH.read_bytes())
        print(f"[four-way] clean rerun: archived prior checkpoint to {backup_path}")
    if CHECKPOINT_PATH.exists() and os.environ.get("CLEAR_CHECKPOINT") != "1":
        with CHECKPOINT_PATH.open(encoding="utf-8") as handle:
            checkpoint = json.load(handle)
        if not isinstance(checkpoint, dict):
            raise RuntimeError("Checkpoint root must be a JSON object; use a fresh output directory")
        prior_metadata = checkpoint.get("__run_metadata__")
        has_equation_rows = any(key != "__run_metadata__" for key in checkpoint)
        if has_equation_rows and prior_metadata is None:
            raise RuntimeError(
                "Existing checkpoint has no run fingerprint; refusing unsafe legacy resume. "
                "Use a fresh output directory."
            )
        if prior_metadata is not None and prior_metadata != run_fingerprint:
            raise RuntimeError(
                "Checkpoint driver/protocol/settings fingerprint mismatch; "
                "use a fresh output directory rather than mixing runs."
            )
    checkpoint["__run_metadata__"] = run_fingerprint

    llm_method = rcsb.PureLLMBaselineMethod(
        verbose=False, no_cache=os.environ.get("NO_LLM_CACHE", "1") == "1"
    )
    nn_method = rcsb.ImprovedNNMethod(verbose=False, nn_seeds=1)

    shard = int(os.environ.get("SHARD_INDEX", os.environ.get("SHARD", "0")))
    task_ids_raw = os.environ.get("TASK_IDS", "").strip()
    if task_ids_raw:
        requested_ids = [item for item in task_ids_raw.split() if item]
        if len(requested_ids) != len(set(requested_ids)):
            raise ValueError("TASK_IDS contains duplicate Core-15 equation IDs")
        valid_ids = {str(i) for i in range(len(abl.CORE_15))}
        unknown = sorted(set(requested_ids) - valid_ids)
        if unknown:
            raise ValueError(f"Unknown Core-15 equation task IDs: {unknown}; expected 0..14")
        selected = {int(item) for item in requested_ids}
    else:
        selected = set(range(len(abl.CORE_15)))
    equations = [(i, eq) for i, eq in enumerate(abl.CORE_15) if i in selected]
    if not equations:
        raise ValueError("No Core-15 equations assigned to this worker")

    for eq_idx, eq in equations:
        key = str(abl.EQ_ID[eq["name"]])
        existing = checkpoint.setdefault(key, {
            "name": eq["name"], "domain": eq["domain"],
            "seed": SEED, "methods": {},
        })
        if not isinstance(existing, dict):
            raise RuntimeError(
                f"Checkpoint row is malformed for {eq['name']}; "
                "use a fresh output directory rather than reusing partial results."
            )
        prior_methods = existing.get("methods", {})
        if not isinstance(prior_methods, dict):
            raise RuntimeError(
                f"Checkpoint methods are malformed for {eq['name']}; "
                "use a fresh output directory rather than reusing partial results."
            )
        eq_seed = SEED + abl.EQ_ID[eq["name"]] * 7
        train_tuple = abl.generate_data(
            eq, N=N_TRAIN_SOURCE, noise_level=NOISE_LEVEL, seed=eq_seed
        )
        X_train, X_test, y_train, y_test, X_all, y_all = train_tuple
        extrap = {
            regime: abl.generate_extrap_data(eq, regime=regime, N=N_EXTRAP, seed=eq_seed)
            for regime, _ in abl.EXTRAP_REGIMES
        }

        if existing.get("seed") != SEED:
            raise RuntimeError(f"Checkpoint seed mismatch for {eq['name']}; use a fresh output directory")
        expected_split = {
            "train_data_sha256": _array_hash(X_train, y_train),
            "outer_test_sha256": _array_hash(X_test, y_test),
            "extrapolation_sha256": {
                regime: _array_hash(X_e, y_e) for regime, (X_e, y_e) in extrap.items()
            },
        }
        prior_split = existing.get("split")
        has_successful_prior_arm = (
            isinstance(prior_methods, dict)
            and any(
                isinstance(row, dict) and row.get("success") is True
                for row in prior_methods.values()
            )
        )
        if prior_split is None and has_successful_prior_arm:
            raise RuntimeError(
                f"Checkpoint has successful arm results but no dataset fingerprints for {eq['name']}; "
                "refusing to reuse scores without proving dataset identity. Use a fresh output directory."
            )
        if prior_split is not None and not isinstance(prior_split, dict):
            raise RuntimeError(
                f"Checkpoint split metadata is malformed for {eq['name']}; "
                "use a fresh output directory rather than mixing results."
            )
        if isinstance(prior_split, dict):
            for field, expected in expected_split.items():
                if prior_split.get(field) != expected:
                    raise RuntimeError(
                        f"Checkpoint {field} mismatch for {eq['name']}; "
                        "do not mix results from different generated datasets"
                    )
        arms = existing.setdefault("methods", {})
        if not isinstance(arms.get("hybrid_llm_pysr"), dict) or not arms["hybrid_llm_pysr"].get("success"):
            arms["hybrid_llm_pysr"] = _run_symbolic_condition(
                eq, "hypatia", eq_seed, train_tuple, extrap
            )
        if not isinstance(arms.get("pysr_only"), dict) or not arms["pysr_only"].get("success"):
            arms["pysr_only"] = _run_symbolic_condition(
                eq, "pysr_only", eq_seed, train_tuple, extrap
            )
        if not isinstance(arms.get("llm_only"), dict) or not arms["llm_only"].get("success"):
            arms["llm_only"] = _run_llm_only(
                llm_method, eq, X_train, y_train, X_test, y_test, extrap
            )
        if not isinstance(arms.get("nn_only"), dict) or not arms["nn_only"].get("success"):
            arms["nn_only"] = _run_nn_only(
                nn_method, eq, X_train, y_train, X_test, y_test, extrap
            )

        existing["split"] = {
            "generator": "exp1_ablation.generate_data",
            "train_data_sha256": _array_hash(X_train, y_train),
            "outer_test_sha256": _array_hash(X_test, y_test),
            "n_source_samples": N_TRAIN_SOURCE,
            "n_train": int(len(X_train)), "n_test": int(len(X_test)),
            "noise_level": NOISE_LEVEL, "equation_seed": eq_seed,
            "test_partition_used_for_fit_or_selection": False,
            "extrapolation_sha256": {
                regime: _array_hash(X_e, y_e) for regime, (X_e, y_e) in extrap.items()
            },
        }
        existing["methods"] = arms
        checkpoint[key] = existing
        tmp = CHECKPOINT_PATH.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            json.dump(_json_safe(checkpoint), handle, indent=2, allow_nan=False)
        os.replace(tmp, CHECKPOINT_PATH)
        print(f"[four-way] {eq_idx + 1}/{len(abl.CORE_15)} {eq['name']} checkpointed")

    with RESULTS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(checkpoint), handle, indent=2, allow_nan=False)
    summary = _aggregate(checkpoint)
    smoke_test = os.environ.get("FOUR_WAY_SMOKE") == "1"
    summary["smoke_test"] = smoke_test
    summary["official_aggregate_eligible"] = not smoke_test
    if smoke_test:
        summary["smoke_scope"] = "single equation; worker-path validation only; not a Core-15 aggregate"
    with SUMMARY_PATH.open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(summary), handle, indent=2, allow_nan=False)
    manifest = {
        "protocol": "Core-15 matched four-arm predictive comparison",
        "smoke_test": smoke_test,
        "official_aggregate_eligible": not smoke_test,
        "smoke_scope": "single equation; worker-path validation only; not a Core-15 aggregate" if smoke_test else None,
        "run_fingerprint": run_fingerprint,
        "seed": SEED, "noise_level": NOISE_LEVEL,
        "common_method_wall_clock_seconds": COMMON_WALL_CLOCK,
        "n_source_samples": N_TRAIN_SOURCE, "n_extrapolation_samples": N_EXTRAP,
        "arms": list(METHOD_KEYS),
        "shard_index": int(os.environ.get("SHARD_INDEX", os.environ.get("SHARD", "0"))),
        "assigned_equation_ids": [str(i) for i, _ in equations],
        "arm_definitions": {
            "hybrid_llm_pysr": "Core-15 HybridDiscoverySystem with LLM enabled and PySR refinement",
            "llm_only": "Zero-shot PureLLMBaseline formula generated from task description/domain/variable names; training arrays are not used for formula generation and are used only for pre-test formula evaluation/eligibility; no PySR refinement; live API provenance required",
            "pysr_only": "raw PySRRegressor with no LLM proposal",
            "nn_only": "ImprovedNN neural network with log preprocessing; OLS and secondary NN fallbacks disabled",
        },
        "primary_metrics": ["test.r2", "test.rmse", "test.mae"],
        "test_policy": "same untouched outer test rows per equation and seed",
        "budget_policy": "same nominal arm wall-clock; raw PySR internal fit timeout is capped at arm wall-clock minus 60s so Julia exits before the outer guard; Hybrid retry profile is unchanged",
        "pysr_only_fit_timeout_seconds": PYSR_ONLY_FIT_TIMEOUT,
        "pysr_only_niterations": abl.NITERATIONS,
        "pysr_only_populations": abl.POPULATIONS,
        "timeout_scope": "main generation/training stage only; prediction/scoring is outside timeout context; this is not a strict end-to-end wall-clock cap",
        "elapsed_time_scope": "elapsed_s covers the complete arm call through outer-test and all extrapolation prediction/scoring, including partial-regime failures; it is observational and does not enforce a timeout",
        "success_semantics": "success means the primary untouched outer-test prediction and all three primary metrics are valid; extrapolation metrics are independently nullable and summarized with per-regime available-equation denominators",
        "extrapolation_regimes": ["near", "medium", "far"],
        "extrapolation_metrics": ["r2", "rmse", "mae"],
        "routing_tau": "null; ensemble fallback; no calibrated routing claim",
        "ablation_scope": "not run by this driver; three-gate leave-one-out remains deferred pending a fresh Phase 2 closure manifest and Phase 3 preflight; three other gates are unavailable in HDS v50_2",
        "source_paths": [
            "hypatiax/experiments/benchmarks/exp1_four_way_matched.py",
            "hypatiax/experiments/benchmarks/exp1_ablation.py",
            "hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py",
            "hypatiax/safe_formula.py",
            "hypatiax/core/r2_canonical.py",
            "hypatiax/core/base_pure_llm/baseline_pure_llm_defi_discovery.py",
            "hypatiax/core/llm_call.py",
            "hypatiax/core/training/baseline_neural_network_defi_improved.py",
            "hypatiax/tools/symbolic/symbolic_engine.py",
            "hypatiax/tools/symbolic/hybrid_system_v50_2.py",
            "hypatiax/core/enforce_flags.py",
        ],
        "summary_file": str(SUMMARY_PATH),
        "results_file": str(RESULTS_PATH),
        "checkpoint_file": str(CHECKPOINT_PATH),
        "execution_status": "runner_completed",
    }
    with MANIFEST_PATH.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
    return checkpoint


if __name__ == "__main__":
    run()
