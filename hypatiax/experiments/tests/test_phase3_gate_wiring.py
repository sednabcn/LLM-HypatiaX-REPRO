from scripts import phase3_all
from scripts.phase3_engine_adapter import GATE_SWITCHES, _gates_off
from hypatiax.tools.symbolic.symbolic_engine import SymbolicEngineWithLLM


def test_core15_complexity_routing_gate_is_switchable():
    assert SymbolicEngineWithLLM._COMPLEXITY_ROUTING is True
    assert GATE_SWITCHES["complexity_routing"] == ("_COMPLEXITY_ROUTING", False)


def test_phase3_exposes_three_core15_gates_and_omits_nn_only_gates():
    assert phase3_all.WIRED == ["llm_acceptance", "complexity_routing", "pysr_prior"]
    assert set(phase3_all.OMIT) == {"probe", "nn_augmentation", "blend_weight"}


def test_complexity_gate_context_restores_full_configuration():
    class FakeEngine:
        _COMPLEXITY_ROUTING = True

    with _gates_off(FakeEngine, ["complexity_routing"]):
        assert FakeEngine._COMPLEXITY_ROUTING is False
    assert FakeEngine._COMPLEXITY_ROUTING is True

def test_nn_specific_core15_gates_are_explicitly_unwired_and_rejected_before_preflight(monkeypatch):
    import pytest
    import scripts.phase3_engine_adapter as adapter

    for gate in ("probe", "nn_augmentation", "blend_weight"):
        assert gate in GATE_SWITCHES
        assert GATE_SWITCHES[gate] is None

    def unexpected_preflight():
        raise AssertionError("unwired gates must be rejected before any preflight")

    monkeypatch.setattr(adapter, "_preflight", unexpected_preflight)
    with pytest.raises(NotImplementedError, match="no engine switch mapped"):
        adapter.run_case("Newton's Second Law", seed=42,
                         disabled=["nn_augmentation"], timeout_s=1.0)


def test_phase3_wired_and_omitted_gate_sets_are_disjoint_and_complete():
    all_gates = {"llm_acceptance", "probe", "complexity_routing",
                 "nn_augmentation", "blend_weight", "pysr_prior"}
    assert set(phase3_all.WIRED).isdisjoint(phase3_all.OMIT)
    assert set(phase3_all.WIRED) | set(phase3_all.OMIT) == all_gates
