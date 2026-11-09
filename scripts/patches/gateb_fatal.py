#!/usr/bin/env python3
"""Turn the three Gate B warnings in run_all.sh into fatal errors.
Dry run by default; --apply writes. Counts must match exactly."""
import argparse, difflib, sys
from pathlib import Path

T = Path("run_all.sh")
EDITS = [
    ("lines 1016 and 1878", 2,
     "echo 'WARNING: split_protocol_disclosure.json not found \u2014 Gate B in ci_runner_disclosure.yml will FAIL'",
     "echo 'ERROR: split_protocol_disclosure.json not found' >&2; exit 1"),
    ("line 1252", 1,
     "echo 'WARNING: split_protocol_disclosure.json not found in 15_pca/ \u2014 Gate B will FAIL'",
     "echo 'ERROR: split_protocol_disclosure.json not found in 15_pca/' >&2; exit 1"),
]

ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true")
args = ap.parse_args()
src = T.read_text(encoding="utf-8"); new = src; bad = False
for name, want, old, repl in EDITS:
    n = new.count(old)
    print(f"[{'ok' if n == want else 'FAIL'}] {name}: {n} match(es), expected {want}")
    if n != want: bad = True; continue
    new = new.replace(old, repl)
if bad:
    print("Refusing to write."); sys.exit(2)
sys.stdout.writelines(difflib.unified_diff(src.splitlines(True), new.splitlines(True), "a/run_all.sh", "b/run_all.sh"))
if args.apply:
    T.write_text(new, encoding="utf-8"); print("applied")
else:
    print("dry run; pass --apply to write")
