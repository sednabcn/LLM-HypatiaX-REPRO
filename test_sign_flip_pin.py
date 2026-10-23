import pytest
from hypatiax.core import enforce_flags

@pytest.mark.parametrize("v", ["1", "true", "yes", "on", "maybe"])
def test_truthy_or_unknown_aborts(monkeypatch, v):
    monkeypatch.delenv("HYPATIAX_ALLOW_LEGACY", raising=False)
    monkeypatch.setenv("HYPATIAX_R2_SIGN_FLIP", v)
    with pytest.raises(RuntimeError):
        enforce_flags.enforce()

def test_unset_is_zero(monkeypatch):
    monkeypatch.delenv("HYPATIAX_R2_SIGN_FLIP", raising=False)
    assert enforce_flags.enforce()["HYPATIAX_R2_SIGN_FLIP"] == "0"

def test_legacy_allows_it(monkeypatch):
    monkeypatch.setenv("HYPATIAX_ALLOW_LEGACY", "1")
    monkeypatch.setenv("HYPATIAX_R2_SIGN_FLIP", "1")
    assert enforce_flags.enforce()["HYPATIAX_R2_SIGN_FLIP"] == "1"
