#!/usr/bin/env python3
"""Write registry-bound Protocol-30 metadata for worker and full-run executions."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def build_manifest(
    *,
    output_dir: Path,
    shard_index: int,
    run_started_ns: int,
    indices: list[int] | None,
    variant: str,
    registry_rows: list[dict],
    effective_temperature: float,
    smoke_test: bool = False,
) -> dict:
    if variant not in ("random_8020", "pca_4060"):
        raise ValueError(f"unsupported Protocol-30 variant: {variant}")
    if effective_temperature != 0.25:
        raise ValueError(
            "Protocol-30 requires effective LLM temperature 0.25, "
            f"got {effective_temperature}"
        )
    if len(registry_rows) != 30:
        raise ValueError(
            f"Protocol30 registry returned {len(registry_rows)} equations, expected 30"
        )

    # No --indices means the runner executed the complete 30-equation protocol
    # in one job. Explicit indices mean this is a worker in the five-shard plan.
    is_shard_worker = indices is not None and not smoke_test
    assigned = list(range(1, 31)) if indices is None else [int(i) for i in indices]
    if not assigned or len(assigned) != len(set(assigned)):
        raise ValueError("assigned Protocol-30 equation indices must be non-empty and unique")
    if any(index < 1 or index > 30 for index in assigned):
        raise ValueError(f"Protocol-30 equation indices out of range: {assigned}")

    result_files = [
        path for path in output_dir.glob("protocol_core_*.json")
        if path.stat().st_mtime_ns >= run_started_ns
    ]
    result_files.sort(key=lambda path: path.stat().st_mtime_ns)
    if not result_files:
        raise ValueError("no detailed Protocol-30 result JSON created during this run")

    identities = [
        {"index": index, **registry_rows[index - 1]}
        for index in assigned
    ]
    manifest = {
        "experiment": f"{variant}_smoke" if smoke_test else variant,
        "execution_mode": (
            "smoke" if smoke_test else
            "five_shard_worker" if is_shard_worker else
            "single_job_full_run"
        ),
        "shard_index": int(shard_index),
        "n_shards": 1 if smoke_test or not is_shard_worker else 5,
        "expected_equation_count": 30 if is_shard_worker else len(assigned),
        "assigned_equation_indices": assigned,
        "equation_identities": identities,
        "result_file": result_files[-1].name,
        "result_files": [path.name for path in result_files],
        "effective_llm_temperature": effective_temperature,
        "smoke_test": smoke_test,
        # The five-shard aggregate validator must not mistake a full single-job
        # result for one of its six-equation worker artifacts.
        "official_aggregate_eligible": is_shard_worker and not smoke_test,
    }
    return manifest


def load_protocol30_registry_rows() -> list[dict]:
    """Load all 30 identities, independent of a worker's SHARD_IDS selection.

    SHARD_IDS is used by the experiment runner to restrict a worker to selected
    equation IDs. Protocol30.get_all_domains(), however, interprets that same
    variable as a list of domain names. Temporarily remove it while enumerating
    the canonical registry, then restore the worker environment unchanged.
    """
    from hypatiax.protocols.experiment_protocol_benchmark_v2 import Protocol30

    missing = object()
    shard_ids = os.environ.pop("SHARD_IDS", missing)
    try:
        protocol = Protocol30(num_samples=200, seed=42, noiseless=True)
        registry_rows = []
        for domain in protocol.get_all_domains():
            for description, _x, _y, _variables, metadata in protocol.load_test_data(
                domain, num_samples=200
            ):
                registry_rows.append({
                    "description": description,
                    "domain": domain,
                    "equation_name": metadata["equation_name"],
                })
        return registry_rows
    finally:
        if shard_ids is not missing:
            os.environ["SHARD_IDS"] = shard_ids


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--started-ns", type=int, required=True)
    parser.add_argument("--variant", choices=("random_8020", "pca_4060"), required=True)
    parser.add_argument("--indices", type=int, nargs="+")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from hypatiax.core.llm_call import configured_temperature

    manifest = build_manifest(
        output_dir=args.output_dir,
        shard_index=args.shard,
        run_started_ns=args.started_ns,
        indices=args.indices,
        variant=args.variant,
        registry_rows=load_protocol30_registry_rows(),
        effective_temperature=configured_temperature(),
        smoke_test=bool(os.environ.get("PROTOCOL30_SMOKE_DIR")),
    )
    target = args.output_dir / "protocol30_shard_manifest.json"
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Protocol-30 execution manifest written: {target}")


if __name__ == "__main__":
    main()
