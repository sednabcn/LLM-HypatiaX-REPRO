"""Offline regression coverage for native V60 candidate normalization."""
from hypatiax.tools.symbolic.v60_candidate_generation import CandidateProposal
from hypatiax.tools.symbolic.v60_candidate_normalization import normalize_candidate_proposals


def _proposal(expression, source="domain_template", seed=7, strategy="templates"):
    return CandidateProposal(
        candidate_id=f"producer-{seed}-{expression}",
        expression=expression,
        source=source,
        strategy=strategy,
        seed=seed,
    )


def test_normalization_deduplicates_equivalent_expressions_and_preserves_lineage():
    result = normalize_candidate_proposals(
        [
            _proposal("x + y", seed=7),
            _proposal("y+x", source="llm_proposal", seed=11, strategy="llm"),
            _proposal("x * y"),
        ],
        variable_names=("x", "y"),
        max_candidates=10,
    )

    assert len(result.candidates) == 2
    equivalent = next(item for item in result.candidates if item.normalized_expression == "x + y")
    assert len(equivalent.producer_provenance) == 2
    assert {item["source"] for item in equivalent.producer_provenance} == {
        "domain_template", "llm_proposal"
    }
    assert result.duplicate_proposal_count == 1
    assert result.rejected == ()


def test_normalization_rejects_undeclared_symbols_without_losing_audit():
    result = normalize_candidate_proposals(
        [_proposal("x + unknown"), _proposal("x + 1")],
        variable_names=("x",),
        max_candidates=10,
    )

    assert len(result.candidates) == 1
    assert len(result.rejected) == 1
    assert "Undeclared variable" in result.rejected[0]["reason"]


def test_normalization_budget_caps_input_processing_and_reports_truncation():
    result = normalize_candidate_proposals(
        [_proposal("x"), _proposal("x + 1"), _proposal("x + 2")],
        variable_names=("x",),
        max_candidates=2,
    )

    assert result.processed_count == 2
    assert result.budget_truncated_count == 1
    assert len(result.candidates) == 2


def test_candidate_identity_is_independent_of_producer_metadata():
    left = normalize_candidate_proposals(
        [_proposal("x+y", source="domain_template", seed=1)],
        variable_names=("x", "y"),
        max_candidates=2,
    ).candidates[0]
    right = normalize_candidate_proposals(
        [_proposal("y + x", source="llm_proposal", seed=99)],
        variable_names=("x", "y"),
        max_candidates=2,
    ).candidates[0]

    assert left.candidate_id == right.candidate_id
