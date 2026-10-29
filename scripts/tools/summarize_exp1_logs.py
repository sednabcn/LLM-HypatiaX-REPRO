#!/usr/bin/env python3
"""
summarize_exp1_logs.py -- merge the per-equation summary tables printed at the end of each
exp1_ablation shard log into ONE two-arm table (PySR-only "P" vs hybrid "H").

Run inside hypatiax/data/results/ablation/exp1_ablation :
    python3 summarize_exp1_logs.py            -> exp1_arms_merged.csv + printed summary

Row format in the logs:   Eq   P_near H_near P_med H_med P_far H_far P_time H_time     (N/A = no result)
A row with P_time == 0 and H_time == 0 is a placeholder (equation belongs to another shard) and is ignored.
H_status: ok = hybrid produced near/med/far values | FAILED = hybrid ran (H_time > 0) but every H value is N/A
"""
import csv, glob, re, sys

NUM = r"(N/A|[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)"
ROW = re.compile(r"^(?P<eq>\S.*?)\s{2,}" + r"\s+".join([NUM] * 8) + r"\s*$")
FIELDS = ["P_near", "H_near", "P_med", "H_med", "P_far", "H_far", "P_time", "H_time"]

def val(x):
    return None if x == "N/A" else float(x)

files = sorted(glob.glob("exp1_ablation_run.log*"))
if not files:
    sys.exit("no exp1_ablation_run.log* files here -- cd into exp1_ablation first")

best = {}   # eq -> (source, dict)
for fn in files:
    for ln in open(fn, errors="replace"):
        m = ROW.match(ln.rstrip())
        if not m:
            continue
        eq = m.group("eq").strip()
        vals = dict(zip(FIELDS, (val(g) for g in m.groups()[1:])))
        if (vals["P_time"] or 0) == 0 and (vals["H_time"] or 0) == 0:
            continue                      # placeholder row from another shard
        best[eq] = (fn, vals)             # later table in the same log wins (final summary)

rows = []
for eq, (fn, v) in best.items():
    h = [v["H_near"], v["H_med"], v["H_far"]]
    h_status = "ok" if all(x is not None for x in h) else ("FAILED" if (v["H_time"] or 0) > 0 and all(x is None for x in h) else "partial")
    rows.append([eq, *[("" if v[k] is None else v[k]) for k in FIELDS], h_status, fn])

with open("exp1_arms_merged.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["equation", *FIELDS, "H_status", "source"]); w.writerows(rows)

from collections import Counter
c = Counter(r[-2] for r in rows)
print(f"{len(rows)} equations with a result in some log | hybrid status: {dict(c)}")
print(f"{'equation':24} {'P_far':>10} {'H_far':>8} {'P_time':>8} {'H_time':>7}  H_status")
for r in rows:
    print(f"{r[0]:24} {str(r[5]):>10} {str(r[6]):>8} {r[7]:>8} {r[8]:>7}  {r[9]}")
