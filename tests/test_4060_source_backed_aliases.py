from scripts.analysis.adjudicate_4060_source_backed_aliases import (
    ALIASES, SOURCE_BACKED_CONSTANTS, expand_source_defined_d1_d2,
)
from hypatiax.experiments.audit import audit_formula


def test_alias_manifest_is_equation_specific_and_well_formed():
    assert len(ALIASES) >= 50
    for equation, aliases in ALIASES.items():
        assert isinstance(equation, str) and equation
        assert isinstance(aliases, dict)
        for alias, canonical in aliases.items():
            assert alias.isidentifier()
            assert canonical.isidentifier()
            assert alias != canonical


def test_liquidation_formulas_do_not_receive_symbol_aliases():
    for equation in (
        "Liquidation Price Long",
        "Liquidation Price Short",
        "Liquidation price for leveraged long",
        "Liquidation price for leveraged short",
    ):
        assert ALIASES.get(equation, {}) == {}


def test_aliases_are_not_generalized_across_equations():
    assert ALIASES["Impermanent loss in constant product"]["r"] == "price_ratio"
    assert ALIASES["Forward price for derivative"]["r"] == "risk_free_rate"



def test_scalar_dot_is_adjudicated_as_multiplication():
    result = audit_formula(
        "def formula(x, y):\n    return np.dot(x, y)",
        "x * y",
        ["x", "y"],
    )
    assert result["status"] == "exact_symbolic_equivalent"


def test_where_comparison_is_preserved_as_piecewise():
    result = audit_formula(
        "def formula(x):\n    return np.where(x == 0, 0, 1 / x)",
        "1 / x",
        ["x"],
    )
    assert result["status"] == "not_symbolically_equivalent"


def test_identical_constant_reassignment_is_safe():
    result = audit_formula(
        "def formula(x):\n    scale = 2.0\n    return x * scale",
        "x * scale",
        ["x"],
        constants={"scale": 2.0},
    )
    assert result["status"] == "exact_symbolic_equivalent"


def test_final_redefinition_is_the_effective_python_function():
    result = audit_formula(
        "def formula(x):\n    return x + 100\n"
        "def formula(x):\n    return 2 * x",
        "2 * x",
        ["x"],
    )
    assert result["status"] == "exact_symbolic_equivalent"



def test_literal_conditional_selects_the_effective_branch():
    result = audit_formula(
        "def formula(x):\n    return x + 1 if False else x * 2",
        "2 * x",
        ["x"],
    )
    assert result["status"] == "exact_symbolic_equivalent"



def test_theta_constants_are_recovered_from_protocol_source():
    assert SOURCE_BACKED_CONSTANTS["Theta of option"] == {"K": 100.0, "r": 0.04}


def test_black_scholes_helper_symbols_are_expanded_from_source_definition():
    expanded = expand_source_defined_d1_d2(
        "Gamma of option", "norm_pdf(d1) / (S * sigma * sqrt(T))"
    )
    assert "d1" not in expanded
    assert "sigma" in expanded



def test_numpy_infinity_is_a_safe_symbolic_constant():
    result = audit_formula(
        "def formula(x):\n    return np.where(x > 0, 1 / x, np.inf)",
        "1 / x",
        ["x"],
    )
    assert result["status"] == "not_symbolically_equivalent"
