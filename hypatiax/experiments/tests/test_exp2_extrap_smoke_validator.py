from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "ci" / "validate_exp2_extrap_smoke.py"
SPEC = importlib.util.spec_from_file_location("exp2_extrap_smoke_validator", SCRIPT)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)

METHODS = [f"method_{i}" for i in range(1, 7)]


def _write_fixture(output_dir: Path, *, omit_far_rmse: bool = False) -> None:
    tests = []
    flat = []
    for eq in range(1, 4):
        description = f"equation_{eq}"
        results = {
            method: {"success": True, "r2": 0.99, "rmse": 0.01}
            for method in METHODS
        }
        far_r2 = {method: 0.9 for method in METHODS}
        far_rmse = {method: 0.02 for method in METHODS}
        if omit_far_rmse:
            far_rmse.pop(METHODS[-1])
        tests.append({
            "description": description,
            "domain": "feynman_mechanics",
            "results": results,
            "extrap_r2_far": far_r2,
            "extrap_rmse_far": far_rmse,
            "extrap_error_pct": {method: 10.0 for method in METHODS},
            "extrap_diagnostics": {method: {"status": "scored"} for method in METHODS},
            "extrap_n_train": 96,
            "extrap_n_test": 24,
        })
        for method in METHODS:
            flat.append({
                "test": description,
                "domain": "feynman_mechanics",
                "method": method,
                "r2": 0.99,
                "rmse": 0.01,
                "extrap_r2_far": 0.9,
                "extrap_rmse_far": 0.02,
                "extrap_error_pct": 10.0,
                "extrap_diagnostic": {"status": "scored"},
            })
    (output_dir / "protocol_core_extrap_smoke.json").write_text(
        json.dumps({"methods": METHODS, "total_tests": 3, "tests": tests}),
        encoding="utf-8",
    )
    (output_dir / "benchmark_results_extrap.json").write_text(
        json.dumps(flat), encoding="utf-8"
    )


def test_three_equation_six_method_smoke_artifacts_validate(tmp_path):
    _write_fixture(tmp_path)
    summary = validator.validate_smoke_outputs(tmp_path)
    assert summary["equation_count"] == 3
    assert summary["method_count"] == 6
    assert summary["method_equation_rows"] == 18
    assert summary["far_r2_non_null_count"] == 18
    assert summary["far_rmse_non_null_count"] == 18
    assert summary["far_error_pct_non_null_count"] == 18
    assert summary["far_diagnostic_status_counts"] == {"scored": 18}


def test_smoke_rejects_missing_far_metric_for_one_method(tmp_path):
    _write_fixture(tmp_path, omit_far_rmse=True)
    try:
        validator.validate_smoke_outputs(tmp_path)
    except ValueError as exc:
        assert "far-region RMSE map" in str(exc)
    else:
        raise AssertionError("validator accepted an incomplete far-RMSE map")


def test_smoke_rejects_incomplete_flat_method_coverage(tmp_path):
    _write_fixture(tmp_path)
    flat_path = tmp_path / "benchmark_results_extrap.json"
    rows = json.loads(flat_path.read_text(encoding="utf-8"))
    flat_path.write_text(json.dumps(rows[:-1]), encoding="utf-8")
    try:
        validator.validate_smoke_outputs(tmp_path)
    except ValueError as exc:
        assert "exactly 18" in str(exc)
    else:
        raise AssertionError("validator accepted fewer than 18 flat rows")
