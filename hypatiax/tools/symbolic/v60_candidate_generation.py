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
from hypatiax.tools.validation.safe_sympy_parser import ALLOWED_UNARY_FUNCTIONS


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
    if limit is not None:
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be a non-negative integer")
        if limit < 0:
            raise ValueError("limit must be a non-negative integer")
    cap = budget.max_candidates if limit is None else min(budget.max_candidates, limit)
    if cap == 0 or budget.max_search_attempts == 0:
        return ()

    names = problem.variable_names
    if any(not re.fullmatch(r"[A-Za-z_]\w*", name) for name in names):
        # The restricted expression grammar uses identifiers; do not guess a
        # lossy sanitization or create a candidate with changed semantics.
        return ()

    binary = problem.allowed_binary_operators or ("+", "-", "*", "/")
    allowed_binary = tuple(dict.fromkeys(op for op in binary if op in {"+", "-", "*", "/"}))
    allow_square = "**" in binary
    # Keep generated calls inside the same explicit function allowlist as the
    # restricted AST parser. Unknown contract operators are never guessed.
    allowed_unary = tuple(dict.fromkeys(
        op for op in problem.allowed_unary_operators if op in ALLOWED_UNARY_FUNCTIONS
    ))
    proposals: list[str] = list(names)
    attempts = 0

    # Unary templates are generated only when explicitly declared by the
    # scientific contract; the attempt and candidate caps apply to each one.
    for name in names:
        for op in allowed_unary:
            if attempts >= budget.max_search_attempts or len(proposals) >= cap:
                break
            attempts += 1
            proposals.append(f"{op}({name})")
        if attempts >= budget.max_search_attempts or len(proposals) >= cap:
            break

    if allow_square:
        for name in names:
            if attempts >= budget.max_search_attempts or len(proposals) >= cap:
                break
            attempts += 1
            proposals.append(f"({name} ** 2)")

    # Multiplication also permits a variable's self-product. Prefer the
    # explicit square form when exponentiation was declared as well.
    if "*" in problem.allowed_binary_operators and not allow_square:
        for name in names:
            if attempts >= budget.max_search_attempts or len(proposals) >= cap:
                break
            attempts += 1
            proposals.append(f"({name} * {name})")

    # Compose pairwise operators over the admitted one-level basis terms,
    # not just raw variables. This enables forms such as sin(x) + y while
    # keeping recursion bounded to one composition layer.
    base_terms = tuple(dict.fromkeys(proposals))
    for i, left in enumerate(base_terms):
        for right in base_terms[i + 1:]:
            for op in allowed_binary:
                if attempts >= budget.max_search_attempts or len(proposals) >= cap:
                    break
                attempts += 1
                binary_expression = f"({left} {op} {right})"
                proposals.append(binary_expression)
                for unary_op in allowed_unary:
                    if attempts >= budget.max_search_attempts or len(proposals) >= cap:
                        break
                    attempts += 1
                    proposals.append(f"{unary_op}({binary_expression})")
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
