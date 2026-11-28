"""Source-backed contracts for the final assessable DeFi 40/60 mismatch cases.

These tests exercise deterministic protocol generators only. They do not run
benchmark experiments, train models, invoke providers, or mutate saved results.
"""

import numpy as np
import pytest
from scipy.stats import norm

from hypatiax.protocols.experiment_protocol_defi import DeFiExperimentProtocol


@pytest.fixture(scope="module")
def protocol():
    return DeFiExperimentProtocol()


def _case(cases, description):
    return next(case for case in cases if case[0] == description)


def _column(features, names, name):
    return features[:, names.index(name)]


def test_call_theta_includes_diffusion_and_discounted_rate_terms(protocol):
    _, features, actual, names, metadata = _case(
        protocol._generate_derivatives_tests(20),
        "Theta of option time decay of call option price per day",
    )
    spot = _column(features, names, "spot_price")
    sigma = _column(features, names, "implied_volatility")
    maturity = _column(features, names, "time_to_expiry")
    strike = 100.0
    rate = 0.04

    assert metadata["ground_truth"] == (
        "-(S*norm_pdf(d1)*sigma)/(2*sqrt(T)) "
        "- r*K*exp(-rT)*norm_cdf(d2)"
    )
    d1 = (
        np.log(spot / strike) + (rate + 0.5 * sigma**2) * maturity
    ) / (sigma * np.sqrt(maturity) + 1e-10)
    d2 = d1 - sigma * np.sqrt(maturity)
    diffusion = -(spot * norm.pdf(d1) * sigma) / (2 * np.sqrt(maturity) + 1e-10)
    discount = -rate * strike * np.exp(-rate * maturity) * norm.cdf(d2)
    expected = diffusion + discount

    np.testing.assert_allclose(actual, expected, rtol=0.0, atol=1e-10)
    assert np.all(diffusion < 0.0)
    assert np.all(discount < 0.0)


def test_position_margin_ratio_uses_signed_notional_on_declared_positive_domain(protocol):
    _, features, actual, names, metadata = _case(
        protocol._generate_liquidation_tests(20),
        "Position margin ratio at mark price including unrealised PnL",
    )
    collateral = _column(features, names, "collateral")
    unrealised_pnl = _column(features, names, "unrealised_pnl")
    notional = _column(features, names, "notional")

    assert metadata["ground_truth"] == "(collateral + upnl) / notional"
    assert np.all(notional > 0.0)
    expected = (collateral + unrealised_pnl) / (notional + 1e-10)
    np.testing.assert_allclose(actual, expected, rtol=0.0, atol=1e-10)

    # abs(notional) agrees only because this generator's declared domain is
    # strictly positive; it is not the same unrestricted symbolic formula.
    np.testing.assert_allclose(
        actual,
        (collateral + unrealised_pnl) / (np.abs(notional) + 1e-10),
        rtol=0.0,
        atol=1e-10,
    )
