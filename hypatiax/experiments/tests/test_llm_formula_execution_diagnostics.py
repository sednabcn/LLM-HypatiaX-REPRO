"""Tests for calibration-only formula execution failure diagnostics."""
import numpy as np
import pytest

from hypatiax.experiments.benchmarks import hypatiax_defi_benchmark_v3c as benchmark
from hypatiax import safe_formula


@pytest.fixture
def parser(monkeypatch):
    def install(fn):
        monkeypatch.setattr(safe_formula, "parse_formula", lambda *_a, **_k: fn)
    return install


def test_parse_error_is_distinguished(monkeypatch):
    def fail(*_a, **_k):
        raise SyntaxError("bad formula")
    monkeypatch.setattr(safe_formula, "parse_formula", fail)
    result = benchmark._execute_formula_diagnostic("bad", np.ones((4, 1)))
    assert result["failure_reason"] == "parse_error"
    assert "SyntaxError" in result["detail"]


def test_execution_error_is_distinguished(parser):
    def fn(x):
        raise RuntimeError("cannot evaluate")
    parser(fn)
    result = benchmark._execute_formula_diagnostic("f", np.arange(4.0).reshape(-1, 1))
    assert result["failure_reason"] == "execution_error"
    assert result["execution_mode"] == "rowwise"


def test_invalid_output_shape_is_distinguished(parser):
    parser(lambda x: np.ones((len(x), 2)))
    result = benchmark._execute_formula_diagnostic("f", np.arange(4.0).reshape(-1, 1))
    assert result["failure_reason"] == "invalid_output_shape"
    assert result["output_shape"] == [4, 2]


def test_excessive_nonfinite_predictions_are_distinguished(parser):
    parser(lambda x: np.array([1.0, np.nan, np.inf, 4.0]))
    result = benchmark._execute_formula_diagnostic("f", np.arange(4.0).reshape(-1, 1))
    assert result["failure_reason"] == "excessive_nonfinite_predictions"


def test_constant_predictions_are_distinguished(parser):
    parser(lambda x: np.ones_like(x))
    result = benchmark._execute_formula_diagnostic("f", np.arange(4.0).reshape(-1, 1))
    assert result["failure_reason"] == "constant_predictions"


def test_success_reports_execution_mode_and_repairs_small_nonfinite_fraction(parser):
    parser(lambda x: np.where(np.asarray(x) == 0, np.nan, np.asarray(x) + 1.0))
    result = benchmark._execute_formula_diagnostic("f", np.arange(20.0).reshape(-1, 1))
    assert result["ok"] is True
    assert result["execution_mode"] == "vectorized"
    assert result["nonfinite_fraction"] == pytest.approx(0.05)
