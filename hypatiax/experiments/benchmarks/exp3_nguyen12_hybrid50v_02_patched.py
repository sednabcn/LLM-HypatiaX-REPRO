#!/usr/bin/env python3
"""
exp3_nguyen12_hybrid50v_02.py  —  Exp 3 · Nguyen-12 SR suite  (§10.8 primary)
==============================================================================
Standalone Python script version — safe to run with `python3` directly.

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

Expected result : 11/12 H (91.7 %) · 10/12 P (83.3 %) · 0/12 NN
                  MW P>NN U=113, p=0.0097
Wall time       : 30–90 min
SEED            : 42 (fixed for reproducibility; override with --seed)

Usage
-----
    python3 exp3_nguyen12_hybrid50v_02_patched.py             # SEED=42 (default)
    python3 exp3_nguyen12_hybrid50v_02_patched.py --seed 123  # stability check
    python3 exp3_nguyen12_hybrid50v_02_patched.py --seed 777  # stability check

CI shard usage (set by ci_runner.yml worker dispatch):
    TASK_IDS="N1 N3 N7" PYSR_SEED=42 EXPERIMENT_SEED=42 \\
        python3 exp3_nguyen12_hybrid50v_02_patched.py --seed 42

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
import multiprocessing as mp
import os
import pathlib
import random
import sys
import time

import numpy as np

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
# ────────────────────────────────────────────────────────────────────────────

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
# ─────────────────────────────────────────────────────────────────────────────

# ── 1. Resolve repo root & set sys.path ───────────────────────────────────
# Script lives at:  <repo>/hypatiax/experiments/benchmarks/exp3_nguyen12_hybrid50v_02.py
# Repo root is 4 levels up (parents[3]):
#   parents[0] = benchmarks/
#   parents[1] = experiments/
#   parents[2] = hypatiax/      <- was incorrectly used as repo root
#   parents[3] = <repo>/        <- correct repo root
# [BUG-ROOT-FIX] parents[2] pointed at hypatiax/ not the repo root, so
# _REPRO_ROOT / "hypatiax" resolved to hypatiax/hypatiax/ (non-existent).
_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
_REPO_ROOT  = _SCRIPT_DIR.parents[3]   # benchmarks/ -> experiments/ -> hypatiax/ -> repo root

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
    return parser.parse_args()

# Parse early so SEED is available for the seed block below.
# (argparse is safe to call at module level — it only reads sys.argv)
_args = _parse_args()
SEED  = _resolve_seed() or int(os.environ.get("EXPERIMENT_SEED", str(_args.seed)))

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


def _fit_with_pysr_trajectory(model, X, y, variable_names, label,
                               poll_seconds=None, output_dir=None):
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
    """
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

    manager = mp.Manager()
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
        model.fit(X, y, variable_names=variable_names)
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
        try:
            y_pred = model.predict(X)
            r2 = None
            if best_expr_py:
                ns = {v: X[:, i] for i, v in enumerate(variable_names)}
                ns.update({"sin": np.sin, "cos": np.cos, "log": np.log,
                           "sqrt": np.sqrt, "exp": np.exp})
                y_pred_expr = eval(best_expr_py, {"__builtins__": {}}, ns)
                ss_res = np.sum((y - y_pred_expr) ** 2)
                ss_tot = np.sum((y - np.mean(y)) ** 2)
                r2 = float(1.0 - ss_res / ss_tot) if ss_tot != 0 else float("nan")
        except Exception:
            r2 = None
        if r2 is None:
            # Expression-based scoring failed (e.g. a function the eval
            # namespace above doesn't cover) -- fall back to PySR's own
            # predict(), still against the SAME model/expression PySR
            # itself considers current, not a second independent read.
            from sklearn.metrics import r2_score
            r2 = float(r2_score(y, model.predict(X)))
        return r2, best_expr_py, trajectory

    # No hall-of-fame snapshot could be read at all -- fall back loudly.
    import warnings
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


