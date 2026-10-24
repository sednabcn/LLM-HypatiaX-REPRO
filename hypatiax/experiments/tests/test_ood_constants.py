import numpy as np
import pytest
sp = pytest.importorskip("sympy")
hs = pytest.importorskip("hypatiax.tools.symbolic.hybrid_system_v50_2")
C = {"N_A": 6.02214076e23, "k_B": 1.380649e-23}

def _pred(expr, names, consts):
    return hs._make_original_space_predictor(
        sp.sympify(expr), names, names, [False] * len(names), False, ["numpy"], constants=consts)

def test_named_constants_are_bound():
    f = _pred("n * N_A * k_B * T / V", ["n", "T", "V"], C)
    assert f is not None
    assert np.isclose(f(np.array([[1.0, 300.0, 2.0]]))[0], 8.314462618 * 300 / 2, rtol=1e-6)

def test_unknown_symbol_still_fails_loudly():
    assert _pred("n * Z_unknown", ["n"], C) is None

def test_input_column_is_not_overridden_by_a_constant():
    f = _pred("k * x", ["k", "x"], {"k": 1.380649e-23})
    assert np.isclose(f(np.array([[2.0, 3.0]]))[0], 6.0)
