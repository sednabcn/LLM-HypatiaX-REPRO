#!/usr/bin/env python3
"""
Diff a fresh per-equation rescore of exp3_nguyen12_seed42.json against the
bolded P/H cells currently hard-coded into tab:nguyen12.

This is a helper for rescore_nguyen12_seed42.yml. It does not exist in the
repo yet -- add it wherever the workflow's checkout expects it (repo root,
or update the workflow's `python diff_rescore_vs_table.py` call site to
match wherever it actually lives).

Expects `--rescored` to be JSON shaped like:
    {"N-1": {"P": true, "H": true}, "N-2": {...}, ...}
i.e. per-equation pass/fail booleans at the paper's Rsq>=0.9999 threshold.
Adjust `load_rescored()` below to match whatever
experiment_protocol_nguyen12.py actually emits -- this assumes a flat
per-equation boolean dict, which may not match its real output shape.
"""
import argparse
import json
import sys


def load_json(path):
    with open(path) as f:
        return json.load(f)


def load_rescored(path):
    """Adapt this if experiment_protocol_nguyen12.py's real output schema
    differs from the flat {"N-1": {"P": bool, "H": bool}} shape assumed
    here."""
    return load_json(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rescored", required=True)
    ap.add_argument("--reference", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rescored = load_rescored(args.rescored)
    reference = load_json(args.reference)

    rows = []
    mismatches = 0
    for eq in sorted(reference, key=lambda k: int(k.split("-")[1])):
        ref = reference[eq]
        got = rescored.get(eq, {"P": None, "H": None})
        p_match = got["P"] == ref["P"]
        h_match = got["H"] == ref["H"]
        if not (p_match and h_match):
            mismatches += 1
        rows.append((eq, ref["P"], got["P"], p_match, ref["H"], got["H"], h_match))

    lines = [
        "# Nguyen-12 seed-42 rescore vs. tab:nguyen12 diff",
        "",
        f"Mismatched equations: {mismatches} / {len(rows)}",
        "",
        "| Eq | Table P | Rescore P | match | Table H | Rescore H | match |",
        "|----|---------|-----------|-------|---------|-----------|-------|",
    ]
    for eq, tp, rp, pm, th, rh, hm in rows:
        lines.append(
            f"| {eq} | {tp} | {rp} | {'OK' if pm else 'MISMATCH'} "
            f"| {th} | {rh} | {'OK' if hm else 'MISMATCH'} |"
        )

    report = "\n".join(lines)
    with open(args.out, "w") as f:
        f.write(report)

    print(report)
    if mismatches:
        sys.exit(1)  # non-zero exit so the Action visibly flags the run


if __name__ == "__main__":
    main()
