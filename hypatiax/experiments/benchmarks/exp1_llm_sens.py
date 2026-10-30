#!/usr/bin/env python3
"""
exp1_llm_sens.py -- driver for the LLM-sensitive DeFi protocol (run_all.sh step
`exp1_llm_sens`, CI experiment `exp1_llm_sens`).

One CI shard == one condition (arm x description x blind, see ablation_conditions.py):
  pysr_only__na  hypatia_nollm__na  pure_llm__named  pure_llm__neutral
  hypatia__named hypatia__neutral
Each condition runs all 27 cases of experiment_protocol_defi_llm_sensitive.py for
every seed and writes flat files  exp1_llm_sens_<condition>_seed<N>.json.

REQUIRED WIRING (this driver cannot guess your arm code):
  LLM_SENS_RUNNER         module:function  with signature
        runner(cases, case_ids, arm, seed, condition, out_dir) -> JSON-serialisable
      cases = list of (description, X, y, var_names, metadata); X[:split_index] is
      the (noisy) training part, the rest the clean test part (metadata['split_index']).
      Ground truth is withheld from metadata; the evaluator may read it from the
      file in $LLM_SENS_TRUTH.
  LLM_SENS_PRIOR_TARGETS  comma-separated module:function for EVERY import site of
      get_llm_prior (needed for the LLM arms so cache_salt and blind are enforced).
The driver refuses to run LLM arms without these.
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
# repo root = hypatiax/experiments/benchmarks/../../.. ; makes hypatiax.protocols importable
for _p in (str(_HERE), str(_HERE.parents[2])):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import ablation_conditions as ac  # noqa: E402

PREFIX = "exp1_llm_sens"


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", required=True)
    p.add_argument("--only", nargs="*", default=[], help="condition ids (default: all)")
    p.add_argument("--seeds", nargs="+", type=int, default=[42, 99, 123, 7, 2024])
    p.add_argument("--n", type=int, default=int(os.environ.get("LLM_SENS_N", "40")))
    p.add_argument("--shard", default=os.environ.get("SHARD_INDEX", ""))
    p.add_argument("--run-tag", default=PREFIX)
    p.add_argument("--runner", default=os.environ.get("LLM_SENS_RUNNER", ""))
    p.add_argument("--prior-target", action="append", default=[])
    p.add_argument("--hook", action="append", default=[])
    p.add_argument("--force", action="store_true")
    a = p.parse_args()

    targets = a.prior_target or [t for t in
                                 os.environ.get("LLM_SENS_PRIOR_TARGETS", "").split(",") if t.strip()]
    hooks = a.hook or [h for h in os.environ.get(
        "LLM_SENS_HOOKS", "hypatia_llm_hook:hybrid_llm_condition").split(",") if h.strip()]
    conds = ac.build_conditions(list(ac.ARMS), a.run_tag)
    sel = [c for c in conds if not a.only or c["id"] in a.only]
    if not sel:
        sys.exit(f"no matching conditions for {a.only}; known: {[c['id'] for c in conds]}")
    if not a.runner:
        sys.exit("ERROR: LLM_SENS_RUNNER is not set (module:function adapter). See --help.")
    if any(c["arm"] == "pure_llm" for c in sel) and not targets:
        sys.exit("ERROR: pure_llm selected but no LLM_SENS_PRIOR_TARGETS / --prior-target "
                 "(e.g. hypatia:get_llm_prior): cache_salt and blind cannot be enforced.")
    if any(c["arm"] == "hypatia" for c in sel) and not hooks:
        sys.exit("ERROR: hypatia arm selected but no hook (LLM_SENS_HOOKS / --hook).")

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    plan_dir = Path(tempfile.mkdtemp(prefix="llm_sens_plan_"))   # not committed
    ac.cmd_plan(argparse.Namespace(
        protocol=os.environ.get("LLM_SENS_PROTOCOL",
                                "hypatiax.protocols.experiment_protocol_defi_llm_sensitive:DeFiLLMSensitiveProtocol"),
        domains=None, n=a.n, arms=list(ac.ARMS), run_tag=a.run_tag, out=str(plan_dir)))
    os.environ["LLM_SENS_PLAN_DIR"] = str(plan_dir)
    os.environ["LLM_SENS_TRUTH"] = str(plan_dir / "truth_registry.json")

    sfx = f"_shard{a.shard}" if str(a.shard) != "" else ""
    ac.cmd_run(argparse.Namespace(
        plan=str(plan_dir), runner=a.runner, prior_target=targets, hook=hooks, seeds=a.seeds,
        out=str(out), force=a.force, allow_missing_params=False, only=a.only,
        prefix=PREFIX, report_name=f"{PREFIX}_run_report{sfx}.json"))


if __name__ == "__main__":
    main()
