"""Regression tests for the shared LLM model/temperature runtime settings."""

from hypatiax.tools.symbolic.symbolic_engine import LLMConfig


def test_llm_config_reads_shared_model_and_temperature_at_instantiation(monkeypatch):
    monkeypatch.setenv("HYPATIAX_LLM_MODEL", "test-model-id")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.25")

    config = LLMConfig()

    assert config.model == "test-model-id"
    assert config.temperature == 0.25
