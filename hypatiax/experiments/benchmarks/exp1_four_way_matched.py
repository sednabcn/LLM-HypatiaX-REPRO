"""
Matched Core-15 four-arm predictive comparison.

Primary arms:
  hybrid_llm_pysr : exp1_ablation.run_condition("hypatia")
  llm_only        : PureLLMBaselineMethod formula, no symbolic refinement
  pysr_only       : exp1_ablation.run_condition("pysr_only")
  nn_only         : ImprovedNNMethod

Every arm receives the same equation/seed training arrays. The outer test
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
NOISE_LEVEL = float(os.environ.get("FOUR_WAY_NOISE_LEVEL", "0.05"))
N_TRAIN_SOURCE = int(os.environ.get("FOUR_WAY_N_SAMPLES", "200"))
N_EXTRAP = int(os.environ.get("FOUR_WAY_N_EXTRAP", "100"))
OUT_DIR = Path(os.environ.get("RESULTS_DIR", str(Path.cwd()))) / "four_way_matched"
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
    if yt.shape != yp.shape or yt.size == 0 or not np.all(np.isfinite(yp)):
        raise ValueError("prediction shape mismatch or non-finite predictions")
    return {
        "r2": abl._safe_r2(yt, yp),
        "rmse": abl._safe_rmse(yt, yp),
        "mae": abl._safe_mae(yt, yp),
    }


def _array_hash(*arrays):
    digest = hashlib.sha256()
    for array in arrays:
        value = np.ascontiguousarray(np.asarray(array, dtype=np.float64))
        digest.update(str(value.shape).encode("ascii"))
        digest.update(value.tobytes())
    return digest.hexdigest()


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
    if not row.get("success"):
        return {
            "method": "hybrid_llm_pysr" if condition == "hypatia" else "pysr_only",
            "success": False, "error": row.get("error") or row.get("best_expression"),
            "elapsed_s": elapsed, "test": None, "extrapolation": {},
            "diagnostics": row,
        }
    return {
        "method": "hybrid_llm_pysr" if condition == "hypatia" else "pysr_only",
        "success": row.get("test_r2") is not None,
        "error": None if row.get("test_r2") is not None else "outer test predictor unavailable",
        "elapsed_s": elapsed,
        "test": {
            "r2": row.get("test_r2"),
            "rmse": row.get("test_rmse"),
            "mae": row.get("test_mae"),
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
        "benchmark_arm": "llm_only_no_pysr_refinement",
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
    try:
        y_pred = rcsb._runner_eval_formula(code, X_test, eq["vars"])
        if y_pred is None:
            raise ValueError("LLM formula could not be evaluated on held-out inputs")
        extrap_rows = {}
        for regime, (X_e, y_e) in extrap.items():
            pred = rcsb._runner_eval_formula(code, X_e, eq["vars"])
            extrap_rows[regime] = _metrics(y_e, pred) if pred is not None else None
        test_metrics = _metrics(y_test, y_pred)
    except Exception as exc:
        return _failure("llm_only", exc, elapsed)
    return {
        "method": "llm_only", "success": True, "error": None,
        "elapsed_s": elapsed, "test": test_metrics,
        "extrapolation": extrap_rows,
        "diagnostics": {
            "formula": code,
            "formula_hash": result.formula_hash,
            "metadata": dict(result.metadata or {}),
            "definition": "PureLLMBaseline formula; no PySR refinement",
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
        extrap_rows = {
            regime: _metrics(y_e, predictor(X_e))
            for regime, (X_e, y_e) in extrap.items()
        }
        return {
            "method": "nn_only", "success": True, "error": None,
            "elapsed_s": elapsed, "test": _metrics(y_test, test_pred),
            "extrapolation": extrap_rows,
            "diagnostics": {
                "architecture": result.formula,
                "metadata": dict(result.metadata or {}),
                "headline_training_metric_not_used": True,
                "fallbacks_disabled": True,
            },
        }
    except Exception as exc:
        return _failure("nn_only", exc, elapsed)


def _aggregate(checkpoint):
    """Descriptive paired summaries; equation is the independent comparison unit."""
    methods = {key: {} for key in METHOD_KEYS}
    for key in METHOD_KEYS:
        rows = [
            entry.get("methods", {}).get(key, {})
            for entry in checkpoint.values() if isinstance(entry, dict)
        ]
        for metric in ("r2", "rmse", "mae"):
            vals = [
                float(row["test"][metric])
                for row in rows
                if row.get("success") and isinstance(row.get("test"), dict)
                and row["test"].get(metric) is not None
                and np.isfinite(float(row["test"][metric]))
            ]
            methods[key][metric] = {
                "n_equations": len(vals),
                "mean": float(np.mean(vals)) if vals else None,
                "median": float(np.median(vals)) if vals else None,
            }

    paired = {}
    for competitor in ("llm_only", "pysr_only", "nn_only"):
        paired[competitor] = {}
        for metric, direction in (("r2", "higher"), ("rmse", "lower"), ("mae", "lower")):
            differences = []
            per_equation = []
            for entry in checkpoint.values():
                if not isinstance(entry, dict):
                    continue
                arms = entry.get("methods", {})
                h = arms.get("hybrid_llm_pysr", {})
                other = arms.get(competitor, {})
                if not (h.get("success") and other.get("success")):
                    continue
                hv = (h.get("test") or {}).get(metric)
                ov = (other.get("test") or {}).get(metric)
                if hv is None or ov is None:
                    continue
                hv, ov = float(hv), float(ov)
                if np.isfinite(hv) and np.isfinite(ov):
                    delta = hv - ov if direction == "higher" else ov - hv
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
            paired[competitor][metric] = {
                "n_paired_equations": n,
                "mean_paired_difference_favoring_hybrid": mean,
                "sd_paired_difference": sd,
                "descriptive_95pct_t_interval": ci,
                "hybrid_wins": sum(v > tol for v in differences),
                "ties": sum(abs(v) <= tol for v in differences),
                "hybrid_losses": sum(v < -tol for v in differences),
                "per_equation": per_equation,
                "direction": "positive favors Hybrid",
            }
    return {
        "independent_unit": "equation (paired within equation; not individual generated samples)",
        "method_test_metrics": methods,
        "paired_hybrid_comparisons": paired,
        "interpretation": "Descriptive paired summaries only; do not infer universal Hybrid superiority. Report missing/failed arms and small n.",
    }


def run():
    if not os.environ.get("ANTHROPIC_API_KEY", "").startswith("sk-"):
        raise RuntimeError("ANTHROPIC_API_KEY is required for a genuine four-arm run; refusing silent Hybrid downgrade")
    checkpoint = {}
    if CHECKPOINT_PATH.exists():
        with CHECKPOINT_PATH.open(encoding="utf-8") as handle:
            checkpoint = json.load(handle)

    llm_method = rcsb.PureLLMBaselineMethod(
        verbose=False, no_cache=os.environ.get("NO_LLM_CACHE", "1") == "1"
    )
    nn_method = rcsb.ImprovedNNMethod(verbose=False, nn_seeds=1)

    shard = int(os.environ.get("SHARD_INDEX", os.environ.get("SHARD", "0")))
    shards = max(1, int(os.environ.get("N_SHARDS", "1")))
    equations = [
        (i, eq) for i, eq in enumerate(abl.CORE_15)
        if i % shards == shard
    ]

    for eq_idx, eq in equations:
        key = str(abl.EQ_ID[eq["name"]])
        existing = checkpoint.setdefault(key, {
            "name": eq["name"], "domain": eq["domain"],
            "seed": SEED, "methods": {},
        })
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
    with SUMMARY_PATH.open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(summary), handle, indent=2, allow_nan=False)
    manifest = {
        "protocol": "Core-15 matched four-arm predictive comparison",
        "seed": SEED, "noise_level": NOISE_LEVEL,
        "common_method_wall_clock_seconds": COMMON_WALL_CLOCK,
        "n_source_samples": N_TRAIN_SOURCE, "n_extrapolation_samples": N_EXTRAP,
        "arms": list(METHOD_KEYS),
        "arm_definitions": {
            "hybrid_llm_pysr": "Core-15 HybridDiscoverySystem with LLM enabled and PySR refinement",
            "llm_only": "PureLLMBaseline generated formula; no PySR refinement; live API provenance required",
            "pysr_only": "raw PySRRegressor with no LLM proposal",
            "nn_only": "ImprovedNN neural network with log preprocessing; OLS and secondary NN fallbacks disabled",
        },
        "primary_metrics": ["test.r2", "test.rmse", "test.mae"],
        "test_policy": "same untouched outer test rows per equation and seed",
        "budget_policy": "same per-arm wall-clock cap; PySR population/iteration settings inherited from frozen rerun config",
        "extrapolation_regimes": ["near", "medium", "far"],
        "extrapolation_metrics": ["r2", "rmse", "mae"],
        "routing_tau": "null; ensemble fallback; no calibrated routing claim",
        "ablation_scope": "not run by this driver; three-gate leave-one-out remains deferred pending a fresh Phase 2 closure manifest and Phase 3 preflight; three other gates are unavailable in HDS v50_2",
        "source_paths": [
            "hypatiax/experiments/benchmarks/exp1_ablation.py",
            "hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py",
        ],
        "summary_file": str(SUMMARY_PATH),
        "results_file": str(RESULTS_PATH),
        "checkpoint_file": str(CHECKPOINT_PATH),
        "execution_status": "not_run_by_source_implementation",
    }
    with MANIFEST_PATH.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
    return checkpoint


if __name__ == "__main__":
    run()
