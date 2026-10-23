"""Fail-closed enforcement of the clean-run flags.

- HYPATIAX_DISABLE_HARDCODED / HYPATIAX_DISABLE_PROMPT_HINTS: unset -> "1"; anything else raises.
- HYPATIAX_R2_SIGN_FLIP: unset -> "0"; any value other than an explicit off value raises,
  unless HYPATIAX_ALLOW_LEGACY=1 (deliberate sensitivity run, separate output dir).
- enforce() returns a dict to write into provenance files and result rows.
"""
import os

REQUIRED = ("HYPATIAX_DISABLE_HARDCODED", "HYPATIAX_DISABLE_PROMPT_HINTS")
SIGN_FLIP = "HYPATIAX_R2_SIGN_FLIP"
_OFF = {"", "0", "false", "no", "off"}


def enforce() -> dict:
    for name in REQUIRED:
        val = os.environ.get(name)
        if val is None or val == "":
            os.environ[name] = "1"
        elif val != "1":
            raise RuntimeError(f"{name}={val!r}: must be '1' for confirmatory runs")
    raw = os.environ.get(SIGN_FLIP, "").strip().lower()
    if raw not in _OFF and os.environ.get("HYPATIAX_ALLOW_LEGACY") != "1":
        raise RuntimeError(f"{SIGN_FLIP}={raw!r}: legacy sign-flip scoring needs HYPATIAX_ALLOW_LEGACY=1")
    if raw in _OFF:
        os.environ[SIGN_FLIP] = "0"
    return {name: os.environ[name] for name in REQUIRED + (SIGN_FLIP,)}


def flag_on(name: str) -> bool:
    """Use this instead of ad-hoc os.environ.get(...) checks. Fails closed."""
    if name not in REQUIRED:
        raise KeyError(name)
    return os.environ.get(name, "1") == "1"
