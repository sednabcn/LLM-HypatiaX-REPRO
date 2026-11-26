#!/usr/bin/env python3
"""Gather the per-seed exp1_ablation results into one manifest.

exp1_ablation_seeds dispatches one ordinary exp1_ablation run per seed.  Each
run commits its own results directory under hypatiax/data/results/ablation/:

    seed 42     -> ablation/exp1_ablation/
    other seeds -> ablation/exp1_ablation_seed<N>/

This script verifies that every requested seed has the complete set of
analysis artifacts and writes an index of them to

    ablation/exp1_ablation_seeds/exp1_ablation_seeds_manifest.json

It does NOT compute cross-seed statistics and does not assume anything about
the schema of the result files beyond "valid JSON".  Exit status is 1 when any
requested seed is incomplete or inconsistent (the manifest is still written).
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REQUIRED = (
    "exp1_ablation_results.json",
    "exp1_rf01_mannwhitney.json",
    "exp1_llm_contribution.json",
)
CANONICAL_SEED = 42
OUT_SUBDIR = "exp1_ablation_seeds"
MANIFEST_NAME = "exp1_ablation_seeds_manifest.json"


def seed_dir(root: Path, seed: int) -> Path:
    return root / ("exp1_ablation" if seed == CANONICAL_SEED else f"exp1_ablation_seed{seed}")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def describe_json(path: Path):
    """Return (info, problem).  info is structure-only; never the data itself."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:  # noqa: BLE001 - report any parse failure
        return None, f"not valid JSON ({e})", None
    if isinstance(data, dict):
        shape = {"type": "dict", "n_keys": len(data), "keys": sorted(map(str, data))[:25]}
    elif isinstance(data, list):
        shape = {"type": "list", "length": len(data)}
    else:
        shape = {"type": type(data).__name__}
    return shape, None, data


def git_last_commit(path: Path):
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%H %cI", "--", str(path)],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        if out:
            sha, when = out.split(" ", 1)
            return {"commit": sha, "committed_at": when}
    except Exception:  # noqa: BLE001 - not in a git checkout is fine
        pass
    return None


def parse_seeds(raw: str):
    seeds = []
    for tok in raw.replace(",", " ").split():
        if not tok.isdigit():
            raise SystemExit(f"invalid seed {tok!r}: seeds must be non-negative integers")
        seeds.append(int(tok))
    if not seeds:
        raise SystemExit("no seeds given")
    if len(set(seeds)) != len(seeds):
        raise SystemExit(f"duplicate seeds in {seeds}")
    return seeds


def parse_run_map(raw: str):
    out = {}
    for pair in (raw or "").split(","):
        if pair.strip():
            seed, _, run_id = pair.partition(":")
            out[int(seed)] = run_id.strip()
    return out


def gather_seed(root: Path, seed: int):
    d = seed_dir(root, seed)
    entry = {"directory": str(d), "files": {}, "problems": []}
    if not d.is_dir():
        entry["problems"].append(f"results directory missing: {d}")
    else:
        for name in REQUIRED:
            p = d / name
            if not p.is_file() or p.stat().st_size == 0:
                entry["problems"].append(f"{name}: missing or empty")
                continue
            shape, problem, data = describe_json(p)
            if problem:
                entry["problems"].append(f"{name}: {problem}")
                continue
            entry["files"][name] = {"bytes": p.stat().st_size, "sha256": sha256(p), "structure": shape}
            # Cross-check only when the file itself records a seed.
            if isinstance(data, dict) and isinstance(data.get("seed"), int) and data["seed"] != seed:
                entry["problems"].append(
                    f"{name}: records seed {data['seed']} but lives in the seed-{seed} directory"
                )
        git = git_last_commit(d)
        if git:
            entry["last_commit"] = git
    entry["status"] = "complete" if not entry["problems"] else "incomplete"
    return entry


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--results-root", required=True, help="e.g. hypatiax/data/results/ablation")
    ap.add_argument("--seeds", required=True, help="comma/space separated, e.g. 42,99,123,777,2024")
    ap.add_argument("--run-map", default="", help="optional 'seed:run_id,...' from the dispatcher")
    args = ap.parse_args(argv)

    root = Path(args.results_root)
    seeds = parse_seeds(args.seeds)
    run_map = parse_run_map(args.run_map)

    per_seed = {}
    for s in seeds:
        entry = gather_seed(root, s)
        if s in run_map:
            entry["workflow_run_id"] = run_map[s]
        per_seed[str(s)] = entry

    manifest = {
        "experiment": "exp1_ablation_seeds",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "results_root": str(root),
        "seeds": seeds,
        "required_files": list(REQUIRED),
        "all_complete": all(e["status"] == "complete" for e in per_seed.values()),
        "per_seed": per_seed,
    }
    out_dir = root / OUT_SUBDIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / MANIFEST_NAME
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = ["### exp1_ablation_seeds - gathered results", "",
             "| seed | status | directory | run |", "|---|---|---|---|"]
    for s in seeds:
        e = per_seed[str(s)]
        lines.append(f"| {s} | {e['status']} | `{e['directory']}` | {e.get('workflow_run_id', '-')} |")
        for p in e["problems"]:
            lines.append(f"|  | ↳ {p} | | |")
    report = "\n".join(lines)
    print(report)
    print(f"\nmanifest: {out}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(report + "\n")

    if not manifest["all_complete"]:
        bad = [s for s in seeds if per_seed[str(s)]["status"] != "complete"]
        print(f"::error::exp1_ablation_seeds: incomplete seed(s): {bad}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
