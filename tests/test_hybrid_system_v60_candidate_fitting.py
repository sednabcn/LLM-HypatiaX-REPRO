"""Offline regression tests for bounded native V60 candidate fitting."""
import numpy as np
import pytest

from hypatiax.tools.symbolic.v60_candidate_fitting import fit_native_candidates


def _candidate(candidate_id="c1", expression="x"):
    return {
        "candidate_id": candidate_id,
        "expression": expression,
        "normalized_expression": expression,
    }


def test_affine_calibration_uses_training_rows_and_records_metrics():
    X = np.array([[1.0], [2.0], [3.0], [4.0]])
    y = 2.0 * X[:, 0] + 1.0
    result = fit_native_candidates(
        [_candidate()], X, y, variable_names=("x",),
        max_candidates=5, max_search_attempts=5,
    )
    record = result.records[0]
    assert record.status == "fitted"
    assert np.isclose(record.scale, 2.0)
    assert np.isclose(record.offset, 1.0)
    assert np.isclose(record.training_rmse, 0.0)
    assert np.isclose(record.training_r2, 1.0)
    assert record.training_row_count == 4
    assert result.to_dict()["selection_performed"] is False


def test_invalid_candidate_is_rejected_without_dropping_rows():
    result = fit_native_candidates(
        [_candidate(expression="undeclared + x")],
        np.array([[1.0], [2.0]]), np.array([1.0, 2.0]),
        variable_names=("x",), max_candidates=2, max_search_attempts=2,
    )
    assert result.records[0].status == "rejected"
    assert result.records[0].training_rmse is None
    assert result.records[0].reason


def test_candidate_and_attempt_budgets_bound_processing():
    candidates = [_candidate("c1"), _candidate("c2"), _candidate("c3")]
    result = fit_native_candidates(
        candidates, np.array([[1.0], [2.0]]), np.array([1.0, 2.0]),
        variable_names=("x",), max_candidates=3, max_search_attempts=1,
    )
    assert result.attempted_count == 1
    assert result.budget_truncated_count == 2


def test_non_finite_training_input_fails_closed():
    try:
        fit_native_candidates(
            [_candidate()], np.array([[1.0], [np.nan]]), np.array([1.0, 2.0]),
            variable_names=("x",), max_candidates=1, max_search_attempts=1,
        )
    except ValueError as exc:
        assert "finite" in str(exc)
    else:
        raise AssertionError("non-finite training data must be rejected")


@pytest.mark.parametrize("candidate_id", [None, 7, True, "   "])
def test_malformed_candidate_identity_is_rejected(candidate_id):
    result = fit_native_candidates(
        [_candidate(candidate_id=candidate_id)],
        np.array([[1.0], [2.0]]), np.array([1.0, 2.0]),
        variable_names=("x",), max_candidates=1, max_search_attempts=1,
    )
    assert result.records[0].status == "rejected"
    assert "non-empty strings" in result.records[0].reason


@pytest.mark.parametrize("deadline", [0, -1, float("nan"), float("inf"), True, "1"])
def test_invalid_wall_time_budget_is_rejected(deadline):
    with pytest.raises(ValueError, match="finite and > 0"):
        fit_native_candidates(
            [_candidate()], np.array([[1.0], [2.0]]), np.array([1.0, 2.0]),
            variable_names=("x",), max_candidates=1, max_search_attempts=1,
            max_wall_time_seconds=deadline,
        )


def test_non_mapping_candidate_is_rejected_without_aborting_batch():
    result = fit_native_candidates(
        [None, _candidate("valid")],
        np.array([[1.0], [2.0]]), np.array([1.0, 2.0]),
        variable_names=("x",), max_candidates=2, max_search_attempts=2,
    )
    assert [record.status for record in result.records] == ["rejected", "fitted"]
