"""All arms send the same configured temperature, with one honest fallback."""
import pytest
from hypatiax.core import llm_call


class _C:
    def __init__(self, reject=None):
        self.calls = []; self.reject = reject
        self.messages = self
    def create(self, **kw):
        self.calls.append(kw)
        if self.reject and "temperature" in kw:
            raise self.reject
        return object()


def test_default_temperature_is_025(monkeypatch):
    monkeypatch.delenv("LLM_TEMPERATURE", raising=False)
    c = _C(); llm_call.create_message(c, model="m")
    assert c.calls[0]["temperature"] == 0.25
    assert llm_call.last_call_info()["temperature_sent"] is True


def test_env_override(monkeypatch):
    monkeypatch.setenv("LLM_TEMPERATURE", "0.5")
    c = _C(); llm_call.create_message(c, model="m")
    assert c.calls[0]["temperature"] == 0.5


@pytest.mark.parametrize("exc", [TypeError("create() got an unexpected keyword argument 'temperature'"),
                                 Exception("400 `temperature` is deprecated for this model")])
def test_fallback_once_and_recorded(exc):
    c = _C(reject=exc); llm_call.create_message(c, model="m")
    assert len(c.calls) == 2 and "temperature" not in c.calls[1]
    info = llm_call.last_call_info()
    assert info["temperature_sent"] is False and info["temperature_requested"] == 0.25


def test_unrelated_error_propagates():
    c = _C(reject=RuntimeError("rate limited"))
    c.reject = None
    c.create = lambda **kw: (_ for _ in ()).throw(RuntimeError("rate limited"))
    with pytest.raises(RuntimeError):
        llm_call.create_message(c, model="m")


def test_no_hardcoded_zero_temperature_left():
    import pathlib, re
    root = pathlib.Path(__file__).resolve().parents[2]
    bad = []
    for p in root.rglob("*.py"):
        if "tests" in p.parts or p.name == "llm_call.py":
            continue
        for i, l in enumerate(p.read_text(errors="ignore").splitlines(), 1):
            if re.search(r"messages\.create\(temperature=0\.0|^\s*temperature=0\.0,\s*$", l):
                bad.append(f"{p.name}:{i}")
    assert not bad, bad


def test_safe_exec_formula_defined():
    import ast, pathlib
    p = pathlib.Path(__file__).resolve().parents[2] / "core/generation/hybrid_defi_system/hybrid_system_nn_defi_domain.py"
    names = {n.name for n in ast.parse(p.read_text()).body if isinstance(n, ast.FunctionDef)}
    assert "_safe_exec_formula" in names
