#!/usr/bin/env python3
"""Copy pure_llm rows, setting r2 / r2_raw from another field (medium or train sensitivity)."""
import argparse, json, sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--src", default="p2")          # or p2_call1 for the call-1 set
ap.add_argument("--field", required=True)       # extrap_r2_medium | train_r2
ap.add_argument("--out", required=True)         # p2_med | p2_train
a = ap.parse_args()

out = Path(a.out); out.mkdir(exist_ok=True)
n = 0
for f in sorted(Path(a.src).glob("pure_llm_*.jsonl")):
    rows = []
    for ln in f.read_text().splitlines():
        if not ln.strip():
            continue
        r = json.loads(ln)
        if a.field not in r:
            sys.exit(f"field {a.field} missing in {f.name}")
        r["r2"] = r["r2_raw"] = r[a.field]
        r["r2_field_used"] = a.field
        rows.append(r)
    (out / f.name).write_text("".join(json.dumps(r) + "\n" for r in rows))
    n += len(rows)
print(f"wrote {n} rows to {out}/ with r2 = {a.field}")
