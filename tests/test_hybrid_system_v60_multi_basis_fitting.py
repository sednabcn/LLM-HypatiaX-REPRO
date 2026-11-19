"""Offline regression coverage for bounded native V60 joint basis fitting."""
import numpy as np

from hypatiax.tools.symbolic.v60_multi_basis_fitting import fit_native_multi_basis_candidates


def _candidate(candidate_id, expression):
    return {
        "candidate_id": candidate_id,
        "normalized_expression": expression,
        "producer_provenance": [{"source": "test_template", "seed": 7}],
    }


def test_joint_fit_recovers_additive_two_basis_relationship():
    X = np.asarray([[1., 1.], [2., 1.], [1., 2.], [3., 2.], [2., 4.]])
    y = 2.0 * X[:, 0] + 3.0 * X[:, 1] + 4.0
    result = fit_native_multi_basis_candidates(
        [_candidate("x-id", "x"), _candidate("y-id", "y")],
        X, y, variable_names=("x", "y"),
        max_candidates=10, max_search_attempts=10,
    )
    fit = result["fitted_candidate_groups"][0]
    assert fit["basis_candidate_ids"] == ["x-id", "y-id"]
    assert fit["training_rmse"] < 1e-12
    assert np.allclose([term["coefficient"] for term in fit["fitted_terms"]], [2., 3.])
    assert np.isclose(fit["intercept"], 4.)
    assert result["selection_performed"] is False
    assert result["far_or_evaluation_data_used"] is False


def test_group_budget_and_invalid_basis_are_audited():
    result = fit_native_multi_basis_candidates(
        [_candidate("x", "x"), _candidate("bad", "unknown"), _candidate("y", "y")],
        np.asarray([[1., 2.], [2., 1.], [3., 4.]]),
        np.asarray([1., 2., 3.]), variable_names=("x", "y"),
        max_candidates=3, max_search_attempts=2,
    )
    assert result["attempted_group_count"] == 2
    assert result["rejected_group_count"] >= 1
    assert result["selection_performed"] is False


def test_non_finite_training_data_fails_closed():
    try:
        fit_native_multi_basis_candidates(
            [_candidate("x", "x"), _candidate("y", "y")],
            np.asarray([[1., 2.], [np.nan, 1.]]), np.asarray([1., 2.]),
            variable_names=("x", "y"), max_candidates=3, max_search_attempts=3,
        )
    except ValueError as exc:
        assert "training data must be finite" in str(exc)
    else:
        raise AssertionError("non-finite data must be rejected")
