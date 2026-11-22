import json

import numpy as np

from scripts.calibrate_llm_edge_degradation import (
    _array_hash,
    _bootstrap_interval,
    _cohort_assignment,
    _json_rows,
    _match_protocol_case,
    benchmark,
)


def test_calibration_cohorts_are_deterministic_and_stratified():
    cases = benchmark._get_test_cases()
    first = _cohort_assignment(cases)
    second = _cohort_assignment(cases)

    assert first == second
    assert len(first) == 74
    for difficulty in {case["difficulty"] for case in cases}:
        labels = {
            first[case["name"]]
            for case in cases
            if case["difficulty"] == difficulty
        }
        assert labels == {"calibration", "evaluation"}


def test_protocol_match_prefers_exact_name_over_substring():
    exact = ("Constant product formula", np.array([[1.0]]), np.array([1.0]), ["x"], {})
    longer = (
        "Constant product formula (multivariate)",
        np.array([[2.0]]),
        np.array([2.0]),
        ["x"],
        {},
    )

    assert _match_protocol_case("Constant product formula", [longer, exact]) is exact


def test_prompt_rows_contain_only_supplied_core_examples():
    X_core = np.array([[1.0, 2.0], [3.0, 4.0]])
    y_core = np.array([5.0, 7.0])

    rows = json.loads(_json_rows(X_core, y_core, ["x", "z"]))

    assert rows == [
        {"x": 1.0, "z": 2.0, "target": 5.0},
        {"x": 3.0, "z": 4.0, "target": 7.0},
    ]


def test_array_hash_covers_labels_as_well_as_covariates():
    X = np.array([[1.0], [2.0]])
    assert _array_hash(X, np.array([3.0, 4.0])) != _array_hash(
        X, np.array([3.0, 5.0])
    )


def test_bootstrap_uncertainty_is_reproducible_and_finite():
    values = np.array([0.01, 0.02, 0.03, 0.10, 0.20])
    first = _bootstrap_interval(values, "q90", seed=123)
    second = _bootstrap_interval(values, "q90", seed=123)

    assert first == second
    assert len(first) == 2
    assert np.isfinite(first).all()
    assert first[0] <= first[1]
