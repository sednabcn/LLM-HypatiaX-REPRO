"""Offline Core-295 catalogue loading and deterministic CI shard planning.

No model, API, Julia, PySR, or experiment code is imported or executed here.
"""
from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import sympy as sp

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST = ROOT / "config" / "core295_catalogue.json"
DOMAINS = ("Chemistry", "Biology", "Physics", "DeFi AMM", "DeFi Risk")


def load_accepted_entries(path: Path = DEFAULT_MANIFEST) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("catalogue_id") != "core295-option2":
        raise ValueError("not a Core-295 Option 2 catalogue")
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise ValueError("catalogue entries must be a list")
    accepted = [entry for entry in entries if entry.get("status") == "accepted"]
    return accepted


def plan_domain_balanced_shards(
    entries: list[dict[str, Any]], n_shards: int = 100
) -> list[list[dict[str, Any]]]:
    """Assign each accepted equation exactly once with balanced load/domains.

    Greedy deterministic assignment minimizes, in order:
      1. current shard task count,
      2. count of this task's domain in that shard,
      3. shard index.

    This is a scheduling heuristic only; it does not change model-level
    parallelism or scientific settings.
    """
    if n_shards < 1:
        raise ValueError("n_shards must be >= 1")
    ids = [entry.get("equation_id") for entry in entries]
    if any(not isinstance(value, str) or not value for value in ids):
        raise ValueError("every entry must have a non-empty equation_id")
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate equation_id in accepted catalogue")
    unknown = sorted({entry.get("domain") for entry in entries} - set(DOMAINS))
    if unknown:
        raise ValueError(f"unknown Core-295 domain(s): {unknown}")

    shards: list[list[dict[str, Any]]] = [[] for _ in range(n_shards)]
    domain_counts = [Counter() for _ in range(n_shards)]
    ordered = sorted(
        entries,
        key=lambda entry: (DOMAINS.index(entry["domain"]), entry["equation_id"]),
    )
    for entry in ordered:
        domain = entry["domain"]
        target = min(
            range(n_shards),
            key=lambda shard_id: (
                len(shards[shard_id]),
                domain_counts[shard_id][domain],
                shard_id,
            ),
        )
        shards[target].append(entry)
        domain_counts[target][domain] += 1

    return shards


def validate_shard_plan(
    entries: list[dict[str, Any]], shards: list[list[dict[str, Any]]]
) -> None:
    expected = [entry["equation_id"] for entry in entries]
    observed = [entry["equation_id"] for shard in shards for entry in shard]
    if len(observed) != len(set(observed)):
        raise ValueError("shard plan assigns an equation more than once")
    if sorted(observed) != sorted(expected):
        raise ValueError("shard plan does not cover the accepted catalogue exactly once")
    if max((len(shard) for shard in shards), default=0) - min(
        (len(shard) for shard in shards), default=0
    ) > 1:
        raise ValueError("shard task counts are not balanced to within one task")




_ALLOWED_FUNCTIONS = {
    "exp": sp.exp, "log": sp.log, "sqrt": sp.sqrt,
    "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
    "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
    "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh,
    "Abs": sp.Abs, "Min": sp.Min, "Max": sp.Max,
    "erf": sp.erf, "erfc": sp.erfc, "Piecewise": sp.Piecewise,
}


