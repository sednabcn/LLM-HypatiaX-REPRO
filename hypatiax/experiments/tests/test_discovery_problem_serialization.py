"""Regression tests for JSON-safe scientific discovery contract deserialization."""

import pytest

from hypatiax.tools.symbolic.discovery_contracts import (
    DiscoveryProblem,
    discovery_problem_from_dict,
)


def test_discovery_problem_json_contract_round_trips():
    original = DiscoveryProblem(
        target_name="force",
        variable_names=("mass", "acceleration"),
        domain="mechanics",
        target_unit="N",
        variable_units={"mass": "kg", "acceleration": "m/s^2"},
        variable_domains={"mass": {"min": 0.1, "max": 10.0}},
        metadata={"source": "user_declared"},
    )
    restored = discovery_problem_from_dict(original.to_dict())
    assert restored.to_dict() == original.to_dict()
    assert isinstance(restored, DiscoveryProblem)


def test_discovery_problem_deserializer_rejects_unknown_fields():
    with pytest.raises(ValueError, match="unknown discovery problem fields"):
        discovery_problem_from_dict({
            "target_name": "y",
            "variable_names": ["x"],
            "assume_positive": True,
        })


def test_discovery_problem_deserializer_rejects_unknown_constraint_fields():
    with pytest.raises(ValueError, match="unknown constraint fields"):
        discovery_problem_from_dict({
            "target_name": "y",
            "variable_names": ["x"],
            "constraints": [{
                "constraint_id": "c1",
                "kind": "positive_output",
                "guess_from_name": True,
            }],
        })


def test_discovery_problem_deserializer_rejects_unsupported_schema_version():
    with pytest.raises(ValueError, match="unsupported discovery contract"):
        discovery_problem_from_dict({
            "schema_version": "99.0",
            "target_name": "y",
            "variable_names": ["x"],
        })
