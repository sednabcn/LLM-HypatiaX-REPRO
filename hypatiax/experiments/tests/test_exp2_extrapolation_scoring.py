"""Regression contracts for the shared Exp2 far-extrapolation scorer.

These tests are offline: they exercise only deterministic formula evaluation and
metric reporting, without loading benchmark backends or calling an LLM.
"""
from types import SimpleNamespace

import numpy as np
import pytest

from hypatiax.experiments.benchmarks.exp2_extrapolation_core import (
    _runner_eval_formula,
    build_extrap_split,
    compute_extrap_r2_far,
)


def test_runner_formula_evaluator_imports_regex_and_scores_expression():
    X = np.array([[1.0], [2.0], [3.0]])
    predicted = _runner_eval_formula("x + 1", X, ["x"])
    np.testing.assert_allclose(predicted, [2.0, 3.0, 4.0])




def test_def_formula_uses_named_columns_when_holdout_has_extra_engineered_features():
    X = np.array([
        [2.0, 3.0, 5.0, 99.0],
        [4.0, 7.0, 2.0, 88.0],
    ])
    formula = """def formula(m1, m2, r):
    return m1 * m2 / r**2
"""
    predicted = _runner_eval_formula(formula, X, ["m1", "m2", "r", "ratio_m1_m2"])
    np.testing.assert_allclose(predicted, [0.24, 7.0])


def test_def_formula_maps_named_parameters_independent_of_feature_column_order():
    X = np.array([
        [5.0, 2.0, 3.0],
        [2.0, 4.0, 7.0],
    ])
    formula = """def formula(m1, m2, r):
    return m1 * m2 / r**2
"""
    predicted = _runner_eval_formula(formula, X, ["r", "m1", "m2"])
    np.testing.assert_allclose(predicted, [0.24, 7.0])


def test_far_rmse_is_preserved_when_far_r2_is_catastrophic():
    X_far = np.array([[1.0], [2.0], [3.0]])
    y_far = np.array([1.0, 2.0, 3.0])
    result = SimpleNamespace(success=True, formula="1000 * x")

    r2, rmse, error_pct = compute_extrap_r2_far(
        {"symbolic": result},
        X_far,
        y_far,
        ["x"],
    )

    assert r2["symbolic"] is None
    assert rmse["symbolic"] == pytest.approx(
        np.sqrt(np.mean((y_far - 1000.0 * X_far[:, 0]) ** 2))
    )
    assert error_pct["symbolic"] is None


def test_extrap_split_is_disjoint_and_reports_expected_coverage():
    X = np.arange(200, dtype=float).reshape(-1, 1)
    y = X[:, 0] ** 2
    X_train, y_train, X_far, y_far, metadata = build_extrap_split(
        X, y, train_frac=0.8, multiplier=2.0
    )
    assert len(X_train) == 160
    assert len(X_far) == 40
    assert X_train[:, 0].max() < X_far[:, 0].min()
    assert metadata["extrap_n_train"] == 160
    assert metadata["extrap_n_test"] == 40


@pytest.mark.parametrize(
    "kwargs",
    [
        {"train_frac": 0.0},
        {"train_frac": 1.0},
        {"train_frac": float("nan")},
        {"multiplier": 0.0},
        {"multiplier": -1.0},
    ],
)
def test_extrap_split_rejects_invalid_protocol_parameters(kwargs):
    X = np.arange(20, dtype=float).reshape(-1, 1)
    y = X[:, 0] ** 2
    with pytest.raises(ValueError):
        build_extrap_split(X, y, **kwargs)


def test_extrap_split_rejects_empty_or_too_small_far_region():
    X = np.arange(200, dtype=float).reshape(-1, 1)
    y = X[:, 0] ** 2
    with pytest.raises(ValueError, match="far region"):
        build_extrap_split(X, y, train_frac=0.8, multiplier=0.001)


