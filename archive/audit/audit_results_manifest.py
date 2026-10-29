#!/usr/bin/env python3
"""Classify every stored result JSON by provenance.

Usage (from the old repo root):
    python audit_results_manifest.py hypatiax/data/results -o audit_out/results_manifest.csv

Schema-agnostic: walks each JSON recursively and counts the provenance keys
wherever they appear. Labels:

  CONTAMINATED        any is_hardcoded=true / bypass_kind != none /
                      method == "pure_llm_hardcoded"
  PROVENANCE_PRESENT  bypass_kind present and always "none" (still needs the
                      evaluator and train/test-split audit before use)
  NO_PROVENANCE       no provenance fields at all -> cannot be verified from
                      the file; treat as historical/exploratory

The dup_or_partial column flags checkpoint / _saved / rescued / _partial files.
Grep-style counts miss compact JSON ("key":true); this does not.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

DUP_HINTS = ("_saved", "rescued", "_partial", "checkpoint")
COLUMNS = [
    "path", "label", "dup_or_partial", "size_bytes", "sha256",
    "is_hardcoded_true", "is_hardcoded_false", "bypass_none", "bypass_other",
    "llm_called_true", "llm_called_false", "method_pure_llm_hardcoded", "error",
]


def walk(obj, c):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "is_hardcoded":
                if v is True:
                    c["is_hardcoded_true"] += 1
                elif v is False:
                    c["is_hardcoded_false"] += 1
            elif k == "bypass_kind":
                c["bypass_none" if v in (None, "none") else "bypass_other"] += 1
            elif k == "llm_called":
                if v is True:
                    c["llm_called_true"] += 1
                elif v is False:
                    c["llm_called_false"] += 1
            elif k == "method" and v == "pure_llm_hardcoded":
                c["method_pure_llm_hardcoded"] += 1
            walk(v, c)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, c)


def label(c):
    if c["is_hardcoded_true"] or c["bypass_other"] or c["method_pure_llm_hardcoded"]:
        return "CONTAMINATED"
    if c["bypass_none"]:
        return "PROVENANCE_PRESENT"
    return "NO_PROVENANCE"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("-o", "--out", default="results_manifest.csv")
    args = ap.parse_args()

    root = Path(args.root)
    rows, summary = [], Counter()
    for path in sorted(root.rglob("*.json")):
        c, err = Counter(), ""
        try:
            walk(json.loads(path.read_text(errors="ignore")), c)
            lab = label(c)
        except Exception as e:  # unreadable / invalid JSON
            lab, err = "UNREADABLE", f"{type(e).__name__}: {e}"[:120]
        dup = any(h in str(path) for h in DUP_HINTS)
        rows.append({
            "path": str(path), "label": lab, "dup_or_partial": dup,
            "size_bytes": path.stat().st_size, "sha256": sha256(path),
            **{k: c[k] for k in COLUMNS[5:12]}, "error": err,
        })
        summary[lab] += 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    print(f"{len(rows)} files -> {out}")
    for k, v in summary.most_common():
        print(f"  {k:20s} {v}")
    print(f"  dup_or_partial       {sum(r['dup_or_partial'] for r in rows)}")


if __name__ == "__main__":
    main()
