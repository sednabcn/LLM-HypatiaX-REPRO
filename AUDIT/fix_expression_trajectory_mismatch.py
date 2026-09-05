#!/usr/bin/env python3
"""
fix_expression_trajectory_mismatch.py

Repairs the data-integrity bug found while independently verifying the
Nguyen-12 rebuild (audit item 1): for some PySR-only records, the
top-level `expression` field does not match the model that was actually
fit and scored -- it holds an unrelated expression string. The correct
model survives in `trajectory[-1]["best_expression"]` (the PySR
hall-of-fame snapshot), which reproduces the record's own reported R^2
when rescored.

ROOT CAUSE: not found. The script that generates these result files
(reads PySR's hall_of_fame.csv, writes both `expression` and
`trajectory`) is not present anywhere in this repository -- same
situation as the missing exp3_nguyen12_hybrid50v.json (see item 1's
provenance note). Without that generator, the actual point of failure
(e.g. an off-by-one index into the hall-of-fame table, a race between
the trajectory monitor thread and final-result serialization, or a
stale variable carried over between equations in a loop) cannot be
located and patched at the source. This script instead repairs *already
generated* result files by detecting the mismatch and correcting it,
and should be re-run on any newly generated file until the upstream
generator (wherever it lives) is found and fixed directly.

WHAT IT DOES, per record with both `expression` and `trajectory`:
  1. Rescore `expression` against the record's own stored extrapolation
     data (X_extrap / y_extrap) and compare to the reported R^2.
  2. If they disagree beyond `tol`, rescore
     `trajectory[-1]["best_expression"]` instead.
  3. If THAT matches the reported R^2, treat it as the real fitted
     model: overwrite `expression` with it (Python-operator form, `^`
     normalized to `**`), and record what was changed under a new
     `_expression_repair` key -- the original corrupted string is kept
     there, not silently discarded.
  4. If neither matches, leave the record untouched and flag it loudly
     for manual investigation -- this script never invents a value.

Usage:
    # Dry run (report only, writes nothing):
    python3 fix_expression_trajectory_mismatch.py path/to/result.json

    # Apply repairs, write to a new file (recommended):
    python3 fix_expression_trajectory_mismatch.py path/to/result.json \
        --write path/to/result.repaired.json

    # Apply repairs in place (only once you trust the dry run):
    python3 fix_expression_trajectory_mismatch.py path/to/result.json --in-place
"""
import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np


