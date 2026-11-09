import csv, sys
p = "audit/LEDGER.csv"
rows = list(csv.reader(open(p, newline="")))
hdr = rows[0]
ix = {c: i for i, c in enumerate(hdr)}
hit = 0
for r in rows[1:]:
    if r and r[0] == "L34":
        r[ix["status"]] = "fixed-committed"
        r[ix["check"]] = ("894f66e: force_llm early return reported NN r2 0.0 with reason nonfinite_metric "
                          "although the NN is skipped; now r2 None and reason skipped_force_llm; "
                          "d49bd60 adds r2_in_sample there; test scripts/audit_checks/test_force_llm_branch.py PASS; "
                          "non-finite NN branch (nn_r2 None to -inf) in 92c53eb")
        hit += 1
assert hit == 1, f"expected 1 L34 row, found {hit}"
with open(p, "w", newline="") as f:
    csv.writer(f, lineterminator="\n").writerows(rows)
print("L34 updated")
