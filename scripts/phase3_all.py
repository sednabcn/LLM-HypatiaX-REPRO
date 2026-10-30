#!/usr/bin/env python3
"""
phase3_all.py - ONE command for Option 3 / Phase 3 (leave-one-gate-out ablation).

    python scripts/phase3_all.py                 # preflight -> run -> close
    python scripts/phase3_all.py --stage preflight   # only the checks (no API spend)
    python scripts/phase3_all.py --stage run         # resume the runs
    python scripts/phase3_all.py --stage close       # only the closure gate

Put it in scripts/ next to phase3_engine_adapter.py, run_phase3_ablation.py, phase3_close.py.
Run from the repo root. It needs no edits to those three files: it patches the adapter
IN MEMORY so rows carry the P-arm hash scheme, a real model_id and a real prompt hash.

PREFLIGHT (blocking unless marked warn) - everything that would otherwise invalidate hours of runs:
  P1  repo root, evaluator sha256 starts with 7d5395ed (the Phase 2 pin)
  P2  engine gates exist (_LLM_ACCEPT_R2, _LLM_PRIOR_SEED); --apply-engine-patch adds them
  P3  clean-run flags: HYPATIAX_DISABLE_PROMPT_HINTS=1, HYPATIAX_DISABLE_HARDCODED=1 are forced,
      HYPATIAX_LLM_MODEL is unset, an API key is present
  P4  git tree clean (or --allow-dirty, recorded as a caveat)
  P5  P rows + Phase 2 manifest exist; equations come from the P rows
  P6  G1 dry check: regenerate train/far data for every (equation, seed) in the P rows with
      the P-arm hash scheme and require equality with the P rows' hashes. This is what
      decides whether G1 can pass; it costs seconds, not hours.
RUN    leave-one-out for llm_acceptance and pysr_prior (the only gates wired in v50_2),
       full config first per (seed, equation); resumable.
CLOSE  phase3_close.py with: P-arm G1 rows, Phase 2 manifest (required), pinned evaluator,
       and --omit reasons for the four gates that have no switch in the v50_2 path.

Exit codes: 0 closed, 1 not closed / preflight failed, 2 bad usage.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, os.getcwd())

EVAL_PREFIX = "7d5395ed"
EVAL_PATH = "hypatiax/core/r2_canonical.py"
ENGINE_PATH = "hypatiax/tools/symbolic/symbolic_engine.py"
WIRED = ["llm_acceptance", "pysr_prior"]
OMIT = {
    'probe': 'not part of the v50_2 / Core-15 path; this gate lives in the v3c DeFi pipeline (hypatiax_defi_benchmark_v3c.py), so it is untested here, not shown to have no effect',
    'complexity_routing': 'only complexity gate is `if False and ...` in symbolic_engine.py, off in the full config, so ablating it is identical by construction',
    'nn_augmentation': 'not part of the v50_2 / Core-15 path; this gate lives in the v3c DeFi pipeline (hypatiax_defi_benchmark_v3c.py), so it is untested here, not shown to have no effect',
    'blend_weight': 'not part of the v50_2 / Core-15 path; this gate lives in the v3c DeFi pipeline (hypatiax_defi_benchmark_v3c.py), so it is untested here, not shown to have no effect',
}


# ------------------------------------------------------------------ helpers
def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def hash_arrays(X, y):
    """IDENTICAL to scripts/run_pure_llm_arm.py::hash_arrays (shape-prefixed little-endian f8)."""
    import numpy as np
    h = hashlib.sha256()
    for a in (np.asarray(X, dtype="<f8"), np.asarray(y, dtype="<f8")):
        h.update(str(a.shape).encode())
        h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()


def read_jsonl(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


class Pre:
    def __init__(self):
        self.rows = []

    def add(self, name, ok, detail="", blocking=True):
        self.rows.append((name, bool(ok), detail, blocking))
        tag = "PASS" if ok else ("FAIL" if blocking else "WARN")
        print(f"  [{tag}] {name}" + (f" - {detail}" if detail else ""))

    @property
    def ok(self):
        return all(ok for _, ok, _, b in self.rows if b)


def apply_engine_patch(path):
    s = Path(path).read_text(encoding="utf-8")
    if "_LLM_ACCEPT_R2" in s and "_LLM_PRIOR_SEED" in s:
        return "already patched"
    a_old = "if best_hyp.r2_score and best_hyp.r2_score > 0.95:"
    b_old = "if best_hyp.r2_score is None or best_hyp.r2_score < 0.5:"
    if s.count(a_old) != 1 or s.count(b_old) != 1:
        raise RuntimeError(f"anchors not unique (accept x{s.count(a_old)}, prior x{s.count(b_old)}); patch by hand")
    s = s.replace(a_old, "if best_hyp.r2_score and best_hyp.r2_score > self._LLM_ACCEPT_R2:")
    s = s.replace(b_old, "if (not self._LLM_PRIOR_SEED) or best_hyp.r2_score is None or best_hyp.r2_score < 0.5:")
    m = re.search(r"^class SymbolicEngineWithLLM\b[^\n]*:\n", s, re.M)
    if not m:
        raise RuntimeError("class SymbolicEngineWithLLM not found")
    s = s[:m.end()] + "    _LLM_ACCEPT_R2 = 0.95\n    _LLM_PRIOR_SEED = True\n" + s[m.end():]
    Path(path).write_text(s, encoding="utf-8")
    return "patched (commit it before the run, or the tree is dirty)"


def force_clean_env():
    os.environ["HYPATIAX_DISABLE_PROMPT_HINTS"] = "1"
    os.environ["HYPATIAX_DISABLE_HARDCODED"] = "1"
    os.environ["HYPATIAX_STRICT"] = "1"
    os.environ.pop("HYPATIAX_R2_SIGN_FLIP", None)
    os.environ.pop("HYPATIAX_LLM_MODEL", None)


# ---------------------------------------------------------------- preflight
def preflight(a):
    print("== PREFLIGHT")
    p = Pre()
    ev_ok = Path(EVAL_PATH).is_file() and sha_file(EVAL_PATH).startswith(EVAL_PREFIX)
    p.add("P1 evaluator pinned", ev_ok, f"{EVAL_PATH} sha {sha_file(EVAL_PATH)[:8] if Path(EVAL_PATH).is_file() else 'missing'}, want {EVAL_PREFIX}")
    if not Path(ENGINE_PATH).is_file():
        p.add("P2 engine file present", False, ENGINE_PATH)
        return p, None
    if a.apply_engine_patch:
        try:
            print("  engine patch:", apply_engine_patch(ENGINE_PATH))
        except RuntimeError as e:
            p.add("P2 engine patch applied", False, str(e))
    txt = Path(ENGINE_PATH).read_text(encoding="utf-8")
    p.add("P2 engine gates exist", "_LLM_ACCEPT_R2" in txt and "_LLM_PRIOR_SEED" in txt,
          "run with --apply-engine-patch if missing")
    force_clean_env()
    p.add("P3 clean-run flags forced", True, "PROMPT_HINTS=1, HARDCODED=1, LLM_MODEL unset (in this process)")
    key = any(os.environ.get(k) for k in ("ANTHROPIC_API_KEY", "CLAUDE_API_KEY"))
    p.add("P3 API key in environment", key, "strict mode aborts the hypatia condition without it")

    import run_phase3_ablation as R
    commit, dirty = R.git_state([a.out_dir.rstrip("/") + "/", "p2_", "phase3_out", "phase3_closure_out"])
    p.add("P4 clean git tree", not dirty or a.allow_dirty,
          f"{commit[:7]} {'DIRTY (accepted via --allow-dirty, recorded)' if dirty else 'clean'}")
    prow_files = sorted(Path(".").glob(a.p_rows_glob))
    p.add("P5 P-arm rows found", len(prow_files) >= 1, f"{len(prow_files)} files for {a.p_rows_glob}")
    p.add("P5 Phase 2 manifest found", Path(a.phase2_manifest).is_file(), a.phase2_manifest)
    if not prow_files:
        return p, None
    prows = [r for f in prow_files for r in read_jsonl(f)]
    a._prows = prows
    eqs = []
    for r in prows:
        if r["equation"] not in eqs:
            eqs.append(r["equation"])
    seeds = sorted({int(r["seed"]) for r in prows})
    a._eqs, a._seeds_p = eqs, seeds
    p.add("P5 seeds in P rows cover requested seeds", set(a.seeds) <= set(seeds), f"P seeds {seeds}, requested {a.seeds}")

    # P6: G1 dry check against the P-arm rows, before any API spend.
    try:
        import importlib
        import phase3_engine_adapter as A
        exp1 = importlib.import_module(A.EXP1_MODULE)
        names = {e["name"] for e in exp1.CORE_15}
        p.add("P5 every P equation is in exp1.CORE_15", set(eqs) <= names, f"unknown: {sorted(set(eqs) - names)}")
        bad, checked = [], 0
        for r in prows:
            eq = next((e for e in exp1.CORE_15 if e["name"] == r["equation"]), None)
            if eq is None:
                continue
            s = int(r["seed"])
            eq_seed = s + exp1.EQ_ID.get(eq["name"], 0) * 7
            with A._rng_isolated():
                X, _, y, _, _, _ = exp1.generate_data(eq, N=200, noise_level=0.05, seed=eq_seed)
                Xf, yf = exp1.generate_extrap_data(eq, regime="far", N=100, seed=eq_seed)
            checked += 1
            train_expected = r.get("train_data_sha256")
            far_expected = r.get("far_data_sha256")
            train_actual = hash_arrays(X, y)
            far_actual = hash_arrays(Xf, yf)
            if train_actual != train_expected or far_actual != far_expected:
                bad.append({
                    "equation": r["equation"],
                    "seed": s,
                    "train_expected": train_expected,
                    "train_actual": train_actual,
                    "far_expected": far_expected,
                    "far_actual": far_actual,
                })
        if bad:
            print("P6 G1 dry check mismatches:")
            for m in bad:
                print(
                    f"  equation={m['equation']}, seed={m['seed']}\n"
                    f"    train expected={m['train_expected']}\n"
                    f"    train actual  ={m['train_actual']}\n"
                    f"    far   expected={m['far_expected']}\n"
                    f"    far   actual  ={m['far_actual']}"
                )
        p.add("P6 G1 dry check: HDS data hashes == P rows (P hash scheme)", not bad and checked > 0,
              f"{checked} (equation, seed) pairs checked; {len(bad)} mismatches {[(m['equation'], m['seed']) for m in bad[:4]]}")
    except Exception as e:  # engine import problems must be visible, not swallowed
        p.add("P6 G1 dry check", False, f"{type(e).__name__}: {e}")
    return p, (commit, dirty)


# ---------------------------------------------------------------------- run
def build_engine(a):
    """Adapter patched in memory: P-arm hash scheme, real model_id and prompt hash, no placeholder guards."""
    import phase3_engine_adapter as A
    prompt_sha = sha_file(ENGINE_PATH)
    A._sha = hash_arrays
    A._model_id = lambda: a.model_id
    A._prompt_sha = lambda: prompt_sha
    A._preflight = lambda: None
    # run_condition's extrap_r2_far already goes through r2_canonical.r2_scored (see exp1._safe_r2)
    A._rescore_far = lambda res: res.get("extrap_r2_far")
    return A.run_case, prompt_sha


def run_stage(a, git):
    print("== RUN")
    import run_phase3_ablation as R
    force_clean_env()
    engine, prompt_sha = build_engine(a)
    commit, dirty = git
    ns = argparse.Namespace(
        out_dir=a.out_dir, components=WIRED, seeds=a.seeds, equations=a._eqs, timeout_s=a.timeout_s,
        code_version=None, evaluator_version=None, retry_errors=a.retry_errors, max_cases=a.max_cases)
    n = R.run(ns, engine, commit, dirty, sha_file(EVAL_PATH))
    print(f"run stage: {n} new rows in {a.out_dir} (prompt_template_sha256 = engine file hash {prompt_sha[:12]})")
    return n


# -------------------------------------------------------------------- close
def close_stage(a):
    print("== CLOSE")
    out = Path(a.out_dir)
    files = [str(out / "full.jsonl")] + [str(out / f"{c}.jsonl") for c in WIRED]
    missing = [f for f in files if not Path(f).is_file()]
    if missing:
        print(f"  cannot close: missing {missing}")
        return 1
    cmd = [sys.executable, str(HERE / "phase3_close.py"), "--results", *files,
           "--phase2-manifest", a.phase2_manifest, "--require-phase2",
           "--p-rows", a.p_rows_glob, "--expected-evaluator-sha", EVAL_PREFIX,
           "--out-dir", a.close_dir]
    if a.allow_dirty:
        cmd.append("--allow-dirty")
    for k, why in OMIT.items():
        cmd += ["--omit", f"{k}:{why}"]
    print("  " + " ".join(cmd[:6]) + " ...")
    return subprocess.run(cmd).returncode


# ----------------------------------------------------------------- selftest
def selftest():
    import numpy as np
    X, y = np.arange(6.0).reshape(3, 2), np.arange(3.0)
    h = hash_arrays(X, y)
    assert h == hash_arrays(X.astype("<f8"), y) and h != hash_arrays(X.ravel(), y)  # shape is part of the hash
    import tempfile
    d = Path(tempfile.mkdtemp()) / "e.py"
    d.write_text("class SymbolicEngineWithLLM:\n    def f(self, best_hyp):\n"
                 "        if best_hyp.r2_score and best_hyp.r2_score > 0.95:\n            pass\n"
                 "        if best_hyp.r2_score is None or best_hyp.r2_score < 0.5:\n            pass\n")
    print(apply_engine_patch(d)); assert apply_engine_patch(d) == "already patched"
    s = d.read_text(); assert "self._LLM_ACCEPT_R2" in s and "not self._LLM_PRIOR_SEED" in s
    compile(s, "e", "exec")
    print("selftest OK")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=["preflight", "run", "close", "all"], default="all")
    ap.add_argument("--out-dir", default="phase3_out", help="where the per-config jsonl rows go")
    ap.add_argument("--close-dir", default="phase3_closure_out")
    ap.add_argument("--seeds", default="42,99,123")
    ap.add_argument("--timeout-s", type=float, default=3600.0)
    ap.add_argument("--model-id", default="claude-sonnet-4-6", help="from your smoke log; written to every row")
    ap.add_argument("--p-rows-glob", default="p2/pure_llm_seed*.jsonl")
    ap.add_argument("--phase2-manifest", default="phase2_out/phase2_closure.json")
    ap.add_argument("--apply-engine-patch", action="store_true")
    ap.add_argument("--allow-dirty", action="store_true")
    ap.add_argument("--retry-errors", action="store_true")
    ap.add_argument("--max-cases", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        selftest()
        return 0
    a.seeds = [int(s) for s in a.seeds.split(",") if s.strip()]

    git = None
    if a.stage != "close":
        pre, git = preflight(a)
        if not pre.ok:
            print("\nPREFLIGHT FAILED - nothing was run. Fix the FAIL lines above.")
            return 1
        print("PREFLIGHT OK")
    if a.stage == "preflight":
        return 0
    if a.stage in ("run", "all"):
        run_stage(a, git)
    if a.stage in ("close", "all"):
        return close_stage(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
