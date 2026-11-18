"""Native V60 declared scientific gates for normalized symbolic candidates.

Uses the shared CandidateValidator contract implementation. Gate evaluation
uses only the immutable problem declaration and candidate expression; it
does not inspect training targets, validation folds, or far/evaluation data.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from hypatiax.tools.symbolic.discovery_contracts import DiscoveryProblem
from hypatiax.tools.symbolic.discovery_validation import CandidateValidator


def validate_native_candidate_pool(
    candidates: Sequence[Mapping[str, Any]],
    problem: DiscoveryProblem,
    *,
    validator: CandidateValidator | None = None,
) -> dict[str, Any]:
    """Apply hard/soft declared gates and retain per-candidate audit evidence.

    Unknown hard constraints remain blocking through CandidateValidator.
    Soft failures are recorded but do not make a candidate ineligible.
    This function deliberately performs no candidate ranking or selection.
    """
    if not isinstance(problem, DiscoveryProblem):
        raise TypeError("problem must be a DiscoveryProblem")
    gate = validator or CandidateValidator()
    records: list[dict[str, Any]] = []
    failed_count = 0
    eligible_count = 0
    unknown_hard_count = 0
    soft_failure_count = 0
    for item in candidates:
        candidate_id = item.get("candidate_id")
        expression = item.get("normalized_expression") or item.get("expression")
        lineage = item.get("producer_provenance", [])
        producer = lineage[0] if isinstance(lineage, (list, tuple)) and lineage else {}
        source = producer.get("source", "unknown") if isinstance(producer, Mapping) else "unknown"
        strategy = producer.get("search_strategy", "v60_native_template") if isinstance(producer, Mapping) else "v60_native_template"
        seed = producer.get("seed", problem.budget.seed) if isinstance(producer, Mapping) else problem.budget.seed
        if source not in {"llm_proposal", "domain_template", "pysr_search", "residual_search", "unknown"}:
            source = "unknown"
        if not isinstance(strategy, str) or not strategy.strip():
            strategy = "v60_native_template"
        if isinstance(seed, bool) or not isinstance(seed, int):
            seed = problem.budget.seed
        try:
            result = gate.validate(
                problem, expression, source=source, search_strategy=strategy, seed=seed,
            )
            record = result.to_dict()
            record["native_candidate_id"] = candidate_id
            record["producer_provenance"] = [dict(entry) for entry in lineage if isinstance(entry, Mapping)]
            record["gate_execution"] = "completed"
        except Exception as exc:
            record = {
                "native_candidate_id": candidate_id,
                "expression": expression,
                "eligible": False,
                "constraint_outcomes": [],
                "rejection_reasons": [f"{type(exc).__name__}: {exc}"],
                "producer_provenance": [dict(entry) for entry in lineage if isinstance(entry, Mapping)],
                "gate_execution": "failed",
            }
        eligible = bool(record.get("eligible", False))
        eligible_count += int(eligible)
        failed_count += int(not eligible)
        for outcome in record.get("constraint_outcomes", []):
            if not isinstance(outcome, Mapping):
                continue
            if outcome.get("severity") == "hard" and outcome.get("status") in {"unknown", "not_checked"}:
                unknown_hard_count += 1
            if outcome.get("severity") == "soft" and outcome.get("status") == "fail":
                soft_failure_count += 1
        records.append(record)
    return {
        "schema": "v60_native_scientific_gates_v1",
        "gate_status": "completed",
        "candidate_count": len(candidates),
        "eligible_candidate_count": eligible_count,
        "ineligible_candidate_count": failed_count,
        "unknown_hard_outcome_count": unknown_hard_count,
        "soft_failure_outcome_count": soft_failure_count,
        "selection_performed": False,
        "training_or_far_data_used": False,
        "candidate_gates": records,
    }


__all__ = ["validate_native_candidate_pool"]
