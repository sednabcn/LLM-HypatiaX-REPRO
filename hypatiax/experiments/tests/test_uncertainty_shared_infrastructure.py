import json

import numpy as np
import pytest

from hypatiax.tools.uncertainty_methods import (
    UncertaintyEstimate,
    UncertaintyResult,
    UNCERTAINTY_METHODS,
    evaluate_estimate,
    write_uncertainty_results_json,
)


def test_estimate_validates_shapes_and_interval_pairing():
    estimate = UncertaintyEstimate(mean=[1, 2], lower=[0, 1], upper=[2, 3])
    assert estimate.validate(2) is estimate
    with pytest.raises(ValueError, match="lower and upper"):
        UncertaintyEstimate(lower=[0]).validate(1)
    with pytest.raises(ValueError, match="mean must contain"):
        UncertaintyEstimate(mean=[1, 2]).validate(1)


def test_estimate_allows_infinite_conservative_interval_bounds():
    estimate = UncertaintyEstimate(mean=[1, 2], lower=[-np.inf, 0], upper=[np.inf, 3])
    estimate.validate(2)


def test_estimate_rejects_negative_scale_and_bad_quantiles():
    with pytest.raises(ValueError, match="scale must be non-negative"):
        UncertaintyEstimate(scale=[-1]).validate(1)
    with pytest.raises(ValueError, match="Invalid quantile"):
        UncertaintyEstimate(quantiles={1.2: [0]}).validate(1)


def test_evaluate_estimate_reports_point_and_interval_metrics():
    estimate = UncertaintyEstimate(mean=[1, 2, 3], lower=[0, 1, 2], upper=[2, 3, 4])
    result = evaluate_estimate([1, 2, 4], estimate, nominal_coverage=0.9)
    assert result["n_evaluated"] == 3
    assert result["point_metrics"]["mae"] == pytest.approx(1 / 3)
    assert result["interval_metrics"]["empirical_coverage"] == 1.0


def test_evaluate_estimate_does_not_invent_point_metrics_or_intervals():
    result = evaluate_estimate([1, 2], UncertaintyEstimate(scale=[0.1, 0.2]))
    assert result["point_metrics"] == {}
    assert result["interval_metrics"] == {}


def test_result_export_is_versioned_and_json_safe(tmp_path):
    record = UncertaintyResult(
        method="demo",
        evaluation_domain="extra",
        n_evaluated=4,
        point_metrics={"rmse": float("inf")},
    )
    destination = write_uncertainty_results_json([record], tmp_path / "results.json")
    payload = json.loads(destination.read_text())
    assert payload["schema_version"] == "1.0"
    assert payload["records"][0]["point_metrics"]["rmse"] is None


def test_registry_register_create_and_duplicate_protection():
    registry = type(UNCERTAINTY_METHODS)("test")
    class Factory:
        def __init__(self, value=1):
            self.value = value
    registry.register("demo", Factory)
    assert registry.create("DEMO", value=3).value == 3
    assert registry.names() == ("demo",)
    with pytest.raises(KeyError, match="already registered"):
        registry.register("demo", Factory)
    with pytest.raises(KeyError, match="Unknown"):
        registry.create("missing")
