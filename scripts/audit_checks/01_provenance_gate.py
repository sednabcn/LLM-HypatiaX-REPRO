#!/usr/bin/env python3
"""L03 gate: every LLM-involving result row must record a live generation path.

FAIL when:
  * llm_source in BAD (local_fallback, hardcoded, frozen_cache_unknown_origin)
  * a row has llm_called != False and llm_source is None / missing (unaudited)
  * a file carries no provenance keys at all (unaudited file: predates B2)
  * r2_sign_flip_enabled is present and not "0" (sign flip active)
WARN when r2_sign_flip_enabled is absent from a file.

Usage: python3 01_provenance_gate.py 'GLOB' [...]     exit 0 clean, 1 fail, 2 no input
"""
import collections, glob, json, sys

BAD = {"local_fallback", "hardcoded", "frozen_cache_unknown_origin"}
KEYS = ("llm_called", "llm_source", "bypass_kind")


def walk(o, rows, flags):
    if isinstance(o, dict):
        if any(k in o for k in KEYS):
            rows.append(o)
        if "r2_sign_flip_enabled" in o:
            flags.add(str(o["r2_sign_flip_enabled"]))
        for v in o.values():
            walk(v, rows, flags)
    elif isinstance(o, list):
        for v in o:
            walk(v, rows, flags)


def main():
    files = sorted({f for p in sys.argv[1:] for f in glob.glob(p, recursive=True)})
    if not files:
        print("no input files")
        return 2
    tot = collections.Counter()
    for f in files:
        try:
            data = ([json.loads(l) for l in open(f) if l.strip()] if f.endswith('.jsonl')
                    else json.load(open(f)))
        except Exception as e:
            print(f"FAIL {f}: unreadable ({e})")
            tot["unreadable"] += 1
            continue
        rows, flags = [], set()
        walk(data, rows, flags)
        if not rows:
            tot["file_no_provenance"] += 1
            continue
        c = collections.Counter()
        for r in rows:
            src = r.get("llm_source")
            if src in BAD:
                c["bad_source"] += 1
            if r.get("llm_called") is not False and src is None:
                c["llm_row_unknown_source"] += 1
        if flags - {"0"}:
            c["sign_flip_active"] += 1
        if not flags:
            c["no_signflip_field"] += 1
        if c:
            print(f"{f}: rows={len(rows)} {dict(c)}")
        tot.update(c)
        tot["files_with_provenance"] += 1
    print("\nSUMMARY", dict(tot))
    fail = sum(tot[k] for k in ("bad_source", "llm_row_unknown_source", "file_no_provenance",
                                "sign_flip_active", "unreadable"))
    print("RESULT:", "FAILED" if fail else "ok", fail)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
