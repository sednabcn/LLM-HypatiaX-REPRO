
"""Restricted AST interpreter for LLM-generated mathematical formulas.

Generated source is parsed and interpreted; it is never passed to exec/eval.
"""
import ast
import inspect
import math
import operator
import numpy as np

_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}

_FUNCTIONS = {
    "sqrt": np.sqrt, "square": np.square, "cube": lambda x: np.asarray(x) ** 3, "power": np.power,
    "abs": np.abs, "exp": np.exp, "log": np.log,
    "log2": np.log2, "log10": np.log10,
    "minimum": np.minimum, "maximum": np.maximum,
    "clip": np.clip, "arcsin": np.arcsin,
    "arccos": lambda x: np.arccos(np.clip(x, -1.0, 1.0)),
    "arctan": np.arctan, "arctan2": np.arctan2,
    "sin": np.sin, "cos": np.cos, "tan": np.tan,
    "sign": np.sign, "tanh": np.tanh,
    "sinh": np.sinh, "cosh": np.cosh,
    "norm_cdf": lambda x: 0.5 * (1.0 + np.vectorize(math.erf)(np.clip(np.asarray(x, dtype=float), -37.0, 37.0) / np.sqrt(2.0))),
    "norm_pdf": lambda x: np.exp(-0.5 * np.asarray(x, dtype=float) ** 2) / np.sqrt(2.0 * np.pi),
    "erf": lambda x: np.vectorize(math.erf)(np.asarray(x, dtype=float)),
    "erfc": lambda x: np.vectorize(math.erfc)(np.asarray(x, dtype=float)),
    "moneyness": lambda S, K: np.log(np.where(np.asarray(K, dtype=float) > 0, np.asarray(S, dtype=float) / np.asarray(K, dtype=float), np.nan)),
}

_CONSTANTS = {"pi": np.pi, "e": np.e}

# Approved bare function aliases used by older generated formulas.
# Keep their historical clipping behavior without enabling arbitrary calls.
_BARE_FUNCTIONS = {
    **_FUNCTIONS,
    "exp": lambda x: np.exp(np.clip(x, -500.0, 500.0)),
    "arcsin": lambda x: np.arcsin(np.clip(x, -1.0, 1.0)),
    "arccos": lambda x: np.arccos(np.clip(x, -1.0, 1.0)),
}


def _expression(node, env):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ValueError("Only numeric constants are allowed")
        return node.value

    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        if node.id in _CONSTANTS:
            return _CONSTANTS[node.id]
        raise ValueError(f"Unknown formula name: {node.id}")

    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        left = _expression(node.left, env)
        right = _expression(node.right, env)
        if isinstance(node.op, ast.Pow):
            if np.isscalar(right) and abs(float(right)) > 1000:
                raise ValueError("Exponent exceeds the permitted limit")
        return _BINOPS[type(node.op)](left, right)

    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_expression(node.operand, env))

    if isinstance(node, ast.Attribute):
        if isinstance(node.value, ast.Name) and node.value.id == "np":
            if node.attr in _CONSTANTS:
                return _CONSTANTS[node.attr]
        raise ValueError("Attribute access is not permitted")

    if isinstance(node, ast.Call):
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "np"
            and node.func.attr in _FUNCTIONS
        ):
            function = _FUNCTIONS[node.func.attr]
        elif isinstance(node.func, ast.Name) and node.func.id in _BARE_FUNCTIONS:
            function = _BARE_FUNCTIONS[node.func.id]
        else:
            raise ValueError("Only approved mathematical functions may be called")
        if node.keywords:
            raise ValueError("Keyword arguments in mathematical calls are not permitted")
        args = [_expression(arg, env) for arg in node.args]
        return function(*args)

    raise ValueError(f"Unsupported formula expression: {type(node).__name__}")


