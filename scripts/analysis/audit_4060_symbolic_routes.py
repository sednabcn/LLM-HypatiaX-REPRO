#!/usr/bin/env python3
"""Build an offline symbolic-equivalence and route-provenance audit for 4060 JSON."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from hypatiax.experiments.symbolic_equivalence import adjudicate_symbolic_equivalence


def audit_record(record: dict[str, Any]) -> dict[str, Any]:
    context = record.get("formula_context") or {}
    results = record.get("results") or {}
    hybrid = results.get("hybrid") or {}
    aliases = context.get("ground_truth_aliases")
    constants = context.get("constants")
    symbolic = adjudicate_symbolic_equivalence(
        hybrid.get("formula"),
        context.get("ground_truth_expression"),
        context.get("variable_names"),
        aliases if isinstance(aliases, dict) else None,
        constants if isinstance(constants, dict) else None,
    )
    return {
        "equation_id": record.get("equation_id"),
        "seed": record.get("seed"),
        "symbolic_equivalence": symbolic,
        "llm_call_status": {
            "called": hybrid.get("llm_called"),
            "bypass_kind": hybrid.get("bypass_kind"),
            "source": hybrid.get("llm_source"),
            "api_request_time_s": hybrid.get("llm_api_request_time_s"),
            "temperature_sent": hybrid.get("llm_temperature_sent"),
            "formula_present": bool(hybrid.get("formula")),
        },
        "trust_gate": hybrid.get("trust_gate_diagnostics"),
        "route": {
            "decision": hybrid.get("decision"),
            "reason": hybrid.get("route_reason"),
            "execution_status": hybrid.get("route_execution_status"),
            "structural_risk_flag": hybrid.get("structural_risk_flag"),
            "structural_risk_tokens": hybrid.get("structural_risk_tokens"),
            "llm_degradation_status": hybrid.get("llm_degradation_status"),
            "llm_degradation_delta": hybrid.get("llm_degradation_delta"),
            "degradation_tau": hybrid.get("degradation_tau"),
            "ood_diagnostic": hybrid.get("ood_diagnostic"),
            "ood_covariate_protocol": hybrid.get("ood_covariate_protocol"),
            "blend_weights": hybrid.get("blend_weights"),
            "nn_selected_model": hybrid.get("nn_selected_model"),
            "nn_abstained": hybrid.get("nn_abstained"),
            "nn_edge_r2": hybrid.get("nn_edge_r2"),
            "ridge_edge_r2": hybrid.get("ridge_edge_r2"),
            "signed_ridge_edge_r2": hybrid.get("signed_ridge_edge_r2"),
            "nn_prediction_validation": hybrid.get("nn_prediction_validation"),
            "final_predictor_source": hybrid.get("selected_predictor_source"),
        },
        "scores": {
            "llm_train_r2": hybrid.get("llm_train_r2"),
            "llm_test_r2": hybrid.get("llm_test_r2"),
            "ensemble_train_r2": hybrid.get("ensemble_train_r2"),
            "ensemble_test_r2": hybrid.get("ensemble_test_r2"),
            "selected_predictor_train_r2": hybrid.get("selected_predictor_train_r2"),
            "selected_predictor_test_r2": hybrid.get("selected_predictor_test_r2"),
            "hybrid_test_r2": hybrid.get("test_r2"),
        },
        "audit_scope": {
            "formula_compared": (
                "saved results.hybrid.formula (serialized from hybrid llm_code), "
                "not final selected predictor"
            ),
            "ground_truth_source": context.get("ground_truth_source"),
            "ground_truth_excluded_from_prompt": context.get("ground_truth_excluded_from_prompt"),
            "constants_used": constants or {},
            "split_protocol": record.get("split_protocol"),
            "audit_data_present": bool(record.get("audit_data")),
            "audit_data_shapes": _audit_data_shapes(record.get("audit_data")),
        },
    }


def _audit_data_shapes(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    result = {}
    for key in ("X_train", "y_train", "X_test", "y_test"):
        value = data.get(key)
        if isinstance(value, list):
            result[key] = {
                "rows": len(value),
                "columns": len(value[0]) if value and isinstance(value[0], list) else 1,
            }
    return result


def build_audit(records: list[dict[str, Any]]) -> dict[str, Any]:
    cases = [audit_record(record) for record in records]
    counts: dict[str, int] = {}
    for case in cases:
        status = case["symbolic_equivalence"]["status"]
        counts[status] = counts.get(status, 0) + 1
    return {
        "schema_version": 3,
        "metric_definition": (
            "Exact symbolic identity after safe AST-to-SymPy conversion with explicit "
            "variable aliases and protocol constants. Predictive R2 is separate."
        ),
        "case_count": len(cases),
        "symbolic_status_counts": counts,
        "cases": cases,
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="saved benchmark results JSON")
    parser.add_argument("--output", type=Path, required=True, help="audit JSON output")
    args = parser.parse_args()
    records = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise SystemExit("input must be a JSON list of benchmark records")
    report = build_audit(records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(_json_safe(report), indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(f"Audited {report['case_count']} cases; symbolic statuses={report['symbolic_status_counts']}")


if __name__ == "__main__":
    main()
