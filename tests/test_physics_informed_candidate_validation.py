"""Regression tests for explicit physics-informed candidate gates."""
import pytest

from hypatiax.tools.symbolic.discovery_contracts import (
    ConstraintSpec,
    DiscoveryProblem,
)
from hypatiax.tools.symbolic.discovery_validation import CandidateValidator


def test_declared_nonnegative_constraint_passes_and_is_audited():
    problem = DiscoveryProblem(
        target_name="energy",
        variable_names=("x",),
        variable_domains={"x": {"minimum": -2, "maximum": 2}},
        constraints=(
            ConstraintSpec(
                constraint_id="energy-nonnegative",
                kind="nonnegative_output",
                severity="hard",
            ),
        ),
    )

    candidate = CandidateValidator().validate(problem, "x**2")

    assert candidate.eligible is True
    assert candidate.constraint_outcomes[-1].constraint_id == "energy-nonnegative"
    assert candidate.constraint_outcomes[-1].status == "pass"


def test_declared_positive_constraint_rejects_zero_boundary():
    problem = DiscoveryProblem(
        target_name="energy",
        variable_names=("x",),
        variable_domains={"x": {"minimum": -2, "maximum": 2}},
        constraints=(
            ConstraintSpec(
                constraint_id="strict-positive",
                kind="positive_output",
                severity="hard",
            ),
        ),
    )

    candidate = CandidateValidator().validate(problem, "x**2")

    assert candidate.eligible is False
    assert any("strict-positive" in reason for reason in candidate.rejection_reasons)


def test_unknown_hard_constraint_blocks_candidate_instead_of_failing_open():
    problem = DiscoveryProblem(
        target_name="force",
        variable_names=("x", "m"),
        variable_domains={"x": {"minimum": 0, "maximum": 1}},
        constraints=(
            ConstraintSpec(
                constraint_id="positive-output",
                kind="positive_output",
                severity="hard",
            ),
        ),
    )

    candidate = CandidateValidator().validate(problem, "x*m")

    assert candidate.eligible is False
    assert candidate.constraint_outcomes[-1].status == "unknown"


def test_untrusted_expression_is_rejected_by_restricted_parser():
    problem = DiscoveryProblem(target_name="y", variable_names=("x",))

    candidate = CandidateValidator().validate(
        problem, "__import__('os').system('echo unsafe')"
    )

    assert candidate.eligible is False
    assert candidate.constraint_outcomes[0].status == "fail"



def test_candidate_validator_expands_engineered_features_to_declared_raw_variables():
    problem = DiscoveryProblem(
        target_name="amplitude",
        variable_names=("a", "b"),
        variable_domains={
            "a": {"minimum": 1.0, "maximum": 5.0},
            "b": {"minimum": 2.0, "maximum": 8.0},
        },
        constraints=(
            ConstraintSpec(
                constraint_id="amplitude-nonnegative",
                kind="nonnegative_output",
                severity="hard",
            ),
        ),
    )

    candidate = CandidateValidator().validate(
        problem,
        "1.0*gm_a_b",
        candidate_variable_names=("a", "b", "gm_a_b"),
        feature_substitutions={
            "a": "a",
            "b": "b",
            "gm_a_b": "sqrt(a*b)",
        },
    )

    assert candidate.eligible is True
    assert "sqrt" in candidate.expression
    assert candidate.constraint_outcomes[-1].status == "pass"


def test_candidate_validator_supports_expanded_fold_log_transform_safely():
    problem = DiscoveryProblem(
        target_name="response",
        variable_names=("x",),
        variable_domains={"x": {"minimum": -5.0, "maximum": 5.0}},
        constraints=(
            ConstraintSpec(
                constraint_id="finite-response",
                kind="finite_output",
                severity="hard",
            ),
        ),
    )

    candidate = CandidateValidator().validate(
        problem,
        "u",
        candidate_variable_names=("u",),
        feature_substitutions={
            "u": "sign(x)*log10(abs(x)+1)",
        },
    )

    assert candidate.eligible is True
    assert "sign" in candidate.expression
    assert candidate.constraint_outcomes[-1].status == "pass"
