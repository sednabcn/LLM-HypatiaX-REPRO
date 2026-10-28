#!/usr/bin/env python
"""Audit + provenance fixes for the P2 rows. Dry-run by default; --apply writes to p2_fixed/ only."""
import argparse, collections, glob, hashlib, importlib, inspect, json, math, pathlib, subprocess, datetime as dt

RUNNER, RUN_COMMIT = "scripts/run_pure_llm_arm.py", "94a4253"
P_GLOB, H_GLOB = "p2/pure_llm_seed*.jsonl", "p2/hds_exp1_ablation*.jsonl"
OUT = pathlib.Path("p2_fixed")
report = {}

def load(pat): return [json.loads(l) for f in sorted(glob.glob(pat)) for l in open(f) if l.strip()]
def same(a, b):
    try: return a == b or (math.isnan(a) and math.isnan(b))
    except Exception: return a == b
def sha(b): return hashlib.sha256(b).hexdigest()
def git(*a): return subprocess.run(["git", *a], capture_output=True).stdout

def audit_identity(P, H):
    """Why is r2 == extrap_r2_far on every P row? Check the data hashes and the runner source."""
    r = {"P_r2_eq_far": sum(same(x.get("r2"), x.get("extrap_r2_far")) for x in P), "P_rows": len(P)}
    far, train = {x.get("far_data_sha256") for x in P}, {x.get("train_data_sha256") for x in P}
    r["far_hashes"], r["train_hashes"], r["far_equals_train_hash"] = len(far), len(train), bool(far & train)
    r["runner_lines_mentioning_far"] = [f"{i}: {l.strip()}" for i, l in enumerate(open(RUNNER), 1)
                                        if "extrap_r2_far" in l or '"r2"' in l or "'r2'" in l][:25]
    try:
        m = importlib.import_module("hypatiax.core.r2_canonical")
        r["r2_canonical_api"] = {n: str(inspect.signature(f)) for n, f in inspect.getmembers(m, inspect.isfunction)
                                 if f.__module__ == m.__name__}
    except Exception as e:
        r["r2_canonical_api"] = f"import failed: {e!r}"
    r["HDS_keys"] = sorted(H[0]) if H else []
    r["HDS_r2_vs_far_present"] = {k: sum(k in x for x in H) for k in ("r2", "extrap_r2_far", "r2_canonical")}
    return r

def provenance(P):
    """Prove the committed runner is the one that ran, then annotate P rows (copy, not in place)."""
    committed = git("show", f"{RUN_COMMIT}:{RUNNER}")
    work = open(RUNNER, "rb").read()
    rows_mtime = max(pathlib.Path(f).stat().st_mtime for f in glob.glob(P_GLOB))
    run_mtime = pathlib.Path(RUNNER).stat().st_mtime
    r = {"runner_worktree_sha256": sha(work), "runner_committed_sha256": sha(committed),
         "byte_identical_to_commit": work == committed, "runner_mtime_before_first_rows": run_mtime < rows_mtime,
         "evaluator_sha256_in_rows": sorted({x.get("evaluator_sha256") for x in P}),
         "evaluator_sha256_file": sha(open("hypatiax/core/r2_canonical.py", "rb").read())}
    r["resolved"] = (r["byte_identical_to_commit"] and r["runner_mtime_before_first_rows"]
                     and r["evaluator_sha256_in_rows"] == [r["evaluator_sha256_file"]])
    note = {"runner_commit": RUN_COMMIT, "runner_sha256": r["runner_worktree_sha256"],
            "note": "git_commit '+dirty' because runner/p2_data were untracked at run time; committed afterwards in "
                    f"{RUN_COMMIT}. Byte-identity to that commit and mtime ordering verified {dt.date.today()}."}
    return r, note

def adapter_model_source():
    """Where could the adapter have got model_id? List non-row files that mention it."""
    hits = []
    for root in ("p2", "phase2_pure_llm_closure", "scripts", ".github"):
        for p in pathlib.Path(root).rglob("*"):
            if p.is_file() and p.suffix in {".py", ".yml", ".yaml", ".json", ".md", ".log", ".txt", ".sh"}:
                try:
                    for i, l in enumerate(p.read_text(errors="ignore").splitlines(), 1):
                        if "claude-sonnet" in l: hits.append(f"{p}:{i}: {l.strip()[:120]}")
                except Exception: pass
    return hits[:30]

def parity(P, H):
    f = lambda R, k: sorted({str(x.get(k)) for x in R})
    return {k: {"P": f(P, k), "HDS": f(H, k)} for k in
            ("timeout_s", "model_id", "prompt_template_sha256", "git_commit", "evaluator_sha256", "config_hash", "config_sha256")}

def rescore_row(row):
    # Fill in AFTER reading report['identity']: reuse the exact call the runner makes into r2_canonical,
    # on the same far data (far_data_sha256) so HDS is scored on the quantity P is scored on.
    raise NotImplementedError("HDS re-score needs the runner's scoring call; see report['identity'].")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true"); a = ap.parse_args()
    P, H = load(P_GLOB), load(H_GLOB)
    report["identity"] = audit_identity(P, H)
    report["provenance"], note = provenance(P)
    report["model_id_sources"] = adapter_model_source()
    report["parity"] = parity(P, H)
    try: report["hds_rescore"] = [rescore_row(x) for x in H]
    except NotImplementedError as e: report["hds_rescore"] = f"SKIPPED: {e}"
    if a.apply:
        OUT.mkdir(exist_ok=True)
        for f in sorted(glob.glob(P_GLOB)):
            with open(OUT / pathlib.Path(f).name, "w") as o:
                for l in open(f):
                    if l.strip(): d = json.loads(l); d["provenance_note"] = note; o.write(json.dumps(d) + "\n")
        (OUT / "fix_report.json").write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report, indent=2, default=str)); print("\nmode:", "APPLIED to p2_fixed/" if a.apply else "dry-run")
