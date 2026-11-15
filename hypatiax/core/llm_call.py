"""Single LLM call wrapper shared by every arm (hybrids, PureLLM, benchmarks).

Core-15 fixes the requested sampling temperature at 0.25. Every live call sends
that parameter exactly once. If the SDK/model rejects it, the call fails closed:
there is no retry at an implicit provider default that would violate arm parity.
"""
from __future__ import annotations

import threading

_state = threading.local()


def configured_temperature() -> float:
    """Fixed benchmark sampling temperature shared by every LLM path."""
    return 0.25


def last_call_info() -> dict:
    """{'temperature_requested', 'temperature_sent'} for the most recent create_message()."""
    return dict(getattr(_state, "info", {}) or {})


def create_message(client, **kwargs):
    """Make exactly one API attempt with the protocol-fixed temperature."""
    # Ignore caller/env overrides so legacy call sites cannot silently create
    # unmatched LLM conditions. Never retry without temperature: that would
    # silently use a provider default instead of the Core-15 protocol value.
    req = configured_temperature()
    kwargs = {**kwargs, "temperature": req}
    # Clear prior-call state before the request. False means no successful
    # response confirmed that the requested parameter was accepted.
    _state.info = {"temperature_requested": req, "temperature_sent": False}
    resp = client.messages.create(**kwargs)
    _state.info = {"temperature_requested": req, "temperature_sent": True}
    return resp
