"""Conservative symbolic adjudication for saved 4060 benchmark formulas.

This module parses expressions into SymPy nodes through an explicit AST allowlist.
It never executes generated Python and never treats predictive R² as symbolic recovery.
"""
from __future__ import annotations

import ast
from typing import Any

import sympy as sp

_FUNCTIONS = {
    "sqrt": sp.sqrt, "exp": sp.exp, "log": sp.log,
    "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
    "asin": sp.asin, "arcsin": sp.asin,
    "acos": sp.acos, "arccos": sp.acos,
    "atan": sp.atan, "arctan": sp.atan,
    "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh,
    "erf": sp.erf, "Abs": sp.Abs, "abs": sp.Abs,
    "Min": sp.Min, "minimum": sp.Min, "Max": sp.Max, "maximum": sp.Max,
}
_BINOPS = {
    ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a ** b,
}
_UNARY = {ast.UAdd: lambda a: a, ast.USub: lambda a: -a}


class FormulaParseError(ValueError):
    """Raised when source is outside the symbolic evaluator's allowlist."""


def _expr(node: ast.AST, env: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise FormulaParseError("only numeric literals are supported")
        return sp.sympify(node.value)
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        if node.id == "pi":
            return sp.pi
        if node.id in ("e", "E"):
            return sp.E
        raise FormulaParseError(f"unmapped symbol: {node.id}")
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        return _BINOPS[type(node.op)](_expr(node.left, env), _expr(node.right, env))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_expr(node.operand, env))
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif (isinstance(node.func, ast.Attribute)
              and isinstance(node.func.value, ast.Name)
              and node.func.value.id == "np"):
            name = node.func.attr
        else:
            raise FormulaParseError("attribute or indirect function calls are forbidden")
        function = _FUNCTIONS.get(name)
        if function is None or node.keywords:
            raise FormulaParseError(f"unsupported function call: {name}")
        return function(*[_expr(arg, env) for arg in node.args])
    raise FormulaParseError(f"unsupported syntax: {type(node).__name__}")


def _parse_llm_function(source: str, variables: list[str]) -> Any:
    if not isinstance(source, str) or not source.strip() or len(source) > 20000:
        raise FormulaParseError("missing or oversized LLM formula")
    tree = ast.parse(source, mode="exec")
    if len(list(ast.walk(tree))) > 256:
        raise FormulaParseError("formula is too complex")
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise FormulaParseError("expected exactly one def formula(...)")
    fn = tree.body[0]
    args = fn.args
    if (fn.name != "formula" or fn.decorator_list or args.vararg or args.kwarg
            or args.kwonlyargs or args.posonlyargs or args.defaults or args.kw_defaults):
        raise FormulaParseError("expected a plain positional formula function")
    params = [arg.arg for arg in args.args]
    if len(params) != len(variables) or len(set(params)) != len(params):
        raise FormulaParseError("formula arity does not match saved variable order")
    env = {param: sp.Symbol(variable) for param, variable in zip(params, variables)}
    statements = list(fn.body)
    if statements and isinstance(statements[0], ast.Expr):
        if isinstance(statements[0].value, ast.Constant) and isinstance(statements[0].value.value, str):
            statements.pop(0)
    if not statements or not isinstance(statements[-1], ast.Return) or statements[-1].value is None:
        raise FormulaParseError("formula must end with a value return")
    for statement in statements[:-1]:
        if (not isinstance(statement, ast.Assign) or len(statement.targets) != 1
                or not isinstance(statement.targets[0], ast.Name)):
            # The only accepted non-assignment is the harmless numpy import declaration.
            if (isinstance(statement, ast.Import) and len(statement.names) == 1
                    and statement.names[0].name == "numpy"
                    and statement.names[0].asname == "np"):
                continue
            raise FormulaParseError("only simple local assignments are supported")
        target = statement.targets[0].id
        if target in env or target.startswith("_"):
            raise FormulaParseError("assignment shadows a parameter or private name")
        env[target] = _expr(statement.value, env)
    return _expr(statements[-1].value, env)


def _parse_ground_truth(source: str, variables: list[str],
                        aliases: dict[str, str] | None = None) -> Any:
    if not isinstance(source, str) or not source.strip() or len(source) > 20000:
        raise FormulaParseError("missing or oversized ground-truth expression")
    alias_map = aliases or {}
    env = {name: sp.Symbol(name) for name in variables}
    for alias, canonical in alias_map.items():
        if canonical not in env or not alias.isidentifier():
            raise FormulaParseError(f"invalid ground-truth alias: {alias}")
        env[alias] = env[canonical]
    return _expr(ast.parse(source, mode="eval").body, env)


def adjudicate_symbolic_equivalence(
    llm_formula: str | None,
    ground_truth: str | None,
    variable_names: list[str] | None,
    ground_truth_aliases: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return a conservative exact-symbolic result, never a predictive-score proxy."""
    if not llm_formula:
        return {"status": "no_llm_formula", "symbolically_equivalent": None}
    if not ground_truth:
        return {"status": "ground_truth_missing", "symbolically_equivalent": None}
    if not isinstance(variable_names, list) or not variable_names:
        return {"status": "variable_schema_missing", "symbolically_equivalent": None}
    try:
        llm_expr = _parse_llm_function(llm_formula, variable_names)
        truth_expr = _parse_ground_truth(ground_truth, variable_names, ground_truth_aliases)
        difference = sp.cancel(sp.together(llm_expr - truth_expr))
        equivalent = bool(sp.simplify(difference) == 0)
        return {
            "status": "exact_symbolic_equivalent" if equivalent else "not_symbolically_equivalent",
            "symbolically_equivalent": equivalent,
            "llm_expression_normalized": str(sp.srepr(llm_expr)),
            "ground_truth_expression_normalized": str(sp.srepr(truth_expr)),
            "comparison": "simplify(together(llm - ground_truth)) == 0",
            "scope": "formal identity under declared variable mapping; domain restrictions are not inferred",
        }
    except (SyntaxError, FormulaParseError, TypeError, ValueError, sp.SympifyError) as exc:
        return {
            "status": "not_assessable",
            "symbolically_equivalent": None,
            "reason": f"{type(exc).__name__}: {exc}",
        }
