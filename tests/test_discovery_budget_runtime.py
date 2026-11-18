from hypatiax.tools.symbolic.discovery_contracts import DiscoveryBudget
from hypatiax.tools.symbolic.discovery_budget_runtime import DiscoveryBudgetRuntime


def test_runtime_budget_caps_search_attempts_and_candidates():
    runtime = DiscoveryBudgetRuntime(
        DiscoveryBudget(max_search_attempts=2, max_candidates=2)
    )

    assert runtime.can_start_search(configured_limit=5)
    runtime.record_search_attempt()
    assert runtime.record_candidates(1) == 1

    assert runtime.can_start_search(configured_limit=5)
    runtime.record_search_attempt()
    assert runtime.record_candidates(4) == 1

    assert not runtime.can_start_search(configured_limit=5)
    audit = runtime.to_dict()
    assert audit["actual"]["search_attempts"] == 2
    assert audit["actual"]["candidates_seen"] == 5
    assert audit["actual"]["candidates_admitted"] == 2
    assert audit["actual"]["candidate_budget_overrun"] == 3
    assert audit["stop_reason"] == "max_candidates"


def test_runtime_budget_reserves_llm_calls_and_tokens_conservatively():
    runtime = DiscoveryBudgetRuntime(
        DiscoveryBudget(
            max_search_attempts=3,
            max_candidates=4,
            max_llm_calls=2,
            max_llm_tokens=75,
        )
    )

    assert runtime.reserve_llm_request(configured_tokens=100) == 75
    assert runtime.reserve_llm_request(configured_tokens=100) is None

    audit = runtime.to_dict()
    assert audit["actual"]["llm_calls_reserved"] == 1
    assert audit["actual"]["llm_requests_started"] == 0
    assert audit["actual"]["llm_responses_received"] == 0
    assert audit["actual"]["llm_tokens_reserved"] == 75
    assert audit["stop_reason"] == "max_llm_tokens"


def test_zero_candidate_budget_prevents_search():
    runtime = DiscoveryBudgetRuntime(DiscoveryBudget(max_candidates=0))
    assert not runtime.can_start_search(configured_limit=5)
    assert runtime.stop_reason == "max_candidates"


def test_zero_llm_call_budget_blocks_llm_reservation():
    runtime = DiscoveryBudgetRuntime(DiscoveryBudget(max_llm_calls=0))
    assert runtime.reserve_llm_request(configured_tokens=128) is None
    assert runtime.stop_reason == "max_llm_calls"



def test_candidate_audit_counts_observed_candidates_beyond_admission_cap():
    runtime = DiscoveryBudgetRuntime(DiscoveryBudget(max_candidates=2))

    assert runtime.record_candidates(5) == 2
    assert runtime.remaining_candidates == 0
    audit = runtime.to_dict()["actual"]
    assert audit["candidates_seen"] == 5
    assert audit["candidates_admitted"] == 2
    assert audit["candidate_budget_overrun"] == 3


def test_llm_request_audit_separates_reservation_start_and_response():
    runtime = DiscoveryBudgetRuntime(
        DiscoveryBudget(max_llm_calls=1, max_llm_tokens=64)
    )
    assert runtime.reserve_llm_request(configured_tokens=64) == 64
    runtime.record_llm_request_started()
    runtime.record_llm_response_received()

    audit = runtime.to_dict()["actual"]
    assert audit["llm_calls_reserved"] == 1
    assert audit["llm_requests_started"] == 1
    assert audit["llm_responses_received"] == 1



def test_expired_deadline_is_recorded(monkeypatch):
    import hypatiax.tools.symbolic.discovery_budget_runtime as budget_module

    runtime = DiscoveryBudgetRuntime(
        DiscoveryBudget(max_wall_time_seconds=1.0)
    )
    monkeypatch.setattr(
        budget_module.time,
        "monotonic",
        lambda: runtime.started_at + 2.0,
    )

    assert runtime.expired() is True
    assert runtime.to_dict()["stop_reason"] == "max_wall_time_seconds"
