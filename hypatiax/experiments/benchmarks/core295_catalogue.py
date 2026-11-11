"""Offline Core-295 catalogue loading and deterministic CI shard planning.

No model, API, Julia, PySR, or experiment code is imported or executed here.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST = ROOT / "config" / "core295_catalogue.json"
DOMAINS = ("Chemistry", "Biology", "Physics", "DeFi AMM", "DeFi Risk")


def load_accepted_entries(path: Path = DEFAULT_MANIFEST) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("catalogue_id") != "core295-option2":
        raise ValueError("not a Core-295 Option 2 catalogue")
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise ValueError("catalogue entries must be a list")
    accepted = [entry for entry in entries if entry.get("status") == "accepted"]
    return accepted


def plan_domain_balanced_shards(
    entries: list[dict[str, Any]], n_shards: int = 100
) -> list[list[dict[str, Any]]]:
    """Assign each accepted equation exactly once with balanced load/domains.

    Greedy deterministic assignment minimizes, in order:
      1. current shard task count,
      2. count of this task's domain in that shard,
      3. shard index.

    This is a scheduling heuristic only; it does not change model-level
    parallelism or scientific settings.
    """
    if n_shards < 1:
        raise ValueError("n_shards must be >= 1")
    ids = [entry.get("equation_id") for entry in entries]
    if any(not isinstance(value, str) or not value for value in ids):
        raise ValueError("every entry must have a non-empty equation_id")
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate equation_id in accepted catalogue")
    unknown = sorted({entry.get("domain") for entry in entries} - set(DOMAINS))
    if unknown:
        raise ValueError(f"unknown Core-295 domain(s): {unknown}")

    shards: list[list[dict[str, Any]]] = [[] for _ in range(n_shards)]
    domain_counts = [Counter() for _ in range(n_shards)]
    ordered = sorted(
        entries,
        key=lambda entry: (DOMAINS.index(entry["domain"]), entry["equation_id"]),
    )
    for entry in ordered:
        domain = entry["domain"]
        target = min(
            range(n_shards),
            key=lambda shard_id: (
                len(shards[shard_id]),
                domain_counts[shard_id][domain],
                shard_id,
            ),
        )
        shards[target].append(entry)
        domain_counts[target][domain] += 1

    return shards


def validate_shard_plan(
    entries: list[dict[str, Any]], shards: list[list[dict[str, Any]]]
) -> None:
    expected = [entry["equation_id"] for entry in entries]
    observed = [entry["equation_id"] for shard in shards for entry in shard]
    if len(observed) != len(set(observed)):
        raise ValueError("shard plan assigns an equation more than once")
    if sorted(observed) != sorted(expected):
        raise ValueError("shard plan does not cover the accepted catalogue exactly once")
    if max((len(shard) for shard in shards), default=0) - min(
        (len(shard) for shard in shards), default=0
    ) > 1:
        raise ValueError("shard task counts are not balanced to within one task")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--n-shards", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true", help="print the allocation; never execute experiments")
    args = parser.parse_args()
    if not args.dry_run:
        parser.error("only --dry-run is supported by this offline planner")
    entries = load_accepted_entries(args.manifest)
    if len(entries) != 295:
        raise SystemExit(
            f"catalogue is not ready for planning: {len(entries)} accepted entries found; 295 required"
        )
    for domain in DOMAINS:
        count = sum(entry["domain"] == domain for entry in entries)
        if count != 59:
            raise SystemExit(f"{domain}: expected 59 accepted entries, found {count}")
    shards = plan_domain_balanced_shards(entries, args.n_shards)
    validate_shard_plan(entries, shards)
    print(f"Core-295 dry-run: {len(entries)} equations -> {len(shards)} shards")
    for index, shard in enumerate(shards):
        counts = Counter(entry["domain"] for entry in shard)
        detail = ", ".join(f"{domain}={counts[domain]}" for domain in DOMAINS if counts[domain])
        ids = ",".join(entry["equation_id"] for entry in shard)
        print(f"shard_{index:03d}: n={len(shard)} [{detail}] tasks={ids}")
    print("No experiments were executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