def _parse_numeric_array(raw, n_cols=1):
    """Parse numpy's str()/repr() serialization of an array (not JSON)
    into a plain Python list of rows, preserving row-major order.
    Always returns a list of rows (each row a list), even for n_cols=1,
    so callers can uniformly index row[i]."""
    if raw is None:
        return None
    if isinstance(raw, list):
        if raw and not isinstance(raw[0], list):
            return [[v] for v in raw]
        return raw
    tokens = re.findall(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?", raw)
    vals = [float(t) for t in tokens]
    n_rows = len(vals) // n_cols
    return [vals[i * n_cols:(i + 1) * n_cols] for i in range(n_rows)]


def _flatten(rows):
    """Flatten a list-of-rows (each a 1-element list) back to a flat list,
    used for the 1-D y arrays."""
    return [r[0] for r in rows]


def _r2(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return float("nan")
    return 1.0 - ss_res / ss_tot


_SAFE_NS = {"sin": np.sin, "cos": np.cos, "log": np.log,
            "sqrt": np.sqrt, "exp": np.exp}


def _score_expression(expr, varnames, X, y):
    """Evaluate `expr` at X and return R^2 against y, or None on error."""
    ns = dict(_SAFE_NS)
    for i, v in enumerate(varnames):
        ns[v] = np.array([row[i] for row in X])
    try:
        with np.errstate(all="ignore"):
            y_pred = eval(expr, {"__builtins__": {}}, ns)
        if np.isscalar(y_pred):
            y_pred = np.full(len(y), y_pred)
        y_pred = np.asarray(y_pred)
        if np.iscomplexobj(y_pred):
            if np.any(np.abs(y_pred.imag) > 1e-9):
                return None  # genuinely complex output -> not comparable
            y_pred = y_pred.real
        if np.any(np.isnan(y_pred)):
            return None
        return _r2(y, y_pred)
    except Exception:
        return None


def repair_file(path, tol=1e-4):
    """Returns (data, report) where report is a list of dicts describing
    every record checked and what (if anything) was repaired."""
    data = json.loads(Path(path).read_text())
    pc_by_id = {r["nguyen_id"]: r for r in data.get("paired_comparison", [])}
    report = []

    for system, key in [("hypatiax", "h"), ("pysr", "p")]:
        for rec in data.get("results", {}).get(system, []):
            meta = rec["metadata"]
            nid = meta["nguyen_id"]
            varnames = list(meta["variable_ranges"].keys())
            n_vars = len(varnames)

            X = _parse_numeric_array(meta.get("X_extrap"), n_vars)
            y_rows = _parse_numeric_array(meta.get("y_extrap"), 1)
            y = _flatten(y_rows) if y_rows else None
            if not X or not y:
                continue

            stored_r2 = pc_by_id.get(nid, {}).get(f"{key}_r2")
            if stored_r2 is None:
                continue

            top_expr = rec.get("expression")
            top_r2 = _score_expression(top_expr, varnames, X, y) if top_expr else None
            top_ok = top_r2 is not None and abs(top_r2 - stored_r2) < tol

            entry = {
                "nguyen_id": nid, "system": system,
                "stored_r2": stored_r2, "top_level_r2": top_r2,
                "top_level_ok": top_ok, "action": "none",
            }

            if not top_ok:
                traj = rec.get("trajectory") or []
                traj_expr_raw = traj[-1].get("best_expression") if traj else None
                if traj_expr_raw:
                    traj_expr = traj_expr_raw.replace("^", "**")
                    traj_r2 = _score_expression(traj_expr, varnames, X, y)
                    entry["trajectory_r2"] = traj_r2
                    if traj_r2 is not None and abs(traj_r2 - stored_r2) < tol:
                        rec["_expression_repair"] = {
                            "original_expression": top_expr,
                            "reason": "top-level expression did not reproduce "
                                      "stored R^2; replaced with "
                                      "trajectory[-1].best_expression, which does",
                        }
                        rec["expression"] = traj_expr
                        entry["action"] = "repaired_from_trajectory"
                    else:
                        entry["action"] = "UNRESOLVED -- neither field reproduces stored R^2"
                else:
                    entry["action"] = "UNRESOLVED -- no trajectory data to fall back on"

            report.append(entry)

    return data, report


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("result_file", type=Path)
    ap.add_argument("--write", type=Path, default=None,
                     help="Write repaired JSON to this path (does not touch the original).")
    ap.add_argument("--in-place", action="store_true",
                     help="Overwrite the original file. Only use after reviewing a dry run.")
    ap.add_argument("--tol", type=float, default=1e-4)
    args = ap.parse_args()

    data, report = repair_file(args.result_file, tol=args.tol)

    n_checked = len(report)
    n_ok = sum(1 for e in report if e["top_level_ok"])
    n_repaired = sum(1 for e in report if e["action"] == "repaired_from_trajectory")
    n_unresolved = sum(1 for e in report if e["action"].startswith("UNRESOLVED"))

    print(f"Checked {n_checked} records in {args.result_file.name}")
    print(f"  Already correct:        {n_ok}")
    print(f"  Repaired from trajectory: {n_repaired}")
    print(f"  Unresolved (flagged):    {n_unresolved}")
    print()

    for e in report:
        if e["action"] != "none":
            print(f"  {e['nguyen_id']:5} [{e['system']:8}] stored_r2={e['stored_r2']:.6f} "
                  f"top_level_r2={e['top_level_r2']}  -> {e['action']}")

    if n_unresolved:
        print()
        print("WARNING: some records could not be repaired automatically. "
              "These need manual investigation -- do not trust their "
              "'expression' field for anything until resolved.")

    if args.in_place:
        Path(args.result_file).write_text(json.dumps(data, indent=2))
        print(f"\nWrote repairs in place to {args.result_file}")
    elif args.write:
        args.write.write_text(json.dumps(data, indent=2))
        print(f"\nWrote repaired copy to {args.write}")
    else:
        print("\n(Dry run only -- pass --write PATH or --in-place to save changes.)")

    sys.exit(1 if n_unresolved else 0)


if __name__ == "__main__":
    main()
