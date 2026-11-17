"""
extrap_r2_far.py
================
Extracted from run_comparative_suite_benchmark_v2.py

Compatibility entry point for the Exp2 far-extrapolation helpers.

All split, formula-evaluation, metric, and diagnostic logic lives in the
lightweight exp2_extrapolation_core module and is re-exported here for
legacy callers. This module also retains the historical standalone runner
configuration below; new code should import the shared core directly.
"""

from __future__ import annotations

import math
import os
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np



# Ensure direct script execution can resolve the repository package.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Canonical shared implementation used by both Exp2 Feynman runners.
from hypatiax.experiments.benchmarks.exp2_extrapolation_core import (
    REGIMES,
    ExtrapolationRegime,
    calculate_extrapolation_error,
    extrapolation_error_status,
    build_extrap_split,
    _runner_eval_formula,
    _far_r2,
    _far_rmse,
    compute_extrap_r2_far,
)

# ──────────────────────────────────────────────────────────────────────────────
# Usage example (matches how it is wired in the benchmark)
# ──────────────────────────────────────────────────────────────────────────────
#
#   # --- pre-processing loop (before running methods) ---
#   X_train, y_train, X_far, y_far, extrap_meta = build_extrap_split(
#       X, y,
#       description = description,
#       train_frac  = args.extrap_train_frac,   # default 0.8
#       multiplier  = args.extrap_multiplier,    # default 2.0
#   )
#   metadata = {**metadata, **extrap_meta}
#
#   # --- after all methods have run on (X_train, y_train) ---
#   extrap_r2_far, extrap_rmse_far, extrap_error_pct = compute_extrap_r2_far(
#       results      = results,           # {name: MethodResult}
#       X_far        = X_far,
#       y_far        = y_far,
#       var_names    = var_names,
#       y_train      = y_train,           # NEW: needed for error_%
#       y_pred_train = y_pred_train_dict, # NEW: {method: train preds}
#       diagnostics  = extrap_diagnostics,
#       verbose      = True,
#   )
#
#   # --- assemble record ---
#   record["extrap_r2_far"]      = extrap_r2_far
#   record["extrap_rmse_far"]    = extrap_rmse_far
#   record["extrapolation_score"] = {
#       name: (extrap_diagnostics.get(name) or {}).get("extrapolation_score")
#       for name in results
#   }  # primary: RMSE_far / std(y_train)
#   record["extrapolation_score_status"] = {
#       name: (extrap_diagnostics.get(name) or {}).get("extrap_nrmse_far_status")
#       for name in results
#   }
#   record["extrap_error_pct"]   = extrap_error_pct  # legacy compatibility
#   record["extrap_train_frac"]  = metadata.get("extrap_train_frac")
#   record["extrap_multiplier"]  = metadata.get("extrap_multiplier")
#   record["extrap_n_train"]     = metadata.get("extrap_n_train")
#   record["extrap_n_test"]      = metadata.get("extrap_n_test")
#   record["extrap_x_train_max"] = metadata.get("extrap_x_train_max")
#   record["extrap_far_ceiling"] = metadata.get("extrap_far_ceiling")

# ---------------------------------------------------------------------------
# Module-level reproducibility seeds (matches the rest of the project).
# ---------------------------------------------------------------------------
random.seed(42)
np.random.seed(42)

# ---------------------------------------------------------------------------
# HYPATIAX_NOISE_LEVEL — injected by run_noise_sweep_benchmark.py orchestrator.
# When present, real Gaussian noise scaled to σ * std(y) is added to every
# test case's y values after load_test_data().  When absent (or 0.0), this
# script runs in its usual noiseless-or-fixed-noisy mode.
# ---------------------------------------------------------------------------
_HYPATIAX_NOISE_LEVEL: float = 0.0
_raw_noise_env = os.environ.get("HYPATIAX_NOISE_LEVEL", "").strip()
if _raw_noise_env:
    try:
        _HYPATIAX_NOISE_LEVEL = float(_raw_noise_env)
    except ValueError:
        print(f"WARNING: Could not parse HYPATIAX_NOISE_LEVEL={_raw_noise_env!r} — defaulting to 0.0")

# ---------------------------------------------------------------------------
# FEATURE-NSHARDS-SUFFIX (corrected 2026-06-23) — injected by
# run_noise_sweep_benchmark.py / run_sample_complexity_benchmark.py
# orchestrators, forwarded from run_all.sh's per-shard SHARD_INDEX (1-based,
# zero-padded), NOT the total shard count. When present, every output
# filename this script writes (protocol_core_*.json, benchmark_results.json,
# benchmark_results_extrap.json) gets "_nshardsNN" appended before the
# extension, where NN distinguishes THIS shard from every other
# concurrently-running shard in the same matrix run — necessary because all
# shards share the same --output-dir and write second-granularity
# timestamped filenames, so same-second saves from different shards would
# otherwise collide. Empty string when unset (e.g. local runs, or any other
# orchestrator that doesn't set it) — filenames are then unchanged from
# before this feature.
# ---------------------------------------------------------------------------
_SHARD_ID = os.environ.get("HYPATIAX_SHARD_ID", "").strip()
_SHARD_TAG = f"_shrd{_SHARD_ID}" if _SHARD_ID else ""

