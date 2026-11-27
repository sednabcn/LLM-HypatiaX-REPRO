#!/usr/bin/env python3
"""Create a symbolic and routing provenance audit from saved 4060 JSON.

This is an offline report utility: it does not call an LLM, fit models, or execute
saved formulas. Symbolic equivalence is deliberately independent of R².
"""
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
    symbolic = adjudicate_symbolic_equivalence(
        hybrid.get("formula"),
        context.get("ground_truth_expression"),
        context.get("variable_names"),
        aliases if isinstance(aliases, dict) else None,
    )
    return {
        "equation_id": record.get("equation_id"),
        "seed": record.get("seed"),
        "symbolic_equivalence": symbolic,
        "llm_call_status": {
            "called": hybrid.get("llm_called"),
            "bypass_kind": hybrid.get("bypass_kind"),
            "source": hybrid.get("llm_source"),\n            "api_request_time_s": hybrid.get("llm_api_request_time_s"),\n            "temperature_sent": hybrid.get("llm_temperature_sent"),
            "formula_present": bool(hybrid.get("formula")),
        },
        "trust_gate": hybrid.get("trust_gate_diagnostics"),
        "route": {
            "decision": hybrid.get("decision"),
            "reason": hybrid.get("route_reason"),
            "structural_risk_tokens": (
                (hybrid.get("trust_gate_diagnostics") or {}).get("structural_risk_tokens")
            ),
            "blend_weights": hybrid.get("blend_weights"),
            "nn_selected_model": hybrid.get("nn_selected_model"),
            "nn_abstained": hybrid.get("nn_abstained"),
            "final_predictor_source": hybrid.get("selected_predictor_source"),
        },
        "scores": {
            "llm_train_r2": hybrid.get("llm_train_r2"),
            "llm_test_r2": hybrid.get("llm_test_r2"),
            "selected_predictor_train_r2": hybrid.get("selected_predictor_train_r2"),
            "selected_predictor_test_r2": hybrid.get("selected_predictor_test_r2"),
            "hybrid_test_r2": hybrid.get("test_r2"),
        },
        "audit_scope": {
            "formula_compared": "saved results.hybrid.formula (serialized from hybrid llm_code), not final selected predictor",\n            "constants_used": context.get("constants") or {},
            "ground_truth_source": context.get("ground_truth_source"),
            "ground_truth_excluded_from_prompt": context.get("ground_truth_excluded_from_prompt"),
            "split_protocol": record.get("split_protocol"),
            "audit_data_present": bool(record.get("audit_data")),
        },
    }


def build_audit(records: list[dict[str, Any]]) -> dict[str, Any]:
    cases = [audit_record(record) for record in records]
    counts: dict[str, int] = {}
    for case in cases:
        status = case["symbolic_equivalence"]["status"]
        counts[status] = counts.get(status, 0) + 1
    return {
        "schema_version": 2,
        "metric_definition": (
            "Exact symbolic identity after safe AST-to-SymPy conversion and explicit "
            "variable mapping. Predictive R2 is reported separately and is not a solve."
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
    args.output.write_text(json.dumps(_json_safe(report), indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Audited {report['case_count']} cases; symbolic statuses={report['symbolic_status_counts']}")


if __name__ == "__main__":
    main()
