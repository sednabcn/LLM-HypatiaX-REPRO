"""Offline tests for trustworthy DeFi metric recomputation.

These tests do not instantiate workers, fit models, or call an LLM.
"""
import numpy as np
import pytest

from hypatiax.experiments.benchmarks.run_comparative_suite_benchmark_v2 import (
    _recompute_prediction_metrics,
)


def test_metrics_are_recomputed_from_one_aligned_prediction_vector():
    y_true = np.array([1.0, 2.0, 3.0, 4.0])
    y_pred = np.array([1.5, 2.5, 3.5, 4.5])

    r2, rmse, status = _recompute_prediction_metrics(y_true, y_pred)

    assert status == "ok"
    assert r2 == pytest.approx(0.8)
    assert rmse == pytest.approx(0.5)


def test_metric_recomputation_rejects_prediction_length_mismatch():
    with pytest.raises(ValueError, match="prediction length mismatch"):
        _recompute_prediction_metrics(
            np.array([1.0, 2.0, 3.0]),
            np.array([1.0, 2.0]),
        )


def test_metric_recomputation_rejects_nonfinite_inputs():
    with pytest.raises(ValueError, match="non-finite"):
        _recompute_prediction_metrics(
            np.array([1.0, 2.0, 3.0]),
            np.array([1.0, np.nan, 3.0]),
        )
