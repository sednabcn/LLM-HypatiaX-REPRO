import pytest
import sympy as sp

from hypatiax.tools.validation.symbolic_validator import safe_sympify as symbolic_parse
from hypatiax.tools.validation.ensemble_validator import safe_sympify as ensemble_parse
from hypatiax.tools.validation.dimensional_validator import safe_sympify as dimensional_parse


@pytest.mark.parametrize("parser", [
    symbolic_parse,
    ensemble_parse,
    dimensional_parse,
])
def test_validator_parser_accepts_implicit_multiplication(parser):
    result = parser("2x + sin(y)", ["x", "y"])
    assert result.has(sp.Symbol("x", real=True))
    assert result.has(sp.Symbol("y", real=True))


@pytest.mark.parametrize("parser", [
    symbolic_parse,
    ensemble_parse,
    dimensional_parse,
])
def test_validator_parser_rejects_undeclared_variables(parser):
    with pytest.raises(ValueError, match="Undeclared variable"):
        parser("x + y", ["x"])


@pytest.mark.parametrize("parser", [
    symbolic_parse,
    ensemble_parse,
    dimensional_parse,
])
@pytest.mark.parametrize("source", [
    "__import__('os')",
    "unknown_function(x)",
    "sp.sqrt(x)",
    "open('secret')",
])
def test_validator_parser_rejects_unsafe_calls(parser, source):
    with pytest.raises(ValueError):
        parser(source, ["x"])
