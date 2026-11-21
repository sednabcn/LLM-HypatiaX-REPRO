"""Runtime regression tests for exp1's single-attempt LLM provenance."""

from importlib import import_module
from types import SimpleNamespace
import sys


def _benchmark():
    return import_module(
        "hypatiax.experiments.benchmarks.hypatiax_defi_benchmark_v3c"
    )


def test_exp1_provider_failure_is_recorded_as_an_attempt(monkeypatch):
    import hypatiax.core.llm_call as llm_call

    class FakeAnthropic:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setitem(
        sys.modules, "anthropic", SimpleNamespace(Anthropic=FakeAnthropic)
    )
    monkeypatch.setenv("ANTHROPIC_API_KEY", "offline-test-key")
    monkeypatch.setenv("LLM_METHOD_TIMEOUT", "17")

    def fail_after_request_entry(*args, **kwargs):
        raise TimeoutError("simulated provider timeout")

    monkeypatch.setattr(llm_call, "create_message", fail_after_request_entry)
    monkeypatch.setattr(
        llm_call,
        "last_call_info",
        lambda: {"temperature_requested": 0.25, "temperature_sent": False},
    )

    result = _benchmark()._generate_llm_formula(
        "test quantity", "test domain", ["x"], {}
    )

    assert result["llm_called"] is True
    assert result["bypass_kind"] == "none"
    assert result["llm_source"] == "v3c_builtin_failed"
    assert result["timeout_s"] == 17.0
    assert result["temperature_requested"] == 0.25
    assert result["temperature_sent"] is False
    assert "simulated provider timeout" in result["error"]


def test_exp1_client_construction_failure_is_not_recorded_as_request(monkeypatch):
    class BrokenAnthropic:
        def __init__(self, **kwargs):
            raise RuntimeError("simulated client configuration failure")

    monkeypatch.setitem(
        sys.modules, "anthropic", SimpleNamespace(Anthropic=BrokenAnthropic)
    )
    monkeypatch.setenv("ANTHROPIC_API_KEY", "offline-test-key")

    result = _benchmark()._generate_llm_formula(
        "test quantity", "test domain", ["x"], {}
    )

    assert result["llm_called"] is False
    assert result["bypass_kind"] == "none"
    assert result["llm_source"] == "v3c_builtin_failed"
    assert "simulated client configuration failure" in result["error"]


def test_exp1_artifact_declares_query_time_ood_covariate_scope():
    from pathlib import Path

    source_path = (
        Path(__file__).resolve().parents[1]
        / "benchmarks"
        / "hypatiax_defi_benchmark_v3c.py"
    )
    source = source_path.read_text(encoding="utf-8")

    assert '"density_fit_rows": "X_train"' in source
    assert '"query_rows": "X_test"' in source
    assert '"query_labels_used": False' in source
    assert '"access_mode": "query_time_covariate_access"' in source
