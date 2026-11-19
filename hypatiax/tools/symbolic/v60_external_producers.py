"""Budget-enforced ingestion boundary for externally produced V60 proposals.

This module never calls an LLM or PySR. Integrators pass completed proposal
records and usage counters explicitly; this layer validates provenance and
resource accounting before the common normalization/gating pipeline.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from hypatiax.tools.symbolic.discovery_contracts import DiscoveryProblem

_ALLOWED_SOURCES = {"llm_proposal", "pysr_search"}


def ingest_external_candidate_proposals(
    problem: DiscoveryProblem,
    *,
    llm_proposals: Sequence[Mapping[str, Any]] = (),
    pysr_proposals: Sequence[Mapping[str, Any]] = (),
    llm_call_count: int = 0,
    llm_token_count: int = 0,
    pysr_search_attempt_count: int = 0,
) -> dict[str, Any]:
    """Validate injected producer output and enforce declared budgets.

    Counts describe work already performed by the caller; this function does
    not make provider calls and cannot refund or conceal upstream usage.
    """
    if not isinstance(problem, DiscoveryProblem):
        raise TypeError("problem must be a DiscoveryProblem")
    for name, value in (
        ("llm_call_count", llm_call_count),
        ("llm_token_count", llm_token_count),
        ("pysr_search_attempt_count", pysr_search_attempt_count),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    budget = problem.budget
    if llm_call_count > budget.max_llm_calls:
        raise ValueError("LLM call usage exceeds max_llm_calls")
    if budget.max_llm_tokens is not None and llm_token_count > budget.max_llm_tokens:
        raise ValueError("LLM token usage exceeds max_llm_tokens")
    if pysr_search_attempt_count > budget.max_search_attempts:
        raise ValueError("PySR search usage exceeds max_search_attempts")
    if not isinstance(llm_proposals, Sequence) or isinstance(llm_proposals, (str, bytes)):
        raise TypeError("llm_proposals must be a sequence of proposal mappings")
    if not isinstance(pysr_proposals, Sequence) or isinstance(pysr_proposals, (str, bytes)):
        raise TypeError("pysr_proposals must be a sequence of proposal mappings")

    combined = []
    rejected = []
    for source, proposals in (("llm_proposal", llm_proposals), ("pysr_search", pysr_proposals)):
        for index, proposal in enumerate(proposals):
            try:
                if not isinstance(proposal, Mapping):
                    raise TypeError("proposal must be a mapping")
                expression = proposal.get("expression")
                if not isinstance(expression, str) or not expression.strip():
                    raise ValueError("proposal expression must be a non-empty string")
                strategy = proposal.get("search_strategy", source)
                if not isinstance(strategy, str) or not strategy.strip():
                    raise ValueError("search_strategy must be a non-empty string")
                seed = proposal.get("seed", budget.seed)
                if isinstance(seed, bool) or not isinstance(seed, int):
                    raise ValueError("seed must be an integer")
                supplied_source = proposal.get("source", source)
                if supplied_source != source or supplied_source not in _ALLOWED_SOURCES:
                    raise ValueError("proposal source does not match its producer channel")
                combined.append({
                    "candidate_id": proposal.get("candidate_id"),
                    "expression": expression,
                    "source": source,
                    "search_strategy": strategy,
                    "seed": seed,
                })
            except Exception as exc:
                rejected.append({
                    "source": source,
                    "proposal_index": index,
                    "reason": f"{type(exc).__name__}: {exc}",
                })

    cap = min(budget.max_candidates, budget.max_search_attempts)
    accepted = combined[:cap]
    return {
        "schema": "v60_external_producer_ingestion_v1",
        "producer_calls_performed": False,
        "llm_usage": {
            "call_count": llm_call_count,
            "token_count": llm_token_count,
            "call_budget": budget.max_llm_calls,
            "token_budget": budget.max_llm_tokens,
        },
        "pysr_usage": {
            "search_attempt_count": pysr_search_attempt_count,
            "search_attempt_budget": budget.max_search_attempts,
        },
        "input_proposal_count": len(combined),
        "accepted_proposal_count": len(accepted),
        "budget_truncated_count": len(combined) - len(accepted),
        "rejected_proposals": rejected,
        "proposals": accepted,
    }


__all__ = ["ingest_external_candidate_proposals"]
