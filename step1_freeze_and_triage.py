#!/usr/bin/env python3
"""
step1_freeze_and_triage.py
==========================
Step 1 of the HypatiaX audit plan: FREEZE and TRIAGE.

Default mode is READ-ONLY (dry run). Nothing in your repo is edited, moved or
deleted unless you pass --apply, and even then results files are never moved or
changed: they are only LABELLED. Only stray junk files in the repo root are moved
into a quarantine folder (never deleted).

What it does
------------
 1. Snapshot   git SHA, branch, clean/dirty state, dirty file list, Python version.
 2. Checksum   sha256 of every code/config/patch file -> freeze_checksums.sha256.
 3. Stray files  root-level junk (e.g. the 4.7 MB ImageMagick PostScript called `os`,
               *.bak, *~) -> listed; with --apply moved to _quarantine/.
 4. Results triage  every file under the results directory is labelled:
        candidate_clean  provenance proves a live run with both flags = 1
                         (still needs re-verification; NOT "trusted" yet)
        exploratory      no provenance / pre-fix / partial / fallback / non-clean
        superseded       _rescued_ fragments, _saved copies, byte-identical duplicates
        corrupt          does not parse
    Anything without positive proof of a clean run defaults to `exploratory`.
 5. Conflict markers  distinguishes REAL merge conflicts from false positives.
 6. Patches    checks every *.patch: target files exist, `patch --dry-run` result,
               and flags path typos (e.g. rsc/ instead of hypatiax/).
 7. Scan errors  summarises the latest scan_after*.txt into a to-fix list.
 8. Outputs    triage_out/freeze_manifest.json, results_status.csv, triage_report.md
               (+ with --apply: RESULTS_STATUS_NOTICE.md in the results dir).

Usage (from the repo root)
--------------------------
  python step1_freeze_and_triage.py                      # dry run, report only
  python step1_freeze_and_triage.py --apply             # quarantine junk + write notice
  python step1_freeze_and_triage.py --fixes-after 2026-10-23T07:55:00
  python step1_freeze_and_triage.py --fixes-after ""    # disable the pre-fix rule

Exit code: 0 = no blocking issues, 1 = blocking issues found (use --no-fail to force 0).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

CODE_SUFFIXES = {".py", ".sh", ".yaml", ".yml", ".toml", ".cfg", ".patch", ".sql", ".txt", ".md"}
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", "triage_out", "_quarantine",
             "hypatiax.egg-info"}
RESULT_SUFFIXES = {".json", ".csv", ".log", ".txt"}
PROV_KEYS = {"llm_called", "bypass_kind", "prompt_sha256", "bypass_flags"}
FLAG_NAMES = ("HYPATIAX_DISABLE_HARDCODED", "HYPATIAX_DISABLE_PROMPT_HINTS")
# Default: the earliest code-fix patch in the zip is stamped 2026-10-23 07:55.
DEFAULT_FIXES_AFTER = "2026-10-23T07:55:00"


# ───────────────────────────── helpers ─────────────────────────────
def sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def run(cmd, cwd=None, timeout=60):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return 127, "", str(e)


def walk(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            yield Path(dirpath) / fn


def rel(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


# ───────────────────────────── 1. snapshot ─────────────────────────────
def git_snapshot(root: Path) -> dict:
    snap = {"timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "python": sys.version.split()[0], "root": str(root.resolve())}
    rc, out, _ = run(["git", "rev-parse", "HEAD"], cwd=root)
    if rc != 0:
        inside = run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root)[0] == 0
        snap.update(git=("git repo with no commits yet" if inside
                         else "not a git repository (or git missing)"),
                    sha=None, dirty=None, dirty_files=[])
        return snap
    snap["sha"] = out
    snap["branch"] = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root)[1]
    _, status, _ = run(["git", "status", "--porcelain"], cwd=root)
    dirty = [ln for ln in status.splitlines() if ln.strip()]
    snap["dirty"] = bool(dirty)
    snap["dirty_files"] = dirty[:200]
    snap["dirty_file_count"] = len(dirty)
    return snap


# ───────────────────────────── 2. checksums ─────────────────────────────
def freeze_checksums(root: Path) -> dict:
    sums = {}
    for p in walk(root):
        if p.suffix.lower() in CODE_SUFFIXES and "data/results" not in rel(p, root).replace("\\", "/"):
            try:
                sums[rel(p, root)] = sha256(p)
            except OSError:
                pass
    return dict(sorted(sums.items()))


# ───────────────────────────── 3. stray files ─────────────────────────────
def find_stray_root_files(root: Path) -> list[dict]:
    """Root-level files that look like accidents: ImageMagick/PostScript dumps, backups,
    large extensionless blobs."""
    stray = []
    for p in sorted(root.iterdir()):
        if not p.is_file():
            continue
        reason = None
        size = p.stat().st_size
        if p.name.endswith(("~", ".bak", ".orig", ".rej", ".swp")):
            reason = "editor/backup artefact"
        else:
            try:
                with open(p, "rb") as f:
                    head = f.read(200)
            except OSError:
                head = b""
            if head.startswith(b"%!PS-Adobe") or b"ImageMagick" in head:
                reason = "PostScript / ImageMagick output (accidental screenshot via `import`)"
            elif p.suffix == "" and size > 1_000_000 and not head.startswith(b"#!"):
                reason = "large extensionless non-script blob"
        if reason:
            stray.append({"path": p.name, "size": size, "reason": reason})
    return stray


# ───────────────────────────── 4. results triage ─────────────────────────────
TS_RE = re.compile(r"(20\d{2})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})")


def filename_timestamp(name: str):
    m = TS_RE.search(name)
    if not m:
        return None
    try:
        return dt.datetime(*map(int, m.groups()))
    except ValueError:
        return None


def collect_provenance(obj, found: dict, depth=0):
    """Walk parsed JSON gathering provenance evidence."""
    if depth > 40:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in PROV_KEYS:
                found["keys"].add(k)
                if k == "bypass_kind":
                    found["bypass_kinds"].add(str(v))
                elif k == "llm_called":
                    found["llm_called"].add(str(v))
                elif k == "bypass_flags" and isinstance(v, dict):
                    for fn in FLAG_NAMES:
                        if fn in v:
                            found["flags"].setdefault(fn, set()).add(str(v[fn]))
            collect_provenance(v, found, depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            collect_provenance(v, found, depth + 1)


def classify_result(p: Path, root: Path, fixes_after, dup_of: dict) -> dict:
    r = rel(p, root).replace("\\", "/")
    name = p.name
    status, reasons = "exploratory", []
    superseded = False

    # structural / naming rules
    if "_rescued_" in name:
        superseded = True
        reasons.append("rescued fragment (recovered from a log; not an original run output)")
    if "/_saved/" in "/" + r:
        superseded = True
        reasons.append("copy in _saved/ (duplicate of a run output)")
    if name.startswith("_") and ("_partial" in name or "_checkpoint" in name):
        reasons.append("partial/checkpoint file (incomplete run)")
    elif "_checkpoint" in name or "_partial" in name:
        reasons.append("checkpoint/partial file")
    low = r.lower()
    if "fallback" in low or "seed_off" in low or "seeds_fallback" in low:
        reasons.append("folder name signals a non-clean / fallback configuration")
    if "sparse" in low:
        reasons.append("sparse-seed variant (not the primary protocol)")
    if p.suffix == ".log":
        reasons.append("log file (evidence only, not a result table)")

    ts = filename_timestamp(name)
    if fixes_after and ts and ts < fixes_after:
        reasons.append(f"produced {ts:%Y-%m-%d %H:%M} before the code fixes ({fixes_after:%Y-%m-%d %H:%M})")
    elif fixes_after and not ts:
        try:
            m = dt.datetime.fromtimestamp(p.stat().st_mtime)
            if m < fixes_after:
                reasons.append("file mtime is before the code fixes (filename carries no timestamp)")
        except OSError:
            pass

    key = dup_of.get(r)
    if key and key != r:
        superseded = True
        reasons.append(f"byte-identical to {key}")

    # content rules (JSON only)
    corrupt = False
    nonstd = False
    prov = None
    if p.suffix == ".json":
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
            if re.search(r"(?<![\w\"])(NaN|-?Infinity)(?![\w\"])", text):
                nonstd = True
            data = json.loads(text)  # python accepts NaN/Infinity
            found = {"keys": set(), "bypass_kinds": set(), "llm_called": set(), "flags": {}}
            collect_provenance(data, found)
            prov = found
        except (json.JSONDecodeError, OSError) as e:
            corrupt = True
            reasons.append(f"does not parse as JSON ({type(e).__name__})")
        if nonstd:
            reasons.append("contains NaN/Infinity tokens (non-standard JSON)")

        if prov is not None:
            if not prov["keys"]:
                reasons.append("no provenance fields (llm_called / bypass_kind / prompt_sha256 / "
                               "bypass_flags): cannot prove a clean live run")
            else:
                bad_kinds = prov["bypass_kinds"] - {"None", "live"}
                if bad_kinds:
                    reasons.append(f"bypass_kind present: {sorted(bad_kinds)}")
                if "False" in prov["llm_called"]:
                    reasons.append("some rows record llm_called=False (LLM did not run)")
                for fn in FLAG_NAMES:
                    vals = prov["flags"].get(fn)
                    if vals is None:
                        reasons.append(f"{fn} not recorded in provenance")
                    elif vals != {"1"}:
                        reasons.append(f"{fn} recorded as {sorted(vals)} (must be 1)")

    if corrupt:
        status = "corrupt"
    elif superseded:
        status = "superseded"
    elif p.suffix == ".json" and prov is not None and prov["keys"] and not reasons:
        status = "candidate_clean"
        reasons.append("provenance present with both flags = 1 and live LLM; still needs re-verification")
    else:
        status = "exploratory"
        if not reasons:
            reasons.append("no positive evidence of a clean run")
    return {"path": r, "size": p.stat().st_size, "status": status, "reasons": "; ".join(reasons)}


def triage_results(results_dir: Path, root: Path, fixes_after) -> list[dict]:
    files = [p for p in walk(results_dir) if p.suffix.lower() in RESULT_SUFFIXES]
    # duplicate detection by (size, sha256); the shortest/earliest path is the "original"
    by_hash = defaultdict(list)
    for p in files:
        try:
            by_hash[(p.stat().st_size, sha256(p))].append(rel(p, root).replace("\\", "/"))
        except OSError:
            pass
    dup_of = {}
    for paths in by_hash.values():
        if len(paths) > 1:
            canon = sorted(paths, key=lambda s: ("_saved" in s, len(s), s))[0]
            for s in paths:
                dup_of[s] = canon
    return [classify_result(p, root, fixes_after, dup_of) for p in sorted(files)]


# ───────────────────────────── 5. conflict markers ─────────────────────────────
def check_conflict_markers(root: Path) -> list[dict]:
    import ast
    findings = []
    for p in walk(root):
        if p.suffix not in {".py", ".sh", ".yaml", ".yml", ".toml", ".md", ".txt", ".patch"}:
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        starts = [i for i, l in enumerate(lines, 1) if l.startswith("<<<<<<< ")]
        mids = [i for i, l in enumerate(lines, 1) if l.rstrip() == "======="]
        ends = [i for i, l in enumerate(lines, 1) if l.startswith(">>>>>>> ")]
        if not (starts or ends):
            # a lone "=======" is usually an RST/markdown underline; ignore
            continue
        real = bool(starts and mids and ends)
        parses = None
        if p.suffix == ".py":
            try:
                ast.parse("\n".join(lines))
                parses = True
            except SyntaxError:
                parses = False
        if real and parses is not True:
            verdict = "REAL conflict (all three markers present" + \
                      (", file does not parse)" if parses is False else ")")
        elif real:
            verdict = "markers present but file parses: probably inside a string/docstring; verify"
        else:
            verdict = "partial markers only: probably text, not a real merge conflict"
        findings.append({"path": rel(p, root), "lines": starts + mids + ends,
                         "verdict": verdict, "blocking": real and parses is not True})
    return findings


# ───────────────────────────── 6. patches ─────────────────────────────
def check_patches(root: Path) -> list[dict]:
    out = []
    have_patch = shutil.which("patch") is not None
    for pf in sorted(root.glob("*.patch")):
        text = pf.read_text(encoding="utf-8", errors="replace")
        targets = []
        for ln in text.splitlines():
            if ln.startswith("+++ b/"):
                targets.append(ln[6:].split("\t")[0].strip())
        info = {"patch": pf.name, "targets": targets, "issues": []}
        for t in targets:
            if not t.startswith("hypatiax/") and not t.startswith("scan_repo") and "/" in t:
                info["issues"].append(f"suspicious target prefix: {t} (typo for hypatiax/ ?)")
            if not (root / t).exists():
                info["issues"].append(f"target file missing in this tree: {t}")
        if have_patch and targets and all((root / t).exists() for t in targets):
            rc, so, se = run(["patch", "-p1", "--dry-run", "-s", "-i", str(pf.resolve())], cwd=root)
            if rc == 0:
                info["dry_run"] = "applies cleanly"
            else:
                tail = (so or se).splitlines()[-1:] or ["failed"]
                # reversed-applies check: a patch that applies in reverse is already applied
                rc2, _, _ = run(["patch", "-p1", "-R", "--dry-run", "-s", "-i", str(pf.resolve())], cwd=root)
                info["dry_run"] = ("ALREADY APPLIED (reverse applies cleanly)" if rc2 == 0
                                   else f"does not apply: {tail[0][:120]}")
        else:
            info["dry_run"] = "not testable (target files absent or `patch` unavailable)"
        out.append(info)
    return out


# ───────────────────────────── 7. scan errors ─────────────────────────────
ACTIONS = {
    "evaluator": "replace absolute ss_tot guard with core.r2_canonical.r2_checked (Rule A)",
    "undefined-name": "add the missing import/definition (e.g. `import subprocess`, define _kill_thread)",
    "import": "create/restore the missing module or remove the dead import",
    "config-path": "fix the script path in config/repro.yaml or restore the script",
    "merge-conflict": "open the file; if markers are real resolve them, if inside a string ignore",
    "parse": "recover the original JSON from the shard/log or mark file corrupt (do not cite)",
    "clean-run": "set HYPATIAX_DISABLE_HARDCODED=1 or document that outputs never feed headline tables",
}


def summarize_scan(root: Path, scan_file: str | None) -> dict:
    cands = [Path(scan_file)] if scan_file else sorted(root.glob("scan_after*.txt"))
    if not cands or not cands[-1].exists():
        return {"file": None, "errors": []}
    f = cands[-1]
    errs = []
    for ln in f.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"ERROR\s+\[([\w-]+)\]\s+(.*)", ln)
        if m:
            errs.append({"rule": m.group(1), "detail": m.group(2)[:220],
                         "suggested_action": ACTIONS.get(m.group(1), "investigate")})
    return {"file": f.name, "errors": errs}


# ───────────────────────────── report ─────────────────────────────
def write_outputs(out_dir: Path, manifest: dict, results: list[dict]):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "freeze_manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    with open(out_dir / "results_status.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path", "size", "status", "reasons"])
        w.writeheader()
        w.writerows(results)
    with open(out_dir / "freeze_checksums.sha256", "w") as f:
        for k, v in manifest["checksums"].items():
            f.write(f"{v}  {k}\n")

    g = manifest["git"]
    counts = defaultdict(int)
    for r in results:
        counts[r["status"]] += 1
    L = ["# Step 1: Freeze & triage report", "",
         f"Generated: {g['timestamp_utc']}  |  root: `{g['root']}`", "",
         "## 1. Snapshot",
         f"- Git SHA: `{g.get('sha')}`  branch: `{g.get('branch')}`",
         f"- Working tree dirty: **{g.get('dirty')}** ({g.get('dirty_file_count', 0)} changed files)",
         f"- Code/config files checksummed: {len(manifest['checksums'])}", ""]
    L += ["## 2. Stray files", ""]
    L += [f"- `{s['path']}` ({s['size']:,} bytes): {s['reason']}" for s in manifest["stray_files"]] \
         or ["- none"]
    L += ["", "## 3. Results triage", "",
          "| status | files |", "|---|---|"]
    L += [f"| {k} | {counts[k]} |" for k in ("candidate_clean", "exploratory", "superseded", "corrupt")]
    L += ["", "Default is `exploratory`; `candidate_clean` requires provenance showing a live run "
          "with both flags = 1. Per-file reasons are in `results_status.csv`.", ""]
    corrupt = [r for r in results if r["status"] == "corrupt"]
    if corrupt:
        L += ["### Corrupt files (do not cite)"] + [f"- `{r['path']}`" for r in corrupt] + [""]
    L += ["## 4. Conflict markers", ""]
    L += [f"- `{c['path']}` lines {c['lines']}: {c['verdict']}" for c in manifest["conflict_markers"]] \
         or ["- none"]
    L += ["", "## 5. Patches", ""]
    for p in manifest["patches"]:
        L.append(f"- `{p['patch']}`: {p['dry_run']}")
        L += [f"    - {i}" for i in p["issues"]]
    L += ["", f"## 6. Remaining scan errors ({manifest['scan']['file']})", ""]
    L += [f"- **[{e['rule']}]** {e['detail']}\n    - action: {e['suggested_action']}"
          for e in manifest["scan"]["errors"]] or ["- none / no scan file found"]
    L += ["", "## 7. Blocking issues", ""]
    L += [f"- {b}" for b in manifest["blocking"]] or ["- none"]
    (out_dir / "triage_report.md").write_text("\n".join(L) + "\n")


NOTICE = """# RESULTS STATUS NOTICE

