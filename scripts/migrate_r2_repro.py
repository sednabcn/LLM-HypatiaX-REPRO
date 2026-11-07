#!/usr/bin/env python3
"""Conservative R2 migration helper for the private HypatiaX archive."""

import argparse
import ast
import json
import os
import re
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "HYPATIAX_R2_CANONICAL_MIGRATION_V1"
TARGETS = (
    ("hypatiax/core/metrics.py", "compute_r2", "float"),
    ("hypatiax/core/recovery_eval.py", "recovery_r2", "float"),
    ("hypatiax/core/generation/hybrid_defi_system/hybrid_system_nn_defi_domain.py",
     "r2_score_checked", "float"),
    ("hypatiax/core/generation/hybrid_all_domains_llm_nn/hybrid_system_llm_nn_all_domains.py",
     "_r2_rule_a", "float"),
    ("hypatiax/core/base_pure_llm/baseline_pure_llm_defi_discovery.py",
     "_r2_checked_call", "float"),
)
BASELINE = ROOT / "hypatiax/experiments/tests/r2_legacy_baseline.json"
_TOKEN = "ss_" + "tot"
_CANONICAL_NAMES = {"r2_checked", "_r2_checked", "r2_scored"}


def _function_nodes(tree, name):
    return [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    ]


def _has_canonical_call(node):
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        if isinstance(func, ast.Name) and func.id in _CANONICAL_NAMES:
            return True
        if (
            isinstance(func, ast.Attribute)
            and func.attr in _CANONICAL_NAMES
        ):
            return True
    return False


def rewrite(src, name, kind):
    """Rewrite one uniquely named legacy scorer while retaining its contract."""
    if kind not in {"float", "optional", "float_raise"}:
        return None, "ERROR: unsupported return kind"
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return None, f"ERROR: source does not parse: {exc}"
    nodes = _function_nodes(tree, name)
    if not nodes:
        return None, f"function {name!r} not found"
    if len(nodes) != 1:
        return None, f"ERROR: function name {name!r} is ambiguous"
    node = nodes[0]
    segment = ast.get_source_segment(src, node) or ""
    if MARKER in segment:
        return None, "already migrated"
    if not node.body:
        return None, "ERROR: function has no body"

    docstring_node = None
    first = node.body[0]
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        docstring_node = first

    if kind == "optional":
        body = [
            "# " + MARKER,
            "from hypatiax.core.r2_canonical import r2_scored",
            "value, status = r2_scored(y_true, y_pred)",
            'if status in {"degenerate_target", "nonfinite_target", '
            '"nonfinite_pred", "bad_shape"}:',
            "    return None",
            "return float(value)",
        ]
    elif kind == "float_raise":
        body = [
            "# " + MARKER,
            "import numpy as np",
            "from hypatiax.core.r2_canonical import r2_scored",
            "yt = np.asarray(y_true, dtype=float)",
            'if not np.all(np.isfinite(yt)):',
            '    raise ValueError("y_true contains NaN or inf")',
            "value, _status = r2_scored(y_true, y_pred)",
            "return float(value)",
        ]
    else:
        body = [
            "# " + MARKER,
            "from hypatiax.core.r2_canonical import r2_scored",
            "value, _status = r2_scored(y_true, y_pred)",
            "return float(value)",
        ]

    indent = " " * (node.col_offset + 4)
    rendered = [indent + line + "\n" for line in body]
    lines = src.splitlines(keepends=True)
    start_line = (
        docstring_node.end_lineno
        if docstring_node is not None
        else node.body[0].lineno - 1
    )
    end_line = node.end_lineno
    updated = lines[:start_line] + rendered + lines[end_line:]
    result = "".join(updated)
    try:
        ast.parse(result)
    except SyntaxError as exc:
        return None, f"ERROR: rewritten source does not parse: {exc}"
    return result, f"rewrite {name} ({kind})"


def _atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def apply_targets():
    errors = []
    for rel, name, _kind in TARGETS:
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"missing target file: {rel}")
            continue
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            errors.append(f"{rel}: parse error: {exc}")
            continue
        nodes = _function_nodes(tree, name)
        if len(nodes) != 1:
            errors.append(f"{rel}::{name}: expected one definition, found {len(nodes)}")
            continue
        node = nodes[0]
        segment = ast.get_source_segment(source, node) or ""
        if MARKER in segment:
            print(f"already marked: {rel}::{name}")
            continue
        if not _has_canonical_call(node):
            errors.append(f"{rel}::{name}: canonical delegation not verified")
            continue
        lines = source.splitlines(keepends=True)
        first = node.body[0]
        is_docstring = (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        )
        insert_after = first.end_lineno if is_docstring else first.lineno - 1
        marker_line = " " * (node.col_offset + 4) + "# " + MARKER + "\n"
        lines.insert(insert_after, marker_line)
        updated = "".join(lines)
        ast.parse(updated)
        _atomic_write(path, updated)
        print(f"marked: {rel}::{name}")
    if errors:
        raise SystemExit("Refusing incomplete migration:\n  " + "\n  ".join(errors))


def files_with_legacy_token():
    pattern = re.compile(r"\b" + re.escape(_TOKEN) + r"\b")
    found = set()
    package = ROOT / "hypatiax"
    for path in package.rglob("*.py"):
        if (
            "__pycache__" in path.parts
            or "tests" in path.parts
            or path.name == "r2_canonical.py"
        ):
            continue
        if pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
            found.add(path.relative_to(ROOT).as_posix())
    return sorted(found)


def write_baseline():
    current = files_with_legacy_token()
    payload = {
        "note": "legacy files that still contain the historical R2 token; may only shrink",
        "files": current,
    }
    _atomic_write(BASELINE, json.dumps(payload, indent=2) + "\n")
    print(f"wrote {len(current)} baseline entries: {BASELINE}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--apply", action="store_true")
    group.add_argument("--write-baseline", action="store_true")
    args = parser.parse_args()
    if args.apply:
        apply_targets()
    else:
        write_baseline()


if __name__ == "__main__":
    main()