def test_both_active_feynman_runners_fail_closed_on_invalid_extrapolation_splits():
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    bench = root / "hypatiax" / "experiments" / "benchmarks"
    core_source = (bench / "exp2_extrapolation_core.py").read_text()
    assert "if split < 2 or n - split < 2:" in core_source
    assert "if len(X_far) < 2:" in core_source
    assert "rmse_far = _far_rmse(y_far, y_far_pred)" in core_source
    for filename in (
        "run_comparative_suite_benchmark_v2.py",
        "run_comparative_suite_benchmark_pca.py",
    ):
        source = (bench / filename).read_text()
        assert "raise RuntimeError(" in source
        assert "refusing an in-sample fallback" in source
        assert "build_extrap_split(" in source


def test_feynman_output_identity_includes_domain_and_timestamp_precision():
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    for filename in (
        "run_comparative_suite_benchmark_v2.py",
        "run_comparative_suite_benchmark_pca.py",
    ):
        source = (root / "hypatiax/experiments/benchmarks" / filename).read_text()
        assert '_new_keys = {(r.get("domain"), r["test"], r["method"])' in source
        assert '_ext_new_keys = {(r.get("domain"), r["test"], r["method"])' in source
        assert 'datetime.now().strftime("%Y%m%d_%H%M%S_%f")' in source


