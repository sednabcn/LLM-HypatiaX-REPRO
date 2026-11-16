from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "hypatiax" / "experiments" / "benchmarks" / "run_comparative_suite_benchmark_v2.py"


def test_far_evaluator_has_retained_predictor_and_reasoned_diagnostics():
    source = RUNNER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    evaluator = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "compute_extrap_r2_far"
    )
    names = {node.id for node in ast.walk(evaluator) if isinstance(node, ast.Name)}
    assert "predictor" in names
    for reason in (
        "method_failed",
        "unsupported_predictor",
        "formula_missing",
        "formula_evaluation_failed",
        "prediction_error",
        "prediction_length_mismatch",
        "nonfinite_prediction",
        "metric_error",
        "scored",
    ):
        assert reason in ast.get_source_segment(source, evaluator)


def test_far_diagnostics_are_persisted_to_protocol_and_flat_rows():
    source = RUNNER.read_text(encoding="utf-8")
    assert 'record["extrap_diagnostics"] = extrap_diagnostics' in source
    assert '"extrap_diagnostic": _diag_map.get(_mname)' in source
    assert '_row["extrap_diagnostic"] = _extrap_diag_map.get(_mname)' in source
