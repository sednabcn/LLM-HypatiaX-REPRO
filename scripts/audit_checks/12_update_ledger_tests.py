import csv
p = "audit/LEDGER.csv"
rows = list(csv.reader(open(p, newline="")))
ix = {c: i for i, c in enumerate(rows[0])}
UPD = {
 "L32": "92c53eb: llm_r2 and llm_ok None-safe via _llm_scored (hybrid_system_llm_nn_all_domains.py 876-880); failure sentinel -inf; 19916f9 test_nonfinite_paths.py PASS (LLM failed with NN finite None or nan); not covered: LLM success True with r2 None",
 "L33": "92c53eb: nn_r2 None becomes -inf and a non-finite NN has its own branch (lines 941-947 on); 19916f9 test_nonfinite_paths.py PASS (NN None and nan with LLM good gives llm; both failed gives fail with r2 -inf or nan)",
}
seen = set()
for r in rows[1:]:
    if r and r[0] in UPD:
        r[ix["check"]] = UPD[r[0]]; seen.add(r[0])
assert seen == set(UPD), set(UPD) - seen
with open(p, "w", newline="") as f:
    csv.writer(f, lineterminator="\n").writerows(rows)
print("updated", sorted(seen))
