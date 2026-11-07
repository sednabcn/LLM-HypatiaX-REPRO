import pytest
import sympy as sp

from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression


@pytest.mark.parametrize("source, expected", [
    ("x + y", "x + y"),
    ("2 * x", "2*x"),
    ("2x", "2*x"),
    ("3(x + 1)", "3*(x + 1)"),
    ("(x + 1)(y + 1)", "(x + 1)*(y + 1)"),
    ("sin(x)", "sin(x)"),
    ("sqrt(x)", "sqrt(x)"),
    ("log(x)", "log(x)"),
])
def test_valid_expressions(source, expected):
    variables = ["x", "y"]
    symbols = {name: sp.Symbol(name, real=True) for name in variables}
    actual = parse_sympy_expression(source, variables)
    reference = sp.sympify(expected, locals=symbols, evaluate=False)
    values = {symbols["x"]: 2, symbols["y"]: 3}
    actual_value = float(actual.subs(values).evalf())
    reference_value = float(reference.subs(values).evalf())
    assert actual_value == pytest.approx(reference_value, rel=1e-12)


def test_scientific_notation():
    result = parse_sympy_expression("1.5e-4*x", ["x"])
    assert sp.simplify(result - sp.Float("1.5e-4") * sp.Symbol("x", real=True)) == 0


def test_undeclared_variable_rejected():
    with pytest.raises(ValueError, match="Undeclared variable"):
        parse_sympy_expression("x + y", ["x"])


@pytest.mark.parametrize("source", [
    "__import__('os')",
    "sp.sqrt(x)",
    "unknown_function(x)",
    "x(y + 1)",
    "open('secret')",
    "x[0]",
    "(lambda: 1)()",
])
def test_unsafe_expressions_rejected(source):
    with pytest.raises(ValueError):
        parse_sympy_expression(source, ["x", "y"])


def test_private_name_rejected():
    with pytest.raises(ValueError):
        parse_sympy_expression("_secret + x", ["x", "_secret"])


def test_excessive_numeric_exponent_rejected():
    with pytest.raises(ValueError, match="exponent"):
        parse_sympy_expression("x**1001", ["x"])
