#!/usr/bin/env python3
"""EXPLORATORY: recompute recovery per method with bypassed equations excluded.

Usage (old repo root; pass UNIQUE files, e.g. one directory, to avoid double counting):
    python reanalyze_excluding_bypass.py hypatiax/data/results/comparison_results/feynman-tests/exp2

An equation is "bypassed" when the PureLLM baseline's metadata.is_hardcoded is true
(the hybrids inherit that path on those rows, so the whole row is dropped for every
method). Uses the STORED r2 values, which came from the old evaluators, so numbers
are exploratory only. Missing / non-finite r2 counts as not recovered.
"""
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

PURE = "PureLLM"


def num(x):
    return float(x) if isinstance(x, (int, float)) and math.isfinite(x) else float("-inf")


def bypassed(res):
    k = next((k for k in res if PURE in k), None)
    return bool(k and (res[k].get("metadata") or {}).get("is_hardcoded") is True)


def rate(vals, th):
    return 100.0 * sum(v >= th for v in vals) / len(vals) if vals else float("nan")


def main(args):
    files = []
    for a in args:
        p = Path(a)
        files += sorted(p.rglob("protocol_core_*.json")) if p.is_dir() else [p]

    acc = defaultdict(lambda: {"all": [], "clean": []})
    n_tests = n_byp = n_files = 0
    for f in files:
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        if not isinstance(d, dict) or not isinstance(d.get("tests"), list):
            continue
        n_files += 1
        for t in d["tests"]:
            res = t.get("results", {})
            byp = bypassed(res)
            n_tests += 1
            n_byp += byp
            for m, r in res.items():
                v = num(r.get("r2"))
                acc[m]["all"].append(v)
                if not byp:
                    acc[m]["clean"].append(v)

    print(f"{n_files} files, {n_tests} test rows, {n_byp} bypassed "
          f"({100 * n_byp / max(n_tests, 1):.0f}%) -> {n_tests - n_byp} clean\n")
    hdr = f"{'method':42s} {'n_all':>5} {'>=.99':>6} {'>=.999999':>9} {'med':>7} | " \
          f"{'n_clean':>7} {'>=.99':>6} {'>=.999999':>9} {'med':>7}"
    print(hdr)
    print("-" * len(hdr))
    for m, s in sorted(acc.items()):
        a, c = s["all"], s["clean"]
        med = lambda v: statistics.median(v) if v else float("nan")
        print(f"{m[:42]:42s} {len(a):5d} {rate(a, .99):5.1f}% {rate(a, .999999):8.1f}% {med(a):7.3f} | "
              f"{len(c):7d} {rate(c, .99):5.1f}% {rate(c, .999999):8.1f}% {med(c):7.3f}")
    print("\nStored r2 from old evaluators: exploratory, not confirmatory.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
