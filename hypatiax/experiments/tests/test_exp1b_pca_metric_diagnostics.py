"""Regression tests for exp1b_pca missing-metric classification."""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
VALIDATOR_PATH = ROOT / "scripts/ci/exp1b_pca_seed_outputs.py"
BENCHMARK_PATH = ROOT / "hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("exp1b_pca_seed_outputs", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_constant_test_target_is_reported_as_undefined_not_feature_mismatch():
    validator = _load_validator()
    case = {
        "equation_id": "Optimal LP Position (Kelly)",
        "results": {
            "neural_network": {"test_r2": None, "test_r2_status": "constant_target"},
            "hybrid": {"test_r2": None, "test_r2_status": "constant_target"},
        },
    }
    assert validator.metric_undefined_reason(case, "neural_network") == "constant_target"
    assert validator.metric_undefined_reason(case, "hybrid") == "constant_target"


def test_exp1b_summary_declares_all_74_equations_not_portfolio_only():
    source = VALIDATOR_PATH.read_text(encoding="utf-8")
    assert '"task_filter": "all_74_equations"' in source
    assert '"nn_undefined_metrics": nn_undefined_metrics' in source
    assert '"hybrid_undefined_metrics": hybrid_undefined_metrics' in source
    assert '"nn_feature_mismatch_records": feature_mismatch_records' in source


def test_pca_benchmark_serializes_nonfinite_floats_as_strict_json_nulls():
    source = BENCHMARK_PATH.read_text(encoding="utf-8")
    assert "def _json_safe(value):" in source
    assert "number if _math.isfinite(number) else None" in source
    assert "allow_nan=False" in source
