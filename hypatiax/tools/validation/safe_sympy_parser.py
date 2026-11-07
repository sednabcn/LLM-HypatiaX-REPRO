"""Restricted AST-to-SymPy parser for untrusted mathematical expressions."""

import ast


def _insert_implicit_multiplication(source):
    """Insert multiplication only between adjacent mathematical operands."""
    import io
    import tokenize

    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    output = []
    previous = None

    ends_operand = lambda t: (
        t.type in (tokenize.NAME, tokenize.NUMBER)
        or (t.type == tokenize.OP and t.string == ")")
    )
    starts_operand = lambda t: (
        t.type in (tokenize.NAME, tokenize.NUMBER)
        or (t.type == tokenize.OP and t.string == "(")
    )

    for token in tokens:
        if token.type == tokenize.NEWLINE:
            previous = None
        elif token.type not in (
            tokenize.NL, tokenize.COMMENT, tokenize.INDENT,
            tokenize.DEDENT, tokenize.ENDMARKER,
        ):
            if previous is not None and ends_operand(previous) and starts_operand(token):
                # Keep NAME(...) as a call; the AST evaluator validates its function.
                is_name_call = (
                    previous.type == tokenize.NAME
                    and token.type == tokenize.OP
                    and token.string == "("
                )
                if not is_name_call:
                    output.append((tokenize.OP, "*"))

            previous = token

        output.append((token.type, token.string))

    return tokenize.untokenize(output)


def parse_sympy_expression(source, variable_names=None):
    """Parse arithmetic and approved math calls without sympify or eval."""
    import sympy as sp

    if not isinstance(source, str) or not source.strip():
        raise ValueError("Expression must be a non-empty string")
    if len(source) > 20000:
        raise ValueError("Expression is too long")

    try:
        source = _insert_implicit_multiplication(source)
        tree = ast.parse(source, mode="eval")
    except (SyntaxError, ValueError) as exc:
        raise ValueError(f"Invalid mathematical expression: {exc}") from exc

    nodes = list(ast.walk(tree))
    if len(nodes) > 256:
        raise ValueError("Expression is too complex")

    functions = {
        "exp": sp.exp, "log": sp.log, "ln": sp.log,
        "log10": lambda x: sp.log(x, 10),
        "sqrt": sp.sqrt, "sin": sp.sin, "cos": sp.cos,
        "tan": sp.tan, "abs": sp.Abs,
        "safe_asin": sp.asin, "safe_acos": sp.acos,
        "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
        "arcsin": sp.asin, "arccos": sp.acos, "arctan": sp.atan,
        "asin_of_sin": lambda x: sp.asin(sp.Max(-1, sp.Min(1, sp.sin(x)))),
        "acos_of_cos": lambda x: sp.acos(sp.Max(-1, sp.Min(1, sp.cos(x)))),
        "atan_of_tan": sp.atan,
    }
    constants = {"pi": sp.pi, "E": sp.E}
    declared = set(variable_names or [])

    for name in declared:
        if not isinstance(name, str) or not name.isidentifier() or name.startswith("_"):
            raise ValueError(f"Invalid variable name: {name!r}")

    symbols = {}

    def build(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise ValueError("Only numeric constants are allowed")
            return sp.Integer(node.value) if isinstance(node.value, int) else sp.Float(node.value)

        if isinstance(node, ast.Name):
            name = node.id
            if name.startswith("_"):
                raise ValueError(f"Private names are not allowed: {name}")
            if name in functions:
                raise ValueError(f"Function name used without a call: {name}")
            if name in declared:
                if name not in symbols:
                    symbols[name] = sp.Symbol(name, real=True)
                return symbols[name]
            if name in constants:
                return constants[name]
            if variable_names is not None:
                raise ValueError(f"Undeclared variable: {name}")
            if name not in symbols:
                symbols[name] = sp.Symbol(name, real=True)
            return symbols[name]

        if isinstance(node, ast.BinOp):
            left, right = build(node.left), build(node.right)
            if isinstance(node.op, ast.Add):
                return sp.Add(left, right, evaluate=False)
            if isinstance(node.op, ast.Sub):
                return sp.Add(left, sp.Mul(-1, right, evaluate=False), evaluate=False)
            if isinstance(node.op, ast.Mult):
                return sp.Mul(left, right, evaluate=False)
            if isinstance(node.op, ast.Div):
                return sp.Mul(left, sp.Pow(right, -1, evaluate=False), evaluate=False)
            if isinstance(node.op, ast.Pow):
                if isinstance(node.right, ast.Constant) and abs(float(node.right.value)) > 1000:
                    raise ValueError("Numeric exponent magnitude exceeds 1000")
                return sp.Pow(left, right, evaluate=False)
            raise ValueError(f"Operator not allowed: {type(node.op).__name__}")

        if isinstance(node, ast.UnaryOp):
            value = build(node.operand)
            if isinstance(node.op, ast.UAdd):
                return value
            if isinstance(node.op, ast.USub):
                return sp.Mul(-1, value, evaluate=False)
            raise ValueError("Unary operator not allowed")

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only direct calls to approved math functions are allowed")
            name = node.func.id
            if name not in functions:
                raise ValueError(f"Function is not allowed: {name}")
            if len(node.args) != 1 or node.keywords:
                raise ValueError(f"{name} requires exactly one positional argument")
            return functions[name](build(node.args[0]))

        raise ValueError(f"Expression construct not allowed: {type(node).__name__}")

    try:
        return build(tree.body)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"Could not parse mathematical expression: {exc}") from exc
