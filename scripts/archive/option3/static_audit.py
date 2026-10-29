#!/usr/bin/env python3
"""Option 3, Phase 1: static audit of the code paths the report flags as confounds.

Read-only. Reports:
  1. every module that delegates formula generation to PureLLMBaseline.generate_formula
     (the hybrid-arm confound, report s2.1)
  2. absolute ss_tot guards in recovery evaluators (report s2.2, e.g. `ss_tot > 1e-10`)
  3. whether the bypass switches are actually read by the baseline module
  4. whether a --clear-checkpoint flag exists next to --resume in the v2 benchmark
  5. whether a gate-ablation toggle (HDS_ABLATE_GATE) exists (Phase 3 prerequisite)

Exit 1 on hard failures (see flags); everything else is reported as a finding.
"""
import argparse, json, re, sys
from pathlib import Path

SRC_DIRS = ["hypatiax", "scripts"]
SKIP_PARTS = {"__pycache__", "results", ".git"}
BASELINE = Path("hypatiax/core/base_pure_llm/baseline_pure_llm_defi_discovery.py")
V2 = Path("hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py")
FLAGS = ("HYPATIAX_DISABLE_HARDCODED", "HYPATIAX_DISABLE_PROMPT_HINTS")
ABS_GUARD = re.compile(r"ss_tot\s*(?:>|>=|<|<=)\s*\d*\.?\d+(?:[eE]-?\d+)?")
REL_HINT = re.compile(r"ss_tot[^\n]*(?:abs\s*\(|np\.mean|\.std\(|var\(|eps\s*\*|scale|rel)", re.I)


def py_files():
    for d in SRC_DIRS:
        for p in Path(d).rglob("*.py"):
            if SKIP_PARTS & set(p.parts):
                continue
            yield p


def scan():
    deleg, guards = [], []
    for p in py_files():
        try:
            lines = p.read_text(errors="replace").splitlines()
        except OSError:
            continue
        text = "\n".join(lines)
        if "PureLLMBaseline" in text and re.search(r"\bgenerate_formula\s*\(", text):
            hits = [i + 1 for i, l in enumerate(lines)
                    if re.search(r"\.generate_formula\s*\(", l) and not l.strip().startswith("#")]
            if hits and p.as_posix() != BASELINE.as_posix():
                deleg.append({"file": p.as_posix(), "call_lines": hits})
        for i, l in enumerate(lines):
            if l.strip().startswith("#"):
                continue
            if ABS_GUARD.search(l) and not REL_HINT.search(l):
                guards.append({"file": p.as_posix(), "line": i + 1, "code": l.strip()[:140]})
    return deleg, guards


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="audit_out/static_audit.json")
    ap.add_argument("--md", default="")
    ap.add_argument("--warn-only", action="store_true",
                    help="report absolute ss_tot guards but do not fail on them")
    ap.add_argument("--require-ablation-toggle", action="store_true")
    a = ap.parse_args()

    deleg, guards = scan()
    failures, notes = [], []

    if not BASELINE.exists():
        failures.append(f"{BASELINE} not found")
        base_txt = ""
    else:
        base_txt = BASELINE.read_text(errors="replace")
    for f in FLAGS:
        if f not in base_txt:
            failures.append(f"{BASELINE.name} never reads {f}; the clean-run switch does nothing")

    if guards and not a.warn_only:
        failures.append(f"{len(guards)} absolute ss_tot guard(s) found; evaluator not yet audited")

    v2 = V2.read_text(errors="replace") if V2.exists() else ""
    has_clear = "--clear-checkpoint" in v2 or "clear_checkpoint" in v2
    if not has_clear:
        notes.append("v2 benchmark has no --clear-checkpoint option: rely on the runner's "
                     "find -delete (clean_llm_rerun) and confirm checkpoint dirs match")

    toggle_files = [p.as_posix() for p in py_files()
                    if "HDS_ABLATE_GATE" in p.read_text(errors="replace")]
    if not toggle_files:
        msg = "no code reads HDS_ABLATE_GATE: leave-one-gate-out (Phase 3) cannot run yet"
        (failures if a.require_ablation_toggle else notes).append(msg)

    report = {"delegating_modules": deleg, "absolute_ss_tot_guards": guards,
              "ablation_toggle_files": toggle_files, "notes": notes, "failures": failures}
    Path(a.json).parent.mkdir(parents=True, exist_ok=True)
    Path(a.json).write_text(json.dumps(report, indent=2))

    out = ["### Option 3 static audit", "",
           f"**Modules delegating to PureLLMBaseline.generate_formula: {len(deleg)}**"]
    out += [f"- `{d['file']}` lines {d['call_lines']}" for d in deleg] or ["- none"]
    out += ["", f"**Absolute ss_tot guards: {len(guards)}**"]
    out += [f"- `{g['file']}:{g['line']}` `{g['code']}`" for g in guards] or ["- none"]
    out += ["", f"**Gate toggle files (HDS_ABLATE_GATE): {len(toggle_files)}**"]
    out += [f"- `{f}`" for f in toggle_files] or ["- none"]
    if notes:
        out += ["", "**Notes**"] + [f"- {n}" for n in notes]
    if failures:
        out += ["", "**FAILURES**"] + [f"- {f}" for f in failures]
    text = "\n".join(out)
    print(text)
    if a.md:
        with open(a.md, "a") as fh:
            fh.write(text + "\n")
    for f in failures:
        print(f"::error::{f}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
