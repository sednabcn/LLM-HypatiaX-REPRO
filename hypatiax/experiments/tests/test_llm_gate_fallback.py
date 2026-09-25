#!/usr/bin/env python3
"""
test_llm_gate_fallback.py
==========================

Purpose
-------
Exercises `exp3_nguyen12_consolidated.py` with `LLM_REQUIRE_VALID_GUESS=0`
(the documented non-strict fallback switch, see line ~1154/1379 of that
script) and answers two questions:

  1. FOCUSED: does Nguyen-5 (N5) actually recover now, across the seeds
     where it previously gate-aborted (99, 777) or converged poorly (2024)?

  2. REGRESSION: do the tasks that already passed under the strict gate
     (e.g. N1, N2, N6, N8, N10, N11 -- 5/5 across all seeds in the
     baseline) still pass once the fallback is enabled? Flipping the gate
     off should be a no-op for any task where the gate never fired in the
     first place, but this checks that assumption instead of assuming it.

It does NOT re-implement any SR logic -- it drives the real script as a
subprocess (so it exercises the actual code path, not a mock of it) and
diffs the resulting JSON against the baseline result files you already
have on disk.

Requirements to actually execute (this harness does not stub these out):
  - The real repo checkout with hypatiax/, PySR, juliacall/Julia, sklearn,
    sympy, and hypatia.py present (same requirements as the script itself).
  - ANTHROPIC_API_KEY set (USE_LLM needs it; without it the script forces
    USE_LLM=False and the LLM gate never engages at all, which would make
    this test meaningless).
  - Wall-clock budget: each (seed, task) pair can take up to
    PYSR_TIMEOUT seconds x 2 (H + P) per the script's own numbers
    (~5-9 min/task observed in the seed42/99/123/777/2024 result files).
    The default CLI below only touches N5 plus a small regression sample
    to keep this tractable; use --full-regression to check all 12 tasks.

Usage
-----
    # Focused N5 check + small regression sample, seeds 42/99/123/777/2024
    python3 test_llm_gate_fallback.py \\
        --script /path/to/exp3_nguyen12_consolidated.py \\
        --baseline-dir /mnt/user-data/uploads \\
        --results-dir /tmp/gate_fallback_results

    # Also re-check every task (full regression, slow)
    python3 test_llm_gate_fallback.py \\
        --script /path/to/exp3_nguyen12_consolidated.py \\
        --baseline-dir /mnt/user-data/uploads \\
        --results-dir /tmp/gate_fallback_results \\
        --full-regression

    # Dry run: prints the exact subprocess commands/env without executing
    # PySR/Julia/the LLM -- use this to sanity-check the harness itself.
    python3 test_llm_gate_fallback.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────

RECOVERY_THRESHOLD = 0.9999  # matches the script's own h_recovered/p_recovered def

# Baseline seeds we have prior results for (seed -> filename glob in --baseline-dir)
BASELINE_FILES = {
    42:   "exp3_nguyen12_seed42.json",
    99:   "exp3_nguyen12_seed99_nshards01.json",
    123:  "exp3_nguyen12_seed123_nshards02.json",
    777:  "exp3_nguyen12_seed777_nshards03.json",
    2024: "exp3_nguyen12_seed2024_nshards04.json",
}

ALL_TASKS = [f"N{i}" for i in range(1, 13)]

# Tasks that were 5/5 recovered (H) across ALL 5 baseline seeds, i.e. the
# gate never fired against them. These are the regression canaries: if
# flipping LLM_REQUIRE_VALID_GUESS to 0 breaks any of these, something in
# the fallback path itself (not just the gate) is broken.
REGRESSION_CANARY_TASKS = ["N1", "N2", "N6", "N8", "N10", "N11"]

# The task under focused investigation.
FOCUS_TASK = "N5"


# ─────────────────────────────────────────────────────────────────────────
# Baseline loading
# ─────────────────────────────────────────────────────────────────────────

def load_baseline(baseline_dir: Path) -> dict:
    """Returns {seed: {task_name: {"h_r2": float|None, "p_r2": float|None}}}."""
    baseline = {}
    for seed, fname in BASELINE_FILES.items():
        path = baseline_dir / fname
        if not path.exists():
            print(f"  [baseline] WARNING: {path} not found, skipping seed {seed}")
            continue
        with open(path) as f:
            d = json.load(f)
        per_task = {}
        h_list = d["results"]["hypatiax"]
        p_list = d["results"]["pysr"]
        for h, p in zip(h_list, p_list):
            name = h["metadata"]["name"]              # e.g. "Nguyen-5"
            short = "N" + name.split("-")[1]            # -> "N5"
            per_task[short] = {
                "h_r2": _safe_r2(h["evaluation"]["r2"]),
                "p_r2": _safe_r2(p["evaluation"]["r2"]),
            }
        baseline[seed] = per_task
    return baseline


def _safe_r2(x) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, float) and (x != x or x in (float("inf"), float("-inf"))):
        return None
    return float(x)


def recovered(r2: Optional[float]) -> bool:
    return r2 is not None and r2 >= RECOVERY_THRESHOLD


# ─────────────────────────────────────────────────────────────────────────
# Running the real script
# ─────────────────────────────────────────────────────────────────────────

def run_case(
    script: Path,
    seed: int,
    task_ids: list[str],
    results_dir: Path,
    run_index: int,
    require_valid_guess: bool,
    temperature: float = 0.25,
    n_candidates: Optional[int] = None,
    timeout_s: int = 3600,
    dry_run: bool = False,
) -> Optional[dict]:
    """Runs exp3_nguyen12_consolidated.py for one seed against `task_ids`
    with LLM_REQUIRE_VALID_GUESS set as requested, in an isolated
    results_dir so it can never silently return a cached result written
    under the old (strict) flag. Returns the parsed result JSON, or None
    if the run failed / dry-run.
    """
    results_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["TASK_IDS"] = " ".join(task_ids)
    env["LLM_REQUIRE_VALID_GUESS"] = "1" if require_valid_guess else "0"
    env["RESULTS_DIR"] = str(results_dir)
    # Belt-and-suspenders: RESULTS_DIR + run_index together guarantee this
    # invocation's output filename can't collide with any prior run's
    # cache, regardless of what LLM_REQUIRE_VALID_GUESS was set to before.
    env["EXPERIMENT_SEED"] = str(seed)

    cmd = [
        sys.executable, str(script),
        "--seed", str(seed),
        "--temperature", str(temperature),
        "--run-index", str(run_index),
    ]
    if n_candidates is not None:
        cmd += ["--n-candidates", str(n_candidates)]

    tag = "FALLBACK(off)" if not require_valid_guess else "STRICT(on)"
    print(f"  [{tag}] seed={seed} tasks={task_ids} run_index={run_index}")

    if dry_run:
        print(f"    would run: TASK_IDS='{env['TASK_IDS']}' "
              f"LLM_REQUIRE_VALID_GUESS={env['LLM_REQUIRE_VALID_GUESS']} "
              f"RESULTS_DIR={env['RESULTS_DIR']} {' '.join(cmd)}")
        return None

    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd, env=env, cwd=str(script.parent),
            capture_output=True, text=True, timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        print(f"    ✗ TIMEOUT after {timeout_s}s")
        return None
    elapsed = time.time() - t0

    if proc.returncode != 0:
        print(f"    ✗ subprocess exited {proc.returncode} after {elapsed:.0f}s")
        print("    ── stderr tail ──")
        print("    " + "\n    ".join(proc.stderr.strip().splitlines()[-15:]))
        return None

    _temp_tag = str(temperature).rstrip("0").rstrip(".").replace(".", "p") or "0"
    out_path = results_dir / f"exp3_nguyen12_seed{seed}_temp{_temp_tag}_run{run_index}.json"
    if not out_path.exists():
        print(f"    ✗ expected output {out_path} not found (elapsed {elapsed:.0f}s)")
        return None

    with open(out_path) as f:
        result = json.load(f)
    print(f"    ✓ done in {elapsed:.0f}s -> {out_path}")
    return result


def extract_per_task(result: dict) -> dict:
    """Same shape as load_baseline()'s per-seed dict, from a fresh run's JSON."""
    per_task = {}
    for h, p in zip(result["results"]["hypatiax"], result["results"]["pysr"]):
        name = h["metadata"]["name"]
        short = "N" + name.split("-")[1]
        per_task[short] = {
            "h_r2": _safe_r2(h["evaluation"]["r2"]),
            "p_r2": _safe_r2(p["evaluation"]["r2"]),
            "h_gate_failed": h.get("llm_gate_failed"),
        }
    return per_task


# ─────────────────────────────────────────────────────────────────────────
# Reporting
# ─────────────────────────────────────────────────────────────────────────

def report_focus_task(seed: int, task: str, before: dict, after: Optional[dict]) -> str:
    b = before.get(task, {})
    b_r2 = b.get("h_r2")
    b_status = "FAIL(gate)" if not recovered(b_r2) else f"{b_r2:.4f}"

    if after is None:
        return f"  seed {seed}  {task}: baseline H={b_status}  ->  [run failed / not executed]"

    a = after.get(task, {})
    a_r2 = a.get("h_r2")
    a_status = "FAIL" if not recovered(a_r2) else f"{a_r2:.4f}"
    verdict = "FIXED ✓" if (not recovered(b_r2) and recovered(a_r2)) else (
        "still failing ✗" if not recovered(a_r2) else "already passed / still passes")
    return f"  seed {seed}  {task}: baseline H={b_status}  ->  fallback H={a_status}   [{verdict}]"


def report_regression(seed: int, task: str, before: dict, after: Optional[dict]) -> str:
    b_r2 = before.get(task, {}).get("h_r2")
    b_ok = recovered(b_r2)
    if after is None:
        return f"  seed {seed}  {task}: baseline={'PASS' if b_ok else 'FAIL'}  ->  [run failed / not executed]"
    a_r2 = after.get(task, {}).get("h_r2")
    a_ok = recovered(a_r2)
    if b_ok and not a_ok:
        verdict = "REGRESSION ✗✗✗"
    elif b_ok and a_ok:
        verdict = "OK (still passes)"
    elif not b_ok and a_ok:
        verdict = "IMPROVED"
    else:
        verdict = "OK (still fails, as before)"
    return (f"  seed {seed}  {task}: baseline H={b_r2:.4f} -> fallback H="
            f"{'FAIL' if a_r2 is None else f'{a_r2:.4f}'}   [{verdict}]")


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--script", type=Path, default=Path("exp3_nguyen12_consolidated.py"),
                     help="Path to exp3_nguyen12_consolidated.py")
    ap.add_argument("--baseline-dir", type=Path, default=Path("."),
                     help="Directory containing the existing seed42/99/123/777/2024 result JSONs")
    ap.add_argument("--results-dir", type=Path, default=Path("./gate_fallback_results"),
                     help="Fresh output directory for the fallback runs (must not reuse the "
                          "original RESULTS_DIR, or cached strict-mode failures could be "
                          "returned instead of a real re-run)")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 99, 123, 777, 2024])
    ap.add_argument("--full-regression", action="store_true",
                     help="Regression-check all 12 tasks instead of just the "
                          f"canary subset {REGRESSION_CANARY_TASKS}")
    ap.add_argument("--run-index", type=int, default=2,
                     help="Distinguishes this run's output files from run_index=1 baselines")
    ap.add_argument("--timeout", type=int, default=3600, help="Per-subprocess timeout, seconds")
    ap.add_argument("--dry-run", action="store_true",
                     help="Print the commands/env that would run, without executing anything")
    args = ap.parse_args()

    print("=" * 72)
    print("STEP 1/3 — loading baseline (strict-gate) results")
    print("=" * 72)
    baseline = load_baseline(args.baseline_dir)
    if not baseline and not args.dry_run:
        print("No baseline files found — nothing to diff against. Exiting.")
        sys.exit(1)

    regression_tasks = ALL_TASKS if args.full_regression else REGRESSION_CANARY_TASKS

    print()
    print("=" * 72)
    print(f"STEP 2/3 — focused check: does {FOCUS_TASK} recover with "
          f"LLM_REQUIRE_VALID_GUESS=0 ?")
    print("=" * 72)
    focus_results = {}
    for seed in args.seeds:
        result = run_case(
            script=args.script, seed=seed, task_ids=[FOCUS_TASK],
            results_dir=args.results_dir, run_index=args.run_index,
            require_valid_guess=False, timeout_s=args.timeout, dry_run=args.dry_run,
        )
        focus_results[seed] = extract_per_task(result) if result else None

    print()
    print("=" * 72)
    print(f"STEP 3/3 — regression check on {'ALL 12 tasks' if args.full_regression else 'canary tasks ' + str(regression_tasks)}"
          f" with LLM_REQUIRE_VALID_GUESS=0")
    print("=" * 72)
    regression_results = {}
    for seed in args.seeds:
        result = run_case(
            script=args.script, seed=seed, task_ids=regression_tasks,
            results_dir=args.results_dir, run_index=args.run_index,
            require_valid_guess=False, timeout_s=args.timeout, dry_run=args.dry_run,
        )
        regression_results[seed] = extract_per_task(result) if result else None

    # ── Summary ─────────────────────────────────────────────────────────
    print()
    print("#" * 72)
    print(f"# SUMMARY: {FOCUS_TASK} fallback outcome")
    print("#" * 72)
    for seed in args.seeds:
        print(report_focus_task(seed, FOCUS_TASK, baseline.get(seed, {}), focus_results.get(seed)))

    print()
    print("#" * 72)
    print("# SUMMARY: regression check on previously-passing tasks")
    print("#" * 72)
    any_regression = False
    for seed in args.seeds:
        for task in regression_tasks:
            line = report_regression(seed, task, baseline.get(seed, {}), regression_results.get(seed))
            print(line)
            if "REGRESSION" in line:
                any_regression = True

    print()
    if args.dry_run:
        print("(dry run — no subprocesses were actually executed)")
    elif any_regression:
        print("RESULT: ⚠ at least one regression detected — see REGRESSION ✗✗✗ lines above.")
        sys.exit(1)
    else:
        print("RESULT: ✓ no regressions detected in the checked tasks.")


if __name__ == "__main__":
    main()
