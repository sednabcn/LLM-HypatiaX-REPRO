#!/usr/bin/env python3
"""
phase2_close.py - closure gate for Option 3 / Phase 2 (matched baseline runs).

Reads per-case result records for Pure LLM and full HDS v50_2, verifies that the
Phase 2 requirements are met, computes the paired comparison, and writes:

    phase2_closure.json   machine-readable manifest (checks, summary, input hashes)
    PHASE2_CLOSED         marker file, written ONLY if every blocking check passes

Exit code 0 = Phase 2 closed, 1 = not closed (blocking failures listed), 2 = bad input.

Input format: JSONL (one object per line) or a JSON list. One record per
(system, equation, seed). Required fields:

    system            "pure_llm" or "hds_v50_2" (override names with --a-name/--b-name)
    equation          equation id
    seed              integer seed
    split_id          identifier or hash of the exact train/test split used
    r2                float, or null/NaN if no valid result
    status            "ok" | "timeout" | "error" | "nan" (free-form failure label)
    formula           formula string actually evaluated (required when status == "ok")
    generation_path   e.g. "llm", "ensemble", "pysr", "hardcoded_bypass"
    llm_called        bool
    bypass_used       bool (true if a hardcoded/ground-truth/least-squares shortcut fired)
    runtime_s         wall-clock seconds
    timeout_s         time budget applied to this case
    model_id          pinned LLM identifier
    code_version      commit hash or equivalent
    config_hash       hash of the run configuration
    evaluator_version version tag of the recovery evaluator

Usage:
    python phase2_close.py --pure-llm results/pure_llm/*.jsonl \
                           --hds results/hds_v50_2/*.jsonl \
                           --out-dir phase2_out
"""
import argparse
import glob
import hashlib
import json
import math
import os
import random
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone

REQUIRED = [
    "system", "equation", "seed", "split_id", "r2", "status", "formula",
    "generation_path", "llm_called", "bypass_used", "runtime_s", "timeout_s",
    "model_id", "code_version", "config_hash", "evaluator_version",
]
# r2 may legitimately be null/NaN, formula may be empty when status != ok.
NULLABLE = {"r2", "formula"}


# ----------------------------------------------------------------- loading
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def expand(patterns):
    files = []
    for p in patterns:
        hits = sorted(glob.glob(p))
        files.extend(hits if hits else [p])
    return files


def load_records(files):
    recs = []
    for fp in files:
        if not os.path.isfile(fp):
            raise FileNotFoundError(fp)
        with open(fp, "r", encoding="utf-8") as f:
            text = f.read().strip()
        if not text:
            continue
        if text[0] == "[":
            data = json.loads(text)
        else:
            data = [json.loads(line) for line in text.splitlines() if line.strip()]
        for d in data:
            d["_file"] = fp
        recs.extend(data)
    return recs


def as_r2(v):
    if v is None:
        return None
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) else v


# ------------------------------------------------------------------ checks
class Report:
    def __init__(self):
        self.checks = []
        self.caveats = []

    def add(self, name, passed, detail="", blocking=True):
        self.checks.append(
            {"name": name, "passed": bool(passed), "blocking": blocking, "detail": detail}
        )

    @property
    def closed(self):
        return all(c["passed"] for c in self.checks if c["blocking"])


def check_schema(name, recs, rep):
    bad = []
    for i, r in enumerate(recs):
        for k in REQUIRED:
            if k not in r or (r[k] is None and k not in NULLABLE):
                bad.append(f"{r.get('_file','?')}#{i}: missing/null '{k}'")
    rep.add(f"[{name}] schema complete", not bad,
            f"{len(bad)} problems; first: {bad[:3]}" if bad else f"{len(recs)} records OK")
    return not bad


def index(name, recs, rep):
    idx, dups = {}, []
    for r in recs:
        key = (r["equation"], int(r["seed"]))
        if key in idx:
            dups.append(key)
        idx[key] = r
    rep.add(f"[{name}] no duplicate (equation, seed) rows", not dups,
            f"{len(dups)} duplicates; first: {dups[:3]}" if dups else f"{len(idx)} unique cases")
    return idx


def single_valued(name, recs, field, rep, blocking=True):
    vals = sorted({str(r[field]) for r in recs})
    rep.add(f"[{name}] single {field}", len(vals) == 1, f"values: {vals[:5]}", blocking)
    return vals


