#!/usr/bin/env python3
"""exp1b_pca Gate B exit honours SKIP_ALLOWED, like the _COUNT warning above it.
Dry run by default; --apply writes. The edit must match exactly once."""
import argparse, difflib, sys
from pathlib import Path

T = Path("run_all.sh")
OLD = r'''  if [[ \"\${_NDISC}\" -eq 0 ]]; then
    echo 'ERROR: split_protocol_disclosure.json not found in 15_pca/' >&2; exit 1'''
NEW = r'''  if [[ \"\${_NDISC}\" -eq 0 && \"\${SKIP_ALLOWED:-false}\" != 'true' ]]; then
    echo 'ERROR: split_protocol_disclosure.json not found in 15_pca/' >&2; exit 1'''

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
args = ap.parse_args()

src = T.read_text(encoding="utf-8")
n = src.count(OLD)
print(f"[{'ok' if n == 1 else 'FAIL'}] exp1b_pca Gate B: {n} match(es), expected 1")
if n != 1:
    sys.exit(2)
new = src.replace(OLD, NEW)
sys.stdout.writelines(difflib.unified_diff(
    src.splitlines(True), new.splitlines(True), "a/run_all.sh", "b/run_all.sh"))
if args.apply:
    T.write_text(new, encoding="utf-8")
    print("applied")
else:
    print("dry run; pass --apply to write")
