#!/usr/bin/env python3
"""
Short trajectory-monitor smoke test.

Runs the existing Nguyen-12 experiment with deliberately small limits so we can
verify:
  1. PySR starts and completes,
  2. the HOF monitor sees checkpoints,
  3. trajectory diagnostics are written,
  4. generate_figures.py can render the resulting trajectory.

This is NOT a benchmark run.
"""

import os
import runpy
from pathlib import Path

# Keep the test short and deterministic.
os.environ.setdefault("PYSR_TIMEOUT", "45")
os.environ.setdefault("METHOD_TIMEOUT", "45")
os.environ.setdefault("PYSR_TRAJECTORY_POLL_SECONDS", "0.05")

# Small search: enough iterations to potentially expose multiple HOF updates,
# but far smaller than the production configuration.
os.environ.setdefault("PYSR_NITERATIONS", "20")
os.environ.setdefault("PYSR_POPULATIONS", "1")

# If the experiment honors CASE_RANGE, run only the first Nguyen case.
os.environ.setdefault("CASE_RANGE_START", "1")
os.environ.setdefault("CASE_RANGE_END", "1")

# One seed for the smoke test.
os.environ.setdefault("SEED", "0")

# Disable the expensive LLM branch unless the caller explicitly enabled it.
os.environ.setdefault("USE_LLM", "0")

runpy.run_path(str(Path(__file__).with_name("exp3_nguyen12_hybrid50v_02.py")),
               run_name="__main__")
