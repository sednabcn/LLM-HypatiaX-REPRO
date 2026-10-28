#!/usr/bin/env python3
"""
run_phase3_ablation.py - Phase 3 leave-one-gate-out runner (feeds phase3_close.py).

For every (seed, equation) it runs the FULL HDS v50_2 configuration and then each
leave-one-out configuration, back to back, so a run stopped early still holds paired data.
One output file per configuration: <out-dir>/full.jsonl, <out-dir>/<component>.jsonl,
one flat row per (ablated_component, equation, seed), every field phase3_close.py requires.

The runner does NOT score anything itself. It calls an engine adapter

    run_case(equation: str, seed: int, disabled: list[str], timeout_s: float) -> dict

(default scripts.phase3_engine_adapter:run_case; override with --engine module:function).
`disabled` is [] for the full config, else [component]. The adapter must score through
hypatiax.core.r2_canonical.r2_checked and return these keys:

    status, r2_raw, formula, generation_path, llm_called, bypass_used, bypass_kind,
    llm_mode_used, model_id, train_data_sha256, far_data_sha256, prompt_template_sha256
optional:
    r2 (defaults to r2_raw), r2_status, error_stage, candidate_r2_status,
    extrap_r2_far, timed_out, llm_r2, gate_reachable, train_r2, extrap_r2_near,
    extrap_r2_medium

A missing required key aborts the run (a silent default would defeat the closure checks).
The runner adds: ablated_component, config_diff, equation, seed, split_id, runtime_s,
timeout_s, code_version, evaluator_version, evaluator_sha256, git_commit, code_dirty,
flags (hypatiax.core.flags.flag_state()) and clean_run.

Safety:
  * refuses to run from a dirty tree unless --allow-dirty (then code_dirty is recorded True)
  * resumable: finished (config, equation, seed) rows are skipped, rows are never edited
  * --retry-errors moves status=="error" rows to <config>.attempts.jsonl and reruns them
  * --max-cases N stops after N new cases (budget control)
  * flag_state() raises if a clean-run flag is misconfigured, which aborts the run on purpose
"""
import argparse
import hashlib
import importlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

COMPONENTS = ["llm_acceptance", "probe", "complexity_routing",
              "nn_augmentation", "blend_weight", "pysr_prior"]
ENGINE_REQUIRED = ["status", "r2_raw", "formula", "generation_path", "llm_called", "bypass_used",
                   "bypass_kind", "llm_mode_used",
                   "model_id", "train_data_sha256", "far_data_sha256", "prompt_template_sha256"]


def _git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, check=True).stdout.strip()


def git_state(ignore_prefixes):
    try:
        commit = _git("rev-parse", "HEAD")
        lines = _git("status", "--porcelain").splitlines()
    except (OSError, subprocess.CalledProcessError):
        return "nogit", True
    dirty = [l for l in lines if not any(l[3:].strip().strip('"').startswith(p) for p in ignore_prefixes)]
    return commit, bool(dirty)


def file_sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_engine(spec):
    mod, _, fn = spec.partition(":")
    sys.path.insert(0, os.getcwd())
    return getattr(importlib.import_module(mod), fn)


