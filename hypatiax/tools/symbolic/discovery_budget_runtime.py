"""Runtime enforcement for caller-declared symbolic discovery budgets."""
from __future__ import annotations

import time
from typing import Any


class DiscoveryBudgetRuntime:
    """Per-discovery, monotonic resource accounting for a typed contract."""

    def __init__(self, budget: Any):
        self.budget = budget
        self.started_at = time.monotonic()
        limit = budget.max_wall_time_seconds
        self.deadline = self.started_at + float(limit) if limit is not None else None
        self.search_attempts = 0
        self.llm_calls_reserved = 0
        self.llm_tokens_reserved = 0
        self.candidates_seen = 0
        self.stop_reason = None

    def expired(self) -> bool:
        if self.deadline is None:
            return False
        expired = time.monotonic() >= self.deadline
        if expired and self.stop_reason is None:
            self.stop_reason = "max_wall_time_seconds"
        return expired

    def can_start_search(self, configured_limit: int) -> bool:
        if self.expired():
            return False
        if self.search_attempts >= min(int(configured_limit), self.budget.max_search_attempts):
            self.stop_reason = "max_search_attempts"
            return False
        if self.candidates_seen >= self.budget.max_candidates:
            self.stop_reason = "max_candidates"
            return False
        return True

    def record_search_attempt(self) -> None:
        self.search_attempts += 1

    @property
    def remaining_candidates(self) -> int:
        return max(0, int(self.budget.max_candidates) - self.candidates_seen)

    def record_candidates(self, count: int) -> int:
        accepted = min(max(0, int(count)), self.remaining_candidates)
        self.candidates_seen += accepted
        if accepted < count and self.stop_reason is None:
            self.stop_reason = "max_candidates"
        return accepted

    def reserve_llm_request(self, configured_tokens: int) -> int | None:
        if self.expired():
            return None
        if self.llm_calls_reserved >= self.budget.max_llm_calls:
            self.stop_reason = "max_llm_calls"
            return None
        token_budget = self.budget.max_llm_tokens
        if token_budget is None:
            token_cap = max(1, int(configured_tokens))
        else:
            remaining = int(token_budget) - self.llm_tokens_reserved
            if remaining <= 0:
                self.stop_reason = "max_llm_tokens"
                return None
            token_cap = min(max(1, int(configured_tokens)), remaining)
        self.llm_calls_reserved += 1
        self.llm_tokens_reserved += token_cap
        return token_cap

    def to_dict(self) -> dict[str, Any]:
        return {
            "enforced": True,
            "requested": self.budget.to_dict(),
            "effective": {
                "max_search_attempts": self.budget.max_search_attempts,
                "max_candidates": self.budget.max_candidates,
                "max_llm_calls": self.budget.max_llm_calls,
                "max_llm_tokens": self.budget.max_llm_tokens,
                "max_wall_time_seconds": self.budget.max_wall_time_seconds,
            },
            "actual": {
                "search_attempts": self.search_attempts,
                "llm_calls_reserved": self.llm_calls_reserved,
                "llm_tokens_reserved": self.llm_tokens_reserved,
                "candidates_seen": self.candidates_seen,
                "elapsed_wall_time_seconds": round(time.monotonic() - self.started_at, 6),
            },
            "stop_reason": self.stop_reason,
            "token_accounting": "conservative_reserved_request_max_tokens",
        }