def run_checks(a_name, b_name, a_recs, b_recs, args, rep):
    ok_a = check_schema(a_name, a_recs, rep)
    ok_b = check_schema(b_name, b_recs, rep)
    if not (ok_a and ok_b):
        return None, None
    a_idx = index(a_name, a_recs, rep)
    b_idx = index(b_name, b_recs, rep)

    # 1. Matched design: identical case sets and splits.
    only_a = sorted(set(a_idx) - set(b_idx))
    only_b = sorted(set(b_idx) - set(a_idx))
    rep.add("matched equations x seeds", not only_a and not only_b,
            f"only in {a_name}: {len(only_a)} {only_a[:3]}; only in {b_name}: {len(only_b)} {only_b[:3]}")
    common = sorted(set(a_idx) & set(b_idx))
    split_mismatch = [k for k in common if a_idx[k]["split_id"] != b_idx[k]["split_id"]]
    rep.add("identical split_id on every paired case", not split_mismatch,
            f"{len(split_mismatch)} mismatches; first: {split_mismatch[:3]}")
    seeds = sorted({k[1] for k in common})
    rep.add(f"at least {args.min_seeds} seeds", len(seeds) >= args.min_seeds,
            f"seeds found: {seeds}")

    # 2. Matched evaluation rules and resource limits.
    both = a_recs + b_recs
    single_valued("both", both, "evaluator_version", rep)
    # Unequal budgets are blocking unless explicitly declared with a reason; a declared
    # exception is recorded as a caveat and produces a DIFFERENT marker file.
    single_valued("both", both, "timeout_s", rep, blocking=not args.declare_unequal_timeout)
    if args.declare_unequal_timeout:
        per_sys = {nm: sorted({float(r["timeout_s"]) for r in recs}) for nm, recs in ((a_name, a_recs), (b_name, b_recs))}
        rep.caveats.append("UNEQUAL TIME BUDGETS declared: " + json.dumps(per_sys) +
                           f" - reason: {args.declare_unequal_timeout}. Results are NOT an equal-budget comparison.")
    single_valued("both", both, "model_id", rep)
    for nm, recs in ((a_name, a_recs), (b_name, b_recs)):
        single_valued(nm, recs, "code_version", rep)
        single_valued(nm, recs, "config_hash", rep)

    # 3. Auditable generation paths and no uncontrolled bypass.
    if args.allow_bypass:
        rep.add("bypass rows declared (allowed by --allow-bypass)", True,
                "bypass is treated as part of the evaluated method; report it", blocking=False)
    else:
        for nm, recs in ((a_name, a_recs), (b_name, b_recs)):
            byp = [(r["equation"], r["seed"]) for r in recs
                   if r["bypass_used"] or "bypass" in str(r["generation_path"]).lower()]
            rep.add(f"[{nm}] no hardcoded/ground-truth bypass rows", not byp,
                    f"{len(byp)} bypass rows; first: {byp[:3]}")
    for nm, recs in ((a_name, a_recs), (b_name, b_recs)):
        nof = [(r["equation"], r["seed"]) for r in recs
               if r["status"] == "ok" and not str(r.get("formula") or "").strip()]
        rep.add(f"[{nm}] formula stored for every ok row", not nof,
                f"{len(nof)} ok rows without formula; first: {nof[:3]}")
        nol = [(r["equation"], r["seed"]) for r in recs
               if not isinstance(r["llm_called"], bool)]
        rep.add(f"[{nm}] llm_called is a boolean on every row", not nol, f"{len(nol)} bad rows")

    # 4. Budget honoured: no row exceeds timeout_s unless labelled a timeout.
    for nm, recs in ((a_name, a_recs), (b_name, b_recs)):
        over = [(r["equation"], r["seed"], r["runtime_s"]) for r in recs
                if float(r["runtime_s"]) > float(r["timeout_s"]) * 1.05 and r["status"] != "timeout"]
        rep.add(f"[{nm}] runtime within timeout_s (or labelled timeout)", not over,
                f"{len(over)} rows over budget; first: {over[:3]}")
    return a_idx, b_idx


# ------------------------------------------------------------- statistics
def rate(flags):
    return sum(flags) / len(flags) if flags else float("nan")


