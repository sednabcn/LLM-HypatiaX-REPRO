import pytest
from hypatiax.core import flags

NAMES = flags.FLAG_NAMES + ("HYPATIAX_ALLOW_LEGACY",)


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    for n in NAMES:
        monkeypatch.delenv(n, raising=False)


def test_unset_is_clean():
    assert flags.clean_run()


def test_exact_one_is_clean(monkeypatch):
    for n in flags.FLAG_NAMES:
        monkeypatch.setenv(n, "1")
    assert flags.clean_run()


@pytest.mark.parametrize("bad", ["true", "yes", "2", "", "off"])
def test_other_values_raise(monkeypatch, bad):
    monkeypatch.setenv("HYPATIAX_DISABLE_PROMPT_HINTS", bad)
    with pytest.raises(RuntimeError):
        flags.clean_run()


def test_zero_without_legacy_raises(monkeypatch):
    monkeypatch.setenv("HYPATIAX_DISABLE_PROMPT_HINTS", "0")
    with pytest.raises(RuntimeError):
        flags.clean_run()


def test_zero_with_legacy_is_not_clean(monkeypatch):
    monkeypatch.setenv("HYPATIAX_DISABLE_PROMPT_HINTS", "0")
    monkeypatch.setenv("HYPATIAX_ALLOW_LEGACY", "1")
    assert not flags.clean_run()


@pytest.mark.parametrize("val", ["true", "yes", "TRUE"])
def test_legacy_requires_exact_one(monkeypatch, val):
    monkeypatch.setenv("HYPATIAX_DISABLE_PROMPT_HINTS", "0")
    monkeypatch.setenv("HYPATIAX_ALLOW_LEGACY", val)
    with pytest.raises(RuntimeError):
        flags.clean_run()
