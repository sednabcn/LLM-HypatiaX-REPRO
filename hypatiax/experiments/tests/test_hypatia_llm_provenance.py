from __future__ import annotations

import hashlib
import json
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from hypatiax.experiments.benchmarks import hypatia


EQ = {"id": "provenance-test", "vars": ["x"], "formula_hint": "unknown structure"}
X = np.linspace(0.1, 1.0, 20).reshape(-1, 1)
Y = X[:, 0] ** 2


def _install_client(monkeypatch, create):
    class Messages:
        def create(self, **kwargs):
            return create(**kwargs)

    client = SimpleNamespace(messages=Messages())
    sdk = SimpleNamespace(Anthropic=lambda api_key: client)
    monkeypatch.setattr(hypatia, "_get_anthropic", lambda: sdk)
    return client


def test_missing_credentials_are_not_reported_as_live_calls(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.warns(RuntimeWarning, match="ANTHROPIC_API_KEY not set"):
        assert hypatia.get_llm_prior(EQ, X, Y, cache_dir=str(tmp_path), verbose=False) == []
    info = hypatia.last_call_info()
    assert info["call_status"] == "missing_credentials"
    assert info["candidate_status"] == "not_evaluated"


def test_provider_failure_is_not_relabelled_as_cache_or_success(monkeypatch, tmp_path):
    def fail(**kwargs):
        raise RuntimeError("provider unavailable")

    _install_client(monkeypatch, fail)
    with pytest.warns(RuntimeWarning, match="API call failed"):
        assert hypatia.get_llm_prior(
            EQ, X, Y, api_key="test-key", cache_dir=str(tmp_path), verbose=False
        ) == []
    assert hypatia.last_call_info()["call_status"] == "provider_failure"


def test_live_response_records_temperature_and_empty_candidate_state(monkeypatch, tmp_path):
    seen = {}

    def respond(**kwargs):
        seen.update(kwargs)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text="raw response")])

    _install_client(monkeypatch, respond)
    monkeypatch.setattr(hypatia, "_parse_response", lambda raw, names: [])
    assert hypatia.get_llm_prior(
        EQ, X, Y, api_key="test-key", temperature=0.9,
        cache_dir=str(tmp_path), verbose=False,
    ) == []
    info = hypatia.last_call_info()
    assert seen["temperature"] == 0.25
    assert info["call_status"] == "live_api_success"
    assert info["candidate_status"] == "empty_or_invalid_candidates"
    assert info["temperature_requested"] == 0.25
    assert info["temperature_sent"] is True


def test_cache_replay_is_distinct_from_a_live_api_call(monkeypatch, tmp_path):
    patterns = hypatia._summarise_patterns(X, Y, EQ["vars"])
    prompt = hypatia._build_prompt(EQ, patterns, 5, blind=False)
    key = hashlib.sha256(
        json.dumps(["claude-sonnet-4-6", 1024, "", prompt]).encode("utf-8")
    ).hexdigest()
    tmp_path.mkdir(exist_ok=True)
    (tmp_path / f"{key}.json").write_text(
        json.dumps({"raw": "cached response"}), encoding="utf-8"
    )
    monkeypatch.setattr(hypatia, "_parse_response", lambda raw, names: ["x"])
    assert hypatia.get_llm_prior(
        EQ, X, Y, api_key="test-key", cache_dir=str(tmp_path), verbose=False
    ) == ["x"]
    info = hypatia.last_call_info()
    assert info["call_status"] == "cache_replay"
    assert info["candidate_status"] == "valid_candidates"
    assert info["temperature_sent"] is False


def test_nonfinite_training_inputs_fail_before_api_call(monkeypatch, tmp_path):
    def unexpected():
        raise AssertionError("API client must not be initialized for non-finite input")

    monkeypatch.setattr(hypatia, "_get_anthropic", unexpected)
    with pytest.warns(RuntimeWarning, match="Non-finite training inputs"):
        assert hypatia.get_llm_prior(
            EQ, np.array([[0.1], [np.nan]]), np.array([0.1, 0.2]),
            api_key="test-key", cache_dir=str(tmp_path), verbose=False,
        ) == []
    info = hypatia.last_call_info()
    assert info["call_status"] == "input_invalid"
    assert info["candidate_status"] == "not_evaluated"


def test_pure_llm_adapter_does_not_claim_missing_key_as_live_call(monkeypatch):
    fake_hypatia = SimpleNamespace(
        get_llm_prior=lambda *args, **kwargs: [],
        last_call_info=lambda: {
            "call_status": "missing_credentials",
            "candidate_status": "not_evaluated",
            "temperature_requested": 0.25,
            "temperature_sent": False,
        },
    )
    monkeypatch.setitem(sys.modules, "hypatia", fake_hypatia)
    from hypatiax.experiments.benchmarks.llm_sens_adapter import _pure_llm

    result = _pure_llm(EQ, X, Y, X, Y)
    assert result["llm_called"] is False
    assert result["llm_source"] == "missing_credentials"
    assert result["llm_candidate_status"] == "not_evaluated"
