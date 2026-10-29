#!/usr/bin/env python3
"""
flatten_results.py - adapter: nested/sharded HypatiaX result JSON -> flat JSONL records
for phase2_close.py / phase3_close.py.

It NEVER invents values. A field it cannot find is written as null, so the closure
scripts' schema check fails and tells you exactly what the runners must log.

Step 1 - look at your data (no output written):
    python flatten_results.py --inspect --root hypatiax/data/results/ablation/exp1_ablation

Step 2 - flatten one directory per system/configuration:
    python flatten_results.py --root <dir> --system pure_llm --out p2/pure_llm.jsonl
    python flatten_results.py --root <dir> --system hds_v50_2 --out p2/hds.jsonl
    # Phase 3: label the configuration being run
    python flatten_results.py --root <dir> --system hds_v50_2 --component probe --out p3/probe.jsonl
    python flatten_results.py --root <dir> --system hds_v50_2 --component full  --out p3/full.jsonl

Record discovery: any dict holding an equation id (equation/equation_name/name/case/...) and
an R2 value (r2/test_r2/r2_test/...). If a case dict instead holds per-method sub-dicts that
each carry an R2, one record is emitted per sub-dict; pick methods with --method (repeatable,
key=system_label, e.g. --method pure_llm=pure_llm --method hybrid=hds_v50_2).

Excluded by default (override with --include-excluded): rescued shards, checkpoints, .bak,
exploratory/, pre_prompt_fix/, pre_fix. Duplicate (equation, seed) rows are reported, never
silently resolved; choose with --on-duplicate {error,first,last}.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sys
from collections import Counter

ALIASES = {
    "equation": ["equation", "equation_id", "equation_name", "eq", "eq_id", "case", "case_id", "name", "problem"],
    "r2": ["r2", "test_r2", "r2_test", "r2_score", "r2_canonical", "r_squared", "R2"],
    "seed": ["seed", "random_seed", "rng_seed"],
    "split_id": ["split_id", "split_hash", "split", "split_protocol_id"],
    "status": ["status", "outcome", "result_status"],
    "formula": ["formula", "best_expression", "expression", "discovered_formula", "final_formula", "best_formula", "equation_str"],
    "generation_path": ["generation_path", "llm_mode_used", "path", "formula_source", "source"],
    "llm_called": ["llm_called", "llm_used", "used_llm"],
    "bypass_used": ["bypass_used", "bypass", "hardcoded_bypass", "used_bypass"],
    "runtime_s": ["runtime_s", "total_time_s", "elapsed_s", "elapsed", "wall_clock_s", "time_s", "duration_s", "runtime"],
    "timeout_s": ["timeout_s", "timeout", "time_budget_s", "budget_s"],
    "model_id": ["model_id", "model", "llm_model"],
    "code_version": ["code_version", "engine_version", "git_commit", "commit", "git_sha", "version"],
    "config_hash": ["config_hash", "config_sha", "cfg_hash"],
    "evaluator_version": ["evaluator_version", "eval_version", "recovery_eval_version"],
    "config_diff": ["config_diff", "ablation_diff"],
}
DEFAULT_EXCLUDE = ["_rescued_", "_checkpoint", "checkpoint", ".bak", "/exploratory/", "pre_prompt_fix",
                   "pre_fix", "/shards/", "_saved/", "__pycache__", "aggregate_run"]
OUT_FIELDS = ["system", "ablated_component", "config_diff", "equation", "seed", "split_id", "r2", "status",
              "formula", "generation_path", "llm_called", "bypass_used", "runtime_s", "timeout_s",
              "model_id", "code_version", "config_hash", "evaluator_version", "_source"]


def pick(d, field):
    for k in ALIASES[field]:
        if k in d and not isinstance(d[k], (dict, list)):
            return d[k], k
    return None, None


def has(d, field):
    return pick(d, field)[1] is not None


def walk(node, path=()):
    """Yield (path, dict) for every dict in the tree."""
    if isinstance(node, dict):
        yield path, node
        for k, v in node.items():
            yield from walk(v, path + (str(k),))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, path + (str(i),))


def find_cases(tree, method_map):
    """Return list of (system_hint, record_dict, path) found in one JSON tree."""
    out = []
    for path, d in walk(tree):
        if not has(d, "equation"):
            continue
        if has(d, "r2"):
            out.append((None, d, path))
            continue
        for k, v in d.items():
            if isinstance(v, dict) and has(v, "r2") and (not method_map or k in method_map):
                merged = {**{kk: vv for kk, vv in d.items() if not isinstance(vv, (dict, list))}, **v}
                out.append((k, merged, path + (k,)))
    return out


def seed_from_name(fp):
    m = re.search(r"seed[_]?(\d+)", fp)
    return int(m.group(1)) if m else None


def to_bool(v):
    if isinstance(v, bool) or v is None:
        return v
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "yes", "y")
    return bool(v)


def to_float(v):
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


def excluded(fp, patterns):
    p = fp.replace("\\", "/")
    return any(x in p for x in patterns)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", nargs="+", required=True, help="directories or globs of result JSON")
    ap.add_argument("--inspect", action="store_true", help="print discovered structure; write nothing")
    ap.add_argument("--system", help="system label to write (pure_llm / hds_v50_2 ...)")
    ap.add_argument("--component", default=None, help="Phase 3: ablated component, or 'full'")
    ap.add_argument("--method", action="append", default=[], metavar="KEY=LABEL",
                    help="per-method sub-dict key -> system label (repeatable)")
    ap.add_argument("--out", help="output JSONL")
    ap.add_argument("--include-excluded", action="store_true")
    ap.add_argument("--on-duplicate", choices=["error", "first", "last"], default="error")
    ap.add_argument("--derive-split-id", action="store_true",
                    help="DERIVE split_id=hash(equation,seed) when absent. Only valid if the runner uses "
                         "a deterministic split from the seed; marked 'derived:' so it is visible.")
    ap.add_argument("--set", action="append", default=[], metavar="FIELD=VALUE",
                    help="constant for a field the files do not contain (e.g. timeout_s=300). "
                         "Use only for facts you know to be true of the whole run.")
    ap.add_argument("--r2-field", help="exact key to use as R2 (e.g. extrap_r2_far, train_r2). REQUIRED when the "
                    "files hold several R2 variants; the choice is a scientific decision, not guessed.")
    args = ap.parse_args()
    if args.r2_field:
        ALIASES["r2"] = [args.r2_field]

    method_map = dict(m.split("=", 1) for m in args.method)
    consts = dict(s.split("=", 1) for s in args.set)
    files = []
    for r in args.root:
        if os.path.isdir(r):
            files += glob.glob(os.path.join(r, "**", "*.json"), recursive=True)
        else:
            files += glob.glob(r, recursive=True)
    files = sorted(set(files))
    skipped = [f for f in files if not args.include_excluded and excluded(f, DEFAULT_EXCLUDE)]
    files = [f for f in files if f not in skipped]
    print(f"{len(files)} JSON files to read, {len(skipped)} excluded by default patterns", file=sys.stderr)

    rows, unreadable, no_cases = [], [], []
    for fp in files:
        try:
            with open(fp, encoding="utf-8") as f:
                tree = json.load(f)
        except (OSError, json.JSONDecodeError):
            unreadable.append(fp)
            continue
        prov = {}
        pp = os.path.join(os.path.dirname(fp), "provenance_map_exp1.json")
        if os.path.isfile(pp):
            try:
                prov = json.load(open(pp, encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                prov = {}
        cases = find_cases(tree, method_map)
        if not cases:
            no_cases.append(fp)
            continue
        for hint, d, path in cases:
            rec = {"_source": f"{fp}::{'/'.join(path)}"}
            for field in ALIASES:
                rec[field], _ = pick(d, field)
            if rec["seed"] is None:
                rec["seed"] = seed_from_name(fp)
            if rec["seed"] is None and prov.get("seed") is not None:
                rec["seed"] = prov["seed"]            # sidecar provenance, same directory
            # bypass_used is DERIVED from the run's own recorded flag state, never assumed:
            # False only if provenance records HYPATIAX_DISABLE_HARDCODED == "1" and clean_run is true.
            pf = prov.get("flags") if isinstance(prov.get("flags"), dict) else None
            if rec["bypass_used"] is None and pf and pf.get("HYPATIAX_DISABLE_HARDCODED") == "1" \
                    and pf.get("clean_run") is True:
                rec["bypass_used"] = False
            if rec["model_id"] is None and prov.get("model_string"):
                rec["model_id"] = prov["model_string"]
            if rec["timeout_s"] is None and d.get("timed_out") is not None:
                pass  # per-condition wall-clocks differ by design; supply explicitly via --set
            rec["r2"] = to_float(rec["r2"])
            rec["runtime_s"] = to_float(rec["runtime_s"])
            rec["timeout_s"] = to_float(rec["timeout_s"])
            rec["llm_called"] = to_bool(rec["llm_called"])
            rec["bypass_used"] = to_bool(rec["bypass_used"])
            for k, v in consts.items():
                if rec.get(k) is None:
                    rec[k] = v
            rec["timeout_s"] = to_float(rec["timeout_s"])
            if rec["split_id"] is None and args.derive_split_id and rec["seed"] is not None:
                rec["split_id"] = "derived:" + hashlib.sha256(f"{rec['equation']}|{rec['seed']}".encode()).hexdigest()[:12]
            rec["system"] = method_map.get(hint, hint) if hint else args.system
            rec["ablated_component"] = None if args.component in (None, "full") else args.component
            if rec["config_diff"] is None:
                rec["config_diff"] = [] if args.component in (None, "full") else [args.component]
            if rec["status"] is None:
                if d.get("timed_out") is True:
                    rec["status"] = "timeout"
                elif d.get("success") is False:
                    rec["status"] = "error"
                else:
                    rec["status"] = "ok" if rec["r2"] is not None else "nan"
            rows.append(rec)

    # ---- inspection report
    cov = {f: sum(1 for r in rows if r.get(f) is not None) for f in OUT_FIELDS if f != "_source"}
    print(f"\nRecords found: {len(rows)} in {len(files) - len(unreadable) - len(no_cases)} files "
          f"({len(no_cases)} files had no case records, {len(unreadable)} unreadable)")
    print("Field coverage (non-null count / total) - anything below 100% will fail the closure schema check:")
    for f, c in cov.items():
        print(f"  {f:20s} {c:6d} / {len(rows)}" + ("" if c == len(rows) else "   <-- INCOMPLETE"))
    keys = Counter((r["system"], r["ablated_component"]) for r in rows)
    print("Records by (system, component):", dict(keys))
    dup = Counter((r["system"], r["ablated_component"], r["equation"], r["seed"]) for r in rows)
    ndup = sum(1 for v in dup.values() if v > 1)
    print(f"Duplicate (system, component, equation, seed) keys: {ndup}")
    if args.inspect:
        for r in rows[:3]:
            print("\nsample:", json.dumps({k: r[k] for k in OUT_FIELDS}, default=str)[:600])
        return 0

    if not args.out or (not args.system and not method_map):
        print("ERROR: need --out and --system (or --method) to write", file=sys.stderr)
        return 2
    if ndup and args.on_duplicate == "error":
        ex = [k for k, v in dup.items() if v > 1][:5]
        print(f"ERROR: {ndup} duplicate keys, e.g. {ex}. Decide the authoritative source or use "
              f"--on-duplicate first|last.", file=sys.stderr)
        return 1
    seen, final = {}, []
    for r in rows:
        k = (r["system"], r["ablated_component"], r["equation"], r["seed"])
        if k in seen and args.on_duplicate == "first":
            continue
        if k in seen and args.on_duplicate == "last":
            final[seen[k]] = r
            continue
        seen[k] = len(final)
        final.append(r)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for r in final:
            f.write(json.dumps({k: r[k] for k in OUT_FIELDS}, default=str) + "\n")
    print(f"\nWrote {len(final)} records -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
