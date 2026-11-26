#!/usr/bin/env python3
"""Validate and index the fixed five-seed Core-15 Exp1 ablation replication.

Each seed is an ordinary exp1_ablation workflow with five domain shards.
This gatherer verifies the 15 x 3 terminal result records and provenance for
every seed, then writes a manifest even when the collection is incomplete.
Cross-seed descriptive statistics are produced by
aggregate_exp1_ablation_multiseed.py after this validation succeeds.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CANONICAL_SEEDS = (42, 99, 123, 777, 2024)
ARMS = ("pysr_only", "hypatia", "hypatia_nollm")
REQUIRED = (
    "exp1_ablation_results.json",
    "exp1_rf01_mannwhitney.json",
    "exp1_llm_contribution.json",
    "provenance_map_exp1.json",
)
PROTOCOL_FIELDS = ("engine_version", "populations", "niterations", "model_string", "flags")
CANONICAL_SEED = 42
OUT_SUBDIR = "exp1_ablation_seeds"
MANIFEST_NAME = "exp1_ablation_seeds_manifest.json"


def seed_dir(root: Path, seed: int) -> Path:
    return root / ("exp1_ablation" if seed == CANONICAL_SEED else f"exp1_ablation_seed{seed}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def describe_json(path: Path):
    """Return (shape, problem, parsed_data)."""
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:
        return None, f"not valid JSON ({exc})", None
    if isinstance(data, dict):
        shape = {"type": "dict", "n_keys": len(data), "keys": sorted(map(str, data))[:25]}
    elif isinstance(data, list):
        shape = {"type": "list", "length": len(data)}
    else:
        shape = {"type": type(data).__name__}
    return shape, None, data


def git_last_commit(path: Path):
    try:
        output = subprocess.run(
            ["git", "log", "-1", "--format=%H %cI", "--", str(path)],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        if output:
            sha, when = output.split(" ", 1)
            return {"commit": sha, "committed_at": when}
    except Exception:
        pass
    return None


def parse_seeds(raw: str):
    seeds = []
    for token in raw.replace(",", " ").split():
        if not token.isdigit():
            raise SystemExit(f"invalid seed {token!r}: seeds must be non-negative integers")
        seeds.append(int(token))
    if tuple(seeds) != CANONICAL_SEEDS:
        raise SystemExit(
            f"exp1_ablation_seeds is fixed to {list(CANONICAL_SEEDS)} in this order; got {seeds}"
        )
    return seeds


def parse_run_map(raw: str):
    output = {}
    for pair in (raw or "").split(","):
        if not pair.strip():
            continue
        seed_text, separator, run_id = pair.partition(":")
        if not separator or not seed_text.isdigit() or not run_id.strip().isdigit():
            raise SystemExit(f"invalid run-map entry {pair!r}; expected seed:run_id")
        seed = int(seed_text)
        if seed in output:
            raise SystemExit(f"duplicate seed {seed} in run map")
        output[seed] = run_id.strip()
    unknown = sorted(set(output) - set(CANONICAL_SEEDS))
    if unknown:
        raise SystemExit(f"run map contains unexpected seed(s): {unknown}")
    return output


def validate_core15_results(data):
    problems = []
    if not isinstance(data, dict):
        return ["exp1_ablation_results.json: expected an object keyed by equation ID"]
    expected_ids = {str(index) for index in range(15)}
    actual_ids = set(data)
    missing = sorted(expected_ids - actual_ids, key=int)
    extra = sorted(actual_ids - expected_ids)
    if missing:
        problems.append(f"exp1_ablation_results.json: missing Core-15 equation IDs {missing}")
    if extra:
        problems.append(f"exp1_ablation_results.json: unexpected equation IDs {extra}")
    for eq_id in sorted(expected_ids & actual_ids, key=int):
        equation = data[eq_id]
        if not isinstance(equation, dict):
            problems.append(f"equation {eq_id}: expected an object")
            continue
        if not isinstance(equation.get("name"), str) or not equation["name"].strip():
            problems.append(f"equation {eq_id}: missing equation name")
        if not isinstance(equation.get("domain"), str) or not equation["domain"].strip():
            problems.append(f"equation {eq_id}: missing domain")
        for arm in ARMS:
            row = equation.get(arm)
            if not isinstance(row, dict):
                problems.append(f"equation {eq_id}: missing {arm} record")
                continue
            if row.get("condition") != arm:
                problems.append(f"equation {eq_id}/{arm}: condition field is {row.get('condition')!r}")
            if row.get("completed") is not True:
                problems.append(f"equation {eq_id}/{arm}: record is not terminal")
            if not isinstance(row.get("success"), bool):
                problems.append(f"equation {eq_id}/{arm}: missing boolean success field")
            if not isinstance(row.get("fit_status"), str):
                problems.append(f"equation {eq_id}/{arm}: missing fit_status")
            if not isinstance(row.get("evaluation_status"), str):
                problems.append(f"equation {eq_id}/{arm}: missing evaluation_status")
    return problems


def validate_provenance(data, seed):
    problems = []
    if not isinstance(data, dict):
        return ["provenance_map_exp1.json: expected a JSON object"]
    if type(data.get("seed")) is not int or data["seed"] != seed:
        problems.append(f"provenance_map_exp1.json: records seed {data.get('seed')!r}, expected {seed}")
    for field in ("source_revision", "benchmark_script_sha256", "engine_version", "model_string"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"provenance_map_exp1.json: missing {field}")
    for field in ("populations", "niterations"):
        if type(data.get(field)) is not int or data[field] <= 0:
            problems.append(f"provenance_map_exp1.json: invalid {field}")
    if not isinstance(data.get("flags"), dict):
        problems.append("provenance_map_exp1.json: missing flags object")
    return problems


def gather_seed(root: Path, seed: int):
    directory = seed_dir(root, seed)
    entry = {"directory": str(directory), "files": {}, "problems": []}
    parsed = {}
    if not directory.is_dir():
        entry["problems"].append(f"results directory missing: {directory}")
    else:
        for name in REQUIRED:
            path = directory / name
            if not path.is_file() or path.stat().st_size == 0:
                entry["problems"].append(f"{name}: missing or empty")
                continue
            shape, problem, data = describe_json(path)
            if problem:
                entry["problems"].append(f"{name}: {problem}")
                continue
            entry["files"][name] = {
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "structure": shape,
            }
            parsed[name] = data
        if "exp1_ablation_results.json" in parsed:
            entry["problems"].extend(validate_core15_results(parsed["exp1_ablation_results.json"]))
        if "provenance_map_exp1.json" in parsed:
            entry["problems"].extend(validate_provenance(parsed["provenance_map_exp1.json"], seed))
        commit = git_last_commit(directory)
        if commit:
            entry["last_commit"] = commit
    provenance = parsed.get("provenance_map_exp1.json")
    if isinstance(provenance, dict):
        entry["provenance"] = {
            key: provenance.get(key)
            for key in ("seed", "source_revision", "benchmark_script_sha256", *PROTOCOL_FIELDS)
        }
    entry["status"] = "complete" if not entry["problems"] else "incomplete"
    return entry


def cross_seed_problems(per_seed, seeds):
    available = [
        per_seed[str(seed)].get("provenance")
        for seed in seeds if per_seed[str(seed)].get("provenance")
    ]
    if len(available) < 2:
        return []
    problems = []
    for field in ("source_revision", "benchmark_script_sha256", *PROTOCOL_FIELDS):
        values = {json.dumps(item.get(field), sort_keys=True) for item in available}
        if len(values) > 1:
            problems.append(f"cross-seed provenance mismatch: {field} differs across seeds")
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--results-root", required=True, help="e.g. hypatiax/data/results/ablation")
    parser.add_argument("--seeds", required=True, help="fixed ordered set: 42,99,123,777,2024")
    parser.add_argument("--run-map", default="", help="optional 'seed:run_id,...' from dispatcher")
    args = parser.parse_args(argv)

    root = Path(args.results_root)
    seeds = parse_seeds(args.seeds)
    run_map = parse_run_map(args.run_map)
    per_seed = {}
    for seed in seeds:
        entry = gather_seed(root, seed)
        if seed in run_map:
            entry["workflow_run_id"] = run_map[seed]
        per_seed[str(seed)] = entry

    cross_problems = cross_seed_problems(per_seed, seeds)
    manifest = {
        "schema_version": 2,
        "experiment": "exp1_ablation_seeds",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "results_root": str(root),
        "seeds": seeds,
        "expected_equations": 15,
        "expected_arms": list(ARMS),
        "required_files": list(REQUIRED),
        "cross_seed_problems": cross_problems,
        "all_complete": (
            all(entry["status"] == "complete" for entry in per_seed.values())
            and not cross_problems
        ),
        "per_seed": per_seed,
    }
    output_dir = root / OUT_SUBDIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / MANIFEST_NAME
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "### exp1_ablation_seeds - validated results", "",
        "| seed | status | Core-15 arms | directory | run |", "|---:|---|---:|---|---|",
    ]
    for seed in seeds:
        entry = per_seed[str(seed)]
        count = "15 x 3" if entry["status"] == "complete" else "invalid/incomplete"
        lines.append(
            f"| {seed} | {entry['status']} | {count} | {entry['directory']} | "
            f"{entry.get('workflow_run_id', '-')} |"
        )
        for problem in entry["problems"]:
            lines.append(f"|  | - {problem} | | | |")
    for problem in cross_problems:
        lines.append(f"|  | - {problem} | | | |")
    report = "\n".join(lines)
    print(report)
    print(f"\nmanifest: {output_path}")
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(report + "\n")

    if not manifest["all_complete"]:
        bad = [seed for seed in seeds if per_seed[str(seed)]["status"] != "complete"]
        print(
            f"::error::exp1_ablation_seeds incomplete/inconsistent: seeds={bad}, "
            f"cross_seed_problems={cross_problems}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