def _safe_symbolic_expression(source: str, symbols: dict[str, sp.Symbol]) -> sp.Expr:
    """Parse a deliberately small arithmetic grammar; never evaluate source code."""
    if not isinstance(source, str) or not source.strip():
        raise ValueError("canonical_expression must be a non-empty string")
    tree = ast.parse(source, mode="eval")

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return sp.sympify(node.value)
        if isinstance(node, ast.Name):
            if node.id in symbols:
                return symbols[node.id]
            if node.id == "pi":
                return sp.pi
            if node.id == "E":
                return sp.E
            if node.id in {"True", "False"}:
                return node.id == "True"
            raise ValueError(f"undeclared name {node.id!r}")
        if isinstance(node, ast.BinOp):
            left, right = visit(node.left), visit(node.right)
            operations = {
                ast.Add: lambda: left + right,
                ast.Sub: lambda: left - right,
                ast.Mult: lambda: left * right,
                ast.Div: lambda: left / right,
                ast.Pow: lambda: left ** right,
            }
            operation = operations.get(type(node.op))
            if operation is None:
                raise ValueError(f"unsupported arithmetic operator {type(node.op).__name__}")
            return operation()
        if isinstance(node, ast.UnaryOp):
            value = visit(node.operand)
            if isinstance(node.op, ast.UAdd):
                return value
            if isinstance(node.op, ast.USub):
                return -value
            if isinstance(node.op, ast.Not):
                return sp.Not(value)
            raise ValueError(f"unsupported unary operator {type(node.op).__name__}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNCTIONS:
                raise ValueError("only explicitly allow-listed mathematical functions may be called")
            if node.keywords:
                raise ValueError("keyword arguments are not supported in formula expressions")
            return _ALLOWED_FUNCTIONS[node.func.id](*(visit(arg) for arg in node.args))
        if isinstance(node, ast.Tuple):
            return tuple(visit(element) for element in node.elts)
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            left, right = visit(node.left), visit(node.comparators[0])
            op = node.ops[0]
            comparisons = {
                ast.Lt: sp.Lt, ast.LtE: sp.Le, ast.Gt: sp.Gt,
                ast.GtE: sp.Ge, ast.Eq: sp.Eq, ast.NotEq: sp.Ne,
            }
            constructor = comparisons.get(type(op))
            if constructor is None:
                raise ValueError(f"unsupported comparison {type(op).__name__}")
            return constructor(left, right)
        if isinstance(node, ast.BoolOp):
            values = [visit(value) for value in node.values]
            if isinstance(node.op, ast.And):
                return sp.And(*values)
            if isinstance(node.op, ast.Or):
                return sp.Or(*values)
        raise ValueError(f"unsupported expression syntax: {type(node).__name__}")

    expression = visit(tree)
    if not isinstance(expression, sp.Expr):
        raise ValueError("canonical_expression must evaluate to a scalar symbolic expression")
    unknown = expression.free_symbols - set(symbols.values())
    if unknown:
        raise ValueError(f"expression contains undeclared symbols: {sorted(map(str, unknown))}")
    return expression


def equations_from_manifest(
    data: dict[str, Any], *, require_complete: bool = True
) -> list[dict[str, Any]]:
    """Convert reviewed symbolic records to the Core-15 equation dictionary API.

    Expressions are parsed by a restricted AST arithmetic grammar into SymPy
    (no source-code evaluation) and lambdified against NumPy. The manifest must
    contain reviewed, accepted records. This adapter
    does not itself certify units, science, or independence.
    """
    if data.get("catalogue_id") != "core295-option2":
        raise ValueError("not a Core-295 Option 2 catalogue")
    entries = [item for item in data.get("entries", [])
               if item.get("status") == "accepted"]
    if require_complete:
        if len(entries) != 295:
            raise ValueError(f"expected 295 accepted equations, found {len(entries)}")
        for domain in DOMAINS:
            count = sum(item.get("domain") == domain for item in entries)
            if count != 59:
                raise ValueError(f"{domain}: expected 59 accepted equations, found {count}")

    ids = [item.get("equation_id") for item in entries]
    if any(not isinstance(value, str) or not value for value in ids):
        raise ValueError("accepted entries require equation_id")
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate equation_id in accepted catalogue")

    converted: list[dict[str, Any]] = []
    for item in entries:
        variables = item.get("variables")
        if not isinstance(variables, dict) or not variables:
            raise ValueError(f"{item['equation_id']}: variables must be a non-empty mapping")
        names = list(variables)
        if any(not isinstance(name, str) or not name.isidentifier() for name in names):
            raise ValueError(f"{item['equation_id']}: variable names must be identifiers")
        symbols = {name: sp.Symbol(name, real=True) for name in names}
        try:
            expression = _safe_symbolic_expression(item["canonical_expression"], symbols)
        except (KeyError, TypeError, ValueError, SyntaxError) as exc:
            raise ValueError(f"{item['equation_id']}: invalid canonical_expression: {exc}") from exc
        ranges = item.get("input_ranges")
        if not isinstance(ranges, dict) or set(ranges) != set(names):
            raise ValueError(f"{item['equation_id']}: input_ranges must match declared variables")
        train_range = []
        extrap_range = []
        for name in names:
            pair = ranges[name].get("train") if isinstance(ranges[name], dict) else None
            extra = ranges[name].get("extrapolation") if isinstance(ranges[name], dict) else None
            if not (isinstance(pair, list) and len(pair) == 2 and pair[0] < pair[1]):
                raise ValueError(f"{item['equation_id']}: invalid training range for {name}")
            if not (isinstance(extra, list) and len(extra) == 2 and extra[0] < extra[1]):
                raise ValueError(f"{item['equation_id']}: invalid extrapolation range for {name}")
            train_range.append(tuple(float(v) for v in pair))
            extrap_range.append(tuple(float(v) for v in extra))
        numeric_fn = sp.lambdify([symbols[name] for name in names], expression, modules="numpy")

        def fn(*args, _fn=numeric_fn):
            return np.asarray(_fn(*args), dtype=float)

        converted.append({
            "id": item["equation_id"],
            "name": item["name"],
            "domain": item["domain"],
            "subdomain": item["subdomain"],
            "vars": names,
            "train_range": train_range,
            "extrap_range": extrap_range,
            "fn": fn,
            "formula_latex": item.get("formula_latex", sp.latex(expression)),
            "formula_sympy": str(expression),
            "source_family_id": item["source_family_id"],
            "source_ids": list(item["source_ids"]),
        })
    return converted


def load_core295_equations(
    path: Path = DEFAULT_MANIFEST, *, require_complete: bool = True
) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return equations_from_manifest(data, require_complete=require_complete)


def smoke_check_equations(equations: list[dict[str, Any]]) -> None:
    """Evaluate each formula at three deterministic interior training points."""
    for equation in equations:
        ranges = equation["train_range"]
        sample_count = 3
        columns = [
            np.linspace(lo + (hi - lo) * 0.2, hi - (hi - lo) * 0.2, sample_count)
            for lo, hi in ranges
        ]
        try:
            output = np.asarray(equation["fn"](*columns), dtype=float)
            if output.ndim == 0:
                output = np.full(sample_count, float(output))
            output = np.broadcast_to(output, (sample_count,))
        except Exception as exc:
            raise ValueError(f"{equation['id']}: numeric smoke check failed: {exc}") from exc
        if not np.all(np.isfinite(output)):
            raise ValueError(f"{equation['id']}: formula produced non-finite smoke-test output")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--n-shards", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true", help="print the allocation; never execute experiments")
    args = parser.parse_args()
    if not args.dry_run:
        parser.error("only --dry-run is supported by this offline planner")
    entries = load_accepted_entries(args.manifest)
    if len(entries) != 295:
        raise SystemExit(
            f"catalogue is not ready for planning: {len(entries)} accepted entries found; 295 required"
        )
    for domain in DOMAINS:
        count = sum(entry["domain"] == domain for entry in entries)
        if count != 59:
            raise SystemExit(f"{domain}: expected 59 accepted entries, found {count}")
    shards = plan_domain_balanced_shards(entries, args.n_shards)
    validate_shard_plan(entries, shards)
    print(f"Core-295 dry-run: {len(entries)} equations -> {len(shards)} shards")
    for index, shard in enumerate(shards):
        counts = Counter(entry["domain"] for entry in shard)
        detail = ", ".join(f"{domain}={counts[domain]}" for domain in DOMAINS if counts[domain])
        ids = ",".join(entry["equation_id"] for entry in shard)
        print(f"shard_{index:03d}: n={len(shard)} [{detail}] tasks={ids}")
    print("No experiments were executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
