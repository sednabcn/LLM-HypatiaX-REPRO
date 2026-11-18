"""Offline regression coverage for V60 training-only residual diagnostics."""
import numpy as np

from hypatiax.tools.symbolic.v60_residual_stability import diagnose_native_training_residuals


def _candidate(expression="x", candidate_id="c1"):
    return {"candidate_id": candidate_id, "expression": expression,
            "normalized_expression": expression}


def _validation(X, y, expression="x"):
    folds = []
    for fold_id, (train, valid) in enumerate(((list(range(4, 8)), list(range(4))),
                                               (list(range(4)), list(range(4, 8))))):
        folds.append({
            "fold": fold_id, "training_row_indices": train,
            "validation_row_indices": valid,
            "training_row_count": len(train), "validation_row_count": len(valid),
            "coefficients": {"scale": 2.0, "intercept": 1.0},
        })
    return {
        "validation_method": "training_only_refit_cross_validation",
        "validation_status": "completed", "far_or_evaluation_data_used": False,
        "fold_count": 2, "candidate_validation": [{
            "candidate_id": "c1", "expression": expression,
            "validation_status": "validated", "folds": folds,
        }],
    }


def test_reconstructs_held_out_residuals_and_fold_coefficient_stability():
    X = np.arange(1.0, 9.0).reshape(-1, 1)
    y = 2.0 * X[:, 0] + 1.0
    result = diagnose_native_training_residuals(
        [_candidate()], _validation(X, y), X, y, variable_names=("x",),
    )
    record = result["candidate_diagnostics"][0]
    assert result["diagnostic_status"] == "completed"
    assert record["fold_count"] == 2
    assert all(fold["residual_rmse"] < 1e-10 for fold in record["folds"])
    assert record["coefficient_stability"]["scale_sign_consistency"] == 1.0
    assert record["coefficient_stability"]["scale_sign_flip_count"] == 0
    assert result["selection_performed"] is False
    assert result["far_or_evaluation_data_used"] is False


def test_expression_mismatch_is_audited_not_silently_diagnosed():
    X = np.arange(1.0, 9.0).reshape(-1, 1)
    y = 2.0 * X[:, 0] + 1.0
    result = diagnose_native_training_residuals(
        [_candidate("x + 1")], _validation(X, y), X, y, variable_names=("x",),
    )
    assert result["diagnosed_candidate_count"] == 0
    assert "does not match" in result["rejected_candidates"][0]["reason"]


def test_fold_row_overlap_is_rejected():
    X = np.arange(1.0, 9.0).reshape(-1, 1)
    y = 2.0 * X[:, 0] + 1.0
    audit = _validation(X, y)
    audit["candidate_validation"][0]["folds"][0]["training_row_indices"] = [0, 1, 2, 3, 4]
    audit["candidate_validation"][0]["folds"][0]["training_row_count"] = 5
    result = diagnose_native_training_residuals(
        [_candidate()], audit, X, y, variable_names=("x",),
    )
    assert result["diagnosed_candidate_count"] == 0
    assert "overlap" in result["rejected_candidates"][0]["reason"]


def test_incomplete_validation_does_not_emit_diagnostics():
    X = np.arange(1.0, 9.0).reshape(-1, 1)
    y = 2.0 * X[:, 0] + 1.0
    audit = _validation(X, y)
    audit["validation_status"] = "budget_limited"
    result = diagnose_native_training_residuals(
        [_candidate()], audit, X, y, variable_names=("x",),
    )
    assert result["diagnostic_status"] == "insufficient_validation_evidence"
    assert result["candidate_diagnostics"] == []
