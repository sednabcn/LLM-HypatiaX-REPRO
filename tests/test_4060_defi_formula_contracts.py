"""Source-backed mathematical contracts for the DeFi 40/60 liquidation cases.

These tests exercise only deterministic protocol data generation. They do not
run an experiment, invoke a model, or modify any saved benchmark artifact.
"""

import numpy as np
import pytest

from hypatiax.protocols.experiment_protocol_defi import DeFiExperimentProtocol


@pytest.fixture(scope="module")
def liquidation_cases():
    protocol = DeFiExperimentProtocol()
    return protocol._generate_liquidation_tests(10)


def _case(cases, description):
    return next(case for case in cases if case[0] == description)


@pytest.mark.parametrize(
    ("description", "target"),
    [
        (
            "Liquidation price for leveraged long position",
            "entry_price * (1 - 1/(leverage * 0.8))",
        ),
        (
            "Liquidation price for leveraged short position",
            "entry_price * (1 + 1/(leverage * 0.8))",
        ),
        (
            "Maximum safe leverage for given acceptable loss tolerance",
            "1 / (loss_pct * 0.8)",
        ),
    ],
)
def test_liquidation_ground_truth_contracts_are_explicit(liquidation_cases, description, target):
    metadata = _case(liquidation_cases, description)[4]
    assert metadata["ground_truth"] == target
    assert metadata["constants"]["maintenance_margin"] == pytest.approx(0.8)


def test_long_liquidation_price_uses_below_entry_sign_and_leverage_fraction(liquidation_cases):
    _, features, actual, names, metadata = _case(
        liquidation_cases, "Liquidation price for leveraged long position"
    )
    entry_price = features[:, names.index("entry_price")]
    leverage = features[:, names.index("leverage")]
    expected = entry_price * (1.0 - 1.0 / (leverage * 0.8))

    np.testing.assert_allclose(actual, expected, rtol=0.0, atol=1e-10)
    assert np.all(actual < entry_price)
    assert metadata["constants"]["maintenance_margin"] == pytest.approx(0.8)


def test_short_liquidation_price_uses_above_entry_sign_and_leverage_fraction(liquidation_cases):
    _, features, actual, names, metadata = _case(
        liquidation_cases, "Liquidation price for leveraged short position"
    )
    entry_price = features[:, names.index("entry_price")]
    leverage = features[:, names.index("leverage")]
    expected = entry_price * (1.0 + 1.0 / (leverage * 0.8))

    np.testing.assert_allclose(actual, expected, rtol=0.0, atol=1e-10)
    assert np.all(actual > entry_price)
    assert metadata["constants"]["maintenance_margin"] == pytest.approx(0.8)


def test_maximum_safe_leverage_treats_loss_tolerance_as_fraction_not_percent(liquidation_cases):
    _, features, actual, names, metadata = _case(
        liquidation_cases, "Maximum safe leverage for given acceptable loss tolerance"
    )
    loss_fraction = features[:, names.index("acceptable_loss_pct")]
    expected = 1.0 / (loss_fraction * 0.8)

    np.testing.assert_allclose(actual, expected, rtol=0.0, atol=1e-10)
    assert np.all((loss_fraction >= 0.05) & (loss_fraction <= 0.20))
    assert metadata["ground_truth"] == "1 / (loss_pct * 0.8)"


def test_trading_liquidation_variants_preserve_long_short_sign_conventions():
    cases = DeFiExperimentProtocol()._generate_trading_tests(10)
    for description, sign in (
        ("Liquidation Price Long for leveraged long trading position", -1.0),
        ("Liquidation Price Short for leveraged short trading position", 1.0),
    ):
        _, features, actual, names, metadata = _case(cases, description)
        entry_price = features[:, names.index("entry_price")]
        leverage = features[:, names.index("leverage")]
        expected = entry_price * (1.0 + sign / (leverage * 0.8))
        np.testing.assert_allclose(actual, expected, rtol=0.0, atol=1e-10)
        assert metadata["constants"]["maintenance_margin"] == pytest.approx(0.8)
