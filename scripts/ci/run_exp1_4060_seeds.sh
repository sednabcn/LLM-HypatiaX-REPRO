#!/usr/bin/env bash
set -euo pipefail

: "${REPO_ROOT:?REPO_ROOT must be set by run_all.sh}"
: "${RESULTS_DIR:?RESULTS_DIR must be set by run_all.sh}"
EXPERIMENTS_DIR="${EXPERIMENTS_DIR:-${REPO_ROOT}/hypatiax/experiments/benchmarks}"
OUTPUT_DIR="${RESULTS_DIR}/comparison_results/noise-noiseless/noiseless/defi_random_4060"
SCRATCH_ROOT="${RUNNER_TEMP:-/tmp}/exp1_4060_seeds_workers"
BENCHMARK="${EXPERIMENTS_DIR}/hypatiax_defi_benchmark_v3c_4060.py"
VALIDATOR="${REPO_ROOT}/scripts/ci/exp1_4060_seed_outputs.py"
SEEDS=(42 99 123 777 2024)

mkdir -p "${OUTPUT_DIR}"
rm -f "${OUTPUT_DIR}"/hypatiax_defi_benchmark_v3c_4060_results*.json \
      "${OUTPUT_DIR}/exp1_4060_seeds_summary.json" \
      "${OUTPUT_DIR}/split_protocol_disclosure.json"
rm -rf "${SCRATCH_ROOT}"
mkdir -p "${SCRATCH_ROOT}"
: > "${RESULTS_DIR}/exp1_4060_seeds_run.log"

for seed in "${SEEDS[@]}"; do
  scratch="${SCRATCH_ROOT}/seed${seed}"
  mkdir -p "${scratch}"
  echo "[exp1_4060_seeds] Running all 74 cases with random 40/60 split; seed=${seed}"
  DEFI_SEEDS="${seed}" PYSR_SEED="${seed}" EXPERIMENT_SEED="${seed}" NN_SEED="${seed}" \
    HYPATIAX_ENGINE_SEED="${seed}" \
    TASK_IDS="" SHARD_IDS="" DOMAIN_FILTER="" DEFI_TASK_FILTER="" \
    ONE_EQUATION="" CASE_RANGE_START="" CASE_RANGE_END="" \
      python3 "${BENCHMARK}" --output-dir "${scratch}" \
        2>&1 | tee -a "${RESULTS_DIR}/exp1_4060_seeds_run.log"

  if [[ "${seed}" == "42" ]]; then
    source_file="${scratch}/hypatiax_defi_benchmark_v3c_4060_results.json"
  else
    source_file="${scratch}/hypatiax_defi_benchmark_v3c_4060_results_seed${seed}.json"
  fi
  python3 "${VALIDATOR}" validate --source "${source_file}" \
    --destination "${OUTPUT_DIR}/$(basename "${source_file}")" --seed "${seed}"
done

python3 "${VALIDATOR}" finalize --directory "${OUTPUT_DIR}"
echo "[exp1_4060_seeds] Verified five isolated random 40/60 seed outputs."
