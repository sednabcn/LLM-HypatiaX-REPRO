#!/usr/bin/env python3
"""Quarantine stored result files that carry hardcoded-bypass contamination.

    python scripts/quarantine_contaminated.py             # dry run: list what would move
    python scripts/quarantine_contaminated.py --apply     # git mv into exploratory/ + write the manifest

A file is CONTAMINATED when any row has is_hardcoded=true, bypass_kind != "none", or
method == "pure_llm_hardcoded" (same rule as audit_results_manifest.py). Files already under
an ``exploratory`` or ``*_pre_prompt_fix`` directory are skipped.

Moved to:  hypatiax/data/results/exploratory/bypass_contaminated/<original relative path>
Manifest:  AUDIT/contaminated_files.json  (old path, new path, sha256, hardcoded-row count)

Moving a file removes it from the paper's evidence base. Only run --apply once you have decided
to quarantine rather than regenerate those results.
"""
import argparse, collections, hashlib, json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from audit_results_manifest import walk, label  # noqa: E402

RES = ROOT / "hypatiax/data/results"
DEST = RES / "exploratory/bypass_contaminated"
SKIP = ("exploratory", "exp1_ablation_pre_prompt_fix")


def scan():
    out = []
    for p in sorted(RES.rglob("*.json")):
        rel = p.relative_to(RES)
        if any(part in SKIP for part in rel.parts):
            continue
        c = collections.Counter()
        try:
            walk(json.loads(p.read_text(encoding="utf-8")), c)
        except Exception:
            continue
        if label(c) == "CONTAMINATED":
            out.append((p, c["is_hardcoded_true"] + c["bypass_other"] + c["method_pure_llm_hardcoded"]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    hits = scan()
    by_dir = collections.Counter(str(p.parent.relative_to(RES)) for p, _ in hits)
    print(f"{len(hits)} contaminated file(s) outside quarantine")
    for d, n in sorted(by_dir.items()):
        print(f"  {n:3}  {d}")
    if not a.apply:
        print("dry run: nothing moved (use --apply)")
        return 1 if hits else 0
    entries = []
    for p, n in hits:
        dst = DEST / p.relative_to(RES)
        dst.parent.mkdir(parents=True, exist_ok=True)
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        subprocess.run(["git", "mv", str(p), str(dst)], cwd=ROOT, check=True)
        entries.append({"old": p.relative_to(ROOT).as_posix(), "new": dst.relative_to(ROOT).as_posix(),
                        "sha256": sha, "contaminated_rows": n})
    man = ROOT / "AUDIT/contaminated_files.json"
    man.parent.mkdir(exist_ok=True)
    man.write_text(json.dumps({"policy": "exploratory only; not to be cited as paper results",
                               "n_files": len(entries), "files": entries}, indent=2), encoding="utf-8")
    print(f"moved {len(entries)} file(s); wrote {man.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
