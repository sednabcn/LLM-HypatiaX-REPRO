#!/usr/bin/env python3
"""
exp3_nguyen12_hybrid50v_consolidated.py  —  Exp 3 · Nguyen-12 SR suite (§10.8 primary)
================================================================================
Standalone Python script version — safe to run with `python3` directly.

CONSOLIDATION NOTE (this file)
-------------------------------
The four prior scripts in this benchmark (_02.py, _02_patched.py,
_02_patched_extrap_safe.py, _03.py) were two fix lineages that never got
merged: branch A (_02_patched -> _02_patched_extrap_safe) added the PySR
hall-of-fame trajectory monitor and boundary-buffer extrapolation-safety
fix; branch B (_03, renamed from _02) added --temperature/--n-candidates
CLI flags, per-run output filenames, and a repo-root off-by-one fix. This
file merges both lineages onto branch A's base (the more complete one on
the trajectory/extrapolation-safety axis) and additionally fixes several
bugs found during a full audit (see audit-exp3.txt) that were present,
unfixed, in ALL four prior scripts:
  [FIX-N3-ii-*]      branch B's CLI flags, filenames, config logging, and
                      repo-root fix — ported in, INCLUDING fixing the
                      off-by-one in the ImportError fallback path that
                      _03.py itself missed (audit #4).
  [FIX-CACHE-SCHEMA]  addresses audit #2 — a cache file is only reused if
                      it carries a matching schema_version; otherwise it's
                      treated as stale and re-run, instead of silently
                      returning a differently-defined "r2" from an older
                      script version.
  [FIX-SEED-ZERO]     addresses audit #6 — an explicit seed of 0 is no
                      longer silently replaced by the argparse default.
  [FIX-MANAGER-LEAK]  addresses audit #7 — mp.Manager() is now explicitly
                      shut down in a try/finally.
  [FIX-STALE-CLAIM]   addresses audit #3 — the unverified 11/12 H (91.7%)
                      headline figure is no longer asserted as this
                      script's expected result; it's reported as an
                      unverified, different-metric prior figure instead.
  [FIX-LLM-WARMSTART] addresses audit #1 — RESOLVED (was KNOWN-BUG-1,
                      "NOT FIXED HERE", in the prior revision of this
                      file). llm_exprs (the LLM warm-start candidates) are
                      now converted to PySR `guesses`-compatible strings
                      (see _llm_exprs_to_pysr_guesses /
                      _sympy_pow_to_pysr_str) and actually passed into
                      model_h.fit(..., guesses=...) for the "H" run only
                      [FIX-LLM-WARMSTART-GATE: a subsequent pass caught
                      that `guesses` is a fit()-level parameter in this
                      pysr build, not a PySRRegressor constructor
                      argument as an intermediate revision assumed; the
                      guard and call site below check/pass it accordingly]
                      — "P" still fits unseeded, so H and P are now a
                      genuine hybrid-vs-baseline comparison instead of the
                      same PySR fit run twice. This was an explicit,
                      owner-approved decision to change what the
                      experiment measures (per the prior note's own
                      caveat that this call belonged to whoever owns
                      §10.8's results, not to a silent consolidation-pass
                      fix) — see the CHANGELOG entry below and
                      _llm_exprs_to_pysr_guesses()'s docstring for exactly
                      what does and doesn't survive conversion, and how a
                      guess that fails to convert or fails to apply is
                      surfaced (never silently dropped without a printed
                      warning and a `llm_guesses_used` field in the saved
                      record). Any result file produced by THIS script
                      version should be treated as a first hybrid-vs-
                      baseline run needing its own verification pass —
                      not as a continuation of, or replacement for, the
                      unverified 11/12 H figure flagged in
                      [FIX-STALE-CLAIM]/audit #3, which came from a
                      pre-fix script where H and P were identical.

Origin: extracted from HypatiaX_Experiments_v6_PUBLIC.ipynb (Cell 27)
Fixes applied (v02 → v03):
  - Removed Jupyter-only magic syntax (!pip install, %env, !)
  - Added __main__ guard
  - Added sys.path setup so imports resolve from repo root
  - Stale lock cleared before run (mirrors notebook Cell 27 logic)
  - Deps checked with importlib instead of subprocess pip call
  [PATCH A] Unified seed block — random/numpy/torch/Julia all set from SEED
  [PATCH E] Google Colab import replaced with pipeline-safe API key loader
  [PATCH F] IPython download block replaced with pipeline-safe output printer
  [PATCH G] Protocol imports use try/fallback for pre/post-restructure layout

CI / sharding fixes (v03 → current):
  [FIX-1] _apply_task_ids_nguyen: silent fallback-all replaced with hard exit.
          Previously a 0-match (wrong meta key, bad TASK_IDS format, etc.) made
          the shard silently run ALL 12 equations instead of its assigned subset,
          producing duplicate results across shards and corrupting checkpoints.
          Now: sys.exit(1) with a clear diagnostic so the CI job fails loudly.
  [FIX-2] _apply_case_range no longer applied to sys.path list.
          The two-element path list is not a test-case sequence; applying
          _apply_case_range to it could silently drop the repo-root sys.path
          entry when CASE_RANGE_START=2, breaking all subsequent imports.
          _apply_case_range is now only applied to all_cases (the correct seq).
  [FIX-3] SHARD_IDS env var honoured in addition to TASK_IDS.
          The CI YML sets both; previously only TASK_IDS was read. If TASK_IDS
          is absent but SHARD_IDS is set the filter now uses SHARD_IDS, which
          makes the script forward-compatible with YML changes.
  [FIX-4] Output JSON path uses RESULTS_DIR env var when set, matching the
          worker step env (RESULTS_DIR = OUT_BASE = hypatiax/data/results).
          Previously the path was always relative to _results_dir (repo-local),
          which diverged from the CI artifact upload path under OUT_BASE.
  [FIX-5] N_NGUYEN_TASKS ceiling applied AFTER _apply_task_ids_nguyen, not
          before. The old order [:n_tasks] → filter could silently exclude
          shard-assigned IDs that fell beyond the ceiling. New order: load all,
          filter by TASK_IDS, then apply the N_NGUYEN_TASKS smoke-test cap.
  [FIX-CHECKPOINT-CALL] Invoke _save() after each equation (not just at end).
          The _save() function was defined but never called in the main loop.
          If the job was killed mid-run, zero checkpoint data was written.
          Now checkpoints are saved after every equation and on deadline approach.
  [FIX-TRAJECTORY] (v02 -> v02_patched) Added PySR hall-of-fame trajectory
          monitoring: _read_pysr_hof_snapshot(), _poll_hof_dir_proc(), and
          _fit_with_pysr_trajectory(). See exp3_trajectory_smoke_test.py,
          which validates a script at this path/name specifically for the
          presence of these three functions.
          SINGLE-SOURCE-OF-TRUTH DESIGN NOTE: a prior version of this patch
          (never committed, referenced only by its result files under
          hypatiax/data/results/extrapolation/) derived the reported
          `expression` field from `model.sympy()` / `model.predict()`
          independently of the trajectory log built from PySR's
          hall_of_fame.csv. On at least 2 of 60 audited records (seed 42,
          N-4 and N-7, PySR-only) the two disagreed: the reported
          `expression` did not reproduce the reported R^2, while the
          trajectory's own best_expression did. Root cause was never
          located (the offending script was never found), but the failure
          mode is structural: two independent reads of "the best model
          found" can drift apart if anything changes between them (a
          background poll landing between iterations, PySR's in-memory
          state advancing after the last CSV flush, etc.).
          This rewrite closes that entire bug class by construction:
          `_fit_with_pysr_trajectory()` takes exactly ONE authoritative
          post-fit snapshot of hall_of_fame.csv, and that single snapshot
          is the source for BOTH the trajectory log AND the reported
          `expression`/`r2`. There is no second, independent code path
          that could disagree with it.

Expected result : UNVERIFIED — see [FIX-STALE-CLAIM] above. Prior figure
                  (different script version, different metric — training
                  r2, not this script's extrapolation r2): 11/12 H (91.7%)
                  · 10/12 P (83.3%) · 0/12 NN, MW P>NN U=113, p=0.0097.
                  Also see [KNOWN-BUG-1]: as written, H and P are the same
                  PySR fit, so this is not yet a hybrid-vs-baseline result.
Wall time       : 30–90 min
SEED            : 42 (fixed for reproducibility; override with --seed)

Usage
-----
    python3 exp3_nguyen12_hybrid50v_consolidated.py                                 # SEED=42, temp=0.25 (defaults)
    python3 exp3_nguyen12_hybrid50v_consolidated.py --seed 123                      # stability check, temp=0.25
    python3 exp3_nguyen12_hybrid50v_consolidated.py --seed 777                      # stability check, temp=0.25
    python3 exp3_nguyen12_hybrid50v_consolidated.py --seed 123 --temperature 0      # determinism control
    python3 exp3_nguyen12_hybrid50v_consolidated.py --seed 123 --temperature 0 --run-index 3   # 3rd of N repeats

CI shard usage (set by ci_runner.yml worker dispatch):
    TASK_IDS="N1 N3 N7" PYSR_SEED=42 EXPERIMENT_SEED=42 \
        python3 exp3_nguyen12_hybrid50v_consolidated.py --seed 42 --temperature 0.25

Trajectory-monitor env vars (read by _fit_with_pysr_trajectory / the poller):
    PYSR_TRAJECTORY_POLL_SECONDS  poll interval in seconds (default: 2.0;
                                   exp3_trajectory_smoke_test.py sets 0.05)
    PYSR_TRAJECTORY_OUTPUT_DIR    parent dir for PySR's per-fit output
                                   (default: hypatiax/data/results/
                                   _pysr_trajectory_runs, matching the path
                                   pattern seen in existing result files)
"""

import argparse
import csv
import importlib
import inspect
import multiprocessing as mp
import os
import pathlib
import random
import re
import sys
import time
import warnings

