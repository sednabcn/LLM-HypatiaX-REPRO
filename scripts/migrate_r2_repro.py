#!/usr/bin/env python3
"""Migrate the central R^2 scorers to hypatiax/core/r2_canonical.py.

Why a script and not a diff: scorers are located by FUNCTION NAME with the
``ast`` module, never by line number, so it applies cleanly to any working
tree (including ones that have drifted from GitHub master). It is idempotent
(already-migrated functions are skipped) and does nothing unless --apply is
given. Every rewritten file is re-parsed before it is written.

    python scripts/migrate_r2_repro.py            # dry run: print diffs
    python scripts/migrate_r2_repro.py --apply    # write the files

Each target keeps its signature and docstring; only the body is replaced by a
call to ``r2_scored`` (canonical R^2, legacy sign-flip opt-in via
HYPATIAX_R2_SIGN_FLIP=1). The return contract of each function is preserved:

  float        -> canonical value (nan = undefined target, -inf = failed pred)
  float_raise  -> as float, but non-finite y_true raises ValueError (exp1)
  optional     -> canonical value; None when it cannot be scored (callers of
                  the _far_r2 helpers test for None); -inf when catastrophic

Inline ``ss_tot`` blocks inside large methods are NOT rewritten (not safe to
do mechanically); test_r2_policy.py keeps them on an allowlist so no new
copies can appear while they are migrated by hand.
"""
from __future__ import annotations

import argparse
import ast
import difflib
import json
import pathlib
import re
import sys

BENCH = "hypatiax/experiments/benchmarks/"
TARGETS = [
    (BENCH + "exp1_ablation.py",                         "_safe_r2", "float_raise"),
    (BENCH + "run_comparative_suite_benchmark_v2.py",    "_safe_r2", "float"),
    (BENCH + "run_comparative_suite_benchmark_pca.py",   "_safe_r2", "float"),
    (BENCH + "run_comparative_suite_benchmark_v2.py",    "_far_r2",  "optional"),
    (BENCH + "run_comparative_suite_benchmark_pca.py",   "_far_r2",  "optional"),
    (BENCH + "extrap_r2_far.py",                         "_far_r2",  "optional"),
]
MARKER = "R2-CANONICAL"
CANONICAL = "hypatiax/core/r2_canonical.py"

IMPORT_BLOCK = [
    "try:",
    "    from hypatiax.core.r2_canonical import r2_scored as _r2_scored",
    "except ImportError:  # run as a bare script, package not on sys.path",
    "    import pathlib as _pl, sys as _sys",
    "    for _up in _pl.Path(__file__).resolve().parents:",
    '        if (_up / "hypatiax" / "core" / "r2_canonical.py").is_file():',
    "            _sys.path.insert(0, str(_up))",
    "            break",
    "    from hypatiax.core.r2_canonical import r2_scored as _r2_scored",
]


def body_lines(kind: str, a: str, b: str, fname: str) -> list[str]:
    head = [
        f"# {MARKER}: single scoring policy, see hypatiax/core/r2_canonical.py.",
        "# Legacy sign-flip credit is opt-in: HYPATIAX_R2_SIGN_FLIP=1.",
        "# NOTE: any docstring above describes the pre-canonical contract.",
    ] + IMPORT_BLOCK
    if kind == "float":
        return head + [f"_val, _status = _r2_scored({a}, {b})", "return _val"]
    if kind == "float_raise":
        return head + [
            f"_val, _status = _r2_scored({a}, {b})",
            'if _status == "nonfinite_target":',
            f'    raise ValueError("non-finite y_true passed to {fname}")',
            "return _val",
        ]
    if kind == "optional":
        # contract: None = could not be scored, -inf = scored but catastrophic
        return head + [
            f"_val, _status = _r2_scored({a}, {b})",
            'if _status == "catastrophic":',
            '    return float("-inf")',
            'return _val if _status == "ok" else None',
        ]
    raise ValueError(kind)


