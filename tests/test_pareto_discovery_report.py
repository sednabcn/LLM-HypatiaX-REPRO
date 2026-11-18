"""Regression tests for training-only Pareto report selection."""
from hypatiax.tools.symbolic.discovery_contracts import (
    CandidateRecord,
    ConstraintOutcome,
)
from hypatiax.tools.symbolic.pareto_discovery import (
    select_pareto_discovery_report,
)


def _candidate(expression, seed, scores, *, eligible=True, outcomes=()):
    return CandidateRecord(
        expression=expression,
        source="pysr_search",
        search_strategy="test_strategy",
        seed=seed,
        constraint_outcomes=tuple(outcomes),
        metrics={
            "training_validation": {
                "fold_metrics": [
                    {"normalized_rmse": score} for score in scores
                ],
                "expression_stability": {
                    "status": "measured",
                    "dominant_fraction": 1.0,
                },
            }
        },
        eligible=eligible,
    )


def test_pareto_report_retains_tradeoffs_and_excludes_dominated_candidate():
    accurate_complex = _candidate("x**2", 1, [0.1, 0.5])
    balanced_simple = _candidate("x", 2, [0.2, 0.3])
    dominated = _candidate("x", 3, [0.4, 0.6])

    report = select_pareto_discovery_report(
        [accurate_complex, balanced_simple, dominated],
        variable_names=["x"],
    )

    assert report.status == "accepted"
    assert set(report.pareto_candidate_ids) == {
        accurate_complex.candidate_id,
        balanced_simple.candidate_id,
    }
    assert dominated.candidate_id not in report.pareto_candidate_ids
    assert report.selected_candidate_id in report.pareto_candidate_ids
    assert report.to_dict()["far_evaluation_used_for_selection"] is False


def test_unknown_hard_gate_blocks_candidate_even_if_marked_eligible():
    unknown = ConstraintOutcome(
        constraint_id="declared_physics",
        status="unknown",
        severity="hard",
        reason="insufficient declared bounds",
    )
    candidate = _candidate("x", 1, [0.1, 0.2], eligible=True, outcomes=[unknown])

    report = select_pareto_discovery_report(
        [candidate], variable_names=["x"]
    )

    assert report.status == "all_candidates_failed_physical_gates"
    assert report.selected_candidate_id is None
    assert report.pareto_candidate_ids == ()
    selection = report.candidates[0].metrics["pareto_selection"]
    assert selection["hard_gates_passed"] is False
    assert "hard_constraint_unknown:declared_physics" in selection["eligibility_reasons"]


def test_insufficient_training_fold_evidence_fails_closed():
    candidate = _candidate("x", 1, [0.1])

    report = select_pareto_discovery_report(
        [candidate], variable_names=["x"], minimum_valid_folds=2
    )

    assert report.status == "insufficient_validation_evidence"
    assert report.selected_candidate_id is None
    assert report.pareto_candidate_ids == ()


def test_empty_candidate_set_has_explicit_status():
    report = select_pareto_discovery_report([], variable_names=["x"])
    assert report.status == "no_candidates_generated"
    assert report.selected_candidate_id is None


def test_selected_candidate_soft_warning_is_preserved_in_report_status():
    warning = ConstraintOutcome(
        constraint_id="soft_monotonicity",
        status="warning",
        severity="soft",
        reason="sampled slope changes sign",
    )
    candidate = _candidate("x", 4, [0.1, 0.2], outcomes=[warning])

    report = select_pareto_discovery_report(
        [candidate], variable_names=["x"]
    )

    assert report.status == "accepted_with_warnings"
    assert report.selected_candidate_id == candidate.candidate_id
    assert report.candidates[0].metrics["pareto_selection"]["eligibility_reasons"] == []



def test_candidate_report_explains_each_pareto_exclusion():
    insufficient = _candidate("x", 10, [0.1])
    insufficient = CandidateRecord(
        expression=insufficient.expression,
        source=insufficient.source,
        search_strategy=insufficient.search_strategy,
        seed=insufficient.seed,
        metrics=insufficient.metrics,
        eligible=True,
    )
    invalid_complexity = CandidateRecord(
        expression="not valid !!!",
        source="pysr_search",
        search_strategy="test_strategy",
        seed=11,
        metrics={"training_validation": {
            "fold_metrics": [
                {"normalized_rmse": 0.1},
                {"normalized_rmse": 0.2},
            ]
        }},
        eligible=True,
    )

    report = select_pareto_discovery_report(
        [insufficient, invalid_complexity], variable_names=["x"],
        minimum_valid_folds=2,
    )
    by_id = {item.candidate_id: item for item in report.candidates}

    insufficient_reasons = by_id[insufficient.candidate_id].metrics[
        "pareto_selection"
    ]["eligibility_reasons"]
    complexity_reasons = by_id[invalid_complexity.candidate_id].metrics[
        "pareto_selection"
    ]["eligibility_reasons"]

    assert "insufficient_valid_training_folds" in insufficient_reasons
    assert "symbolic_complexity_unavailable" in complexity_reasons
    assert all(
        item.metrics["pareto_selection"]["eligible_for_pareto"] is False
        for item in report.candidates
    )


def test_required_nested_evidence_has_explicit_exclusion_reason_and_policy():
    candidate = _candidate("x", 12, [0.1, 0.2])
    report = select_pareto_discovery_report(
        [candidate], variable_names=["x"],
        require_nested_structure_evidence=True,
    )

    selection = report.candidates[0].metrics["pareto_selection"]
    assert selection["eligible_for_pareto"] is False
    assert "required_nested_structure_evidence_not_matched" in selection[
        "eligibility_reasons"
    ]
    assert report.provenance["selection_policy"] == (
        "training_only_pareto_v2_nested_structure_gate"
    )


def test_candidate_declared_rejection_reason_is_retained_in_pareto_audit():
    rejected = CandidateRecord(
        expression="x",
        source="pysr_search",
        search_strategy="test_strategy",
        seed=13,
        metrics={"training_validation": {
            "fold_metrics": [
                {"normalized_rmse": 0.1},
                {"normalized_rmse": 0.2},
            ]
        }},
        rejection_reasons=("candidate_failed_domain_gate",),
        eligible=False,
    )
    report = select_pareto_discovery_report(
        [rejected], variable_names=["x"],
    )
    reasons = report.candidates[0].metrics["pareto_selection"]["eligibility_reasons"]
    assert "candidate_failed_domain_gate" in reasons
