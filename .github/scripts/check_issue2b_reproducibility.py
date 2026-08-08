#!/usr/bin/env python3
"""
check_issue2b_reproducibility.py
=================================
Closes (or re-opens) Item 2b: does the FIX-ISSUE2-UNSEEDED-NN patch
actually make HSL/M4 ("HybridSystemLLMNN all-domains (core)") and
EHD/M3 ("EnhancedHybridSystemDeFi (core)") deterministic across
repeated, otherwise-identical noiseless runs?

This does NOT run the benchmark itself — it can't, PySR/Julia aren't
available wherever this was written. It consumes the JSON output of
runs YOU perform on a machine that has the real stack (same one you
used for hds_gap_investigation.py), and tells you whether it's safe to
regenerate Table 4 / the noise-sweep tables from that output.

--------------------------------------------------------------------
STEP 1 — preflight: confirm you're actually running the patched file
--------------------------------------------------------------------
    python3 check_issue2b_reproducibility.py --check-patch \
        /path/to/run_comparative_suite_benchmark_v2.py

    Expect: "0 live hash() calls" and "7 hashlib.sha256(...) call sites".
    If this doesn't match, you're not running the patched harness —
    stop here and sort that out first, the runs below will be wasted.

--------------------------------------------------------------------
STEP 2 — run the SAME command 3 times, into 3 separate directories
--------------------------------------------------------------------
    mkdir -p run1 run2 run3

    python run_protocol_benchmark_core.py --noiseless --threshold 0.9999 \
        --nn-seeds 3 --samples 200 --method-timeout 900 --pysr-timeout 1100 \
        --output-dir run1
    # repeat unchanged into run2, then run3

    If your harness doesn't support --output-dir, just `mv` each batch
    of timestamped protocol_core_noiseless_*.json files into run1/,
    run2/, run3/ between invocations — same idea, just manual.

    Use 3 runs minimum (2 only tells you "differs or doesn't", not
    whether a match was a fluke). More is better if you have the time.

--------------------------------------------------------------------
STEP 3 — compare
--------------------------------------------------------------------
    python3 check_issue2b_reproducibility.py run1 run2 run3

Exit code 0 + "CLOSED" means every HSL/M4 and EHD/M3 result was
bit-identical across all 3 runs — safe to regenerate Table 4 and the
noise-sweep tables from any one of them (or with --emit-table4 to get
a starting LaTeX snippet from this script directly).

Exit code 1 + "STILL OPEN" means at least one equation still varies —
the seeding fix in the follow-up patch doesn't cover every source of
non-determinism (e.g. GPU nondeterminism, an unpinned dataloader
shuffle, an LLM API call with temperature > 0 feeding into y_pred_llm
upstream of the seeded NN step) and needs another pass before the
paper tables are touched.
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import defaultdict

METHODS_UNDER_TEST = [
    "HybridSystemLLMNN all-domains (core)",   # HSL / M4
    "EnhancedHybridSystemDeFi (core)",         # EHD / M3
]

METHOD_CODE = {
    "PureLLM Baseline (core)": "M1",
    "ImprovedNN (core)": "M2",
    "EnhancedHybridSystemDeFi (core)": "M3",
    "HybridSystemLLMNN all-domains (core)": "M4",
    "SymbolicEngineWithLLM (tools)": "M5",
    "HybridDiscoverySystem v50_2 (tools)": "M6",
}

THRESHOLD = 0.9999


# ──────────────────────────────────────────────────────────────────
# Preflight: is the file actually patched?
# ──────────────────────────────────────────────────────────────────
def check_patch(path):
    src = open(path, encoding="utf-8").read()
    lines = src.splitlines()

    live_hash_calls = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        # crude but effective: a call to the builtin hash( not preceded
        # by a dot (method call like foo.hash() or hashlib.sha256 etc.)
        for m in re.finditer(r"(?<![\w.])hash\(", line):
            # allow it if it's inside a comment tail after code (already
            # filtered whole-line comments above; good enough for a
            # preflight check, not a security tool)
            live_hash_calls.append((i, line.strip()))

    sha_sites = [i for i, l in enumerate(lines, 1) if "hashlib.sha256(" in l]
    has_procbox = "_ProcBox" in src
    has_ctypes_import = bool(re.search(r"^\s*import ctypes\b", src, re.M))

    print(f"Patch check on: {path}")
    print(f"  Live hash() calls (non-comment):  {len(live_hash_calls)}"
          f"{'  <-- PATCH NOT FULLY APPLIED' if live_hash_calls else '  OK'}")
    for i, l in live_hash_calls[:10]:
        print(f"    line {i}: {l}")
    print(f"  hashlib.sha256(...) call sites:   {len(sha_sites)}"
          f"{' OK (matches 7-site patch)' if len(sha_sites) == 7 else '  <-- expected 7, check patch_report_unseeded_nn_followup.md'}")
    print(f"  _ProcBox present (Item 10b):      {'OK' if has_procbox else 'MISSING'}")
    print(f"  dead ctypes import (Item 10b/Bug2): "
          f"{'STILL PRESENT <-- not cleaned up' if has_ctypes_import else 'absent, OK'}")

    ok = (not live_hash_calls) and len(sha_sites) == 7 and has_procbox and not has_ctypes_import
    print(f"\n{'PATCH LOOKS CORRECT — safe to run.' if ok else 'PATCH INCOMPLETE — fix before running the suite.'}")
    return 0 if ok else 1


# ──────────────────────────────────────────────────────────────────
# Load one run (a directory of protocol_core_noiseless_*.json, or a
# glob pattern) into {(domain, description): {method: result}}.
# ──────────────────────────────────────────────────────────────────
def load_run(run_arg):
    tests = {}
    if os.path.isdir(run_arg):
        files = sorted(glob.glob(os.path.join(run_arg, "protocol_core_noiseless_*.json")))
    else:
        files = sorted(glob.glob(run_arg))
    if not files:
        print(f"WARNING: no files found for run '{run_arg}'", file=sys.stderr)
    for f in files:
        d = json.load(open(f))
        for t in d.get("tests", []):
            key = (t["domain"], t["description"])
            tests[key] = t["results"]
    return tests, files


def fmt_key(key, width=48):
    dom, desc = key
    s = f"{dom}: {desc}"
    return s if len(s) <= width else s[: width - 1] + "…"


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--check-patch", metavar="PATH",
                     help="Static check of the harness .py file, no run comparison.")
    ap.add_argument("--emit-table4", action="store_true",
                     help="If runs are deterministic, print a Table 4-style LaTeX snippet from run[0].")
    ap.add_argument("--tol", type=float, default=0.0,
                     help="Allowed |r2_a - r2_b| before flagging as a mismatch (default 0.0 = exact).")
    ap.add_argument("runs", nargs="*", help="Run directories (or glob patterns), 2 or more.")
    args, _ = ap.parse_known_args()

    if args.check_patch:
        sys.exit(check_patch(args.check_patch))

    if len(args.runs) < 2:
        print(__doc__)
        sys.exit(1)

    run_dirs = args.runs
    loaded = [load_run(r) for r in run_dirs]
    runs = [t for t, _ in loaded]
    n_runs = len(runs)
    for r_dir, (_, files) in zip(run_dirs, loaded):
        print(f"Run '{r_dir}': {len(files)} file(s) loaded")

    all_keys = sorted(set().union(*[set(r.keys()) for r in runs]))
    print(f"\n{len(all_keys)} distinct equations across {n_runs} runs.\n")

    any_open = False
    for method in METHODS_UNDER_TEST:
        code = METHOD_CODE.get(method, "?")
        n_pass_per_run = [0] * n_runs
        mismatches = []
        missing = []

        for key in all_keys:
            r2s = []
            for i, run in enumerate(runs):
                res = run.get(key, {}).get(method)
                if res is None:
                    missing.append((key, i))
                    r2s.append(None)
                    continue
                r2 = res.get("r2")
                r2s.append(r2)
                if r2 is not None and r2 >= THRESHOLD:
                    n_pass_per_run[i] += 1
            valid = [v for v in r2s if v is not None]
            if len(valid) == n_runs:
                spread = max(valid) - min(valid)
                if spread > args.tol:
                    mismatches.append((key, r2s, spread))

        print(f"=== {method} ({code}) ===")
        print(f"  Pass rate per run (@R2>={THRESHOLD}): "
              + ", ".join(f"{n}/{len(all_keys)}" for n in n_pass_per_run))
        if mismatches:
            any_open = True
            print(f"  NON-DETERMINISTIC on {len(mismatches)} equation(s):")
            for key, r2s, spread in sorted(mismatches, key=lambda x: -x[2]):
                r2_str = ", ".join(f"{v:.6f}" if v is not None else "None" for v in r2s)
                print(f"    spread={spread:.2e}  {fmt_key(key)}  r2=[{r2_str}]")
        else:
            print(f"  DETERMINISTIC: identical R² across all {n_runs} runs, every matched equation.")
        if missing:
            any_open = True
            print(f"  WARNING: {len(missing)} (equation, run) pairs missing this method's "
                  f"result entirely — check harness errors for those runs.")
        print()

    print("=" * 72)
    if not any_open:
        print(f"RESULT: Item 2b CLOSED — {', '.join(METHODS_UNDER_TEST)} "
              f"deterministic across {n_runs} independent runs.")
        print("Safe to regenerate Table 4 / tab:r2_noise / tab:rr_noise from any one of these runs.")
        if args.emit_table4:
            print("\n--- Table 4-style summary (from first run listed) ---")
            base_run = runs[0]
            for method, code in METHOD_CODE.items():
                n = sum(
                    1 for key in all_keys
                    if (base_run.get(key, {}).get(method) or {}).get("r2", -1) >= THRESHOLD
                )
                pct = 100.0 * n / len(all_keys) if all_keys else 0.0
                print(f"{code} & {method} & {n}/{len(all_keys)} & {pct:.1f}\\% \\\\")
        sys.exit(0)
    else:
        print("RESULT: Item 2b STILL OPEN — at least one equation still varies across runs, "
              "or a method's result is missing in at least one run.")
        print("Do NOT regenerate paper tables from this data yet. Investigate the "
              "flagged equation(s)/method(s) above before re-running.")
        sys.exit(1)


if __name__ == "__main__":
    main()
