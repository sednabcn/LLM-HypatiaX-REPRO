from scripts import phase3_all
from scripts.phase3_engine_adapter import GATE_SWITCHES
from hypatiax.tools.symbolic.symbolic_engine import SymbolicEngineWithLLM


def test_core15_complexity_routing_gate_is_switchable():
    assert SymbolicEngineWithLLM._COMPLEXITY_ROUTING is True
    assert GATE_SWITCHES["complexity_routing"] == ("_COMPLEXITY_ROUTING", False)


def test_phase3_exposes_three_core15_gates_and_omits_nn_only_gates():
    assert phase3_all.WIRED == ["llm_acceptance", "complexity_routing", "pysr_prior"]
    assert set(phase3_all.OMIT) == {"probe", "nn_augmentation", "blend_weight"}
