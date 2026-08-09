#!/usr/bin/env bash
#
# run_issue2b_experiment.sh
# =========================
# Closes (or re-opens) Item 2b: does the FIX-ISSUE2-UNSEEDED-NN patch make
# HSL/M4 and EHD/M3 deterministic across repeated, otherwise-identical
# noiseless runs?
#
# Two phases, run in order, second one gated on the first:
#
#   PHASE A (fast, no PySR/Julia):
#     3 independent runs with --skip-pysr, since Item 2b only concerns
#     HSL/M4 and EHD/M3, neither of which uses PySR/Julia. This isolates
#     the NN-seeding determinism question cheaply -- no 60-90s Julia
#     startup x 30 equations x 3 runs.
#
#   PHASE B (slow, full stack -- only runs if Phase A closes cleanly):
#     1 full run, all 6 methods, to regenerate Table 4 / tab:r2_noise /
#     tab:rr_noise from real, patched-code output. Skipped entirely if
#     Phase A finds any non-determinism, so you don't burn hours of PySR
#     time chasing a bug that Phase A already caught for free.
#
# Both phases use --no-llm-cache: without it, repeated runs replay a
# cached LLM formula at R^2=1.0 in 0.0s regardless of what the NN-seeding
# fix does, which would report "deterministic" for the wrong reason (this
# is documented in the harness's own --no-llm-cache help text as "the
# root cause of the 100% recovery artefact").
#
# Usage
# -----
#   ./run_issue2b_experiment.sh hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py
#
# Optional environment overrides:
#   RUNS_DIR      Where run1/run2/run3/full_run get created (default: ./issue2b_experiment)
#   N_RUNS        Number of Phase A runs (default: 3, minimum 2)
#   CHECK_SCRIPT  Path to check_issue2b_reproducibility.py (default: alongside this script)
#   PYTHON        Python interpreter (default: python3)
#   SKIP_PHASE_B  Set to 1 to stop after Phase A regardless of result
#   TOL           Allowed |r2_a - r2_b| before check_issue2b_reproducibility.py flags
#                 a mismatch (default: 0.0 = exact bit-match). Only use a non-zero
#                 value deliberately, e.g. "1e-5" -- see the DETERMINISM PINNING
#                 note below for why this should be a last resort, not a first one.
#
# --------------------------------------------------------------------------
# DETERMINISM PINNING
# --------------------------------------------------------------------------
# The NN-seeding patch (hash() -> hashlib.sha256()) fixes seed derivation,
# but PyTorch is not bit-deterministic by default even with a fixed seed:
# reduction order in matmul/conv ops can vary run-to-run depending on BLAS
# thread scheduling and algorithm selection, producing tiny (~1e-6) R^2
# spread that has nothing to do with the seeding bug. This was observed on
# a live CI run (Item 2b workflow_dispatch, run 31252014219): EHD/M3 was
# bit-identical across 3 runs, HSL/M4 was bit-identical on 29/30 equations
# but showed a 7.6e-07 R^2 spread on exactly one (Snell's Law: n1*sin(θ1)
# = n2*sin(θ2)) -- a pass/fail-neutral spread consistent with reduction-order
# noise, not a seeding failure.
#
# The env vars below pin every determinism knob that's controllable from
# OUTSIDE the harness (i.e. without editing run_comparative_suite_benchmark_v2.py
# itself). They are exported unconditionally, before either phase runs, so
# both Phase A and Phase B benefit. If a harness code change is later made
# to call torch.use_deterministic_algorithms(True) internally,
# CUBLAS_WORKSPACE_CONFIG must already be set in the environment before the
# Python process starts (PyTorch reads it at CUDA init) -- these exports
# stay correct either way.
#
# Exit codes: 0 = both phases completed, Item 2b closed, Table 4 data ready.
#             1 = Phase A found non-determinism; Phase B was not attempted.
#             2 = bad arguments / preflight failure.
#             3 = a benchmark run itself failed (non-zero exit).

set -euo pipefail

# ── Args / config ────────────────────────────────────────────────────────
HARNESS_PATH="${1:-}"
if [[ -z "$HARNESS_PATH" ]]; then
    echo "Usage: $0 /path/to/run_comparative_suite_benchmark_v2.py" >&2
    exit 2
fi
if [[ ! -f "$HARNESS_PATH" ]]; then
    echo "ERROR: harness file not found: $HARNESS_PATH" >&2
    exit 2
fi
HARNESS_PATH="$(cd "$(dirname "$HARNESS_PATH")" && pwd)/$(basename "$HARNESS_PATH")"
HARNESS_DIR="$(dirname "$HARNESS_PATH")"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNS_DIR="${RUNS_DIR:-$SCRIPT_DIR/issue2b_experiment}"
N_RUNS="${N_RUNS:-3}"
CHECK_SCRIPT="${CHECK_SCRIPT:-$SCRIPT_DIR/check_issue2b_reproducibility.py}"
PYTHON="${PYTHON:-python3}"
SKIP_PHASE_B="${SKIP_PHASE_B:-0}"
TOL="${TOL:-0.0}"

