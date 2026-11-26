"""Validate and promote the five isolated Exp1 PCA seed worker artifacts."""
from __future__ import annotations
import argparse
import json
import shutil
from pathlib import Path

EXPECTED_SEEDS = {0: 42, 1: 99, 2: 123, 3: 777, 4: 2024}
RESULT_PREFIX = "hypatiax_defi_benchmark_pca_results_seed"

def _records(payload: object) -> list[dict]:
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        records = payload.get("results")
    else:
        records = None
    if not isinstance(records, list) or not all(isinstance(row, dict) for row in records):
        raise ValueError("PCA result JSON must contain a list of result records")
    return records

def aggregate_seed_artifacts(artifacts_dir: str | Path, output_dir: str | Path, *, run_id: str | None = None, commit: str | None = None) -> dict:
    """Require five complete, seed-stamped PCA results before promoting any file."""
    artifacts_dir, output_dir = Path(artifacts_dir), Path(output_dir)
    validated: list[tuple[int, int, Path, int]] = []
    errors: list[str] = []
    for shard, seed in EXPECTED_SEEDS.items():
        result_path = artifacts_dir / f"results-exp1_pca-shard{shard}" / f"{RESULT_PREFIX}{seed}.json"
        if not result_path.is_file():
            errors.append(f"shard {shard} seed {seed}: missing {result_path.name}")
            continue
        try:
            records = _records(json.loads(result_path.read_text(encoding="utf-8")))
        except Exception as exc:
            errors.append(f"{result_path}: invalid JSON/result records: {exc}")
            continue
        if len(records) != 74:
            errors.append(f"{result_path.name}: expected 74 records, found {len(records)}")
            continue
        if {str(row.get("seed")) for row in records} != {str(seed)}:
            errors.append(f"{result_path.name}: record seed stamps do not all equal {seed}")
            continue
        equation_ids = [row.get("equation_id") for row in records]
        if len(set(equation_ids)) != 74 or any(not value for value in equation_ids):
            errors.append(f"{result_path.name}: expected 74 unique non-empty equation_id values")
            continue
        bad_splits = [
            row.get("equation_id") for row in records
            if not isinstance(row.get("split_protocol"), dict)
            or row["split_protocol"].get("name") != "pca_40_60_pc1"
            or row["split_protocol"].get("train_fraction") != 0.4
            or row["split_protocol"].get("test_fraction") != 0.6
        ]
        if bad_splits:
            errors.append(f"{result_path.name}: PCA 40/60 split metadata missing/invalid for {bad_splits[:3]}")
            continue
        validated.append((shard, seed, result_path, len(records)))
    if errors:
        raise ValueError("PCA seed aggregate rejected; no files promoted:\n- " + "\n- ".join(errors))
    if len(validated) != len(EXPECTED_SEEDS):
        raise ValueError("PCA seed aggregate rejected: not all five workers validated")

    output_dir.mkdir(parents=True, exist_ok=True)
    for _, seed, source, _ in validated:
        shutil.copy2(source, output_dir / f"{RESULT_PREFIX}{seed}.json")
    manifest = {
        "experiment_id": "exp1_pca", "status": "passed", "protocol": "pca_40_60_pc1",
        "train_fraction": 0.4, "test_fraction": 0.6,
        "expected_seeds": list(EXPECTED_SEEDS.values()),
        "validated_seeds": [seed for _, seed, _, _ in validated],
        "expected_cases_per_seed": 74,
        "validated_case_records": sum(count for _, _, _, count in validated),
        "workflow_run_id": run_id, "commit_sha": commit,
        "shards": [
            {"shard": shard, "seed": seed, "result_file": source.name, "case_count": count}
            for shard, seed, source, count in validated
        ],
    }
    (output_dir / "pca_seed_aggregate_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--commit")
    args = parser.parse_args()
    manifest = aggregate_seed_artifacts(args.artifacts_dir, args.output_dir, run_id=args.run_id, commit=args.commit)
    print("PASS: validated five PCA seed workers (" + ", ".join(map(str, manifest["validated_seeds"])) + "); " + str(manifest["validated_case_records"]) + " case records promoted.")

if __name__ == "__main__":
    main()