Generated by step1_freeze_and_triage.py on {ts} (git SHA {sha}).

All files in this directory are PRESERVED UNCHANGED. They are labelled in
`triage_out/results_status.csv`:

- `candidate_clean`: provenance shows a live run with both flags = 1; pending re-verification.
- `exploratory`: no provenance, pre-fix, partial, fallback or otherwise unproven.
  Do not use for headline claims.
- `superseded`: rescued fragments, _saved copies or byte-identical duplicates.
- `corrupt`: does not parse; do not cite.

Only controlled, auditable reruns (both HYPATIAX_DISABLE_* flags = 1, provenance recorded)
may feed the abstract, tables and figures.
"""


# ───────────────────────────── main ─────────────────────────────
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="repo root (default: cwd)")
    ap.add_argument("--results-dir", default="hypatiax/data/results")
    ap.add_argument("--out", default="triage_out")
    ap.add_argument("--scan-file", default=None, help="scan report to summarise (default: latest scan_after*.txt)")
    ap.add_argument("--fixes-after", default=DEFAULT_FIXES_AFTER,
                    help="ISO time of the first code fix; results older than this are marked "
                         "pre-fix. Pass '' to disable.")
    ap.add_argument("--apply", action="store_true", help="quarantine stray files + write notice")
    ap.add_argument("--no-fail", action="store_true", help="always exit 0")
    a = ap.parse_args()

    root = Path(a.root).resolve()
    results_dir = (root / a.results_dir)
    fixes_after = dt.datetime.fromisoformat(a.fixes_after) if a.fixes_after else None

    print(f"[1/7] git snapshot … {root}")
    git = git_snapshot(root)
    print("[2/7] checksums …")
    sums = freeze_checksums(root)
    print("[3/7] stray files …")
    stray = find_stray_root_files(root)
    print("[4/7] results triage …")
    results = triage_results(results_dir, root, fixes_after) if results_dir.exists() else []
    if not results_dir.exists():
        print(f"      (results dir not found: {results_dir})")
    print("[5/7] conflict markers …")
    conflicts = check_conflict_markers(root)
    print("[6/7] patches …")
    patches = check_patches(root)
    print("[7/7] scan summary …")
    scan = summarize_scan(root, a.scan_file)

    blocking = []
    if git.get("sha") is None:
        blocking.append("not a git repository: cannot record a SHA (run `git init && git add -A && git commit`)")
    elif git.get("dirty"):
        blocking.append(f"git working tree is dirty ({git['dirty_file_count']} files): commit or stash "
                        "before any confirmatory run")
    blocking += [f"real merge conflict in {c['path']}" for c in conflicts if c["blocking"]]
    n_corrupt = sum(r["status"] == "corrupt" for r in results)
    if n_corrupt:
        blocking.append(f"{n_corrupt} corrupt result file(s): exclude from every table")
    for p in patches:
        if p["dry_run"].startswith("does not apply"):
            blocking.append(f"{p['patch']} does not apply cleanly")
        if any("typo" in i for i in p["issues"]):
            blocking.append(f"{p['patch']} has a suspicious target path")
    if scan["errors"]:
        blocking.append(f"{len(scan['errors'])} unresolved scan error(s) in {scan['file']}")

    manifest = {"git": git, "checksums": sums, "stray_files": stray, "conflict_markers": conflicts,
                "patches": patches, "scan": scan, "blocking": blocking,
                "fixes_after": a.fixes_after or None,
                "results_summary": {s: sum(r["status"] == s for r in results)
                                    for s in ("candidate_clean", "exploratory", "superseded", "corrupt")}}
    out_dir = root / a.out
    write_outputs(out_dir, manifest, results)

    if a.apply:
        q = root / "_quarantine"
        for s in stray:
            q.mkdir(exist_ok=True)
            shutil.move(str(root / s["path"]), str(q / s["path"]))
            print(f"      quarantined {s['path']} -> _quarantine/")
        if results_dir.exists():
            (results_dir / "RESULTS_STATUS_NOTICE.md").write_text(
                NOTICE.format(ts=git["timestamp_utc"], sha=git.get("sha")))
            print(f"      wrote {rel(results_dir / 'RESULTS_STATUS_NOTICE.md', root)}")
    elif stray:
        print(f"      (dry run) would quarantine {len(stray)} stray file(s); use --apply")

    print(f"\nReport: {out_dir / 'triage_report.md'}")
    print("Results:", manifest["results_summary"])
    if blocking:
        print("\nBLOCKING ISSUES:")
        for b in blocking:
            print("  -", b)
    sys.exit(0 if (a.no_fail or not blocking) else 1)


if __name__ == "__main__":
    main()
