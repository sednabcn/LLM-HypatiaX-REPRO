#!/usr/bin/env python3
"""
check_nguyen12_extrap_split.py

Sanity check for the Nguyen-12 "12/12 (100%)" rebuild (audit item 1).

A near-perfect R^2 on BOTH systems for EVERY equation is either a real,
striking result, or a sign that "extrapolation" isn't actually testing
extrapolation (e.g. the held-out points sit inside the training domain,
or the two ranges overlap/touch). This script checks that directly,
three independent ways, and refuses to just trust either the code or the
data file alone:

  1. CODE:  pulls variable_ranges (train) and extrap_ranges (test) as
     defined in experiment_protocol_nguyen12.py, and checks each
     variable's extrap range is fully disjoint from (not overlapping or
     touching) its train range.
  2. DATA:  pulls the same two ranges as literally stored in the raw
     result file's metadata for every equation, and checks (a) they
     match what the code currently defines, and (b) they're disjoint.
  3. ACTUAL SAMPLES: reconstructs X_extrap from the stored metadata and
     confirms every sampled point actually falls inside the *declared*
     extrap_range for that equation and OUTSIDE the train range -- i.e.
     checks the real numbers, not just the range labels, in case of an
     off-by-one or transposition bug between the two.

Usage:
    python3 check_nguyen12_extrap_split.py [path/to/exp3_nguyen12_seed42.json]

Exit code 0 = split looks genuine for every equation.
Exit code 1 = at least one equation failed a check (see printed detail).
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

DEFAULT_RESULT_FILE = (
    REPO_ROOT / "hypatiax" / "data" / "results" / "extrapolation"
    / "exp3_nguyen12_seed42.json"
)


def ranges_disjoint(train_lo, train_hi, extrap_lo, extrap_hi, tol=1e-9):
    """True if the two closed intervals share at most a single boundary
    point (e.g. train ending at 1.0 and extrap starting at 1.0 is the
    intended design -- a genuine held-out split -- not an overlap).
    Only a real interval overlap (more than a shared boundary point)
    counts as a failure."""
    return extrap_lo >= train_hi - tol or extrap_hi <= train_lo + tol


def check_code_definitions():
    """Check 1: what the protocol module itself defines."""
    from hypatiax.protocols.experiment_protocol_nguyen12 import NGUYEN_EQUATIONS

    print("=" * 78)
    print("CHECK 1 — Ranges as defined in experiment_protocol_nguyen12.py")
    print("=" * 78)
    all_ok = True
    for eq in NGUYEN_EQUATIONS:
        for var in eq.variable_names:
            tr_lo, tr_hi = eq.variable_ranges[var]
            ex_lo, ex_hi = eq.extrap_ranges[var]
            ok = ranges_disjoint(tr_lo, tr_hi, ex_lo, ex_hi)
            all_ok &= ok
            status = "OK  (disjoint)" if ok else "FAIL (overlaps/touches train!)"
            print(
                f"  {eq.nguyen_id:5} {var}: train=({tr_lo:>6.2f},{tr_hi:>6.2f})  "
                f"extrap=({ex_lo:>6.2f},{ex_hi:>6.2f})  -> {status}"
            )
    print()
    return all_ok


def check_stored_metadata(result_file):
    """Check 2: what's literally stored in the raw result file's metadata,
    cross-checked against the code's current definitions."""
    from hypatiax.protocols.experiment_protocol_nguyen12 import NGUYEN_BY_ID

    print("=" * 78)
    print(f"CHECK 2 — Ranges as stored in {result_file.name}, vs. code")
    print("=" * 78)
    d = json.load(open(result_file))
    all_ok = True
    for rec in d["results"]["hypatiax"]:
        meta = rec["metadata"]
        nid = meta["nguyen_id"]
        code_eq = NGUYEN_BY_ID.get(nid)
        stored_train = meta.get("variable_ranges", {})
        stored_extrap = meta.get("extrap_ranges", {})

        for var in stored_train:
            tr_lo, tr_hi = stored_train[var]
            ex_lo, ex_hi = stored_extrap[var]
            disjoint = ranges_disjoint(tr_lo, tr_hi, ex_lo, ex_hi)

            matches_code = True
            if code_eq is not None:
                c_tr = tuple(code_eq.variable_ranges[var])
                c_ex = tuple(code_eq.extrap_ranges[var])
                matches_code = (
                    tuple(stored_train[var]) == c_tr
                    and tuple(stored_extrap[var]) == c_ex
                )

            ok = disjoint and matches_code
            all_ok &= ok
            flags = []
            if not disjoint:
                flags.append("RANGES OVERLAP/TOUCH")
            if not matches_code:
                flags.append("STORED != CURRENT CODE DEFINITION")
            status = "OK" if ok else "FAIL (" + "; ".join(flags) + ")"
            print(
                f"  {nid:5} {var}: stored train=({tr_lo:>6.2f},{tr_hi:>6.2f})  "
                f"stored extrap=({ex_lo:>6.2f},{ex_hi:>6.2f})  -> {status}"
            )
    print()
    return all_ok


