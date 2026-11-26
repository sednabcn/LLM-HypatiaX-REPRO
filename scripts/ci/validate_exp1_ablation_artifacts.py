#!/usr/bin/env python3
"""Validate all five archived Exp1 ablation worker artifacts before aggregation.

This recovery path consumes artifacts from an earlier workflow run; it never
starts PySR, Julia, or LLM model fits. Every shard must contain only its
assigned Core-15 checkpoint and satisfy the current shard completion contract.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hypatiax.experiments.benchmarks.exp1_ablation_contracts import (
    expected_equation_ids,
    validate_shard_checkpoint,
)

SHARDS = {
    0: "chemistry",
    1: "defi_risk",
    2: "biology",
    3: "physics",
    4: "defi_amm",
}
ARMS = ("pysr_only", "hypatia", "hypatia_nollm")


def validate_artifacts(root: Path) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: list[int] = []
    manifest_shards = []

    for shard, task in SHARDS.items():
        artifact = root / f"results-exp1_ablation-shard{shard}"
        if not artifact.is_dir():
            errors.append(f"missing artifact directory: {artifact.name}")
            continue

        expected_name = f"exp1_ablation_checkpoint_shard{shard}.json"
        matches = sorted(artifact.rglob(expected_name))
        if len(matches) != 1:
            errors.append(
                f"{artifact.name}: expected exactly one {expected_name}, found {len(matches)}"
            )
            continue

        path = matches[0]
        try:
            checkpoint = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{artifact.name}: invalid checkpoint JSON: {exc}")
            continue
        if not isinstance(checkpoint, dict):
            errors.append(f"{artifact.name}: checkpoint root must be a JSON object")
            continue

        assigned = expected_equation_ids((task,))
        expected_keys = {str(eq_id) for eq_id in assigned}
        observed_keys = {str(key) for key in checkpoint}
        missing_keys = sorted(expected_keys - observed_keys, key=int)
        unexpected_keys = sorted(
            (key for key in observed_keys if key.isdigit() and key not in expected_keys),
            key=int,
        )
        if missing_keys:
            errors.append(f"{artifact.name}: missing assigned equation IDs {missing_keys}")
        if unexpected_keys:
            errors.append(f"{artifact.name}: contains equations assigned to other shards {unexpected_keys}")

        shard_errors, shard_warnings = validate_shard_checkpoint(
            checkpoint, (task,), ARMS
        )
        errors.extend(f"{artifact.name}: {message}" for message in shard_errors)
        warnings.extend(f"{artifact.name}: {message}" for message in shard_warnings)
        seen_ids.extend(assigned)
        manifest_shards.append({
            "shard": shard,
            "task": task,
            "artifact": artifact.name,
            "checkpoint": str(path.relative_to(root)),
            "assigned_equation_ids": list(assigned),
            "observed_equation_ids": sorted(
                (int(key) for key in observed_keys if key.isdigit())
            ),
        })

    if sorted(seen_ids) != list(range(15)):
        errors.append(f"shard registry does not cover Core-15 exactly once: {sorted(seen_ids)}")

    expected_artifacts = {f"results-exp1_ablation-shard{i}" for i in SHARDS}
    observed_artifacts = {
        p.name for p in root.iterdir()
        if p.is_dir() and p.name.startswith("results-exp1_ablation-shard")
    } if root.exists() else set()
    extras = sorted(observed_artifacts - expected_artifacts)
    if extras:
        errors.append(f"unexpected shard artifact directories: {extras}")

    return errors, warnings, {
        "experiment": "exp1_ablation",
        "expected_shards": 5,
        "arms": list(ARMS),
        "shards": manifest_shards,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()

    errors, warnings, manifest = validate_artifacts(args.artifacts_dir)
    for warning in warnings:
        print(f"::warning::{warning}")
    if errors:
        for error in errors:
            print(f"::error::{error}")
        return 1

    manifest.update({
        "source_workflow_run_id": str(args.source_run_id),
        "source_commit": args.source_commit,
        "validation": "passed",
    })
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / "exp1_ablation_recovery_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Validated five archived shards / 15 equations / three arms.")
    print(f"Source run: {args.source_run_id} ({args.source_commit})")
    print(f"Recovery manifest: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
