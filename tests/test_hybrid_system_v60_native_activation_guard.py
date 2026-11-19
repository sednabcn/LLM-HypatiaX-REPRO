"""Fail-closed contract for the not-yet-integrated native V60 handoff."""

import numpy as np
import pytest

from hypatiax.tools.symbolic.discovery_contracts import DiscoveryProblem
from hypatiax.tools.symbolic.hybrid_system_v60 import HybridDiscoverySystemV60


def _problem():
    return DiscoveryProblem(target_name="y", variable_names=("x",))


def test_explicit_native_activation_is_rejected_instead_of_falling_back():
    engine = HybridDiscoverySystemV60(use_llm=False)
    X = np.arange(1.0, 5.0).reshape(-1, 1)
    y = 2.0 * X[:, 0] + 1.0

    with pytest.raises(NotImplementedError, match="not wired into discover"):
        engine.discover(
            X=X,
            y=y,
            var_names=["x"],
            metadata={
                "discovery_problem": _problem(),
                "v60_activate_native_model": True,
            },
        )

    assert engine._last_v60_run_context is None
    assert engine._last_v60_candidate_proposals == ()


def test_native_activation_flag_must_be_boolean():
    engine = HybridDiscoverySystemV60(use_llm=False)
    X = np.arange(1.0, 5.0).reshape(-1, 1)
    y = 2.0 * X[:, 0] + 1.0

    with pytest.raises(TypeError, match="must be a boolean"):
        engine.discover(
            X=X,
            y=y,
            var_names=["x"],
            metadata={
                "discovery_problem": _problem(),
                "v60_activate_native_model": "true",
            },
        )
