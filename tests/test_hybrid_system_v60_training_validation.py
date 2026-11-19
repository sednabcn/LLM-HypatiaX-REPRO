"""Offline regression coverage for native V60 training-only fold validation."""
import numpy as np

from hypatiax.tools.symbolic.v60_training_validation import validate_native_training_candidates


def _candidate(expression="x", candidate_id="c1"):
    return {
        "candidate_id": candidate_id,
        "expression": expression,
        "normalized_expression": expression,
        "producer_provenance": [{"source": "domain_template", "seed": 11}],
    }


def _run(candidates, X, y, **kwargs):
    return validate_native_training_candidates(
        candidates, X, y, variable_names=("x",),
        eligible_candidate_ids=kwargs.pop("eligible_candidate_ids", ["c1"]),
        **kwargs,
    )


def test_kfold_refits_on_fold_training_rows_and_scores_held_in_rows():
    X = np.arange(1.0, 13.0).reshape(-1, 1)
    y = 3.0 * X[:, 0] + 2.0
    result = _run(
        [_candidate()], X, y, split_protocol={"strategy": "kfold", "n_splits": 4},
        seed=17, max_candidates=5, max_search_attempts=5,
    )
    record = result["candidate_validation"][0]
    assert result["validation_status"] == "completed"
    assert record["validation_method"] == "training_only_refit_cross_validation"
    assert record["fold_count"] == 4
    assert record["validation_rmse_mean"] < 1e-10
    assert all(fold["training_row_count"] + fold["validation_row_count"] == 12 for fold in record["folds"])
    assert all(fold["training_row_count"] == 9 for fold in record["folds"])
    assert result["selection_performed"] is False
    assert result["far_or_evaluation_data_used"] is False


def test_ineligible_candidates_are_not_validated_and_budget_is_audited():
    X = np.arange(1.0, 9.0).reshape(-1, 1)
    y = 2.0 * X[:, 0]
    result = _run(
        [_candidate(candidate_id="c1"), _candidate(candidate_id="c2")],
        X, y, eligible_candidate_ids=["c1"], max_candidates=1, max_search_attempts=1,
    )
    assert result["input_eligible_candidate_count"] == 1
    assert result["validated_candidate_count"] == 1
    assert result["candidate_validation"][0]["candidate_id"] == "c1"
    assert result["budget_truncated_count"] == 0


def test_time_series_folds_use_only_prior_rows_for_each_fit():
    X = np.arange(1.0, 11.0).reshape(-1, 1)
    y = 4.0 * X[:, 0] - 1.0
    result = _run(
        [_candidate()], X, y,
        split_protocol={"strategy": "time_series", "n_splits": 3},
        max_candidates=2, max_search_attempts=2,
    )
    folds = result["candidate_validation"][0]["folds"]
    assert len(folds) == 3
    assert [fold["training_row_count"] for fold in folds] == sorted(
        fold["training_row_count"] for fold in folds
    )
    assert all(fold["training_row_count"] < 10 for fold in folds)


def test_nonfinite_training_data_fails_closed():
    try:
        _run([_candidate()], np.asarray([[1.0], [np.nan], [3.0]]),
             np.asarray([1.0, 2.0, 3.0]))
    except ValueError as exc:
        assert "training data must be finite" in str(exc)
    else:
        raise AssertionError("non-finite training data must be rejected")


def test_unsupported_split_protocol_fails_closed():
    try:
        _run([_candidate()], np.arange(1.0, 7.0).reshape(-1, 1),
             np.arange(1.0, 7.0), split_protocol={"strategy": "random_magic"})
    except ValueError as exc:
        assert "unsupported split_protocol strategy" in str(exc)
    else:
        raise AssertionError("unsupported split strategy must be rejected")
