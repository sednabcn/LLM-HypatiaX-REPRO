"""The hybrids' local flag helpers must behave exactly like hypatiax.core.flags.flag_on:
unset or "1" = clean; "0" only under HYPATIAX_ALLOW_LEGACY=1; anything else raises.
A typo such as HYPATIAX_DISABLE_PROMPT_HINTS=ON must never silently re-enable hints."""
import importlib

import pytest

NAME = "HYPATIAX_DISABLE_PROMPT_HINTS"
G = "hypatiax.core.generation."
CASES = [
    (G + "hybrid_all_domains_llm_nn.hybrid_system_llm_nn_all_domains", "_switch_on"),
    (G + "hybrid_defi_llm_nn.hybrid_ensemble_system_defi_domain", "_flag"),
]


@pytest.fixture(params=CASES, ids=lambda c: c[0].split(".")[-1])
def parser(request, monkeypatch):
    module, fn = request.param
    monkeypatch.delenv("HYPATIAX_ALLOW_LEGACY", raising=False)
    monkeypatch.delenv(NAME, raising=False)
    return getattr(importlib.import_module(module), fn)


def test_unset_counts_as_clean(parser):
    assert parser(NAME) is True


def test_one_is_clean(parser, monkeypatch):
    monkeypatch.setenv(NAME, "1")
    assert parser(NAME) is True


@pytest.mark.parametrize("junk", ["ON", "off", "true", "yes", "2"])
def test_junk_values_raise(parser, monkeypatch, junk):
    monkeypatch.setenv(NAME, junk)
    with pytest.raises(RuntimeError):
        parser(NAME)


def test_zero_without_legacy_raises(parser, monkeypatch):
    monkeypatch.setenv(NAME, "0")
    with pytest.raises(RuntimeError):
        parser(NAME)


def test_zero_with_legacy_turns_it_off(parser, monkeypatch):
    monkeypatch.setenv("HYPATIAX_ALLOW_LEGACY", "1")
    monkeypatch.setenv(NAME, "0")
    assert parser(NAME) is False
