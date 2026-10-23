import numpy as np, pytest
from hypatiax.experiments.tests.test_enhanced_defi_extrapolation import (
    _r2_reported, _r2_internal)
from hypatiax.core.generation.hybrid_defi_llm_nn.hybrid_ensemble_system_defi_domain import ensemble_llm_nn

def test_constant_target_is_nan_even_if_exact():
    y = np.full(50, 3.0)
    assert np.isnan(_r2_reported(y, y.copy())[0])      # rule A: never recovered
    assert np.isnan(_r2_reported(y, y + 0.1)[0])

def test_near_constant_target_is_nan():
    y = 3.0 + 1e-15 * np.arange(50)
    assert np.isnan(_r2_reported(y, y)[0])

def test_tiny_scale_still_scored():                    # the old 1e-10 guard failed this
    y = 1e-19 * np.random.default_rng(0).uniform(1, 2, 100)
    assert _r2_reported(y, y)[0] == pytest.approx(1.0)

def test_large_offset_not_perfect():
    rng = np.random.default_rng(0); y = 1e6 + rng.normal(0, 1, 200)
    assert _r2_reported(y, y + rng.normal(0, 5, 200))[0] < 0

def test_internal_never_nan():
    y = np.full(20, 2.0)
    assert _r2_internal(y, y) == 0.0

def test_ensemble_weights_do_not_use_test_labels():
    rng = np.random.default_rng(1)
    llm, nn = rng.normal(size=30), rng.normal(size=30)
    wd = (rng.normal(size=60), rng.normal(size=60), rng.normal(size=60))
    a, _ = ensemble_llm_nn(llm, nn, rng.normal(size=30), 0.5, 0.5, weight_data=wd)
    b, _ = ensemble_llm_nn(llm, nn, rng.normal(size=30) * 100, 0.5, 0.5, weight_data=wd)
    assert np.allclose(a, b)    # different y_test, identical blend
