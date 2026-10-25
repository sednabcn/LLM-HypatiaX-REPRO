"""OOD predictor must evaluate formulas that use engine-engineered ratio_/gm_ features."""
import numpy as np
import pytest
sp = pytest.importorskip("sympy")
hs = pytest.importorskip("hypatiax.tools.symbolic.hybrid_system_v50_2")


def _pred(formula, names=("A", "HA"), flags=(False, False)):
    return hs._make_original_space_predictor(sp.sympify(formula), list(names), list(names),
                                             list(flags), False, ["numpy"])


def test_ratio_feature_is_rebuilt():
    f = _pred("-0.43448144*log(ratio_HA_A) + 4.7475924")
    assert f is not None
    X = np.array([[2.0, 4.0], [1.0, 10.0]])
    np.testing.assert_allclose(f(X), -0.43448144 * np.log(X[:, 1] / X[:, 0]) + 4.7475924)


def test_geometric_mean_feature_is_rebuilt():
    f = _pred("2*gm_A_HA")
    np.testing.assert_allclose(f(np.array([[4.0, 9.0]])), [12.0])


def test_unknown_symbol_still_returns_none():
    assert _pred("foo + A") is None
    assert _pred("ratio_A_nope") is None
