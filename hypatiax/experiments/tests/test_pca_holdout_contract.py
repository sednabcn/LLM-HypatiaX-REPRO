"""Regression tests for genuine PCA holdout scoring and inference."""
import json
from pathlib import Path

import numpy as np
import pytest

from hypatiax.experiments.benchmarks.pca_holdout_utils import compose_hybrid_predictor
from scripts.ci.summarize_pca_holdout import build_summary


def test_pca_summary_uses_holdout_score_and_counts_missing_as_failure(tmp_path):
    pca_dir = tmp_path / "pca"
    pca_dir.mkdir()
    method_a = "EnhancedHybridSystemDeFi (core)"
    method_b = "HybridDiscoverySystem v50_2 (tools)"
    payload = {
        "tests": [
            {
                "description": "equation A",
                "domain": "feynman_mechanics",
                "results": {
                    method_a: {"success": True, "r2": 1.0, "metadata": {}},
                    method_b: {"success": True, "r2": 1.0, "metadata": {}},
                    "HybridSystemLLMNN all-domains (core)": {
                        "success": True, "r2": 1.0,
                        "metadata": {"provenance_status": "unverified_no_formula"},
                    },
                },
                "pca_test_r2": {method_a: 0.25, method_b: 0.9999999},
            },
            {
                "description": "equation B",
                "domain": "feynman_mechanics",
                "results": {
                    method_a: {"success": True, "r2": 1.0, "metadata": {}},
                    method_b: {"success": True, "r2": 1.0, "metadata": {}},
                },
                "pca_test_r2": {method_a: None, method_b: 0.8},
            },
        ]
    }
    (pca_dir / "protocol_core_noiseless_pca_test.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )

    summary = build_summary(pca_dir, threshold=0.999999, expected_equations=2)
    assert summary["per_method"][method_a]["n_pass"] == 0
    assert summary["per_method"][method_a]["n_total"] == 2
    assert summary["per_method"][method_a]["n_failed_or_unavailable"] == 1
    assert summary["per_method"][method_b]["n_pass"] == 1
    assert summary["per_method"][method_b]["n_total"] == 2
    assert summary["n_total"] == 4
    assert summary["train_fraction"] == 0.4
    assert "HybridSystemLLMNN all-domains (core)" in summary["excluded_methods"]


def test_pca_summary_rejects_duplicate_equation_records(tmp_path):
    pca_dir = tmp_path / "pca"
    pca_dir.mkdir()
    payload = {"tests": [{
        "description": "duplicate",
        "results": {},
        "pca_test_r2": {},
    }]}
    for name in ("protocol_core_noiseless_pca_a.json",
                 "protocol_core_noiseless_pca_b.json"):
        (pca_dir / name).write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate PCA equation"):
        build_summary(pca_dir, expected_equations=1)


def test_hybrid_predictor_reproduces_training_selected_ensemble():
    formula = lambda X: np.asarray(X)[:, 0] * 2.0
    nn = lambda X: np.asarray(X)[:, 0] * 4.0
    predictor = compose_hybrid_predictor(
        "ensemble", formula, nn, {"llm": 0.25, "nn": 0.75}
    )
    np.testing.assert_allclose(predictor(np.array([[1.0], [2.0]])), [3.5, 7.0])


def test_hybrid_predictor_fails_closed_when_selected_component_missing():
    assert compose_hybrid_predictor("ensemble", lambda X: X[:, 0], None,
                                    {"llm": 0.5, "nn": 0.5}) is None
    assert compose_hybrid_predictor("nn", None, None) is None


def test_hybrid_predictor_rejects_invalid_blend_weights():
    assert compose_hybrid_predictor("ensemble", lambda X: X[:, 0],
                                    lambda X: X[:, 0],
                                    {"llm": 0.8, "nn": 0.8}) is None
