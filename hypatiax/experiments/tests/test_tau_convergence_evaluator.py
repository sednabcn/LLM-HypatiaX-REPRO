import math

import pytest

from scripts.evaluate_tau_convergence import (
    APPROVED,
    _binomial_lower_tail,
    evaluate,
    exact_bad_route_test,
    select_threshold,
)


def _payload(n=59, *, deltas=None, bad_indices=()):
    deltas = deltas or [0.05] * n
    return {
        "approved_protocol": dict(APPROVED),
        "candidate_tau_values": [0.05, 0.10],
        "category_list": ["continuous_bivariate"],
        "records": [
            {
                "equation_id": f"eq-{i:03d}",
                "independent_unit_id": f"family-{i:03d}",
                "category": "continuous_bivariate",
                "llm_eligible": True,
                "delta_llm": deltas[i],
                # This label must come from the frozen edge/ensemble evaluator.
                "bad_route": i in set(bad_indices),
                "status": "scored",
            }
            for i in range(n)
        ],
    }


def test_exact_zero_failure_minimum_is_59():
    assert _binomial_lower_tail(0, 59, 0.05) <= 0.05
    assert _binomial_lower_tail(0, 58, 0.05) > 0.05
    assert exact_bad_route_test(0, 59, 0.05, 0.05)["certified"] is True


def test_one_bad_route_is_not_certified_at_59_units():
    result = exact_bad_route_test(1, 59, 0.05, 0.05)
    assert result["certified"] is False
    assert result["reason"] == "risk_not_certified"


def test_fixed_sequence_stops_at_first_uncertified_candidate():
    rows = [
        {
            "independent_unit_id": f"f{i}",
            "llm_eligible": True,
            "delta_llm": 0.10 if i == 0 else 0.01,
            "bad_route": i == 0,
        }
        for i in range(59)
    ]
    result = select_threshold(rows, [0.05, 0.10], 0.05, 0.05)
    assert result["selected_tau"] == 0.05
    assert len(result["candidate_trace"]) == 2
    assert result["candidate_trace"][0]["certified"] is True
    assert result["candidate_trace"][1]["certified"] is False


def test_evaluator_certifies_threshold_but_does_not_claim_generalization():
    result = evaluate(_payload(), bootstrap_replicates=30, seed=7)
    category = result["categories"]["continuous_bivariate"]
    assert result["status"] == "calibration_converged_on_calibration_data"
    assert result["generalization_claim"] is False
    assert category["selected_tau"] == 0.10
    assert category["bootstrap_stability"]["available"] is True
    assert category["local_decision_sensitivity"]["decision_stability"] == "measured"


def test_underpowered_category_fails_closed_without_threshold():
    result = evaluate(_payload(n=58), bootstrap_replicates=0)
    category = result["categories"]["continuous_bivariate"]
    assert result["status"] == "not_converged_or_insufficient_evidence"
    assert category["selection_status"] == "insufficient_evidence"
    assert category["selected_tau"] is None


def test_invalid_protocol_constants_are_rejected():
    payload = _payload()
    payload["approved_protocol"]["edge_r2_floor"] = 0.95
    with pytest.raises(ValueError, match="approved_protocol.edge_r2_floor"):
        evaluate(payload, bootstrap_replicates=0)


def test_duplicate_independent_unit_is_rejected():
    payload = _payload()
    payload["records"][1]["independent_unit_id"] = payload["records"][0]["independent_unit_id"]
    with pytest.raises(ValueError, match="independent unit reused"):
        evaluate(payload, bootstrap_replicates=0)


def test_nonfinite_degradation_is_rejected():
    payload = _payload()
    payload["records"][0]["delta_llm"] = math.nan
    with pytest.raises(ValueError, match="delta_llm must be finite"):
        evaluate(payload, bootstrap_replicates=0)


def test_bad_route_label_required_for_eligible_records():
    payload = _payload()
    payload["records"][0]["bad_route"] = None
    with pytest.raises(ValueError, match="bad_route must be boolean"):
        evaluate(payload, bootstrap_replicates=0)