def exact_sign_p(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def paired_summary(a_idx, b_idx, args):
    """Compare per-equation (seed-averaged) outcomes; the equation is the unit of analysis."""
    eqs = sorted({k[0] for k in a_idx})
    seeds = sorted({k[1] for k in a_idx})

    def per_eq(idx, pred):
        return {e: statistics.mean(1.0 if pred(idx[(e, s)]) else 0.0
                                   for s in seeds if (e, s) in idx) for e in eqs}

    def rec(th):
        return lambda r: (as_r2(r["r2"]) is not None and r["status"] == "ok" and as_r2(r["r2"]) >= th)

    def cat(r):
        v = as_r2(r["r2"])
        return v is not None and v < args.catastrophic_r2

    def nan(r):
        return as_r2(r["r2"]) is None

    metrics = {
        f"recovery_r2>={args.threshold}": rec(args.threshold),
        f"recovery_r2>={args.strict_threshold}": rec(args.strict_threshold),
        f"catastrophic_r2<{args.catastrophic_r2}": cat,
        "nan_or_missing_r2": nan,
    }
    rng = random.Random(args.bootstrap_seed)
    out = {}
    for name, pred in metrics.items():
        pa, pb = per_eq(a_idx, pred), per_eq(b_idx, pred)
        diffs = [pb[e] - pa[e] for e in eqs]
        boots = []
        for _ in range(args.bootstrap_iters):
            sample = [diffs[rng.randrange(len(diffs))] for _ in diffs]
            boots.append(sum(sample) / len(sample))
        boots.sort()
        lo = boots[int(0.025 * len(boots))]
        hi = boots[int(0.975 * len(boots)) - 1]
        b_better = sum(1 for d in diffs if d > 0)
        a_better = sum(1 for d in diffs if d < 0)
        per_seed = {}
        for s in seeds:
            fa = [pred(a_idx[(e, s)]) for e in eqs if (e, s) in a_idx]
            fb = [pred(b_idx[(e, s)]) for e in eqs if (e, s) in b_idx]
            per_seed[str(s)] = {"a": rate(fa), "b": rate(fb)}
        out[name] = {
            "a_rate": statistics.mean(pa.values()),
            "b_rate": statistics.mean(pb.values()),
            "paired_diff_b_minus_a": statistics.mean(diffs),
            "bootstrap_95ci": [lo, hi],
            "equations_b_better": b_better,
            "equations_a_better": a_better,
            "equations_tied": len(eqs) - a_better - b_better,
            "exact_sign_test_p": exact_sign_p(b_better, a_better),
            "per_seed": per_seed,
        }
    rt = [float(b_idx[k]["runtime_s"]) / float(a_idx[k]["runtime_s"])
          for k in a_idx if float(a_idx[k]["runtime_s"]) > 0]
    out["runtime_ratio_b_over_a"] = {
        "median": statistics.median(rt) if rt else None,
        "p10_p90": [sorted(rt)[int(0.1 * len(rt))], sorted(rt)[min(len(rt) - 1, int(0.9 * len(rt)))]] if rt else None,
    }
    out["n_equations"] = len(eqs)
    out["seeds"] = seeds
    return out


# --------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pure-llm", nargs="+", required=True, help="result files for baseline A")
    ap.add_argument("--hds", nargs="+", required=True, help="result files for HDS v50_2 (B)")
    ap.add_argument("--a-name", default="pure_llm")
    ap.add_argument("--b-name", default="hds_v50_2")
    ap.add_argument("--out-dir", default="phase2_out")
    ap.add_argument("--min-seeds", type=int, default=3)
    ap.add_argument("--threshold", type=float, default=0.99, help="primary recovery threshold")
    ap.add_argument("--strict-threshold", type=float, default=0.999999)
    ap.add_argument("--catastrophic-r2", type=float, default=-10.0,
                    help="pre-specified: R2 below this is catastrophic (main-paper definition is -10)")
    ap.add_argument("--declare-unequal-timeout", metavar="REASON", default=None,
                    help="make unequal timeout_s non-blocking; REASON is stored as a caveat and the marker "
                         "becomes PHASE2_CLOSED_WITH_CAVEATS. Not an equal-budget result.")
    ap.add_argument("--allow-bypass", action="store_true",
                    help="permit bypass rows (only if bypass is part of the declared method)")
    ap.add_argument("--bootstrap-iters", type=int, default=10000)
    ap.add_argument("--bootstrap-seed", type=int, default=0)
    args = ap.parse_args()

    a_files, b_files = expand(args.pure_llm), expand(args.hds)
    try:
        a_recs, b_recs = load_records(a_files), load_records(b_files)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR reading inputs: {e}", file=sys.stderr)
        return 2
    if not a_recs or not b_recs:
        print("ERROR: no records loaded", file=sys.stderr)
        return 2

    # keep only the records that belong to each system
    a_recs = [r for r in a_recs if r.get("system") == args.a_name]
    b_recs = [r for r in b_recs if r.get("system") == args.b_name]
    rep = Report()
    rep.add("records present for both systems", bool(a_recs and b_recs),
            f"{args.a_name}: {len(a_recs)}, {args.b_name}: {len(b_recs)}")
    summary = None
    if a_recs and b_recs:
        a_idx, b_idx = run_checks(args.a_name, args.b_name, a_recs, b_recs, args, rep)
        if a_idx is not None and rep.closed:
            summary = paired_summary(a_idx, b_idx, args)

    os.makedirs(args.out_dir, exist_ok=True)
    manifest = {
        "phase": "Option 3 / Phase 2 - matched baseline runs",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "closed": rep.closed,
        "settings": {k: v for k, v in vars(args).items() if k not in ("pure_llm", "hds")},
        "inputs": {f: sha256(f) for f in a_files + b_files if os.path.isfile(f)},
        "checks": rep.checks,
        "caveats": rep.caveats,
        "paired_summary": summary,
        "note": ("Phase 2 reports measured differences only; it does not assume the hybrid is better. "
                 "Per-equation seed-averaged outcomes are the unit of the paired comparison."),
    }
    man_path = os.path.join(args.out_dir, "phase2_closure.json")
    with open(man_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)

    marker = os.path.join(args.out_dir, "PHASE2_CLOSED_WITH_CAVEATS" if rep.caveats else "PHASE2_CLOSED")
    for m in ("PHASE2_CLOSED", "PHASE2_CLOSED_WITH_CAVEATS"):
        mp = os.path.join(args.out_dir, m)
        if os.path.exists(mp):
            os.remove(mp)

    print(f"{'PASS' if rep.closed else 'FAIL'}  checks ({sum(c['passed'] for c in rep.checks)}/{len(rep.checks)} passed)")
    for c in rep.checks:
        if not c["passed"]:
            print(f"  FAIL{' (blocking)' if c['blocking'] else ''}: {c['name']} - {c['detail']}")
    if rep.closed and summary:
        print(f"\nPaired comparison ({args.b_name} minus {args.a_name}), n={summary['n_equations']} equations, seeds={summary['seeds']}")
        for k, v in summary.items():
            if isinstance(v, dict) and "paired_diff_b_minus_a" in v:
                print(f"  {k}: {v['a_rate']:.3f} -> {v['b_rate']:.3f}  diff {v['paired_diff_b_minus_a']:+.3f} "
                      f"CI [{v['bootstrap_95ci'][0]:+.3f}, {v['bootstrap_95ci'][1]:+.3f}]  "
                      f"B better/A better/tied {v['equations_b_better']}/{v['equations_a_better']}/{v['equations_tied']}  "
                      f"sign p={v['exact_sign_test_p']:.3f}")
        rr = summary["runtime_ratio_b_over_a"]
        if rr["median"] is not None:
            print(f"  runtime ratio (B/A) median {rr['median']:.2f}")
        with open(marker, "w") as f:
            f.write(f"Phase 2 closed {manifest['generated_utc']}\nmanifest: {man_path}\n")
        for c in rep.caveats:
            print(f"\n  CAVEAT: {c}")
        print(f"\nPhase 2 CLOSED{' WITH CAVEATS' if rep.caveats else ''} -> {marker}")
    else:
        print("\nPhase 2 NOT closed. Fix the failing blocking checks and rerun.")
    print(f"Manifest: {man_path}")
    return 0 if rep.closed else 1


if __name__ == "__main__":
    sys.exit(main())
