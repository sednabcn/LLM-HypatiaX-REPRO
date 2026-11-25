#!/usr/bin/env python3
"""Build a scientific, equation-keyed summary from validated Exp1 provenance shards.

This stage performs no model fitting or provider calls. It preserves every
seed/equation row, summarizes seeds within each equation, and never treats the
five repeated-seed measurements as 370 independent equations.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

EXPECTED_SEEDS = (42, 99, 123, 777, 2024)
EXPECTED_CASES = 74
ARMS = ("neural_network", "hybrid")
METRIC = "test_r2"


def _finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def _stats(values):
    xs = [_finite(v) for v in values]
    xs = [v for v in xs if v is not None]
    if not xs:
        return {"n_finite": 0, "mean": None, "median": None, "std": None,
                "min": None, "max": None}
    return {
        "n_finite": len(xs),
        "mean": statistics.fmean(xs),
        "median": statistics.median(xs),
        "std": statistics.stdev(xs) if len(xs) > 1 else 0.0,
        "min": min(xs),
        "max": max(xs),
    }


def _load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc


def _records(data, path):
    records = data if isinstance(data, list) else data.get("results", [])
    if not isinstance(records, list):
        raise ValueError(f"{path}: expected a list of case records")
    return records


def _result_file(root, manifest):
    name = manifest.get("result_file")
    if not isinstance(name, str) or not name:
        raise ValueError("manifest is missing result_file")
    matches = [p for p in root.rglob(Path(name).name) if p.is_file()]
    if len(matches) != 1:
        raise ValueError(f"{name}: expected exactly one matching artifact file, found {len(matches)}")
    path = matches[0]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != manifest.get("result_sha256"):
        raise ValueError(f"{path}: SHA-256 does not match seed manifest")
    return path


def aggregate(root: Path):
    root = root.resolve()
    manifests = sorted(root.rglob("exp1-provenance_seed*_manifest.json"))
    if len(manifests) != len(EXPECTED_SEEDS):
        raise ValueError(f"expected 5 seed manifests, found {len(manifests)}")

    by_seed = {}
    seed_manifests = {}
    for path in manifests:
        m = _load_json(path)
        seed = int(m.get("seed"))
        if seed not in EXPECTED_SEEDS or seed in by_seed:
            raise ValueError(f"{path}: unexpected or duplicate seed {seed}")
        if m.get("experiment_id") != "exp1-provenance" or m.get("status") != "passed":
            raise ValueError(f"{path}: seed manifest is not a passed exp1-provenance shard")
        if m.get("expected_case_count") != EXPECTED_CASES or m.get("observed_case_count") != EXPECTED_CASES:
            raise ValueError(f"{path}: expected 74/74 cases")
        result_path = _result_file(root, m)
        records = _records(_load_json(result_path), result_path)
        if len(records) != EXPECTED_CASES:
            raise ValueError(f"{result_path}: expected 74 records, found {len(records)}")
        seen = set()
        normalized = {}
        for rec in records:
            if not isinstance(rec, dict):
                raise ValueError(f"{result_path}: non-object record")
            eq = rec.get("equation_id")
            if not isinstance(eq, str) or not eq.strip() or eq in seen:
                raise ValueError(f"{result_path}: missing or duplicate equation_id {eq!r}")
            seen.add(eq)
            stamp = rec.get("seed")
            if str(stamp) != str(seed):
                raise ValueError(f"{result_path}: {eq!r} has seed stamp {stamp!r}, expected {seed}")
            normalized[eq] = rec
        if len(normalized) != EXPECTED_CASES:
            raise ValueError(f"{result_path}: equation ID coverage mismatch")
        by_seed[seed] = normalized
        seed_manifests[seed] = m

    if tuple(sorted(by_seed)) != EXPECTED_SEEDS:
        raise ValueError(f"expected seeds {EXPECTED_SEEDS}, found {tuple(sorted(by_seed))}")
    reference_ids = set(by_seed[EXPECTED_SEEDS[0]])
    for seed in EXPECTED_SEEDS[1:]:
        if set(by_seed[seed]) != reference_ids:
            missing = sorted(reference_ids - set(by_seed[seed]))
            extra = sorted(set(by_seed[seed]) - reference_ids)
            raise ValueError(f"seed {seed} equation IDs differ; missing={missing}, extra={extra}")

    case_rows = []
    by_equation = {}
    seed_summaries = {}
    route_counts = Counter()
    total_input_tokens = total_output_tokens = 0
    for seed in EXPECTED_SEEDS:
        seed_records = []
        paired_deltas = []
        arm_values = {arm: [] for arm in ARMS}
        statuses = Counter()
        metric_statuses = Counter()
        clipped_values = {arm: [] for arm in ARMS}
        for eq in sorted(reference_ids):
            rec = by_seed[seed][eq]
            results = rec.get("results") if isinstance(rec.get("results"), dict) else {}
            nn = results.get("neural_network") if isinstance(results.get("neural_network"), dict) else {}
            hy = results.get("hybrid") if isinstance(results.get("hybrid"), dict) else {}
            intractable = bool(rec.get("extrapolation_intractable", False))
            nn_r2 = _finite(nn.get(METRIC))
            hy_r2 = _finite(hy.get(METRIC))
            status = "intractable" if intractable else "standard"
            metric_status = (
                "undefined_both" if nn_r2 is None and hy_r2 is None else
                "undefined_nn" if nn_r2 is None else
                "undefined_hybrid" if hy_r2 is None else "finite_pair"
            )
            statuses[status] += 1
            metric_statuses[metric_status] += 1
            if nn_r2 is not None:
                arm_values["neural_network"].append(nn_r2)
                clipped_values["neural_network"].append(max(-10.0, min(1.0, nn_r2)))
            if hy_r2 is not None:
                arm_values["hybrid"].append(hy_r2)
                clipped_values["hybrid"].append(max(-10.0, min(1.0, hy_r2)))
            delta = (hy_r2 - nn_r2) if nn_r2 is not None and hy_r2 is not None else None
            if delta is not None:
                paired_deltas.append(delta)
            route = hy.get("decision") or hy.get("route") or hy.get("selected_route")
            if route is not None:
                route_counts[str(route)] += 1
            for key, target in (("llm_input_tokens", "input"), ("llm_output_tokens", "output")):
                value = _finite(hy.get(key))
                if value is not None:
                    if target == "input":
                        total_input_tokens += int(value)
                    else:
                        total_output_tokens += int(value)
            row = {
                "seed": seed, "equation_id": eq, "difficulty": rec.get("difficulty"),
                "formula_type": rec.get("formula_type"),
                "extrapolation_intractable": intractable, "case_status": status,
                "metric_status": metric_status,
                "nn_success": nn.get("success"), "hybrid_success": hy.get("success"),
                "nn_test_r2": nn_r2, "hybrid_test_r2": hy_r2,
                "nn_test_r2_clipped_minus10_1": None if nn_r2 is None else max(-10.0, min(1.0, nn_r2)),
                "hybrid_test_r2_clipped_minus10_1": None if hy_r2 is None else max(-10.0, min(1.0, hy_r2)),
                "hybrid_minus_nn_test_r2": delta,
                "hybrid_route": route,
                "hybrid_route_reason": hy.get("route_reason"),
                "hybrid_route_execution_status": hy.get("route_execution_status"),
                "nn_test_r2_source": nn.get("test_r2_source"),
                "hybrid_test_r2_source": hy.get("test_r2_source"),
                "nn_time_s": _finite(nn.get("time_s")),
                "hybrid_time_s": _finite(hy.get("time_s")),
                "nn_component_time_s": _finite(hy.get("nn_component_time_s")),
                "hybrid_component_time_s": _finite(hy.get("hybrid_component_time_s")),
                "llm_api_request_time_s": _finite(hy.get("llm_api_request_time_s")),
                "llm_input_tokens": _finite(hy.get("llm_input_tokens")),
                "llm_output_tokens": _finite(hy.get("llm_output_tokens")),
            }
            case_rows.append(row)
            seed_records.append(row)

        seed_summaries[str(seed)] = {
            "case_count": len(seed_records),
            "case_status_counts": dict(sorted(statuses.items())),
            "metric_status_counts": dict(sorted(metric_statuses.items())),
            "neural_network_test_r2": _stats(arm_values["neural_network"]),
            "hybrid_test_r2": _stats(arm_values["hybrid"]),
            "neural_network_test_r2_clipped_minus10_1": _stats(clipped_values["neural_network"]),
            "hybrid_test_r2_clipped_minus10_1": _stats(clipped_values["hybrid"]),
            "threshold_rates": {
                "nn_gt_0_9": sum(v > 0.9 for v in arm_values["neural_network"]) / len(arm_values["neural_network"]) if arm_values["neural_network"] else None,
                "hybrid_gt_0_9": sum(v > 0.9 for v in arm_values["hybrid"]) / len(arm_values["hybrid"]) if arm_values["hybrid"] else None,
                "nn_gt_0_99": sum(v > 0.99 for v in arm_values["neural_network"]) / len(arm_values["neural_network"]) if arm_values["neural_network"] else None,
                "hybrid_gt_0_99": sum(v > 0.99 for v in arm_values["hybrid"]) / len(arm_values["hybrid"]) if arm_values["hybrid"] else None,
            },
            "paired_hybrid_minus_nn_test_r2": _stats(paired_deltas),
            "paired_counts": {
                "n": len(paired_deltas),
                "hybrid_better": sum(x > 0 for x in paired_deltas),
                "tie": sum(x == 0 for x in paired_deltas),
                "hybrid_worse": sum(x < 0 for x in paired_deltas),
            },
        }

    for eq in sorted(reference_ids):
        rows = [r for r in case_rows if r["equation_id"] == eq]
        nn_vals = [r["nn_test_r2"] for r in rows]
        hy_vals = [r["hybrid_test_r2"] for r in rows]
        deltas = [r["hybrid_minus_nn_test_r2"] for r in rows]
        first = by_seed[EXPECTED_SEEDS[0]][eq]
        by_equation[eq] = {
            "difficulty": first.get("difficulty"),
            "formula_type": first.get("formula_type"),
            "extrapolation_intractable": bool(first.get("extrapolation_intractable", False)),
            "n_seed_records": len(rows),
            "neural_network_test_r2": _stats(nn_vals),
            "hybrid_test_r2": _stats(hy_vals),
            "paired_hybrid_minus_nn_test_r2": _stats(deltas),
            "neural_network_test_r2_clipped_minus10_1": _stats(r["nn_test_r2_clipped_minus10_1"] for r in rows),
            "hybrid_test_r2_clipped_minus10_1": _stats(r["hybrid_test_r2_clipped_minus10_1"] for r in rows),
            "seed_results": [
                {k: r[k] for k in ("seed", "case_status", "metric_status", "nn_success", "hybrid_success",
                                   "nn_test_r2", "hybrid_test_r2", "hybrid_minus_nn_test_r2",
                                   "hybrid_route")}
                for r in rows
            ],
        }

    all_deltas = [r["hybrid_minus_nn_test_r2"] for r in case_rows
                  if r["hybrid_minus_nn_test_r2"] is not None]
    status_counts = Counter(r["case_status"] for r in case_rows)
    summary = {
        "schema_version": 1,
        "experiment_id": "exp1-provenance",
        "source": "five validated per-seed result artifacts",
        "seeds": list(EXPECTED_SEEDS),
        "seed_count": len(EXPECTED_SEEDS),
        "unique_equation_count": len(reference_ids),
        "seed_equation_record_count": len(case_rows),
        "interpretation": (
            "The 370 rows are 74 repeated equation families measured under five seeds; "
            "seeds are repeated runs, not 370 independent equation families. "
            "Cross-seed summaries are calculated within equation_id. Clipped R² uses [-10, 1] "
            "and is reported separately from raw R²."
        ),
        "metric": METRIC,
        "case_status_counts_across_seed_records": dict(sorted(status_counts.items())),
        "metric_status_counts_across_seed_records": dict(sorted(Counter(r["metric_status"] for r in case_rows).items())),
        "per_seed": seed_summaries,
        "per_equation": by_equation,
        "paired_delta_across_seed_records_descriptive_only": {
            **_stats(all_deltas),
            "hybrid_better": sum(x > 0 for x in all_deltas),
            "tie": sum(x == 0 for x in all_deltas),
            "hybrid_worse": sum(x < 0 for x in all_deltas),
            "warning": "Descriptive repeated-seed pairs; not an independent-sample significance test.",
        },
        "hybrid_route_counts": dict(sorted(route_counts.items())),
        "hybrid_llm_token_totals": {
            "input": total_input_tokens, "output": total_output_tokens,
        },
        "provenance": {
            "seed_manifests": {
                str(seed): {
                    "result_file": seed_manifests[seed].get("result_file"),
                    "result_sha256": seed_manifests[seed].get("result_sha256"),
                    "script_sha256": seed_manifests[seed].get("script_sha256"),
                    "protocol_config_sha256": seed_manifests[seed].get("protocol_config_sha256"),
                    "repro_config_sha256": seed_manifests[seed].get("repro_config_sha256"),
                } for seed in EXPECTED_SEEDS
            }
        },
    }
    return summary, case_rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        summary, rows = aggregate(args.artifacts_dir)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        json_path = args.output_dir / "exp1-provenance_scientific_summary.json"
        csv_path = args.output_dir / "exp1-provenance_case_seed_records.csv"
        json_path.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        with csv_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"PASS: {len(summary['per_equation'])} equation families x {len(summary['seeds'])} seeds")
        print(f"PASS: wrote {json_path} and {csv_path} ({len(rows)} preserved rows)")
        with (args.output_dir / "exp1-provenance_scientific_summary.md").open("w", encoding="utf-8") as stream:
            stream.write("# Exp1 five-seed scientific summary\n\n")
            stream.write(f"- Unique equation families: {summary['unique_equation_count']}\n")
            stream.write(f"- Preserved seed/equation records: {summary['seed_equation_record_count']}\n")
            stream.write(f"- Seeds: {', '.join(map(str, summary['seeds']))}\n")
            stream.write("- Repeated seeds are not counted as independent equation families.\n")
            stream.write("- Undefined metrics and intractable cases remain explicit in the CSV and JSON.\n\n")
            stream.write("## Per-seed results\n\n")
            stream.write("| Seed | NN median test R² | Hybrid median test R² | NN mean clipped R² [-10,1] | Hybrid mean clipped R² [-10,1] | Paired n | Better / tie / worse |\n")
            stream.write("|---:|---:|---:|---:|---:|---:|---:|\n")
            for seed, s in summary["per_seed"].items():
                nn, hy, pair = s["neural_network_test_r2"], s["hybrid_test_r2"], s["paired_counts"]
                fmt = lambda x: "NA" if x is None else f"{x:.6f}"
                nn_clip = s["neural_network_test_r2_clipped_minus10_1"]["mean"]
                hy_clip = s["hybrid_test_r2_clipped_minus10_1"]["mean"]
                stream.write(f"| {seed} | {fmt(nn['median'])} | {fmt(hy['median'])} | {fmt(nn_clip)} | {fmt(hy_clip)} | {pair['n']} | {pair['hybrid_better']} / {pair['tie']} / {pair['hybrid_worse']} |\n")
            stream.write("\n## Interpretation limits\n\n")
            stream.write(summary["interpretation"] + "\n")
            stream.write("The paired delta counts are descriptive only; no inferential test treats seeds as independent samples.\n")
        with open(__import__("os").environ.get("GITHUB_STEP_SUMMARY", "/dev/null"), "a", encoding="utf-8") as stream:
            stream.write("## Exp1 scientific aggregation\n\n")
            stream.write(f"- Equation families: {summary['unique_equation_count']}\n")
            stream.write(f"- Seed/equation records: {len(rows)}\n")
            stream.write("- Output: JSON summary, CSV case-level records, Markdown report\n")
    except Exception as exc:
        print(f"ERROR: scientific aggregation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
