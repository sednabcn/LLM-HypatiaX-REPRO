#!/usr/bin/env python3
"""Descriptive five-seed aggregation for the Core-15 Exp1 ablation.

This consumes completed per-seed outputs; it never runs PySR or calls an LLM.
The five seeds are repeated measurements of the same 15 equations. The report
therefore presents seed-level and equation-level summaries, not a pooled test
that treats 75 equation-seed observations as independent equations.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean, median, stdev

SEEDS = (42, 99, 123, 777, 2024)
EQUATIONS = 15
ARMS = ("pysr_only", "hypatia", "hypatia_nollm")
METRICS = ("test_r2", "extrap_r2_far", "total_time_s")


def finite_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def seed_directory(results_root: Path, seed: int) -> Path:
    return results_root / ("exp1_ablation" if seed == 42 else f"exp1_ablation_seed{seed}")


def load_seed(results_root: Path, seed: int):
    directory = seed_directory(results_root, seed)
    result_path = directory / "exp1_ablation_results.json"
    provenance_path = directory / "provenance_map_exp1.json"
    if not result_path.is_file() or not provenance_path.is_file():
        raise ValueError(f"seed {seed}: missing results or provenance in {directory}")
    results = json.loads(result_path.read_text(encoding="utf-8"))
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    if int(provenance.get("seed", -1)) != seed:
        raise ValueError(f"seed {seed}: provenance records seed={provenance.get('seed')!r}")
    if not provenance.get("benchmark_script_sha256"):
        raise ValueError(f"seed {seed}: missing benchmark_script_sha256")
    for eq_id in range(EQUATIONS):
        equation = results.get(str(eq_id))
        if not isinstance(equation, dict):
            raise ValueError(f"seed {seed}: missing equation id {eq_id}")
        for arm in ARMS:
            row = equation.get(arm)
            if not isinstance(row, dict) or row.get("completed") is not True:
                raise ValueError(f"seed {seed}: equation {eq_id} has no completed {arm} record")
    return results, provenance


def build_summary(results_by_seed, provenance_by_seed):
    hashes = {p["benchmark_script_sha256"] for p in provenance_by_seed.values()}
    revisions = {p.get("source_revision") for p in provenance_by_seed.values()}
    if len(hashes) != 1:
        raise ValueError(f"benchmark script hashes differ across seeds: {sorted(hashes)}")
    if len(revisions) != 1 or None in revisions:
        raise ValueError(f"source revisions differ or are missing across seeds: {sorted(str(x) for x in revisions)}")
    protocol_fields = ("engine_version", "populations", "niterations", "model_string", "flags")
    protocol = {}
    for field in protocol_fields:
        values = {json.dumps(p.get(field), sort_keys=True) for p in provenance_by_seed.values()}
        if len(values) != 1:
            raise ValueError(f"protocol field {field!r} differs across seeds")
        protocol[field] = provenance_by_seed[SEEDS[0]].get(field)
    for eq_id in range(EQUATIONS):
        first = results_by_seed[SEEDS[0]][str(eq_id)]
        expected_identity = (first.get("name"), first.get("domain"))
        for seed in SEEDS[1:]:
            row = results_by_seed[seed][str(eq_id)]
            if (row.get("name"), row.get("domain")) != expected_identity:
                raise ValueError(f"equation identity/domain differs for id {eq_id} at seed {seed}")

    records = []
    seed_summaries = {}
    equation_summaries = {}
    contrasts = (("hypatia_vs_pysr", "hypatia", "pysr_only"),
                 ("hypatia_vs_nollm", "hypatia", "hypatia_nollm"),
                 ("nollm_vs_pysr", "hypatia_nollm", "pysr_only"))

    for seed in SEEDS:
        results = results_by_seed[seed]
        arm_values = {arm: {metric: [] for metric in METRICS} for arm in ARMS}
        paired = {name: [] for name, _, _ in contrasts}
        for eq_id in range(EQUATIONS):
            equation = results[str(eq_id)]
            eq_name = equation.get("name", f"equation_{eq_id}")
            domain = equation.get("domain", "unknown")
            equation_summaries.setdefault(eq_name, {"domain": domain, "arms": {arm: {} for arm in ARMS}})
            for arm in ARMS:
                row = equation[arm]
                valid = row.get("success") is True
                values = {metric: finite_number(row.get(metric)) if valid else None for metric in METRICS}
                for metric, value in values.items():
                    if value is not None:
                        arm_values[arm][metric].append(value)
                records.append({
                    "seed": seed, "equation_id": eq_id, "equation": eq_name,
                    "domain": domain, "arm": arm, "completed": row.get("completed") is True,
                    "success": valid, "fit_status": row.get("fit_status"),
                    "evaluation_status": row.get("evaluation_status"),
                    **values,
                })
            for name, first, second in contrasts:
                a = equation[first]
                b = equation[second]
                av = finite_number(a.get("extrap_r2_far")) if a.get("success") is True else None
                bv = finite_number(b.get("extrap_r2_far")) if b.get("success") is True else None
                if av is not None and bv is not None:
                    paired[name].append(av - bv)
        seed_summaries[str(seed)] = {
            "arms": {
                arm: {
                    "n_success_test_r2": len(arm_values[arm]["test_r2"]),
                    "test_r2_mean": mean(arm_values[arm]["test_r2"]) if arm_values[arm]["test_r2"] else None,
                    "test_r2_median": median(arm_values[arm]["test_r2"]) if arm_values[arm]["test_r2"] else None,
                    "far_r2_n": len(arm_values[arm]["extrap_r2_far"]),
                    "far_r2_mean": mean(arm_values[arm]["extrap_r2_far"]) if arm_values[arm]["extrap_r2_far"] else None,
                    "far_r2_median": median(arm_values[arm]["extrap_r2_far"]) if arm_values[arm]["extrap_r2_far"] else None,
                    "time_n": len(arm_values[arm]["total_time_s"]),
                    "total_time_mean_s": mean(arm_values[arm]["total_time_s"]) if arm_values[arm]["total_time_s"] else None,
                } for arm in ARMS
            },
            "paired_far_r2_delta": {
                name: {"n_equations": len(values),
                       "mean": mean(values) if values else None,
                       "median": median(values) if values else None}
                for name, values in paired.items()
            },
        }

    for eq_id in range(EQUATIONS):
        eq = results_by_seed[SEEDS[0]][str(eq_id)]
        eq_name = eq.get("name", f"equation_{eq_id}")
        for arm in ARMS:
            for metric in METRICS:
                values = []
                by_seed = {}
                for seed in SEEDS:
                    row = results_by_seed[seed][str(eq_id)][arm]
                    value = finite_number(row.get(metric)) if row.get("success") is True else None
                    by_seed[str(seed)] = value
                    if value is not None:
                        values.append(value)
                equation_summaries[eq_name]["arms"][arm][metric] = {
                    "values_by_seed": by_seed,
                    "n_successful_seeds": len(values),
                    "mean": mean(values) if values else None,
                    "sd_sample": stdev(values) if len(values) > 1 else (0.0 if values else None),
                }

    across_seed = {}
    for arm in ARMS:
        for metric, key in (("test_r2", "test_r2_mean"), ("extrap_r2_far", "far_r2_mean"),
                            ("total_time_s", "total_time_mean_s")):
            vals = [seed_summaries[str(seed)]["arms"][arm][key] for seed in SEEDS]
            vals = [v for v in vals if v is not None]
            across_seed[f"{arm}.{metric}.seed_level_mean"] = {
                "n_seeds": len(vals), "mean": mean(vals) if vals else None,
                "sd_sample": stdev(vals) if len(vals) > 1 else (0.0 if vals else None),
            }
    for name, _, _ in contrasts:
        vals = [seed_summaries[str(seed)]["paired_far_r2_delta"][name]["mean"] for seed in SEEDS]
        vals = [v for v in vals if v is not None]
        across_seed[f"{name}.seed_level_mean_delta"] = {
            "n_seeds": len(vals), "mean": mean(vals) if vals else None,
            "sd_sample": stdev(vals) if len(vals) > 1 else (0.0 if vals else None),
        }

    return {
        "schema_version": 1,
        "experiment": "exp1_ablation_core15",
        "seeds": list(SEEDS),
        "n_equation_families": EQUATIONS,
        "n_equation_seed_units": EQUATIONS * len(SEEDS),
        "n_arm_records": len(records),
        "benchmark_script_sha256": next(iter(hashes)),
        "source_revision": next(iter(revisions)),
        "protocol": protocol,
        "seed_level_summary": seed_summaries,
        "equation_level_summary": equation_summaries,
        "across_seed_descriptive_summary": across_seed,
        "methodology": {
            "unit": "15 fixed equation families measured repeatedly at five seeds",
            "interpretation": "seeds are repeated measurements, not independent equation families",
            "inferential_tests": "none across seeds; descriptive mean and sample SD only",
            "failed_or_nonfinite_primary_evaluations": "preserved as null and excluded from metric means",
            "llm_contrast": "hypatia_vs_nollm is the incremental LLM-enabled Hybrid contrast, not standalone Pure LLM",
        },
    }, records


def write_outputs(summary, records, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "exp1_ablation_multiseed_summary.json"
    csv_path = output_dir / "exp1_ablation_multiseed_case_seed_records.csv"
    md_path = output_dir / "exp1_ablation_multiseed_report.md"
    json_path.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        fields = ["seed", "equation_id", "equation", "domain", "arm", "completed",
                  "success", "fit_status", "evaluation_status", "test_r2",
                  "extrap_r2_far", "total_time_s"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    lines = [
        "# Exp1 Core-15 five-seed descriptive summary", "",
        f"- Equation families: {summary['n_equation_families']}",
        f"- Repeated seeds: {', '.join(map(str, summary['seeds']))}",
        f"- Preserved arm records: {summary['n_arm_records']}",
        f"- Source revision: {summary['source_revision']}",
        f"- Benchmark script SHA-256: {summary['benchmark_script_sha256']}", "",
        "## Per-seed results", "",
        "| Seed | Arm | Successful test rows | Mean test R² | Mean far-OOD R² | Mean wall time (s) |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for seed in summary["seeds"]:
        for arm, values in summary["seed_level_summary"][str(seed)]["arms"].items():
            fmt = lambda value: "—" if value is None else f"{value:.4f}"
            lines.append(f"| {seed} | {arm} | {values['n_success_test_r2']} | "
                         f"{fmt(values['test_r2_mean'])} | {fmt(values['far_r2_mean'])} | "
                         f"{fmt(values['total_time_mean_s'])} |")
    lines += ["", "## Across-seed descriptive contrasts", "",
              "| Contrast | Seeds with paired data | Mean of seed-level mean Δ far-R² | Sample SD |",
              "|---|---:|---:|---:|"]
    for name in ("hypatia_vs_pysr", "hypatia_vs_nollm", "nollm_vs_pysr"):
        values = summary["across_seed_descriptive_summary"][f"{name}.seed_level_mean_delta"]
        fmt = lambda value: "—" if value is None else f"{value:.4f}"
        lines.append(f"| {name} | {values['n_seeds']} | {fmt(values['mean'])} | {fmt(values['sd_sample'])} |")
    lines += ["", "## Interpretation and limits", "",
              "The 15 equation families are measured repeatedly across five seeds. The 75 equation-seed units are not 75 independent equation families. This report therefore gives descriptive seed-level means and sample standard deviations only; it performs no pooled significance test.",
              "Failed primary evaluations remain visible in the case/seed CSV and are excluded from successful metric summaries. H−N estimates the incremental effect of enabling the LLM within the Hybrid pipeline, not a standalone Pure-LLM effect.", ""]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, csv_path, md_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path, default=Path("hypatiax/data/results/ablation"))
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    results_by_seed, provenance_by_seed = {}, {}
    for seed in SEEDS:
        results_by_seed[seed], provenance_by_seed[seed] = load_seed(args.results_root, seed)
    summary, records = build_summary(results_by_seed, provenance_by_seed)
    output_dir = args.output_dir or args.results_root / "exp1_ablation_multiseed"
    paths = write_outputs(summary, records, output_dir)
    print(f"PASS: {EQUATIONS} equation families x {len(SEEDS)} repeated seeds = {EQUATIONS * len(SEEDS)} equation-seed units")
    for path in paths:
        print(f"WROTE: {path}")


if __name__ == "__main__":
    main()
