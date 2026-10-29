#!/usr/bin/env python3
"""Write AUDIT/quarantine_manifest.json: which stored results are quarantined (exploratory,
not for the paper) or proposed for quarantine, with file hashes and the git commit that
moved or last touched them.  It only states facts it can read from the repo; items under
"proposed" stay proposals until the files are moved or you edit the JSON.
"""
from __future__ import annotations
import argparse, csv, fnmatch, hashlib, json, pathlib, subprocess, sys, time

DIR_PATTERNS = ("*_pre_fix*", "*pre_prompt_fix*", "*quarantine*", "*exploratory*")
SKIP = {".git", ".venv", "venv", "node_modules", "__pycache__", "site-packages"}


def sh(root, *cmd):
    r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def commit_of(root, rel):
    out = sh(root, "git", "log", "-1", "--format=%h|%ad|%s", "--date=short", "--", rel)
    if not out:
        return None
    h, d, s = (out.split("|", 2) + ["", ""])[:3]
    return {"commit": h, "date": d, "subject": s}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="AUDIT/quarantine_manifest.json")
    a = ap.parse_args()
    root = pathlib.Path(a.root).resolve()

    quarantined, tops = [], []
    for d in sorted(root.rglob("*")):
        if (d.is_dir() and not (SKIP & set(d.parts))
                and not any(t in d.parents for t in tops)        # nested in a folder already listed
                and any(fnmatch.fnmatch(d.name.lower(), pat) for pat in DIR_PATTERNS)):
            tops.append(d)
            files = [f for f in sorted(d.rglob("*")) if f.is_file()]
            rel = d.relative_to(root).as_posix()
            quarantined.append({
                "path": rel, "n_files": len(files), "git": commit_of(root, rel),
                "n_tracked_by_git": len(sh(root, "git", "ls-files", "--", rel).splitlines()),
                "reason": "see git.subject (the quarantine commit message); edit if more detail is needed",
                "files": [{"path": f.relative_to(root).as_posix(), "bytes": f.stat().st_size,
                           "sha256": sha(f)} for f in files],
            })

    proposed, evidence = [], []
    bp = root / "bypass_audit.csv"
    if bp.is_file():
        with open(bp, newline="") as fh:
            rows = list(csv.DictReader(fh))
        yes = lambda v: str(v).strip().lower() == "true"
        bypassed = [r for r in rows if yes(r.get("bypassed_when_switch_off"))]
        evidence.append({
            "path": "bypass_audit.csv", "sha256": sha(bp), "git": commit_of(root, "bypass_audit.csv"),
            "what": "per-task audit of the hardcoded-formula bypass (these are tasks, not result rows)",
            "n_tasks": len(rows),
            "n_bypassed_when_switch_off": len(bypassed),
            "n_not_restored_by_switch_on": sum(1 for r in rows if not yes(r.get("switch_on_returns_None"))),
            "bypassed_tasks": [f"{r.get('suite')}:{r.get('id_or_domain')}" for r in bypassed],
        })
    for f in sorted(root.glob("hypatiax/data/results/**/*all_domains*.json")):
        if not (SKIP & set(f.parts)) and not any(fnmatch.fnmatch(p.lower(), pat)
                                                  for p in f.parts for pat in DIR_PATTERNS):
            proposed.append({"path": f.relative_to(root).as_posix(), "sha256": sha(f),
                             "git": commit_of(root, f.relative_to(root).as_posix()),
                             "reason": "stored all-domains hybrid output (M4): predates per-row "
                                       "provenance, the clean-run flags and the canonical R^2 policy"})
    fab = []
    for f in root.rglob("*"):
        if (f.suffix in {".json", ".csv", ".jsonl"} and f.is_file() and not (SKIP & set(f.parts))
                and f.stat().st_size < 64_000_000):
            try:
                if "algebraic_reconstruction" in f.read_text(errors="ignore"):
                    fab.append(f.relative_to(root).as_posix())
            except OSError:
                pass
    if fab:
        proposed.append({"paths": fab, "reason": "rows with y_pred fabricated from a reported R^2 "
                                                 "(removed algebraic_reconstruction path)"})

    out = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "head": sh(root, "git", "rev-parse", "--short", "HEAD"),
           "policy": "quarantined = exploratory only; not to be cited as paper results",
           "quarantined": quarantined, "proposed": proposed, "evidence": evidence}
    dest = root / a.out
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {a.out}: {len(quarantined)} quarantined dir(s), "
          f"{sum(q['n_files'] for q in quarantined)} file(s); {len(proposed)} proposed item(s)")
    for q in quarantined:
        print(f"  quarantined  {q['path']}  ({q['n_files']} files)  {q['git']['subject'] if q['git'] else ''}")
    for p in proposed:
        print(f"  proposed     {p.get('path') or p.get('paths')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