import numpy as np
# [FIX-LLM-WARMSTART] sympy was already a required dependency (see
# _REQUIRED below, and model.sympy() elsewhere in this file) -- imported
# at module level here so _llm_exprs_to_pysr_guesses() doesn't have to
# guess at import timing relative to the dependency check.
import sympy as sp

# ── CASE RANGE INJECTION (auto-generated by add_case_range_benchmark.py) ──
def _apply_case_range(seq):
    """Return the slice of *seq* selected by CASE_RANGE_START/CASE_RANGE_END.

    Uses 1-based inclusive indexing to match CI --case-range N-M syntax.
    Returns seq unchanged when neither variable is set (local runs).

    NOTE: must only be applied to test-case sequences, NOT to sys.path lists.
    See FIX-2 in the module docstring.
    """
    try:
        n     = len(seq)
        start = max(0, int(os.getenv("CASE_RANGE_START", "1")) - 1)
        end   = min(n, int(os.getenv("CASE_RANGE_END",   str(n))))
        return seq[start:end]
    except Exception:
        return seq
# ──────────────────────────────────────────────────────────────── [...]

# ── TASK_IDS / SHARD_IDS / SEED injection ───────────────────────────────────
def _apply_task_ids_nguyen(seq):
    """Filter Nguyen case list to those whose nguyen_id appears in TASK_IDS.

    TASK_IDS format for exp3: "N1 N2 N5 N11"  (space- or comma-separated).
    SHARD_IDS is also checked when TASK_IDS is absent (CI forward-compat).
    Each element of *seq* is (desc, X, y, var_names, meta); meta["nguyen_id"]
    is the canonical ID.

    Returns seq unchanged when neither env var is set (full-12 local run).

    [FIX-1] Zero-match is now a hard exit, not a silent fallback-all.
    A 0-match means TASK_IDS contains IDs that do not exist in the protocol
    (e.g. wrong format, missing meta key) — silently running all 12 equations
    would corrupt checkpoint deduplication across shards.
    """
    # Priority: TASK_IDS > SHARD_IDS  (mirrors hybrid_system_llm_nn_all_domains.py)
    raw = ""
    for var in ("TASK_IDS", "SHARD_IDS"):
        raw = os.environ.get(var, "").replace(",", " ").strip()
        if raw:
            break

    if not raw:
        return seq  # local run — no filter

    allowed  = set(raw.split())
    filtered = [t for t in seq if t[4].get("nguyen_id") in allowed]

    if not filtered:
        # [FIX-1] Hard exit instead of silent fallback-all.
        # List which IDs were requested vs what the protocol actually provides
        # so the CI log immediately shows the mismatch.
        available = sorted(set(t[4].get("nguyen_id", "?") for t in seq))
        print(
            f"ERROR: TASK_IDS={sorted(allowed)!r} matched 0/{len(seq)} Nguyen tasks.\n"
            f"       Available nguyen_ids: {available}\n"
            f"       Check that meta['nguyen_id'] is set in NguYenProtocol and that\n"
            f"       the CI plan registry uses the same IDs (N1–N12).",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        f"ℹ️  TASK_IDS filter: {len(filtered)}/{len(seq)} tasks selected "
        f"({[t[4]['nguyen_id'] for t in filtered]})"
    )
    return filtered


def _resolve_seed():
    """Return seed: PYSR_SEED → EXPERIMENT_SEED → NN_SEED → CLI --seed → 42.

    Priority order ensures CI env-var always wins over the argparse default,
    while local runs with an explicit --seed still work correctly.
    """
    for var in ("PYSR_SEED", "EXPERIMENT_SEED", "NN_SEED"):
        v = os.environ.get(var, "").strip()
        if v:
            try:
                return int(v)
            except ValueError:
                pass
    return None   # sentinel → caller uses _args.seed (argparse default)


def _resolve_results_dir(repo_results_dir: pathlib.Path) -> pathlib.Path:
    """Return the output directory, preferring RESULTS_DIR env var.

    [FIX-4] CI sets RESULTS_DIR = OUT_BASE = hypatiax/data/results (absolute
    path inside the runner workspace).  Using it here keeps JSON output in the
    same tree the artifact upload step expects.  Falls back to the repo-local
    path for local runs where RESULTS_DIR is not set.
    """
    env_dir = os.environ.get("RESULTS_DIR", "").strip()
    if env_dir:
        return pathlib.Path(env_dir)
    return repo_results_dir
# ──────────────────────────────────────────────────────────────── [...]

# ── 1. Resolve repo root & set sys.path ───────────────────────────────────
# Script lives at:  <repo>/hypatiax/experiments/benchmarks/exp3_nguyen12_hybrid50v_consolidated.py
# [FIX-N3-ii-d, merged from _03.py] _SCRIPT_DIR is already benchmarks/
# (Path(__file__).parent already strips the filename), so repo root is only
# 2 more hops up, not 3:
#   parents[0] = experiments/
#   parents[1] = hypatiax/
#   parents[2] = <repo>/        <- correct repo root
# The old parents[3] indexing was calibrated as if _SCRIPT_DIR were still the
# file path itself, so it walked one directory too far up in every layout —
# IndexError on a flat/local checkout, and a silently-wrong _REPRO_ROOT
# (missing hypatiax/) on CI's nested runner/work/<repo>/<repo>/ checkout.
_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
_REPO_ROOT  = _SCRIPT_DIR.parents[2]   # benchmarks/ -> experiments/ -> hypatiax/ -> repo root

# Support override via environment variable (set by pipeline or notebook)
_REPRO_ROOT = pathlib.Path(os.environ.get("REPRO_ROOT", str(_REPO_ROOT)))

