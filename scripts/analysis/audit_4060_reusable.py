#!/usr/bin/env python3
"""Offline retrospective symbolic and routing audit of committed DeFi 40/60 artifacts.

This script reads saved JSON only. It does not train models, call an LLM, or
invoke any experiment runner. Symbolic comparisons use the reusable audit API.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from hypatiax.experiments.audit import audit_formula

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "hypatiax/data/results/comparison_results/noise-noiseless/noiseless"
SEEDS = (42, 99, 123, 777, 2024)
CASES_PER_SEED = 74


def artifact_path(protocol: str, seed: int) -> Path:
    if protocol == "random":
        name = (
            "hypatiax_defi_benchmark_v3c_4060_results.json"
            if seed == 42
            else f"hypatiax_defi_benchmark_v3c_4060_results_seed{seed}.json"
        )
        return RESULTS / "defi_random_4060" / name
    return RESULTS / "defi_pca" / f"hypatiax_defi_benchmark_pca_results_seed{seed}.json"


def load_records(protocol: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for seed in SEEDS:
        path = artifact_path(protocol, seed)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list) or len(payload) != CASES_PER_SEED:
            raise ValueError(f"{path}: expected {CASES_PER_SEED} records")
        for index, record in enumerate(payload):
            if record.get("seed") != seed:
                raise ValueError(f"{path}[{index}]: seed does not match filename")
            if not record.get("equation_id"):
                raise ValueError(f"{path}[{index}]: missing equation_id")
            records.append(record)
    return records


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def audit_protocol(protocol: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    cases = []
    status_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    route_decisions: Counter[str] = Counter()
    predictor_sources: Counter[str] = Counter()
    selected_scores: list[float] = []
    hybrid_scores: list[float] = []
    ground_truth_count = formula_count = 0
    identified: set[tuple[str, int]] = set()

    for record in records:
        context = record.get("formula_context") or {}
        hybrid = (record.get("results") or {}).get("hybrid") or {}
        formula = hybrid.get("formula")
        ground_truth = context.get("ground_truth_expression")
        variables = context.get("variable_names")
        aliases = context.get("ground_truth_aliases")
        constants = context.get("constants")
        result = audit_formula(
            formula,
            ground_truth,
            variables if isinstance(variables, list) else None,
            aliases if isinstance(aliases, dict) else None,
            constants if isinstance(constants, dict) else None,
        )
        status = result.get("status", "missing_status")
        status_counts[status] += 1
        if result.get("reason"):
            reason_counts[result["reason"]] += 1
        if ground_truth:
            ground_truth_count += 1
        if isinstance(formula, str) and formula.strip():
            formula_count += 1

        decision = hybrid.get("decision") or "unspecified"
        source = hybrid.get("selected_predictor_source") or "unspecified"
        route_decisions[decision] += 1
        predictor_sources[source] += 1

        selected = hybrid.get("selected_predictor_test_r2")
        raw_hybrid = hybrid.get("test_r2")
        if finite(selected):
            selected_scores.append(float(selected))
        if finite(raw_hybrid):
            hybrid_scores.append(float(raw_hybrid))

        cases.append({
            "equation_id": record.get("equation_id"),
            "seed": record.get("seed"),
            "symbolic_equivalence": result,
            "ground_truth_source": context.get("ground_truth_source"),
            "ground_truth_excluded_from_prompt": context.get("ground_truth_excluded_from_prompt"),
            "split_protocol": (record.get("split_protocol") or {}).get("name"),
            "llm_called": hybrid.get("llm_called"),
            "route_decision": decision,
            "route_reason": hybrid.get("route_reason"),
            "selected_predictor_source": source,
            "selected_predictor_test_r2": selected if finite(selected) else None,
            "hybrid_test_r2": raw_hybrid if finite(raw_hybrid) else None,
        })
        if record.get("equation_id") is not None and record.get("seed") is not None:
            identified.add((str(record["equation_id"]), int(record["seed"])))

    def stats(values: list[float]) -> dict[str, Any]:
        if not values:
            return {"n_finite": 0, "median": None, "mean": None}
        return {
            "n_finite": len(values),
            "median": statistics.median(values),
            "mean": statistics.fmean(values),
        }

    return {
        "protocol": protocol,
        "case_count": len(records),
        "seed_coverage": list(SEEDS),
        "ground_truth_present": ground_truth_count,
        "formula_present": formula_count,
        "unique_equation_seed_pairs": len(identified),
        "symbolic_status_counts": dict(sorted(status_counts.items())),
        "symbolic_reason_counts": dict(sorted(reason_counts.items())),
        "route_decision_counts": dict(sorted(route_decisions.items())),
        "selected_predictor_source_counts": dict(sorted(predictor_sources.items())),
        "selected_predictor_test_r2": stats(selected_scores),
        "hybrid_test_r2": stats(hybrid_scores),
        "cases": cases,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Retrospective DeFi 40/60 symbolic and routing audit",
        "",
        f"**Audit date:** {report['audit_date']}",
        "**Method:** reusable `hypatiax.experiments.audit.audit_formula` API",
        "**Execution scope:** read-only analysis of committed JSON; no training, experiment reruns, or LLM calls",
        "",
        "## Coverage and symbolic results",
        "",
        "| Protocol | Cases | Seeds | Ground truth | Saved formulas | Symbolic status counts |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for p in report["protocols"]:
        statuses = ", ".join(f"{k}: {v}" for k, v in p["symbolic_status_counts"].items())
        lines.append(
            f"| {p['protocol']} | {p['case_count']} | {len(p['seed_coverage'])} | "
            f"{p['ground_truth_present']} | {p['formula_present']} | {statuses or 'none'} |"
        )
    lines.extend(["", "## Selected predictor and hybrid score summaries", "",
        "| Protocol | Selected predictor finite n | Median selected test R² | Hybrid finite n | Median hybrid test R² |",
        "|---|---:|---:|---:|---:|"])
    for p in report["protocols"]:
        s, h = p["selected_predictor_test_r2"], p["hybrid_test_r2"]
        lines.append(
            f"| {p['protocol']} | {s['n_finite']} | {s['median']} | "
            f"{h['n_finite']} | {h['median']} |"
        )
    lines.extend(["", "## Route decisions", ""])
    for p in report["protocols"]:
        lines.append(f"### {p['protocol']}")
        lines.append("")
        for route, count in p["route_decision_counts"].items():
            lines.append(f"- {route}: {count}")
        lines.append("")
    lines.extend([
        "## Interpretation safeguards",
        "",
        "- Symbolic status is computed from the saved generated formula and the persisted ground-truth expression using the reusable restricted AST/SymPy evaluator.",
        "- Missing or unmapped variables remain not assessable; no aliases are inferred from variable names, formula text, or benchmark scores.",
        "- Symbolic equivalence is distinct from predictive R² and does not establish domain/branch equivalence.",
        "- Route-selected predictor metrics are reported separately from the hybrid formula score.",
        "- Historical result files are read only and are not modified.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    protocols = []
    for protocol in ("random", "pca"):
        protocols.append(audit_protocol(protocol, load_records(protocol)))
    report = {
        "schema_version": 1,
        "audit_date": "2026-11-28",
        "repository": "sednabcn/LLM-HypatiaX-REPRO",
        "method": "hypatiax.experiments.audit.audit_formula",
        "read_only": True,
        "experiments_rerun": False,
        "llm_calls": 0,
        "protocols": protocols,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    for p in protocols:
        print(
            f"{p['protocol']}: cases={p['case_count']}; "
            f"ground_truth={p['ground_truth_present']}; "
            f"symbolic={p['symbolic_status_counts']}; "
            f"selected_score={p['selected_predictor_test_r2']}"
        )
    print(f"JSON report: {args.output_json}")
    print(f"Markdown report: {args.output_md}")


if __name__ == "__main__":
    main()