def _load_exp2_worker_validator():
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    script = root / "scripts/ci/validate_exp2_extrap_worker.py"
    spec = importlib.util.spec_from_file_location("validate_exp2_extrap_worker", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_synthetic_extrap_worker_outputs(tmp_path):
    import json
    import os
    from pathlib import Path

    methods = [f"method-{index}" for index in range(6)]
    tests = []
    rows = []
    for equation in ("equation-A", "equation-B"):
        tests.append({
            "description": equation,
            "domain": "domain-A",
            "results": {method: {"success": True} for method in methods},
            "extrap_r2_far": {method: 0.9 for method in methods},
            "extrap_rmse_far": {method: 0.1 for method in methods},
            "extrap_n_train": 8,
            "extrap_n_test": 2,
        })
        for method in methods:
            rows.append({
                "test": equation,
                "domain": "domain-A",
                "method": method,
                "success": True,
                "extrap_r2_far": 0.9,
                "extrap_rmse_far": 0.1,
            })
    marker = tmp_path / "run-start.marker"
    marker.touch()
    protocol = tmp_path / "protocol_core_extrap_test.json"
    protocol.write_text(json.dumps({
        "total_tests": len(tests),
        "methods": methods,
        "tests": tests,
    }))
    benchmark = tmp_path / "benchmark_results_extrap.json"
    benchmark.write_text(json.dumps(rows))
    future_ns = marker.stat().st_mtime_ns + 1_000_000
    os.utime(protocol, ns=(future_ns, future_ns))
    os.utime(benchmark, ns=(future_ns, future_ns))
    return marker, methods, rows


def test_exp2_worker_validator_accepts_complete_method_equation_coverage(tmp_path):
    module = _load_exp2_worker_validator()
    marker, methods, rows = _write_synthetic_extrap_worker_outputs(tmp_path)
    summary = module.validate_worker_outputs(tmp_path, marker, ["domain-A"])
    assert summary["worker_outputs_complete"] is True
    assert summary["method_count"] == 6
    assert summary["equation_count"] == 2
    assert summary["expected_method_equation_rows"] == 12


def test_exp2_worker_validator_rejects_missing_method_rows(tmp_path):
    import json
    import pytest

    module = _load_exp2_worker_validator()
    marker, methods, rows = _write_synthetic_extrap_worker_outputs(tmp_path)
    rows.pop()
    (tmp_path / "benchmark_results_extrap.json").write_text(json.dumps(rows))
    future_ns = marker.stat().st_mtime_ns + 2_000_000
    import os
    os.utime(tmp_path / "benchmark_results_extrap.json", ns=(future_ns, future_ns))
    with pytest.raises(ValueError, match="missing"):
        module.validate_worker_outputs(tmp_path, marker, ["domain-A"])


def test_retained_predictor_supplies_training_baseline_on_training_rows_only():
    X_train = np.array([[0.0], [1.0], [2.0]])
    y_train = np.array([1.1, 2.1, 3.1])
    X_far = np.array([[3.0], [4.0], [5.0]])
    y_far = np.array([5.0, 6.0, 7.0])
    seen = []

    def predict(X):
        values = np.asarray(X, dtype=float).copy()
        seen.append(values)
        return values[:, 0] + 1.0

    result = SimpleNamespace(success=True, formula="N/A", _predict_fn=predict)
    diagnostics = {}
    _, _, error_pct = compute_extrap_r2_far(
        {"retained": result},
        X_far,
        y_far,
        ["x"],
        y_train=y_train,
        X_train_predictor=X_train,
        verbose=False,
        diagnostics=diagnostics,
    )

    assert error_pct["retained"] == pytest.approx(1000.0)
    np.testing.assert_array_equal(seen[0], X_far)
    np.testing.assert_array_equal(seen[1], X_train)
    assert diagnostics["retained"]["error_pct_status"] == "available"


def test_zero_training_rmse_keeps_ratio_undefined_with_explicit_status():
    X_train = np.array([[0.0], [1.0], [2.0]])
    X_far = np.array([[3.0], [4.0], [5.0]])
    predict = lambda X: np.asarray(X)[:, 0] + 1.0
    result = SimpleNamespace(success=True, formula="N/A", _predict_fn=predict)
    diagnostics = {}
    _, _, error_pct = compute_extrap_r2_far(
        {"retained": result},
        X_far,
        np.array([4.0, 5.0, 6.0]),
        ["x"],
        y_train=np.array([1.0, 2.0, 3.0]),
        X_train_predictor=X_train,
        verbose=False,
        diagnostics=diagnostics,
    )
    assert error_pct["retained"] is None
    assert diagnostics["retained"]["error_pct_status"] == "zero_training_rmse"


def test_extrap_split_supports_each_feature_without_dropping_other_columns():
    X = np.column_stack([
        np.arange(100, dtype=float),
        np.arange(100, dtype=float)[::-1],
        np.arange(100, dtype=float) * 3.0,
    ])
    y = X[:, 0] + X[:, 1]
    for feature_index, feature_name in enumerate(("a", "b", "c")):
        X_train, y_train, X_far, y_far, metadata = build_extrap_split(
            X, y, train_frac=0.8, multiplier=2.0, feature_index=feature_index
        )
        assert X_train.shape[1] == X.shape[1]
        assert X_far.shape[1] == X.shape[1]
        assert metadata["extrap_direction"] == f"feature_{feature_index}"
        assert metadata["extrap_feature_index"] == feature_index
        assert X_train[:, feature_index].max() < X_far[:, feature_index].min()
        assert len(y_train) == len(X_train)
        assert len(y_far) == len(X_far)


def test_joint_extrap_split_uses_all_feature_percentile_ranks():
    X = np.column_stack([
        np.arange(100, dtype=float),
        np.arange(100, dtype=float) * 10.0,
        np.arange(100, dtype=float)[::-1],
    ])
    y = X.sum(axis=1)
    X_train, y_train, X_far, y_far, metadata = build_extrap_split(
        X, y, train_frac=0.8, multiplier=2.0, feature_index=None
    )
    assert metadata["extrap_direction"] == "joint_mean_percentile"
    assert metadata["extrap_direction_score"] == "mean_empirical_percentile"
    assert X_train.shape[1] == X.shape[1] == X_far.shape[1]
    assert len(y_train) == len(X_train)
    assert len(y_far) == len(X_far)


def test_extrap_split_rejects_out_of_range_feature_index():
    X = np.arange(40, dtype=float).reshape(20, 2)
    y = X.sum(axis=1)
    with pytest.raises(ValueError, match="feature_index"):
        build_extrap_split(X, y, feature_index=2)
