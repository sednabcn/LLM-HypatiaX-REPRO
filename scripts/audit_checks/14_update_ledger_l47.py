import csv
p = "audit/LEDGER.csv"
rows = list(csv.reader(open(p, newline="")))
ix = {c: i for i, c in enumerate(rows[0])}
UPD = {
 "L47": ("fixed-committed", "scripts removed deliberately in 78e4244 (results-only repro repo); run_all.sh now says SKIP removed, not WARN promising a producer; analyze_hybrid_performance call dropped; paper_targets.json restored 92c53eb; paper-side use of ablation_paired.json and the symbolic report must be checked in the paper repo"),
 "L49": ("fixed-committed", "no producer in this repo; message corrected in run_all.sh and ablation_paired.json removed from ci_pipeline_check.yml expected globs; results depending on it are not reproducible here"),
}
seen = set()
for r in rows[1:]:
    if r and r[0] in UPD:
        r[ix["status"]], r[ix["check"]] = UPD[r[0]]; seen.add(r[0])
assert seen == set(UPD), set(UPD) - seen
with open(p, "w", newline="") as f:
    csv.writer(f, lineterminator="\n").writerows(rows)
print("updated", sorted(seen))
