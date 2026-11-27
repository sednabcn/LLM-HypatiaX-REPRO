#!/usr/bin/env bash
set -euo pipefail

: "\${REPO_ROOT:?REPO_ROOT must be set by run_all.sh}"
: "\${RESULTS_DIR:?RESULTS_DIR must be set by run_all.sh}"
EXPERIMENTS_DIR="\${EXPERIMENTS_DIR:-\${REPO_ROOT}/hypatiax/experiments/benchmarks}"
OUTPUT_DIR="\${RESULTS_DIR}/comparison_results/noise-noiseless/15_pca"
SCRATCH_ROOT="\${RUNNER_TEMP:-/tmp}/exp1b_pca_seed_workers"
VALIDATOR="\${REPO_ROOT}/scripts/ci/exp1b_pca_seed_outputs.py"
BENCHMARK="\${EXPERIMENTS_DIR}/hypatiax_defi_benchmark_pca.py"
SEEDS=(42 99 123 777 2024)

mkdir -p "\${OUTPUT_DIR}"
rm -f "\${OUTPUT_DIR}/hypatiax_defi_benchmark_pca_results_seed42.json" \
      "\${OUTPUT_DIR}/hypatiax_defi_benchmark_pca_results_seed99.json" \
      "\${OUTPUT_DIR}/hypatiax_defi_benchmark_pca_results_seed123.json" \
      "\${OUTPUT_DIR}/hypatiax_defi_benchmark_pca_results_seed777.json" \
      "\${OUTPUT_DIR}/hypatiax_defi_benchmark_pca_results_seed2024.json" \
      "\${OUTPUT_DIR}/exp1b_pca_summary.json" \
      "\${OUTPUT_DIR}/split_protocol_disclosure.json"
rm -rf "\${SCRATCH_ROOT}"
mkdir -p "\${SCRATCH_ROOT}"
: > "\${RESULTS_DIR}/exp1b_pca_run.log"

for seed in "\${SEEDS[@]}"; do
  scratch="\${SCRATCH_ROOT}/seed\${seed}"
  mkdir -p "\${scratch}"
  echo "[exp1b_pca] Running all 74 PCA cases for seed \${seed}"
  DEFI_SEEDS="\${seed}" \
  PYSR_SEED="\${seed}" \
  EXPERIMENT_SEED="\${seed}" \
  NN_SEED="\${seed}" \
  HYPATIAX_ENGINE_SEED="\${seed}" \
  TASK_IDS="" SHARD_IDS="" DOMAIN_FILTER="" DEFI_TASK_FILTER="" \
  ONE_EQUATION="" CASE_RANGE_START="" CASE_RANGE_END="" \
    python3 "\${BENCHMARK}" --output-dir "\${scratch}" --force-fresh \
      2>&1 | tee -a "\${RESULTS_DIR}/exp1b_pca_run.log"

  if [[ "\${seed}" == "42" ]]; then
    source_file="\${scratch}/hypatiax_defi_benchmark_pca_results.json"
  else
    source_file="\${scratch}/hypatiax_defi_benchmark_pca_results_seed\${seed}.json"
  fi
  python3 "\${VALIDATOR}" validate \
    --source "\${source_file}" \
    --destination "\${OUTPUT_DIR}/hypatiax_defi_benchmark_pca_results_seed\${seed}.json" \
    --seed "\${seed}"
done

python3 "\${VALIDATOR}" finalize --directory "\${OUTPUT_DIR}"

for seed in "\${SEEDS[@]}"; do
  test -s "\${OUTPUT_DIR}/hypatiax_defi_benchmark_pca_results_seed\${seed}.json"
done
test -s "\${OUTPUT_DIR}/exp1b_pca_summary.json"
test -s "\${OUTPUT_DIR}/split_protocol_disclosure.json"
echo "[exp1b_pca] Verified isolated results for all five seeds."
find "\${OUTPUT_DIR}" -maxdepth 1 -type f -name 'hypatiax_defi_benchmark_pca_results_seed*.json' -print | sort
