"""Single source of truth for the HypatiaX clean-run flags.

Copy to hypatiax/core/flags.py.

Rules
-----
* Unset or exactly "1"  -> shortcut disabled (clean run).
* "0" is accepted ONLY when HYPATIAX_ALLOW_LEGACY is exactly "1".
* Any other value ("true", "yes", "2", "") raises RuntimeError.
"""
import os

FLAG_NAMES = ("HYPATIAX_DISABLE_HARDCODED", "HYPATIAX_DISABLE_PROMPT_HINTS")


def legacy_allowed() -> bool:
    return os.environ.get("HYPATIAX_ALLOW_LEGACY") == "1"


def flag_on(name: str) -> bool:
    """True means the shortcut is disabled (clean)."""
    raw = os.environ.get(name)
    if raw is None or raw == "1":
        return True
    if raw == "0" and legacy_allowed():
        return False
    raise RuntimeError(
        f"{name}={raw!r}: only '1' is accepted "
        "('0' additionally requires HYPATIAX_ALLOW_LEGACY=1)"
    )


def clean_run() -> bool:
    """True only if every leakage flag is on."""
    return all(flag_on(n) for n in FLAG_NAMES)


def flag_state() -> dict:
    """Record this in every result row / provenance map."""
    return {
        "HYPATIAX_DISABLE_HARDCODED": os.environ.get("HYPATIAX_DISABLE_HARDCODED"),
        "HYPATIAX_DISABLE_PROMPT_HINTS": os.environ.get("HYPATIAX_DISABLE_PROMPT_HINTS"),
        "HYPATIAX_ALLOW_LEGACY": os.environ.get("HYPATIAX_ALLOW_LEGACY"),
        "clean_run": clean_run(),
    }
