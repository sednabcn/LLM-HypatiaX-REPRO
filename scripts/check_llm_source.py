#!/usr/bin/env python3
"""Fail if any result row used a non-live generation path (confirmatory arms).
Usage: python3 scripts/check_llm_source.py 'DIR/**/*.json' [...]
Exit 0 clean, 1 bad rows found, 2 no input."""
import collections, glob, json, sys

BAD = {"local_fallback", "hardcoded", "frozen_cache_unknown_origin"}
FIELDS = ("llm_source", "bypass_kind")


def walk(o, hits, seen):
    if isinstance(o, dict):
        for k in FIELDS:
            v = o.get(k)
            if isinstance(v, str):
                seen[(k, v)] += 1
                if v in BAD:
                    hits.append((k, v, o.get("equation") or o.get("name") or "?"))
        if "llm_source" in o and o["llm_source"] is None and o.get("llm_called") is not False:
            hits.append(("llm_source", "None(unknown)", o.get("equation") or o.get("name") or "?"))
        if o.get("llm_called") is False:
            seen[("llm_called", "False")] += 1
        for v in o.values():
            walk(v, hits, seen)
    elif isinstance(o, list):
        for v in o:
            walk(v, hits, seen)


def main():
    files = sorted({f for p in sys.argv[1:] for f in glob.glob(p, recursive=True)})
    if not files:
        print("no input files"); return 2
    bad = 0
    for f in files:
        hits, seen = [], collections.Counter()
        try:
            walk(json.load(open(f)), hits, seen)
        except Exception as e:
            print(f"{f}: unreadable ({e})"); bad += 1; continue
        if not any(k == "llm_source" for k, _ in seen):
            hits.append(("llm_source", "MISSING_FIELD(unaudited file)", f))
        print(f"{f}: {dict(seen)}")
        for k, v, eq in hits[:5]:
            print(f"   BAD {k}={v} equation={eq}")
        bad += len(hits)
    print("RESULT:", "FAILED" if bad else "ok", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
