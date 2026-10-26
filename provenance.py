#!/usr/bin/env python3
"""Provenance report for the exp1 ablation results.

Records, in one reproducible artifact:
  * git state of the repo (commit, branch, dirty flag, remote)
  * every results file used (path, size, sha256, mtime)
  * which seeds were found (unsuffixed dir == seed 42) and which dirs were skipped
  * per-seed counts of llm_mode_used
  * per-equation, per-seed comparison: PySR-only vs Hybrid vs Hybrid-no-LLM
    (extrapolation R2 far, final expression, LLM expression / R2, mode)
  * integrity flags (e.g. hybrid_llm_only but final != llm_expression,
    hybrid worse than PySR-only)

Usage (from anywhere):
    python3 provenance.py                       # markdown to stdout, JSON next to results
    python3 provenance.py --repo /path/to/repo
    python3 provenance.py --names "Ideal Gas Law" "Price Impact"
    python3 provenance.py --all                 # every equation, not just the default five
    python3 provenance.py --out provenance.json --md provenance.md
"""
import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

DEFAULT_RESULTS = "hypatiax/data/results/ablation/"
DEFAULT_NAMES = ["Ideal Gas Law", "Price Impact", "Portfolio Std Dev",
                 "Kinetic Energy", "Allometric Scaling"]
DEFAULT_SEED = 42  # unsuffixed exp1_ablation dir
DIR_RE = re.compile(r"exp1_ablation(?:_seed(\d+))?$")
RESULT_FILE = "exp1_ablation_results.json"
WORSE_TOL = 1e-3


def sh(cmd, cwd):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return None


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_info(repo):
    status = sh(["git", "status", "--porcelain"], repo)
    return {
        "commit": sh(["git", "rev-parse", "HEAD"], repo),
        "branch": sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo),
        "remote": sh(["git", "config", "--get", "remote.origin.url"], repo),
        "commit_date": sh(["git", "log", "-1", "--format=%cI"], repo),
        "dirty": bool(status) if status is not None else None,
        "dirty_files": status.splitlines() if status else [],
    }


def discover(results_dir):
    runs, files, skipped = {}, [], []
    for d in sorted(glob.glob(os.path.join(results_dir, "exp1_ablation*"))):
        base = os.path.basename(d.rstrip("/"))
        m = DIR_RE.search(base)
        f = os.path.join(d, RESULT_FILE)
        if not (m and os.path.isfile(f)):
            skipped.append(base)
            continue
        seed = int(m.group(1) or DEFAULT_SEED)
        with open(f) as fh:
            runs[seed] = json.load(fh)
        st = os.stat(f)
        files.append({
            "seed": seed, "path": os.path.relpath(f, results_dir),
            "bytes": st.st_size, "sha256": sha256(f),
            "mtime": dt.datetime.fromtimestamp(st.st_mtime, dt.timezone.utc).isoformat(),
        })
    return runs, files, skipped


def fnum(x, nd=4):
    return None if x is None else round(float(x), nd)


def find(run, name):
    for v in run.values():
        if v.get("name") == name:
            return v
    return None


def build(runs, names):
    mode_counts, equations, flags = {}, {}, []
    for s, r in sorted(runs.items()):
        c = {}
        for v in r.values():
            m = v["hypatia"].get("llm_mode_used")
            c[m] = c.get(m, 0) + 1
        mode_counts[s] = c
        # integrity checks over every equation, not just the displayed ones
        for v in r.values():
            H, P = v["hypatia"], v["pysr_only"]
            if (H.get("llm_mode_used") == "hybrid_llm_only"
                    and H.get("best_expression") != H.get("llm_expression")):
                flags.append({"seed": s, "equation": v["name"],
                              "flag": "llm_only_but_final_differs_from_llm_expression"})
            h, p = H.get("extrap_r2_far"), P.get("extrap_r2_far")
            if h is not None and p is not None and h < p - WORSE_TOL:
                flags.append({"seed": s, "equation": v["name"],
                              "flag": "hybrid_worse_than_pysr_only",
                              "pysr": fnum(p), "hybrid": fnum(h),
                              "mode": H.get("llm_mode_used")})
    for name in names:
        equations[name] = {}
        for s, r in sorted(runs.items()):
            e = find(r, name)
            if e is None:
                equations[name][s] = None
                continue
            H, N, P = e["hypatia"], e["hypatia_nollm"], e["pysr_only"]
            equations[name][s] = {
                "pysr_r2_far": fnum(P.get("extrap_r2_far")),
                "pysr_expr": P.get("best_expression"),
                "hybrid_r2_far": fnum(H.get("extrap_r2_far")),
                "hybrid_expr": H.get("best_expression"),
                "mode": H.get("llm_mode_used"),
                "llm_expr": H.get("llm_expression"),
                "llm_r2": fnum(H.get("llm_best_r2")),
                "nollm_r2_far": fnum(N.get("extrap_r2_far")),
                "nollm_expr": N.get("best_expression"),
            }
    return mode_counts, equations, flags