# PySR subprocess timeout — overridden by --pysr-timeout at runtime.
# Paper-quality default (repro.yaml timeouts.feynman_pysr_seconds = 1100).
_PYSR_TIMEOUT: int = 1100

# ---------------------------------------------------------------------------
# Path setup.
# This file lives at hypatiax/experiments/benchmarks/
# Package root is three levels up.
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent        # …/experiments/benchmarks/
_PKG_ROOT = _HERE.parent.parent                # …/hypatiax/
sys.path.insert(0, str(_PKG_ROOT.parent))      # parent of hypatiax/ → import hypatiax.*

# Checkpoint file stem — overridden at runtime via --checkpoint-name so the
# orchestrator can give each condition (noisy/noiseless) its own file and
# prevent the two passes from colliding on the same JSON.
_CHECKPOINT_NAME: str = "protocol_core_checkpoint"
_RESULTS_ROOT: Path = Path(
    os.environ.get("RESULTS_DIR", str(_PKG_ROOT / "data/results"))
).expanduser().resolve()
_OUTPUT_DIR: Path = _RESULTS_ROOT / "comparison_results"
# _FLAT_OUTPUT_DIR: always the configured comparison_results/ root — never overridden by
# --output-dir.  benchmark_results.json lands here so it is NOT buried or
# clobbered across multi-run sweeps (noise-sweep/, sample-complexity/).
# Checkpoints also land here.
# NOTE: benchmark_results_extrap.json no longer uses this — see the
# FIX-EXTRAP-OUTPUT-DIR comment near its write site — it now uses
# _OUTPUT_DIR (honors --output-dir) so it lands alongside
# protocol_core_extrap_*.json in the per-experiment directory.
_FLAT_OUTPUT_DIR: Path = _RESULTS_ROOT / "comparison_results"

# ---------------------------------------------------------------------------
# juliacall MUST be imported before torch to prevent a segfault when PySR
# (which uses Julia via juliacall) and PyTorch are both present.
# See https://github.com/pytorch/pytorch/issues/78829
#
# IMPORTANT: this import must happen before ANY call that could transitively
# load torch — including the _probe() availability checks below.
#
# NOTE: PYTHON_JULIACALL_HANDLE_SIGNALS is set above (via os.environ) so
# it is guaranteed to be in the environment when juliacall reads it here.
# ---------------------------------------------------------------------------
try:
    import juliacall  # noqa: F401
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Optional heavy imports — torch / sklearn.
# Load torch NOW (eagerly, after juliacall) so that the _probe() calls below
# do not trigger torch's first import after Julia is already initialised,
# which is the sequence that causes the segfault.
# ---------------------------------------------------------------------------
try:
    import torch
    import torch.nn as nn
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    TORCH_AVAILABLE = True

    # FIX-ISSUE2-DETERMINISM (follow-up to FIX-ISSUE2-UNSEEDED-NN): seeding
    # via the sha256-derived-seed -> torch.manual_seed() pattern (see
    # _nn_residual_fit, both copies) fixes *seed derivation*, but does not by itself make
    # PyTorch's CPU kernels deterministic. Confirmed against a live CI run
    # (workflow_dispatch 31256573694): after exporting OMP_NUM_THREADS=1 /
    # MKL_NUM_THREADS=1 / OPENBLAS_NUM_THREADS=1 at the shell level (see
    # run_issue2b_experiment.sh), HSL/M4 still showed a ~1e-6 R^2 spread on
    # at least one equation. Two gaps: (1) env-var thread pinning at process
    # start is not guaranteed to fully constrain ATen's own internal thread
    # pool the way an explicit in-process call does; (2) without
    # use_deterministic_algorithms, some CPU ops can still choose a
    # non-deterministic reduction path independent of thread count. Setting
    # both explicitly, in-process, right after import and before any model
    # is constructed, closes both gaps. warn_only=True rather than the
    # strict default: this codebase doesn't use any op lacking a
    # deterministic CPU implementation (plain Linear/Tanh MLPs), so a hard
    # RuntimeError isn't needed, but if that assumption ever breaks, warn
    # mode still surfaces it in the log instead of the run silently
    # continuing non-deterministic.
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True, warn_only=True)
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠️  torch / sklearn not available — NN-based methods will be skipped")

# ---------------------------------------------------------------------------
# Anthropic client
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    for _env in [_HERE / ".env", _HERE.parent / ".env", _PKG_ROOT / ".env"]:
        if _env.exists():
            load_dotenv(dotenv_path=_env, override=True)
            print(f"✅ Loaded .env from {_env}")
            break
except ImportError:
    pass

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = bool(os.getenv("ANTHROPIC_API_KEY"))
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  anthropic library not available — LLM-based methods will fall back")


# ============================================================================
# CORE SCRIPT AVAILABILITY PROBES
# All imports are lazy (inside each method's __init__) so that a missing
# optional core module only disables that method, not the whole script.
# ============================================================================
