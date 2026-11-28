from scripts.analysis.adjudicate_4060_source_backed_aliases import ALIASES


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
        assert ALIASES[equation] == {}


def test_aliases_are_not_generalized_across_equations():
    assert ALIASES["Impermanent loss in constant product"]["r"] == "price_ratio"
    assert ALIASES["Forward price for derivative"]["r"] == "risk_free_rate"
