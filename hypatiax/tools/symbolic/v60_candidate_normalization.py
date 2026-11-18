"""Native V60 candidate normalization, semantic identity, and lineage.

Only restricted arithmetic expressions are parsed. Normalization is performed
without training/evaluation values; producer records are retained when multiple
proposals collapse to one symbolic identity.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping, Sequence

from hypatiax.tools.validation.safe_sympy_parser import parse_sympy_expression


@dataclass(frozen=True)
class NormalizedCandidate:
    candidate_id: str
    expression: str
    normalized_expression: str
    producer_provenance: tuple[Mapping[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "expression": self.expression,
            "normalized_expression": self.normalized_expression,
            "producer_provenance": [dict(item) for item in self.producer_provenance],
        }


@dataclass(frozen=True)
class CandidateNormalizationResult:
    candidates: tuple[NormalizedCandidate, ...]
    rejected: tuple[Mapping[str, Any], ...]
    input_count: int
    processed_count: int
    budget_truncated_count: int
    duplicate_proposal_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidates": [item.to_dict() for item in self.candidates],
            "rejected": [dict(item) for item in self.rejected],
            "input_count": self.input_count,
            "processed_count": self.processed_count,
            "budget_truncated_count": self.budget_truncated_count,
            "duplicate_proposal_count": self.duplicate_proposal_count,
        }


def _proposal_dict(proposal: Any) -> dict[str, Any]:
    if hasattr(proposal, "to_dict") and callable(proposal.to_dict):
        value = proposal.to_dict()
    elif isinstance(proposal, Mapping):
        value = dict(proposal)
    else:
        raise TypeError("proposal must be a mapping or expose to_dict()")
    return value


def normalize_candidate_proposals(
    proposals: Sequence[Any],
    *,
    variable_names: Sequence[str],
    max_candidates: int,
) -> CandidateNormalizationResult:
    """Parse, canonicalize, deduplicate, and retain producer lineage.

    The processing ceiling applies to input proposals, not just unique outputs,
    so duplicate-heavy producer pools cannot bypass the configured budget.
    Candidate identity is expression-semantic and therefore independent of
    producer, strategy, and seed; those remain in producer_provenance.
    """
    if isinstance(max_candidates, bool) or not isinstance(max_candidates, int) or max_candidates < 0:
        raise ValueError("max_candidates must be a non-negative integer")
    if not isinstance(proposals, Sequence):
        raise TypeError("proposals must be a finite sequence")

    input_count = len(proposals)
    processed = proposals[:max_candidates]
    groups: dict[str, dict[str, Any]] = {}
    rejected: list[Mapping[str, Any]] = []
    duplicate_count = 0

    for index, item in enumerate(processed):
        raw: dict[str, Any] = {}
        try:
            raw = _proposal_dict(item)
            expression = raw.get("expression")
            source = raw.get("source")
            strategy = raw.get("search_strategy", raw.get("strategy"))
            seed = raw.get("seed")
            if not isinstance(expression, str) or not expression.strip():
                raise ValueError("expression must be a non-empty string")
            if not isinstance(source, str) or not source.strip():
                raise ValueError("source must be a non-empty string")
            if not isinstance(strategy, str) or not strategy.strip():
                raise ValueError("search strategy must be a non-empty string")
            if isinstance(seed, bool) or not isinstance(seed, int):
                raise ValueError("seed must be an integer")

            import sympy as sp
            parsed = parse_sympy_expression(expression, list(variable_names))
            canonical = sp.simplify(parsed)
            canonical_key = sp.srepr(canonical)
            normalized_expression = sp.sstr(canonical)
            candidate_id = sha256(canonical_key.encode("utf-8")).hexdigest()[:20]
            producer = {
                "proposal_candidate_id": raw.get("candidate_id"),
                "source": source,
                "search_strategy": strategy,
                "seed": seed,
                "original_expression": expression,
            }
            if candidate_id in groups:
                groups[candidate_id]["producer_provenance"].append(producer)
                duplicate_count += 1
            else:
                groups[candidate_id] = {
                    "candidate_id": candidate_id,
                    "expression": expression,
                    "normalized_expression": normalized_expression,
                    "producer_provenance": [producer],
                }
        except Exception as exc:
            rejected.append({
                "proposal_index": index,
                "expression": (
                    raw.get("expression")
                ),
                "reason": f"{type(exc).__name__}: {exc}",
            })

    candidates = tuple(
        NormalizedCandidate(
            candidate_id=value["candidate_id"],
            expression=value["expression"],
            normalized_expression=value["normalized_expression"],
            producer_provenance=tuple(dict(item) for item in value["producer_provenance"]),
        )
        for value in groups.values()
    )
    return CandidateNormalizationResult(
        candidates=candidates,
        rejected=tuple(rejected),
        input_count=input_count,
        processed_count=len(processed),
        budget_truncated_count=input_count - len(processed),
        duplicate_proposal_count=duplicate_count,
    )


__all__ = [
    "NormalizedCandidate",
    "CandidateNormalizationResult",
    "normalize_candidate_proposals",
]
