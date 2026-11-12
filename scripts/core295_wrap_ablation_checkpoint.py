#!/usr/bin/env python3
"""Wrap a same-run native ablation checkpoint in the Core-295 shard envelope.

This is an artifact adapter only. It does not execute equations or infer run
identity, equation identity, or success from checkpoint contents.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

RESULT_SCHEMA = "core295-ablation-shard-v1"
MANIFEST_SCHEMA = "core295-task-manifest-v1"
ARMS = ("pysr_only", "hypatia", "hypatia_nollm")
STATUSES = {"success", "failed", "timeout", "skipped"}


def fail(message: str) -> None:
    raise SystemExit("BLOCKED: " + message)


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {path}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--shard-id", type=int, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True,
                        help="native checkpoint object keyed by runner-local checkpoint keys")
    parser.add_argument("--mapping", type=Path, required=True,
                        help="explicit mapping: equation_id -> checkpoint_key + per-arm statuses")
    parser.add_argument("--output", type=Path, required=True,
                        help="new wrapper artifact path; never overwritten")
    args = parser.parse_args()

    manifest = read_json(args.manifest)
    if not isinstance(manifest, dict) or manifest.get("schema") != MANIFEST_SCHEMA:
        fail("manifest schema mismatch")
    if manifest.get("planning_only") is not True or manifest.get("experiments_executed") is not False:
        fail("manifest must be the immutable planning-only task manifest")
    for key in ("run_id", "catalogue_sha256", "task_set_sha256"):
        if not isinstance(manifest.get(key), str) or not manifest[key]:
            fail(f"manifest {key} is missing")
    shards = manifest.get("shards")
    if not isinstance(shards, list):
        fail("manifest shards must be an array")
    if type(manifest.get("shard_count")) is not int or manifest["shard_count"] < 1:
        fail("manifest shard_count must be a positive integer")
    if len(shards) != manifest["shard_count"]:
        fail("manifest shard_count does not match shard list")
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        fail("manifest tasks must be an array")
    task_hash = hashlib.sha256(canonical(tasks)).hexdigest()
    plan_hash = hashlib.sha256(canonical({"tasks": tasks, "shards": shards})).hexdigest()
    if task_hash != manifest.get("task_set_sha256") or plan_hash != manifest.get("shard_plan_sha256"):
        fail("manifest task/shard hashes do not validate")
    if type(args.shard_id) is not int or args.shard_id < 0:
        fail("shard ID must be a non-negative integer")
    matches = [s for s in shards if isinstance(s, dict) and type(s.get("shard_id")) is int and s.get("shard_id") == args.shard_id]
    if len(matches) != 1:
        fail(f"shard_id {args.shard_id} is not uniquely present in manifest")
    expected_ids = matches[0].get("equation_ids")
    if not isinstance(expected_ids, list) or not all(isinstance(x, str) for x in expected_ids):
        fail("manifest shard equation_ids malformed")

    checkpoint = read_json(args.checkpoint)
    mapping = read_json(args.mapping)
    if not isinstance(checkpoint, dict) or not isinstance(mapping, dict):
        fail("checkpoint and mapping roots must be JSON objects")
    if set(mapping) != set(expected_ids):
        fail("mapping equation IDs must exactly match this shard's planned IDs")
    if len(set(mapping.values())) != len(mapping):
        fail("mapping must use unique checkpoint keys")

    equations = []
    for equation_id in expected_ids:
        spec = mapping[equation_id]
        if not isinstance(spec, dict) or not isinstance(spec.get("checkpoint_key"), str):
            fail(f"{equation_id}: mapping requires checkpoint_key")
        key = spec["checkpoint_key"]
        statuses = spec.get("arm_statuses")
        if not isinstance(statuses, dict) or set(statuses) != set(ARMS):
            fail(f"{equation_id}: arm_statuses must declare exactly {list(ARMS)}")
        native = checkpoint.get(key)
        if not isinstance(native, dict):
            fail(f"{equation_id}: native checkpoint row {key!r} is absent or malformed")
        arms = {}
        for arm in ARMS:
            status = statuses[arm]
            if not isinstance(status, str) or status not in STATUSES:
                fail(f"{equation_id}/{arm}: invalid explicit status {status!r}")
            payload = native.get(arm)
            if status == "success" and not isinstance(payload, dict):
                fail(f"{equation_id}/{arm}: success requires a native payload object")
            if status != "success" and payload is not None and not isinstance(payload, dict):
                fail(f"{equation_id}/{arm}: non-success payload must be an object or absent")
            row = {"status": status}
            if isinstance(payload, dict):
                row["payload"] = payload
            arms[arm] = row
        equations.append({"equation_id": equation_id, "arms": arms})

    artifact = {
        "schema": RESULT_SCHEMA,
        "run_id": manifest["run_id"],
        "catalogue_sha256": manifest["catalogue_sha256"],
        "task_set_sha256": manifest["task_set_sha256"],
        "shard_id": args.shard_id,
        "shard_count": manifest.get("shard_count"),
        "equations": equations,
        "provenance": {
            "checkpoint_sha256": hashlib.sha256(args.checkpoint.read_bytes()).hexdigest(),
            "mapping_sha256": hashlib.sha256(args.mapping.read_bytes()).hexdigest(),
            "adapter": "core295_wrap_ablation_checkpoint.py"
        }
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.output.open("xb", encoding="utf-8") as stream:
            stream.write(canonical(artifact).decode("utf-8"))
    except FileExistsError:
        fail(f"refusing to overwrite existing artifact: {args.output}")
    print(json.dumps({"status": "WRAPPED", "run_id": artifact["run_id"],
                      "shard_id": args.shard_id, "equations": len(equations),
                      "output": str(args.output),
                      "checkpoint_sha256": artifact["provenance"]["checkpoint_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
