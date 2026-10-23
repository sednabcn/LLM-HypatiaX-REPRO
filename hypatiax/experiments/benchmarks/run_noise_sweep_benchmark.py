#!/usr/bin/env python3
"""
run_noise_sweep_benchmark.py
============================

Noise-level sweep experiment for the HypatiaX benchmark suite.

Runs the selected methods (default: EnhancedHybridSystemDeFi = 3 and
HybridSystemLLMNN all-domains = 4) across noise levels sigma.

REVISION NOTES (re-runs plan, B5)
---------------------------------
  * ONE recovery-threshold policy for every sigma: --threshold (default
    0.99).  Exact recovery (--exact-threshold, default 0.999999) is always
    reported alongside it.  The old per-sigma ladder (0.95/0.995/0.99/0.90)
    is only available via --legacy-thresholds.
  * --seed sets python/numpy seeds and exports PYSR_SEED, EXPERIMENT_SEED
    and NN_SEED to the inner runner, and tags every output/checkpoint name
    with _seed<N>, so several noise seeds per sigma never collide.
  * NaN / inf R2 on a row is counted as a failure (n_nonfinite) instead of
    silently dropped from the denominator-visible statistics.
  * Result-file matching: a result JSON is only accepted if its own
    protocol.noise_level matches the sigma launched (mtime alone is not enough
    when shards/seeds share a directory).
  * Noise-ceiling audit: with noise = sigma*std(y), no method can exceed
    R2 = 1 - sigma^2/(1+sigma^2) against noisy targets.  Rows above that
    (plus a 3-s.d. finite-sample slack) are counted in n_above_noise_ceiling
    and flagged in the report: they indicate CLEAN-target scoring.
  * sigma is declared as a FRACTION of std(y) in the output JSON
    ("sigma_definition").  The injection itself lives in the inner runner
    and is NOT verified here -- audit it (clean vs noisy targets) first.

Background
----------
sigma=0% (noiseless) and sigma=0.5% are already completed and on disk.
Pass those result files via --existing-results so they are merged into
the final report without re-running.

The two target methods were identified from the noisy benchmark results
(protocol_core_noisy_20260313_094752.json):

    EnhancedHybridSystemDeFi (core)        median R2 = 0.9999998   wins 18/30  avg 19.7s
    HybridSystemLLMNN all-domains (core)   median R2 = 0.9999998   wins 11/30  avg 10.8s

Both are in a separate tier from the remaining four methods
(median R2 approx 0.9977).

Important per-equation notes
-----------------------------
  - M4 (HybridSystemLLMNN) has a catastrophic failure on "Newton's
    gravitational force" at sigma=5% in the baseline run: R2=0.643.
    This is flagged in the report and should be verified across seeds.
  - M4 is on average 1.8x faster than M3 (10.8s vs 19.7s per equation).

What it does
------------
1. Optionally merges pre-existing result JSONs via --existing-results
   (list of  sigma_value:path  pairs, no spaces around the colon).
2. For each sigma in --noise-levels that is NOT already covered, launches
   run_comparative_suite_benchmark_v2.py as a subprocess.
3. Uses mtime-gating to match each run to its result file, preventing
   collisions between the three noisy passes that all write
   protocol_core_noisy_*.json.
4. Saves
       data/results/comparison_results/feynman-tests/noise-sweep/noise_sweep_<TS>.json
       data/results/comparison_results/feynman-tests/noise-sweep/noise_sweep_<TS>.csv

Usage
-----
    # Default: methods 3 & 4, sigma in {1%,5%,10%}
    python run_noise_sweep_benchmark.py

    # Merge the already-completed sigma=0% and sigma=0.5% runs:
    python run_noise_sweep_benchmark.py \\
        --existing-results 0.0:path/to/noiseless.json 0.005:path/to/sig0005.json

    # Full five-level sweep (re-running sigma=0 and sigma=0.5% too):
    python run_noise_sweep_benchmark.py --noise-levels 0.0 0.005 0.01 0.05 0.10

    # Quick smoke-test on one equation
    python run_noise_sweep_benchmark.py --test arrhenius

    # Abort on any failure
    python run_noise_sweep_benchmark.py --fail-fast

Outputs
-------
  data/results/comparison_results/feynman-tests/noise-sweep/noise_sweep_<TS>.json
  data/results/comparison_results/feynman-tests/noise-sweep/noise_sweep_<TS>.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
random.seed(42)
np.random.seed(42)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_HERE        = Path(__file__).resolve().parent
_PKG_ROOT    = _HERE.parent.parent
_RUNNER      = _HERE / "run_comparative_suite_benchmark_v2.py"

# OUT_BASE: set by CI worker (env OUT_BASE = hypatiax/data/results).
# suppB output must land in feynman-tests/noise-sweep/ so that:
#   • ci_experiment_simplify.yml move_matching "noise_sweep_*.json" finds them
#   • the verify step glob comparison_results/feynman-tests/noise-sweep/*.json passes
#   • the artifact upload path matches RESULT_SUBDIR
# Fall back to the package-relative path when running locally without OUT_BASE.
_OUT_BASE    = Path(os.environ["OUT_BASE"]) if "OUT_BASE" in os.environ else (_PKG_ROOT / "data/results")
_RESULTS_DIR = _OUT_BASE / "comparison_results/feynman-tests/noise-sweep"
_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# FEATURE-NSHARDS-SUFFIX (corrected 2026-06-23): when set, append "_nshardsNN"
# to every output filename this script writes. NN is the per-shard index
# (1-based, zero-padded), not the total shard count -- run_all.sh's suppB
# step derives it from SHARD_INDEX+1, so each of the N concurrently-running
# matrix shards gets a DISTINCT suffix (01, 02, ... for shard 0, 1, ...).
# Using the total count instead would tag every shard identically and risk
# collisions, since shards run in parallel and write second-granularity
# timestamped filenames. Empty string when unset (e.g. local runs outside
# CI) so filenames are unchanged from before this feature existed.
_NSHARDS_SUFFIX = os.environ.get("HYPATIAX_NSHARDS_SUFFIX", "").strip()
_SHARD_TAG = f"_nshards{_NSHARDS_SUFFIX}" if _NSHARDS_SUFFIX else ""
_SEED_TAG  = ""   # set in main() once --seed is known: "_seed<N>"

# Full 5-level sweep matching CI `noise_levels` default "0.0,0.5,1.0,5.0,10.0"
# (fractions: 0.0, 0.005, 0.01, 0.05, 0.10).
# sigma=0% and sigma=0.5% are passed via --existing-results when already done;
# running all 5 here keeps the default consistent with Tab 28 requirements.
_DEFAULT_NOISE_LEVELS: list[float] = [0.0, 0.005, 0.01, 0.05, 0.10]

# Top-two methods from protocol_core_noisy_20260313_094752.json:
#   3 -> EnhancedHybridSystemDeFi (core)       median R2=0.9999998  wins=18/30
#   4 -> HybridSystemLLMNN all-domains (core)  median R2=0.9999998  wins=11/30
_DEFAULT_METHODS: list[int] = [3, 4]

# R2 below this triggers a catastrophic-failure flag in the report
_CATASTROPHIC_R2_THRESHOLD: float = 0.90

# Single recovery-threshold policy (re-runs plan: fixed 0.99 for cross-
# condition comparison, strict 0.999999 reported as "exact recovery").
_DEFAULT_THRESHOLD:   float = 0.99
_EXACT_THRESHOLD:     float = 0.999999

# Legacy per-sigma ladder, kept ONLY for --legacy-thresholds reproduction of
# the old tables.  Do not use for new results.
_LEGACY_THRESHOLDS: dict = {
    0.0: 0.999999, 0.0005: 0.995, 0.001: 0.995, 0.005: 0.995,
    0.01: 0.990, 0.05: 0.950, 0.10: 0.900,
}

# Seed handling (matches the pca/v3c convention: NN seed = 2024 + (seed-42)).
def _seed_from_env() -> int:
    for k in ("EXPERIMENT_SEED", "PYSR_SEED"):
        v = os.environ.get(k, "").strip()
        if v:
            try:
                return int(v)
            except ValueError:
                pass
    return 42


def _seed_env(seed: int) -> dict:
    return {
        "PYSR_SEED":       str(seed),
        "EXPERIMENT_SEED": str(seed),
        "NN_SEED":         str(2024 + (seed - 42)),
    }


def _resolve_threshold(sigma: float, args: argparse.Namespace) -> float:
    """Single place that decides the recovery threshold for a sigma level."""
    for tok in getattr(args, "threshold_per_sigma", []) or []:
        try:
            s_, v_ = tok.split(":")
            if abs(float(s_) - sigma) < 1e-12:
                return float(v_)
        except ValueError:
            pass
    if getattr(args, "legacy_thresholds", False):
        if sigma == 0.0:
            return args.threshold_noiseless
        return _LEGACY_THRESHOLDS.get(sigma, args.threshold_noisy)
    return args.threshold


# ============================================================================
# TEE LOGGER
# ============================================================================

class _TeeLogger:
    """Mirror every write to both a real stream and an open log file."""

    def __init__(self, stream, log_file):
        self._stream   = stream
        self._log_file = log_file

    def write(self, data):
        self._stream.write(data)
        self._log_file.write(data)
        self._log_file.flush()

    def flush(self):
        self._stream.flush()
        self._log_file.flush()

    def fileno(self):
        return self._stream.fileno()

    def isatty(self):
        return hasattr(self._stream, "isatty") and self._stream.isatty()


# ============================================================================
# RESULT HELPERS
# ============================================================================

def _result_matches(path: Path, noise_level, n_samples=None) -> bool:
    """
    True if the result JSON's own protocol block matches the run we launched.

    Guards against (a) parallel shards/seeds writing into the same directory and
    (b) a crashed run silently picking up a stale file from another sigma.
    Keys ABSENT from the file are not held against it (no protection then; the
    noise-ceiling audit below is the backstop).  noise_level may be stored as a
    fraction (0.01) or a percent (1.0); both are accepted.
    """
    try:
        with open(path) as fh:
            proto = (json.load(fh) or {}).get("protocol", {}) or {}
    except Exception:
        return False
    nl = proto.get("noise_level")
    if noise_level is not None and nl is not None:
        try:
            nlf = float(nl)
        except (TypeError, ValueError):
            return False
        want = float(noise_level)
        if not (abs(nlf - want) <= 1e-9 or abs(nlf - want * 100.0) <= 1e-7):
            return False
    if n_samples is not None:
        for k in ("n_samples", "samples", "n"):
            if proto.get(k) is not None:
                try:
                    if int(proto[k]) != int(n_samples):
                        return False
                except (TypeError, ValueError):
                    pass
                break
    return True


def _noise_ceiling(sigma: float) -> float:
    """
    Max achievable R2 of the TRUE function scored against NOISY targets when
    noise = sigma * std(y):   1 - sigma^2 / (1 + sigma^2)   (~ 1 - sigma^2).
    """
    return 1.0 - (sigma ** 2) / (1.0 + sigma ** 2)


def _ceiling_tol(sigma: float, n_test: int) -> float:
    """Finite-sample slack on the ceiling: ~3 s.d. of the R2 estimate."""
    return 3.0 * (sigma ** 2) * (2.0 / max(int(n_test), 20)) ** 0.5


def _find_result_written_after(mode: str, t_start: float, noise_level=None) -> Path | None:
    """
    Return the newest result JSON for *mode* whose mtime is >= t_start.

    Prevents the collision where three sequential sigma>0 passes all write
    protocol_core_noisy_*.json and a naive find-latest would return the
    same file for all three.
    """
    candidates = [
        p for p in _RESULTS_DIR.glob(f"protocol_core_{mode}_*.json")
        if p.stat().st_mtime >= t_start and _result_matches(p, noise_level)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _find_latest_result(mode: str, noise_level=None) -> Path | None:
    """Return the most-recently-modified JSON for protocol_core_{mode}_*.json."""
    candidates = sorted(
        _RESULTS_DIR.glob(f"protocol_core_{mode}_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    candidates = [p for p in candidates if _result_matches(p, noise_level)]
    return candidates[0] if candidates else None


def _extract_per_test(data: dict) -> dict[str, dict]:
    """Return {equation_name: {method_name: result_dict}}."""
    out: dict[str, dict] = {}
    for test in data.get("tests", []):
        eq_name = (
            test.get("metadata", {}).get("equation_name", "")
            or test.get("description", "unknown")
        )
        key = test.get("metadata", {}).get("equation_name", eq_name) or eq_name[:50]
        out[key] = {name: res for name, res in test.get("results", {}).items()}
    return out


def _load_results(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


# ============================================================================
# SUBPROCESS BUILDER
# ============================================================================

def _build_runner_cmd(
    noise_level: float,
    args:        argparse.Namespace,
    runner:      Path,
) -> tuple[list[str], str]:
    """
    Build the subprocess command for one noise level.

    Returns (cmd_list, sigma_label) where sigma_label encodes the sigma
    as an integer number of thousandths, giving unique checkpoint names:
      0.000 -> sig0000
      0.005 -> sig0005
      0.010 -> sig0010
      0.050 -> sig0050
      0.100 -> sig0100
    """
    # FIX SIGMA-LABEL-COLLISION: thousandths gave sigma=0 and sigma=0.0005 the same
    # label (sig0000).  Ten-thousandths, 5 digits, keeps all CI levels distinct.
    sigma_label = f"sig{int(round(noise_level * 10000)):05d}"
    cmd = [sys.executable, str(runner)]

    # Single threshold policy (see _resolve_threshold); legacy ladder opt-in.
    _sigma_threshold = _resolve_threshold(noise_level, args)

    if noise_level == 0.0:
        cmd.append("--noiseless")
    cmd += ["--threshold", str(_sigma_threshold)]

    cmd += ["--samples",        str(args.samples)]
    cmd += ["--nn-seeds",       str(args.nn_seeds)]
    cmd += ["--method-timeout", str(args.method_timeout)]
    cmd += ["--pysr-timeout",   str(args.pysr_timeout)]
    cmd += ["--methods"] + [str(m) for m in args.methods]

    if args.skip_pysr:
        cmd.append("--skip-pysr")
    if getattr(args, "test", None):
        # Normalize common human-readable aliases to canonical Feynman IDs.
        # The inner runner (run_comparative_suite_benchmark_v2.py) only
        # accepts canonical IDs (e.g. "I.12.1"); passing a bare name like
        # "newton" causes an exit-code-1 crash with no result JSON written.
        _TEST_ALIASES: dict = {
            # Newton's gravitational force  F = G*m1*m2/r^2
            "newton":          "I.12.1",
            "newton_gravity":  "I.12.1",
            "gravity":         "I.12.1",
            # Coulomb's law  F = q1*q2/(4*pi*eps0*r^2)
            "coulomb":         "I.12.2",
            # Kinetic energy  E = 0.5*m*v^2
            "kinetic_energy":  "I.12.4",
            "kinetic":         "I.12.4",
            # Arrhenius  k = A*exp(-Ea/(R*T))
            "arrhenius":       "II.11.27",
            # Ideal gas  P*V = n*R*T
            "ideal_gas":       "II.11.28",
        }
        canonical = _TEST_ALIASES.get(args.test.lower().replace(" ", "_"), args.test)
        if canonical != args.test:
            print(f"  [INFO] --test alias '{args.test}' resolved to canonical ID '{canonical}'")
        cmd += ["--test", canonical]
    if getattr(args, "equations", None):
        cmd += ["--equations"] + [str(e) for e in args.equations]
    if getattr(args, "domain", "all_domains") != "all_domains":
        cmd += ["--domain", args.domain]
    if getattr(args, "series", None):
        cmd += ["--series", args.series]
    if getattr(args, "benchmark", "feynman") != "feynman":
        cmd += ["--benchmark", args.benchmark]
    if args.verbose:
        cmd.append("--verbose")
    if getattr(args, "quiet", False):
        cmd.append("--quiet")
    if getattr(args, "no_llm_cache", False):
        cmd.append("--no-llm-cache")

    # ALL sigma levels — including sigma=0 (noiseless) — write to _RESULTS_DIR
    # (noise-sweep/).  suppB needs every protocol_core_*.json in the same dir
    # so the aggregate glob finds all five sigma values.
    cmd += ["--output-dir", str(_RESULTS_DIR)]

    # Unique checkpoint per sigma — prevents noisy passes colliding.
    # FEATURE-NSHARDS-SUFFIX: also tag with the per-shard-index _nshardsNN
    # suffix so concurrently-running shards (each pinned to a different sigma
    # via NOISE_LEVEL, but all five sharing this same _FLAT_OUTPUT_DIR
    # checkpoint location -- see that script's _checkpoint_path()) never
    # collide with each other, regardless of sigma.
    cmd += ["--checkpoint-name", f"noise_sweep_{sigma_label}_checkpoint{_SEED_TAG}{_SHARD_TAG}"]

    # NOTE: The TASK_ID env-var → --test forwarding block that previously lived
    # here has been removed.  The CI suppB dispatch shards by feynman *domain*
    # (e.g. "feynman_biology"), not by individual equation ID.  Forwarding the
    # domain key as --test caused the inner runner to exit with code 1 because
    # domain keys are not valid equation IDs in its registry.  The correct
    # scoping is handled by DOMAIN_FILTER / --domain (see below) and by the
    # YAML's per-noise-level loop; no per-equation TASK_ID injection is needed.

    # ── CI domain filter ──────────────────────────────────────────────────────
    # The CI suppB dispatch sets DOMAIN_FILTER to a space-separated list of
    # feynman domain keys assigned to this shard (e.g. "feynman_biology
    # feynman_chemistry").  The YAML loop calls this script once per noise
    # level; each call should restrict the inner runner to the shard's domains.
    # When DOMAIN_FILTER contains exactly one domain and --domain was not
    # overridden on the CLI, honour it.  For multiple domains the inner runner
    # sweeps all assigned equations in one pass (YAML does not loop per-domain
    # for suppB), so we cannot express it as a single --domain flag — log and
    # proceed with the full sweep for this shard's noise level.
    _ci_domain_filter = os.environ.get("DOMAIN_FILTER", "").strip()
    if _ci_domain_filter and getattr(args, "domain", "all_domains") == "all_domains":
        _domains = _ci_domain_filter.split()
        if len(_domains) == 1:
            cmd += ["--domain", _domains[0]]
            print(f"  [CI] DOMAIN_FILTER={_ci_domain_filter!r} → --domain {_domains[0]!r}")
        else:
            print(f"  [CI] DOMAIN_FILTER={_ci_domain_filter!r} — {len(_domains)} domains, "
                  f"inner runner will sweep all assigned equations in one pass")

    return cmd, sigma_label


# ============================================================================
# RUN ONE NOISE LEVEL
# ============================================================================

def _run_noise_level(
    noise_level: float,
    args:        argparse.Namespace,
    runner:      Path,
) -> Path | None:
    """
    Run the inner benchmark for one noise level and return the result JSON path.

    Noise is injected via HYPATIAX_NOISE_LEVEL env var.
    The result JSON is identified by mtime >= run-start time to avoid
    the collision bug where all three noisy passes write to the same
    protocol_core_noisy_*.json filename pattern.
    """
    pct = f"{noise_level*100:.4g}%"
    print(f"\n{'='*80}")
    print(f"  NOISE SWEEP  --  sigma={pct}  (noise_level={noise_level:.4f})".center(80))
    print(f"{'='*80}\n")

    cmd, _label = _build_runner_cmd(noise_level, args, runner)
    child_env   = os.environ.copy()
    child_env["HYPATIAX_NOISE_LEVEL"] = str(noise_level)
    child_env.update(_seed_env(args.seed))   # propagate seed to inner runner
    # Remove TASK_ID / TASK_IDS from the child environment.  These are set by
    # the CI worker step and contain feynman domain keys (e.g. "feynman_biology")
    # or compound shard IDs ("noise0.0__feynman_biology"), not equation IDs.
    # Forwarding them into the inner runner would cause invalid --test injection
    # if run_comparative_suite_benchmark_v2.py has its own TASK_ID-reading path.
    child_env.pop("TASK_ID",  None)
    child_env.pop("TASK_IDS", None)

    print(f"  Command: {' '.join(cmd)}\n")
    t_start = time.time()
    result  = subprocess.run(cmd, env=child_env)
    elapsed = time.time() - t_start

    if result.returncode != 0:
        print(f"\n  ERROR: Runner exited with code {result.returncode} "
              f"for noise_level={noise_level:.4f}  ({elapsed/60:.1f} min).")
        if getattr(args, "fail_fast", False):
            print("  FAIL-FAST: aborting noise sweep.")
            sys.exit(result.returncode)
        print("  Attempting to locate partial results...")

    mode      = "noiseless" if noise_level == 0.0 else "noisy"
    json_path = _find_result_written_after(mode, t_start, noise_level=noise_level)
    if json_path is None:
        # Fallback only accepts a file whose own protocol.noise_level matches;
        # never a stale file from another sigma/seed.
        json_path = _find_latest_result(mode, noise_level=noise_level)

    if json_path is None:
        print(f"\n  ERROR: No result JSON found for noise_level={noise_level:.4f}.")
        if getattr(args, "fail_fast", False):
            sys.exit(1)
        return None

    print(f"\n  OK: noise_level={noise_level:.4f} completed in {elapsed/60:.1f} min")
    print(f"     Results: {json_path}")
    return json_path


# ============================================================================
# AGGREGATION
# ============================================================================

def _aggregate_results(
    noise_levels:    list[float],
    result_paths:    dict[float, Path | None],
    threshold_fn,
    exact_threshold: float = _EXACT_THRESHOLD,
    noise_n_test_hint: int = 40,
) -> dict:
    """
    Build a unified cross-noise comparison object.

    per_noise schema per sigma level:
      method_summary  : median_r2, mean_r2, std_r2, recovery_rate,
                        exact_recovery_rate, n_success, n_total, n_nonfinite,
                        threshold_used, n_catastrophic
      per_equation    : {eq: {method: {r2, rmse, success, catastrophic}}}
      catastrophic_failures: [{equation, method, r2}]  (R2 < 0.90)

    cross_noise_summary: {method: {sigma_str: {median_r2, recovery_rate,
                                               std_r2, n_catastrophic}}}
    """
    loaded: dict[float, dict | None] = {}
    all_methods: set = set()

    for sigma in noise_levels:
        path = result_paths.get(sigma)
        if path is None:
            loaded[sigma] = None
            continue
        try:
            data = _load_results(path)
        except Exception as exc:
            print(f"  WARNING: Cannot load {path}: {exc}")
            loaded[sigma] = None
            continue
        loaded[sigma] = data
        for eq_methods in _extract_per_test(data).values():
            all_methods.update(eq_methods.keys())

    all_methods_sorted = sorted(all_methods)
    per_noise_data: dict[str, dict | None] = {}

    for sigma in noise_levels:
        sigma_str = f"{sigma:.4f}"
        data      = loaded.get(sigma)
        if data is None:
            per_noise_data[sigma_str] = None
            continue

        per_eq    = _extract_per_test(data)
        threshold = threshold_fn(sigma)
        method_summary: dict[str, dict] = {}
        catastrophic_failures: list[dict] = []

        for method in all_methods_sorted:
            r2_vals: list[float] = []
            time_vals: list[float] = []
            n_success = n_total = n_recovery = n_catastrophic = 0
            n_exact = n_nonfinite = 0
            n_above_ceiling = 0
            sigma_c = (
                (_noise_ceiling(sigma), _ceiling_tol(sigma, noise_n_test_hint))
                if sigma > 0 else None
            )

            for eq_name, eq_results in per_eq.items():
                n_total += 1
                res = eq_results.get(method, {})
                # FIX-TIMING-DROPPED (2026-08-04): 'time' is already present
                # in the raw per-equation result (same protocol_core_*.json
                # subprocess output this method's per_equation dict is built
                # from -- see _extract_per_test, which passes the full res
                # dict through) but was never collected here. This is the
                # same bug found and fixed in run_sample_complexity_benchmark
                # .py's _aggregate_results() for Issue 3 -- see
                # 03_ehsdefi_runtime_SECTION_REPLACEMENT.tex. Collected over
                # ALL attempts (not gated on success), matching that fix and
                # matching how tab:overall's Avg Runtime column is computed.
                t = res.get("time")
                if t is not None:
                    try:
                        tf = float(t)
                        if np.isfinite(tf):
                            time_vals.append(tf)
                    except (TypeError, ValueError):
                        pass
                # NaN / -inf / missing R2 is a FAILURE, not a missing cell.
                _r2_raw = res.get("r2")
                try:
                    _r2_ok = _r2_raw is not None and np.isfinite(float(_r2_raw))
                except (TypeError, ValueError):
                    _r2_ok = False
                if not _r2_ok:
                    n_nonfinite += 1
                elif sigma_c is not None and float(_r2_raw) > sigma_c[0] + sigma_c[1]:
                    # Checked on every finite R2, success-flagged or not.
                    n_above_ceiling += 1
                if res.get("success", False):
                    n_success += 1
                    r2 = res.get("r2")
                    if r2 is not None:
                        try:
                            r2f = float(r2)
                            if np.isfinite(r2f):
                                r2_vals.append(r2f)
                                if r2f >= threshold:
                                    n_recovery += 1
                                if r2f >= exact_threshold:
                                    n_exact += 1
                                if r2f < _CATASTROPHIC_R2_THRESHOLD:
                                    n_catastrophic += 1
                                    catastrophic_failures.append(
                                        {"equation": eq_name, "method": method, "r2": r2f}
                                    )
                        except (TypeError, ValueError):
                            pass

            method_summary[method] = {
                "median_r2":      float(np.median(r2_vals))         if r2_vals          else None,
                "mean_r2":        float(np.mean(r2_vals))           if r2_vals          else None,
                "std_r2":         float(np.std(r2_vals, ddof=1))    if len(r2_vals) > 1 else 0.0,
                "recovery_rate":  n_recovery / n_total              if n_total > 0      else None,
                "exact_recovery_rate": n_exact / n_total            if n_total > 0      else None,
                "exact_threshold": exact_threshold,
                "n_nonfinite":    n_nonfinite,
                # B5 check: R2 above the theoretical ceiling for noisy targets
                # means the row was scored on CLEAN targets (or noise was not
                # applied as declared).  None at sigma=0 (no ceiling).
                "noise_r2_ceiling": (sigma_c[0] if sigma_c else None),
                "n_above_noise_ceiling": (n_above_ceiling if sigma_c else None),
                "n_success":      n_success,
                "n_total":        n_total,
                "threshold_used": threshold,
                "n_catastrophic": n_catastrophic,
                # FIX-TIMING-DROPPED: see comment in the collection loop above.
                "mean_time_s":    float(np.mean(time_vals))          if time_vals          else None,
                "median_time_s":  float(np.median(time_vals))        if time_vals          else None,
                "std_time_s":     float(np.std(time_vals, ddof=1))   if len(time_vals) > 1 else 0.0,
                "n_timed":        len(time_vals),
            }

        per_noise_data[sigma_str] = {
            "method_summary":       method_summary,
            "catastrophic_failures": sorted(catastrophic_failures, key=lambda x: x["r2"]),
            "per_equation": {
                eq: {
                    m: {
                        "r2":          eq_res.get("r2"),
                        "rmse":        eq_res.get("rmse"),
                        "success":     eq_res.get("success", False),
                        "llm_called":  eq_res.get("llm_called"),    # B2
                        "bypass_kind": eq_res.get("bypass_kind"),   # B2
                        # FIX-TIMING-DROPPED: see comment in the collection
                        # loop above -- this is the root fix for Issue 3's
                        # missing tab:time_noise timing data.
                        "time":        eq_res.get("time"),
                        "catastrophic": (
                            np.isfinite(float(eq_res["r2"]))
                            and float(eq_res["r2"]) < _CATASTROPHIC_R2_THRESHOLD
                        ) if eq_res.get("r2") is not None else False,
                    }
                    for m, eq_res in methods_dict.items()
                }
                for eq, methods_dict in per_eq.items()
            },
        }

    # Cross-noise summary
    cross_noise: dict[str, dict] = {}
    for method in all_methods_sorted:
        cross_noise[method] = {}
        for sigma in noise_levels:
            sigma_str = f"{sigma:.4f}"
            pnd = per_noise_data.get(sigma_str)
            if pnd is None:
                cross_noise[method][sigma_str] = None
                continue
            ms = pnd["method_summary"].get(method, {})
            cross_noise[method][sigma_str] = {
                "median_r2":      ms.get("median_r2"),
                "recovery_rate":  ms.get("recovery_rate"),
                "exact_recovery_rate": ms.get("exact_recovery_rate"),
                "std_r2":         ms.get("std_r2"),
                "n_catastrophic": ms.get("n_catastrophic", 0),
                "n_nonfinite":    ms.get("n_nonfinite", 0),
                "n_above_noise_ceiling": ms.get("n_above_noise_ceiling"),
            }

    return {
        "generated":           datetime.now().isoformat(),
        "noise_levels":        noise_levels,
        "sigma_definition":    "fraction of std(y) (declared; injection lives in the inner runner; see n_above_noise_ceiling for an indirect check)",
        "exact_threshold":     exact_threshold,
        "methods":             all_methods_sorted,
        "per_noise":           per_noise_data,
        "cross_noise_summary": cross_noise,
    }


# ============================================================================
# REPORTING
# ============================================================================

def _print_noise_sweep_table(agg: dict) -> None:
    """Pretty-print cross-noise comparison tables and flag catastrophic failures."""
    methods      = agg["methods"]
    noise_levels = agg["noise_levels"]

    if not methods or not noise_levels:
        print("  (no data to display)")
        return

    col_w   = 13
    headers = "".join(f"sigma={s*100:.4g}%".rjust(col_w) for s in noise_levels)

    # Median R2 table
    print(f"\n{'='*100}")
    print("  NOISE SWEEP  --  Median R2 across sigma levels".center(100))
    print(f"{'='*100}")
    print(f"  {'Method':<44}" + headers)
    print("  " + "-" * 98)
    for method in sorted(methods):
        row = f"  {method:<44}"
        for sigma in noise_levels:
            pnd = agg["per_noise"].get(f"{sigma:.4f}")
            if pnd is None:
                row += f"{'N/A':>{col_w}}"
                continue
            ms  = pnd["method_summary"].get(method, {})
            med = ms.get("median_r2")
            cat = ms.get("n_catastrophic", 0)
            val = (f"{med:.5f}" if med is not None else "N/A") + (" (!)  " if cat > 0 else "")
            row += f"{val:>{col_w}}"
        print(row)

    # Recovery rate table
    print(f"\n{'='*100}")
    print("  NOISE SWEEP  --  Recovery Rate  (R2 >= threshold)".center(100))
    _thr_used = sorted({
        ms.get("threshold_used")
        for pnd in agg["per_noise"].values() if pnd
        for ms in pnd["method_summary"].values()
        if ms.get("threshold_used") is not None
    })
    print(f"  threshold(s) used: {_thr_used}   exact: {agg.get('exact_threshold')}".center(100))
    print(f"{'='*100}")
    print(f"  {'Method':<44}" + headers)
    print("  " + "-" * 98)
    for method in sorted(methods):
        row = f"  {method:<44}"
        for sigma in noise_levels:
            pnd = agg["per_noise"].get(f"{sigma:.4f}")
            if pnd is None:
                row += f"{'N/A':>{col_w}}"
                continue
            ms  = pnd["method_summary"].get(method, {})
            rec = ms.get("recovery_rate")
            val = f"{rec*100:.1f}%" if rec is not None else "N/A"
            row += f"{val:>{col_w}}"
        print(row)
    print(f"  (!) = one or more equations with R2 < {_CATASTROPHIC_R2_THRESHOLD} (catastrophic)")

    # Exact-recovery table
    print(f"\n{'='*100}")
    print(f"  NOISE SWEEP  --  Exact Recovery  (R2 >= {agg.get('exact_threshold')})".center(100))
    print(f"{'='*100}")
    print(f"  {'Method':<44}" + headers)
    print("  " + "-" * 98)
    for method in sorted(methods):
        row = f"  {method:<44}"
        for sigma in noise_levels:
            pnd = agg["per_noise"].get(f"{sigma:.4f}")
            if pnd is None:
                row += f"{'N/A':>{col_w}}"
                continue
            ex = pnd["method_summary"].get(method, {}).get("exact_recovery_rate")
            row += f"{(f'{ex*100:.1f}%' if ex is not None else 'N/A'):>{col_w}}"
        print(row)

    # Noise-ceiling audit (B5)
    _ceil_rows = []
    for sigma in noise_levels:
        pnd = agg["per_noise"].get(f"{sigma:.4f}")
        if not pnd:
            continue
        for m_, ms_ in pnd["method_summary"].items():
            if ms_.get("n_above_noise_ceiling"):
                _ceil_rows.append((sigma, m_, ms_["n_above_noise_ceiling"], ms_["noise_r2_ceiling"]))
    if _ceil_rows:
        print(f"\n  !! NOISE-CEILING AUDIT: R2 above the theoretical ceiling "
              f"1 - s^2/(1+s^2) for noisy targets:")
        for sg, m_, k, c in _ceil_rows:
            print(f"     sigma={sg*100:.4g}%  {m_:<44} {k} equation(s) above ceiling {c:.6f}")
        print("     -> those rows were most likely scored on CLEAN targets, or noise was not "
              "applied as declared.")

    # Catastrophic failures block
    all_cats = []
    for sigma in noise_levels:
        pnd = agg["per_noise"].get(f"{sigma:.4f}")
        if pnd:
            for cf in pnd.get("catastrophic_failures", []):
                all_cats.append({**cf, "sigma": sigma})

    if all_cats:
        print(f"\n{'='*100}")
        print(f"  CATASTROPHIC FAILURES  (R2 < {_CATASTROPHIC_R2_THRESHOLD:.2f})".center(100))
        print(f"{'='*100}")
        print(f"  {'sigma':>8}  {'Method':<44}  {'Equation':<38}  {'R2':>8}")
        print("  " + "-" * 96)
        for cf in sorted(all_cats, key=lambda x: x["r2"]):
            eq_short = cf["equation"][:38]
            print(f"  {cf['sigma']*100:>7.4g}%  {cf['method']:<44}  {eq_short:<38}  {cf['r2']:>8.4f}")
        print()

    print(f"{'='*100}\n")


def _save_sweep_json(agg: dict, ts: str) -> Path:
    # FIX-EMPTY-SHARD-WRITE: refuse to write a noise_sweep_*.json (the Shape S
    # shard file that merge_shards.py will later read) when every per_noise
    # point's per_equation dict is empty.  An empty shard file passes
    # merge_sweep_files()'s is_sweep_file() check (it has the correct top-level
    # keys) but contributes zero equation records, so the merged _merged.json
    # ends up with 0 records and the analysis step dies with "FATAL: EMPTY
    # DATASET" several pipeline steps later with no pointer back to here.
    #
    # Raising here gives an immediate, actionable error message in the worker
    # job log — the correct place to diagnose why the inner benchmark produced
    # no results — rather than a cryptic downstream failure in the analysis job.
    #
    # Note: agg["noise_levels"] may legitimately contain only one sigma when
    # running in CI single-level mode (NOISE_LEVEL env var).  The guard checks
    # per_equation across ALL sigma points that are present, so a single empty
    # point still triggers the error.
    n_eq_total = sum(
        len(pt.get("per_equation", {}))
        for pt in agg.get("per_noise", {}).values()
        if isinstance(pt, dict)
    )
    if n_eq_total == 0:
        sigmas_present = list(agg.get("per_noise", {}).keys())
        raise RuntimeError(
            f"FATAL: noise sweep produced 0 equation records across all "
            f"sigma points {sigmas_present} — the inner benchmark run(s) "
            f"failed or timed out for every equation.  The shard file "
            f"'{_RESULTS_DIR / f'noise_sweep_{ts}{_SEED_TAG}{_SHARD_TAG}.json'}' will "
            f"NOT be written to prevent poisoning the downstream merge step.  "
            f"Check the run_comparative_suite_benchmark_v2.py output above "
            f"for the underlying failure cause (missing runner, API key "
            f"error, timeout, etc.)."
        )
    path = _RESULTS_DIR / f"noise_sweep_{ts}{_SEED_TAG}{_SHARD_TAG}.json"
    with open(path, "w") as f:
        json.dump(agg, f, indent=2, default=str)
    print(f"  Saved noise sweep JSON  -> {path}")
    return path


def _save_sweep_csv(agg: dict, ts: str) -> Path:
    """
    Two-section CSV:
      section=aggregate    : one row per (method, sigma) -- summary stats
      section=per_equation : one row per (method, sigma, equation) -- individual R2
    """
    path = _RESULTS_DIR / f"noise_sweep_{ts}{_SEED_TAG}{_SHARD_TAG}.csv"
    fieldnames = [
        "section", "method", "noise_level_fraction", "noise_level_pct", "equation",
        "median_r2", "mean_r2", "std_r2", "recovery_rate", "exact_recovery_rate",
        "n_success", "n_total", "n_nonfinite", "n_above_noise_ceiling", "threshold_used", "n_catastrophic", "seed",
        "r2", "rmse", "success", "catastrophic",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for sigma in agg["noise_levels"]:
            sigma_str = f"{sigma:.4f}"
            pnd       = agg["per_noise"].get(sigma_str)
            for method in agg["methods"]:
                ms = (pnd or {}).get("method_summary", {}).get(method, {}) if pnd else {}
                # Aggregate row
                writer.writerow({
                    "section": "aggregate", "method": method,
                    "noise_level_fraction": sigma,
                    "noise_level_pct":      f"{sigma*100:.4g}%",
                    "equation": "",
                    "median_r2":      ms.get("median_r2"),
                    "mean_r2":        ms.get("mean_r2"),
                    "std_r2":         ms.get("std_r2"),
                    "recovery_rate":  ms.get("recovery_rate"),
                    "exact_recovery_rate": ms.get("exact_recovery_rate"),
                    "n_nonfinite":    ms.get("n_nonfinite"),
                    "n_above_noise_ceiling": ms.get("n_above_noise_ceiling"),
                    "seed":           agg.get("seed"),
                    "n_success":      ms.get("n_success"),
                    "n_total":        ms.get("n_total"),
                    "threshold_used": ms.get("threshold_used"),
                    "n_catastrophic": ms.get("n_catastrophic", 0),
                    "r2": "", "rmse": "", "success": "", "catastrophic": "",
                })
                if pnd is None:
                    continue
                # Per-equation rows
                for eq, eq_methods in pnd.get("per_equation", {}).items():
                    res = eq_methods.get(method, {})
                    writer.writerow({
                        "section": "per_equation", "method": method,
                        "noise_level_fraction": sigma,
                        "noise_level_pct":      f"{sigma*100:.4g}%",
                        "equation": eq,
                        "median_r2": "", "mean_r2": "", "std_r2": "",
                        "recovery_rate": "", "n_success": "", "n_total": "",
                        "threshold_used": "", "n_catastrophic": "",
                        "r2":          res.get("r2"),
                        "rmse":        res.get("rmse"),
                        "success":     res.get("success"),
                        "catastrophic": res.get("catastrophic", False),
                    })
    print(f"  Saved noise sweep CSV   -> {path}")
    return path


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:
    from hypatiax.core.enforce_flags import enforce; enforce()  # fail-closed flag guard
    parser = argparse.ArgumentParser(
        description=(
            "Noise-level sweep  sigma in {1%,5%,10%}  for "
            "EnhancedHybridDeFi and HybridSystemLLMNN (top two from HypatiaX "
            "noisy benchmark).  Merge pre-existing results with --existing-results."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--noise-levels", type=float, nargs="+",
        default=_DEFAULT_NOISE_LEVELS, dest="noise_levels", metavar="SIGMA",
        help=(
            "Noise levels to run (fractions of signal std). "
            "Default: full 5-level sweep {0, 0.005, 0.01, 0.05, 0.10} "
            "(= 0%%, 0.5%%, 1%%, 5%%, 10%% — all required for Tab 28). "
            "Pass --existing-results to skip already-completed sigma values. "
            f"Default: {_DEFAULT_NOISE_LEVELS}"
        ),
    )
    parser.add_argument(
        "--existing-results", nargs="+", default=[], dest="existing_results",
        metavar="SIGMA:PATH",
        help=(
            "Pre-existing result JSONs to merge without re-running. "
            "Format: sigma_value:path  e.g.  0.0:noiseless.json  0.005:sig0005.json"
        ),
    )
    parser.add_argument(
        "--methods", type=int, nargs="+", default=_DEFAULT_METHODS, metavar="N",
        help=(
            "Core method indices (1-6). "
            "Default: [3, 4]  (EnhancedHybridDeFi + HybridLLMNN-all-domains)."
        ),
    )
    parser.add_argument("--threshold", type=float, default=_DEFAULT_THRESHOLD,
                        help=f"Single R² recovery threshold used at EVERY sigma (default: {_DEFAULT_THRESHOLD}).")
    parser.add_argument("--exact-threshold", type=float, default=_EXACT_THRESHOLD, dest="exact_threshold",
                        help=f"Strict 'exact recovery' threshold, always reported (default: {_EXACT_THRESHOLD}).")
    parser.add_argument("--legacy-thresholds", action="store_true", dest="legacy_thresholds",
                        help="Use the old per-sigma threshold ladder (reproduction only).")
    parser.add_argument("--seed", type=int, default=_seed_from_env(),
                        help="Run seed; exported as PYSR_SEED/EXPERIMENT_SEED/NN_SEED (default: env or 42).")
    parser.add_argument("--threshold-noisy",     type=float, default=0.950,  dest="threshold_noisy",
                        help="DEPRECATED: only used with --legacy-thresholds.")
    parser.add_argument("--threshold-noiseless", type=float, default=0.999999, dest="threshold_noiseless",
                        help="DEPRECATED: only used with --legacy-thresholds.")
    parser.add_argument(
        "--threshold-per-sigma", nargs="+", default=[], dest="threshold_per_sigma",
        metavar="SIGMA:VALUE",
        help=(
            "Per-sigma threshold overrides. "
            "Format: sigma:value  e.g.  0.005:0.999  0.01:0.998  0.10:0.990. "
            "Overrides --threshold for that sigma only (default: none, single policy)."
        ),
    )
    parser.add_argument("--samples",             type=int,   default=200)
    parser.add_argument("--nn-seeds",            type=int,   default=3,   dest="nn_seeds")
    parser.add_argument("--method-timeout",      type=int,   default=900, dest="method_timeout")
    parser.add_argument("--pysr-timeout",        type=int,   default=1100,dest="pysr_timeout")
    parser.add_argument("--skip-pysr",           action="store_true", dest="skip_pysr")
    parser.add_argument("--test",                type=str,   default=None)
    parser.add_argument("--equations",           type=int,   nargs="+", metavar="N", default=None)
    parser.add_argument("--domain",              type=str,   default="all_domains")
    parser.add_argument("--series",              choices=["I","II","III","crossover"], default=None)
    parser.add_argument("--benchmark",           choices=["feynman","srbench","both"], default="feynman")
    parser.add_argument("--verbose",             action="store_true")
    parser.add_argument("--quiet",               action="store_true")
    parser.add_argument("--no-llm-cache",        action="store_true", dest="no_llm_cache")
    parser.add_argument("--fail-fast",           action="store_true", dest="fail_fast")
    parser.add_argument("--log",                 type=str,   default=None, metavar="FILE")
    parser.add_argument("--runner",              type=str,   default=None)

    args = parser.parse_args()

    global _SEED_TAG
    _SEED_TAG = f"_seed{args.seed}"
    random.seed(args.seed)
    np.random.seed(args.seed)

    # ── CI per-task noise injection ───────────────────────────────────────────
    # The CI suppB dispatch sets NOISE_LEVEL (the numeric noise-level string
    # extracted from the task ID "noise{level}__{domain}") before launching
    # this script once per noise level.  When present and args.noise_levels
    # was not overridden on the CLI, restrict the sweep to exactly that one
    # sigma so this subprocess does not re-run all noise levels.
    # Units: CI passes values matching the dispatch noise_levels input
    # (e.g. "0.0", "0.5", "1.0", "5.0", "10.0"); values > 1 are treated as
    # percentages and divided by 100 to get fractions.
    _ci_noise_env = os.environ.get("NOISE_LEVEL", "").strip()
    if _ci_noise_env:
        try:
            _raw = float(_ci_noise_env)
            # NOISE_LEVEL is always in PERCENT units (e.g. "0.5" = 0.5%, "1.0" = 1%).
            # Always divide by 100 to get the fraction used internally.
            # The previous '>1' guard was wrong: it passed NOISE_LEVEL="0.5" as
            # sigma=0.5 (50%) and NOISE_LEVEL="1.0" as sigma=1.0 (100%),
            # which are 100x too large and caused those sigma runs to produce
            # near-zero R² across all equations.
            _ci_sigma = _raw / 100.0
            if args.noise_levels == _DEFAULT_NOISE_LEVELS:  # not overridden on CLI
                args.noise_levels = [_ci_sigma]
                print(f"  [CI] NOISE_LEVEL={_ci_noise_env!r}% → sigma={_ci_sigma:.4f} (single-level run)")
        except ValueError:
            print(f"  WARNING: could not parse NOISE_LEVEL={_ci_noise_env!r} — using CLI default")

    if args.log:
        log_path = Path(args.log)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        _log_fh    = open(log_path, "a", buffering=1)
        sys.stdout = _TeeLogger(sys.stdout, _log_fh)
        sys.stderr = _TeeLogger(sys.stderr, _log_fh)
        print(f"  Logging to: {log_path}  (append mode)")

    runner_path = Path(args.runner) if args.runner else _RUNNER
    if not runner_path.exists():
        print(f"ERROR: Cannot find runner: {runner_path}\n"
              f"       Pass --runner /path/to/run_comparative_suite_benchmark_v2.py")
        sys.exit(1)

    # Parse --existing-results tokens
    existing_map: dict[float, Path] = {}
    for token in args.existing_results:
        try:
            sigma_s, path_s = token.split(":", 1)
            sigma = float(sigma_s)
            p     = Path(path_s)
            if not p.exists():
                print(f"  WARNING: --existing-results file not found for sigma={sigma}: {p}")
            else:
                existing_map[sigma] = p
                print(f"  Merging existing result  sigma={sigma*100:.4g}%  -> {p.name}")
        except ValueError:
            print(f"  WARNING: Cannot parse '{token}'  (expected sigma:path)")

    noise_levels   = sorted(set(args.noise_levels))
    all_sigmas     = sorted(set(noise_levels) | set(existing_map.keys()))
    sigmas_to_run  = [s for s in noise_levels if s not in existing_map]

    print(f"\n{'='*80}")
    print("  NOISE SWEEP BENCHMARK RUNNER".center(80))
    print(f"{'='*80}")
    print(f"  Runner          : {runner_path}")
    print(f"  Results dir     : {_RESULTS_DIR}")
    print(f"  Sigma to RUN    : {[f'{s*100:.4g}%' for s in sigmas_to_run]}")
    if existing_map:
        print(f"  Sigma MERGED    : {[f'{s*100:.4g}%' for s in sorted(existing_map)]}")
    print(f"  Methods         : {args.methods}  (3=EnhancedHybridDeFi, 4=HybridLLMNN)")
    print(f"  Samples         : {args.samples}")
    print(f"  Seed            : {args.seed}  (PYSR/EXPERIMENT; NN={2024 + (args.seed - 42)})")
    print(f"  Threshold       : {'legacy per-sigma' if args.legacy_thresholds else args.threshold}  (exact: {args.exact_threshold})")
    print(f"  NN seeds        : {args.nn_seeds}")
    print(f"  Method timeout  : {args.method_timeout}s")
    print(f"  PySR timeout    : {args.pysr_timeout}s")
    print(f"  Fail-fast       : {'ON' if args.fail_fast else 'OFF'}")
    if args.log:
        print(f"  Log             : {args.log}")
    print(f"{'='*80}\n")

    ts            = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_paths: dict[float, Path | None] = dict(existing_map)
    sweep_start   = time.time()

    for i, sigma in enumerate(sigmas_to_run, 1):
        print(f"\n  [{i}/{len(sigmas_to_run)}]  sigma = {sigma*100:.4g}%")
        result_paths[sigma] = _run_noise_level(sigma, args, runner_path)

    elapsed_total = time.time() - sweep_start
    print(f"\n  Total sweep time: {elapsed_total/60:.1f} min\n")

    n_available = sum(1 for v in result_paths.values() if v is not None)
    if n_available == 0:
        print("ERROR: No result JSONs available -- cannot build report.")
        sys.exit(1)

    missing = [f"sigma={s*100:.4g}%" for s in all_sigmas if result_paths.get(s) is None]
    if missing:
        print(f"  WARNING: Missing results for {missing} -- proceeding with {n_available} available.\n")

    print(f"\n{'='*80}")
    print("  GENERATING NOISE SWEEP REPORT".center(80))
    print(f"{'='*80}")

    agg = _aggregate_results(
        all_sigmas, result_paths,
        threshold_fn=lambda sg: _resolve_threshold(sg, args),
        exact_threshold=args.exact_threshold,
        noise_n_test_hint=max(int(args.samples * 0.2), 20),
    )
    agg["seed"] = args.seed
    agg["threshold_policy"] = "legacy_per_sigma" if args.legacy_thresholds else f"fixed_{args.threshold}"
    _print_noise_sweep_table(agg)
    agg["n_samples"] = args.samples   # FIX: record n so table captions need no hard-coded n=200
    _save_sweep_json(agg, ts)
    _save_sweep_csv(agg, ts)

    print("\nNoise sweep complete.\n")


if __name__ == "__main__":
    main()
