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
        shard_manifests[shard] = manifest

        mapping = manifest.get("equation_identities")
        if not isinstance(mapping, list) or {x.get("index") for x in mapping} != set(assigned):
            fail(f"{manifest_path}: identity map does not match assigned indices")
        for item in mapping:
            idx = item["index"]
            if idx in identities:
                fail(f"equation index {idx} assigned to multiple shards")
            identities[idx] = item

        result_files = sorted(manifest_path.parent.glob("protocol_core_*.json"))
        result_files = [p for p in result_files if "aggregate" not in p.name]
        if len(result_files) != 1:
            fail(f"shard {shard}: expected exactly one detailed result JSON, found {len(result_files)}")
        payload = load_json(result_files[0])
        if not isinstance(payload.get("tests"), list):
            fail(f"{result_files[0]}: missing tests list")
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
        protocol = payload.get("protocol")
        methods = payload.get("methods")
        if not isinstance(protocol, dict) or not isinstance(methods, list):
            fail(f"shard {shard}: missing protocol/method metadata")
        if common_protocol is None:
            common_protocol, common_methods = protocol, methods
        elif protocol != common_protocol or methods != common_methods:
            fail(f"shard {shard}: protocol settings or method order differ")
        for record in payload["tests"]:
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
    merged["protocol30_aggregate"] = {
        "variant": variant,
        "shard_count": 5,
        "equation_count": 30,
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
        "methods": common_methods,
        "protocol": common_protocol,
        "all_method_records_retained": True,
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
