#!/usr/bin/env python3
"""Read-only diagnostics for symbolic gaps in committed DeFi 40/60 artifacts."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from audit_4060_reusable import SEEDS, load_records
from hypatiax.experiments.audit import audit_formula

def diagnose(protocol, records):
    grouped = {}
    for record in records:
        eq = str(record.get("equation_id"))
        ctx = record.get("formula_context") or {}
        hybrid = (record.get("results") or {}).get("hybrid") or {}
        variables = ctx.get("variable_names")
        formula = hybrid.get("formula")
        truth = ctx.get("ground_truth_expression")
        aliases = ctx.get("ground_truth_aliases")
        constants = ctx.get("constants")
        result = audit_formula(formula, truth, variables if isinstance(variables, list) else None,
                               aliases if isinstance(aliases, dict) else None,
                               constants if isinstance(constants, dict) else None)
        item = grouped.setdefault(eq, {
            "equation_id": eq, "seeds": [], "variable_names": variables,
            "ground_truth_expression": truth, "ground_truth_source": ctx.get("ground_truth_source"),
            "saved_formulas_by_seed": {}, "audit_results_by_seed": {}
        })
        if item["variable_names"] != variables or item["ground_truth_expression"] != truth:
            item["metadata_drift"] = True
        seed = str(record.get("seed"))
        item["seeds"].append(int(record.get("seed")))
        item["saved_formulas_by_seed"][seed] = formula
        item["audit_results_by_seed"][seed] = result
    selected = []
    for eq in sorted(grouped):
        item = grouped[eq]
        statuses = sorted({r.get("status", "missing") for r in item["audit_results_by_seed"].values()})
        if statuses != ["exact_symbolic_equivalent"]:
            item["seeds"] = sorted(item["seeds"])
            item["statuses"] = statuses
            selected.append(item)
    return {"protocol": protocol, "record_count": len(records), "equation_count": len(grouped),
            "non_universally_equivalent_equations": len(selected), "diagnostics": selected}

def render(report):
    lines = ["# DeFi 40/60 symbolic remediation diagnostics", "",
      "Read-only committed-artifact analysis. No experiments, training, or LLM calls. No aliases inferred and no source artifacts edited.", "",
      "| Protocol | Records | Equation families | Families needing review |",
      "|---|---:|---:|---:|"]
    for p in report["protocols"]:
        lines.append("| {} | {} | {} | {} |".format(p["protocol"], p["record_count"], p["equation_count"], p["non_universally_equivalent_equations"]))
    for p in report["protocols"]:
        lines += ["", "## " + p["protocol"], ""]
        for item in p["diagnostics"]:
            lines += ["### " + item["equation_id"], "",
              "- Seeds: " + ", ".join(map(str, item["seeds"])),
              "- Statuses: " + ", ".join(item["statuses"]),
              "- Variable names: " + json.dumps(item["variable_names"], ensure_ascii=False),
              "- Ground-truth source: " + str(item["ground_truth_source"]),
              "- Ground-truth expression: " + str(item["ground_truth_expression"]),
              "- Formulae and audit outcomes by seed:"]
            for seed in sorted(item["saved_formulas_by_seed"]):
                lines += ["  - Seed " + seed + " formula:"]
                lines += ["    " + line for line in (item["saved_formulas_by_seed"][seed] or "<missing>").splitlines()]
                lines += ["    Audit: " + json.dumps(item["audit_results_by_seed"][seed], ensure_ascii=False)]
            lines.append("")
    lines += ["## Remediation safeguards", "",
      "- Map aliases only when the original benchmark metadata or generator definition proves the mapping.",
      "- Extend the evaluator only for constructs with exact, safe semantics; otherwise retain not_assessable.",
      "- Change a generated formula or answer key only after verifying the original benchmark definition and intended domain semantics.",
      "- Keep all historical experiment JSON files unchanged.", ""]
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    protocols = [diagnose(name, load_records(name)) for name in ("random", "pca")]
    report = {"schema_version": 1, "seeds": list(SEEDS), "read_only": True,
              "experiments_rerun": False, "llm_calls": 0, "aliases_inferred": False,
              "protocols": protocols}
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    args.output_md.write_text(render(report), encoding="utf-8")
    for p in protocols:
        print("{}: {} records; {} families; {} need review".format(
            p["protocol"], p["record_count"], p["equation_count"], p["non_universally_equivalent_equations"]))

if __name__ == "__main__":
    main()
