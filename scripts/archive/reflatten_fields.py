#!/usr/bin/env python3
"""reflatten_fields.py - re-flatten Phase 2 rows onto another R^2 field.

Why this exists
---------------
scripts/phase2_close.py reads one flat ``r2`` per row and has no ``--r2-field``
option.  The p2/*.jsonl rows were flattened from exp1_ablation_results.json,
which stores several scores per block (train_r2, extrap_r2_near/medium/far).
To run a sensitivity check you re-flatten onto a different field and run the
unchanged closure script on the copy.

What it guarantees
------------------
1. VERIFY FIRST.  Before anything is written, every input row's ``r2`` must
   equal the *primary field* (default ``extrap_r2_far``) of the source block it
   came from.  If any row differs the script stops with exit code 2 and writes
   nothing.  That makes "r2 is the far-extrapolation score" a checked fact for
   every row, not an assumption.
2. LOOKUP BY KEY.  ``_source`` looks like ``<path>.json::<key>/<block>``.  The
   JSON file is a dict keyed by the *strings* '0'..'14' in non-numeric order
   (0, 1, 2, 12, 13, 14, 3, ...).  <key> is that dict key.  It is NOT a list
   position, so ``list(d.values())[key]`` is wrong; this script uses ``d[key]``.
3. TRACEABLE OUTPUT.  Each output row keeps every original field, replaces
   ``r2`` with the chosen field, and adds ``r2_field`` (the field used) and
   ``r2_primary`` (the original r2).  Each output directory gets a
   ``reflatten_manifest.json`` with source-file SHA-256 hashes.

Rows that already carry the metric fields themselves (``extrap_r2_far`` etc. as
top-level keys, as the Pure LLM runner spec requires) are handled without any
``_source`` lookup.

Examples
--------
  # verify only (no files written)
  python scripts/reflatten_fields.py --check-only

  # the two sensitivity sets used in the Phase 2 report
  python scripts/reflatten_fields.py

  # explicit
  python scripts/reflatten_fields.py --in-dir p2 --repo-root . \
      --primary-field extrap_r2_far \
      --sens p2_med=extrap_r2_medium --sens p2_train=train_r2

Exit codes: 0 ok | 1 usage / IO error | 2 primary-field mismatch | 3 source lookup failed
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import math
import os
import sys
from collections import Counter

VERSION = "1.0"
DEFAULT_PRIMARY = "extrap_r2_far"
DEFAULT_SENS = ["p2_med=extrap_r2_medium", "p2_train=train_r2"]
KNOWN_FIELDS = ["train_r2", "extrap_r2_near", "extrap_r2_medium", "extrap_r2_far"]


def same(a, b) -> bool:
    """Exact equality; NaN == NaN; None only equals None."""
    if a is None or b is None:
        return a is None and b is None
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return a == b
    if math.isnan(a) and math.isnan(b):
        return True
    return a == b  # +-inf compare equal to themselves; JSON round-trip is exact


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class SourceCache:
    def __init__(self, repo_root: str):
        self.root = repo_root
        self.data: dict[str, object] = {}
        self.paths: dict[str, str] = {}

    def load(self, rel: str):
        if rel not in self.data:
            full = rel if os.path.isabs(rel) else os.path.join(self.root, rel)
            with open(full, "r", encoding="utf-8") as fh:
                self.data[rel] = json.load(fh)  # accepts -Infinity / NaN
            self.paths[rel] = full
        return self.data[rel]

    def locate(self, source: str):
        """Return (record, block_name) for '<path>::<key>/<block>'."""
        path, rest = source.rsplit("::", 1)
        key, block = rest.split("/", 1)
        doc = self.load(path)
        if isinstance(doc, dict):
            rec = doc[key]
        else:  # tolerate a plain list keyed by position
            rec = doc[int(key)]
        return rec, block


def metrics_for(row: dict, cache: SourceCache, primary: str):
    """Return (metrics_dict, record_or_None, how)."""
    if primary in row:
        return row, None, "embedded"
    src = row.get("_source")
    if not src or "::" not in src or "/" not in src.rsplit("::", 1)[1]:
        raise LookupError(f"no usable _source on row {row.get('equation')!r} seed {row.get('seed')!r}: {src!r}")
    rec, block = cache.locate(src)
    blk = rec.get(block)
    if not isinstance(blk, dict):
        raise LookupError(f"block {block!r} missing in record for {src}")
    return blk, rec, "source"


def parse_sens(items: list[str]) -> list[tuple[str, str]]:
    out = []
    for it in items:
        if "=" not in it:
            raise SystemExit(f"--sens expects name=field, got {it!r}")
        name, field = it.split("=", 1)
        out.append((name.strip(), field.strip()))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in-dir", default="p2", help="directory with the *.jsonl rows (default: p2)")
    ap.add_argument("--glob", default="*.jsonl", help="file pattern inside --in-dir (default: *.jsonl)")
    ap.add_argument("--repo-root", default=".", help="base for relative _source paths (default: .)")
    ap.add_argument("--primary-field", default=DEFAULT_PRIMARY,
                    help=f"field that the rows' r2 must equal (default: {DEFAULT_PRIMARY})")
    ap.add_argument("--sens", action="append", default=None, metavar="OUTDIR=FIELD",
                    help="sensitivity set to write; repeatable. "
                         f"Default: {' '.join(DEFAULT_SENS)}")
    ap.add_argument("--check-only", action="store_true", help="verify the primary field and exit; write nothing")
    ap.add_argument("--force", action="store_true", help="overwrite a non-empty output directory")
    args = ap.parse_args(argv)

    sens = parse_sens(args.sens if args.sens else DEFAULT_SENS)
    files = sorted(glob.glob(os.path.join(args.in_dir, args.glob)))
    if not files:
        print(f"no input files match {os.path.join(args.in_dir, args.glob)}", file=sys.stderr)
        return 1

    cache = SourceCache(args.repo_root)
    loaded = []          # (basename, row, metrics, how)
    mismatches, lookup_errors, name_warn = [], [], 0
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            for ln, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                row = json.loads(line)
                try:
                    m, rec, how = metrics_for(row, cache, args.primary_field)
                except (LookupError, KeyError, ValueError, OSError, IndexError) as e:
                    lookup_errors.append((os.path.basename(f), ln, f"{type(e).__name__}: {e}"))
                    continue
                if rec is not None:  # advisory: equation name should appear among the record's strings
                    if row.get("equation") not in [v for v in rec.values() if isinstance(v, str)]:
                        name_warn += 1
                if not same(row.get("r2"), m.get(args.primary_field)):
                    mismatches.append((row.get("system"), row.get("equation"), row.get("seed"),
                                       row.get("r2"), m.get(args.primary_field)))
                    continue
                loaded.append((os.path.basename(f), row, m, how))

    n_total = len(loaded) + len(mismatches) + len(lookup_errors)
    print(f"rows {n_total}  verified {len(loaded)}  mismatch {len(mismatches)}  "
          f"lookup_errors {len(lookup_errors)}  name_warnings {name_warn}")
    print("how:", dict(Counter(h for *_, h in loaded)))

    if lookup_errors:
        for e in lookup_errors[:10]:
            print("LOOKUP ERROR:", e, file=sys.stderr)
        print("stop: some rows could not be traced to a source record", file=sys.stderr)
        return 3
    if mismatches:
        print(f"first mismatches (system, equation, seed, row r2, source {args.primary_field}):", file=sys.stderr)
        for m in mismatches[:10]:
            print("  ", m, file=sys.stderr)
        print(f"stop: r2 is NOT {args.primary_field} for {len(mismatches)} rows; nothing written", file=sys.stderr)
        return 2

    print(f"OK: r2 equals {args.primary_field} for all {len(loaded)} rows")
    if args.check_only:
        return 0

    created = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    src_hashes = {rel: sha256_file(full) for rel, full in cache.paths.items()}
    for outdir, field in sens:
        if os.path.isdir(outdir) and os.listdir(outdir) and not args.force:
            print(f"refusing to write into non-empty {outdir!r} (use --force)", file=sys.stderr)
            return 1
        os.makedirs(outdir, exist_ok=True)
        per_file: dict[str, list] = {}
        missing = 0
        for base, row, m, _how in loaded:
            val = m.get(field)
            if val is None:
                missing += 1
            y = dict(row)
            y["r2_primary"] = row.get("r2")
            y["r2"] = val
            y["r2_field"] = field
            per_file.setdefault(base, []).append(y)
        for base, ys in per_file.items():
            with open(os.path.join(outdir, base), "w", encoding="utf-8") as fh:
                for y in ys:
                    fh.write(json.dumps(y) + "\n")
        manifest = {
            "script": "reflatten_fields.py", "script_version": VERSION, "created_utc": created,
            "in_dir": args.in_dir, "primary_field": args.primary_field, "field": field,
            "rows": sum(len(v) for v in per_file.values()), "rows_with_missing_field": missing,
            "files": {k: len(v) for k, v in sorted(per_file.items())},
            "source_sha256": src_hashes,
        }
        with open(os.path.join(outdir, "reflatten_manifest.json"), "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)
        print(f"{outdir}: {field} written ({manifest['rows']} rows, {missing} missing)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