def trunc(x, n):
    return str(x)[:n]


def to_markdown(report):
    g, L = report["git"], []
    L.append("# Provenance: exp1 ablation\n")
    L.append(f"Generated: {report['generated_utc']}")
    L.append(f"Commit: `{g['commit']}` ({g['branch']}), committed {g['commit_date']}")
    L.append(f"Remote: {g['remote']}")
    L.append(f"Working tree dirty: {g['dirty']}"
             + (f" ({len(g['dirty_files'])} files)" if g["dirty_files"] else ""))
    L.append(f"Seeds: {report['seeds']}  (unsuffixed dir = seed {DEFAULT_SEED})")
    L.append(f"Skipped dirs: {report['skipped_dirs']}\n")
    L.append("## Result files\n")
    L.append("| seed | path | bytes | sha256 |\n|---|---|---|---|")
    for f in report["files"]:
        L.append(f"| {f['seed']} | {f['path']} | {f['bytes']} | `{f['sha256'][:16]}...` |")
    L.append("\n## llm_mode_used per seed\n")
    for s, c in report["mode_counts"].items():
        L.append(f"- seed {s}: {c}")
    L.append("\n## Per-equation results (extrapolation R2, far)\n")
    for name, per in report["equations"].items():
        L.append(f"### {name}\n")
        L.append("| seed | PySR | Hybrid | mode | LLM expr (R2) | final expr | no-LLM |\n|---|---|---|---|---|---|---|")
        for s, d in per.items():
            if d is None:
                L.append(f"| {s} | missing | | | | | |")
                continue
            L.append(f"| {s} | {d['pysr_r2_far']} | {d['hybrid_r2_far']} | {d['mode']} "
                     f"| `{trunc(d['llm_expr'], 34)}` ({d['llm_r2']}) "
                     f"| `{trunc(d['hybrid_expr'], 40)}` "
                     f"| {d['nollm_r2_far']} `{trunc(d['nollm_expr'], 34)}` |")
        L.append("")
    L.append("## Integrity flags\n")
    if report["flags"]:
        for f in report["flags"]:
            L.append(f"- {f}")
    else:
        L.append("None.")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", help="repo root (default: cwd)")
    ap.add_argument("--results", default=DEFAULT_RESULTS,
                    help="results dir relative to repo")
    ap.add_argument("--names", nargs="*", default=None, help="equation names to show")
    ap.add_argument("--all", action="store_true", help="show every equation")
    ap.add_argument("--out", default=None, help="JSON output path")
    ap.add_argument("--md", default=None, help="markdown output path (also printed)")
    a = ap.parse_args()

    repo = os.path.abspath(a.repo)
    rdir = os.path.join(repo, a.results)
    if not os.path.isdir(rdir):
        sys.exit(f"results dir not found: {rdir}")
    runs, files, skipped = discover(rdir)
    if not runs:
        sys.exit("no exp1_ablation result files found")

    if a.all:
        names = sorted({v["name"] for r in runs.values() for v in r.values()})
    else:
        names = a.names or DEFAULT_NAMES

    mode_counts, equations, flags = build(runs, names)
    report = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "git": git_info(repo),
        "results_dir": a.results,
        "seeds": sorted(runs),
        "skipped_dirs": skipped,
        "files": files,
        "mode_counts": mode_counts,
        "equations": equations,
        "flags": flags,
    }

    out = a.out or os.path.join(rdir, "provenance.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2, default=str)
    md = to_markdown(report)
    if a.md:
        with open(a.md, "w") as f:
            f.write(md)
    print(md)
    print(f"[wrote {out}]")


if __name__ == "__main__":
    main()