if [[ "$N_RUNS" -lt 2 ]]; then
    echo "ERROR: N_RUNS must be >= 2 (need at least 2 runs to compare)." >&2
    exit 2
fi
if [[ ! -f "$CHECK_SCRIPT" ]]; then
    echo "ERROR: check_issue2b_reproducibility.py not found at $CHECK_SCRIPT" >&2
    echo "       Set CHECK_SCRIPT=/path/to/it or place it next to this script." >&2
    exit 2
fi

mkdir -p "$RUNS_DIR"
LOG="$RUNS_DIR/experiment.log"
echo "=== Item 2b experiment started $(date -u +%FT%TZ) ===" | tee -a "$LOG"
echo "Harness:  $HARNESS_PATH" | tee -a "$LOG"
echo "Runs dir: $RUNS_DIR" | tee -a "$LOG"
echo "N_RUNS:   $N_RUNS (Phase A)" | tee -a "$LOG"

# ── Determinism pinning ─────────────────────────────────────────────────
# See "DETERMINISM PINNING" note above the args block. Exported before
# either phase runs, so both Phase A and Phase B benefit.
export CUBLAS_WORKSPACE_CONFIG=":4096:8"   # required by cuBLAS for deterministic GEMM
export PYTHONHASHSEED=0                     # belt-and-suspenders alongside the sha256 patch
export OMP_NUM_THREADS=1                    # fixes reduction order in NumPy/torch CPU ops
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export TORCH_DETERMINISTIC=1                # advisory; harness must still call
                                             # torch.use_deterministic_algorithms(True)
                                             # for CUDA algorithm selection to honor this

# EnhancedHybridSystemDeFi (M3) delegates to PureLLMBaseline first, then trains
# a residual-correction MLP on top of the LLM's output. The Anthropic API is
# not guaranteed bit-exact at temperature=0 (server-side batching/kernel
# effects), so identical prompts across the three separate Phase A
# subprocesses can return slightly different formula text -- which is what
# produced the 2.38e-10 R^2 spread on "Logistic Growth" that keeps Item 2b
# open. HYPATIAX_LLM_FREEZE_CACHE makes generate_llm_formula file-backed: the
# first process to hit a given prompt writes the formula to this file, and
# every subsequent process (same run or a different one) reads it back
# instead of re-querying the API, so all three Phase A runs train their
# residual MLP on byte-identical LLM input. Must be the SAME path across all
# three Phase A invocations for this to close the gap -- a per-run path would
# just recreate the original problem.
export HYPATIAX_LLM_FREEZE_CACHE="$RUNS_DIR/llm_freeze_cache.json"
rm -f "$HYPATIAX_LLM_FREEZE_CACHE"          # start each experiment from a clean cache so
                                             # stale formulas from a prior code version
                                             # can't mask a real regression
echo "Determinism pinning: CUBLAS_WORKSPACE_CONFIG=$CUBLAS_WORKSPACE_CONFIG, OMP/MKL/OPENBLAS_NUM_THREADS=1, PYTHONHASHSEED=0" | tee -a "$LOG"
echo "LLM freeze cache:    HYPATIAX_LLM_FREEZE_CACHE=$HYPATIAX_LLM_FREEZE_CACHE (fresh, cleared)" | tee -a "$LOG"
echo "Comparator tolerance: TOL=$TOL (0.0 = exact bit-match)" | tee -a "$LOG"

# Shared flags for the 30-equation / 11-domain exp2 protocol, matching the
# published reproduction command in supp_benchmark_report.tex plus the two
# corrections found by reading the actual argparse block: --protocol
# all_domains (the default 'benchmark' protocol does NOT produce the exp2
# set) and --no-llm-cache (required, see header comment above).
COMMON_FLAGS=(
    --protocol all_domains
    --noiseless
    --threshold 0.9999
    --nn-seeds 3
    --samples 200
    --method-timeout 900
    --pysr-timeout 1100
    --no-llm-cache
    --clear-checkpoint
)

# ── Preflight: confirm the patch is actually present before spending any
#    compute on runs that would just reproduce garbage. ─────────────────
echo "" | tee -a "$LOG"
echo "--- Preflight: patch check ---" | tee -a "$LOG"
if ! "$PYTHON" "$CHECK_SCRIPT" --check-patch "$HARNESS_PATH" | tee -a "$LOG"; then
    echo "" | tee -a "$LOG"
    echo "ABORT: patch check failed. Fix the harness before running the experiment." | tee -a "$LOG"
    exit 2
fi