def rewrite(src: str, name: str, kind: str):
    """Return (new_text | None, message). None means nothing to write."""
    tree = ast.parse(src)
    found = [n for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    if len(found) != 1:
        return None, f"ERROR: expected exactly 1 def {name}, found {len(found)}"
    node = found[0]
    lines = src.splitlines(keepends=True)
    seg = "".join(lines[node.lineno - 1:node.end_lineno])
    if MARKER in seg:
        return None, "already migrated"

    pos = [a.arg for a in node.args.args if a.arg not in ("self", "cls")]
    if len(pos) < 2:
        return None, f"ERROR: {name} has fewer than 2 positional args"
    a, b = pos[0], pos[1]

    first = node.body[0]
    if first.lineno <= node.lineno:
        return None, "ERROR: one-line function, refusing to rewrite"
    doc = (isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant)
           and isinstance(first.value.value, str))
    if doc:
        keep_end = first.end_lineno                      # keep through docstring
    else:
        keep_end = first.lineno - 1                      # keep the header only
        while keep_end > node.lineno and (not lines[keep_end - 1].strip()
                                          or lines[keep_end - 1].lstrip().startswith("#")):
            keep_end -= 1                                # drop old-body comments

    indent = " " * first.col_offset
    new_body = [indent + ln + "\n" if ln else "\n" for ln in body_lines(kind, a, b, name)]
    out = lines[:keep_end] + new_body + lines[node.end_lineno:]
    new = "".join(out)
    try:
        ast.parse(new)
    except SyntaxError as e:                              # never write broken code
        return None, f"ERROR: rewritten file would not parse ({e})"
    return new, f"rewrite ({kind}), lines {node.lineno}-{node.end_lineno}"


BASELINE_REL = "hypatiax/experiments/tests/r2_legacy_baseline.json"


def scan_ss_tot(root: pathlib.Path) -> list[str]:
    """Files (outside tests and the canonical module) that compute ss_tot."""
    pat = re.compile(r"\bss_tot\b")
    hits = []
    for path in (root / "hypatiax").rglob("*.py"):
        parts = set(path.parts)
        if "__pycache__" in parts or "tests" in parts or path.name == "r2_canonical.py":
            continue
        if pat.search(path.read_text(errors="ignore")):
            hits.append(path.relative_to(root).as_posix())
    return sorted(hits)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", default=str(pathlib.Path(__file__).resolve().parents[1]))
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    ap.add_argument("--write-baseline", action="store_true",
                    help="record the files that still compute ss_tot (ratchet baseline)")
    args = ap.parse_args()
    root = pathlib.Path(args.root)
    if not (root / CANONICAL).is_file():
        print(f"missing {CANONICAL} under {root}", file=sys.stderr)
        return 2
    if args.write_baseline:
        files = scan_ss_tot(root)
        (root / BASELINE_REL).write_text(json.dumps(
            {"note": "legacy files that still compute ss_tot; may only shrink",
             "files": files}, indent=2) + "\n")
        print(f"wrote {BASELINE_REL} ({len(files)} legacy files)")
        return 0

    errors = 0
    pending: dict[pathlib.Path, str] = {}
    for rel, name, kind in TARGETS:
        path = root / rel
        if not path.is_file():
            print(f"[skip] {rel}: file not found")
            continue
        # chain rewrites per file: later targets see the earlier rewrites
        new, msg = rewrite(pending.get(path) or path.read_text(), name, kind)
        print(f"[{'ERR ' if msg.startswith('ERROR') else 'ok  '}] {rel}::{name}: {msg}")
        if msg.startswith("ERROR"):
            errors += 1
        if new is not None:
            pending[path] = new

    for path, new in pending.items():
        old = path.read_text()
        if not args.apply:
            sys.stdout.writelines(difflib.unified_diff(
                old.splitlines(keepends=True), new.splitlines(keepends=True),
                f"a/{path.relative_to(root)}", f"b/{path.relative_to(root)}"))
        else:
            path.write_text(new)
            print(f"wrote {path.relative_to(root)}")
    if not args.apply and pending:
        print("\n(dry run) re-run with --apply to write these changes")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
