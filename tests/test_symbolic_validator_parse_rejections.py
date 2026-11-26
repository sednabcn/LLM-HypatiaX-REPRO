"""Regression tests for strict symbolic-variable validation."""

from hypatiax.tools.validation.symbolic_validator import SymbolicValidator


def test_undeclared_engineered_feature_is_a_structured_rejection():
    validator = SymbolicValidator()
    result = validator.validate(
        expression="(log(ratio_HA_A) * -0.4345) - -4.7476",
        variable_definitions={
            "A": "Conjugate base concentration",
            "HA": "Conjugate acid concentration",
        },
        domain="defi",
    )

    assert result["valid"] is False
    assert result["syntactically_valid"] is False
    assert result["sympy_expr"] is None
    assert any("Undeclared variable: ratio_HA_A" in error for error in result["errors"])
    assert not any("Unexpected validation error" in error for error in result["errors"])


def test_declared_variables_still_validate_normally():
    validator = SymbolicValidator()
    result = validator.validate(
        expression="log(A / HA)",
        variable_definitions={
            "A": "Conjugate base concentration",
            "HA": "Conjugate acid concentration",
        },
        domain="defi",
    )

    assert result["syntactically_valid"] is True
    assert result["sympy_expr"] is not None
