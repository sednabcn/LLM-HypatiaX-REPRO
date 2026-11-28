"""Additional source-backed contracts for remaining DeFi 40/60 families.

Only deterministic protocol data generators are exercised; no benchmark run,
model training, provider call, or saved artifact mutation occurs here.
"""

import numpy as np
import pytest

from hypatiax.protocols.experiment_protocol_defi import DeFiExperimentProtocol


@pytest.fixture(scope="module")
def protocol():
    return DeFiExperimentProtocol()


def _case(cases, description):
    return next(case for case in cases if case[0] == description)


def _col(features, names, name):
    return features[:, names.index(name)]


def test_component_expected_shortfall_uses_weight_es_and_correlation(protocol):
    _, X, actual, names, metadata = _case(
        protocol._generate_es_tests(16),
        "Component ES for portfolio position from weight and correlation",
    )
    weight, es, corr = (_col(X, names, n) for n in ("weight", "individual_es", "correlation"))
    assert metadata["ground_truth"] == "weight * ES * (1 + correlation)"
    assert np.all((weight > 0) & (weight < 1))
    assert np.all(corr >= 0)
    np.testing.assert_allclose(actual, weight * es * (1 + corr), rtol=0, atol=1e-10)


def test_portfolio_expected_shortfall_uses_signed_correlation_term(protocol):
    _, X, actual, names, metadata = _case(
        protocol._generate_es_tests(16),
        "Portfolio Expected Shortfall for correlated positions",
    )
    es1, es2, rho = (_col(X, names, n) for n in ("position1_es", "position2_es", "correlation"))
    assert metadata["ground_truth"] == "ES1 + ES2 + rho*sqrt(ES1*ES2)"
    assert np.any(rho < 0) and np.any(rho > 0)
    np.testing.assert_allclose(actual, es1 + es2 + rho * np.sqrt(es1 * es2), rtol=0, atol=1e-10)


def test_concentrated_liquidity_width_is_upper_lower_price_ratio(protocol):
    _, X, actual, names, metadata = _case(
        protocol._generate_liquidity_tests(16),
        "Concentrated liquidity position width from upper and lower price bounds",
    )
    lower, upper = (_col(X, names, n) for n in ("price_lower", "price_upper"))
    assert metadata["ground_truth"] == "P_upper / P_lower"
    np.testing.assert_allclose(actual, upper / (lower + 1e-10), rtol=0, atol=1e-10)


def test_capital_efficiency_is_upper_price_over_price_range(protocol):
    _, X, actual, names, metadata = _case(
        protocol._generate_liquidity_tests(16),
        "Capital efficiency multiplier for concentrated liquidity position",
    )
    lower, upper = (_col(X, names, n) for n in ("price_lower", "price_upper"))
    assert metadata["ground_truth"] == "P_upper / (P_upper - P_lower)"
    expected = upper / (upper - lower)
    np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-10)


def test_kelly_position_is_risk_adjusted_and_capped_at_one(protocol):
    _, X, actual, names, metadata = _case(
        protocol._generate_liquidity_tests(16),
        "Optimal LP Position (Kelly) using risk-adjusted Kelly criterion",
    )
    mu, sigma = (_col(X, names, n) for n in ("expected_fee_apy", "il_risk"))
    assert metadata["ground_truth"] == "min(mu / (2 * sigma**2), 1.0)"
    assert metadata["constants"]["risk_aversion"] == pytest.approx(2.0)
    expected = np.minimum(mu / (2.0 * sigma**2), 1.0)
    np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-10)
    assert np.all((actual >= 0) & (actual <= 1))


def test_amm_convexity_adjustment_uses_half_trade_depth_term(protocol):
    _, X, actual, names, metadata = _case(
        protocol._generate_amm_tests(16),
        "Convexity Adjustment effective price in AMM with slippage",
    )
    spot, trade, depth = (_col(X, names, n) for n in ("spot_price", "trade_size", "pool_depth"))
    assert metadata["ground_truth"] == "spot * (1 + 0.5 * trade_size / pool_depth)"
    expected = spot * (1 + 0.5 * trade / (depth + 1e-10))
    np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-10)


def test_uniswap_v3_virtual_liquidity_uses_sqrt_price_span(protocol):
    _, X, actual, names, metadata = _case(
        protocol._generate_amm_tests(16),
        "Uniswap V3 virtual liquidity L for concentrated position",
    )
    lower, upper, amount = (
        _col(X, names, n) for n in ("price_lower", "price_upper", "token_amount")
    )
    assert metadata["ground_truth"] == "amount / (sqrt(P_upper) - sqrt(P_lower))"
    expected = amount / (np.sqrt(upper) - np.sqrt(lower) + 1e-10)
    np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-10)


def test_options_delta_is_clipped_linear_proxy_not_unbounded_delta(protocol):
    _, X, actual, names, metadata = _case(
        protocol._generate_derivatives_tests(16),
        "Options Delta rate of change of option price relative to underlying",
    )
    m, vol, expiry = (
        _col(X, names, n) for n in ("moneyness", "implied_volatility", "time_to_expiry")
    )
    assert metadata["ground_truth"] == "clip(0.5 + m/(2*vol*sqrt(T)), 0, 1)"
    expected = np.clip(0.5 + m / (2 * vol * np.sqrt(expiry) + 1e-10), 0.0, 1.0)
    np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-10)
    assert np.all((actual >= 0) & (actual <= 1))