def read_rows(path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _flag_state():
    """Imported lazily so this module imports even if the repo root is not yet on sys.path."""
    sys.path.insert(0, os.getcwd())
    from hypatiax.core.flags import flag_state
    return flag_state()


def run(args, engine, commit, dirty, evaluator_sha, flag_fn=None):
    flag_fn = flag_fn or _flag_state
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    configs = ["full"] + [c for c in args.components if c != "full"]
    done = {}
    for c in configs:
        p = out / f"{c}.jsonl"
        rows = read_rows(p)
        if args.retry_errors and any(r.get("status") == "error" for r in rows):
            with open(out / f"{c}.attempts.jsonl", "a", encoding="utf-8") as f:
                for r in rows:
                    if r.get("status") == "error":
                        f.write(json.dumps(r) + "\n")
            rows = [r for r in rows if r.get("status") != "error"]
            p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        done[c] = {(r["equation"], int(r["seed"])) for r in rows}

    code_version = args.code_version or f"v50_2@{commit[:7]}"
    evaluator_version = args.evaluator_version or f"r2_checked@{evaluator_sha[:8]}"
    n_new = 0
    for seed in args.seeds:
        for eq in args.equations:
            for c in configs:
                if (eq, seed) in done[c]:
                    continue
                if args.max_cases and n_new >= args.max_cases:
                    print(f"--max-cases {args.max_cases} reached; rerun the same command to resume.")
                    return n_new
                disabled = [] if c == "full" else [c]
                t0 = time.monotonic()
                try:
                    res = engine(eq, seed, disabled, args.timeout_s)
                    err = None
                except Exception as e:  # infrastructure failure: record, do not hide
                    res, err = {}, f"{type(e).__name__}: {e}"
                runtime = time.monotonic() - t0
                if err is None:
                    miss = [k for k in ENGINE_REQUIRED if k not in res]
                    if miss:
                        print(f"ABORT: engine result for {c}/{eq}/{seed} lacks {miss}", file=sys.stderr)
                        sys.exit(2)
                    status = res["status"]
                    if res.get("timed_out") and status == "ok":
                        status = "timeout"
                    row = dict(res)
                    row["status"] = status
                    row.setdefault("r2", res["r2_raw"])
                    row.setdefault("r2_status", "ok" if status == "ok" else f"failed:{status}")
                else:
                    row = {"status": "error", "error_stage": err, "r2": None, "r2_raw": None,
                           "r2_status": "failed:error", "formula": None, "generation_path": "error",
                           "llm_called": False, "bypass_used": False, "model_id": "unknown",
                           "train_data_sha256": "unknown", "far_data_sha256": "unknown",
                           "prompt_template_sha256": "unknown",
                           "bypass_kind": None, "llm_mode_used": None, "llm_r2": None,
                           "gate_reachable": None, "train_r2": None,
                           "extrap_r2_near": None, "extrap_r2_medium": None}
                fs = flag_fn()  # raises on a misconfigured flag: aborts the run on purpose
                row.update({
                    "ablated_component": None if c == "full" else c,
                    "config_diff": disabled,
                    "equation": eq, "seed": seed, "split_id": f"{eq}|{seed}",
                    "runtime_s": round(runtime, 3), "timeout_s": args.timeout_s,
                    "code_version": code_version, "evaluator_version": evaluator_version,
                    "evaluator_sha256": evaluator_sha, "git_commit": commit, "code_dirty": dirty,
                    "flags": fs, "clean_run": fs.get("clean_run"),
                })
                with open(out / f"{c}.jsonl", "a", encoding="utf-8") as f:
                    f.write(json.dumps(row) + "\n")
                n_new += 1
                print(f"[{n_new}] {c:18s} {eq:28s} seed {seed}  {row['status']}  r2_raw={row['r2_raw']}")
    return n_new


# ----------------------------------------------------------------- selftest
def _fake_engine(equation, seed, disabled, timeout_s):
    base = {"model_id": "fake-model", "generation_path": "hds_fake", "llm_called": True,
            "bypass_used": False, "bypass_kind": "none", "llm_mode_used": "hybrid_llm_only",
            "prompt_template_sha256": "p" * 64,
            "train_data_sha256": hashlib.sha256(f"tr|{equation}|{seed}".encode()).hexdigest(),
            "far_data_sha256": hashlib.sha256(f"far|{equation}|{seed}".encode()).hexdigest()}
    if equation == "Michaelis-Menten" and "probe" not in disabled and seed == 99:
        return {**base, "status": "failed", "r2_raw": float("-inf"), "r2": float("-inf"), "formula": None,
                "error_stage": "no_calls", "r2_status": "failed:no_calls",
                "candidate_r2_status": ["nonfinite_pred"] * 3}
    hit = equation != "Kinetic Energy" or "pysr_prior" not in disabled
    r2 = 0.9999 if hit else 0.4
    return {**base, "status": "ok", "r2_raw": r2, "formula": "def formula(x): return x", "r2_status": "ok"}


def selftest():
    d = tempfile.mkdtemp(prefix="p3_selftest_")
    ns = argparse.Namespace(
        out_dir=d, components=COMPONENTS, seeds=[42, 99, 123],
        equations=["Michaelis-Menten", "Kinetic Energy", "Arrhenius", "Ideal Gas"],
        timeout_s=3600, code_version="v50_2@selftest", evaluator_version="r2_checked@selftest",
        retry_errors=False, max_cases=0)
    fake_flags = lambda: {"clean_run": True, "selftest": True}
    n = run(ns, _fake_engine, "selftest", False, "7d5395ed" + "0" * 56, flag_fn=fake_flags)
    print(f"selftest wrote {n} rows to {d}")
    return d


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engine", default="scripts.phase3_engine_adapter:run_case")
    ap.add_argument("--out-dir", default="results/ablation_p3")
    ap.add_argument("--components", default=",".join(COMPONENTS), help="comma list; 'full' is always run")
    ap.add_argument("--seeds", default="42,99,123")
    ap.add_argument("--equations", default=None, help="comma list of equation names")
    ap.add_argument("--equations-from", default=None, help="jsonl whose 'equation' field lists them, e.g. p2/pure_llm_seed42.jsonl")
    ap.add_argument("--timeout-s", type=float, default=3600.0,
                    help="3600 matches the Phase 2 HDS runs, which the full config must reproduce")
    ap.add_argument("--evaluator-path", default="hypatiax/core/r2_canonical.py")
    ap.add_argument("--code-version", default=None)
    ap.add_argument("--evaluator-version", default=None)
    ap.add_argument("--allow-dirty", action="store_true")
    ap.add_argument("--retry-errors", action="store_true")
    ap.add_argument("--max-cases", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        selftest()
        return 0
    a.seeds = [int(s) for s in a.seeds.split(",") if s.strip()]
    a.components = [c.strip() for c in a.components.split(",") if c.strip()]
    bad = [c for c in a.components if c != "full" and c not in COMPONENTS]
    if bad:
        print(f"unknown components: {bad}", file=sys.stderr)
        return 2
    if a.equations:
        a.equations = [e.strip() for e in a.equations.split(",") if e.strip()]
    elif a.equations_from:
        seen = []
        for r in read_rows(Path(a.equations_from)):
            if r["equation"] not in seen:
                seen.append(r["equation"])
        a.equations = seen
    else:
        print("give --equations or --equations-from", file=sys.stderr)
        return 2
    commit, dirty = git_state([a.out_dir.rstrip("/") + "/", "p2_", "phase3_out"])
    if dirty and not a.allow_dirty:
        print("Working tree is dirty (G8). Commit or stash, or pass --allow-dirty to record the caveat.", file=sys.stderr)
        return 2
    run(a, load_engine(a.engine), commit, dirty, file_sha(a.evaluator_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
