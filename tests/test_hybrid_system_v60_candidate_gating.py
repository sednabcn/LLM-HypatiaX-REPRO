"""Offline regression coverage for native V60 declared scientific gates."""
from hypatiax.tools.symbolic.discovery_contracts import ConstraintSpec, DiscoveryProblem
from hypatiax.tools.symbolic.v60_candidate_gating import validate_native_candidate_pool


def _candidate(expression, candidate_id):
    return {
        "candidate_id": candidate_id,
        "expression": expression,
        "normalized_expression": expression,
        "producer_provenance": [{
            "source": "domain_template", "search_strategy": "bounded_template", "seed": 7,
        }],
    }


def test_hard_declared_constraint_blocks_candidate_and_records_lineage():
    problem = DiscoveryProblem(
        target_name="energy", variable_names=("x",),
        variable_domains={"x": {"minimum": -2.0, "maximum": 2.0}},
        constraints=(ConstraintSpec("positive", "positive_output", severity="hard"),),
    )
    result = validate_native_candidate_pool([_candidate("x**2", "cand-1")], problem)
    record = result["candidate_gates"][0]
    assert result["eligible_candidate_count"] == 0
    assert record["native_candidate_id"] == "cand-1"
    assert record["constraint_outcomes"][-1]["status"] == "fail"
    assert record["producer_provenance"][0]["seed"] == 7


def test_unknown_hard_constraint_fails_closed_but_soft_failure_is_audited():
    problem = DiscoveryProblem(
        target_name="response", variable_names=("x",),
        variable_domains={"x": {"minimum": -1.0, "maximum": 1.0}},
        constraints=(
            ConstraintSpec("unknown-hard", "not_a_supported_gate", severity="hard"),
            ConstraintSpec("soft-positive", "positive_output", severity="soft"),
        ),
    )
    result = validate_native_candidate_pool([_candidate("x", "cand-2")], problem)
    record = result["candidate_gates"][0]
    assert record["eligible"] is False
    assert result["unknown_hard_outcome_count"] == 1
    assert result["soft_failure_outcome_count"] == 1
    assert result["selection_performed"] is False


def test_no_declared_constraints_does_not_infer_physics():
    problem = DiscoveryProblem(target_name="response", variable_names=("x",))
    result = validate_native_candidate_pool([_candidate("x", "cand-3")], problem)
    record = result["candidate_gates"][0]
    assert record["eligible"] is True
    assert record["constraint_outcomes"][-1]["status"] == "not_applicable"
    assert result["training_or_far_data_used"] is False
