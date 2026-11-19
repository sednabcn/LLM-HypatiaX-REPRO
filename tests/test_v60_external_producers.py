"""Offline tests for bounded external V60 proposal ingestion."""
import pytest

from hypatiax.tools.symbolic.discovery_contracts import DiscoveryBudget, DiscoveryProblem
from hypatiax.tools.symbolic.v60_external_producers import ingest_external_candidate_proposals


def _problem():
    return DiscoveryProblem(
        target_name="y",
        variable_names=("x",),
        budget=DiscoveryBudget(
            max_search_attempts=4,
            max_candidates=3,
            max_llm_calls=1,
            max_llm_tokens=100,
            seed=11,
        ),
    )


def test_ingests_llm_and_pysr_outputs_with_source_lineage():
    result = ingest_external_candidate_proposals(
        _problem(),
        llm_proposals=[{"expression": "x**2", "search_strategy": "prompted", "seed": 2}],
        pysr_proposals=[{"expression": "x**3", "search_strategy": "pysr", "seed": 3}],
        llm_call_count=1,
        llm_token_count=50,
        pysr_search_attempt_count=2,
    )
    assert result["producer_calls_performed"] is False
    assert [item["source"] for item in result["proposals"]] == ["llm_proposal", "pysr_search"]


def test_rejects_usage_over_declared_budgets():
    with pytest.raises(ValueError, match="max_llm_calls"):
        ingest_external_candidate_proposals(_problem(), llm_call_count=2)


def test_rejects_misattributed_producer_source():
    result = ingest_external_candidate_proposals(
        _problem(),
        llm_proposals=[{"expression": "x", "source": "pysr_search"}],
    )
    assert result["accepted_proposal_count"] == 0
    assert "source" in result["rejected_proposals"][0]["reason"]


def test_llm_candidate_volume_uses_candidate_budget_not_search_attempt_budget():
    problem = DiscoveryProblem(
        target_name="target",
        variable_names=("x",),
        budget=DiscoveryBudget(
            max_search_attempts=1, max_candidates=4, max_llm_calls=1
        ),
    )
    proposals = [
        {"expression": f"x + {index}", "source": "llm_proposal"}
        for index in range(4)
    ]

    audit = ingest_external_candidate_proposals(
        problem, llm_proposals=proposals, llm_call_count=1
    )
    assert audit["accepted_proposal_count"] == 4
    assert audit["budget_truncated_count"] == 0


def test_combined_external_pool_is_bounded():
    result = ingest_external_candidate_proposals(
        _problem(),
        llm_proposals=[{"expression": f"x+{i}"} for i in range(5)],
        llm_call_count=1,
        llm_token_count=10,
    )
    assert result["accepted_proposal_count"] == 3
    assert result["budget_truncated_count"] == 2
