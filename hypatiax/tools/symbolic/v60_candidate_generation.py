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


def generate_native_template_candidates_with_audit(
    problem: DiscoveryProblem, *, limit: int | None = None,
    search_attempt_limit: int | None = None,
) -> dict[str, Any]:
    """Generate a deterministic, strictly bounded set of algebraic templates."""
    if not isinstance(problem, DiscoveryProblem):
        raise TypeError("problem must be a DiscoveryProblem")
    budget = problem.budget
    if limit is not None:
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be a non-negative integer")
        if limit < 0:
            raise ValueError("limit must be a non-negative integer")
    if search_attempt_limit is not None:
        if isinstance(search_attempt_limit, bool) or not isinstance(search_attempt_limit, int):
            raise TypeError("search_attempt_limit must be a non-negative integer")
        if search_attempt_limit < 0:
            raise ValueError("search_attempt_limit must be a non-negative integer")
    search_cap = (
        budget.max_search_attempts if search_attempt_limit is None
        else min(budget.max_search_attempts, search_attempt_limit)
    )
    cap = budget.max_candidates if limit is None else min(budget.max_candidates, limit)
    if cap == 0 or search_cap == 0:
        return {
            "schema": "v60_native_template_generation_v1",
            "generation_status": "completed",
            "proposals": (),
            "generation_attempt_count": 0,
            "candidate_count": 0,
            "base_variable_candidate_count": len(problem.variable_names),
            "operator_candidate_count": 0,
            "duplicate_expression_count": 0,
            "search_attempt_budget": search_cap,
            "contract_search_attempt_budget": budget.max_search_attempts,
            "candidate_budget": budget.max_candidates,
            "effective_candidate_cap": cap,
            "search_attempt_budget_exhausted": search_cap == 0,
            "candidate_cap_reached": cap == 0,
            "declared_unary_operators": list(problem.allowed_unary_operators),
            "accepted_unary_operators": list(dict.fromkeys(
                op for op in problem.allowed_unary_operators if op in ALLOWED_UNARY_FUNCTIONS
            )),
            "ignored_unary_operators": [
                op for op in problem.allowed_unary_operators if op not in ALLOWED_UNARY_FUNCTIONS
            ],
            "declared_binary_operators": list(problem.allowed_binary_operators),
            "accepted_binary_operators": list(dict.fromkeys(
                op for op in (problem.allowed_binary_operators or ("+", "-", "*", "/"))
                if op in {"+", "-", "*", "/"}
            )) + (["**"] if "**" in problem.allowed_binary_operators else []),
            "ignored_binary_operators": [
                op for op in problem.allowed_binary_operators
                if op not in {"+", "-", "*", "/", "**"}
            ],
            "seed": int(budget.seed),
        }

    names = problem.variable_names
    if any(not re.fullmatch(r"[A-Za-z_]\w*", name) for name in names):
        # The restricted expression grammar uses identifiers; do not guess a
        # lossy sanitization or create a candidate with changed semantics.
        return {
            "schema": "v60_native_template_generation_v1",
            "generation_status": "no_candidates_invalid_variable_names",
            "proposals": (),
            "generation_attempt_count": 0,
            "candidate_count": 0,
            "base_variable_candidate_count": 0,
            "operator_candidate_count": 0,
            "duplicate_expression_count": 0,
            "search_attempt_budget": budget.max_search_attempts,
            "candidate_budget": budget.max_candidates,
            "effective_candidate_cap": cap,
            "search_attempt_budget_exhausted": False,
            "candidate_cap_reached": False,
            "declared_unary_operators": list(problem.allowed_unary_operators),
            "accepted_unary_operators": list(dict.fromkeys(
                op for op in problem.allowed_unary_operators if op in ALLOWED_UNARY_FUNCTIONS
            )),
            "ignored_unary_operators": [
                op for op in problem.allowed_unary_operators if op not in ALLOWED_UNARY_FUNCTIONS
            ],
            "declared_binary_operators": list(problem.allowed_binary_operators),
            "accepted_binary_operators": list(dict.fromkeys(
                op for op in (problem.allowed_binary_operators or ("+", "-", "*", "/"))
                if op in {"+", "-", "*", "/"}
            )) + (["**"] if "**" in problem.allowed_binary_operators else []),
            "ignored_binary_operators": [
                op for op in problem.allowed_binary_operators
                if op not in {"+", "-", "*", "/", "**"}
            ],
            "seed": int(budget.seed),
        }

    binary = problem.allowed_binary_operators or ("+", "-", "*", "/")
    supported_binary = {"+", "-", "*", "/", "**"}
    allowed_binary = tuple(dict.fromkeys(op for op in binary if op in {"+", "-", "*", "/"}))
    ignored_binary = [op for op in problem.allowed_binary_operators if op not in supported_binary]
    allow_square = "**" in binary
    # Keep generated calls inside the same explicit function allowlist as the
    # restricted AST parser. Unknown contract operators are never guessed.
    allowed_unary = tuple(dict.fromkeys(
        op for op in problem.allowed_unary_operators if op in ALLOWED_UNARY_FUNCTIONS
    ))
    ignored_unary = [
        op for op in problem.allowed_unary_operators if op not in ALLOWED_UNARY_FUNCTIONS
    ]
    proposals: list[str] = list(names)
    attempts = 0

    # Unary templates are generated only when explicitly declared by the
    # scientific contract; the attempt and candidate caps apply to each one.
    for name in names:
        for op in allowed_unary:
            if attempts >= search_cap or len(proposals) >= cap:
                break
            attempts += 1
            proposals.append(f"{op}({name})")
        if attempts >= search_cap or len(proposals) >= cap:
            break

    if allow_square:
        for name in names:
            if attempts >= search_cap or len(proposals) >= cap:
                break
            attempts += 1
            proposals.append(f"({name} ** 2)")

    # Multiplication also permits a variable's self-product. Prefer the
    # explicit square form when exponentiation was declared as well.
    if "*" in problem.allowed_binary_operators and not allow_square:
        for name in names:
            if attempts >= search_cap or len(proposals) >= cap:
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
                if attempts >= search_cap or len(proposals) >= cap:
                    break
                attempts += 1
                binary_expression = f"({left} {op} {right})"
                proposals.append(binary_expression)
                for unary_op in allowed_unary:
                    if attempts >= search_cap or len(proposals) >= cap:
                        break
                    attempts += 1
                    proposals.append(f"{unary_op}({binary_expression})")
            if attempts >= search_cap or len(proposals) >= cap:
                break
        if attempts >= search_cap or len(proposals) >= cap:
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
    return {
        "schema": "v60_native_template_generation_v1",
        "generation_status": "completed",
        "proposals": tuple(output),
        "generation_attempt_count": int(attempts),
        "candidate_count": len(output),
        "base_variable_candidate_count": len(names),
        "operator_candidate_count": int(attempts),
        "duplicate_expression_count": max(0, len(proposals[:cap]) - len(output)),
        "search_attempt_budget": int(search_cap),
            "contract_search_attempt_budget": int(budget.max_search_attempts),
        "candidate_budget": int(budget.max_candidates),
        "effective_candidate_cap": int(cap),
        "search_attempt_budget_exhausted": attempts >= search_cap,
        "candidate_cap_reached": len(proposals) >= cap,
        "declared_unary_operators": list(problem.allowed_unary_operators),
        "accepted_unary_operators": list(allowed_unary),
        "ignored_unary_operators": ignored_unary,
        "declared_binary_operators": list(problem.allowed_binary_operators),
        "accepted_binary_operators": list(allowed_binary) + (["**"] if allow_square else []),
        "ignored_binary_operators": ignored_binary,
        "seed": int(budget.seed),
    }


def generate_native_template_candidates(
    problem: DiscoveryProblem, *, limit: int | None = None,
    search_attempt_limit: int | None = None,
) -> tuple[CandidateProposal, ...]:
    """Compatibility wrapper returning only the deterministic proposal tuple."""
    return generate_native_template_candidates_with_audit(
        problem, limit=limit, search_attempt_limit=search_attempt_limit
    )["proposals"]
