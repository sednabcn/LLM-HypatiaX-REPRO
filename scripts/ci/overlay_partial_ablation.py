#!/usr/bin/env python3
"""Overlay a PARTIAL exp1_ablation re-run onto the committed results so the aggregate
step sees every equation.

Why: a dispatch with task_ids_override (e.g. "physics") runs one shard, but the merge
requires all 15 equations x all arms.  Without this step that run always fails with
"equations missing from all shards".

Rules (kept deliberately conservative):
  * base  = committed exp1_ablation_checkpoint.json, then committed *_shard<N>.json (in order)
  * new   = checkpoints from this run's downloaded artifacts; they WIN
  * an equation is replaced as a WHOLE entry -- arms from different runs are never mixed
  * if the artifacts alone already cover every equation, nothing is changed (full run)
  * if the overlay is still incomplete, exit 1 and name what is missing
  * writes overlay_manifest.json recording where every equation came from
"""
from __future__ import annotations
import argparse, glob, json, os, re, shutil, sys

CKPT = "exp1_ablation_checkpoint"


def _load(path):
    try:
        with open(path) as fh:
            d = json.load(fh)
    except Exception as exc:                      # unreadable / corrupt -> skip, say so
        print(f"  skip {path}: {type(exc).__name__}: {exc}")
        return None
    return d if isinstance(d, dict) and d else None


def _shard_no(p):
    m = re.search(r"_shard(\d+)\.json$", p)
    return int(m.group(1)) if m else -1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", required=True)
    ap.add_argument("--artifacts-dir", required=True)
    ap.add_argument("--n-equations", type=int, default=15)
    ap.add_argument("--nollm", action="store_true", help="the no-LLM arm is required")
    a = ap.parse_args()
    arms = ["pysr_only", "hypatia"] + (["hypatia_nollm"] if a.nollm else [])
    want = [str(i) for i in range(a.n_equations)]

    new_files = sorted(glob.glob(os.path.join(a.artifacts_dir, "*", f"{CKPT}_shard*.json")),
                       key=_shard_no)
    new, new_src = {}, {}
    for p in new_files:
        d = _load(p)
        if d:
            for k, v in d.items():
                new[str(k)] = v
                new_src[str(k)] = "artifact:" + os.path.relpath(p, a.artifacts_dir)
    print(f"new equations from this run: {sorted(new, key=int)}")
    if not new:
        print("::error::no readable shard checkpoint in the downloaded artifacts")
        return 1
    if all(k in new for k in want):
        print("artifacts already cover every equation - nothing to overlay")
        return 0

    base, base_src = {}, {}
    base_files = [os.path.join(a.results_dir, f"{CKPT}.json")] + sorted(
        glob.glob(os.path.join(a.results_dir, f"{CKPT}_shard*.json")), key=_shard_no)
    for p in base_files:
        if os.path.isfile(p):
            d = _load(p)
            if d:
                print(f"committed base: {os.path.relpath(p, a.results_dir)} ({len(d)} equations)")
                for k, v in d.items():
                    base[str(k)] = v
                    base_src[str(k)] = "committed:" + os.path.basename(p)

    merged, src = dict(base), dict(base_src)
    merged.update(new)
    src.update(new_src)

    problems = []
    for k in want:
        e = merged.get(k)
        if not isinstance(e, dict):
            problems.append(f"eq {k}: missing")
            continue
        miss = [m for m in arms if not isinstance(e.get(m), dict)]
        if miss:
            problems.append(f"eq {k} ({e.get('name', '?')}): missing arm(s) {miss} [from {src[k]}]")
    if problems:
        print("::error::overlay is still incomplete - run the missing domains (leave "
              "task_ids_override blank for a full run):")
        for p in problems:
            print("  " + p)
        return 1

    # one merged source, so the merge cannot see an equation twice
    first = new_files[0]
    folder = os.path.dirname(first)
    for p in new_files:
        shutil.move(p, p + ".pre_overlay")
    res_old = glob.glob(os.path.join(a.artifacts_dir, "*", "exp1_ablation_results_shard*.json"))
    for p in res_old:
        shutil.move(p, p + ".pre_overlay")
    n = _shard_no(first)
    for stem in (CKPT, "exp1_ablation_results"):
        with open(os.path.join(folder, f"{stem}_shard{n}.json"), "w") as fh:
            json.dump({k: merged[k] for k in want}, fh, indent=2)
    manifest = {"github_run_id": os.environ.get("GITHUB_RUN_ID"),
                "replaced_by_this_run": sorted(new, key=int),
                "source_per_equation": {k: src[k] for k in want}}
    for d in (folder, a.results_dir):
        with open(os.path.join(d, "overlay_manifest.json"), "w") as fh:
            json.dump(manifest, fh, indent=2)
    print(f"overlay complete: {len(new)} equation(s) from this run, "
          f"{len(want) - len(new)} from committed results")
    return 0


if __name__ == "__main__":
    sys.exit(main())
