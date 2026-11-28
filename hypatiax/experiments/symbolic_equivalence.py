"""Conservative symbolic adjudication for saved 4060 benchmark formulas.

Generated Python is parsed through an AST allowlist and is never executed.
"""
from __future__ import annotations

import ast
import math
from typing import Any

import sympy as sp


def _clip(value: Any, lower: Any, upper: Any) -> Any:
    return sp.Min(sp.Max(value, lower), upper)


def _log10(value: Any) -> Any:
    """Base-10 logarithm (distinct from the natural logarithm)."""
    return sp.log(value, 10)


def _norm_cdf(value: Any) -> Any:
    return (1 + sp.erf(value / sp.sqrt(2))) / 2


def _norm_pdf(value: Any) -> Any:
    return sp.exp(-(value ** 2) / 2) / sp.sqrt(2 * sp.pi)


def _where(condition: Any, when_true: Any, when_false: Any) -> Any:
    if condition is sp.true:
        return when_true
    if condition is sp.false:
        return when_false
    return sp.Piecewise((when_true, condition), (when_false, True))


_FUNCTIONS = {
    "sqrt": sp.sqrt, "exp": sp.exp, "log": sp.log, "log10": _log10,
    "power": lambda a, b: a ** b, "floor": sp.floor, "ceil": sp.ceiling,
    "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
    "asin": sp.asin, "arcsin": sp.asin, "acos": sp.acos, "arccos": sp.acos,
    "atan": sp.atan, "arctan": sp.atan, "sinh": sp.sinh, "cosh": sp.cosh,
    "tanh": sp.tanh, "erf": sp.erf, "Abs": sp.Abs, "abs": sp.Abs,
    "Min": sp.Min, "min": sp.Min, "minimum": sp.Min,
    "Max": sp.Max, "max": sp.Max, "maximum": sp.Max,
    "clip": _clip, "norm_cdf": _norm_cdf, "norm_pdf": _norm_pdf,
    # np.dot is multiplication when both validated formula arguments are scalars.
    "dot": lambda a, b: a * b,
    "where": _where,
}
_BINOPS = {
    ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a ** b,
}
_UNARY = {ast.UAdd: lambda a: a, ast.USub: lambda a: -a}
_COMPARISONS = {
    ast.Eq: sp.Eq, ast.NotEq: sp.Ne, ast.Lt: sp.Lt,
    ast.LtE: sp.Le, ast.Gt: sp.Gt, ast.GtE: sp.Ge,
}


class FormulaParseError(ValueError):
    """Raised when source is outside the symbolic evaluator allowlist."""


def _numeric_constants(constants: dict[str, Any] | None) -> dict[str, Any]:
    env = {}
    for name, value in (constants or {}).items():
        if (isinstance(name, str) and name.isidentifier()
                and name not in {"pi", "e", "E"}
                and isinstance(value, (int, float)) and not isinstance(value, bool)
                and math.isfinite(float(value))):
            env[name] = sp.sympify(value)
    return env


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
    if isinstance(node, ast.Compare):
        if len(node.ops) != 1 or len(node.comparators) != 1:
            raise FormulaParseError("only single comparisons are supported")
        comparison = _COMPARISONS.get(type(node.ops[0]))
        if comparison is None:
            raise FormulaParseError("unsupported comparison operator")
        return comparison(_expr(node.left, env), _expr(node.comparators[0], env))
    if isinstance(node, ast.IfExp):
        if isinstance(node.test, ast.Constant) and isinstance(node.test.value, bool):
            condition = sp.true if node.test.value else sp.false
        else:
            condition = _expr(node.test, env)
        if condition is sp.true:
            return _expr(node.body, env)
        if condition is sp.false:
            return _expr(node.orelse, env)
        return sp.Piecewise(
            (_expr(node.body, env), condition),
            (_expr(node.orelse, env), True),
        )
    if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
            and node.value.id == "np" and node.attr in {"pi", "e", "inf"}):
        if node.attr == "pi":
            return sp.pi
        if node.attr == "e":
            return sp.E
        return sp.oo
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


