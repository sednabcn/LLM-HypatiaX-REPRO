#!/usr/bin/env python3
"""
rescore_seed42.py
==================

The real scoring step for rescore_nguyen12_seed42.yml.

experiment_protocol_nguyen12.py is an experiment *runner* (it defines the
12 equations and drives fresh PySR/HypatiaX fits) -- it has no
--input/--rsq-threshold/--output CLI, so it cannot be used to rescore an
*existing* raw result file. This script does that instead: it reads a raw
result file shaped like exp3_nguyen12_seed42.json (results.hypatiax /
results.pysr, each a list of 12 per-equation dicts with
metadata.nguyen_id and evaluation.r2), applies the paper's Rsq threshold,
and emits the flat pass/fail schema AUDIT/diff_rescore_vs_table.py
expects:

    {"N-1": {"P": bool, "H": bool}, ...}

Usage:
    python AUDIT/rescore_seed42.py \
        --input hypatiax/data/results/extrapolation/exp3_nguyen12_seed42.json \
        --rsq-threshold 0.9999 \
        --output rescored_seed42_output.json
"""
import argparse
import json
import re
import sys

SYSTEM_TO_FLAG = {"pysr": "P", "hypatiax": "H"}


def eq_key(nguyen_id: str) -> str:
    """'N1' -> 'N-1', 'N12' -> 'N-12' (matches tab_nguyen12_reference.json)."""
    m = re.match(r"N(\d+)$", nguyen_id)
    if not m:
        raise ValueError(f"Unrecognized nguyen_id format: {nguyen_id!r}")
    return f"N-{int(m.group(1))}"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, help="Raw result JSON to score")
    ap.add_argument("--rsq-threshold", type=float, default=0.9999)
    ap.add_argument("--output", required=True, help="Where to write the scored JSON")
    args = ap.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    if "results" not in data:
        sys.exit(f"::error::{args.input} has no top-level 'results' key -- "
                  f"unexpected schema, cannot score.")

    out = {}
    for system, flag in SYSTEM_TO_FLAG.items():
        entries = data["results"].get(system)
        if entries is None:
            sys.exit(f"::error::{args.input} is missing results.{system}")
        for entry in entries:
            nid = entry["metadata"]["nguyen_id"]
            key = eq_key(nid)
            r2 = entry.get("evaluation", {}).get("r2")
            passed = r2 is not None and r2 >= args.rsq_threshold
            out.setdefault(key, {})[flag] = passed

    with open(args.output, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)

    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
