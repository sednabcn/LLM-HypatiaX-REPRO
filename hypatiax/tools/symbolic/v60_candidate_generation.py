"""Native, bounded V60 candidate proposal generation.

This stage is deliberately data-independent: it receives the immutable problem
contract and emits deterministic structural templates. It never reads targets,
far/evaluation data, credentials, or external services. LLM/PySR adapters are
left for later stages and are not invoked here.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Any

from .discovery_contracts import DiscoveryProblem


@dataclass(frozen=True)
class CandidateProposal:
    candidate_id: str
    expression: str
    source: str
    strategy: str
    seed: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "expression": self.expression,
            "source": self.source,
            "search_strategy": self.strategy,
            "seed": self.seed,
        }


def generate_native_template_candidates(
    problem: DiscoveryProblem, *, limit: int | None = None
) -> tuple[CandidateProposal, ...]:
    """Generate a deterministic, strictly bounded set of algebraic templates."""
    if not isinstance(problem, DiscoveryProblem):
        raise TypeError("problem must be a DiscoveryProblem")
    budget = problem.budget
    cap = budget.max_candidates if limit is None else min(
        budget.max_candidates, max(0, int(limit))
    )
    if cap == 0 or budget.max_search_attempts == 0:
        return ()

    names = problem.variable_names
    if any(not re.fullmatch(r"[A-Za-z_]\w*", name) for name in names):
        # The restricted expression grammar uses identifiers; do not guess a
        # lossy sanitization or create a candidate with changed semantics.
        return ()

    binary = problem.allowed_binary_operators or ("+", "-", "*", "/")
    allowed = tuple(op for op in binary if op in {"+", "-", "*", "/"})
    proposals: list[str] = list(names)
    attempts = 0
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            for op in allowed:
                if attempts >= budget.max_search_attempts or len(proposals) >= cap:
                    break
                attempts += 1
                proposals.append(f"({left} {op} {right})")
            if attempts >= budget.max_search_attempts or len(proposals) >= cap:
                break
        if attempts >= budget.max_search_attempts or len(proposals) >= cap:
            break

    output = []
    seen = set()
    for expression in proposals[:cap]:
        normalized = re.sub(r"\s+", "", expression)
        if normalized in seen:
            continue
        seen.add(normalized)
        identity = {
            "expression": normalized,
            "source": "domain_template",
            "strategy": "v60_bounded_algebraic_templates",
            "seed": int(budget.seed),
        }
        candidate_id = sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:20]
        output.append(CandidateProposal(
            candidate_id=candidate_id,
            expression=expression,
            source="domain_template",
            strategy="v60_bounded_algebraic_templates",
            seed=int(budget.seed),
        ))
        if len(output) >= cap:
            break
    return tuple(output)
