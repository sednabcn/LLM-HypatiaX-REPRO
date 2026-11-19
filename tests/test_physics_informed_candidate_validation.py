"""Regression tests for explicit physics-informed candidate gates."""
import pytest

from hypatiax.tools.symbolic.discovery_contracts import (
    ConstraintSpec,
    DiscoveryProblem,
)
from hypatiax.tools.symbolic.discovery_validation import CandidateValidator


def test_declared_nonnegative_sample_pass_does_not_claim_continuous_proof():
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

    assert candidate.eligible is False
    assert candidate.constraint_outcomes[-1].constraint_id == "energy-nonnegative"
    assert candidate.constraint_outcomes[-1].status == "unknown"
    assert candidate.constraint_outcomes[-1].evidence["sampled_screening_status"] == "pass"
    assert candidate.constraint_outcomes[-1].evidence["continuous_domain_proof_established"] is False
    assert candidate.constraint_outcomes[-1].evidence["proof_scope"] == "finite_sample_screening_only_not_continuous_domain_proof"


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

    assert candidate.eligible is False
    assert "sqrt" in candidate.expression
    assert candidate.constraint_outcomes[-1].status == "unknown"
    assert candidate.constraint_outcomes[-1].evidence["sampled_screening_status"] == "pass"


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

    assert candidate.eligible is False
    assert "sign" in candidate.expression
    assert candidate.constraint_outcomes[-1].status == "unknown"
    assert candidate.constraint_outcomes[-1].evidence["sampled_screening_status"] == "pass"


def test_soft_constraint_reports_quantitative_violation_fraction_without_rejecting():
    problem = DiscoveryProblem(
        target_name="response",
        variable_names=("x",),
        variable_domains={"x": {"minimum": -1.0, "maximum": 1.0}},
        constraints=(
            ConstraintSpec(
                constraint_id="soft-positive-output",
                kind="positive_output",
                severity="soft",
            ),
        ),
    )

    candidate = CandidateValidator().validate(problem, "x")

    outcome = candidate.constraint_outcomes[-1]
    assert candidate.eligible is True
    assert outcome.status == "fail"
    assert outcome.evidence["evaluation_count"] == 3
    assert outcome.evidence["violation_count"] == 2
    assert outcome.evidence["violation_fraction"] == pytest.approx(2.0 / 3.0)


def test_symmetry_constraint_reports_fraction_of_failed_mirrored_pairs():
    problem = DiscoveryProblem(
        target_name="response",
        variable_names=("x",),
        variable_domains={"x": {"minimum": -2.0, "maximum": 2.0}},
        constraints=(
            ConstraintSpec(
                constraint_id="soft-odd-symmetry",
                kind="odd_in",
                severity="soft",
                parameters={"variable": "x"},
            ),
        ),
    )

    candidate = CandidateValidator().validate(problem, "x**2")

    outcome = candidate.constraint_outcomes[-1]
    assert candidate.eligible is True
    assert outcome.status == "fail"
    assert outcome.evidence["evaluation_count"] == 3
    assert outcome.evidence["violation_count"] == 2
    assert outcome.evidence["violation_fraction"] == pytest.approx(2.0 / 3.0)


def test_finite_output_violation_count_includes_nonfinite_samples():
    problem = DiscoveryProblem(
        target_name="response",
        variable_names=("x",),
        variable_domains={"x": {"minimum": -1.0, "maximum": 1.0}},
        constraints=(
            ConstraintSpec(
                constraint_id="finite-output",
                kind="finite_output",
                severity="soft",
            ),
        ),
    )

    candidate = CandidateValidator().validate(problem, "1/x")

    outcome = candidate.constraint_outcomes[-1]
    assert outcome.evidence["evaluation_count"] == 3
    assert outcome.evidence["violation_count"] == 1
    assert outcome.evidence["violation_fraction"] == pytest.approx(1.0 / 3.0)


def test_soft_constraint_sample_pass_is_reported_as_unknown_not_proof():
    problem = DiscoveryProblem(
        target_name="energy",
        variable_names=("x",),
        variable_domains={"x": {"minimum": -2, "maximum": 2}},
        constraints=(
            ConstraintSpec(
                constraint_id="soft-nonnegative",
                kind="nonnegative_output",
                severity="soft",
            ),
        ),
    )
    candidate = CandidateValidator().validate(problem, "x**2")
    outcome = candidate.constraint_outcomes[-1]
    assert candidate.eligible is True
    assert outcome.status == "unknown"
    assert outcome.evidence["sampled_screening_status"] == "pass"
    assert outcome.evidence["grid_is_exhaustive"] is True
    assert outcome.evidence["continuous_domain_proof_established"] is False
