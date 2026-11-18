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



def test_deserializer_rejects_string_coercion_for_variable_names():
    with pytest.raises(TypeError, match="variable_names must be a list"):
        discovery_problem_from_dict({"target_name": "y", "variable_names": "x"})


def test_deserializer_rejects_non_string_variable_names():
    with pytest.raises(TypeError, match="contain only strings"):
        discovery_problem_from_dict({"target_name": "y", "variable_names": ["x", 2]})


def test_deserializer_rejects_boolean_budget_integer():
    with pytest.raises(TypeError, match="max_llm_calls must be an integer"):
        discovery_problem_from_dict({
            "target_name": "y", "variable_names": ["x"],
            "budget": {"max_llm_calls": True},
        })


def test_deserializer_rejects_non_finite_json_numbers():
    with pytest.raises(ValueError, match="finite numbers"):
        discovery_problem_from_dict({
            "target_name": "y", "variable_names": ["x"],
            "metadata": {"tolerance": float("nan")},
        })


def test_deserializer_rejects_non_json_metadata_objects():
    with pytest.raises(TypeError, match="non-JSON value"):
        discovery_problem_from_dict({
            "target_name": "y", "variable_names": ["x"],
            "metadata": {"opaque": object()},
        })


def test_serialized_contract_is_strict_json():
    import json

    problem = DiscoveryProblem(
        target_name="force",
        variable_names=("mass", "acceleration"),
        constraints=(),
    )
    encoded = json.dumps(problem.to_dict(), allow_nan=False, sort_keys=True)
    restored = discovery_problem_from_dict(json.loads(encoded))
    assert restored.to_dict() == problem.to_dict()
