import numpy as np

from hypatiax.core.routing import select_hypatiax_route, structural_risk_tokens


def test_detects_exact_transcendental_calls_not_substrings():
    assert structural_risk_tokens("def formula(x):\n    return np.exp(x) + math.erf(x)") == ["erf", "exp"]
    assert structural_risk_tokens("def formula(exponential_rate):\n    return exponential_rate + 1") == []


def test_structural_risk_overrides_high_fit_pure_llm_route():
    llm = np.array([1.0, 2.0, 3.0])
    nn = np.array([1.1, 1.9, 3.1])
    route = select_hypatiax_route(0.99, 0.80, llm, nn, ["exp"])
    assert route["decision"] == "ensemble"
    assert route["route_reason"] == "structural_risk_precedence"
    assert route["structural_risk_flag"] is True
    assert np.isclose(route["blend_weights"]["llm"] + route["blend_weights"]["nn"], 1.0)


def test_high_fit_without_structural_risk_can_use_pure_llm():
    route = select_hypatiax_route(0.99, 0.80, np.ones(3), np.zeros(3), [])
    assert route["decision"] == "fitted_llm"
    assert route["route_reason"] == "trusted_high_fit_no_structural_risk"


def test_failed_trust_gate_routes_to_nn():
    route = select_hypatiax_route(0.49, 0.90, np.ones(3), np.zeros(3), ["sin"])
    assert route["decision"] == "nn"
    assert route["route_reason"] == "trust_gate_failed"
    assert route["trust_gate_passed"] is False


def test_formula_fragment_fallback_detects_function_calls():
    assert structural_risk_tokens("exp(x") == ["exp"]
