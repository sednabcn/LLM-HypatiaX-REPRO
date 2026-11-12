#!/usr/bin/env python3
"""Strictly merge the five isolated Core-15 four-way worker shards."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path


def load_driver(repo_root: Path):
    path = repo_root / "hypatiax/experiments/benchmarks/exp1_four_way_matched.py"
    spec = importlib.util.spec_from_file_location("core15_four_way_driver", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load Core-15 driver: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    os.environ.setdefault("FOUR_WAY_OUTPUT_DIR", str(args.output_dir.resolve()))
    driver = load_driver(args.repo_root.resolve())
    expected_ids = {str(i) for i in range(len(driver.abl.CORE_15))}
    shard_dirs = sorted(
        path.parent for path in args.artifacts_dir.rglob("exp1_four_way_matched_checkpoint.json")
    )
    errors = []
    if len(shard_dirs) != 5:
        errors.append(f"expected exactly 5 shard checkpoints, found {len(shard_dirs)}")

    merged = {}
    common_fingerprint = None
    observed_shards = set()
    for shard_dir in shard_dirs:
        checkpoint_path = shard_dir / "exp1_four_way_matched_checkpoint.json"
        manifest_path = shard_dir / "exp1_four_way_matched_manifest.json"
        try:
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{shard_dir}: unreadable checkpoint/manifest: {exc}")
            continue

        shard_index = manifest.get("shard_index")
        if not isinstance(shard_index, int) or shard_index not in range(5):
            errors.append(f"{manifest_path}: invalid shard_index {shard_index!r}")
        elif shard_index in observed_shards:
            errors.append(f"duplicate shard_index {shard_index}")
        else:
            observed_shards.add(shard_index)

        fingerprint = checkpoint.get("__run_metadata__")
        if not isinstance(fingerprint, dict) or fingerprint != manifest.get("run_fingerprint"):
            errors.append(f"{shard_dir}: checkpoint/manifest run fingerprint mismatch")
        if common_fingerprint is None:
            common_fingerprint = fingerprint
        elif fingerprint != common_fingerprint:
            errors.append(f"{shard_dir}: incompatible source/protocol/runtime/settings fingerprint")

        assigned = manifest.get("assigned_equation_ids")
        if not isinstance(assigned, list) or not assigned:
            errors.append(f"{manifest_path}: missing assigned_equation_ids")
            assigned = []
        shard_rows = {key for key in checkpoint if key != "__run_metadata__"}
        if shard_rows != set(assigned):
            errors.append(
                f"{shard_dir}: checkpoint equation keys {sorted(shard_rows)} "
                f"do not match manifest assignment {sorted(set(assigned))}"
            )
        for key in sorted(shard_rows):
            if key not in expected_ids:
                errors.append(f"{shard_dir}: unexpected equation ID {key}")
                continue
            if key in merged:
                errors.append(f"equation {key} appears in more than one shard")
                continue
            row = checkpoint[key]
            if not isinstance(row, dict) or not isinstance(row.get("split"), dict):
                errors.append(f"equation {key}: missing row or shared-split fingerprints")
                continue
            methods = row.get("methods")
            if not isinstance(methods, dict) or set(methods) != set(driver.METHOD_KEYS):
                errors.append(f"equation {key}: expected all four method records")
                continue
            merged[key] = row

    if observed_shards != set(range(5)):
        errors.append(f"expected shard indices 0..4, found {sorted(observed_shards)}")
    if set(merged) != expected_ids:
        errors.append(
            f"Core-15 coverage mismatch: missing={sorted(expected_ids-set(merged))}, "
            f"extra={sorted(set(merged)-expected_ids)}"
        )
    if not isinstance(common_fingerprint, dict):
        errors.append("no valid common run fingerprint found")
    elif common_fingerprint.get("settings", {}).get("llm_temperature_effective") != 0.25:
        errors.append("effective LLM temperature is not the required 0.25")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = {"__run_metadata__": common_fingerprint, **merged}
    results_path = args.output_dir / "exp1_four_way_matched_results.json"
    checkpoint_path = args.output_dir / "exp1_four_way_matched_checkpoint.json"
    summary_path = args.output_dir / "exp1_four_way_matched_summary.json"
    manifest_path = args.output_dir / "exp1_four_way_matched_manifest.json"

    safe = driver._json_safe(checkpoint)
    for path in (results_path, checkpoint_path):
        path.write_text(json.dumps(safe, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    summary = driver._aggregate(merged)
    summary_path.write_text(
        json.dumps(driver._json_safe(summary), indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "protocol": "Core-15 matched four-arm predictive comparison",
        "execution_status": "aggregated_complete",
        "expected_equations": 15,
        "observed_equations": len(merged),
        "validated_shards": sorted(observed_shards),
        "run_fingerprint": common_fingerprint,
        "llm_temperature_effective": 0.25,
        "assigned_equation_ids": sorted(merged, key=int),
        "arms": list(driver.METHOD_KEYS),
        "results_file": str(results_path),
        "checkpoint_file": str(checkpoint_path),
        "summary_file": str(summary_path),
        "scientific_interpretation": (
            "Descriptive paired comparisons only; do not infer universal Hybrid superiority. "
            "LLM-only is zero-shot and does not use training arrays for formula generation."
        ),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: merged all {len(merged)} Core-15 equations from five isolated shards.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
