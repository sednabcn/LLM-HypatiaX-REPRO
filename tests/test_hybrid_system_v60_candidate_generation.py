"""Offline contract tests for native V60 bounded template proposals."""
from hypatiax.tools.symbolic.discovery_contracts import DiscoveryBudget, DiscoveryProblem
from hypatiax.tools.symbolic.v60_candidate_generation import generate_native_template_candidates


def _problem(*, budget=None):
    return DiscoveryProblem(
        target_name="target",
        variable_names=("x", "y", "z"),
        budget=budget or DiscoveryBudget(
            max_search_attempts=2, max_candidates=8, seed=17
        ),
    )


def test_v60_template_generation_is_deterministic_and_budget_bounded():
    first = generate_native_template_candidates(_problem())
    second = generate_native_template_candidates(_problem())

    assert [item.to_dict() for item in first] == [item.to_dict() for item in second]
    assert len(first) == 5  # three variables plus at most two binary templates
    assert all(item.source == "domain_template" for item in first)
    assert len({item.candidate_id for item in first}) == len(first)

def test_v60_template_generation_uses_only_declared_supported_unary_operators():
    problem = DiscoveryProblem(
        target_name="target",
        variable_names=("x", "y"),
        allowed_unary_operators=("sin", "sqrt", "unknown"),
        allowed_binary_operators=("+",),
        budget=DiscoveryBudget(max_search_attempts=3, max_candidates=10, seed=17),
    )

    proposals = generate_native_template_candidates(problem)
    assert [item.expression for item in proposals] == [
        "x", "y", "sin(x)", "sqrt(x)", "sin(y)",
    ]


def test_v60_unary_templates_obey_candidate_cap_and_attempt_budget():
    problem = DiscoveryProblem(
        target_name="target",
        variable_names=("x", "y"),
        allowed_unary_operators=("exp", "log"),
        budget=DiscoveryBudget(max_search_attempts=1, max_candidates=3, seed=17),
    )

    proposals = generate_native_template_candidates(problem)
    assert [item.expression for item in proposals] == ["x", "y", "exp(x)"]


def test_v60_template_generation_composes_declared_unary_and_binary_operators():
    problem = DiscoveryProblem(
        target_name="target",
        variable_names=("x", "y"),
        allowed_unary_operators=("sin",),
        allowed_binary_operators=("+",),
        budget=DiscoveryBudget(max_search_attempts=4, max_candidates=10, seed=17),
    )

    proposals = generate_native_template_candidates(problem)
    assert [item.expression for item in proposals] == [
        "x", "y", "sin(x)", "sin(y)", "(x + y)", "sin((x + y))",
    ]


def test_v60_template_generation_emits_square_only_when_power_is_declared():
    problem = DiscoveryProblem(
        target_name="target",
        variable_names=("x", "y"),
        allowed_binary_operators=("**",),
        budget=DiscoveryBudget(max_search_attempts=2, max_candidates=10, seed=17),
    )

    proposals = generate_native_template_candidates(problem)
    assert [item.expression for item in proposals] == [
        "x", "y", "(x ** 2)", "(y ** 2)",
    ]


def test_v60_template_generation_respects_zero_candidate_budget():
    problem = _problem(budget=DiscoveryBudget(
        max_search_attempts=10, max_candidates=0, seed=17
    ))

    assert generate_native_template_candidates(problem) == ()


def test_v60_template_generation_does_not_invent_unsupported_operators():
    problem = DiscoveryProblem(
        target_name="target",
        variable_names=("x", "y"),
        allowed_binary_operators=("^", "unknown"),
        budget=DiscoveryBudget(max_search_attempts=10, max_candidates=10),
    )

    proposals = generate_native_template_candidates(problem)
    assert [item.expression for item in proposals] == ["x", "y"]
