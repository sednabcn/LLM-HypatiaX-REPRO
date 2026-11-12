#!/usr/bin/env python3
"""Verify Core-295 same-run ablation shard coverage; never computes scientific metrics."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

MANIFEST_SCHEMA = "core295-task-manifest-v1"
RESULT_SCHEMA = "core295-ablation-shard-v1"
REQUIRED_ARMS = ("pysr_only", "hypatia", "hypatia_nollm")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def blocked(message: str) -> None:
    raise SystemExit("BLOCKED: " + message)


def read_json(path: Path) -> tuple[object, bytes]:
    try:
        raw = path.read_bytes()
        return json.loads(raw), raw
    except (OSError, json.JSONDecodeError) as exc:
        blocked(f"cannot read valid JSON from {path}: {exc}")


def verify_manifest(m: object) -> tuple[dict, dict[int, set[str]]]:
    if not isinstance(m, dict) or m.get("schema") != MANIFEST_SCHEMA:
        blocked("task manifest schema must be core295-task-manifest-v1")
    if m.get("planning_only") is not True or m.get("experiments_executed") is not False:
        blocked("input is not an immutable planning-only task manifest")
    for field in ("run_id", "catalogue_sha256", "task_set_sha256", "shard_plan_sha256"):
        if not isinstance(m.get(field), str) or not m[field]:
            blocked(f"manifest {field} is required")
    tasks, shards = m.get("tasks"), m.get("shards")
    if not isinstance(tasks, list) or not isinstance(shards, list):
        blocked("manifest tasks and shards must be arrays")
    task_ids = [t.get("equation_id") for t in tasks if isinstance(t, dict)]
    if len(task_ids) != len(tasks) or len(task_ids) != len(set(task_ids)):
        blocked("manifest task IDs are malformed or duplicated")
    task_hash = digest(canonical(tasks))
    if task_hash != m["task_set_sha256"]:
        blocked("manifest task_set_sha256 does not match canonical task list")
    payload = {"tasks": tasks, "shards": shards}
    if digest(canonical(payload)) != m["shard_plan_sha256"]:
        blocked("manifest shard_plan_sha256 does not match tasks/shards")
    shard_map: dict[int, set[str]] = {}
    seen = []
    for row in shards:
        if not isinstance(row, dict) or type(row.get("shard_id")) is not int:
            blocked("manifest contains malformed shard row")
        sid, ids = row["shard_id"], row.get("equation_ids")
        if sid in shard_map or not isinstance(ids, list) or not all(isinstance(x, str) for x in ids):
            blocked("manifest has duplicate shard ID or malformed equation_ids")
        if row.get("equation_count") != len(ids):
            blocked(f"manifest shard {sid} equation_count mismatch")
        shard_map[sid] = set(ids)
        seen.extend(ids)
    if set(seen) != set(task_ids) or len(seen) != len(set(seen)):
        blocked("manifest shard assignment is not exact-once")
    if len(shard_map) != m.get("shard_count") or set(shard_map) != set(range(m["shard_count"])):
        blocked("manifest shard IDs are not contiguous or shard_count mismatches")
    return m, shard_map


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--shard-results", type=Path, nargs="+", required=True,
                   help="one core295-ablation-shard-v1 JSON artifact per planned shard")
    p.add_argument("--report-json", type=Path, required=True)
    p.add_argument("--report-md", type=Path, required=True)
    args = p.parse_args()

    manifest, manifest_raw = read_json(args.manifest)
    m, expected_shards = verify_manifest(manifest)
    if len(args.shard_results) != len(expected_shards):
        blocked(f"expected exactly {len(expected_shards)} shard artifacts, received {len(args.shard_results)}")

    seen_shards: set[int] = set()
    seen_equations: set[str] = set()
    artifact_rows = []
    failures = []
    for path in args.shard_results:
        obj, raw = read_json(path)
        if not isinstance(obj, dict) or obj.get("schema") != RESULT_SCHEMA:
            blocked(f"{path}: schema must be {RESULT_SCHEMA}")
        for field in ("run_id", "catalogue_sha256", "task_set_sha256"):
            if obj.get(field) != m[field]:
                blocked(f"{path}: {field} does not match the task manifest")
        sid = obj.get("shard_id")
        if type(sid) is not int or sid not in expected_shards:
            blocked(f"{path}: invalid or unexpected shard_id {sid!r}")
        if sid in seen_shards:
            blocked(f"duplicate shard_id {sid}")
        seen_shards.add(sid)
        if obj.get("shard_count") != len(expected_shards):
            blocked(f"{path}: shard_count mismatch")
        rows = obj.get("equations")
        if not isinstance(rows, list):
            blocked(f"{path}: equations must be an array")
        ids = []
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("equation_id"), str):
                blocked(f"{path}: malformed equation result row")
            eid = row["equation_id"]
            if eid in ids or eid in seen_equations:
                blocked(f"{path}: duplicate equation result {eid}")
            ids.append(eid)
            if eid not in expected_shards[sid]:
                blocked(f"{path}: equation {eid} is not assigned to shard {sid}")
            arms = row.get("arms")
            if not isinstance(arms, dict) or set(arms) != set(REQUIRED_ARMS):
                blocked(f"{path}: {eid} must contain exactly arms {list(REQUIRED_ARMS)}")
            for arm in REQUIRED_ARMS:
                result = arms[arm]
                if not isinstance(result, dict) or result.get("status") not in ("success", "failed", "timeout", "skipped"):
                    blocked(f"{path}: {eid}/{arm} requires a result object and explicit terminal status")
                if result.get("status") != "success":
                    failures.append({"equation_id": eid, "arm": arm, "status": result["status"]})
            seen_equations.add(eid)
        if set(ids) != expected_shards[sid] or len(ids) != len(expected_shards[sid]):
            missing = sorted(expected_shards[sid] - set(ids))
            extra = sorted(set(ids) - expected_shards[sid])
            blocked(f"{path}: shard {sid} equation coverage mismatch; missing={missing}, extra={extra}")
        artifact_rows.append({"path": str(path), "sha256": digest(raw), "shard_id": sid,
                              "equation_count": len(ids)})

    if seen_shards != set(expected_shards):
        blocked(f"missing shard IDs: {sorted(set(expected_shards) - seen_shards)}")
    task_ids = {t["equation_id"] for t in m["tasks"]}
    if seen_equations != task_ids:
        blocked("combined shard results do not exactly cover the manifest task set")

    report = {
        "schema": "core295-ablation-coverage-report-v1",
        "run_id": m["run_id"],
        "manifest_sha256": digest(manifest_raw),
        "catalogue_sha256": m["catalogue_sha256"],
        "task_set_sha256": m["task_set_sha256"],
        "shard_count_expected": len(expected_shards),
        "shard_count_verified": len(seen_shards),
        "equation_count_expected": len(task_ids),
        "equation_count_verified": len(seen_equations),
        "required_arms": list(REQUIRED_ARMS),
        "equation_arm_slots_expected": len(task_ids) * len(REQUIRED_ARMS),
        "equation_arm_slots_present": sum(len(REQUIRED_ARMS) for _ in seen_equations),
        "non_success_arm_results": failures,
        "shards": sorted(artifact_rows, key=lambda x: x["shard_id"]),
        "coverage_verified": True,
        "all_arms_successful": not failures,
        "scientific_metrics_computed": False,
        "historical_backfill_used": False,
        "acceptance_authority": "none"
    }
    md = [
        "# Core-295 same-run ablation coverage",
        "",
        f"- Run ID: `{m['run_id']}`",
        f"- Manifest SHA-256: `{report['manifest_sha256']}`",
        f"- Catalogue SHA-256: `{m['catalogue_sha256']}`",
        f"- Task-set SHA-256: `{m['task_set_sha256']}`",
        f"- Shards: {len(seen_shards)}/{len(expected_shards)}",
        f"- Equations: {len(seen_equations)}/{len(task_ids)}",
        f"- Required arms: {', '.join(REQUIRED_ARMS)}",
        f"- Arm slots: {report['equation_arm_slots_present']}/{report['equation_arm_slots_expected']}",
        f"- All arm statuses successful: {'yes' if not failures else 'no'}",
        "",
        "## Shard artifacts",
        "",
        "| Shard | Equations | SHA-256 | Artifact |",
        "|---:|---:|---|---|",
    ]
    for a in report["shards"]:
        md.append(f"| {a['shard_id']} | {a['equation_count']} | `{a['sha256']}` | `{a['path']}` |")
    md += ["", "## Non-success arm results", ""]
    md += ([f"- {x['equation_id']} / {x['arm']}: {x['status']}" for x in failures]
           if failures else ["- None"])
    md += ["", "This report verifies artifact identity and exact coverage only. It does not compute metrics, validate scientific results, or accept equations.", ""]

    for path in (args.report_json, args.report_md):
        path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.report_json.open("xb", encoding="utf-8") as f:
            f.write(canonical(report).decode())
        with args.report_md.open("xb", encoding="utf-8") as f:
            f.write("\n".join(md))
    except FileExistsError as exc:
        blocked(f"refusing to overwrite report output: {exc.filename}")
    print(json.dumps({"status": "COVERAGE_VERIFIED", "all_arms_successful": not failures,
                      "equations": len(seen_equations), "shards": len(seen_shards),
                      "report_json": str(args.report_json), "report_md": str(args.report_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
