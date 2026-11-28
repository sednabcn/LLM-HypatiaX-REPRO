"""Offline fail-closed generated-formula gate regression tests."""

from hypatiax.experiments.audit import validate_generated_formula


def test_exact_formula_is_eligible_only_after_symbolic_identity():
    result = validate_generated_formula(
        "def formula(entry_price, leverage):\n    return entry_price * (1 - 1 / (leverage * 0.8))",
        "entry_price * (1 - 1/(leverage * 0.8))",
        ["entry_price", "leverage"],
    )
    assert result["status"] == "exact_symbolic_equivalent"
    assert result["symbolically_equivalent"] is True
    assert result["eligible_for_exact_match"] is True
    assert result["validation_scope"] == "future_run_offline_gate"


def test_sign_error_is_not_eligible_even_if_formula_is_parseable():
    result = validate_generated_formula(
        "def formula(entry_price, leverage):\n    return entry_price * (1 + 1 / (leverage * 0.8))",
        "entry_price * (1 - 1/(leverage * 0.8))",
        ["entry_price", "leverage"],
    )
    assert result["status"] == "not_symbolically_equivalent"
    assert result["eligible_for_exact_match"] is False


def test_percentage_points_and_fraction_are_not_conflated():
    result = validate_generated_formula(
        "def formula(deposit, pool_total):\n    return deposit / pool_total",
        "deposit / pool_total * 100",
        ["deposit", "pool_total"],
    )
    assert result["status"] == "not_symbolically_equivalent"
    assert result["eligible_for_exact_match"] is False


def test_output_semantics_difference_is_not_eligible():
    result = validate_generated_formula(
        "def formula(principal, apr, n):\n    return principal * ((1 + apr / n) ** n - 1)",
        "principal * (1 + apr/n)**n",
        ["principal", "apr", "n"],
    )
    assert result["status"] == "not_symbolically_equivalent"
    assert result["eligible_for_exact_match"] is False


def test_malformed_or_unsupported_formula_remains_not_assessable():
    result = validate_generated_formula(
        "def formula(x):\n    return eval('x')",
        "x",
        ["x"],
    )
    assert result["status"] == "not_assessable"
    assert result["symbolically_equivalent"] is None
    assert result["eligible_for_exact_match"] is False


def test_missing_variable_schema_fails_before_symbolic_comparison():
    result = validate_generated_formula(
        "def formula(x):\n    return x",
        "x",
        [],
    )
    assert result["status"] == "variable_schema_missing"
    assert result["eligible_for_exact_match"] is False


def test_explicit_aliases_and_source_constants_are_supported():
    result = validate_generated_formula(
        "def formula(price, lev):\n    return price * (1 - 1 / (lev * MMR))",
        "entry_price * (1 - 1 / (leverage * MMR))",
        ["entry_price", "leverage"],
        ground_truth_aliases={"price": "entry_price", "lev": "leverage"},
        constants={"MMR": 0.8},
    )
    assert result["status"] == "exact_symbolic_equivalent"
    assert result["eligible_for_exact_match"] is True
