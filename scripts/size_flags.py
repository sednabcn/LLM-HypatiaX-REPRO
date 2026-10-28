#!/usr/bin/env python3
"""size_flags.py - how much do the published DeFi benchmark statistics move if the cases the test
harness marks extrapolation_intractable are excluded?  Read-only: never writes to a results file.

    python scripts/size_flags.py [RESULTS.json ...]

Default file: the v3c2 noise-noiseless run.  Handles both layouts seen in the repo:
  v3c2: {"cases": [ {"test_case": NAME, "results": {method: {"test_r2": ..}}}, ... ]}
  pca : {"0": {"equation_id": NAME, "results": {...}}, ...}   (or a list of such dicts)
Statistics reproduce _generate_report: clip to [CLIP_LO, 1], NaN dropped, fixed denominator.
"""
import json
import math
import re
import sys

import numpy as np

DEFAULT = "hypatiax/data/results/comparison_results/noise-noiseless/15/hypatiax_defi_benchmark_v3c2_results.json"
SRC = "hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py"
# Names flagged extrapolation_intractable in hypatiax/experiments/tests/test_enhanced_defi_extrapolation.py
FLAGGED = ["AMM arbitrage profit", "Impermanent loss breakeven", "Optimal LP Position (Kelly)",
           "Options Delta", "Black-Scholes Call Price", "Put option intrinsic"]
METHODS = ("pure_llm", "neural_network", "hybrid")

norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
WANT = {norm(n): n for n in FLAGGED}


def clip_lo():
    try:
        m = re.search(r"^\s*CLIP_LO\s*=\s*(-?[0-9.eE+-]+)", open(SRC).read(), re.M)
        if m:
            return float(m.group(1))
    except OSError:
        pass
    return -10.0


def load_cases(fn):
    d = json.load(open(fn))
    if isinstance(d, dict) and isinstance(d.get("cases"), list):
        items = d["cases"]
    elif isinstance(d, dict):
        items = [v for v in d.values() if isinstance(v, dict) and "results" in v]
    else:
        items = [v for v in d if isinstance(v, dict)]
    out = []
    for c in items:
        name = c.get("test_case") or c.get("equation_id") or c.get("name") or "?"
        out.append((str(name), c))
    return out


def value(c, method):
    r = (c.get("results") or {}).get(method) or {}
    v = r.get("test_r2")
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None, r
    return float(v), r


def stats(vals, denom, lo):
    raw = np.array(vals, float)
    if raw.size == 0:
        return "n=0"
    a = np.clip(raw, lo, 1.0)
    return (f"n={raw.size:3d} median={np.median(a):8.4f} mean_clip={np.mean(a):8.4f} "
            f"pct>0.9={100 * int((raw > 0.9).sum()) / denom:6.2f} pct>0.99={100 * int((raw > 0.99).sum()) / denom:6.2f}")


def run(fn, lo):
    cases = load_cases(fn)
    hit = [n for n, _ in cases if norm(n) in WANT]
    miss = sorted(WANT[k] for k in WANT if k not in {norm(n) for n in hit})
    print(f"\n=== {fn.split('/')[-1]}  ({len(cases)} cases, CLIP_LO={lo})")
    print("flagged cases found:", hit or "none")
    if miss:
        print("flagged names NOT found in this file:", miss)
    for n, c in cases:
        if norm(n) in WANT:
            row = []
            for m in METHODS:
                v, r = value(c, m)
                row.append(f"{m}={'nan' if v is None else round(v, 4)}{'' if r.get('success', True) else '(failed)'}")
            print(f"  {n}: " + "  ".join(row))
    for m in METHODS:
        for label, drop in (("as published (all cases)", False), ("flagged cases excluded", True)):
            vals, denom = [], 0
            for n, c in cases:
                if drop and norm(n) in WANT:
                    continue
                denom += 1
                v, _ = value(c, m)
                if v is not None:
                    vals.append(v)
            print(f"{m:15} {label:26} {stats(vals, max(denom, 1), lo)}")
    zeros = [(n, m) for n, c in cases for m in METHODS
             if value(c, m)[0] == 0.0 and norm(n) not in WANT]
    print("exact-zero test_r2 outside the flagged set:", zeros or "none")


if __name__ == "__main__":
    lo = clip_lo()
    for fn in (sys.argv[1:] or [DEFAULT]):
        run(fn, lo)
