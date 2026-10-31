import csv, io, subprocess
p = "audit/LEDGER.csv"
rows = list(csv.reader(open(p, newline="")))
ix = {c: i for i, c in enumerate(rows[0])}
old = subprocess.check_output(["git", "show", "33822e6^:audit/LEDGER.csv"], text=True)
old_l68 = next(r for r in csv.reader(io.StringIO(old)) if r and r[0] == "L68")

UPD = {
 "L32": ("fixed-committed", "92c53eb: llm_r2 and llm_ok None-safe via _llm_scored (hybrid_system_llm_nn_all_domains.py 876-880); failure sentinel -inf; no unit test for the None path yet"),
 "L33": ("fixed-committed", "92c53eb: nn_r2 None becomes -inf and a non-finite NN has its own branch (lines 941-947 on); no unit test for the nan path yet"),
 "L51": ("fixed-committed", "duplicate of L65; assertion at run_all.sh:55 added in 92c53eb"),
 "L65": ("fixed-committed", "assertion at run_all.sh:55 committed in 92c53eb"),
 "L68": ("fixed-committed", "33822e6: _is_poor flags None; NaN; unparsable and any R2 < 0.80; -inf flagged and +inf passes; 8-case unit check passes; reporting block only (hard gates are S06/S08)"),
}
seen = set()
for r in rows[1:]:
    if r and r[0] in UPD:
        status, check = UPD[r[0]]
        if r[0] == "L68":                      # restore the original descriptive fields
            for c in ("source", "item", "step_or_area", "code", "stage"):
                r[ix[c]] = old_l68[ix[c]]
        r[ix["status"]], r[ix["check"]] = status, check
        seen.add(r[0])
assert seen == set(UPD), f"missing rows: {set(UPD) - seen}"
with open(p, "w", newline="") as f:
    csv.writer(f, lineterminator="\n").writerows(rows)
print("updated", sorted(seen))
