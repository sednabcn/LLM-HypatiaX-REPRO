#!/usr/bin/env python3
"""
merge_targeted_rerun.py

Merges a targeted rerun (produced by running
exp3_nguyen12_hybrid50v_02_patched.py with TASK_IDS set to only the
broken equations for one seed) into the real, full 12-equation result
file for that seed -- replacing ONLY the rerun equations' records and
leaving everything else in the target file untouched.

WHY THIS EXISTS: exp3_nguyen12_hybrid50v_02_patched.py refuses to re-run
if its output path already exists (`if _out_path.exists(): ... skip
re-run`), and always writes to a fixed filename
(exp3_nguyen12_seed{seed}.json) regardless of which equations TASK_IDS
filtered it down to. A targeted rerun therefore lands in a SEPARATE
directory as a small, equation-subset file -- this script folds that
subset back into the real file (which uses a different filename pattern,
exp3_nguyen12_seed{seed}_nshardsNN.json, and is never touched by the
rerun itself).

Usage:
    python3 merge_targeted_rerun.py \\
        --source path/to/targeted_rerun/exp3_nguyen12_seed123.json \\
        --target hypatiax/data/results/extrapolation/multi_seed/exp3_nguyen12_seed123_nshards02.json \\
        --task-ids N4

    # Dry run (default): reports what would change, writes nothing.
    # Add --write to actually update --target in place.

Safety:
    - Refuses to merge a nguyen_id that ISN'T present in --source (typo
      guard: if you meant to fix N4 and the source only has N7, this is
      caught, not silently ignored).
    - Refuses to run if --source's config.seed doesn't match --target's
      config.seed (wrong-file guard).
    - Recomputes paired_comparison and summary counts for the WHOLE file
      after merging, not just the touched IDs, so h_recovered/p_recovered
      etc. are never stale relative to the merged records.
    - Always prints a before/after diff for every touched nguyen_id.
"""
import argparse
import json
import sys
from pathlib import Path

RECOVERY_THRESHOLD = 0.9999


def _by_id(records):
    return {r["metadata"]["nguyen_id"]: r for r in records}


def _recompute_paired_comparison_and_summary(data):
    """Rebuild `paired_comparison` and `summary` from `results.hypatiax` /
    `results.pysr` -- the same logic exp3_nguyen12_hybrid50v_02_patched.py
    itself would use, kept independent here so a merge is self-verifying
    rather than trusting whatever the file's old aggregate fields said."""
    h_by_id = _by_id(data["results"]["hypatiax"])
    p_by_id = _by_id(data["results"]["pysr"])
    ids = sorted(set(h_by_id) | set(p_by_id))

    paired = []
    h_recovered = p_recovered = h_recovered_independent = 0
    n_h_copy_of_p = n_same_final_expression = 0

    for nid in ids:
        h = h_by_id.get(nid)
        p = p_by_id.get(nid)
        h_r2 = h["evaluation"]["r2"] if h else None
        p_r2 = p["evaluation"]["r2"] if p else None
        h_ok = h_r2 is not None and h_r2 >= RECOVERY_THRESHOLD
        p_ok = p_r2 is not None and p_r2 >= RECOVERY_THRESHOLD
        h_recovered += int(h_ok)
        p_recovered += int(p_ok)

        h_is_copy = bool(h.get("h_is_copy_of_p")) if h else False
        same_expr = bool(h.get("same_final_expression_as_p")) if h else False
        n_h_copy_of_p += int(h_is_copy)
        n_same_final_expression += int(same_expr)
        h_recovered_independent += int(h_ok and not h_is_copy)

        paired.append({
            "nguyen_id": nid,
            "h_r2": h_r2, "p_r2": p_r2,
            "h_success": h_ok, "p_success": p_ok,
            "h_is_copy_of_p": h_is_copy,
            "same_expression": same_expr,
        })

    n_total = len(ids)
    summary = dict(data.get("summary", {}))  # preserve any extra keys
    summary.update({
        "h_recovered": h_recovered,
        "p_recovered": p_recovered,
        "h_recovered_independent": h_recovered_independent,
        "n_total": n_total,
        "h_rate": h_recovered / n_total if n_total else 0.0,
        "p_rate": p_recovered / n_total if n_total else 0.0,
        "n_completed": n_total,
        "n_independent_h": n_total - n_h_copy_of_p,
        "n_h_copy_of_p": n_h_copy_of_p,
        "n_same_final_expression": n_same_final_expression,
        "complete": True,
    })

    data["paired_comparison"] = paired
    data["summary"] = summary
    return data


def merge(source_path, target_path, task_ids):
    source = json.loads(Path(source_path).read_text())
    target = json.loads(Path(target_path).read_text())

    src_seed = source.get("config", {}).get("seed")
    tgt_seed = target.get("config", {}).get("seed")
    if src_seed is not None and tgt_seed is not None and src_seed != tgt_seed:
        raise ValueError(
            f"Refusing to merge: source seed={src_seed!r} != target seed={tgt_seed!r}. "
            f"This looks like the wrong source/target pair."
        )

    changes = []
    for system in ("hypatiax", "pysr"):
        src_by_id = _by_id(source["results"][system])
        tgt_records = target["results"][system]
        tgt_by_id = _by_id(tgt_records)

        for nid in task_ids:
            if nid not in src_by_id:
                raise ValueError(
                    f"--task-ids includes {nid!r} but it is not present in "
                    f"{source_path}'s results.{system} -- refusing to merge "
                    f"partial/typo'd input. Available IDs there: "
                    f"{sorted(src_by_id)}"
                )
            old = tgt_by_id.get(nid)
            new = src_by_id[nid]
            changes.append({
                "system": system, "nguyen_id": nid,
                "old_r2": old["evaluation"]["r2"] if old else None,
                "new_r2": new["evaluation"]["r2"],
                "old_expression": old.get("expression") if old else None,
                "new_expression": new.get("expression"),
            })
            if old is not None:
                idx = tgt_records.index(old)
                tgt_records[idx] = new
            else:
                tgt_records.append(new)  # shouldn't normally happen, but don't drop data

    target = _recompute_paired_comparison_and_summary(target)
    return target, changes


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True, type=Path,
                     help="Targeted rerun's output JSON (subset of equations)")
    ap.add_argument("--target", required=True, type=Path,
                     help="The real, full result file to merge into")
    ap.add_argument("--task-ids", required=True, nargs="+",
                     help="Nguyen IDs to merge, e.g. --task-ids N4 N7")
    ap.add_argument("--write", action="store_true",
                     help="Actually overwrite --target. Default is dry-run.")
    args = ap.parse_args()

    merged, changes = merge(args.source, args.target, args.task_ids)

    print(f"Merging {args.task_ids} from {args.source.name} into {args.target.name}\n")
    for c in changes:
        print(f"  [{c['system']:8}] {c['nguyen_id']:5} "
              f"R2: {c['old_r2']} -> {c['new_r2']}")
        if c["old_expression"] != c["new_expression"]:
            print(f"             expr: {c['old_expression']!r} -> {c['new_expression']!r}")

    print(f"\nNew summary: {merged['summary']}")

    if args.write:
        args.target.write_text(json.dumps(merged, indent=2))
        print(f"\nWrote merged result to {args.target}")
    else:
        print("\n(Dry run only -- pass --write to save changes.)")


if __name__ == "__main__":
    main()