def parse_formula(source, constants=None):
    if not isinstance(source, str) or not source.strip():
        raise ValueError("Formula source must be a non-empty string")
    if len(source) > 20000:
        raise ValueError("Formula source is too long")

    tree = ast.parse(source, mode="exec")
    if len(list(ast.walk(tree))) > 256:
        raise ValueError("Formula is too complex")

    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise ValueError("Source must contain exactly one formula function")

    definition = tree.body[0]
    args = definition.args
    if (
        definition.name != "formula"
        or definition.decorator_list
        or args.posonlyargs
        or args.vararg
        or args.kwarg
        or args.kwonlyargs
        or args.defaults
        or args.kw_defaults
        or definition.returns is not None
    ):
        raise ValueError("Expected a plain def formula(...) with positional parameters")

    names = [arg.arg for arg in args.args]
    if not names or len(names) > 32 or len(set(names)) != len(names):
        raise ValueError("Formula must have 1–32 unique parameters")
    if any(not name.isidentifier() or name.startswith("_") for name in names):
        raise ValueError("Invalid formula parameter name")

    statements = list(definition.body)
    if statements and isinstance(statements[0], ast.Expr):
        value = statements[0].value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            statements.pop(0)

    if not statements or not isinstance(statements[-1], ast.Return):
        raise ValueError("Formula must end with a return statement")
    return_node = statements.pop().value
    if return_node is None:
        raise ValueError("Formula must return a value")

    assignments = []
    for statement in statements:
        if (
            isinstance(statement, ast.Import)
            and len(statement.names) == 1
            and statement.names[0].name == "numpy"
            and statement.names[0].asname == "np"
        ):
            # Accepted as a declaration only. It is never imported or executed.
            continue
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            raise ValueError("Only simple assignments and a final return are allowed")
        target = statement.targets[0].id
        if target in names or target.startswith("_"):
            raise ValueError("Assignments cannot overwrite parameters or private names")
        assignments.append((target, statement.value))

    supplied_constants = {}
    if constants is not None:
        if not isinstance(constants, dict):
            raise ValueError("Formula constants must be a dictionary")
        reserved = (
            set(names) | {name for name, _ in assignments}
            | set(_CONSTANTS) | set(_BARE_FUNCTIONS) | {"np"}
        )
        for key, value in constants.items():
            if (
                not isinstance(key, str)
                or not key.isidentifier()
                or key.startswith("_")
                or key in reserved
                or isinstance(value, (bool, np.bool_))
                or not isinstance(value, (int, float, np.integer, np.floating))
                or not np.isfinite(value)
            ):
                raise ValueError(f"Invalid formula constant: {key!r}")
            supplied_constants[key] = float(value)
        reserved.update(supplied_constants)

    allowed_names = (
        set(names) | {name for name, _ in assignments}
        | set(_CONSTANTS) | set(_BARE_FUNCTIONS) | {"np"}
        | set(supplied_constants)
    )
    for _, expression in assignments:
        for node in ast.walk(expression):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                if node.id not in allowed_names:
                    raise ValueError(f"Unknown formula name: {node.id}")
    for node in ast.walk(return_node):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id not in allowed_names:
                raise ValueError(f"Unknown formula name: {node.id}")

    signature = inspect.Signature([
        inspect.Parameter(name, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        for name in names
    ])

    def formula_callable(*call_args, **call_kwargs):
        bound = signature.bind(*call_args, **call_kwargs)
        env = dict(supplied_constants)
        env.update(bound.arguments)
        with np.errstate(all="ignore"):
            for target, expression in assignments:
                env[target] = _expression(expression, env)
            return _expression(return_node, env)

    formula_callable.__name__ = "formula"
    formula_callable.__signature__ = signature
    return formula_callable



def evaluate_expression(source, namespace):
    """Evaluate a mathematical expression using an explicit safe namespace."""
    if not isinstance(source, str) or not source.strip():
        raise ValueError("Expression must be a non-empty string")
    if len(source) > 20000:
        raise ValueError("Expression is too long")

    tree = ast.parse(source, mode="eval")
    if len(list(ast.walk(tree))) > 256:
        raise ValueError("Expression is too complex")

    def visit(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise ValueError("Only numeric constants are allowed")
            return node.value

        if isinstance(node, ast.Name):
            if node.id not in namespace:
                raise ValueError(f"Unknown expression name: {node.id}")
            return namespace[node.id]

        if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow):
                if np.isscalar(right) and abs(float(right)) > 1000:
                    raise ValueError("Exponent exceeds the permitted limit")
            return _BINOPS[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            return _UNARY[type(node.op)](visit(node.operand))

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in namespace:
                raise ValueError("Only explicitly supplied functions may be called")
            if node.keywords:
                raise ValueError("Keyword arguments are not permitted")
            function = namespace[node.func.id]
            if not callable(function):
                raise ValueError("Expression name is not callable")
            return function(*(visit(arg) for arg in node.args))

        raise ValueError(f"Unsupported expression element: {type(node).__name__}")

    with np.errstate(all="ignore"):
        return visit(tree.body)