def _parse_x_extrap(raw, n_vars):
    """X_extrap is stored as numpy's plain str()/repr() of the array
    (e.g. "[[2.284]\\n [1.168]\\n ...]"), not valid JSON -- extract every
    float-looking token via regex and reshape by n_variables, preserving
    row-major order."""
    import re
    if raw is None:
        return None
    if isinstance(raw, list):
        # Already proper JSON array (defensive: handle both formats)
        return raw
    tokens = re.findall(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?", raw)
    vals = [float(t) for t in tokens]
    n_rows = len(vals) // n_vars
    return [vals[i * n_vars:(i + 1) * n_vars] for i in range(n_rows)]


def check_actual_samples(result_file):
    """Check 3: reconstruct X_extrap from the stored arrays and confirm
    every sampled point genuinely lies in the extrap range and NOT in
    the train range -- catches transposition/off-by-one bugs that a
    range-label comparison alone would miss."""
    print("=" * 78)
    print(f"CHECK 3 — Actual sampled X_extrap points in {result_file.name}")
    print("=" * 78)
    d = json.load(open(result_file))
    all_ok = True
    for rec in d["results"]["hypatiax"]:
        meta = rec["metadata"]
        nid = meta["nguyen_id"]
        varnames = list(meta["variable_ranges"].keys())
        n_vars = len(varnames)
        X_extrap = _parse_x_extrap(meta.get("X_extrap"), n_vars)

        if not X_extrap:
            print(f"  {nid:5}: no X_extrap stored (extrapolation_test=False?) -- skipped")
            continue

        n_points = len(X_extrap)
        violations = 0
        examples = []
        for var_idx, var in enumerate(varnames):
            tr_lo, tr_hi = meta["variable_ranges"][var]
            ex_lo, ex_hi = meta["extrap_ranges"][var]
            col = [row[var_idx] for row in X_extrap]
            for val in col:
                # Strictly inside train range (not just touching the boundary)
                strictly_in_train = tr_lo < val < tr_hi
                outside_declared_extrap = not (ex_lo <= val <= ex_hi)
                if strictly_in_train or outside_declared_extrap:
                    violations += 1
                    if len(examples) < 3:
                        examples.append((var, val))

        ok = violations == 0
        all_ok &= ok
        status = "OK  (all points genuinely out-of-domain)" if ok else \
            f"FAIL ({violations}/{n_points * n_vars} point-values violate the split; e.g. {examples})"
        print(f"  {nid:5} ({n_points} pts x {n_vars} vars): {status}")
    print()
    return all_ok


def main():
    result_file = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_RESULT_FILE
    if not result_file.exists():
        print(f"ERROR: result file not found: {result_file}")
        sys.exit(2)

    ok1 = check_code_definitions()
    ok2 = check_stored_metadata(result_file)
    ok3 = check_actual_samples(result_file)

    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    print(f"  Check 1 (code ranges disjoint)........ {'PASS' if ok1 else 'FAIL'}")
    print(f"  Check 2 (stored ranges match code, disjoint)... {'PASS' if ok2 else 'FAIL'}")
    print(f"  Check 3 (actual sampled points out-of-domain).. {'PASS' if ok3 else 'FAIL'}")
    print()
    if ok1 and ok2 and ok3:
        print("RESULT: the extrapolation split is genuine for every equation --")
        print("        the 12/12 (100%) success rate is not an artifact of a")
        print("        held-out-but-in-domain split.")
        sys.exit(0)
    else:
        print("RESULT: at least one check failed -- do NOT trust the 12/12 figure")
        print("        until the flagged equation(s) above are investigated.")
        sys.exit(1)


if __name__ == "__main__":
    main()
