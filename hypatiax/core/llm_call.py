"""Single LLM call wrapper shared by every arm (hybrids, PureLLM, benchmarks).

Why: arms used to differ -- hybrids hard-coded temperature=0.0 (and crashed with a
client-side TypeError on SDKs that dropped the argument), PureLLM sent none, and the
engine/CI config says LLM_TEMPERATURE=0.25.  Now every arm requests the SAME configured
temperature, falls back ONCE without it if the SDK/model rejects it, and records what was
really sent so rows can report 'temperature_sent' honestly.
"""
from __future__ import annotations

import os
import threading

_state = threading.local()


def configured_temperature() -> float:
    try:
        return float(os.environ.get("LLM_TEMPERATURE") or 0.25)
    except ValueError:
        return 0.25


def last_call_info() -> dict:
    """{'temperature_requested', 'temperature_sent'} for the most recent create_message()."""
    return dict(getattr(_state, "info", {}) or {})


def _rejects_temperature(exc: Exception) -> bool:
    m = str(exc).lower()
    if isinstance(exc, TypeError) and "temperature" in m:
        return True
    return "temperature" in m and any(k in m for k in ("deprecated", "not supported", "unexpected", "invalid"))


def create_message(client, **kwargs):
    """client.messages.create(**kwargs) with the configured temperature, one fallback."""
    if "temperature" in kwargs:
        req = kwargs["temperature"]
    else:
        req = configured_temperature()
        kwargs = {**kwargs, "temperature": req}
    try:
        resp = client.messages.create(**kwargs)
        _state.info = {"temperature_requested": req, "temperature_sent": True}
        return resp
    except Exception as e:  # noqa: BLE001
        if not _rejects_temperature(e):
            raise
        kwargs.pop("temperature", None)
        resp = client.messages.create(**kwargs)
        _state.info = {"temperature_requested": req, "temperature_sent": False}
        return resp
