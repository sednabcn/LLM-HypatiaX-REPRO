#!/usr/bin/env python3
"""
phase3_patch_omit.py - rewrite the OMIT reasons in scripts/phase3_all.py (issue I6).

Uses ast to locate the module-level `OMIT = {...}` assignment, replaces just that
statement, and keeps a .bak copy. No run is started.

    python phase3_patch_omit.py            # patches scripts/phase3_all.py
    python phase3_patch_omit.py --dry-run  # prints the new block only

Then: git diff scripts/phase3_all.py ; git add scripts/ ; git commit
"""
import argparse
import ast
import shutil
import sys
from pathlib import Path

TARGET = Path("scripts/phase3_all.py")

REASON = ("not part of the v50_2 / Core-15 path; this gate lives in the v3c DeFi pipeline "
          "(hypatiax_defi_benchmark_v3c.py), so it is untested here, not shown to have no effect")

NEW = {
    "probe": REASON,
    "complexity_routing": REASON,
    "nn_augmentation": REASON,
    "blend_weight": REASON,
}


def render(new):
    lines = ["OMIT = {"]
    for k, v in new.items():
        lines.append(f"    {k!r}: {v!r},")
    lines.append("}")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--file", default=str(TARGET))
    a = ap.parse_args()
    path = Path(a.file)
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    node = None
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "OMIT" for t in n.targets):
            node = n
            break
    if node is None:
        print("OMIT assignment not found at module level; nothing changed.", file=sys.stderr)
        return 1
    try:
        old = ast.literal_eval(node.value)
    except Exception as e:
        print(f"OMIT is not a plain literal ({e}); edit it by hand.", file=sys.stderr)
        return 1
    if set(old) != set(NEW):
        print(f"OMIT keys differ from expected: have {sorted(old)}, expected {sorted(NEW)}. "
              "Nothing changed.", file=sys.stderr)
        return 1
    block = render(NEW)
    print(block)
    if a.dry_run:
        return 0
    lines = src.splitlines(keepends=True)
    start, end = node.lineno - 1, node.end_lineno
    shutil.copy(path, str(path) + ".bak")
    lines[start:end] = [block]
    path.write_text("".join(lines), encoding="utf-8")
    ast.parse(path.read_text(encoding="utf-8"))  # syntax check
    print(f"patched {path} (backup: {path}.bak)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
