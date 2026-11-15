import numpy as np
import pytest

from hypatiax.core.core15_nn import (
    Core15NN, blend_predictions, training_edge_indices,
)


def test_core15_nn_is_deterministic_and_returns_finite_predictions():
    rng = np.random.default_rng(7)
    X = rng.normal(size=(64, 2))
    y = 2.0 * X[:, 0] - 0.5 * X[:, 1] + 1.0
    a = Core15NN(seed=19, hidden_layer_sizes=(16, 8), max_iter=300).fit(X, y)
    b = Core15NN(seed=19, hidden_layer_sizes=(16, 8), max_iter=300).fit(X, y)
    np.testing.assert_allclose(a.predict(X[:8]), b.predict(X[:8]), rtol=0, atol=1e-10)
    assert np.isfinite(a.predict(X[:8])).all()


def test_core15_nn_rejects_nonfinite_training_and_unfitted_prediction():
    X = np.ones((12, 2))
    model = Core15NN(hidden_layer_sizes=(8,), max_iter=20)
    with pytest.raises(RuntimeError, match="fitted"):
        model.predict(X[:2])
    X[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        model.fit(X, np.ones(12))


def test_training_edge_probe_is_symmetric_and_partitions_training_rows():
    rng = np.random.default_rng(3)
    X = rng.normal(size=(100, 3))
    core, edge = training_edge_indices(X, edge_fraction=0.15)
    assert len(set(core).intersection(edge)) == 0
    assert sorted(np.concatenate([core, edge]).tolist()) == list(range(len(X)))
    assert len(edge) >= 2


def test_manuscript_blend_uses_per_query_ood_weights():
    out = blend_predictions(
        [10.0, 10.0], [0.0, 0.0], [0.0, 1.0], alpha=0.3
    )
    np.testing.assert_allclose(out["llm_weights"], [0.3, 1.0])
    np.testing.assert_allclose(out["nn_weights"], [0.7, 0.0])
    np.testing.assert_allclose(out["predictions"], [3.0, 10.0])


def test_blend_rejects_invalid_probabilities_and_shape_mismatch():
    with pytest.raises(ValueError, match="identical"):
        blend_predictions([1.0], [1.0, 2.0], [0.5])
    with pytest.raises(ValueError, match="probabilities"):
        blend_predictions([1.0], [1.0], [1.2])
