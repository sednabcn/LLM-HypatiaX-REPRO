"""Offline tests for Feynman horizon integration."""
import numpy as np
import pytest

from hypatiax.tools.feynman_horizon import evaluate_feynman_horizon_curves


@pytest.mark.parametrize("equation_id,X,truth", [
    ("I.12.1", np.array([[1., 2., 3.], [2., 3., 4.], [3., 4., 5.]]),
     lambda X: 6.674e-11 * X[:, 0] * X[:, 1] / X[:, 2] ** 2),
    ("FEY_MECH_KE", np.array([[1., 2.], [2., 3.], [3., 4.]]),
     lambda X: 0.5 * X[:, 0] * X[:, 1] ** 2),
    ("I.18.4", np.array([[1., 2.], [2., 3.], [3., 4.]]),
     lambda X: X[:, 0] * X[:, 1] / (X[:, 0] + X[:, 1])),
])
def test_feynman_adapter_emits_single_and_combination_curves(equation_id, X, truth):
    y = truth(X)
    records = evaluate_feynman_horizon_curves(
        equation_id, X, y, {"oracle": lambda points: truth(points)},
        distances=(0.25, 0.5), n_points=5,
    )
    assert records
    assert {r["method"] for r in records} == {"oracle"}
    assert any(r["evaluation"]["strategy"] == "both" for r in records)
    assert any(r["evaluation"]["strategy"] == "feature_combination" for r in records)
    assert all(r["provenance"]["model_retrained"] is False for r in records)
    scored = [r for r in records if r["metrics"].get("far_rmse") is not None]
    assert scored
    assert all(r["metrics"]["far_rmse"] == pytest.approx(0.0) for r in scored)


def test_adapter_rejects_unknown_equation_and_nonphysical_training_data():
    with pytest.raises(ValueError, match="Unsupported"):
        evaluate_feynman_horizon_curves("unknown", [[1.0]], [1.0], {"m": lambda X: X[:, 0]})
    with pytest.raises(ValueError, match="positive physical domain"):
        evaluate_feynman_horizon_curves(
            "FEY_MECH_KE", [[1.0, 0.0], [2.0, 1.0]], [0.0, 1.0],
            {"m": lambda X: X[:, 0]},
        )
