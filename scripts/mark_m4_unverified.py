#!/usr/bin/env python3
"""Flag stored HybridSystemLLMNN (M4) rows that report a score but no formula.

    python scripts/mark_m4_unverified.py            # dry run: count rows/files
    python scripts/mark_m4_unverified.py --apply    # annotate those rows in place

A row is UNVERIFIED when its method starts with "HybridSystemLLMNN", its formula is empty/"N/A"/
"None", and it carries no llm_called field. Such a row (e.g. R2 = 1.0, formula "N/A") cannot be
checked, so it must not be cited. Only the M4 row is touched; PureLLM / ImprovedNN / other rows in
the same file are left exactly as they are. Added keys:
    "provenance_status": "unverified_no_formula"
    "exclude_from_reported_results": true

Caveat: a test's "comparison" / "winner" fields were computed with the M4 score included and are
NOT recomputed. Recompute them from non-excluded rows (or rerun M4) before using them.
Rerun instead of flagging:  re-execute the benchmark that produced the file with the clean flags
(HYPATIAX_DISABLE_HARDCODED=1 HYPATIAX_DISABLE_PROMPT_HINTS=1, HYPATIAX_R2_SIGN_FLIP unset);
the patched engine always returns a formula and logs llm_called.
"""
import argparse, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
RES = ROOT / "hypatiax/data/results"
STATUS = "unverified_no_formula"


def is_unverified(o: dict) -> bool:
    m = o.get("method")
    if not (isinstance(m, str) and m.startswith("HybridSystemLLMNN")):
        return False
    if "llm_called" in o:
        return False
    return str(o.get("formula", "")).strip() in ("", "N/A", "None")


def mark(o, found, apply):
    if isinstance(o, dict):
        if is_unverified(o):
            found[0] += 1
            if apply and o.get("provenance_status") != STATUS:
                o["provenance_status"] = STATUS
                o["exclude_from_reported_results"] = True
        for v in o.values():
            mark(v, found, apply)
    elif isinstance(o, list):
        for v in o:
            mark(v, found, apply)


def scan(apply=False):
    """Return [(path, n_rows_unflagged_or_flagged)] for active files with unverified M4 rows."""
    out = []
    for p in sorted(RES.rglob("*.json")):
        if any(part in ("exploratory", "exp1_ablation_pre_prompt_fix") for part in p.relative_to(RES).parts):
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        found = [0]
        before = json.dumps(data, sort_keys=True)
        mark(data, found, apply)
        if found[0]:
            changed = json.dumps(data, sort_keys=True) != before
            out.append((p, found[0], changed))
            if apply and changed:
                p.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")  # same serialization as the stored files
    return out


def unflagged():
    """Files that still contain an M4 no-formula row without the flag (what the audit checks)."""
    res = []
    for p in sorted(RES.rglob("*.json")):
        if any(part in ("exploratory", "exp1_ablation_pre_prompt_fix") for part in p.relative_to(RES).parts):
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        n = [0]
        def w(o):
            if isinstance(o, dict):
                if is_unverified(o) and o.get("provenance_status") != STATUS:
                    n[0] += 1
                for v in o.values(): w(v)
            elif isinstance(o, list):
                for v in o: w(v)
        w(data)
        if n[0]:
            res.append((p, n[0]))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    hits = scan(apply=a.apply)
    rows = sum(n for _, n, _ in hits)
    print(f"{rows} unverified M4 row(s) in {len(hits)} active file(s)")
    if a.apply:
        print(f"annotated {sum(1 for *_, c in hits if c)} file(s)")
    else:
        print("dry run: nothing written (use --apply)")
    return 0 if a.apply or not hits else 1


if __name__ == "__main__":
    sys.exit(main())