# [FIX-2] sys.path setup — _apply_case_range intentionally NOT applied here.
# The two path strings are not a test-case sequence; slicing them could silently
# drop the repo-root entry and break all subsequent protocol imports.
for _p in [str(_REPRO_ROOT), str(_REPRO_ROOT / "hypatiax")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── 2. Argument parsing (early — SEED needed before env setup) ────────────
def _parse_args():
    parser = argparse.ArgumentParser(
        description="Exp 3 · Nguyen-12 SR suite (§10.8 primary)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for all RNG sources (default: 42)"
    )
    # [FIX-N3-ii-a, merged from _03.py] Explicit, loggable sampling
    # temperature for the LLM warm-start call, in place of hypatia.py's
    # implicit temperature=0.25 default.
    parser.add_argument(
        "--temperature", type=float, default=0.25,
        help="LLM sampling temperature passed to get_llm_prior() "
             "(default: 0.25, matching hypatia.py's prior default)"
    )
    # [FIX-N3-ii-b, merged from _03.py] Distinguishes repeated runs at the
    # same (seed, temperature) pair so their output files don't collide
    # with the "already exists, skip" guard in run().
    parser.add_argument(
        "--run-index", type=int, default=1,
        help="1-based index of this run among repeated runs at the same "
             "seed/temperature, used only to disambiguate output filenames "
             "(default: 1)"
    )
    # [FIX-N3-ii-c, merged from _03.py] hypatia.py's get_llm_prior()
    # candidate-sampling width, recorded alongside temperature/solve-rate.
    parser.add_argument(
        "--n-candidates", "--candidate-count",
        dest="n_candidates", type=int, default=None,
        help="Number of LLM-proposed candidate expressions to sample per "
             "equation before trust-gating, passed to get_llm_prior() "
             "(default: LLM_N_CANDIDATES env var, else 8)"
    )
    return parser.parse_args()

# Parse early so SEED is available for the seed block below.
# (argparse is safe to call at module level — it only reads sys.argv)
_args = _parse_args()
# [FIX-SEED-ZERO] `_resolve_seed() or ...` silently discarded an explicit,
# legitimate seed of 0 (0 is falsy in Python), replacing it with the
# EXPERIMENT_SEED/--seed fallback (typically 42). Any CI run that set
# PYSR_SEED=0 / EXPERIMENT_SEED=0 / NN_SEED=0 was silently reseeded to 42
# without warning. Use an explicit None check instead.
_resolved_seed = _resolve_seed()
SEED = _resolved_seed if _resolved_seed is not None else int(os.environ.get("EXPERIMENT_SEED", str(_args.seed)))

# ── 3. [PATCH A] Unified seed block — ALL sources seeded from SEED ────────
random.seed(SEED)
np.random.seed(SEED)
os.environ["PYTHONHASHSEED"] = str(SEED)
os.environ["JULIA_SEED"]     = str(SEED)   # PySR / Julia RNG

# [FIX-SEGFAULT] juliacall MUST be imported before torch.
# torch imported first causes segfault — PyTorch signal handlers clobber Julia's.
# PYTHON_JULIACALL_HANDLE_SIGNALS=yes is already set in CI global env.
# See: https://github.com/pytorch/pytorch/issues/78829
os.environ.setdefault("PYTHON_JULIACALL_HANDLE_SIGNALS", "yes")
try:
    import juliacall  # noqa: F401  — must precede torch import
except ImportError:
    pass  # juliacall absent — PySR subprocess handles Julia init

try:
    import torch
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark     = False
except ImportError:
    pass
print(f"✅ All seeds set to {SEED}")

# ── 4. Dependency check (no !pip magic — deps managed by pipeline) ─────────
_REQUIRED = ["pysr", "anthropic", "sklearn", "scipy", "sympy", "numpy", "pandas", "matplotlib"]
_MISSING  = []
for _pkg in _REQUIRED:
    try:
        importlib.import_module(_pkg)
    except ImportError:
        _MISSING.append(_pkg)

if _MISSING:
    print(f"  ✗  Missing packages: {', '.join(_MISSING)}")
    print("     Install via:  pip install " + " ".join(_MISSING))
    print("     Or run the full pipeline first (it installs deps in Phase 0).")
    sys.exit(1)

# ── 5. Clear stale protocol cache lock (mirrors notebook Cell 27) ──────────
_repo_results_dir = _REPRO_ROOT / "hypatiax" / "data" / "results"
_locks = list(_repo_results_dir.glob(".lock_*")) if _repo_results_dir.exists() else []
if _locks:
    for _l in _locks:
        _l.unlink()
    print(f"  Cleared {len(_locks)} stale lock(s) — experiment will run fresh")
else:
    print("  No stale locks found")

# ── 6. Environment variables (mirrors notebook Cell 2 / %env block) ────────
os.environ["NN_SEED"]   = str(SEED)   # always propagate resolved SEED
os.environ["PYSR_SEED"] = str(SEED)
os.environ.setdefault("LLM_MODEL",   "claude-sonnet-4-6")
os.environ.setdefault("LLM_RETRIES", "3")
os.environ.setdefault("LLM_K_RUNS",  "1")
os.environ.setdefault("ENGINE",      "hybrid_system_v50_2")
os.environ.setdefault("REPRO_ROOT",  str(_REPRO_ROOT))

# ── 7. [PATCH E] Pipeline-safe API key loader (replaces Colab userdata) ───
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

if not ANTHROPIC_API_KEY:
    # Try Colab userdata only if actually running inside Colab
    try:
        from google.colab import userdata as _colab_userdata
        ANTHROPIC_API_KEY = _colab_userdata.get("ANTHROPIC_API_KEY") or ""
    except (ImportError, Exception):
        pass

if not ANTHROPIC_API_KEY:
    # Try .env file relative to repo root
    for _env_path in [
        _REPRO_ROOT / ".env",
        _REPRO_ROOT / "hypatiax" / ".env",
    ]:
        if _env_path.exists():
            for _line in _env_path.read_text().splitlines():
                if _line.startswith("ANTHROPIC_API_KEY="):
                    ANTHROPIC_API_KEY = _line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
        if ANTHROPIC_API_KEY:
            break

USE_LLM = True
if ANTHROPIC_API_KEY:
    os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY
    print("API key set ✓")
else:
    print("⚠  No API key found — LLM guidance disabled (USE_LLM forced False)")
    USE_LLM = False


# ── 7b. PySR hall-of-fame trajectory monitor  [FIX-TRAJECTORY] ─────────────
#
# Three functions, matching the names exp3_trajectory_smoke_test.py checks
# for verbatim:
#   _read_pysr_hof_snapshot  — parse one hall_of_fame.csv into a snapshot dict
#   _poll_hof_dir_proc       — separate-process poller (see rationale below)
#   _fit_with_pysr_trajectory — orchestrates fit() + polling + final snapshot
#
# WHY A SEPARATE PROCESS, NOT A THREAD: PySR's actual search runs in Julia
# via PyJulia/PythonCall, which holds its own GIL-adjacent locks during
# `.fit()`. A polling *thread* in the same process competes with that call
# for the Python GIL and, worse, has been observed (informally, not on the
# record here) to stall until `.fit()` yields control back to Python -- at
# which point there is nothing left to poll *during*, only after. A separate
# process reading the CSV file from disk has no such contention: PySR writes
# hall_of_fame.csv incrementally to disk regardless of what the calling
# process's Python interpreter is doing, so a fully independent OS process
# can poll it on a wall-clock timer with no risk of being blocked by the fit
# call itself.
_TRAJ_POLL_SECONDS = float(os.environ.get("PYSR_TRAJECTORY_POLL_SECONDS", "2.0"))
_TRAJ_OUTPUT_DIR = pathlib.Path(
    os.environ.get(
        "PYSR_TRAJECTORY_OUTPUT_DIR",
        str(pathlib.Path(__file__).resolve().parents[2]
            / "data" / "results" / "_pysr_trajectory_runs"),
    )
)


def _read_pysr_hof_snapshot(csv_path, label=None, iteration=None, elapsed_seconds=None):
    """Parse one PySR hall_of_fame.csv into the snapshot dict format used
    throughout this codebase's `trajectory` field (matches the keys already
    found in committed result files: source_file, source_mtime_ns,
    source_size_bytes, hall_of_fame_rows, best_loss, best_expression,
    best_complexity, best_score, elapsed_seconds, iteration, label).

    Returns None if the file doesn't exist yet or has no data rows (both
    expected transient states early in a fit -- the caller should treat
    None as "no snapshot available yet", not as an error).

    PySR's hall_of_fame.csv columns (as of the PySR versions this repo
    targets): Complexity, Loss, Equation, and optionally Score. "Best" is
    defined here as the LOWEST-LOSS row, not PySR's own accuracy/complexity
    trade-off "best" pick used by `model.sympy()` -- this is a deliberate
    choice: it is a single, simple, reproducible criterion that this
    function can apply identically whether reading mid-fit or post-fit,
    which is what makes the single-source-of-truth design below possible.
    """
    csv_path = pathlib.Path(csv_path)
    if not csv_path.exists():
        return None

    try:
        stat = csv_path.stat()
        with open(csv_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except (OSError, csv.Error):
        return None

    if not rows:
        return None

    def _row_loss(row):
        try:
            return float(row["Loss"])
        except (KeyError, ValueError, TypeError):
            return float("inf")

    best_row = min(rows, key=_row_loss)

    try:
        best_loss = float(best_row["Loss"])
    except (KeyError, ValueError, TypeError):
        best_loss = float("nan")
    try:
        best_complexity = float(best_row["Complexity"])
    except (KeyError, ValueError, TypeError):
        best_complexity = float("nan")
    best_score = best_row.get("Score")
    try:
        best_score = float(best_score) if best_score not in (None, "") else None
    except (ValueError, TypeError):
        best_score = None

    return {
        "source_file": str(csv_path),
        "source_mtime_ns": stat.st_mtime_ns,
        "source_size_bytes": stat.st_size,
        "hall_of_fame_rows": len(rows),
        "best_loss": best_loss,
        "best_expression": best_row.get("Equation"),
        "best_complexity": best_complexity,
        "best_score": best_score,
        "elapsed_seconds": elapsed_seconds,
        "iteration": iteration,
        "label": label,
    }


def _poll_hof_dir_proc(csv_path_str, poll_seconds, label, queue, stop_event, t_start):
    """Target function for the poller process. Polls `csv_path_str` every
    `poll_seconds` and pushes a snapshot onto `queue` whenever the file's
    (mtime, size) changes since the last successful read -- avoids pushing
    duplicate snapshots between PySR's own internal write intervals.

    Runs until `stop_event` is set by the parent process (after `.fit()`
    returns), then does one final poll attempt before exiting so a
    fast-converging fit that produced its only update late still gets
    captured -- this is why iteration=1 is a normal, valid trajectory length
    (a single snapshot), not evidence of a broken poller.
    """
    csv_path = pathlib.Path(csv_path_str)
    last_key = None
    iteration = 0

    def _try_poll():
        nonlocal last_key, iteration
        if not csv_path.exists():
            return
        try:
            stat = csv_path.stat()
        except OSError:
            return
        key = (stat.st_mtime_ns, stat.st_size)
        if key == last_key:
            return  # no change since last successful read
        snap = _read_pysr_hof_snapshot(
            csv_path, label=label, iteration=iteration + 1,
            elapsed_seconds=time.time() - t_start,
        )
        if snap is not None:
            last_key = key
            iteration += 1
            queue.put(snap)

    while not stop_event.is_set():
        _try_poll()
        stop_event.wait(poll_seconds)  # sleep, but wake immediately on stop
    _try_poll()  # final catch-up poll after fit() has returned


def _score_expr(expr_py, X, y, variable_names):
    """Evaluate a PySR expression string's R^2 against an arbitrary (X, y)
    pair. Used both for the training-domain score (during fit) and,
    [FIX-EXTRAP-R2], for re-scoring the final expression against the
    held-out extrapolation split -- the same eval namespace and R^2
    formula as `_fit_with_pysr_trajectory`'s internal scoring, factored
    out so both call sites can't drift apart.

    Returns None (not NaN, not an exception) if `expr_py`, X, or y is
    unavailable, or if evaluation fails for any reason -- callers treat
    None as "no score computable" and fall back accordingly.
    """
    if not expr_py or X is None or y is None:
        return None
    try:
        ns = {v: X[:, i] for i, v in enumerate(variable_names)}
        ns.update({"sin": np.sin, "cos": np.cos, "log": np.log,
                   "sqrt": np.sqrt, "exp": np.exp,
                   # [FIX-SAFE-POW] square/cube replace the generic "^"
                   # operator below -- see _pysr_kwargs. Expressions coming
                   # back from PySR now use these names instead of "**"
                   # with a fractional/negative-base exponent, so the eval
                   # namespace has to know them too.
                   "square": np.square, "cube": lambda z: z ** 3})
        y_pred = eval(expr_py, {"__builtins__": {}}, ns)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return float(1.0 - ss_res / ss_tot) if ss_tot != 0 else float("nan")
    except Exception:
        return None


# [FIX-LLM-WARMSTART] Operators this script's PySR model is actually
# configured with (see _pysr_kwargs: binary_operators=["+","-","*","/"],
# unary_operators=["sin","cos","log","sqrt","exp","square","cube"] —
# no "^", removed by [FIX-SAFE-POW] to keep exponents integer and stop
# fractional/negative-base powers reaching PySR's search). A converted
# guess must stay inside this exact set or PySR's `guesses` parser will
# reject it.
_PYSR_ALLOWED_UNARY_FUNCS = {"sin", "cos", "log", "sqrt", "exp"}
_PYSR_MAX_INT_POWER = 6  # sanity cap; every Nguyen-12 ground truth needs <=4


def _sympy_pow_to_pysr_str(expr, variable_names):
    """Render a sympy expression as a string PySR's `guesses` parser can
    read, restricted to exactly this script's operator set (see
    _PYSR_ALLOWED_UNARY_FUNCS / _pysr_kwargs above — no "^", so integer
    powers are expanded into square()/cube()/repeated-multiplication
    instead).

    Returns None if `expr` can't be represented under that restricted set
    (a fractional or symbolic exponent, a function PySR doesn't have, an
    exponent above _PYSR_MAX_INT_POWER) -- callers treat None as "drop
    this guess", not "guess at a lossy translation". A rejected sub-term
    fails the whole guess (the caller only ever sees a clean string or
    None) rather than silently substituting something PySR happens to
    accept but which no longer means what the LLM proposed.
    """
    if expr.is_Symbol:
        name = str(expr)
        return name if name in variable_names else None
    if expr.is_Number:
        try:
            return repr(float(expr))
        except (TypeError, ValueError):
            return None
    if expr.is_Add:
        parts = [_sympy_pow_to_pysr_str(a, variable_names) for a in expr.args]
        return None if any(p is None for p in parts) else "(" + " + ".join(parts) + ")"
    if expr.is_Mul:
        # Route any Pow(base, negative_int) factor through division --
        # "^" (and therefore a negative exponent) isn't in the allowed
        # operator set, but "/" is.
        num_terms, den_terms = [], []
        for a in expr.args:
            if a.is_Pow and a.args[1].is_Integer and int(a.args[1]) < 0:
                den_terms.append(sp.Pow(a.args[0], -int(a.args[1])))
            else:
                num_terms.append(a)
        num_parts = [_sympy_pow_to_pysr_str(a, variable_names) for a in num_terms] or ["1.0"]
        if any(p is None for p in num_parts):
            return None
        num_str = "(" + " * ".join(num_parts) + ")"
        if not den_terms:
            return num_str
        den_parts = [_sympy_pow_to_pysr_str(a, variable_names) for a in den_terms]
        if any(p is None for p in den_parts):
            return None
        return "(" + num_str + " / (" + " * ".join(den_parts) + "))"
    if expr.is_Pow:
        base, exponent = expr.args
        base_str = _sympy_pow_to_pysr_str(base, variable_names)
        if base_str is None or not exponent.is_Integer:
            return None  # fractional/symbolic power -- unrepresentable here
        n = int(exponent)
        if n == 0:
            return "1.0"
        if n < 0:
            recip = _sympy_pow_to_pysr_str(base ** (-n), variable_names)
            return None if recip is None else f"(1.0 / {recip})"
        if n > _PYSR_MAX_INT_POWER:
            return None
        if n == 2:
            return f"square({base_str})"
        if n == 3:
            return f"cube({base_str})"
        # n in {4,5,6}: plain repeated multiplication -- always valid
        # under +,-,*,/ regardless of whether n factors nicely into
        # square/cube compositions.
        return "(" + " * ".join([base_str] * n) + ")"
    func_name = getattr(expr, "func", None) and expr.func.__name__
    if func_name in _PYSR_ALLOWED_UNARY_FUNCS and len(expr.args) == 1:
        arg_str = _sympy_pow_to_pysr_str(expr.args[0], variable_names)
        return None if arg_str is None else f"{func_name}({arg_str})"
    # Anything else (tan, asin, Abs, a leftover free symbol not in
    # variable_names, ...) can't be expressed under this script's
    # restricted PySR operator set.
    return None


def _llm_exprs_to_pysr_guesses(llm_exprs, variable_names):
    """[FIX-LLM-WARMSTART, resolves audit-exp3.txt item #1] Convert
    get_llm_prior()'s Python/numpy-syntax expression strings (e.g.
    "np.sin(x)**2 + x**4") into strings PySRRegressor.fit(guesses=...)
    can parse, under this script's actual restricted operator set (see
    _pysr_kwargs / _PYSR_ALLOWED_UNARY_FUNCS — no "^", integer powers
    only, sin/cos/log/sqrt/exp/square/cube only).

    Each candidate is converted independently; one that fails to parse
    or uses an operator outside the allowed set is logged with a
    printed warning and dropped, not silently skipped -- callers should
    not treat an empty return as equivalent to `USE_LLM=False` without
    surfacing that distinction (see the `llm_guesses_used` field written
    into each saved record in run()).
    """
    local_dict = {v: sp.Symbol(v) for v in variable_names}
    guesses = []
    for raw in llm_exprs:
        cleaned = re.sub(r"\bnp\.", "", str(raw))
        try:
            parsed = sp.sympify(cleaned, locals=local_dict)
        except (sp.SympifyError, TypeError, SyntaxError, AttributeError) as e:
            print(f"    ⚠ [FIX-LLM-WARMSTART] could not parse LLM candidate "
                  f"{raw!r}: {e} -- skipped, not used as a PySR guess.")
            continue
        rendered = _sympy_pow_to_pysr_str(parsed, variable_names)
        if rendered is None:
            print(f"    ⚠ [FIX-LLM-WARMSTART] LLM candidate {raw!r} uses an "
                  f"operator/power outside this script's PySR operator set "
                  f"-- skipped, not used as a PySR guess.")
            continue
        guesses.append(rendered)
    return guesses


def _validate_llm_pysr_guesses(guesses, X, y, X_buffer, y_buffer,
                                variable_names, min_r2=0.95,
                                max_abs_pred=1e12):
    """Quality/safety gate for LLM -> PySR warm-start candidates.

    A candidate is accepted only if it is already numerically meaningful on
    the data PySR will see: finite predictions on the original training data
    AND on the boundary-buffer data, bounded predictions, and R² above the
    configured threshold on both sets.  This is deliberately a pre-PySR gate:
    a syntactically valid expression is not trusted merely because PySR can
    parse it.

    Returns (accepted_guesses, audit_rows).
    """
    accepted = []
    audit = []
    seen = set()

    def _predict(expr, Xv):
        ns = {v: Xv[:, i] for i, v in enumerate(variable_names)}
        ns.update({"sin": np.sin, "cos": np.cos, "log": np.log,
                   "sqrt": np.sqrt, "exp": np.exp,
                   "square": np.square, "cube": lambda z: z ** 3})
        pred = eval(expr, {"__builtins__": {}}, ns)
        pred = np.asarray(pred, dtype=float)
        if pred.ndim == 0:
            pred = np.full(Xv.shape[0], float(pred))
        if pred.shape != (Xv.shape[0],):
            raise ValueError(f"prediction shape {pred.shape}, expected {(Xv.shape[0],)}")
        return pred

    def _r2(yv, pred):
        ss_tot = np.sum((yv - np.mean(yv)) ** 2)
        if ss_tot == 0:
            return float("nan")
        return float(1.0 - np.sum((yv - pred) ** 2) / ss_tot)

    for expr in guesses:
        row = {"expression": expr, "accepted": False, "r2_train": None,
               "r2_buffer": None, "reason": None}
        if expr in seen:
            row["reason"] = "duplicate"
            audit.append(row)
            continue
        seen.add(expr)
        try:
            pred = _predict(expr, X)
            pred_buf = _predict(expr, X_buffer)
            if not np.all(np.isfinite(pred)) or not np.all(np.isfinite(pred_buf)):
                row["reason"] = "non_finite_prediction"
            elif (np.max(np.abs(pred)) > max_abs_pred or
                  np.max(np.abs(pred_buf)) > max_abs_pred):
                row["reason"] = "prediction_magnitude_limit"
            else:
                row["r2_train"] = _r2(y, pred)
                row["r2_buffer"] = _r2(y_buffer, pred_buf)
                if (not np.isfinite(row["r2_train"]) or
                    not np.isfinite(row["r2_buffer"])):
                    row["reason"] = "non_finite_r2"
                elif min(row["r2_train"], row["r2_buffer"]) < min_r2:
                    row["reason"] = f"r2_below_threshold_{min_r2:g}"
                else:
                    row["accepted"] = True
                    accepted.append(expr)
        except Exception as exc:
            row["reason"] = f"evaluation_error:{type(exc).__name__}"
        audit.append(row)

    return accepted, audit


def _build_boundary_buffer(X, y, meta, variable_names,
                            buffer_frac=0.15, gap_frac=0.4, n_buffer=40):
    """[FIX-SINGULARITY-BUFFER] Widen the FIT data (not the reported R^2,
    not the real held-out extrapolation set) with points sampled from a
    band just outside the training range, using the same ground-truth
    formula that generated the training data in the first place.

    This is what catches the N12/seed99 failure mode: PySR fit an
    exp(.../cos(x)...) term whose denominator approaches zero just past
    x=1 (the training boundary), so training loss kept improving while the
    fitted curve blew up to R^2 ~ -10^47 a short distance outside the box.
    A candidate like that scores terribly the moment the buffer band is
    part of the loss, so it gets weeded out of the hall-of-fame during the
    search instead of surviving to become "best" and only failing on the
    real extrapolation split we never let the search see.

    [FIX-SINGULARITY-BUFFER-v2] The original version sized the buffer band
    as `buffer_frac` of the TRAINING width on each side (e.g. 15% of a
    width-2 box = 0.3 units). That was too narrow relative to how far some
    equations' actual extrapolation set reaches: N7/seed777 has training
    x in [0,2] but extrapolation x in [2,5] -- a gap of 3 units -- so a
    0.3-unit buffer only ever "saw" as far as x=2.3, and a denominator
    that's safely nonzero there could still approach zero somewhere in the
    remaining [2.3, 5] the buffer never touched (this is exactly what
    happened: N7/seed777 went from NaN to a real but still-overfit
    r2_extrap=0.76 after the v1 fix). This version prefers sizing the
    buffer as `gap_frac` of the actual distance to `extrap_ranges` (from
    the metadata) when that's available, falling back to the old
    training-width-based sizing when it isn't. `gap_frac` is deliberately
    NOT 1.0 -- covering 100% of the gap would make "extrapolation R^2"
    measure something close to interpolation again. 0.4 is a compromise:
    wide enough to catch a singularity that would otherwise only surface
    partway through the real extrapolation region, without training on
    (and thus disguising failure on) most of that region.

    Returns (X_aug, y_aug). Falls back to (X, y) unchanged if the ground
    truth expression can't be parsed/evaluated for any reason -- augmenting
    training data should never be able to crash a run that would otherwise
    have worked.
    """
    ranges = meta.get("variable_ranges")
    extrap_ranges = meta.get("extrap_ranges") or {}
    formula = meta.get("ground_truth")
    if not ranges or not formula:
        return X, y
    try:
        rng = np.random.RandomState(0)
        buf_cols = []
        for v in variable_names:
            lo, hi = ranges[v]
            width = hi - lo
            ext = extrap_ranges.get(v)
            if ext is not None:
                ext_lo, ext_hi = ext
                # gap on each side between the training box and where the
                # real extrapolation set actually goes (0 if the extrap
                # range doesn't extend that direction, e.g. N7's ext_lo
                # equals its train lo -- no lower-side extrapolation there)
                gap_lo = max(lo - ext_lo, 0.0)
                gap_hi = max(ext_hi - hi, 0.0)
                pad_lo = gap_frac * gap_lo
                pad_hi = gap_frac * gap_hi
            else:
                # no extrap_ranges in metadata -- fall back to the original
                # training-width-based sizing rather than skip the buffer
                pad_lo = pad_hi = buffer_frac * width
            lo_band = rng.uniform(lo - pad_lo, lo, size=n_buffer // 2) \
                if pad_lo > 0 else np.full(n_buffer // 2, lo)
            hi_band = rng.uniform(hi, hi + pad_hi, size=n_buffer - n_buffer // 2) \
                if pad_hi > 0 else np.full(n_buffer - n_buffer // 2, hi)
            buf_cols.append(np.concatenate([lo_band, hi_band]))
        X_buf = np.column_stack(buf_cols)
        ns = {v: X_buf[:, i] for i, v in enumerate(variable_names)}
        ns.update({"sin": np.sin, "cos": np.cos, "log": np.log,
                   "sqrt": np.sqrt, "exp": np.exp})
        y_buf = eval(formula, {"__builtins__": {}}, ns)
        y_buf = np.asarray(y_buf, dtype=float)
        if not np.all(np.isfinite(y_buf)):
            return X, y  # ground truth itself is singular in the buffer band
        return np.vstack([X, X_buf]), np.concatenate([y, y_buf])
    except Exception:
        return X, y


def _fit_with_pysr_trajectory(model, X, y, variable_names, label,
                               poll_seconds=None, output_dir=None,
                               X_score=None, y_score=None, fit_kwargs=None):
    """Fit `model` (a PySRRegressor) on (X, y) while recording a hall-of-fame
    trajectory, and return (r2, best_expr, trajectory) where `r2` and
    `best_expr` are derived from EXACTLY the same final snapshot that ends
    the trajectory list -- see the [FIX-TRAJECTORY] module docstring note
    for why this single-source-of-truth design is the point of this
    function, not an incidental detail.

    Falls back to `model.sympy()` / `model.predict()` (with a loud warning,
    not a silent one) only if no hall-of-fame snapshot could be read at all
    post-fit -- e.g. PySR's output layout changed in a future version and
    _read_pysr_hof_snapshot's column assumptions no longer hold. That
    fallback path is intentionally the ONLY place in this function where
    `expression` and the scoring value could in principle come from
    different reads -- and even then, both still come from the same
    `model` object's own post-fit state, not from a stale trajectory poll.

    `fit_kwargs`, if given, is forwarded verbatim into model.fit(). The H
    run uses this to pass `guesses` (the converted LLM warm-start
    candidates) -- [FIX-LLM-WARMSTART-GATE] `guesses` is a fit()-level
    parameter in this pysr build (2.0.0a1), not a constructor argument;
    see the module-level guard and the H-run call site.
    """
    # [FIX-SINGULARITY-BUFFER] `model.fit(X, y, ...)` below fits on whatever
    # X/y the caller passes in -- which may now be the boundary-buffer-
    # augmented set. r2_train should still describe the ORIGINAL training
    # domain only (X_score/y_score), so it stays comparable to past runs
    # and doesn't quietly include the buffer band in its own score.
    X_score = X if X_score is None else X_score
    y_score = y if y_score is None else y_score

    poll_seconds = _TRAJ_POLL_SECONDS if poll_seconds is None else poll_seconds
    output_dir = _TRAJ_OUTPUT_DIR if output_dir is None else pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    run_id = f"{time.strftime('%Y%m%d_%H%M%S')}_{os.urandom(3).hex()}"
    run_dir = output_dir / run_id
    # Pre-declaring output_directory + run_id (rather than letting PySR
    # generate its own) is what makes it possible to know the CSV path
    # *before* calling fit(), so the poller process can be started first.
    model.set_params(output_directory=str(output_dir), run_id=run_id)
    csv_path = run_dir / "hall_of_fame.csv"

    # [FIX-MANAGER-LEAK, addresses audit #7] mp.Manager() spins up its own
    # server process and was never explicitly shut down — called twice per
    # equation (H and P) x 12 equations = up to 24 leaked Manager server
    # processes per run. Wrap the manager's whole lifetime (not just
    # model.fit()) in try/finally so manager.shutdown() always runs, even
    # if fit() raises or an early return happens below.
    manager = mp.Manager()
    try:
        queue = manager.Queue()
        stop_event = manager.Event()
        t_start = time.time()

        poller = mp.Process(
            target=_poll_hof_dir_proc,
            args=(str(csv_path), poll_seconds, label, queue, stop_event, t_start),
            daemon=True,
        )
        poller.start()

        try:
            # [FIX-LLM-WARMSTART-GATE] `guesses` (when present) is threaded
            # through fit_kwargs into fit() itself -- see the H-run call
            # site, which only sets fit_kwargs={"guesses": ...} when there's
            # at least one converted LLM candidate. P (baseline) is called
            # with fit_kwargs=None so it stays unseeded.
            model.fit(X, y, variable_names=variable_names, **(fit_kwargs or {}))
        finally:
            stop_event.set()
            poller.join(timeout=max(5.0, poll_seconds * 3))
            if poller.is_alive():
                poller.terminate()

        # Drain every snapshot the poller captured during the fit into the
        # trajectory log, in order.
        trajectory = []
        while not queue.empty():
            trajectory.append(queue.get())

        # The single authoritative post-fit read: taken AFTER fit() has fully
        # returned and AFTER the poller has been joined, so nothing else can
        # touch csv_path concurrently. If this snapshot differs from the last
        # entry the poller captured, it replaces it as the final trajectory
        # entry -- fit() may have written its last update after the poller's
        # final pre-stop poll but before its post-stop catch-up poll landed.
        final_snapshot = _read_pysr_hof_snapshot(
            csv_path, label=label, iteration=len(trajectory) + 1,
            elapsed_seconds=time.time() - t_start,
        )
        if final_snapshot is not None:
            if trajectory and trajectory[-1]["source_mtime_ns"] == final_snapshot["source_mtime_ns"]:
                trajectory[-1] = final_snapshot  # same file state, richer record
            else:
                trajectory.append(final_snapshot)
            best_expr = final_snapshot["best_expression"]
            # PySR's raw hall_of_fame.csv stores '^' for power; normalize to
            # Python's '**' so downstream eval()/rescoring works without a
            # separate translation step (this is a display/audit-file
            # convenience -- normalize the same way, everywhere it's read).
            best_expr_py = best_expr.replace("^", "**") if best_expr else None
            r2 = _score_expr(best_expr_py, X_score, y_score, variable_names)
            if r2 is None:
                # Expression-based scoring failed (e.g. a function the eval
                # namespace above doesn't cover) -- fall back to PySR's own
                # predict(), still against the SAME model/expression PySR
                # itself considers current, not a second independent read.
                from sklearn.metrics import r2_score
                r2 = float(r2_score(y_score, model.predict(X_score)))
            return r2, best_expr_py, trajectory

        # No hall-of-fame snapshot could be read at all -- fall back loudly.
        warnings.warn(
            f"[_fit_with_pysr_trajectory] no hall_of_fame.csv snapshot readable "
            f"at {csv_path} for label={label!r} after fit() completed; falling "
            f"back to model.sympy()/model.predict(). Trajectory will be empty.",
            RuntimeWarning, stacklevel=2,
        )
        from sklearn.metrics import r2_score
        y_pred = model.predict(X)
        r2 = float(r2_score(y, y_pred))
        best_expr = str(model.sympy())
        return r2, best_expr, trajectory
    finally:
        manager.shutdown()


# ── 8. Main experiment logic ───────────────────────────────────────────────
def run(seed: int = 42, temperature: float = 0.25, run_index: int = 1,
        n_candidates: "int | None" = None):
    """Run the Nguyen-12 benchmark directly (no subprocess recursion)."""
    import json
    import time

    # [FIX-4] Resolve output directory from RESULTS_DIR env var when set so
    # JSON lands under the CI artifact-upload path (OUT_BASE), not the
    # repo-local path that diverges inside the GitHub Actions runner workspace.
    _results_dir = _resolve_results_dir(_repo_results_dir)
    _results_dir.mkdir(parents=True, exist_ok=True)

    # [FIX-N3-ii-b, merged from _03.py] Filename now encodes temperature and
    # run_index so repeated runs at the same seed land in distinct files
    # instead of the first run's "already exists, skipping" guard silently
    # no-op'ing every subsequent repeat.
    _temp_tag = str(temperature).rstrip("0").rstrip(".").replace(".", "p") or "0"
    _out_path = _results_dir / f"exp3_nguyen12_seed{seed}_temp{_temp_tag}_run{run_index}.json"

    # [FIX-CACHE-SCHEMA, addresses audit #2] The "r2" field's MEANING changed
    # across script versions: earlier scripts (_02, _02_patched) report
    # TRAINING r2 under that key; this script (extrap-safe lineage)
    # deliberately redefines "r2" to mean EXTRAPOLATION r2. A cache file
    # written by an old script version has no version tag, so blindly
    # trusting "file exists -> reuse it" would silently hand back
    # mislabeled training-R2 numbers as if they were extrapolation-R2.
    # This script only ever reuses a cache file it can confirm was written
    # by a script of this same schema (schema_version below); anything else
    # (missing key, older/unversioned file, mismatched value) is treated as
    # absent and re-run from scratch rather than trusted.
    _SCHEMA_VERSION = "consolidated-extrap-r2-v1"
    if _out_path.exists():
        try:
            with open(_out_path) as _f:
                _cached = json.load(_f)
            if _cached.get("config", {}).get("schema_version") == _SCHEMA_VERSION:
                print(f"  ✓ Results already exist for seed={seed} temp={temperature} "
                      f"run={run_index} (schema={_SCHEMA_VERSION}), skipping re-run.")
                return _cached
            else:
                print(f"  ⚠ Cache at {_out_path} has no/mismatched schema_version "
                      f"(expected {_SCHEMA_VERSION}) — treating as stale and re-running "
                      f"rather than trusting a possibly differently-defined 'r2' field.")
        except (json.JSONDecodeError, OSError):
            print(f"  ⚠ Cache at {_out_path} unreadable — re-running.")

    # [FIX-CHECKPOINT] The old version of this script only ever wrote
    # exp3_nguyen12_seed{seed}.json ONCE, after the full 12-equation loop
    # finished (2 PySR fits/equation x up to METHOD_TIMEOUT=1100s each =
    # worst case ~440 min). That exceeds the CI worker's 330-min job
    # timeout, so if the runner is SIGKILLed mid-loop, NOTHING is ever
    # written -- not even the equations that had already finished --
    # because the write only happens after the loop. This is what produced
    # the "No exp3_nguyen12_seed*.json files found" failure with zero
    # output files on disk despite the job apparently running for hours.
    #
    # Fix: (1) write a checkpoint after every equation so completed work is
    # never lost, and (2) honour JOB_DEADLINE (already exported by
    # run_all.sh/CI but previously never read by this script) to stop
    # gracefully with a partial-but-valid JSON instead of being killed
    # mid-write.
    _start_time    = time.time()
    _job_deadline  = int(os.environ.get("JOB_DEADLINE", 0)) or None  # seconds; 0/unset = no cap
    _CKPT_PATH     = _results_dir / f"_exp3_seed{seed}_temp{_temp_tag}_run{run_index}_partial.json"

    def _save(results_hypatia, results_pysr, n_total, complete):
        h_recovered = sum(1 for r in results_hypatia if r["evaluation"]["r2"] >= 0.9999)
        p_recovered = sum(1 for r in results_pysr    if r["evaluation"]["r2"] >= 0.9999)
        payload = {
            "config": {
                "name": "nguyen12_exp3", "seed": seed, "n_tasks": n_total,
                "niterations": _niter, "populations": _pops,
                "timeout": _timeout, "use_llm": USE_LLM,
                # [FIX-CACHE-SCHEMA] lets a future run tell whether a cache
                # file was produced by this script's metric definitions
                # (extrapolation r2 + boundary-buffer fit) before reusing it.
                "schema_version": _SCHEMA_VERSION,
                # [FIX-N3-ii-b, merged from _03.py] previously unlogged —
                # a reader had to cross-reference hypatia.py's source to
                # know these values.
                "temperature": temperature, "n_candidates": _n_candidates,
                "llm_min_r2": _llm_min_r2,
                "llm_max_abs_pred": _llm_max_abs_pred,
                "llm_require_valid_guess": _llm_require_valid_guess,
                "run_index": run_index,
            },
            "results": {"hypatiax": results_hypatia, "pysr": results_pysr},
            "summary": {
                "h_recovered": h_recovered, "p_recovered": p_recovered,
                "n_total": n_total,
                "h_rate": h_recovered / n_total if n_total else 0.0,
                "p_rate": p_recovered / n_total if n_total else 0.0,
                "n_completed": len(results_hypatia),
                "complete": complete,
            },
        }
        _target = _out_path if complete else _CKPT_PATH
        _tmp = _target.with_suffix(".json.tmp")
        with open(_tmp, "w") as _f:
            json.dump(payload, _f, indent=2, default=str)
        os.replace(_tmp, _target)  # atomic — never leaves a truncated file if killed mid-write
        return payload

    def _write_canonical_seed_alias(payload):
        """Write the canonical exp3 filename expected by the CI validator.

        The workflow checks for `exp3_nguyen12_seed*.json` under the result dir.
        This script historically wrote only the run-indexed temp file name, which
        does not match the CI filename contract. Emitting the canonical alias keeps
        both the detailed run metadata and the expected exp3 filename in sync.
        """
        canonical_path = _results_dir / f"exp3_nguyen12_seed{seed}.json"
        tmp_path = canonical_path.with_suffix(".json.tmp")
        with open(tmp_path, "w") as _f:
            json.dump(payload, _f, indent=2, default=str)
        os.replace(tmp_path, canonical_path)
        return canonical_path

    # ── Config from env vars (smoke-test / paper-quality modes) ──────────
    _n_tasks        = int(os.environ.get("N_NGUYEN_TASKS", 12))
    _niter          = int(os.environ.get("N_ITERATIONS",   1000))
    _pops           = int(os.environ.get("POPULATIONS",    30))
    # FIX-WALLCLOCK: use PYSR_TIMEOUT (1100s) not a hardcoded 360s default.
    # No cap — repro.yaml values are authoritative.
    _pysr_timeout   = int(os.environ.get("PYSR_TIMEOUT",   1100))
    _method_timeout = int(os.environ.get("METHOD_TIMEOUT", _pysr_timeout))
    _timeout        = _pysr_timeout   # passed to PySR's timeout_in_seconds
    # [FIX-N3-ii-b/c, merged from _03.py] Named so it can be logged in the
    # config payload above, not just embedded inline in the get_llm_prior()
    # call below. The run() arg takes priority when given; otherwise falls
    # back to the pre-existing LLM_N_CANDIDATES env var / 8.
    _n_candidates   = n_candidates if n_candidates is not None else int(os.environ.get("LLM_N_CANDIDATES", 8))
    # [FIX-LLM-GATE] LLM guesses must pass a numerical safety/quality gate
    # before they are allowed into PySR.  The gate uses only training data and
    # the existing boundary-buffer data, never the held-out extrapolation set.
    _llm_min_r2 = float(os.environ.get("LLM_MIN_R2", "0.95"))
    _llm_max_abs_pred = float(os.environ.get("LLM_MAX_ABS_PRED", "1e12"))
    _llm_require_valid_guess = os.environ.get("LLM_REQUIRE_VALID_GUESS", "1").lower() not in {"0", "false", "no"}

    print(f"\n{'='*68}")
    print(f"  Exp 3 · Nguyen-12 SR suite  (§10.8)  SEED={seed}  TEMP={temperature}  RUN={run_index}")
    # [FIX-STALE-CLAIM, addresses audit #3] The 11/12 H (91.7%) figure was
    # never re-run/re-verified after the trajectory-monitor patch that
    # produced it — that patch's own docstring documents a prior,
    # never-located discrepancy bug (reported expression not reproducing
    # reported R^2 on 2/60 records) as its justification for the jump from
    # 7/12. This script also redefines "r2" to mean EXTRAPOLATION r2, not
    # the training r2 the 11/12 figure was computed against, so even if
    # verified that number would describe a different metric than the one
    # this script reports. Treat as UNVERIFIED until re-run end-to-end.
    print("  Expected: UNVERIFIED pending re-run — see [FIX-STALE-CLAIM] docstring note.")
    print("  Prior (unverified, different-metric) figures: 11/12 H (91.7%) train-r2 · "
          "10/12 P train-r2 · MW U=113, p=0.0097")
    print(f"  Config  : n_tasks={_n_tasks}  niterations={_niter}  populations={_pops}"
          f"  pysr_timeout={_timeout}s  method_timeout={_method_timeout}s"
          f"  temperature={temperature}  n_candidates={_n_candidates}")
    print(f"{'='*68}\n")

    # ── Import protocol data layer ────────────────────────────────────────
    try:
        from hypatiax.protocols.experiment_protocol_nguyen12 import NguYenProtocol
    except ImportError:
        # [FIX-IMPORT] 'protocols' is a subpackage of hypatiax/, not standalone.
        # Re-insert repo root and retry with the full dotted path.
        # [FIX-N3-ii-d] Same off-by-one as the primary _REPO_ROOT calc above —
        # this fallback path used parents[3] even after _03.py fixed the
        # primary computation to parents[2], so a failed primary import still
        # inserted a directory one level too high into sys.path. Fixed here.
        import pathlib as _pl
        _root = str(_pl.Path(__file__).resolve().parents[2])
        if _root not in sys.path:
            sys.path.insert(0, _root)
        from hypatiax.protocols.experiment_protocol_nguyen12 import NguYenProtocol

    # ── Import SR engine ──────────────────────────────────────────────────
    from pysr import PySRRegressor
    from sklearn.metrics import r2_score

    # [FIX-LLM-WARMSTART-GATE] Fail fast, once, before burning any LLM API
    # budget or PySR search time: if this pysr build's PySRRegressor.fit()
    # has no `guesses` parameter, the hybrid seeding this script depends on
    # cannot happen. Silently falling back to an unseeded H run here would
    # reproduce audit #1's exact failure mode (H and P identical) in a new
    # place -- so this refuses to run at all rather than degrade quietly.
    # Only enforced when USE_LLM is actually on; a pure-PySR-only run (no
    # API key / USE_LLM False) never needs `guesses` and shouldn't be
    # blocked by this check.
    #
    # NOTE: an earlier revision of this check (and the H-run call site)
    # looked for `guesses` on PySRRegressor.__init__ and passed it into the
    # constructor, on the mistaken premise that pysr==2.0.0a1 moved
    # `guesses` there. It didn't: per the pysr v2.0.0a1 release notes,
    # `guesses` is, and always was in this build, a `fit()`-level parameter
    # ("pass initial equation guesses to guide the search using the
    # `guesses` parameter to fit") -- there is no `guesses` on __init__ at
    # all. Checking __init__ made this guard raise unconditionally whenever
    # USE_LLM was on (a real installed pysr 2.0.0a1 never has `guesses` in
    # __init__'s signature), and the constructor call at the old H-run call
    # site would have raised TypeError on any build that actually enforces
    # its __init__ signature. Checking fit() is what actually reflects
    # whether this pysr build can accept guesses; see the matching change
    # at the H-run call site below (guesses now flows into model_h.fit(),
    # not into PySRRegressor(...)).
    if USE_LLM and "guesses" not in inspect.signature(PySRRegressor.fit).parameters:
        raise RuntimeError(
            "[FIX-LLM-WARMSTART-GATE] Installed pysr version's "
            "PySRRegressor.fit() has no 'guesses' parameter, so LLM "
            "warm-start candidates cannot be wired into the PySR search. "
            "Upgrade pysr, or set USE_LLM=False / unset the API key to run "
            "PySR-only intentionally. Refusing to start rather than silently "
            "fall back to an unseeded H run -- see audit-exp3.txt item #1."
        )

    # ── Import LLM warm-start ─────────────────────────────────────────────
    # hypatia.py must be committed to the repo at:
    #   hypatiax/experiments/benchmarks/hypatia.py   (next to this script)
    # [BUG-HYPATIA-FIX] Previously the import silently failed in CI because
    # hypatia.py was not committed to the repository. The bench_dir sys.path
    # insertion is correct, but the file must actually exist there.
    # We raise an explicit ImportError with a remediation message so the
    # failure is actionable rather than a cryptic ModuleNotFoundError.
    _bench_dir = pathlib.Path(__file__).resolve().parent
    _hypatia_path = _bench_dir / "hypatia.py"
    if not _hypatia_path.exists():
        raise ImportError(
            f"hypatia.py not found at {_hypatia_path}\n"
            "  Fix: commit hypatia.py to hypatiax/experiments/benchmarks/ in the repo.\n"
            "  The file provides get_llm_prior() for the LLM warm-start prior."
        )
    if str(_bench_dir) not in sys.path:
        sys.path.insert(0, str(_bench_dir))
    from hypatia import get_llm_prior

    # ── Load all 12 Nguyen equations ──────────────────────────────────────
    all_cases = NguYenProtocol.load_all(num_samples=200, noise_level=0.0, seed=seed)

    # [FIX-2/FIX-5] Apply filters in the correct order:
    #   1. _apply_task_ids_nguyen — shard/CI filter (TASK_IDS / SHARD_IDS)
    #   2. _apply_case_range      — positional slice (CASE_RANGE_START/END)
    #   3. [:_n_tasks]            — smoke-test ceiling (N_NGUYEN_TASKS)
    #
    # Old order was [:_n_tasks] first, then _apply_task_ids_nguyen, which
    # could silently exclude shard-assigned IDs that fell beyond the ceiling.
    # _apply_case_range was previously and incorrectly applied to the sys.path
    # list; it is now applied here to the actual test-case sequence.
    all_cases = _apply_task_ids_nguyen(all_cases)  # CI shard filter  (FIX-1 / FIX-3)
    all_cases = _apply_case_range(all_cases)        # positional slice (FIX-2)
    all_cases = all_cases[:_n_tasks]                # smoke-test cap   (FIX-5)

    results_hypatia = []
    results_pysr    = []
    # [KNOWN-BUG-1] tracked only to surface the end-of-run warning below —
    # does not change any fitting behavior.
    llm_exprs_any_used = False

    for i, (desc, X, y, var_names, meta) in enumerate(all_cases):
        nid = meta["nguyen_id"]
        print(f"\n  [{i+1}/{len(all_cases)}] {nid} — {meta['ground_truth']}")

        # ── Build eq_dict for get_llm_prior ──────────────────────────────
        eq_dict = {
            "id":           nid,
            "vars":         var_names,
            "formula_hint": meta["formula_hint"],
            "formula":      meta["ground_truth"],
        }

        # ── LLM warm-start candidates ─────────────────────────────────────
        llm_exprs = []
        llm_error = None
        if USE_LLM:
            try:
                llm_exprs = get_llm_prior(
                    eq_dict, X, y,
                    n_candidates=_n_candidates,
                    verbose=False,
                    model=os.environ["LLM_MODEL"],
                    temperature=temperature,
                ) or []
                print(f"    LLM candidates: {llm_exprs[:3]} ...")
            except Exception as _e:
                llm_error = f"{type(_e).__name__}: {_e}"
                print(f"    ✗ LLM warm-start failed: {_e}")

        # ── Shared PySR config ────────────────────────────────────────────
        _pysr_kwargs = dict(
            niterations=_niter,
            populations=_pops,
            timeout_in_seconds=_timeout,
            random_state=seed,
            deterministic=True,
            parallelism="serial",
            verbosity=0,
            progress=False,
            # [FIX-SAFE-POW] The old [CONSTRAINTS-FIX] pass restricted "^"'s
            # exponent to a single leaf (constraints={"^": (-1, 1)}) to stop
            # PySR fitting whole-subexpression exponents. That did NOT stop
            # it fitting e.g. sin(x) ^ 1.84 -- a bare-constant exponent, so
            # it satisfied the constraint -- which is undefined/NaN the
            # moment sin(x) goes negative, and was the actual cause of the
            # N7/seed777 extrapolation failure (train R^2 -> 0.999999998,
            # extrap R^2 -> NaN for the back half of the run). Every
            # Nguyen-12-family ground truth only ever needs small INTEGER
            # powers of a bare variable (x**4, x**3, y**2), so instead of
            # trying to constrain "^" further, remove it entirely and give
            # PySR dedicated integer-power unary ops it can compose (e.g.
            # x**4 = square(square(x))). This makes fractional/negative-base
            # powers structurally unreachable rather than just discouraged.
            binary_operators=["+", "-", "*", "/"],
            unary_operators=["sin", "cos", "log", "sqrt", "exp",
                              "square", "cube"],
        )

        # [FIX-SINGULARITY-BUFFER] Fit on the training domain PLUS a thin
        # boundary band so near-boundary singularities (e.g. 1/cos(x) just
        # past x=1) show up in the loss during search, not only on the real
        # held-out extrapolation split afterwards. r2_h/r2_p are still
        # scored against the original (X, y) only -- see X_score/y_score
        # below -- so "training R^2" keeps meaning what it always meant.
        X_fit, y_fit = _build_boundary_buffer(X, y, meta, var_names)

        # ── HypatiaX run (PySR + LLM warm-start) ─────────────────────────
        # [FIX-LLM-WARMSTART, resolves audit-exp3.txt item #1] llm_exprs
        # are now actually converted (see _llm_exprs_to_pysr_guesses) and
        # passed into model_h.fit(guesses=...) below. P (further down)
        # deliberately does NOT receive guesses, so H vs P is now a real
        # hybrid-vs-baseline comparison instead of the same PySR fit run
        # twice. `llm_guesses_used` is recorded on this record (not just
        # a module-level flag) so a per-equation conversion failure is
        # auditable after the fact, not just visible in the run log.
        pysr_guesses = []
        n_llm_candidates = len(llm_exprs)
        llm_candidates_parsed = 0
        llm_gate_audit = []
        llm_gate_failed = False
        if llm_exprs:
            converted = _llm_exprs_to_pysr_guesses(llm_exprs, var_names)
            llm_candidates_parsed = len(converted)
            pysr_guesses, llm_gate_audit = _validate_llm_pysr_guesses(
                converted, X, y, X_fit, y_fit, var_names,
                min_r2=_llm_min_r2, max_abs_pred=_llm_max_abs_pred)
            if pysr_guesses:
                llm_exprs_any_used = True
                print(f"    ✓ [FIX-LLM-GATE] accepted {len(pysr_guesses)}/"
                      f"{n_llm_candidates} LLM candidate(s) for PySR "
                      f"(parsed={llm_candidates_parsed}, min_r2={_llm_min_r2:g}).")
            else:
                llm_gate_failed = True
                print(f"    ✗ [FIX-LLM-GATE] no LLM candidate passed numerical "
                      f"validation for {nid} (parsed={llm_candidates_parsed}/"
                      f"{n_llm_candidates}, min_r2={_llm_min_r2:g}).")
        elif USE_LLM:
            llm_gate_failed = True
            if llm_error:
                print(f"    ✗ [FIX-LLM-GATE] LLM unavailable; no hybrid seed is valid.")
            else:
                print(f"    ✗ [FIX-LLM-GATE] LLM returned no candidates; no hybrid seed is valid.")
        t0 = time.time()
        try:
            # [FIX-LLM-GATE] In strict mode, USE_LLM means H must actually be
            # a hybrid run. Do not silently relabel an LLM outage, parse failure,
            # or numerically invalid candidate as "H = unseeded PySR".
            if USE_LLM and llm_gate_failed and _llm_require_valid_guess:
                raise RuntimeError(
                    "LLM warm-start gate failed; no validated LLM guess available "
                    "(set LLM_REQUIRE_VALID_GUESS=0 only for an explicitly "
                    "non-strict fallback run)"
                )
            # [FIX-LLM-WARMSTART-GATE] `guesses` is a PySRRegressor.fit()
            # parameter in this pysr build (2.0.0a1), not a constructor
            # argument -- see the module-level guard above, and the real
            # pysr v2.0.0a1 release notes ("pass initial equation guesses
            # to guide the search using the `guesses` parameter to fit").
            # Passing it into PySRRegressor(...) instead (the prior
            # revision of this code) raised TypeError on construction for
            # any build that enforces its __init__ signature, which would
            # have defeated the hybrid-vs-baseline comparison entirely.
            # `guesses` is only included in fit_kwargs when there's at
            # least one converted candidate, so a no-candidates H run still
            # calls fit() exactly as before (no guesses kwarg at all,
            # rather than an explicit guesses=None).
            model_h = PySRRegressor(
                **_pysr_kwargs,
                warm_start=False,
            )
            r2_h, best_expr_h, trajectory_h = _fit_with_pysr_trajectory(
                model_h, X_fit, y_fit, var_names, label="H",
                X_score=X, y_score=y,
                fit_kwargs=({"guesses": pysr_guesses} if pysr_guesses else None),
            )
        except Exception as _e:
            print(f"    ✗ HypatiaX run failed: {_e}")
            r2_h        = float("-inf")
            best_expr_h = "FAILED"
            trajectory_h = []
        elapsed_h = time.time() - t0

        # ── PySR-only run (no LLM) ────────────────────────────────────────
        t0 = time.time()
        try:
            model_p = PySRRegressor(**_pysr_kwargs)
            r2_p, best_expr_p, trajectory_p = _fit_with_pysr_trajectory(
                model_p, X_fit, y_fit, var_names, label="P",
                X_score=X, y_score=y,
            )
        except Exception as _e:
            print(f"    ✗ PySR-only run failed: {_e}")
            r2_p        = float("-inf")
            best_expr_p = "FAILED"
            trajectory_p = []
        elapsed_p = time.time() - t0

        # [FIX-EXTRAP-R2] r2_h/r2_p above are scored against (X, y) --
        # the TRAINING split (see NguyenEquation.generate: it returns
        # X_train/y_train as the 2nd/3rd tuple elements; X_extrap/y_extrap
        # only ever land in `meta`, never in the (X, y) passed into
        # _fit_with_pysr_trajectory). These results are written under
        # hypatiax/data/results/extrapolation/ and compared against THRESH
        # as if they were held-out extrapolation scores -- but until now
        # nothing ever actually scored the final expression against
        # meta["X_extrap"]/meta["y_extrap"]. That let a model that fits
        # the training range near-perfectly but diverges outside it
        # (e.g. N12/seed99, R²≈0.99996 train vs R²≈-1.07 extrap) get
        # silently reported and thresholded as a training-domain number
        # wearing an "extrapolation" label. Re-score both systems' final
        # expressions against the extrap split (when the equation has
        # one) and report THAT as the headline `r2`, keeping the
        # training score alongside it rather than discarding it.
        # [FIX-EXTRAP-R2-STRICT] Every one of the 12 Nguyen equations has
        # extrapolation_test=True, so X_ext/y_ext should always be present
        # here -- the only way they're missing is if NguyenEquation.generate
        # hit an exception building the extrap split (e.g. a domain error
        # like log/sqrt of a negative value for a specific seed, the kind
        # of thing seen for N12/seed777). That's a real degraded-evaluation
        # condition, not a "shrug and fall back to training R²" condition:
        # silently substituting r2_h/r2_p here is exactly the bug this
        # patch exists to remove, just moved one level down. But this loop
        # also checkpoints after every equation and honours JOB_DEADLINE
        # for graceful early exit (see _save() call below and the deadline
        # check that follows it) -- hard-crashing the whole run on one
        # equation's missing extrap split would throw away every
        # checkpoint after it. So: don't raise, but never let a missing
        # extrap score masquerade as a real one. Loudly warn, and mark the
        # record with an explicit sentinel (-inf, extrap_missing=True) so
        # any downstream detector/threshold check treats it as an
        # unresolved failure, never as an accidental pass.
        X_ext, y_ext = meta.get("X_extrap"), meta.get("y_extrap")
        extrap_missing = X_ext is None or y_ext is None
        if extrap_missing:
            warnings.warn(
                f"[{nid}/seed{seed}] no extrapolation data available "
                "(NguyenEquation.generate likely hit a domain error "
                "building the extrap split) -- reporting r2=-inf rather "
                "than silently falling back to training-domain R².",
                RuntimeWarning, stacklevel=2,
            )
        r2_h_extrap = None if extrap_missing else _score_expr(best_expr_h, X_ext, y_ext, var_names)
        r2_p_extrap = None if extrap_missing else _score_expr(best_expr_p, X_ext, y_ext, var_names)
        r2_h_report = r2_h_extrap if r2_h_extrap is not None else float("-inf")
        r2_p_report = r2_p_extrap if r2_p_extrap is not None else float("-inf")

        # ── Per-equation summary ──────────────────────────────────────────
        THRESH = 0.9999
        h_ok   = "✅" if r2_h_report >= THRESH else "✗"
        p_ok   = "✅" if r2_p_report >= THRESH else "✗"
        print(f"    H  {h_ok}  R²={r2_h_report:.7f} (train={r2_h:.7f})  expr={best_expr_h}  ({elapsed_h:.1f}s)")
        print(f"    P  {p_ok}  R²={r2_p_report:.7f} (train={r2_p:.7f})  expr={best_expr_p}  ({elapsed_p:.1f}s)")

        results_hypatia.append({
            "system":     "hypatiax",
            "metadata":   meta,
            "expression": best_expr_h,
            "evaluation": {
                "r2":              r2_h_report,   # extrap score, or -inf if extrap data is unavailable -- NEVER a silent training-R² fallback
                "r2_train":        r2_h,
                "r2_extrap":       r2_h_extrap,    # None if extrap scoring wasn't possible
                "extrap_missing":  extrap_missing,
            },
            "elapsed":    elapsed_h,
            "trajectory": trajectory_h,
            # [FIX-LLM-WARMSTART] Per-equation audit trail for the hybrid
            # seeding, so "was H actually hybrid for THIS record" never
            # has to be inferred from the run-level llm_exprs_any_used
            # flag or the console log.
            "llm_guesses_used":       len(pysr_guesses),
            "llm_candidates_total":   n_llm_candidates,
            "llm_candidates_parsed":  llm_candidates_parsed,
            "llm_gate_failed":        llm_gate_failed,
            "llm_gate_strict":        _llm_require_valid_guess,
            "llm_gate_min_r2":        _llm_min_r2,
            "llm_gate_audit":         llm_gate_audit,
            "llm_error":              llm_error,
        })
        results_pysr.append({
            "system":     "pysr",
            "metadata":   meta,
            "expression": best_expr_p,
            "evaluation": {
                "r2":              r2_p_report,
                "r2_train":        r2_p,
                "r2_extrap":       r2_p_extrap,
                "extrap_missing":  extrap_missing,
            },
            "elapsed":    elapsed_p,
            "trajectory": trajectory_p,
        })

        # [FIX-CHECKPOINT-CALL] Save checkpoint after each equation ────────
        _save(results_hypatia, results_pysr, len(all_cases), complete=False)

        # ── Check JOB_DEADLINE and exit gracefully if running out of time ──
        if _job_deadline:
            elapsed = time.time() - _start_time
            if elapsed > _job_deadline * 0.9:  # exit at 90% of deadline
                print(f"\n⏰ Approaching job deadline ({elapsed:.0f}s/{_job_deadline}s)")
                print(f"   Saving partial results ({len(results_hypatia)}/{len(all_cases)} completed) and exiting gracefully...")
                break  # exit loop, save final checkpoint below

    # ── Aggregate summary ─────────────────────────────────────────────────
    THRESH      = 0.9999
    h_recovered = sum(1 for r in results_hypatia if r["evaluation"]["r2"] >= THRESH)
    p_recovered = sum(1 for r in results_pysr    if r["evaluation"]["r2"] >= THRESH)
    n           = len(all_cases)

    print(f"\n{'='*68}")
    print(f"  RESULTS  (strict R²≥{THRESH}, seed={seed}, temp={temperature}, run={run_index})")
    print(f"  HypatiaX : {h_recovered}/{n}  ({100*h_recovered/n:.1f}%)")
    print(f"  PySR-only: {p_recovered}/{n}  ({100*p_recovered/n:.1f}%)")
    # [FIX-STALE-CLAIM, addresses audit #3] see note earlier in run() —
    # this figure is unverified and was computed against a different
    # metric (training r2) than the one this script reports (extrap r2).
    print("  Expected : UNVERIFIED pending re-run (prior figure, different metric: "
          "11/12 H (91.7%) train-r2 · 10/12 P)")
    n_h_with_guesses = sum(1 for r in results_hypatia if r.get("llm_guesses_used"))
    print(f"  LLM guesses used: {n_h_with_guesses}/{n} equation(s) had >=1 "
          f"converted LLM candidate wired into the H run "
          f"[FIX-LLM-WARMSTART, resolves audit-exp3.txt item #1].")
    if not llm_exprs_any_used:
        # [FIX-LLM-WARMSTART] This is no longer the audit #1 bug (that
        # path is fixed) -- it now means either USE_LLM was off this run
        # (no API key / disabled), or every LLM candidate this run failed
        # to convert to this script's PySR operator set. Either way, H and
        # P below are NOT a hybrid-vs-baseline comparison for this run;
        # check the per-equation "⚠ [FIX-LLM-WARMSTART] ... skipped" lines
        # above (or each record's llm_guesses_used field) to see which.
        print("  ⚠ No LLM guesses were wired into any H run this session — "
              "HypatiaX and PySR-only results above are NOT a hybrid-vs-"
              "baseline comparison for this run. Check USE_LLM and the "
              "per-equation conversion warnings above.")
    print(f"{'='*68}\n")

    # ── Save JSON output (final) ──────────────────────────────────────────
    # [FIX-4] _results_dir already resolved above via _resolve_results_dir().
    # [FIX-CHECKPOINT-CALL] Use _save() for final output too (complete=True).
    result = _save(results_hypatia, results_pysr, len(all_cases), complete=True)
    canonical_output = _write_canonical_seed_alias(result)

    OUTPUT_JSON = str(_out_path)
    print("\n  Protocol returned: success")
    print(f"  JSON: {OUTPUT_JSON}")
    print(f"  Canonical exp3 seed alias: {canonical_output}")

    # Notebook download link (Colab/Jupyter only — skipped in CLI)
    try:
        _ipy = get_ipython()  # type: ignore[name-defined]
    except NameError:
        _ipy = None
    if _ipy is not None:
        import base64
        from IPython.display import HTML, display
        _jpath = pathlib.Path(OUTPUT_JSON)
        if _jpath.exists():
            _data = base64.b64encode(_jpath.read_bytes()).decode()
            display(HTML(
                '<div style="border:1px solid #ccc;border-radius:6px;padding:12px;background:#f9f9f9">'
                f'<b>⬇ Download experiment outputs</b><ul>'
                f'<li><a href="data:application/json;base64,{_data}" download="{_jpath.name}">'
                f'📄 JSON results</a> ({_jpath.stat().st_size / 1024:.1f} KB)</li>'
                '</ul></div>'
            ))

    return result


# ── 9. Entry point ──────────────────────────────────────────────────────── [...]
if __name__ == "__main__":
    run(seed=SEED, temperature=_args.temperature, run_index=_args.run_index,
        n_candidates=_args.n_candidates)
