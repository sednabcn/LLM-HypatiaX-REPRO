#!/usr/bin/env python3
"""
Short trajectory-monitor smoke test.

Runs the Nguyen-12 experiment with deliberately small limits so we can
verify:
  1. PySR starts and completes,
  2. the HOF monitor sees checkpoints,
  3. trajectory diagnostics are written,
  4. generate_figures.py can render the resulting trajectory.

This is NOT a benchmark run.

[FIX-SMOKE-TEST-ENV-NAMES] The env vars this smoke test sets must match
what exp3_nguyen12_hybrid50v_02.py itself reads, or they're silently
ignored and the "smoke test" ends up running the full production config
(1000 iterations x 30 populations, LLM enabled if ANTHROPIC_API_KEY is
set) instead of a small one. Confirmed against the target script:
  N_ITERATIONS   (not PYSR_NITERATIONS)
  POPULATIONS    (not PYSR_POPULATIONS)
  PYSR_SEED / EXPERIMENT_SEED / NN_SEED  (not a plain SEED var)
  USE_LLM is a hardcoded Python constant in the target script -- there is
  no env var that disables it. The only way to force it off is to make
  sure ANTHROPIC_API_KEY is unset/empty for this process, since the
  target script does: "if no API key: USE_LLM = False".
"""

import os
import runpy
from pathlib import Path

# Keep the test short and deterministic.
os.environ.setdefault("PYSR_TIMEOUT", "45")
os.environ.setdefault("METHOD_TIMEOUT", "45")
os.environ.setdefault("PYSR_TRAJECTORY_POLL_SECONDS", "0.05")

# Small search: enough iterations to potentially expose multiple HOF updates,
# but far smaller than the production configuration (1000 x 30).
os.environ.setdefault("N_ITERATIONS", "20")
os.environ.setdefault("POPULATIONS", "1")

# If the experiment honors CASE_RANGE, run only the first Nguyen case.
os.environ.setdefault("CASE_RANGE_START", "1")
os.environ.setdefault("CASE_RANGE_END", "1")

# One seed for the smoke test. The target script's _resolve_seed() checks
# PYSR_SEED / EXPERIMENT_SEED / NN_SEED (in that order) before falling
# back to --seed / 42 -- a bare SEED env var has no effect.
os.environ.setdefault("PYSR_SEED", "0")
os.environ.setdefault("EXPERIMENT_SEED", "0")
os.environ.setdefault("NN_SEED", "0")

# Disable the expensive LLM branch. USE_LLM is a hardcoded constant in the
# target script, not env-driven -- the only lever is the API key check
# ("if no ANTHROPIC_API_KEY: USE_LLM = False"). Explicitly clear it here
# (rather than merely setdefault) so this smoke test stays LLM-free even
# if the calling shell/CI job has a real key exported for other steps.
# CAVEAT: if ANTHROPIC_API_KEY is empty, the target script also falls back
# to reading a .env file (REPRO_ROOT/.env or REPRO_ROOT/hypatiax/.env) --
# this override cannot suppress that. If your repo checkout has one of
# those files with a real key, USE_LLM will still end up True.
if os.environ.get("SMOKE_TEST_ALLOW_LLM", "0") != "1":
    os.environ["ANTHROPIC_API_KEY"] = ""

# Which copy of the experiment script to run. Defaults to the patched
# version (fixed trajectory monitor) if present alongside this file,
# otherwise falls back to the original filename. Override explicitly with
# EXP3_SCRIPT_NAME if your layout differs -- silently picking up the
# wrong (unpatched) file here would make this smoke test validate nothing.
_here = Path(__file__).parent
_default_candidates = [
    os.environ.get("EXP3_SCRIPT_NAME", ""),
    "exp3_nguyen12_hybrid50v_02_patched.py",
    "exp3_nguyen12_hybrid50v_02.py",
]
_script_path = next(
    (_here / name for name in _default_candidates if name and (_here / name).exists()),
    None,
)
if _script_path is None:
    raise FileNotFoundError(
        "No exp3 experiment script found next to this smoke test. Looked for: "
        + ", ".join(n for n in _default_candidates if n)
        + f" under {_here}. Set EXP3_SCRIPT_NAME or place the script alongside this file."
    )

# [FIX-STALE-SCRIPT-CHECK] A prior CI run silently executed a stale,
# pre-trajectory-instrumentation copy of exp3_nguyen12_hybrid50v_02.py (594
# lines, no HOF monitor at all) that happened to sit at the resolved path on
# `master`. It ran to completion, produced a plausible-looking result JSON,
# and only failed three steps later in "Verify trajectory diagnostics were
# written" -- with nothing at this point in the log indicating *why*
# trajectory was empty. Fail here instead, immediately and specifically,
# so a stale/wrong-branch checkout is caught before spending the rest of
# the job's wall-clock time on a run that can't possibly pass.
_script_text = _script_path.read_text(encoding="utf-8", errors="replace")
# [FIX-MARKER-NAME] "_find_hof_path" was never the real function name in
# the trajectory-instrumented script -- it's "_read_pysr_hof_snapshot"
# (the checkpoint reader) plus "_poll_hof_dir_proc" (the separate-process
# poller) and "_fit_with_pysr_trajectory" (the wrapper that drives both).
# The stale marker made this guard fire against the CORRECT, fully
# instrumented file, which is worse than not checking at all: it fails
# the smoke test for the exact opposite reason the check exists.
_required_markers = (
    "_read_pysr_hof_snapshot",
    "_poll_hof_dir_proc",
    "_fit_with_pysr_trajectory",
)
_missing_markers = [m for m in _required_markers if m not in _script_text]
if _missing_markers:
    raise RuntimeError(
        f"{_script_path} does not contain the trajectory-monitor instrumentation "
        f"(missing: {', '.join(_missing_markers)}). This looks like a stale, "
        "pre-instrumentation copy of the script (the pre-fix version was 594 "
        f"lines with no HOF polling at all; this file is {_script_text.count(chr(10)) + 1} "
        "lines). Verify the correct branch/commit was checked out and that "
        "exp3_nguyen12_hybrid50v_02.py at this path is the trajectory-instrumented "
        "version before re-running -- do not let this smoke test silently pass "
        "against the wrong file."
    )

print(f"[smoke test] running {_script_path.name} ({_script_text.count(chr(10)) + 1} lines) "
      f"(N_ITERATIONS={os.environ['N_ITERATIONS']}, POPULATIONS={os.environ['POPULATIONS']}, "
      f"USE_LLM effectively {'ON' if os.environ.get('ANTHROPIC_API_KEY') else 'OFF'})")

runpy.run_path(str(_script_path), run_name="__main__")
