#!/usr/bin/env bash
set -euo pipefail

: "\${REPO_ROOT:?REPO_ROOT must be set by the workflow}"
: "\${RESULTS_DIR:?RESULTS_DIR must be set by the workflow}"
: "\${SEED:?Pass exactly one SEED (42, 99, 123, 777, or 2024)}"
EXPERIMENTS_DIR="\${EXPERIMENTS_DIR:-\${REPO_ROOT}/hypatiax/experiments/benchmarks}"
OUTPUT_DIR="\${RESULTS_DIR}/comparison_results/noise-noiseless/noiseless/defi_random_4060"
SCRATCH_ROOT="\${RUNNER_TEMP:-/tmp}/exp1_4060_seed\${SEED}"
BENCHMARK="\${EXPERIMENTS_DIR}/hypatiax_defi_benchmark_v3c_4060.py"
VALIDATOR="\${REPO_ROOT}/scripts/ci/exp1_4060_seed_outputs.py"

case "$SEED" in 42|99|123|777|2024) ;; *) echo "::error::Unsupported seed '$SEED'"; exit 2;; esac
mkdir -p "$OUTPUT_DIR"
rm -rf "$SCRATCH_ROOT"
mkdir -p "$SCRATCH_ROOT"
: > "$OUTPUT_DIR/exp1_4060_seed\${SEED}_run.log"

echo "[exp1_4060_seeds] Running all 74 equations; random 40/60; seed=$SEED"
DEFI_SEEDS="$SEED" PYSR_SEED="$SEED" EXPERIMENT_SEED="$SEED" NN_SEED="$SEED" \
  HYPATIAX_ENGINE_SEED="$SEED" TASK_IDS="" SHARD_IDS="" DOMAIN_FILTER="" DEFI_TASK_FILTER="" \
  ONE_EQUATION="" CASE_RANGE_START="" CASE_RANGE_END="" \
  python3 "$BENCHMARK" --output-dir "$SCRATCH_ROOT" 2>&1 | tee "$OUTPUT_DIR/exp1_4060_seed\${SEED}_run.log"

if [[ "$SEED" == "42" ]]; then source_file="$SCRATCH_ROOT/hypatiax_defi_benchmark_v3c_4060_results.json"; suffix=""
else source_file="$SCRATCH_ROOT/hypatiax_defi_benchmark_v3c_4060_results_seed\${SEED}.json"; suffix="_seed\${SEED}"; fi
python3 "$VALIDATOR" validate --source "$source_file" \
  --destination "$OUTPUT_DIR/hypatiax_defi_benchmark_v3c_4060_results\${suffix}.json" --seed "$SEED"
