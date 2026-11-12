#!/usr/bin/env python3
"""Validate and merge one complete five-shard manuscript Protocol-30 run.

Worker manifests bind each 1-based runner equation index to the Protocol30
registry identity assembled in the same sorted-domain order as the benchmark.
Method failures remain in the merged records; they are never imputed.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def fail(message: str) -> None:
    raise SystemExit(f"Protocol-30 aggregate validation failed: {message}")


def aggregate(artifacts_dir: Path, output_dir: Path, variant: str) -> None:
    expected_indices = set(range(1, 31))
    expected_shards = set(range(5))
    shard_manifests = {}
    shard_payloads = {}
    identities = {}

    for manifest_path in sorted(artifacts_dir.rglob("protocol30_shard_manifest.json")):
        manifest = load_json(manifest_path)
        if manifest.get("experiment") != variant:
            continue
        shard = manifest.get("shard_index")
        if not isinstance(shard, int) or shard not in expected_shards:
            fail(f"{manifest_path}: invalid shard_index {shard!r}")
        if shard in shard_manifests:
            fail(f"duplicate manifest for shard {shard}")
        assigned = manifest.get("assigned_equation_indices")
        if not isinstance(assigned, list) or not assigned:
            fail(f"{manifest_path}: empty/missing assigned_equation_indices")
        if any(not isinstance(i, int) or i not in expected_indices for i in assigned):
            fail(f"{manifest_path}: invalid equation indices {assigned!r}")
        if len(assigned) != len(set(assigned)):
            fail(f"{manifest_path}: duplicate assigned equation indices")
        expected_assignment = list(range(shard * 6 + 1, shard * 6 + 7))
        if sorted(assigned) != expected_assignment:
            fail(f"{manifest_path}: shard {shard} must own indices {expected_assignment}, got {sorted(assigned)}")
        shard_manifests[shard] = manifest

        mapping = manifest.get("equation_identities")
        if not isinstance(mapping, list) or {x.get("index") for x in mapping} != set(assigned):
            fail(f"{manifest_path}: identity map does not match assigned indices")
        for item in mapping:
            idx = item["index"]
            if idx in identities:
                fail(f"equation index {idx} assigned to multiple shards")
            identities[idx] = item

        result_name = manifest.get("result_file")
        if not isinstance(result_name, str) or Path(result_name).name != result_name:
            fail(f"{manifest_path}: missing/unsafe result_file")
        result_path = manifest_path.parent / result_name
        if not result_path.is_file() or not result_name.startswith("protocol_core_") or "aggregate" in result_name:
            fail(f"shard {shard}: declared detailed result file is absent or invalid: {result_name!r}")
        payload = load_json(result_path)
        if not isinstance(payload.get("tests"), list):
            fail(f"{result_path}: missing tests list")
        if len(payload["tests"]) != len(assigned):
            fail(f"shard {shard}: {len(payload['tests'])} records for {len(assigned)} assigned equations")
        shard_payloads[shard] = payload

    if set(shard_manifests) != expected_shards:
        fail(f"expected shards {sorted(expected_shards)}, found {sorted(shard_manifests)}")
    if set(identities) != expected_indices:
        fail(f"equation coverage incomplete; missing {sorted(expected_indices - set(identities))}")

    common_protocol = None
    common_methods = None
    merged_records = {}
    for shard in sorted(expected_shards):
        manifest = shard_manifests[shard]
        payload = shard_payloads[shard]
        if manifest.get("expected_equation_count") != 30 or manifest.get("n_shards") != 5:
            fail(f"shard {shard}: expected 30 equations and five shards")
        if manifest.get("effective_llm_temperature") != 0.25:
            fail(f"shard {shard}: effective LLM temperature must be exactly 0.25")
        protocol = payload.get("protocol")
        methods = payload.get("methods")
        if not isinstance(protocol, dict) or not isinstance(methods, list):
            fail(f"shard {shard}: missing protocol/method metadata")
        if len(methods) != 6 or len(set(methods)) != 6:
            fail(f"shard {shard}: expected six distinct registered methods, got {methods!r}")
        expected_mode = "noiseless" if variant == "random_8020" else "noiseless_pca"
        if protocol.get("mode") != expected_mode or float(protocol.get("noise_level", -1)) != 0.0:
            fail(f"shard {shard}: protocol mode/noise does not match {variant}")
        if variant == "pca_4060" and protocol.get("noise_injected") is not False:
            fail(f"shard {shard}: PCA runner must explicitly report noise_injected=false")
        if common_protocol is None:
            common_protocol, common_methods = protocol, methods
        elif protocol != common_protocol or methods != common_methods:
            fail(f"shard {shard}: protocol settings or method order differ")
        for record in payload["tests"]:
            results = record.get("results")
            if not isinstance(results, dict) or set(results) != set(methods):
                fail(f"shard {shard}: equation record does not retain every declared method result")
            for method_name, method_result in results.items():
                if not isinstance(method_result, dict) or "success" not in method_result:
                    fail(f"shard {shard}: {method_name!r} result is missing its explicit success status")
            if variant == "pca_4060" and record.get("pca_split_protocol") != "pca_40_60":
                fail(f"shard {shard}: PCA record is not stamped pca_40_60")
            domain = record.get("domain")
            description = record.get("description")
            matches = [
                idx for idx in manifest["assigned_equation_indices"]
                if identities[idx].get("domain") == domain
                and identities[idx].get("description") == description
            ]
            if len(matches) != 1:
                fail(f"shard {shard}: record identity does not match exactly one assigned registry equation: {domain!r}/{description!r}")
            idx = matches[0]
            if idx in merged_records:
                fail(f"duplicate result record for equation index {idx}")
            merged_records[idx] = record

    if set(merged_records) != expected_indices:
        fail(f"result records incomplete; missing {sorted(expected_indices - set(merged_records))}")

    output_dir.mkdir(parents=True, exist_ok=True)
    merged = dict(shard_payloads[0])
    merged["timestamp"] = datetime.now(timezone.utc).isoformat()
    merged["total_tests"] = 30
    merged["tests"] = [merged_records[i] for i in range(1, 31)]
    truncation_details = {}
    for record in merged["tests"]:
        llm = record.get("results", {}).get("PureLLM Baseline (core)", {})
        if llm:
            audit_key = f"{record.get('domain', '')}::{record.get('description', '')}"
            truncation_details[audit_key] = {
                "domain": record.get("domain", ""),
                "description": record.get("description", ""),
                "truncated": llm.get("metadata", {}).get("truncated_formula", False),
                "r2": llm.get("r2"),
                "success": llm.get("success"),
                "formula": llm.get("formula", "")[:80],
            }
    truncated_count = sum(1 for item in truncation_details.values() if item["truncated"])
    merged["purelm_truncation_audit"] = {
        "truncated_count": truncated_count,
        "total_purelm_tests": len(truncation_details),
        "note": (
            f"{truncated_count} PureLLM formulas were syntactically incomplete and remain invalid."
            if truncated_count else
            "No truncated PureLLM formulas detected in the merged 30-equation run."
        ),
        "details": truncation_details,
    }
    method_failure_counts = {
        name: sum(1 for record in merged["tests"] if not record["results"][name]["success"])
        for name in common_methods
    }
    method_success_counts = {name: 30 - count for name, count in method_failure_counts.items()}
    all_methods_successful = all(count == 0 for count in method_failure_counts.values())
    merged["protocol30_aggregate"] = {
        "variant": variant,
        "shard_count": 5,
        "equation_count": 30,
        "method_failure_counts": method_failure_counts,
        "method_success_counts": method_success_counts,
        "all_methods_successful": all_methods_successful,
        "method_failures_preserved": True,
        "aggregation_note": "Per-method failures remain explicit in source records; no scores are imputed.",
    }
    result_path = output_dir / f"protocol30_{variant}_aggregate.json"
    result_path.write_text(json.dumps(merged, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    manifest = {
        "experiment": variant,
        "status": "validated_complete",
        "validated_shards": sorted(shard_manifests),
        "validated_equation_indices": sorted(merged_records),
        "equation_count": len(merged_records),
        "equation_identities": [identities[i] for i in range(1, 31)],
        "methods": common_methods,
        "protocol": common_protocol,
        "all_method_records_retained": True,
        "method_failure_counts": method_failure_counts,
        "method_success_counts": method_success_counts,
        "all_methods_successful": all_methods_successful,
        "effective_llm_temperature": 0.25,
        "result_file": result_path.name,
    }
    manifest_path = output_dir / f"protocol30_{variant}_aggregate_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"PASS: {variant}: five shards, 30 unique registry-bound equations -> {result_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--variant", choices=("random_8020", "pca_4060"), required=True)
    args = parser.parse_args()
    aggregate(args.artifacts_dir, args.output_dir, args.variant)


if __name__ == "__main__":
    main()
