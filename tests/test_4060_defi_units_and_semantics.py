"""Source-backed contracts for DeFi percentage units and output semantics.

These tests exercise deterministic protocol generators only. They do not run
experiments, train models, invoke an LLM/provider, or touch saved benchmark data.
"""

import numpy as np
import pytest

from hypatiax.protocols.experiment_protocol_defi import DeFiExperimentProtocol


@pytest.fixture(scope="module")
def protocol():
    return DeFiExperimentProtocol()


def _case(cases, description):
    return next(case for case in cases if case[0] == description)


def _column(features, names, name):
    return features[:, names.index(name)]


@pytest.mark.parametrize(
    ("description", "formula"),
    [
        (
            "Impermanent loss percentage in AMM",
            "(2*sqrt(r)/(1+r) - 1) * 100",
        ),
        (
            "LP share percentage after deposit relative to pool total",
            "deposit / pool_total * 100",
        ),
        (
            "Price slippage percentage in AMM swap from trade size",
            "100 * dx / (2*x + dx)",
        ),
        (
            "Simple options moneyness percentage relative to strike price",
            "(S - K) / K * 100",
        ),
    ],
)
def test_percentage_outputs_are_scaled_to_percentage_points(protocol, description, formula):
    if description == "Impermanent loss percentage in AMM":
        cases = protocol._generate_amm_tests(12)
    elif description in {
        "LP share percentage after deposit relative to pool total",
        "Price slippage percentage in AMM swap from trade size",
    }:
        cases = protocol._generate_amm_tests(12)
    else:
        cases = protocol._generate_derivatives_tests(12)

    _, features, actual, names, metadata = _case(cases, description)
    assert metadata["ground_truth"] == formula

    if description == "Impermanent loss percentage in AMM":
        ratio = _column(features, names, "price_ratio")
        fraction = 2 * np.sqrt(ratio) / (1 + ratio) - 1
        expected = fraction * 100
        assert np.all(actual <= 0.0)
    elif description == "LP share percentage after deposit relative to pool total":
        deposit = _column(features, names, "lp_deposit")
        pool_total = _column(features, names, "pool_total")
        expected = deposit / (pool_total + 1e-10) * 100
        assert np.all((actual > 0.0) & (actual < 100.0))
    elif description == "Price slippage percentage in AMM swap from trade size":
        reserve = _column(features, names, "reserve_x")
        dx = _column(features, names, "trade_dx")
        expected = 100.0 * dx / (2 * reserve + dx + 1e-10)
        assert np.all((actual > 0.0) & (actual < 100.0))
    else:
        spot = _column(features, names, "spot_price")
        expected = (spot - 100.0) / 100.0 * 100.0

    np.testing.assert_allclose(actual, expected, rtol=0.0, atol=1e-10)


def test_effective_leverage_price_change_is_a_decimal_fraction(protocol):
    cases = protocol._generate_trading_tests(12)
    _, features, actual, names, metadata = _case(
        cases, "Effective Leverage accounting for price movement"
    )
    leverage = _column(features, names, "initial_leverage")
    delta_p = _column(features, names, "price_change_pct")

    assert metadata["ground_truth"] == "L / (1 + L * delta_p)"
    assert np.all((delta_p >= -0.20) & (delta_p <= 0.20))
    expected = leverage / (1.0 + leverage * delta_p + 1e-10)
    np.testing.assert_allclose(actual, expected, rtol=0.0, atol=1e-10)


def test_slashing_rate_is_a_fraction_not_percentage_points(protocol):
    cases = protocol._generate_staking_tests(12)
    _, features, actual, names, metadata = _case(
        cases,
        "Slashing penalty for validator misbehavior proportional to stake",
    )
    stake = _column(features, names, "staked_amount")
    slash_fraction = _column(features, names, "slash_pct")

    assert metadata["ground_truth"] == "staked * slash_pct"
    assert np.all((slash_fraction >= 0.005) & (slash_fraction <= 0.10))
    expected = stake * slash_fraction
    np.testing.assert_allclose(actual, expected, rtol=0.0, atol=1e-10)


def test_utilization_is_borrowed_over_positive_supplied_liquidity(protocol):
    cases = protocol._generate_lending_tests(12)
    _, features, actual, names, metadata = _case(
        cases, "Utilization rate of DeFi lending pool (borrowed / supplied)"
    )
    borrowed = _column(features, names, "total_borrowed")
    supplied = _column(features, names, "total_supplied")

    assert metadata["ground_truth"] == "borrowed / supplied"
    assert np.all(supplied > 0.0)
    assert np.all((actual > 0.0) & (actual < 1.0))
    np.testing.assert_allclose(actual, borrowed / (supplied + 1e-10), rtol=0.0, atol=1e-10)


def test_compounding_staking_output_is_total_balance_not_interest_only(protocol):
    cases = protocol._generate_staking_tests(12)
    _, features, actual, names, metadata = _case(
        cases, "Compounding Staking Returns with auto-compounding rewards"
    )
    principal = _column(features, names, "principal")
    apr = _column(features, names, "apr")
    compounds = _column(features, names, "compounds_per_year")

    assert metadata["ground_truth"] == "principal * (1 + apr/n)**n"
    expected_balance = principal * (1.0 + apr / compounds) ** compounds
    np.testing.assert_allclose(actual, expected_balance, rtol=0.0, atol=1e-10)
    assert np.all(actual > principal)
    # Interest-earned semantics would be expected_balance - principal.
    assert not np.allclose(actual, expected_balance - principal)


def test_simple_staking_annual_reward_is_reward_amount_not_total_balance(protocol):
    cases = protocol._generate_staking_tests(12)
    _, features, actual, names, metadata = _case(
        cases, "Simple Staking APY annual reward for staked tokens"
    )
    stake = _column(features, names, "staked_amount")
    rate = _column(features, names, "reward_rate")

    assert metadata["ground_truth"] == "staked_amount * reward_rate"
    expected_reward = stake * rate
    np.testing.assert_allclose(actual, expected_reward, rtol=0.0, atol=1e-10)
    assert np.all(actual < stake)
