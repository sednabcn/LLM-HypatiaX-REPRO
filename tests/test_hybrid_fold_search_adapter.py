"""Regression source for the fold-local Hybrid/PySR adapter (not executed here)."""
import numpy as np

from hypatiax.tools.symbolic import hybrid_fold_search as fold_search


class FakeConfig:
    def __init__(self):
        self.niterations = 100
        self.pysr_timeout = 900
        self.parsimony = 0.01
        self.binary_operators = ["+", "-", "*", "/"]
        self.populations = 5


class FakeEngine:
    instances = []

    def __init__(self, config, domain):
        self.config = config
        self.domain = domain
        self._last_fold_transform_state = None
        self.fit_X = None
        self.fit_y = None
        self.validation_X = None
        FakeEngine.instances.append(self)

    def discover(self, X, y, variable_names, equation_name, random_state):
        self.fit_X = np.asarray(X).copy()
        self.fit_y = np.asarray(y).copy()
        self._last_fold_transform_state = {"fake": True}
        return {"expression": "x0"}

    def predict_fold_validation(self, X):
        self.validation_X = np.asarray(X).copy()
        return np.ones(X.shape[0], dtype=float)


def _searcher(monkeypatch, X_fit, y_fit):
    monkeypatch.setattr(fold_search, "SymbolicEngine", FakeEngine)
    FakeEngine.instances.clear()
    model = fold_search.HybridFoldPySRSearcher(
        config=FakeConfig(),
        domain="general",
        variable_names=["x0"],
        equation_name="fold test",
        seed=7,
        parsimony=0.01,
        fold_iterations=10,
        fold_timeout_seconds=5,
    )
    model.fit(X_fit, y_fit)
    return model, FakeEngine.instances[-1]


def test_outer_log_transforms_are_fit_only_and_reused_for_validation(monkeypatch):
    X_fit = np.array([[1.0], [10.0], [1e4], [1e6]])
    y_fit = np.array([1.0, 10.0, 1e4, 1e6])
    model, engine = _searcher(monkeypatch, X_fit, y_fit)

    expected_fit = np.sign(X_fit) * np.log10(np.abs(X_fit) + 1.0)
    np.testing.assert_allclose(engine.fit_X, expected_fit)
    np.testing.assert_allclose(
        engine.fit_y, np.sign(y_fit) * np.log10(np.abs(y_fit) + 1.0)
    )

    X_validation = np.array([[1e7], [2e7]])
    prediction = model.predict(X_validation)
    expected_validation = np.sign(X_validation) * np.log10(
        np.abs(X_validation) + 1.0
    )
    np.testing.assert_allclose(engine.validation_X, expected_validation)
    np.testing.assert_allclose(prediction, np.array([9.0, 9.0]))
    assert model.get_best()["equation"] == "x0"


def test_validation_range_does_not_change_fit_learned_log_flags(monkeypatch):
    X_fit = np.array([[1.0], [2.0], [3.0], [4.0]])
    y_fit = np.array([2.0, 3.0, 4.0, 5.0])
    model, engine = _searcher(monkeypatch, X_fit, y_fit)

    X_validation = np.array([[1e12]])
    model.predict(X_validation)
    np.testing.assert_allclose(engine.validation_X, X_validation)
    assert model.x_log_flags == [False]
    assert model.y_log is False



class FakeParetoModel:
    def __init__(self):
        self.received_X = None
        self.received_index = None

    def predict(self, X, index=None):
        self.received_X = np.asarray(X).copy()
        self.received_index = index
        return np.ones(X.shape[0], dtype=float)


def test_engine_reuses_fold_fitted_scale_gm_and_ratio_plan():
    from hypatiax.tools.symbolic.symbolic_engine import SymbolicEngine

    engine = SymbolicEngine.__new__(SymbolicEngine)
    engine.model = FakeParetoModel()
    engine._last_fold_transform_state = {
        "input_feature_count": 2,
        "x_scales": [2.0, 1.0],
        "gm_pairs": [[0, 1]],
        "ratio_pairs": [[2, 1]],
        "y_std": 3.0,
        "best_index": 4,
        "feature_names": ["a", "b", "gm_a_b", "ratio_gm_a_b_b"],
    }
    X_validation = np.array([[8.0, 2.0], [18.0, 8.0]])
    prediction = engine.predict_fold_validation(X_validation)

    scaled = X_validation / np.array([2.0, 1.0])
    gm = np.sqrt(scaled[:, 0] * scaled[:, 1])
    with_gm = np.column_stack((scaled, gm))
    ratio = with_gm[:, 2] / (with_gm[:, 1] + 1e-300)
    expected = np.column_stack((with_gm, ratio))
    np.testing.assert_allclose(engine.model.received_X, expected)
    np.testing.assert_allclose(prediction, np.full(2, 3.0))
    assert engine.model.received_index == 4


def test_engine_rejects_validation_outside_fit_selected_positive_domain():
    from hypatiax.tools.symbolic.symbolic_engine import SymbolicEngine

    engine = SymbolicEngine.__new__(SymbolicEngine)
    engine.model = FakeParetoModel()
    engine._last_fold_transform_state = {
        "input_feature_count": 2,
        "x_scales": [1.0, 1.0],
        "gm_pairs": [[0, 1]],
        "ratio_pairs": [],
        "y_std": 1.0,
        "best_index": 0,
        "feature_names": ["a", "b", "gm_a_b"],
    }
    try:
        engine.predict_fold_validation(np.array([[1.0, -1.0]]))
    except ValueError as exc:
        assert "positive GM feature domain" in str(exc)
    else:
        raise AssertionError("positive-domain violation must fail closed")
