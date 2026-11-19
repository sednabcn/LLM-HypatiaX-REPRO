#!/usr/bin/env python3
"""Fail-closed validator for the three-equation Exp2 extrapolation CI smoke."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _reject_constant(token: str) -> None:
    raise ValueError(f"non-standard JSON numeric token: {token}")


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)


def _find_nested_value(payload: Any, key: str) -> Any:
    """Find a provenance field in serialized method-result metadata."""
    if isinstance(payload, dict):
        if key in payload:
            return payload[key]
        for value in payload.values():
            found = _find_nested_value(value, key)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = _find_nested_value(value, key)
            if found is not None:
                return found
    return None


def _validate_hybrid_method(result: Any, description: str, expected: str) -> dict[str, Any]:
    """Fail closed unless method 6 provenance matches the requested engine."""
    if expected == "v60":
        return _validate_native_v60_method(result, description)
    benchmark = _find_nested_value(result, "benchmark_provenance")
    if not isinstance(benchmark, dict):
        raise ValueError(f"{description}: method 6 has no benchmark_provenance")
    if benchmark.get("engine") != "HybridDiscoverySystem":
        raise ValueError(f"{description}: method 6 did not identify HybridDiscoverySystem")
    if benchmark.get("engine_implementation") != "v50_2":
        raise ValueError(f"{description}: requested V50.2 but executed {benchmark.get('engine_implementation')!r}")
    if benchmark.get("engine_variant") not in {"llm_hybrid", "pysr_fallback"}:
        raise ValueError(f"{description}: unexpected V50.2 engine variant {benchmark.get('engine_variant')!r}")
    if _find_nested_value(result, "strategy") == "native_v60":
        raise ValueError(f"{description}: V50.2 result contains native V60 strategy")
    implementation = _find_nested_value(result, "implementation_provenance")
    if not isinstance(implementation, dict) or implementation.get("engine_family") != "hybrid_discovery":
        raise ValueError(f"{description}: method 6 lacks HybridDiscovery implementation provenance")
    if implementation.get("native_v60_pipeline") is True:
        raise ValueError(f"{description}: V50.2 result activated native V60")
    return {
        "engine_family": implementation["engine_family"],
        "engine_version": benchmark.get("engine_version"),
        "engine_implementation": "v50_2",
        "engine_variant": benchmark["engine_variant"],
        "native_v60_pipeline": False,
    }


def _validate_native_v60_method(result: Any, description: str) -> dict[str, Any]:
    """Fail closed unless method 6 records a completed native V60 handoff."""
    provenance = _find_nested_value(result, "implementation_provenance")
    if not isinstance(provenance, dict):
        raise ValueError(f"{description}: method 6 has no implementation_provenance")
    if provenance.get("engine_family") != "hybrid_discovery":
        raise ValueError(f"{description}: method 6 did not identify the HybridDiscovery engine")
    if provenance.get("native_v60_pipeline") is not True:
        raise ValueError(f"{description}: native V60 pipeline was not confirmed")
    if provenance.get("native_v60_production_handoff_enabled") is not True:
        raise ValueError(f"{description}: native V60 production handoff was not enabled")
    mode = provenance.get("implementation_mode")
    if not isinstance(mode, str) or not mode.startswith("native_v60"):
        raise ValueError(f"{description}: implementation mode is not native V60 (found {mode!r})")
    strategy = _find_nested_value(result, "strategy")
    if strategy != "native_v60":
        raise ValueError(f"{description}: method 6 strategy is not native_v60 (found {strategy!r})")
    final_model = _find_nested_value(result, "native_v60_final_model")
    if not isinstance(final_model, dict) or final_model.get("execution_status") != "selected":
        raise ValueError(f"{description}: native V60 final model was not selected")
    handoff = _find_nested_value(result, "native_v60_production_handoff")
    if not isinstance(handoff, dict) or handoff.get("status") != "active":
        raise ValueError(f"{description}: native V60 production handoff is not active")
    compatibility = _find_nested_value(result, "v50_2_compatibility_result")
    if not isinstance(compatibility, dict) or compatibility.get("status") != "not_executed":
        raise ValueError(f"{description}: V50.2 compatibility result is not explicitly marked not_executed")
    return {
        "engine_family": provenance["engine_family"],
        "engine_version": provenance.get("engine_version"),
        "implementation_mode": mode,
        "native_v60_pipeline": True,
        "strategy": strategy,
        "final_model_execution_status": final_model["execution_status"],
        "production_handoff_status": handoff["status"],
        "v50_2_compatibility_status": compatibility["status"],
    }

def validate_smoke_outputs(output_dir: Path, expected_equations: int = 3,
                            expected_methods: int = 6,
                            hybrid_implementation: str = "v50_2") -> dict[str, Any]:
    output_dir = Path(output_dir)
    protocol_files = sorted(output_dir.glob("protocol_core_extrap_*.json"))
    if len(protocol_files) != 1:
        raise ValueError(f"expected exactly one extrap protocol JSON, found {len(protocol_files)}")
    protocol_path = protocol_files[0]
    protocol = _load(protocol_path)
    methods = protocol.get("methods")
    tests = protocol.get("tests")
    if not isinstance(methods, list) or len(methods) != expected_methods or len(set(methods)) != expected_methods:
        raise ValueError(f"expected {expected_methods} unique methods; found {methods!r}")
    if not isinstance(tests, list) or not tests:
        raise ValueError("protocol tests must be a non-empty list")
    if protocol.get("total_tests") != len(tests):
        raise ValueError("protocol total_tests does not match the number of direction-specific test records")

    equation_names: list[str] = []
    direction_names: set[tuple[str, str]] = set()
    direction_labels: set[str] = set()
    method_rows = 0
    far_r2_available = 0
    far_rmse_available = 0
    far_error_pct_available = 0
    hybrid_method_audits: list[dict[str, Any]] = []
    diagnostic_status_counts: Counter[str] = Counter()
    for test in tests:
        description = str(test.get("description") or "")
        if not description:
            raise ValueError("equation/direction description is missing")
        if " [extrap:" in description and description.endswith("]"):
            equation_name, direction_name = description.rsplit(" [extrap:", 1)
            direction_name = direction_name[:-1]
        else:
            equation_name, direction_name = description, "legacy_default"
        if not equation_name or not direction_name or (equation_name, direction_name) in direction_names:
            raise ValueError(f"equation/direction description missing or duplicated: {description!r}")
        direction_names.add((equation_name, direction_name))
        direction_labels.add(direction_name)
        if equation_name not in equation_names:
            equation_names.append(equation_name)
        results = test.get("results")
        far_r2 = test.get("extrap_r2_far")
        far_rmse = test.get("extrap_rmse_far")
        far_error_pct = test.get("extrap_error_pct")
        diagnostics = test.get("extrap_diagnostics")
        prediction_audit = test.get("extrap_prediction_audit")
        if not isinstance(results, dict) or set(results) != set(methods):
            raise ValueError(f"{description}: missing one or more of the six method results")
        if not isinstance(far_r2, dict) or set(far_r2) != set(methods):
            raise ValueError(f"{description}: far-region R² map does not cover all methods")
        if not isinstance(far_rmse, dict) or set(far_rmse) != set(methods):
            raise ValueError(f"{description}: far-region RMSE map does not cover all methods")
        if not isinstance(far_error_pct, dict) or set(far_error_pct) != set(methods):
            raise ValueError(f"{description}: extrapolation error-percent map does not cover all methods")
        if not isinstance(diagnostics, dict) or set(diagnostics) != set(methods):
            raise ValueError(f"{description}: far-region diagnostic map does not cover all methods")
        if not isinstance(prediction_audit, dict) or set(prediction_audit) != set(methods):
            raise ValueError(f"{description}: prediction-audit map does not cover all methods")
        if int(test.get("extrap_n_train") or 0) < 2 or int(test.get("extrap_n_test") or 0) < 2:
            raise ValueError(f"{description}: extrapolation split has fewer than two rows in a region")
        for method in methods:
            result = results[method]
            if not isinstance(result, dict) or not isinstance(result.get("success"), bool):
                raise ValueError(f"{description}/{method}: missing method success status")
            if method == methods[-1]:
                hybrid_method_audits.append(_validate_hybrid_method(result, f"{description}/{method}", hybrid_implementation))
            if "r2" not in result or "rmse" not in result:
                raise ValueError(f"{description}/{method}: missing ordinary R²/RMSE scores")
            if method not in far_r2 or method not in far_rmse:
                raise ValueError(f"{description}/{method}: missing far-region scores")
            far_r2_available += far_r2[method] is not None
            far_rmse_available += far_rmse[method] is not None
            far_error_pct_available += far_error_pct[method] is not None
            audit = prediction_audit[method]
            if not isinstance(audit, dict) or not isinstance(audit.get("verification_status"), str):
                raise ValueError(f"{description}/{method}: missing prediction-audit status")
            if audit["verification_status"] == "recomputed_from_aligned_far_predictions":
                y_true = audit.get("y_true")
                y_pred = audit.get("y_pred")
                row_count = int(test.get("extrap_n_test") or 0)
                if (not isinstance(y_true, list) or not isinstance(y_pred, list)
                        or len(y_true) != row_count or len(y_pred) != row_count
                        or audit.get("row_count") != row_count):
                    raise ValueError(f"{description}/{method}: prediction arrays are not aligned to the far split")
                try:
                    yt = [float(value) for value in y_true]
                    yp = [float(value) for value in y_pred]
                except (TypeError, ValueError):
                    raise ValueError(f"{description}/{method}: prediction arrays contain non-numeric values")
                if not all(math.isfinite(value) for value in yt + yp):
                    raise ValueError(f"{description}/{method}: prediction arrays contain non-finite values")
                recomputed_rmse = math.sqrt(sum((a - b) ** 2 for a, b in zip(yt, yp)) / row_count)
                stored_rmse = audit.get("rmse")
                if stored_rmse is None or not math.isclose(float(stored_rmse), recomputed_rmse, rel_tol=1e-9, abs_tol=1e-12):
                    raise ValueError(f"{description}/{method}: audited RMSE does not match row-level predictions")
                if far_rmse[method] is None or not math.isclose(float(far_rmse[method]), recomputed_rmse, rel_tol=1e-9, abs_tol=1e-12):
                    raise ValueError(f"{description}/{method}: published far RMSE does not match row-level predictions")
                from hypatiax.core.r2_canonical import r2_scored
                recomputed_r2, _ = r2_scored(yt, yp)
                expected_r2 = float(recomputed_r2) if math.isfinite(float(recomputed_r2)) else None
                audited_r2 = audit.get("r2")
                if expected_r2 is None:
                    if audited_r2 is not None or far_r2[method] is not None:
                        raise ValueError(f"{description}/{method}: undefined audited R² must remain null")
                elif (audited_r2 is None or far_r2[method] is None
                      or not math.isclose(float(audited_r2), expected_r2, rel_tol=1e-9, abs_tol=1e-12)
                      or not math.isclose(float(far_r2[method]), expected_r2, rel_tol=1e-9, abs_tol=1e-12)):
                    raise ValueError(f"{description}/{method}: published far R² does not match row-level predictions")
                if not isinstance(audit.get("prediction_source"), str) or not audit["prediction_source"]:
                    raise ValueError(f"{description}/{method}: prediction source is missing")
            else:
                if audit.get("y_true") is not None or audit.get("y_pred") is not None:
                    raise ValueError(f"{description}/{method}: unavailable prediction audit must not contain partial arrays")
                if audit["verification_status"] != "predictions_unavailable":
                    raise ValueError(f"{description}/{method}: unsupported prediction-audit status")
            diagnostic = diagnostics[method]
            if not isinstance(diagnostic, dict) or not isinstance(diagnostic.get("status"), str):
                raise ValueError(f"{description}/{method}: missing far-region diagnostic status")
            if "extrap_nrmse_far" in diagnostic:
                score = diagnostic.get("extrap_nrmse_far")
                scale = diagnostic.get("extrap_target_scale_train")
                if diagnostic.get("extrap_nrmse_far_status") == "available":
                    if score is None or scale is None or float(scale) <= 0.0:
                        raise ValueError(f"{description}/{method}: normalized far score has no positive training scale")
                    expected_score = float(far_rmse[method]) / float(scale)
                    if far_rmse[method] is None or not math.isclose(float(score), expected_score, rel_tol=1e-9, abs_tol=1e-12):
                        raise ValueError(f"{description}/{method}: normalized far score does not match RMSE_far / training target scale")
                elif score is not None:
                    raise ValueError(f"{description}/{method}: unavailable normalized far score must be null")
            diagnostic_status_counts[diagnostic["status"]] += 1
            method_rows += 1

    if len(equation_names) != expected_equations:
        raise ValueError(
            f"expected {expected_equations} distinct equations; found {len(equation_names)}"
        )

    flat_files = sorted(output_dir.glob("benchmark_results_extrap*.json"))
    if len(flat_files) != 1:
        raise ValueError(f"expected exactly one flat extrap benchmark JSON, found {len(flat_files)}")
    flat_rows = _load(flat_files[0])
    if not isinstance(flat_rows, list) or len(flat_rows) != len(tests) * expected_methods:
        raise ValueError("flat extrap benchmark must contain one method row per direction-specific test")
    counts: Counter[tuple[str, str, str]] = Counter()
    expected = {
        (str(test.get("domain") or ""), str(test.get("description") or ""), method)
        for test in tests for method in methods
    }
    expected_audits = {
        (str(test.get("domain") or ""), str(test.get("description") or ""), method):
            (test.get("extrap_prediction_audit") or {}).get(method)
        for test in tests for method in methods
    }
    for row in flat_rows:
        identity = (str(row.get("domain") or ""), str(row.get("test") or ""), str(row.get("method") or ""))
        counts[identity] += 1
        if "r2" not in row or "rmse" not in row or "extrap_r2_far" not in row or "extrap_rmse_far" not in row:
            raise ValueError(f"flat row {identity} is missing ordinary or far-region score fields")
        if row.get("extrap_prediction_audit") != expected_audits.get(identity):
            raise ValueError(f"flat row {identity} does not preserve its protocol prediction audit")
        matching_test = next(test for test in tests if str(test.get("domain") or "") == identity[0] and str(test.get("description") or "") == identity[1])
        diagnostic = (matching_test.get("extrap_diagnostics") or {}).get(identity[2], {})
        for field in ("extrap_nrmse_far", "extrapolation_score", "extrap_nrmse_far_status"):
            if row.get(field) != diagnostic.get(field):
                raise ValueError(f"flat row {identity} does not preserve normalized extrapolation field {field}")
    if set(counts) != expected or any(count != 1 for count in counts.values()):
        raise ValueError("flat extrap rows do not provide exactly one row per equation/method pair")

    return {
        "status": "complete",
        "step": "exp2_feynman_extrap_smoke",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "equation_count": len(equation_names),
        "direction_count": len(direction_labels),
        "equation_direction_count": len(direction_names),
        "method_count": expected_methods,
        "method_equation_rows": method_rows,
        "hybrid_implementation": hybrid_implementation,
        "method_6_implementation_audits": hybrid_method_audits,
        "method_6_implementation_verified_count": len(hybrid_method_audits),
        "equations": equation_names,
        "methods": methods,
        "far_r2_non_null_count": far_r2_available,
        "far_rmse_non_null_count": far_rmse_available,
        "far_error_pct_non_null_count": far_error_pct_available,
        "far_diagnostic_status_counts": dict(sorted(diagnostic_status_counts.items())),
        "prediction_audit_verified_count": sum(1 for test in tests for status in test["extrap_prediction_audit"].values() if status.get("verification_status") == "recomputed_from_aligned_far_predictions"),
        "prediction_audit_unavailable_count": sum(1 for test in tests for status in test["extrap_prediction_audit"].values() if status.get("verification_status") == "predictions_unavailable"),
        "protocol_file": {"name": protocol_path.name, "sha256": hashlib.sha256(protocol_path.read_bytes()).hexdigest()},
        "flat_file": {"name": flat_files[0].name, "sha256": hashlib.sha256(flat_files[0].read_bytes()).hexdigest()},
        "note": "Null far scores are retained as explicit method outcomes; missing score fields or rows fail validation.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--summary-name", default="exp2_extrap_smoke_summary.json")
    parser.add_argument("--hybrid-implementation", choices=("v50_2", "v60"), default="v50_2")
    args = parser.parse_args()
    summary = validate_smoke_outputs(args.output_dir, hybrid_implementation=args.hybrid_implementation)
    target = args.output_dir / args.summary_name
    target.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"[exp2-extrap-smoke] PASS: {summary['equation_count']} equations x {summary['method_count']} methods")
    print(f"[exp2-extrap-smoke] far R² available: {summary['far_r2_non_null_count']}/{summary['method_equation_rows']}")
    print(f"[exp2-extrap-smoke] far RMSE available: {summary['far_rmse_non_null_count']}/{summary['method_equation_rows']}")
    print(f"[exp2-extrap-smoke] error-% available: {summary['far_error_pct_non_null_count']}/{summary['method_equation_rows']}")
    print(f"[exp2-extrap-smoke] diagnostic statuses: {summary['far_diagnostic_status_counts']}")
    print(f"[exp2-extrap-smoke] row-level prediction audits verified/unavailable: {summary['prediction_audit_verified_count']}/{summary['prediction_audit_unavailable_count']}")
    print(f"[exp2-extrap-smoke] {args.hybrid_implementation} method-6 provenance verified: {summary['method_6_implementation_verified_count']}/{summary['equation_direction_count']}")
    print(f"[exp2-extrap-smoke] summary: {target}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        raise SystemExit(f"::error::Exp2 extrapolation smoke validation failed: {exc}")
