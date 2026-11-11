import numpy as np

from hypatiax.core.routing import (
    kde_ood_probability,
    manuscript_blend_weights,
    select_hypatiax_route,
    structural_risk_tokens,
    training_edge_degradation_probe,
)


def test_detects_exact_transcendental_calls_not_substrings():
    assert structural_risk_tokens("def formula(x):\n    return np.exp(x) + math.erf(x)") == ["erf", "exp"]
    assert structural_risk_tokens("def formula(exponential_rate):\n    return exponential_rate + 1") == []


def test_structural_risk_overrides_high_fit_pure_llm_route():
    llm = np.array([1.0, 2.0, 3.0])
    nn = np.array([1.1, 1.9, 3.1])
    route = select_hypatiax_route(
        0.99, 0.80, llm, nn, ["exp"], degradation_delta=0.01,
        degradation_tau=0.1, p_ood=0.5,
    )
    assert route["decision"] == "ensemble"
    assert route["route_reason"] == "structural_risk_precedence"
    assert route["structural_risk_flag"] is True
    assert np.isclose(route["blend_weights"]["llm"], 0.3)
    assert np.isclose(route["blend_weights"]["nn"], 0.7)


def test_high_fit_without_structural_risk_needs_low_degradation():
    route = select_hypatiax_route(
        0.99, 0.80, np.ones(3), np.zeros(3), [],
        degradation_delta=0.02, degradation_tau=0.1,
    )
    assert route["decision"] == "fitted_llm"
    assert route["route_reason"] == "trusted_high_fit_low_degradation"


def test_missing_tau_fails_closed_to_ensemble():
    route = select_hypatiax_route(0.99, 0.80, np.ones(3), np.zeros(3), [])
    assert route["decision"] == "ensemble"
    assert route["route_reason"] == "degradation_probe_or_tau_unavailable"


def test_degradation_above_tau_requires_ensemble():
    route = select_hypatiax_route(
        0.99, 0.80, np.ones(3), np.zeros(3), [],
        degradation_delta=0.2, degradation_tau=0.1,
    )
    assert route["decision"] == "ensemble"
    assert route["route_reason"] == "degradation_exceeds_tau_or_fit_below_0.95"


def test_failed_trust_gate_routes_to_nn():
    route = select_hypatiax_route(0.49, 0.90, np.ones(3), np.zeros(3), ["sin"])
    assert route["decision"] == "nn"
    assert route["route_reason"] == "trust_gate_failed"
    assert route["trust_gate_passed"] is False


def test_formula_fragment_fallback_detects_function_calls():
    assert structural_risk_tokens("exp(x") == ["exp"]


def test_detects_all_manuscript_function_names():
    assert structural_risk_tokens("Phi(x) + log(x) + sin(x) + cos(x)") == [
        "Phi", "cos", "log", "sin"
    ]


def test_structural_risk_fails_closed_when_nn_prediction_is_unavailable():
    route = select_hypatiax_route(
        0.99, 0.0, np.ones(3), None, ["erf"],
        degradation_delta=0.01, degradation_tau=0.1,
    )
    assert route["decision"] == "nn"
    assert route["predictions"] is None
    assert route["route_reason"] == "structural_risk_precedence_nn_unavailable"


def test_training_edge_probe_uses_outer_training_rows():
    x = np.linspace(-2.0, 2.0, 100).reshape(-1, 1)
    y = x[:, 0]
    pred = y.copy()
    edge = np.r_[0:10, 90:100]
    pred[edge] += 10.0
    result = training_edge_degradation_probe(x, y, pred, edge_fraction=0.2)
    assert result["status"] == "ok"
    assert result["r2_train"] > result["r2_edge"]
    assert result["delta"] == result["r2_train"] - result["r2_edge"]
    assert result["delta"] > 0.0
    assert result["n_edge"] == 20


def test_kde_ood_probability_uses_training_covariates_only():
    x_train = np.linspace(-2.0, 2.0, 100).reshape(-1, 1)
    in_domain = kde_ood_probability(x_train, np.array([[0.0], [0.1]]))
    out_domain = kde_ood_probability(x_train, np.array([[20.0], [25.0]]))
    assert in_domain["status"] == out_domain["status"] == "ok"
    assert out_domain["p_ood"] > in_domain["p_ood"]
    assert out_domain["p_ood"] > 0.9


def test_manuscript_blend_weights():
    weights = manuscript_blend_weights(0.8, alpha=0.3)
    assert np.isclose(weights["llm"], 0.86)
    assert np.isclose(weights["nn"], 0.14)
    assert np.isclose(weights["llm"] + weights["nn"], 1.0)


def test_query_blend_weights_vary_with_query_ood_probability():
    route = select_hypatiax_route(
        0.8, 0.7, np.ones(3), np.zeros(3), ["exp"],
        p_ood=0.5, p_ood_per_query=[0.0, 1.0],
    )
    assert route["decision"] == "ensemble"
    assert np.allclose(route["query_blend_weights"]["llm"], [0.3, 1.0])
    assert np.allclose(route["query_blend_weights"]["nn"], [0.7, 0.0])
    # Training predictions use the in-distribution alpha floor, not query OOD.
    assert np.isclose(route["blend_weights"]["llm"], 0.3)
    assert np.isclose(route["blend_weights"]["nn"], 0.7)
