#!/usr/bin/env python3
"""Phase 3 audit wiring check (no API spend, seconds). Fails loudly if any part of the seed-audit
chain is missing from the checked-out tree, so a run can never start without it.

    python scripts/phase3_audit_wiring_check.py [--root .]

Static: each file must contain the markers that wire the audit in. Functional: the sanitizer's audit
round-trip must produce every G9 row field. Exit 0 = wired, 1 = something is missing."""
import argparse
import subprocess
import sys
from pathlib import Path

CHECKS = {
    "hypatiax/tools/symbolic/guess_sanitizer.py": [
        "def sanitize_guesses", "def record_audit", "def drain_audit", "def reset_audit",
        "def record_llm_response", "def record_llm_r2", "guess_set_sha256", "llm_best_r2"],
    "hypatiax/tools/symbolic/symbolic_engine.py": [
        "guess_sanitizer", "record_audit", "_note_llm_sample(response)", "record_llm_r2",
        "HYPATIAX_LLM_REPLAY_DIR", "isinstance(_fit_exc, TimeoutError)",
        "_LLM_ACCEPT_R2", "_LLM_PRIOR_SEED"],
    "scripts/phase3_engine_adapter.py": [
        "guess_sanitizer.reset_audit()", "guess_sanitizer.drain_audit()", "**seed_audit",
        'seed_audit.get("llm_best_r2")'],
    "scripts/phase3_close.py": [
        "G9 seed record present", "G9 seed record consistent", "G9 no in-fit seed fallback",
        "G9 llm_sample_sha256 (hash of the LLM response)", "G9 same LLM sample in every arm"],
    "scripts/phase3_all.py": [
        "NPY_DISABLE_CPU_FEATURES", "phase3_engine_adapter", "--require-phase2", "run_phase3_ablation"],
    ".github/workflows/ci_phase3_ablation.yml": [
        "HYPATIAX_LLM_REPLAY_DIR", "bypass_audit.csv", "phase3_all.py"],
}
# flags that would hide exactly what the audit guards: must NOT appear on the real path
FORBIDDEN = {
    "scripts/phase3_all.py": ["--allow-legacy-seed-record"],
    ".github/workflows/ci_phase3_ablation.yml": ["--allow-legacy-seed-record", "--allow-dirty"],
}
G9_FIELDS = ("guesses_requested", "guesses_used", "guesses_dropped", "guess_dropped_reasons",
             "guess_fit_fallback", "llm_sample_sha256", "llm_best_r2")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    root = Path(ap.parse_args().root).resolve()
    bad = []
    for rel, needles in CHECKS.items():
        p = root / rel
        if not p.is_file():
            bad.append(f"MISSING FILE {rel}")
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        for n in needles:
            if n not in txt:
                bad.append(f"{rel}: marker not found: {n!r}")
    for rel, flags in FORBIDDEN.items():
        p = root / rel
        if p.is_file():
            txt = p.read_text(encoding="utf-8", errors="replace")
            for f in flags:
                if f in txt:
                    bad.append(f"{rel}: contains {f!r} (must not be used for the real run)")
    # Phase 3 outputs must never be tracked: the runner resumes from phase3_out/*.jsonl and replays
    # phase3_out/llm_replay, so a committed row or sample from an earlier trial silently contaminates a run.
    try:
        tracked = subprocess.run(["git", "-C", str(root), "ls-files", "phase3_out", "phase3_closure_out"],
                                 capture_output=True, text=True, timeout=30)
        if tracked.returncode == 0 and tracked.stdout.strip():
            files = tracked.stdout.split()
            bad.append(f"tracked Phase 3 outputs in git (would be resumed/replayed): {files[:4]}"
                       f"{' ...' if len(files) > 4 else ''}")
    except (OSError, subprocess.SubprocessError):
        pass
    # functional round trip of the audit
    try:
        sys.path.insert(0, str(root))
        from hypatiax.tools.symbolic import guess_sanitizer as G
        G.reset_audit()
        G.record_llm_response("resp A")
        G.record_llm_r2(0.9)
        kept, dropped = G.sanitize_guesses(["x0*x1", "sign(x0)"], ["+", "-", "*", "/"], ["sqrt"], ["x0", "x1"])
        G.record_audit(["x0*x1", "sign(x0)"], kept, dropped)
        row = G.drain_audit()
        miss = [k for k in G9_FIELDS if k not in row]
        if miss:
            bad.append(f"audit round trip lacks row fields {miss}")
        elif not (row["guesses_requested"] == 2 and row["guesses_used"] == 1 and row["guesses_dropped"] == 1
                  and row["llm_sample_sha256"] and row["llm_best_r2"] == 0.9 and row["guess_fit_fallback"] is False):
            bad.append(f"audit round trip gave unexpected values: {row}")
        G.reset_audit()
        if G.drain_audit()["llm_sample_sha256"] is not None:
            bad.append("audit state leaks between cases (reset_audit did not clear the response hash)")
    except Exception as e:
        bad.append(f"audit round trip failed: {type(e).__name__}: {e}")
    if bad:
        print("PHASE 3 AUDIT WIRING: FAIL")
        for b in bad:
            print("  -", b)
        return 1
    print("PHASE 3 AUDIT WIRING: OK (all markers present, forbidden flags absent, audit round trip complete)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
