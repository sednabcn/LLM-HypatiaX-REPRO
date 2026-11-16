#!/usr/bin/env python3
"""Fail-closed validator for the three-equation Exp2 extrapolation CI smoke."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _reject_constant(token: str) -> None:
    raise ValueError(f"non-standard JSON numeric token: {token}")


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)


def validate_smoke_outputs(output_dir: Path, expected_equations: int = 3,
                            expected_methods: int = 6) -> dict[str, Any]:
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
    if not isinstance(tests, list) or len(tests) != expected_equations:
        raise ValueError(f"expected exactly {expected_equations} equations; found {len(tests) if isinstance(tests, list) else 'invalid'}")
    if protocol.get("total_tests") != expected_equations:
        raise ValueError("protocol total_tests does not match the expected equation count")

    equation_names: list[str] = []
    method_rows = 0
    far_r2_available = 0
    far_rmse_available = 0
    far_error_pct_available = 0
    diagnostic_status_counts: Counter[str] = Counter()
    for test in tests:
        description = str(test.get("description") or "")
        if not description or description in equation_names:
            raise ValueError(f"equation description missing or duplicated: {description!r}")
        equation_names.append(description)
        results = test.get("results")
        far_r2 = test.get("extrap_r2_far")
        far_rmse = test.get("extrap_rmse_far")
        far_error_pct = test.get("extrap_error_pct")
        diagnostics = test.get("extrap_diagnostics")
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
        if int(test.get("extrap_n_train") or 0) < 2 or int(test.get("extrap_n_test") or 0) < 2:
            raise ValueError(f"{description}: extrapolation split has fewer than two rows in a region")
        for method in methods:
            result = results[method]
            if not isinstance(result, dict) or not isinstance(result.get("success"), bool):
                raise ValueError(f"{description}/{method}: missing method success status")
            if "r2" not in result or "rmse" not in result:
                raise ValueError(f"{description}/{method}: missing ordinary R²/RMSE scores")
            if method not in far_r2 or method not in far_rmse:
                raise ValueError(f"{description}/{method}: missing far-region scores")
            far_r2_available += far_r2[method] is not None
            far_rmse_available += far_rmse[method] is not None
            far_error_pct_available += far_error_pct[method] is not None
            diagnostic = diagnostics[method]
            if not isinstance(diagnostic, dict) or not isinstance(diagnostic.get("status"), str):
                raise ValueError(f"{description}/{method}: missing far-region diagnostic status")
            diagnostic_status_counts[diagnostic["status"]] += 1
            method_rows += 1

    flat_files = sorted(output_dir.glob("benchmark_results_extrap*.json"))
    if len(flat_files) != 1:
        raise ValueError(f"expected exactly one flat extrap benchmark JSON, found {len(flat_files)}")
    flat_rows = _load(flat_files[0])
    if not isinstance(flat_rows, list) or len(flat_rows) != expected_equations * expected_methods:
        raise ValueError("flat extrap benchmark must contain exactly 18 equation/method rows")
    counts: Counter[tuple[str, str, str]] = Counter()
    expected = {
        (str(test.get("domain") or ""), str(test.get("description") or ""), method)
        for test in tests for method in methods
    }
    for row in flat_rows:
        identity = (str(row.get("domain") or ""), str(row.get("test") or ""), str(row.get("method") or ""))
        counts[identity] += 1
        if "r2" not in row or "rmse" not in row or "extrap_r2_far" not in row or "extrap_rmse_far" not in row:
            raise ValueError(f"flat row {identity} is missing ordinary or far-region score fields")
    if set(counts) != expected or any(count != 1 for count in counts.values()):
        raise ValueError("flat extrap rows do not provide exactly one row per equation/method pair")

    return {
        "status": "complete",
        "step": "exp2_feynman_extrap_smoke",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "equation_count": expected_equations,
        "method_count": expected_methods,
        "method_equation_rows": method_rows,
        "equations": equation_names,
        "methods": methods,
        "far_r2_non_null_count": far_r2_available,
        "far_rmse_non_null_count": far_rmse_available,
        "far_error_pct_non_null_count": far_error_pct_available,
        "far_diagnostic_status_counts": dict(sorted(diagnostic_status_counts.items())),
        "protocol_file": {"name": protocol_path.name, "sha256": hashlib.sha256(protocol_path.read_bytes()).hexdigest()},
        "flat_file": {"name": flat_files[0].name, "sha256": hashlib.sha256(flat_files[0].read_bytes()).hexdigest()},
        "note": "Null far scores are retained as explicit method outcomes; missing score fields or rows fail validation.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--summary-name", default="exp2_extrap_smoke_summary.json")
    args = parser.parse_args()
    summary = validate_smoke_outputs(args.output_dir)
    target = args.output_dir / args.summary_name
    target.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"[exp2-extrap-smoke] PASS: {summary['equation_count']} equations x {summary['method_count']} methods")
    print(f"[exp2-extrap-smoke] far R² available: {summary['far_r2_non_null_count']}/{summary['method_equation_rows']}")
    print(f"[exp2-extrap-smoke] far RMSE available: {summary['far_rmse_non_null_count']}/{summary['method_equation_rows']}")
    print(f"[exp2-extrap-smoke] error-% available: {summary['far_error_pct_non_null_count']}/{summary['method_equation_rows']}")
    print(f"[exp2-extrap-smoke] diagnostic statuses: {summary['far_diagnostic_status_counts']}")
    print(f"[exp2-extrap-smoke] summary: {target}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        raise SystemExit(f"::error::Exp2 extrapolation smoke validation failed: {exc}")
