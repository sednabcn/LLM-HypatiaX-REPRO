"""Fail-closed enforcement of HYPATIAX_DISABLE_HARDCODED and HYPATIAX_DISABLE_PROMPT_HINTS.

Place at hypatiax/core/enforce_flags.py and call enforce() at the very top of every
entrypoint (hybrid system, baseline pure-LLM, run scripts) BEFORE any prompt is built.

- Unset            -> set to "1" (fail closed)
- Set to anything other than "1" -> RuntimeError (no silent override of an explicit 0)
- Returns a dict to be written into provenance files (provenance_map, results rows)
"""
import os

REQUIRED = ("HYPATIAX_DISABLE_HARDCODED", "HYPATIAX_DISABLE_PROMPT_HINTS")


def enforce() -> dict:
    for name in REQUIRED:
        val = os.environ.get(name)
        if val is None or val == "":
            os.environ[name] = "1"
        elif val != "1":
            raise RuntimeError(f"{name}={val!r}: must be '1' for confirmatory runs")
    return {name: os.environ[name] for name in REQUIRED}


def flag_on(name: str) -> bool:
    """Use this instead of ad-hoc os.environ.get(...) checks. Fails closed."""
    if name not in REQUIRED:
        raise KeyError(name)
    return os.environ.get(name, "1") == "1"
