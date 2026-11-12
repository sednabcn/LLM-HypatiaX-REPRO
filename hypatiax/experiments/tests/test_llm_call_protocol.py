"""Core-15 shared LLM temperature protocol regressions."""
import pytest

from hypatiax.core.llm_call import create_message, last_call_info


class _SuccessClient:
    def __init__(self):
        self.calls = []

    class _Messages:
        def __init__(self, outer):
            self.outer = outer

        def create(self, **kwargs):
            self.outer.calls.append(kwargs)
            return object()

    @property
    def messages(self):
        return self._Messages(self)


class _RejectTemperatureClient:
    def __init__(self):
        self.calls = []

    class _Messages:
        def __init__(self, outer):
            self.outer = outer

        def create(self, **kwargs):
            self.outer.calls.append(kwargs)
            raise TypeError("temperature is not supported")

    @property
    def messages(self):
        return self._Messages(self)


def test_shared_wrapper_forces_temperature_025_even_when_caller_overrides():
    client = _SuccessClient()

    create_message(
        client,
        model="test-model",
        max_tokens=10,
        temperature=0.9,
        messages=[{"role": "user", "content": "test"}],
    )

    assert len(client.calls) == 1
    assert client.calls[0]["temperature"] == 0.25
    assert last_call_info() == {
        "temperature_requested": 0.25,
        "temperature_sent": True,
    }


def test_temperature_rejection_fails_closed_without_default_temperature_retry():
    client = _RejectTemperatureClient()

    with pytest.raises(TypeError, match="temperature"):
        create_message(
            client,
            model="test-model",
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}],
        )

    assert len(client.calls) == 1
    assert client.calls[0]["temperature"] == 0.25
    assert last_call_info() == {
        "temperature_requested": 0.25,
        "temperature_sent": False,
    }
