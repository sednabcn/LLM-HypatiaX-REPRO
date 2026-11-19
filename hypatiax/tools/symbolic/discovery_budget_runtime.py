"""Runtime enforcement for caller-declared symbolic discovery budgets."""
from __future__ import annotations

import time
from typing import Any


class DiscoveryBudgetRuntime:
    """Per-discovery, monotonic resource accounting for a typed contract."""

    def __init__(self, budget: Any, configured_search_attempts: int | None = None):
        self.budget = budget
        self.configured_search_attempts = configured_search_attempts
        self.started_at = time.monotonic()
        limit = budget.max_wall_time_seconds
        self.deadline = self.started_at + float(limit) if limit is not None else None
        self.search_attempts = 0
        self.llm_calls_reserved = 0
        self.llm_requests_started = 0
        self.llm_responses_received = 0
        self.llm_tokens_reserved = 0
        self.candidates_seen = 0
        self.candidates_admitted = 0
        self.candidate_budget_overrun = 0
        self.stop_reason = None

    def expired(self) -> bool:
        if self.deadline is None:
            return False
        expired = time.monotonic() >= self.deadline
        if expired and self.stop_reason is None:
            self.stop_reason = "max_wall_time_seconds"
        return expired

    @property
    def remaining_wall_time_seconds(self) -> float | None:
        """Return the remaining per-discovery wall-time budget, clamped at zero."""
        if self.deadline is None:
            return None
        return max(0.0, self.deadline - time.monotonic())

    def can_start_search(self, configured_limit: int) -> bool:
        if self.expired():
            return False
        if self.search_attempts >= min(int(configured_limit), self.budget.max_search_attempts):
            self.stop_reason = self.stop_reason or "max_search_attempts"
            return False
        if self.candidates_admitted >= self.budget.max_candidates:
            self.stop_reason = self.stop_reason or "max_candidates"
            return False
        return True

    def record_search_attempt(self) -> None:
        self.search_attempts += 1

    @property
    def remaining_candidates(self) -> int:
        return max(0, int(self.budget.max_candidates) - self.candidates_admitted)

    def record_candidates(self, count: int) -> int:
        """Record every surfaced candidate and return the subset admitted by budget."""
        observed = max(0, int(count))
        accepted = min(observed, self.remaining_candidates)
        self.candidates_seen += observed
        self.candidates_admitted += accepted
        rejected = observed - accepted
        self.candidate_budget_overrun += rejected
        if rejected and self.stop_reason is None:
            self.stop_reason = "max_candidates"
        return accepted

    def record_llm_request_started(self) -> None:
        """Record a reserved request immediately before invoking the provider."""
        self.llm_requests_started += 1

    def record_llm_response_received(self) -> None:
        """Record a provider response; failed requests remain visible as started only."""
        self.llm_responses_received += 1

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
                "max_search_attempts": (
                    min(self.budget.max_search_attempts, self.configured_search_attempts)
                    if self.configured_search_attempts is not None
                    else self.budget.max_search_attempts
                ),
                "max_candidates": self.budget.max_candidates,
                "max_llm_calls": self.budget.max_llm_calls,
                "max_llm_tokens": self.budget.max_llm_tokens,
                "max_wall_time_seconds": self.budget.max_wall_time_seconds,
            },
            "actual": {
                "search_attempts": self.search_attempts,
                "llm_calls_reserved": self.llm_calls_reserved,
                "llm_requests_started": self.llm_requests_started,
                "llm_responses_received": self.llm_responses_received,
                "llm_tokens_reserved": self.llm_tokens_reserved,
                "candidates_seen": self.candidates_seen,
                "candidates_admitted": self.candidates_admitted,
                "candidate_budget_overrun": self.candidate_budget_overrun,
                "elapsed_wall_time_seconds": round(time.monotonic() - self.started_at, 6),
            },
            "stop_reason": self.stop_reason,
            "token_accounting": "conservative_reserved_request_max_tokens",
        }
