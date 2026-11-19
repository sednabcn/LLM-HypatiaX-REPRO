"""End-to-end native V60 orchestration and strict data-boundary contracts."""

import numpy as np
import pytest

from hypatiax.tools.symbolic.discovery_contracts import DiscoveryBudget, DiscoveryProblem
from hypatiax.tools.symbolic.hybrid_system_v60 import HybridDiscoverySystemV60


def _problem():
    return DiscoveryProblem(
        target_name="y",
        variable_names=("x",),
        budget=DiscoveryBudget(
            max_search_attempts=10,
            max_candidates=10,
            seed=7,
        ),
    )


def _training_data():
    X = np.linspace(1.0, 12.0, 24).reshape(-1, 1)
    y = 2.5 * X[:, 0] + 1.25
    return X, y


def test_native_activation_requires_a_typed_problem_contract():
    engine = HybridDiscoverySystemV60(use_llm=False)
    X, y = _training_data()

    with pytest.raises(ValueError, match="requires a typed DiscoveryProblem"):
        engine.discover(
            X=X, y=y, var_names=["x"],
            metadata={"v60_activate_native_model": True},
        )
    assert engine._last_v60_run_context is None
    assert engine._last_v60_activate_native_result is False


def test_native_activation_runs_training_only_pipeline_without_v50_fallback():
    engine = HybridDiscoverySystemV60(use_llm=False)
    X, y = _training_data()

    result = engine.discover(
        X=X, y=y, var_names=["x"],
        metadata={
            "discovery_problem": _problem(),
            "v60_activate_native_model": True,
        },
    )

    assert result["strategy"] == "native_v60"
    assert result["success"] is True
    assert result["implementation_provenance"]["native_v60_pipeline"] is True
    assert result["implementation_provenance"]["native_v60_production_handoff_enabled"] is True
    assert result["v50_2_compatibility_result"]["status"] == "not_executed"
    assert engine._last_v60_gate_audit["training_or_far_data_used"] is False
    assert engine._last_v60_training_validation_audit["far_or_evaluation_data_used"] is False
    assert engine._last_v60_objective_selection_audit["far_or_evaluation_data_used"] is False
    assert engine._last_v60_final_model_audit["far_or_evaluation_data_used"] is False
    assert engine._last_v60_far_evaluation_audit == {}


def test_far_evaluation_is_separate_and_cannot_change_frozen_selection():
    engine = HybridDiscoverySystemV60(use_llm=False)
    X, y = _training_data()
    engine.discover(
        X=X, y=y, var_names=["x"],
        metadata={
            "discovery_problem": _problem(),
            "v60_activate_native_model": True,
        },
    )
    before = engine._last_v60_final_model_audit["selected_model_sha256"]

    far_X = np.array([[20.0], [21.0], [22.0]])
    far_y = 2.5 * far_X[:, 0] + 1.25
    audit = engine.evaluate_native_far_set(far_X, far_y)

    assert audit["evaluation_status"] == "completed"
    assert audit["selection_changed"] is False
    assert audit["selection_performed"] is False
    assert audit["far_or_evaluation_data_used_for_selection"] is False
    assert engine._last_v60_final_model_audit["selected_model_sha256"] == before


def test_far_evaluation_is_rejected_before_native_finalization():
    engine = HybridDiscoverySystemV60(use_llm=False)
    with pytest.raises(RuntimeError, match="activation must complete"):
        engine.evaluate_native_far_set([[1.0]], [1.0])



def test_far_arrays_are_rejected_from_native_discovery_metadata():
    engine = HybridDiscoverySystemV60(use_llm=False)
    X, y = _training_data()

    with pytest.raises(ValueError, match="far/evaluation arrays are not accepted"):
        engine.discover(
            X=X, y=y, var_names=["x"],
            metadata={
                "discovery_problem": _problem(),
                "v60_activate_native_model": True,
                "X_far": [[100.0]],
                "y_far": [251.25],
            },
        )

def test_native_activation_flag_must_be_boolean():
    engine = HybridDiscoverySystemV60(use_llm=False)
    X, y = _training_data()

    with pytest.raises(TypeError, match="must be a boolean"):
        engine.discover(
            X=X, y=y, var_names=["x"],
            metadata={
                "discovery_problem": _problem(),
                "v60_activate_native_model": "true",
            },
        )
