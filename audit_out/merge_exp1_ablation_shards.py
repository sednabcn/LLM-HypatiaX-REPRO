#!/usr/bin/env python3
"""
Merge per-shard exp1_ablation checkpoints into one all-15 checkpoint.

CI mode  : --artifacts-dir DIR  (DIR/results-exp1_ablation-shard<N>/exp1_ablation_checkpoint_shard<N>.json)
Local    : --from-dir DIR       (DIR/exp1_ablation_checkpoint_shard*.json)

Each shard artifact also contains whatever was committed in the results dir at checkout,
so ONLY the file belonging to the artifact's own shard number is read (stale files ignored).
Keys are global CORE_15 indices (FIX-SHARDKEY), so shards are disjoint by construction.
Exits 1 unless all 15 equations carry every required arm.
"""
import argparse, json, os, re, sys
from pathlib import Path

ap = argparse.ArgumentParser()
g = ap.add_mutually_exclusive_group(required=True)
g.add_argument("--artifacts-dir")
g.add_argument("--from-dir")
ap.add_argument("--out", required=True)
ap.add_argument("--n-equations", type=int, default=15)
ap.add_argument("--nollm", choices=["0", "1"], default=os.environ.get("HYPATIAX_NOLLM_ARM", "0") or "0")
a = ap.parse_args()

arms = ["pysr_only", "hypatia"] + (["hypatia_nollm"] if a.nollm == "1" else [])

sources = []  # (label, path)
if a.artifacts_dir:
    for d in sorted(Path(a.artifacts_dir).iterdir()):
        m = re.fullmatch(r"results-exp1_ablation-shard(\d+)", d.name)
        if not (d.is_dir() and m):
            continue
        n = m.group(1)
        p = d / f"exp1_ablation_checkpoint_shard{n}.json"
        if not p.exists():
            p = d / f"exp1_ablation_results_shard{n}.json"
        sources.append((f"shard{n}", p))
else:
    for p in sorted(Path(a.from_dir).glob("exp1_ablation_checkpoint_shard*.json")):
        sources.append((p.stem.split("_")[-1], p))

if not sources:
    sys.exit("::error::no shard checkpoints found")

def complete(e):
    return isinstance(e, dict) and all(isinstance(e.get(c), dict) for c in arms)

merged, owner = {}, {}
for label, p in sources:
    if not p.exists():
        print(f"::error::{label}: {p} missing"); continue
    data = json.loads(p.read_text())
    for k, e in data.items():
        if not isinstance(e, dict):
            continue
        if k in merged:
            # same key from two shards: keep the complete one; two complete ones must agree on identity
            if complete(merged[k]) and complete(e):
                if merged[k].get("name") != e.get("name"):
                    sys.exit(f"::error::key {k} is '{merged[k].get('name')}' in {owner[k]} but '{e.get('name')}' in {label}")
                print(f"::warning::key {k} ({e.get('name')}) present in {owner[k]} and {label}; keeping {owner[k]}")
                continue
            if complete(merged[k]) and not complete(e):
                continue
        merged[k], owner[k] = e, label

missing = [str(i) for i in range(a.n_equations) if str(i) not in merged]
incomplete = {k: [c for c in arms if not isinstance(e.get(c), dict)]
              for k, e in merged.items() if not complete(e)}
print(f"{'idx':>3}  {'equation':<24}" + "".join(f"{c:>15}" for c in arms) + "  shard")
for i in range(a.n_equations):
    e = merged.get(str(i))
    if e is None:
        print(f"{i:>3}  {'<MISSING>':<24}"); continue
    print(f"{i:>3}  {str(e.get('name')):<24}" + "".join(f"{'ok' if isinstance(e.get(c), dict) else '--':>15}" for c in arms) + f"  {owner[str(i)]}")

if missing or incomplete:
    if missing: print(f"::error::equations missing from all shards: {missing}")
    for k, miss in incomplete.items(): print(f"::error::equation {k} ({merged[k].get('name')}) lacks arm(s) {miss}")
    sys.exit(1)

Path(a.out).write_text(json.dumps(dict(sorted(merged.items(), key=lambda kv: int(kv[0]))), indent=2))
print(f"merged {len(merged)} equations x {len(arms)} arms -> {a.out}")