# ── Phase A: fast, --skip-pysr, N_RUNS independent passes ──────────────
echo "" | tee -a "$LOG"
echo "=== PHASE A: $N_RUNS runs, --skip-pysr (HSL/M4 + EHD/M3 only need NN, no PySR/Julia) ===" | tee -a "$LOG"

PHASE_A_DIRS=()
for i in $(seq 1 "$N_RUNS"); do
    run_dir="$RUNS_DIR/phaseA_run${i}"
    mkdir -p "$run_dir"
    PHASE_A_DIRS+=("$run_dir")
    echo "" | tee -a "$LOG"
    echo "--- Phase A, run $i/$N_RUNS -> $run_dir ---" | tee -a "$LOG"
    t0=$(date +%s)
    (
        cd "$HARNESS_DIR"
        "$PYTHON" "$(basename "$HARNESS_PATH")" \
            "${COMMON_FLAGS[@]}" \
            --skip-pysr \
            --checkpoint-name "issue2b_phaseA_run${i}" \
            --output-dir "$run_dir"
    ) 2>&1 | tee -a "$LOG"
    rc=${PIPESTATUS[0]}
    t1=$(date +%s)
    echo "run $i finished in $((t1 - t0))s, exit code $rc" | tee -a "$LOG"
    if [[ "$rc" -ne 0 ]]; then
        echo "ABORT: Phase A run $i failed (exit $rc). See $LOG." | tee -a "$LOG"
        exit 3
    fi
done

# ── Compare Phase A runs ────────────────────────────────────────────────
echo "" | tee -a "$LOG"
echo "=== PHASE A: comparing ${#PHASE_A_DIRS[@]} runs ===" | tee -a "$LOG"
if "$PYTHON" "$CHECK_SCRIPT" "${PHASE_A_DIRS[@]}" --tol "$TOL" | tee -a "$LOG"; then
    phase_a_rc=0
else
    phase_a_rc=$?
fi

if [[ "$phase_a_rc" -ne 0 ]]; then
    echo "" | tee -a "$LOG"
    echo "RESULT: Item 2b STILL OPEN after Phase A. Stopping before Phase B" | tee -a "$LOG"
    echo "        (no point burning PySR/Julia time on a fix that doesn't hold)." | tee -a "$LOG"
    exit 1
fi

echo "" | tee -a "$LOG"
echo "Phase A: HSL/M4 and EHD/M3 deterministic across $N_RUNS runs." | tee -a "$LOG"

if [[ "$SKIP_PHASE_B" == "1" ]]; then
    echo "SKIP_PHASE_B=1 set — stopping after Phase A as requested." | tee -a "$LOG"
    exit 0
fi

# ── Phase B: one full run, all 6 methods, to regenerate paper tables ───
echo "" | tee -a "$LOG"
echo "=== PHASE B: 1 full run, all methods (incl. PySR/Julia), for Table 4 regeneration ===" | tee -a "$LOG"
full_dir="$RUNS_DIR/phaseB_full"
mkdir -p "$full_dir"
t0=$(date +%s)
(
    cd "$HARNESS_DIR"
    "$PYTHON" "$(basename "$HARNESS_PATH")" \
        "${COMMON_FLAGS[@]}" \
        --checkpoint-name "issue2b_phaseB_full" \
        --output-dir "$full_dir"
) 2>&1 | tee -a "$LOG"
rc=${PIPESTATUS[0]}
t1=$(date +%s)
echo "Phase B run finished in $((t1 - t0))s, exit code $rc" | tee -a "$LOG"
if [[ "$rc" -ne 0 ]]; then
    echo "ABORT: Phase B run failed (exit $rc). See $LOG." | tee -a "$LOG"
    exit 3
fi

echo "" | tee -a "$LOG"
echo "=== Table 4 candidate summary (from Phase B full run) ===" | tee -a "$LOG"
"$PYTHON" "$CHECK_SCRIPT" "$full_dir" "$full_dir" --tol "$TOL" --emit-table4 | tee -a "$LOG"
# (passing full_dir twice: the check script wants >=2 runs to compare; with
#  a single run this trivially reports "deterministic vs itself" and still
#  emits the --emit-table4 summary, which is what we actually want here.)

echo "" | tee -a "$LOG"
echo "=== DONE. $(date -u +%FT%TZ) ===" | tee -a "$LOG"
echo "Phase A runs:  ${PHASE_A_DIRS[*]}" | tee -a "$LOG"
echo "Phase B run:   $full_dir" | tee -a "$LOG"
echo "Full log:      $LOG" | tee -a "$LOG"
echo "" | tee -a "$LOG"
echo "Item 2b CLOSED. Table 4 / tab:r2_noise / tab:rr_noise can be regenerated" | tee -a "$LOG"
echo "from $full_dir's protocol_core_noiseless_*.json files." | tee -a "$LOG"
exit 0
