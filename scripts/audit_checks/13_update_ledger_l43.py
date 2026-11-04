import csv
p = "audit/LEDGER.csv"
rows = list(csv.reader(open(p, newline="")))
ix = {c: i for i, c in enumerate(rows[0])}
hit = 0
for r in rows[1:]:
    if r and r[0] == "L43":
        r[ix["status"]] = "fixed-committed"
        r[ix["check"]] = ("16166e4 fail-closed DISABLE flags; 2503407 pins SIGN_FLIP=0 and STRICT=1 in run_all.sh and CI; "
                          "84aef30 refuses HYPATIAX_ALLOW_LEGACY in CI; run_all.sh 59-62 aborts on SIGN_FLIP unless ALLOW_LEGACY=1; "
                          "STRICT assertion at line 55 (92c53eb)")
        hit += 1
assert hit == 1, hit
with open(p, "w", newline="") as f:
    csv.writer(f, lineterminator="\n").writerows(rows)
print("L43 updated")
