"""Offline regression coverage for the native V60 contract preflight."""
import numpy as np
import pytest

from hypatiax.tools.symbolic.discovery_contracts import DiscoveryProblem
from hypatiax.tools.symbolic.hybrid_system_v60 import _prepare_v60_contract_context


def _problem():
    return DiscoveryProblem(
        target_name="force",
        variable_names=("mass", "distance"),
        domain="physics",
        variable_units={"mass": "kg", "distance": "m"},
    )


def test_v60_preflight_builds_data_free_immutable_context():
    X = np.ones((8, 2))
    y = np.arange(8, dtype=float)
    metadata, context = _prepare_v60_contract_context(
        X, y, ["mass", "distance"], {"discovery_problem": _problem()}, "general"
    )

    assert context is not None
    assert context.training_shape == (8, 2)
    assert context.target_shape == (8,)
    assert context.training_row_count == 8
    assert len(context.contract_digest) == 64
    assert "X" not in context.to_dict()
    assert metadata["discovery_problem"].variable_names == ("mass", "distance")
    with pytest.raises((AttributeError, TypeError)):
        context.training_row_count = 99


def test_v60_preflight_deserializes_strict_problem_spec():
    spec = _problem().to_dict()
    metadata, context = _prepare_v60_contract_context(
        np.ones((3, 2)), np.ones(3), ["mass", "distance"],
        {"discovery_problem_spec": spec}, "general"
    )

    assert context is not None
    assert metadata["discovery_problem"].target_name == "force"
    assert "discovery_problem_spec" in metadata


def test_v60_preflight_rejects_variable_order_mismatch():
    with pytest.raises(ValueError, match="variable_names"):
        _prepare_v60_contract_context(
            np.ones((3, 2)), np.ones(3), ["distance", "mass"],
            {"discovery_problem": _problem()}, "general"
        )


def test_v60_preflight_rejects_misaligned_training_shapes():
    with pytest.raises(ValueError, match="target"):
        _prepare_v60_contract_context(
            np.ones((3, 2)), np.ones(2), ["mass", "distance"],
            {"discovery_problem": _problem()}, "general"
        )


def test_v60_without_typed_contract_keeps_compatibility_path():
    metadata, context = _prepare_v60_contract_context(
        np.ones((3, 2)), np.ones(3), ["mass", "distance"], {}, "physics"
    )
    assert context is None
    assert metadata == {}
