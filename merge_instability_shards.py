#!/usr/bin/env python3
"""
merge_instability_shards.py -- rebuild one instability table from the tracked CSV plus the
__shardN_rescued_*.csv files, where each shard filled only ITS equations and left the rest as
placeholder rows (0.0, 0.0, 0.0).

Run inside hypatiax/data/results/ablation/exp1_ablation :
    python3 merge_instability_shards.py            -> instability_extrapolation_v2_merged.csv
Columns: equation, domain, extrap_r2_near, extrap_r2_far, instability_index, status, source
status: ok | nonfinite (nan/inf in the source; value left empty) | conflict (>1 non-placeholder
        source disagrees) | not_run (placeholder in every file: no shard measured it)
Exit code 1 if any equation is conflict or not_run.
"""
import csv, glob, math, sys
from pathlib import Path

BASE = "instability_extrapolation_v2.csv"
files = [BASE] + sorted(glob.glob(BASE + "__shard*_rescued_*.csv"))
files = [f for f in files if Path(f).exists()]
if not files:
    sys.exit("no instability csv files here -- cd into exp1_ablation first")

def f(x):
    try: return float(x)
    except (TypeError, ValueError): return float("nan")

PLACEHOLDER = (0.0, 0.0, 0.0)
by_eq = {}   # equation -> {"domain":..., "cands":[(file, vals)]}
for fn in files:
    for r in csv.DictReader(open(fn)):
        vals = (f(r["extrap_r2_near"]), f(r["extrap_r2_far"]), f(r["instability_index"]))
        e = by_eq.setdefault(r["equation"], {"domain": r["domain"], "cands": [], "files": 0})
        e["files"] += 1
        if vals != PLACEHOLDER:        # nan != 0.0, so nan/inf rows count as real measurements
            e["cands"].append((fn, vals))

rows, bad = [], 0
for eq, e in by_eq.items():
    if not e["cands"]:
        status, src, vals = "not_run", "", ("", "", ""); bad += 1
    else:
        src, vals = e["cands"][0]
        agree = all(all((a == b) or (math.isnan(a) and math.isnan(b)) for a, b in zip(v, vals)) for _, v in e["cands"])
        status = "ok" if agree else "conflict"
        if not agree: bad += 1
        if any(not math.isfinite(x) for x in vals):
            status = "nonfinite" if status == "ok" else status
            vals = tuple("" if not math.isfinite(x) else x for x in vals)
        src = "; ".join(c[0] for c in e["cands"])
    rows.append([eq, e["domain"], *vals, status, src])

out = "instability_extrapolation_v2_merged.csv"
with open(out, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["equation", "domain", "extrap_r2_near", "extrap_r2_far", "instability_index", "status", "source"])
    w.writerows(rows)

from collections import Counter
c = Counter(r[5] for r in rows)
print(f"merged {len(files)} files -> {out}: {len(rows)} equations | {dict(c)}")
for r in rows:
    if r[5] != "ok":
        print(f"  {r[5]:10} {r[0]}")
sys.exit(1 if bad else 0)