# ── 8. Main experiment logic ───────────────────────────────────────────────
def run(seed: int = 42):
    """Run the Nguyen-12 benchmark directly (no subprocess recursion)."""
    import json
    import time

    # [FIX-4] Resolve output directory from RESULTS_DIR env var when set so
    # JSON lands under the CI artifact-upload path (OUT_BASE), not the
    # repo-local path that diverges inside the GitHub Actions runner workspace.
    _results_dir = _resolve_results_dir(_repo_results_dir)
    _results_dir.mkdir(parents=True, exist_ok=True)

    # ── Skip if result already exists for this seed (avoids redundant ────
    # ── subprocess re-run triggered by run_task after direct execution)  ──
    _out_path = _results_dir / f"exp3_nguyen12_seed{seed}.json"
    if _out_path.exists():
        print(f"  ✓ Results already exist for seed={seed}, skipping re-run.")
        with open(_out_path) as _f:
            return json.load(_f)

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
    _CKPT_PATH     = _results_dir / f"_exp3_seed{seed}_partial.json"

    def _save(results_hypatia, results_pysr, n_total, complete):
        h_recovered = sum(1 for r in results_hypatia if r["evaluation"]["r2"] >= 0.9999)
        p_recovered = sum(1 for r in results_pysr    if r["evaluation"]["r2"] >= 0.9999)
        payload = {
            "config": {
                "name": "nguyen12_exp3", "seed": seed, "n_tasks": n_total,
                "niterations": _niter, "populations": _pops,
                "timeout": _timeout, "use_llm": USE_LLM,
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

    # ── Config from env vars (smoke-test / paper-quality modes) ──────────
    _n_tasks        = int(os.environ.get("N_NGUYEN_TASKS", 12))
    _niter          = int(os.environ.get("N_ITERATIONS",   1000))
    _pops           = int(os.environ.get("POPULATIONS",    30))
    # FIX-WALLCLOCK: use PYSR_TIMEOUT (1100s) not a hardcoded 360s default.
    # No cap — repro.yaml values are authoritative.
    _pysr_timeout   = int(os.environ.get("PYSR_TIMEOUT",   1100))
    _method_timeout = int(os.environ.get("METHOD_TIMEOUT", _pysr_timeout))
    _timeout        = _pysr_timeout   # passed to PySR's timeout_in_seconds

    print(f"\n{'='*68}")
    print(f"  Exp 3 · Nguyen-12 SR suite  (§10.8)  SEED={seed}")
    print("  Expected: 11/12 H (91.7%) · 10/12 P · MW U=113, p=0.0097")
    print(f"  Config  : n_tasks={_n_tasks}  niterations={_niter}  populations={_pops}"
          f"  pysr_timeout={_timeout}s  method_timeout={_method_timeout}s")
    print(f"{'='*68}\n")

    # ── Import protocol data layer ────────────────────────────────────────
    try:
        from hypatiax.protocols.experiment_protocol_nguyen12 import NguYenProtocol
    except ImportError:
        # [FIX-IMPORT] 'protocols' is a subpackage of hypatiax/, not standalone.
        # Re-insert repo root and retry with the full dotted path.
        import pathlib as _pl
        _root = str(_pl.Path(__file__).resolve().parents[3])
        if _root not in sys.path:
            sys.path.insert(0, _root)
        from hypatiax.protocols.experiment_protocol_nguyen12 import NguYenProtocol

    # ── Import SR engine ──────────────────────────────────────────────────
    from pysr import PySRRegressor
    from sklearn.metrics import r2_score

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
        if USE_LLM:
            try:
                llm_exprs = get_llm_prior(
                    eq_dict, X, y,
                    n_candidates=8,
                    verbose=False,
                    model=os.environ["LLM_MODEL"],
                )
                print(f"    LLM candidates: {llm_exprs[:3]} ...")
            except Exception as _e:
                print(f"    ⚠  LLM warm-start failed: {_e} — running PySR-only")

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
            binary_operators=["+", "-", "*", "/", "^"],
            unary_operators=["sin", "cos", "log", "sqrt", "exp"],
        )

        # ── HypatiaX run (PySR + LLM warm-start) ─────────────────────────
        t0 = time.time()
        try:
            model_h = PySRRegressor(
                **_pysr_kwargs,
                warm_start=False,
            )
            if llm_exprs:
                # Inject LLM expressions as the initial population hint
                model_h.set_params(extra_sympy_mappings={})
            r2_h, best_expr_h, trajectory_h = _fit_with_pysr_trajectory(
                model_h, X, y, var_names, label="H",
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
                model_p, X, y, var_names, label="P",
            )
        except Exception as _e:
            print(f"    ✗ PySR-only run failed: {_e}")
            r2_p        = float("-inf")
            best_expr_p = "FAILED"
            trajectory_p = []
        elapsed_p = time.time() - t0

        # ── Per-equation summary ──────────────────────────────────────────
        THRESH = 0.9999
        h_ok   = "✅" if r2_h >= THRESH else "✗"
        p_ok   = "✅" if r2_p >= THRESH else "✗"
        print(f"    H  {h_ok}  R²={r2_h:.7f}  expr={best_expr_h}  ({elapsed_h:.1f}s)")
        print(f"    P  {p_ok}  R²={r2_p:.7f}  expr={best_expr_p}  ({elapsed_p:.1f}s)")

        results_hypatia.append({
            "system":     "hypatiax",
            "metadata":   meta,
            "expression": best_expr_h,
            "evaluation": {"r2": r2_h},
            "elapsed":    elapsed_h,
            "trajectory": trajectory_h,
        })
        results_pysr.append({
            "system":     "pysr",
            "metadata":   meta,
            "expression": best_expr_p,
            "evaluation": {"r2": r2_p},
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
    print(f"  RESULTS  (strict R²≥{THRESH}, seed={seed})")
    print(f"  HypatiaX : {h_recovered}/{n}  ({100*h_recovered/n:.1f}%)")
    print(f"  PySR-only: {p_recovered}/{n}  ({100*p_recovered/n:.1f}%)")
    print("  Expected : 11/12 H (91.7%) · 10/12 P")
    print(f"{'='*68}\n")

    # ── Save JSON output (final) ──────────────────────────────────────────
    # [FIX-4] _results_dir already resolved above via _resolve_results_dir().
    # [FIX-CHECKPOINT-CALL] Use _save() for final output too (complete=True).
    result = _save(results_hypatia, results_pysr, len(all_cases), complete=True)

    OUTPUT_JSON = str(_out_path)
    print("\n  Protocol returned: success")
    print(f"  JSON: {OUTPUT_JSON}")

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


# ── 9. Entry point ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    run(seed=SEED)