def _parse_llm_function(
    source: str, variables: list[str], constants: dict[str, Any] | None = None
) -> Any:
    if not isinstance(source, str) or not source.strip() or len(source) > 20000:
        raise FormulaParseError("missing or oversized LLM formula")
    tree = ast.parse(source, mode="exec")
    if len(list(ast.walk(tree))) > 256:
        raise FormulaParseError("formula is too complex")
    # Multiple same-name definitions are legal Python: the last binding wins.
    # Accept only a sequence of plain formula definitions, with no top-level
    # executable statements, and adjudicate the final definition.
    if (not tree.body or any(
            not isinstance(item, ast.FunctionDef) or item.name != "formula"
            for item in tree.body)):
        raise FormulaParseError("expected one or more plain def formula(...) definitions")
    fn = tree.body[-1]
    args = fn.args
    if (fn.name != "formula" or fn.decorator_list or args.vararg or args.kwarg
            or args.kwonlyargs or args.posonlyargs or args.defaults or args.kw_defaults):
        raise FormulaParseError("expected a plain positional formula function")
    params = [arg.arg for arg in args.args]
    if len(params) != len(variables) or len(set(params)) != len(params):
        raise FormulaParseError("formula arity does not match saved variable order")
    env = _numeric_constants(constants)
    for param, variable in zip(params, variables):
        if param in env or variable in env:
            raise FormulaParseError("constant name collides with a formula variable")
        env[param] = sp.Symbol(variable)
    statements = list(fn.body)
    if statements and isinstance(statements[0], ast.Expr):
        value = statements[0].value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            statements.pop(0)
    if not statements or not isinstance(statements[-1], ast.Return) or statements[-1].value is None:
        raise FormulaParseError("formula must end with a value return")
    for statement in statements[:-1]:
        if (isinstance(statement, ast.Import) and len(statement.names) == 1
                and statement.names[0].name == "numpy"
                and statement.names[0].asname == "np"):
            continue
        if (not isinstance(statement, ast.Assign) or len(statement.targets) != 1
                or not isinstance(statement.targets[0], ast.Name)):
            raise FormulaParseError("only simple local assignments are supported")
        target = statement.targets[0].id
        if target.startswith("_") or target in params:
            raise FormulaParseError("assignment shadows a parameter or private name")
        value = _expr(statement.value, env)
        if target in env:
            # Reassigning a declared numeric constant to the identical value is
            # semantically inert; differing values remain rejected.
            if sp.simplify(value - env[target]) != 0:
                raise FormulaParseError("assignment shadows a declared constant")
            continue
        env[target] = value
    return _expr(statements[-1].value, env)


def _parse_ground_truth(
    source: str, variables: list[str], aliases: dict[str, str] | None = None,
    constants: dict[str, Any] | None = None,
) -> Any:
    if not isinstance(source, str) or not source.strip() or len(source) > 20000:
        raise FormulaParseError("missing or oversized ground-truth expression")
    env = _numeric_constants(constants)
    for name in variables:
        if name in env:
            raise FormulaParseError("constant name collides with a ground-truth variable")
        env[name] = sp.Symbol(name)
    for alias, canonical in (aliases or {}).items():
        if canonical not in env or not isinstance(alias, str) or not alias.isidentifier():
            raise FormulaParseError(f"invalid ground-truth alias: {alias}")
        env[alias] = env[canonical]
    tree = ast.parse(source, mode="eval")
    if len(list(ast.walk(tree))) > 256:
        raise FormulaParseError("ground-truth expression is too complex")
    return _expr(tree.body, env)


def adjudicate_symbolic_equivalence(
    llm_formula: str | None,
    ground_truth: str | None,
    variable_names: list[str] | None,
    ground_truth_aliases: dict[str, str] | None = None,
    constants: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return exact symbolic status; predictive R² is never used as a proxy."""
    if not llm_formula:
        return {"status": "no_llm_formula", "symbolically_equivalent": None}
    if not ground_truth:
        return {"status": "ground_truth_missing", "symbolically_equivalent": None}
    if (not isinstance(variable_names, list) or not variable_names
            or not all(isinstance(name, str) and name.isidentifier() for name in variable_names)
            or len(set(variable_names)) != len(variable_names)):
        return {
            "status": "variable_schema_missing",
            "symbolically_equivalent": None,
            "reason": "variable_names must be a non-empty list of unique identifiers",
        }
    try:
        llm_expr = _parse_llm_function(llm_formula, variable_names, constants)
        truth_expr = _parse_ground_truth(
            ground_truth, variable_names, ground_truth_aliases, constants
        )
        difference = sp.cancel(sp.together(llm_expr - truth_expr))
        equivalent = bool(sp.simplify(difference) == 0)
        return {
            "status": "exact_symbolic_equivalent" if equivalent else "not_symbolically_equivalent",
            "symbolically_equivalent": equivalent,
            "llm_expression_normalized": str(sp.srepr(llm_expr)),
            "ground_truth_expression_normalized": str(sp.srepr(truth_expr)),
            "comparison": "simplify(together(llm - ground_truth)) == 0",
            "scope": "formal identity under declared variable and constant mapping; domain restrictions are not inferred",
        }
    except (SyntaxError, FormulaParseError, TypeError, ValueError, sp.SympifyError) as exc:
        return {
            "status": "not_assessable",
            "symbolically_equivalent": None,
            "reason": f"{type(exc).__name__}: {exc}",
        }
