#!/usr/bin/env python3
"""Per-arm census of r2 / extrap_r2_far values in result JSONs.
Counts: finite, None, nan, +-inf, exactly 0.0 (failure-as-score signature), < -100.
Use it to report failures per arm (Table 14) and to find rows that predate PHASE1-FIX.

Usage: python3 05_null_census.py 'GLOB' [...] [--fields r2,extrap_r2_far]
Exit 0 always (reporting tool); exit 2 if no input."""
import collections, glob, json, math, sys

args = sys.argv[1:]
fields = ("r2", "extrap_r2_far")
if "--fields" in args:
    i = args.index("--fields")
    fields = tuple(args[i + 1].split(","))
    del args[i:i + 2]
primary = "--primary" in args
args = [a for a in args if a != "--primary"]
files = sorted({f for p in args for f in glob.glob(p, recursive=True)})
if primary:
    files = [f for f in files if not any(s in f.rsplit("/", 1)[-1] for s in ("checkpoint", "shard", "merged", "rescued"))]
if not files:
    print("no input files")
    sys.exit(2)

C = collections.defaultdict(collections.Counter)


def klass(v):
    if v is None:
        return "None"
    if isinstance(v, str):
        return "str:" + v[:8]
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return "other"
    if math.isnan(v):
        return "nan"
    if math.isinf(v):
        return "+inf" if v > 0 else "-inf"
    if v == 0.0:
        return "exact_0.0"
    return "below_-100" if v < -100 else "finite"


def walk(o, label):
    if isinstance(o, dict):
        arm = o.get("method") or o.get("arm") or label
        for f in fields:
            if f in o:
                C[(str(arm), f)][klass(o[f])] += 1
        for k, v in o.items():
            walk(v, k if isinstance(v, (dict, list)) else label)
    elif isinstance(o, list):
        for v in o:
            walk(v, label)


for f in files:
    try:
        walk(json.load(open(f)), "?")
    except Exception as e:
        print(f"unreadable {f}: {e}")

print(f"{'arm':38s} {'field':14s} counts")
for (arm, f), c in sorted(C.items()):
    tot = sum(c.values())
    flag = "  <-- 0.0 may be a failure-as-score" if c.get("exact_0.0") else ""
    print(f"{arm[:38]:38s} {f:14s} n={tot} {dict(c)}{flag}")
