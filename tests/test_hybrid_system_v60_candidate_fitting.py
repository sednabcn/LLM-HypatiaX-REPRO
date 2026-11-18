"""Offline regression coverage for native V60 training-only candidate fitting."""
import numpy as np

from hypatiax.tools.symbolic.v60_candidate_fitting import fit_native_training_candidates


def _candidate(expression, candidate_id="c1"):
    return {
        "candidate_id": candidate_id, "expression": expression,
        "normalized_expression": expression,
        "producer_provenance": [{"source": "domain_template", "seed": 3}],
    }


def test_affine_fit_recovers_scale_and_intercept_from_training_rows():
    X = np.asarray([[1.0], [2.0], [3.0], [4.0]])
    y = 3.0 * X[:, 0] + 5.0
    result = fit_native_training_candidates(
        [_candidate("x")], X, y, variable_names=("x",),
        max_candidates=5, max_search_attempts=5,
    )
    fit = result["fitted_candidates"][0]
    assert fit["candidate_id"] == "c1"
    assert fit["training_rmse"] < 1e-12
    assert fit["coefficients"]["scale"] == 3.0
    assert fit["coefficients"]["intercept"] == 5.0
    assert fit["training_row_count"] == 4
    assert result["selection_performed"] is False


def test_fit_budget_and_rejection_audit_are_preserved():
    result = fit_native_training_candidates(
        [_candidate("x", "ok"), _candidate("unknown", "bad"), _candidate("x+1", "truncated")],
        np.asarray([[1.0], [2.0], [3.0]]), np.asarray([2.0, 4.0, 6.0]),
        variable_names=("x",), max_candidates=2, max_search_attempts=2,
    )
    assert result["fit_attempt_count"] == 2
    assert result["fitted_candidate_count"] == 1
    assert result["rejected_candidates"][0]["candidate_id"] == "bad"
    assert result["budget_truncated_count"] == 1


def test_non_finite_training_data_fails_closed():
    try:
        fit_native_training_candidates(
            [_candidate("x")], np.asarray([[1.0], [np.nan]]), np.asarray([1.0, 2.0]),
            variable_names=("x",), max_candidates=2, max_search_attempts=2,
        )
    except ValueError as exc:
        assert "training data must be finite" in str(exc)
    else:
        raise AssertionError("non-finite training data must be rejected")