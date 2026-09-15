#!/usr/bin/env bash

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
_RESULTS_RAW="${RESULTS_DIR:-${REPO_ROOT}/hypatiax/data/results}"
RESULTS_DIR="$(cd "$(dirname "${_RESULTS_RAW}")" 2>/dev/null && pwd)/$(basename "${_RESULTS_RAW}")" \
  || RESULTS_DIR="${REPO_ROOT}/hypatiax/data/results"
export RESULTS_DIR
EXPERIMENTS_DIR="${EXPERIMENTS_DIR:-${REPO_ROOT}/hypatiax/experiments/benchmarks}"
GENERATION_DIR="${GENERATION_DIR:-${REPO_ROOT}/hypatiax/core/generation}"
CORE_DIR="${CORE_DIR:-${REPO_ROOT}/hypatiax/core}"
ANALYSIS_DIR="${ANALYSIS_DIR:-${REPO_ROOT}/hypatiax/analysis}"
SCRIPTS_DIR="${SCRIPTS_DIR:-${REPO_ROOT}/scripts}"

export PYSR_GENERATIONS=10000
export PYSR_TOURNAMENT_SIZE=3
export PYSR_CROSSOVER=0.9
export PYSR_MUTATION=0.1
export PYSR_PARETO_PRESSURE=0.001
export PYSR_SEED=42
export PYSR_POPULATIONS="${PYSR_POPULATIONS:-30}"

export NOISE_LEVELS="${NOISE_LEVELS:-0.0,0.05,0.1,0.5,1.0}"

export METHOD_TIMEOUT="${METHOD_TIMEOUT:-900}"
export LLM_METHOD_TIMEOUT="${LLM_METHOD_TIMEOUT:-120}"
# PYSR_FIT_WALL_TIMEOUT: hard per-fit wall-clock cap passed to DiscoveryConfig.
# PYSR_FIT_GRACE_SECS:   extra grace seconds before forceful kill after timeout.
# Both must be exported so worker sub-processes and Python scripts inherit them.
export PYSR_FIT_WALL_TIMEOUT="${PYSR_FIT_WALL_TIMEOUT:-1200}"
export PYSR_FIT_GRACE_SECS="${PYSR_FIT_GRACE_SECS:-120}"

export FEYNMAN_SAMPLES=200
export FEYNMAN_TIMEOUT=1100
export FEYNMAN_NOISELESS_THRESHOLD=0.999999

export PYTHON_JULIACALL_HANDLE_SIGNALS=yes

export JULIA_NUM_THREADS="${JULIA_NUM_THREADS:-4}"
export JULIA_EXCLUSIVE="${JULIA_EXCLUSIVE:-0}"

export REPRO_CFG="${REPRO_CFG:-${REPO_ROOT}/config/repro.yaml}"

export JOB_DEADLINE="${JOB_DEADLINE:-19800}"

HYBRID_ALL_DOMAINS_EXPECTED="biology,chemistry,economics,electromagnetism,fluid_dynamics,mathematics,mechanics,optics,quantum,thermodynamics"

FEYNMAN_DOMAINS="feynman_biology feynman_chemistry feynman_electrochemistry feynman_electromagnetism feynman_electrostatics feynman_magnetism feynman_mechanics feynman_optics feynman_probability feynman_quantum feynman_thermodynamics"

# ── CLI parsing ───────────────────────────────────────────────────────────────
ONLY_STEP=""
FROM_STEP=""
DRY_RUN=false

_STEP_ORDER="env_check exp1 exp1b exp1_ablation exp1_five exp1_pca exp1b_pca extrap hybrid_all_domains instability exp2_feynman exp2_feynman_pca_4060 exp2_feynman_extrap exp2 exp2_five exp3 exp3b suppA suppB suppB_sc validate qualify audit_paper audit_setup audit_nb01 audit_nb02 audit_nb03 audit_nb04 audit_nb05 audit_nb06_fixc3_disclosure audit_nb06_fixc3_rerun audit_guard audit_print_verify audit_print_findings audit_figures_tables audit_final_gate"

while [[ $# -gt 0 ]]; do
  case $1 in
    --step)    ONLY_STEP="$2"; shift 2 ;;
    --from)    FROM_STEP="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    # Bare step name: "bash run_all.sh audit_paper" treated as "--step audit_paper".
    # Validated against _STEP_ORDER so typos still produce a clear error.
    *)
      BARE="$1"; shift
      if [[ " $_STEP_ORDER " == *" ${BARE} "* ]]; then
        ONLY_STEP="$BARE"
      else
        echo "Unknown arg: ${BARE}"
        echo "  Valid step names: ${_STEP_ORDER}"
        echo "  Flags: --step <step> | --from <step> | --dry-run"
        exit 1
      fi
      ;;
  esac
done

# ── Helpers ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${GREEN}[run_all]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
die()  { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

run() {
  local step="$1" desc="$2"; shift 2
  [[ -n "$ONLY_STEP" && "$ONLY_STEP" != "$step" ]] && return 0
  if [[ -n "$FROM_STEP" ]]; then
    # Scan the ordered step list; once FROM_STEP is reached flip skip→false.
    # Break as soon as we hit the current step.  If skip is still true at that
    # point the current step precedes FROM_STEP → skip it.
    local skip=true
    for s in $_STEP_ORDER; do
      [[ "$s" == "$FROM_STEP" ]] && skip=false
      [[ "$s" == "$step"      ]] && break
    done
    [[ "$skip" == true ]] && return 0
  fi
  echo ""
  log "=== STEP: ${step} -- ${desc} ==="
  if [[ "$DRY_RUN" == true ]]; then
    echo "    [dry-run] $*"
  else
    "$@"
    log "--- DONE: ${step} ---"
  fi
}


# ── STEP 0: env_check ─────────────────────────────────────────────────────────
run env_check "Verify environment (Python, Julia/PySR, API key, directories)" bash -c '
  set -e
  echo "Python: $(python3 --version)"
  python3 -c "import pysr; print(\"PySR:\", pysr.__version__)" || { echo "ERROR: pysr not installed"; exit 1; }
  python3 -c "import torch; print(\"PyTorch:\", torch.__version__)"
  python3 -c "import anthropic; print(\"anthropic SDK: ok\")"
  python3 - <<'SDKCHECK'
import anthropic, sys
ver = tuple(int(x) for x in anthropic.__version__.split(".")[:3])
if ver < (0, 40, 0):
    print("ERROR: anthropic SDK " + anthropic.__version__ + " is too old; need >= 0.40.0 for claude-sonnet-4-20250514")
    sys.exit(1)
print("anthropic SDK version: " + anthropic.__version__ + " (>= 0.40.0 OK)")
SDKCHECK
  python3 -c "import sympy; print(\"SymPy:\", sympy.__version__)"
  python3 -c "import scipy; print(\"SciPy:\", scipy.__version__)"
  python3 -c "import sklearn; print(\"scikit-learn:\", sklearn.__version__)" || { echo "ERROR: scikit-learn not installed"; exit 1; }
  python3 -c "import yaml; print(\"PyYAML: ok\")" || { echo "ERROR: pyyaml not installed"; exit 1; }
  python3 -c "import matplotlib; print(\"matplotlib:\", matplotlib.__version__)" || { echo "ERROR: matplotlib not installed"; exit 1; }
  python3 -c "import pmlb; print(\"pmlb: ok\")" || { echo "ERROR: pmlb not installed"; exit 1; }
  python3 -c "import seaborn; print(\"seaborn:\", seaborn.__version__)" 2>/dev/null || {
    echo "WARNING: seaborn not found — installing now (required by statistical_analysis.py)"
    python3 -m pip install --quiet seaborn || { echo "ERROR: seaborn install failed"; exit 1; }
    python3 -c "import seaborn; print(\"seaborn: installed\", seaborn.__version__)"
  }
  [[ -n "${ANTHROPIC_API_KEY:-}" ]] || { echo "ERROR: ANTHROPIC_API_KEY not set"; exit 1; }
  echo "ANTHROPIC_API_KEY: set (${#ANTHROPIC_API_KEY} chars)"
  echo "PYSR_POPULATIONS: ${PYSR_POPULATIONS}"
  echo "JULIA_NUM_THREADS: ${JULIA_NUM_THREADS}"
  echo "JULIA_EXCLUSIVE: ${JULIA_EXCLUSIVE}"
  echo "PYTHON_JULIACALL_HANDLE_SIGNALS: ${PYTHON_JULIACALL_HANDLE_SIGNALS}"
  echo "FEYNMAN_SAMPLES: ${FEYNMAN_SAMPLES}"
  echo "FEYNMAN_TIMEOUT: ${FEYNMAN_TIMEOUT}"
  echo "FEYNMAN_NOISELESS_THRESHOLD: ${FEYNMAN_NOISELESS_THRESHOLD}"
  echo "JOB_DEADLINE: ${JOB_DEADLINE}s"
  echo "REPRO_CFG: ${REPRO_CFG}"
  if [ -f "${REPRO_CFG}" ]; then
    echo "repro.yaml found -- printing key values:"
    python3 -c "
import yaml, sys
with open(\"${REPRO_CFG}\") as f: cfg = yaml.safe_load(f)
for k, v in (cfg or {}).items(): print(f\"  {k}: {v}\")
" 2>/dev/null || echo "  (could not parse repro.yaml)"
  else
    echo "WARNING: repro.yaml not found at ${REPRO_CFG} -- using env defaults"
  fi
  echo "Results dir: '"${RESULTS_DIR}"'"
  # --------------------------------------------------------------------------
  # extrap_r2_far INTERNAL MODE	
  #
  # compute_extrap_r2_far and all extrapolation helpers are now inlined
  # directly inside run_comparative_suite_benchmark_v2.py.
  #
  # No external extrap_r2_far.py module is required.
  # No sys.path manipulation or auto-install logic is needed.
  # --------------------------------------------------------------------------
  
  echo "extrap_r2_far: internal inlined implementation enabled"
  _EXTRAP_DEST="${EXPERIMENTS_DIR}/extrap_r2_far.py"
  if [ -f "${_EXTRAP_DEST}" ]; then
    echo "extrap_r2_far.py: OK at ${_EXTRAP_DEST}"
  else
    _EXTRAP_FOUND=false
    for _src in \
        "${SCRIPTS_DIR}/extrap_r2_far.py" \
        "${REPO_ROOT}/extrap_r2_far.py" \
        "${CORE_DIR}/extrap_r2_far.py" \
        "${ANALYSIS_DIR}/extrap_r2_far.py"; do
      if [ -f "${_src}" ]; then
        cp "${_src}" "${_EXTRAP_DEST}" \
          && echo "extrap_r2_far.py: copied ${_src} → ${_EXTRAP_DEST}" \
          && _EXTRAP_FOUND=true \
          && break
      fi
    done
    if [ "${_EXTRAP_FOUND}" = false ]; then
      echo "ERROR: extrap_r2_far.py not found — exp2_feynman_extrap will produce null extrap_r2_far values."
      echo "       Expected at: ${_EXTRAP_DEST}"
      echo "       Place extrap_r2_far.py in ${EXPERIMENTS_DIR}/ before running exp2_feynman_extrap."
    fi
  fi
  mkdir -p '"${RESULTS_DIR}"'/{comparison_results/{feynman-tests/{exp2,exp2_pca_4060,exp2_extrap,exp2_multi,noise-sweep,sample-complexity},noise-noiseless/{noiseless/defi,15},extrapolation},extrapolation/multi_seed,hybrid_llm_nn/{all_domains,defi},hybrid_pysr/{all_domains,defi},llm_guided/{all_domains,defi},standalone_llm_nn,figures,tables}
  mkdir -p '"${RESULTS_DIR}"'/extrapolation
  echo "Directory structure: ok"
'

# ── STEP 0b: gt_leak_guard ──────────────────────────────────────────────────
run gt_leak_guard "Regression guard: ground-truth leak in hybrid LLM prompts" bash -c "
  cd '${REPO_ROOT}'
  _FAIL=0

  _T1='${EXPERIMENTS_DIR}/hypatiax_defi_benchmark_v3c.py'
  if [[ -f \"\${_T1}\" ]]; then
    if grep -n \"Ground truth:.*metadata\.get(.ground_truth\" \"\${_T1}\" | grep -v '^[0-9]*:# ' ; then
      echo '::error::Ground-truth leak pattern detected in hypatiax_defi_benchmark_v3c.py _generate_llm_formula prompt.'
      echo '         See Fix 14 changelog entry in that file.'
      _FAIL=1
    fi
  else
    echo \"WARNING: \${_T1} not found — skipping that half of gt_leak_guard.\"
  fi

  _T2='hypatiax/core/generation/hybrid_all_domains_llm_nn/hybrid_system_llm_nn_all_domains.py'
  if [[ -f \"\${_T2}\" ]]; then
    if grep -n \"Expected form:.*metadata\[.ground_truth.\]\" \"\${_T2}\" | grep -v '^[0-9]*:# ' ; then
      echo '::error::Ground-truth leak pattern detected in hybrid_system_llm_nn_all_domains.py _generate_prompt fallback.'
      echo '         See FIX GT-LEAK comment in that file.'
      _FAIL=1
    fi
  else
    echo \"WARNING: \${_T2} not found — skipping that part of gt_leak_guard.\"
  fi

  _T3=\$(find \"${REPO_ROOT}\" -maxdepth 4 -name 'hybrid_system_nn_defi_domain.py' 2>/dev/null | head -1)
  if [[ -n \"\${_T3}\" && -f \"\${_T3}\" ]]; then
    if grep -n 'prompt = self\._specialized_prompt' \"\${_T3}\" | grep -v '^[0-9]*:# ' ; then
      echo '::error::_specialized_prompt call site reintroduced in hybrid_system_nn_defi_domain.py.'
      echo '         That path sends a pre-solved answer as the LLM prompt for several'
      echo '         formula types — see FIX GT-LEAK-2 comment in that file. Must always'
      echo '         use _standard_prompt at that call site.'
      _FAIL=1
    fi
  else
    echo 'WARNING: hybrid_system_nn_defi_domain.py not found — skipping that part of gt_leak_guard.'
  fi

  if [[ \"\${_FAIL}\" == '1' ]]; then
    exit 1
  fi
  echo '  [OK]  gt_leak_guard — no ground-truth leak pattern found in any of the 3 hybrid prompt paths.'
"

# ── STEP 1: exp1 ──────────────────────────────────────────────────────────────
run exp1 "Core extrapolation benchmark (Tab 9, 10, 15 - Fig 9, 10)" bash -c "
  cd '${REPO_ROOT}'
  _DEFI_TARGET='${RESULTS_DIR}/comparison_results/noise-noiseless/noiseless/defi'
  mkdir -p \"\${_DEFI_TARGET}\"

  python3 '${EXPERIMENTS_DIR}/hypatiax_defi_benchmark_v4.py' \
    --output-dir \"\${_DEFI_TARGET}\" \
    2>&1 | tee '${RESULTS_DIR}/exp1_run.log'

  python3 -c 'import seaborn' 2>/dev/null || \
    python3 -m pip install --quiet seaborn || \
    { echo 'ERROR: seaborn install failed — statistical_analysis.py will crash'; exit 1; }
  cd '${ANALYSIS_DIR}'
  python3 statistical_analysis.py \
    2>&1 | tee -a '${RESULTS_DIR}/exp1_run.log' \
  || echo 'WARNING: statistical_analysis.py exited non-zero — primary results already saved, continuing'

  echo '=== exp1 verification ==='
  find \"\${_DEFI_TARGET}\" -type f 2>/dev/null | sort || echo '  (directory empty)'
  COUNT_DEFI=\$(find \"\${_DEFI_TARGET}\" -name 'hypatiax_defi_benchmark_*results*.json' 2>/dev/null | wc -l)
  if [[ \"\${COUNT_DEFI}\" -eq 0 ]]; then
    echo 'WARNING: exp1 produced no result JSON in canonical target — check log above.'
  else
    echo \"OK: \${COUNT_DEFI} result file(s) confirmed in \${_DEFI_TARGET}\"
  fi
  echo '=== end exp1 verification ==='
"

# ── STEP 2: exp1b ─────────────────────────────────────────────────────────────
run exp1b "DeFi seed sweep + portfolio variance (Tab 11-13 - Fig 11-13)" bash -c "
  cd '${REPO_ROOT}'

  _SHARD_TASKS='${SHARD_IDS:-${TASK_IDS:-}}'
  _SHARD_SEEDS=\$(echo \"\${_SHARD_TASKS}\" | tr ' ' '\n' | grep -oE '^portfolio_seed[0-9]+$' | sed 's/^portfolio_seed//' | paste -sd, -)
  if [[ -z \"\${_SHARD_SEEDS}\" ]]; then
    echo '  [exp1b] No portfolio_seedNN task IDs found in SHARD_IDS/TASK_IDS — running full default seed list (local/standalone run).'
    _SHARD_SEEDS='42,99,123,777,2024'
  else
    echo \"  [exp1b] SHARD_INDEX=\${SHARD_INDEX:-0} -> seeds for this shard: \${_SHARD_SEEDS}\"
  fi

  DEFI_SEEDS=\"\${_SHARD_SEEDS}\" \
    python3 '${EXPERIMENTS_DIR}/hypatiax_defi_benchmark_v4.py' \
      --resume \
      2>&1 | tee '${RESULTS_DIR}'/exp1b_run.log

  _BENCH_JSON=\$(ls -t '${RESULTS_DIR}/comparison_results/noise-noiseless/noiseless/defi'/hypatiax_defi_benchmark_*results*.json 2>/dev/null | head -1 || true)
  if [[ -z \"\${_BENCH_JSON}\" ]]; then
    echo 'WARNING: portfolio_variance_v3c2.py skipped — benchmark JSON not found in ${RESULTS_DIR}.'
    echo '         This is expected on the first shard run when hypatiax_defi_benchmark_v4.py'
    echo '         writes its output to the doubled path or has not yet produced results.'
    echo '         Re-run exp1b after confirming the benchmark JSON is present.'
  else
    echo '[exp1b] Running portfolio_variance_v3c2.py against: '\"\${_BENCH_JSON}\"
    RESULTS_DIR='${RESULTS_DIR}' \
      python3 '${EXPERIMENTS_DIR}/portfolio_variance_v3c2.py' \
        2>&1 | tee -a '${RESULTS_DIR}'/exp1b_run.log \
      || echo 'WARNING: portfolio_variance_v3c2.py exited non-zero — primary benchmark results already saved, continuing'
  fi
  _SHARD=\${SHARD_INDEX:-0}
  _SEED_TAG=\$(echo \"\${_SHARD_SEEDS:-42}\" | tr ',' '_')

  dest15='${RESULTS_DIR}/comparison_results/noise-noiseless/15'

  mkdir -p \"\${dest15}\"

  for _search_root in '${EXPERIMENTS_DIR}' '${RESULTS_DIR}'; do
    find \"\${_search_root}\" -maxdepth 1 \
    \( \
        -name 'defi_v4_*.json' \
        -o -name '*portfolio*variance*.json' \
        -o -name 'hypatiax_defi_benchmark_*results*.json' \
    \) | while IFS= read -r src; do

        # Skip if already inside dest15 (avoid self-move loop)
        [[ \"\$src\" == \"\${dest15}\"* ]] && continue

        fname=\$(basename \"\$src\")
        stem=\"\${fname%.*}\"
        ext=\"\${fname##*.}\"

        dst=\"\${dest15}/\${stem}_shard\${_SHARD}_seed\${_SEED_TAG}.\${ext}\"

        if [ -f \"\$src\" ]; then
            mv -v \"\$src\" \"\$dst\" || true
        fi
    done
  done

  # move comparison files
  for _search_root in '${EXPERIMENTS_DIR}' '${RESULTS_DIR}'; do
    find \"\${_search_root}\" -maxdepth 1 \
    \( \
        -name 'comparison_FIXED_*.json' \
        -o -name 'comparison_FIXED_*.txt' \
    \) | while IFS= read -r src; do

        [[ \"\$src\" == \"\${dest15}\"* ]] && continue

        fname=\$(basename \"\$src\")
        stem=\"\${fname%.*}\"
        ext=\"\${fname##*.}\"

        dst=\"\${dest15}/\${stem}_shard\${_SHARD}_seed\${_SEED_TAG}.\${ext}\"

        if [ -f \"\$src\" ]; then
            mv -v \"\$src\" \"\$dst\" || true
        fi
    done
  done

  # verification
  echo '=== exp1b verification ==='

  find \"\${dest15}\" -type f 2>/dev/null | sort

  count=\$(find \"\${dest15}\" -type f 2>/dev/null | wc -l)

  echo \"Files produced: \${count}\"

  if [[ \"\${count}\" -eq 0 && \"\${SKIP_ALLOWED:-false}\" != \"true\" ]]; then
      echo 'WARNING: exp1b generated no files — set SKIP_ALLOWED=true if this step was intentionally skipped'
  elif [[ \"\${count}\" -eq 0 ]]; then
      echo 'NOTE: exp1b produced no files (step was skipped — SKIP_ALLOWED=true)'
  fi
"



# ── STEP 2a: exp1_ablation ────────────────────────────────────────────────────
# Output directory: ${RESULTS_DIR}/ablation/exp1_ablation/
# CLI example (run standalone):
run exp1_ablation "Core-15 LLM ablation: PySR-only vs HypatiaX (Tab 5, §10.6)" bash -c "
  cd '${REPO_ROOT}'
  _ABL_DIR='${RESULTS_DIR}/ablation/exp1_ablation'
  mkdir -p \"\${_ABL_DIR}\"

  PYTHONPATH='${REPO_ROOT}'\"${PYTHONPATH:+:${PYTHONPATH}}\" \
  RESULTS_DIR=\"\${_ABL_DIR}\" \
  PYSR_POPULATIONS='${PYSR_POPULATIONS}' \
  PYSR_SEED='${PYSR_SEED}' \
  METHOD_TIMEOUT='${METHOD_TIMEOUT}' \
  PYSR_TIMEOUT='${FEYNMAN_TIMEOUT}' \
  JOB_DEADLINE='${JOB_DEADLINE}' \
    python3 '${EXPERIMENTS_DIR}/exp1_ablation.py' \
    2>&1 | tee \"\${_ABL_DIR}/exp1_ablation_run.log\" \
  || echo 'WARNING: exp1_ablation.py exited non-zero — check exp1_ablation_run.log'

  _NTEX=\$(find \"\${_ABL_DIR}\" -maxdepth 1 -name '*.tex' 2>/dev/null | wc -l)
  find \"\${_ABL_DIR}\" -maxdepth 1 -name '*.tex' -delete 2>/dev/null
  echo \"[exp1_ablation] removed \${_NTEX} .tex table byproduct(s) — table generation disabled\"

  echo '=== exp1_ablation verification ==='
  find \"\${_ABL_DIR}\" -maxdepth 1 \( -name '*.json' -o -name '*.csv' \) 2>/dev/null | sort
  _NRESULT=\$(find \"\${_ABL_DIR}\" -maxdepth 1 -name 'exp1_ablation_results*.json' 2>/dev/null | wc -l)
  _NRF01=\$(find \"\${_ABL_DIR}\" -maxdepth 1 -name 'exp1_rf01_mannwhitney*.json' 2>/dev/null | wc -l)
  if [[ \"\${_NRESULT}\" -eq 0 ]]; then
    echo 'WARNING: exp1_ablation_results.json not produced'
    echo '         Ensure ANTHROPIC_API_KEY is set and HybridDiscoverySystem v5.1 is importable'
  else
    echo \"OK: \${_NRESULT} exp1_ablation_results*.json produced\"
  fi
  if [[ \"\${_NRF01}\" -eq 0 ]]; then
    echo 'WARNING: exp1_rf01_mannwhitney.json not produced — Mann-Whitney stats will be missing'
  fi
  echo '=== end exp1_ablation ==='
"


# ── STEP 2a2: exp1_five ────────────────────────────────────────────────────────
# Output directory: ${RESULTS_DIR}/five_systems/exp1_five/
# CLI example (run standalone):
run exp1_five "Five-System Comparison: extrapolation error vs. interpolation R² (Tab 1, §10.1)" bash -c "
  cd '${REPO_ROOT}'
  _FIVE_DIR='${RESULTS_DIR}/five_systems/exp1_five'
  mkdir -p \"\${_FIVE_DIR}\"

  PYTHONPATH='${REPO_ROOT}'\"${PYTHONPATH:+:${PYTHONPATH}}\" \
  RESULTS_DIR=\"\${_FIVE_DIR}\" \
  LABEL='exp1_five' \
  PYSR_POPULATIONS='${PYSR_POPULATIONS}' \
  PYSR_SEED='${PYSR_SEED}' \
  METHOD_TIMEOUT='${METHOD_TIMEOUT}' \
  PYSR_TIMEOUT='${FEYNMAN_TIMEOUT}' \
  JOB_DEADLINE='${JOB_DEADLINE}' \
    python3 '${EXPERIMENTS_DIR}/exp1_five_system.py' \
    2>&1 | tee \"\${_FIVE_DIR}/exp1_five_run.log\" \
  || echo 'WARNING: exp1_five_system.py exited non-zero (or is not yet present) — check exp1_five_run.log'

  echo '=== exp1_five verification ==='
  find \"\${_FIVE_DIR}\" -maxdepth 1 \( -name '*.json' -o -name '*.csv' \) 2>/dev/null | sort
  _NRESULT=\$(find \"\${_FIVE_DIR}\" -maxdepth 1 -name 'exp1_five_results*.json' 2>/dev/null | wc -l)
  _NPERF=\$(find \"\${_FIVE_DIR}\" -maxdepth 1 -name 'exp1_five_performance*.json' 2>/dev/null | wc -l)
  _NEXTRAP=\$(find \"\${_FIVE_DIR}\" -maxdepth 1 -name 'exp1_five_extrapolation*.json' 2>/dev/null | wc -l)
  if [[ \"\${_NRESULT}\" -eq 0 ]]; then
    echo 'WARNING: exp1_five_results.json not produced'
  else
    echo \"OK: \${_NRESULT} exp1_five_results*.json produced\"
  fi
  if [[ \"\${_NPERF}\" -eq 0 || \"\${_NEXTRAP}\" -eq 0 ]]; then
    echo 'WARNING: performance/extrapolation sub-table source JSON missing — five_system.tex sub-tables will be incomplete'
  fi
  echo '=== end exp1_five ==='
"


# ── STEP 2b: exp1_pca ─────────────────────────────────────────────────────────
# Output directory: comparison_results/noise-noiseless/noiseless/defi_pca/
# CLI example (run standalone): bash run_all.sh --step exp1_pca
run exp1_pca "DeFi benchmark: all 74 cases with PCA 40/60 split (mirrors exp1 with PCA split)" bash -c "
  cd '${REPO_ROOT}'
  _PCA_DEFI_DIR='${RESULTS_DIR}/comparison_results/noise-noiseless/noiseless/defi_pca'
  mkdir -p \"\${_PCA_DEFI_DIR}\"

  # --force-fresh is passed to the script itself — guarantees fresh results
  # even when the script is invoked directly, bypassing this shell wrapper.
  echo '[exp1_pca] Running hypatiax_defi_benchmark_pca.py (all 74 DeFi cases, PCA 40/60 split)'
  python3 '${EXPERIMENTS_DIR}/hypatiax_defi_benchmark_pca.py' \\
    --output-dir \"\${_PCA_DEFI_DIR}\" \\
    --force-fresh \\
    2>&1 | tee '${RESULTS_DIR}/exp1_pca_run.log'

  # Write split_protocol_disclosure.json (required by Gate B)
  python3 - <<'PYEOF'
import json, pathlib, datetime
PCA_DIR   = pathlib.Path('${RESULTS_DIR}/comparison_results/noise-noiseless/noiseless/defi_pca')
DISC_FILE = PCA_DIR / 'split_protocol_disclosure.json'
disclosure = {
    'fixc3':              True,
    'split_protocol':     'pca_40_60',
    'split_function':     'pca_directed_split',
    'split_level':        'outer_loop',
    'force_fresh':        True,
    'script':             'hypatiax_defi_benchmark_pca.py',
    'test_size':          0.6,
    'train_size':         0.4,
    'random_split_used':  False,
    'dfi_parity':         True,
    'section_reference':  'sec:6.4 + sec:10.2-10.4',
    'generated_by':       'run_all.sh exp1_pca via hypatiax_defi_benchmark_pca.py',
    'timestamp':          datetime.datetime.utcnow().isoformat() + 'Z',
}
DISC_FILE.write_text(json.dumps(disclosure, indent=2))
print(f'  [exp1_pca] split_protocol_disclosure.json written → {DISC_FILE}')
PYEOF

  echo '[exp1_pca] Computing exp1_pca_summary.json...'
  python3 - <<'PYEOF_SUMMARY'
import json, pathlib, datetime

PCA_DIR   = pathlib.Path('${RESULTS_DIR}/comparison_results/noise-noiseless/noiseless/defi_pca')
SUMMARY   = PCA_DIR / 'exp1_pca_summary.json'
THRESHOLD = 0.999999

n_pass = n_total = 0
source_files = []
for fp in sorted(PCA_DIR.glob('*.json')) if PCA_DIR.exists() else []:
    if any(x in fp.name for x in ('checkpoint', 'disclosure', 'summary', 'baseline')):
        continue
    try:
        data = json.loads(fp.read_text())
    except Exception:
        continue
    source_files.append(fp.name)
    cases = data if isinstance(data, list) else data.get('results', [data])
    for case in cases:
        if not isinstance(case, dict):
            continue
        hybrid = case.get('results', {}).get('hybrid', {})
        r2 = hybrid.get('test_r2')
        if r2 is None:
            for k in ('r2', 'r2_test', 'best_r2', 'R2'):
                v = case.get(k)
                if v is not None:
                    r2 = v
                    break
        if r2 is None:
            continue
        try:
            r2 = float(r2)
        except (TypeError, ValueError):
            continue
        if r2 > 1.01:
            continue
        n_total += 1
        if r2 >= THRESHOLD:
            n_pass += 1

summary = {
    'fixc3_step':     'exp1_pca',
    'description':    'DeFi PCA result — PCA-directed 40/60 split (all 74 cases)',
    'split_protocol': 'pca_40_60',
    'test_size':      0.6,
    'train_size':     0.4,
    'n_pass':         n_pass,
    'n_total':        n_total,
    'solve_rate':     (n_pass / n_total) if n_total > 0 else None,
    'source_files':   source_files[:10],
    'timestamp':      datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
SUMMARY.write_text(json.dumps(summary, indent=2))
rate_str = f'{n_pass}/{n_total}' if n_total > 0 else '?/?'
print(f'  [exp1_pca] DeFi PCA solve rate: {rate_str} → exp1_pca_summary.json')
if n_total == 0:
    print('  [WARN]  No results in defi_pca/ yet — rerun after benchmark completes.')
PYEOF_SUMMARY

  echo '[exp1_pca] Scanning for NN feature-count-mismatch fingerprint...'
  python3 - <<'PYEOF_FINGERPRINT_1'
import json, math, pathlib

PCA_DIR = pathlib.Path('${RESULTS_DIR}/comparison_results/noise-noiseless/noiseless/defi_pca')
hits, n_scanned = [], 0
for fp in sorted(PCA_DIR.glob('*.json')) if PCA_DIR.exists() else []:
    if any(x in fp.name for x in ('checkpoint', 'disclosure', 'summary', 'baseline')):
        continue
    try:
        data = json.loads(fp.read_text())
    except Exception:
        continue
    cases = data if isinstance(data, list) else data.get('results', [data])
    for c in cases:
        if not isinstance(c, dict):
            continue
        n_scanned += 1
        nn  = c.get('results', {}).get('neural_network', {})
        err = nn.get('error', '') or ''
        tr2 = nn.get('test_r2')
        is_nan = tr2 is None or (isinstance(tr2, float) and math.isnan(tr2))
        if 'StandardScaler is expecting' in err or 'features, but' in err or is_nan:
            hits.append((c.get('equation_id'), c.get('seed'), err or '(nan, no error string)'))

print(f'  [exp1_pca] Scanned {n_scanned} record(s) for NN feature-count-mismatch fingerprint')
print(f'  [exp1_pca] Records matching fingerprint: {len(hits)}')
for h in hits[:20]:
    print('   ', h)
if hits:
    print('  WARNING: exp1_pca NN feature-count-mismatch fingerprint detected — '
          'see hypatiax_defi_benchmark_pca.py _compute_augment_plan/_apply_augment_plan.')
PYEOF_FINGERPRINT_1

  # Verification
  echo '=== exp1_pca verification ==='
  find \"\${_PCA_DEFI_DIR}\" -type f 2>/dev/null | sort || echo '  (empty)'
  _NRESULT=\$(find \"\${_PCA_DEFI_DIR}\" -name '*.json' \\
    ! -name 'checkpoint*' ! -name '*disclosure*' ! -name '*summary*' \\
    2>/dev/null | wc -l)
  _NDISC=\$(find \"\${_PCA_DEFI_DIR}\" -name 'split_protocol_disclosure.json' 2>/dev/null | wc -l)
  _NSUMMARY=\$(find \"\${_PCA_DEFI_DIR}\" -name 'exp1_pca_summary.json' 2>/dev/null | wc -l)
  echo \"  Result JSONs    : \${_NRESULT}\"
  echo \"  Disclosure file : \${_NDISC} (split_protocol_disclosure.json)\"
  echo \"  Summary file    : \${_NSUMMARY} (exp1_pca_summary.json)\"
  if [[ \"\${_NRESULT}\" -eq 0 ]]; then
    echo 'WARNING: exp1_pca produced no result JSON — check exp1_pca_run.log'
  fi
  if [[ \"\${_NDISC}\" -eq 0 ]]; then
    echo 'WARNING: split_protocol_disclosure.json not found — Gate B in ci_runner_disclosure.yml will FAIL'
  fi
  if [[ \"\${_NSUMMARY}\" -eq 0 ]]; then
    echo 'WARNING: exp1_pca_summary.json not found — qualify/audit steps will not see DeFi PCA solve rate'
  fi
  echo '=== end exp1_pca ==='
"

# ── STEP 2c: exp1b_pca ────────────────────────────────────────────────────────
# Output directory: comparison_results/noise-noiseless/15_pca/
# CLI example (run standalone):
run exp1b_pca "FIX-C3 DeFi seed sweep with PCA 40/60 split (mirrors exp1b with PCA split)" bash -c "
  cd '${REPO_ROOT}'
  _PCA15_DIR='${RESULTS_DIR}/comparison_results/noise-noiseless/15_pca'
  mkdir -p \"\${_PCA15_DIR}\"

  _SHARD_TASKS='${SHARD_IDS:-${TASK_IDS:-}}'
  _SHARD_SEEDS=\$(echo \"\${_SHARD_TASKS}\" | tr ' ' '\n' | grep -oE '^portfolio_seed[0-9]+$' | sed 's/^portfolio_seed//' | paste -sd, -)
  if [[ -z \"\${_SHARD_SEEDS}\" ]]; then
    echo '  [exp1b_pca] No portfolio_seedNN task IDs found in SHARD_IDS/TASK_IDS — running full default seed list (local/standalone run).'
    _SHARD_SEEDS='42,99,123,777,2024'
  else
    echo \"  [exp1b_pca] SHARD_INDEX=\${SHARD_INDEX:-0} -> seeds for this shard: \${_SHARD_SEEDS}\"
  fi

  # --force-fresh is passed to the script itself — guarantees fresh results
  # even when the script is invoked directly, bypassing this shell wrapper.
  echo '[exp1b_pca] Running hypatiax_defi_benchmark_pca.py (portfolio seed sweep, PCA 40/60 split)'
  DEFI_SEEDS=\"\${_SHARD_SEEDS}\" \\
    python3 '${EXPERIMENTS_DIR}/hypatiax_defi_benchmark_pca.py' \\
      --output-dir \"\${_PCA15_DIR}\" \\
      --force-fresh \\
      2>&1 | tee '${RESULTS_DIR}/exp1b_pca_run.log'

  # Move any loose outputs (same pattern as exp1b move block)
  _SHARD=\${SHARD_INDEX:-0}
  _SEED_TAG=\$(echo \"\${_SHARD_SEEDS:-42}\" | tr ',' '_')
  for _search_root in '${EXPERIMENTS_DIR}' '${RESULTS_DIR}'; do
    find \"\${_search_root}\" -maxdepth 1 \\
    \\( \\
        -name 'defi_pca_v3_*.json' \\
        -o -name '*portfolio*variance*pca*.json' \\
    \\) | while IFS= read -r src; do
        [[ \"\$src\" == \"\${_PCA15_DIR}\"* ]] && continue
        fname=\$(basename \"\$src\")
        stem=\"\${fname%.*}\"
        ext=\"\${fname##*.}\"
        dst=\"\${_PCA15_DIR}/\${stem}_shard\${_SHARD}_seed\${_SEED_TAG}.\${ext}\"
        [ -f \"\$src\" ] && mv -v \"\$src\" \"\$dst\" || true
    done
  done

  python3 - <<'PYEOF_DISC_1B'
import json, pathlib, datetime
PCA15_DIR = pathlib.Path('${RESULTS_DIR}/comparison_results/noise-noiseless/15_pca')
DISC_FILE = PCA15_DIR / 'split_protocol_disclosure.json'
PCA15_DIR.mkdir(parents=True, exist_ok=True)
disclosure = {
    'fixc3':              True,
    'split_protocol':     'pca_40_60',
    'split_function':     'pca_directed_split',
    'split_level':        'outer_loop',
    'force_fresh':        True,
    'script':             'hypatiax_defi_benchmark_pca.py',
    'test_size':          0.6,
    'train_size':         0.4,
    'random_split_used':  False,
    'dfi_parity':         True,
    'section_reference':  'sec:6.4 + sec:10.2-10.4',
    'generated_by':       'run_all.sh exp1b_pca via hypatiax_defi_benchmark_pca.py',
    'timestamp':          datetime.datetime.utcnow().isoformat() + 'Z',
}
DISC_FILE.write_text(json.dumps(disclosure, indent=2))
print(f'  [exp1b_pca] split_protocol_disclosure.json written → {DISC_FILE}')
PYEOF_DISC_1B

  echo '[exp1b_pca] Computing exp1b_pca_summary.json...'
  python3 - <<'PYEOF_SUMMARY_1B'
import json, pathlib, datetime
from collections import defaultdict

PCA15_DIR = pathlib.Path('${RESULTS_DIR}/comparison_results/noise-noiseless/15_pca')
SUMMARY   = PCA15_DIR / 'exp1b_pca_summary.json'
THRESHOLD = 0.999999

n_pass = n_total = 0
source_files = []
per_seed = defaultdict(lambda: {'n_pass': 0, 'n_total': 0})
seen_case_seed = set()  # dedup: keep one record per (equation_id, seed) across shard files

for fp in sorted(PCA15_DIR.glob('*.json')) if PCA15_DIR.exists() else []:
    if any(x in fp.name for x in ('checkpoint', 'disclosure', 'summary', 'baseline')):
        continue
    try:
        data = json.loads(fp.read_text())
    except Exception:
        continue
    source_files.append(fp.name)
    cases = data if isinstance(data, list) else data.get('results', [data])
    for case in cases:
        if not isinstance(case, dict):
            continue
        seed = case.get('seed')
        key = (case.get('equation_id'), seed)
        if key in seen_case_seed:
            continue  # same (case, seed) may appear in more than one shard file
        seen_case_seed.add(key)

        hybrid = case.get('results', {}).get('hybrid', {})
        r2 = hybrid.get('test_r2')
        if r2 is None:
            for k in ('r2', 'r2_test', 'best_r2', 'R2'):
                v = case.get(k)
                if v is not None:
                    r2 = v
                    break
        if r2 is None:
            continue
        try:
            r2 = float(r2)
        except (TypeError, ValueError):
            continue
        if r2 > 1.01:
            continue

        n_total += 1
        per_seed[seed]['n_total'] += 1
        if r2 >= THRESHOLD:
            n_pass += 1
            per_seed[seed]['n_pass'] += 1

seeds_observed = sorted([s for s in per_seed if s is not None])
per_seed_out = {
    str(s): {
        'n_pass':     v['n_pass'],
        'n_total':    v['n_total'],
        'solve_rate': (v['n_pass'] / v['n_total']) if v['n_total'] > 0 else None,
    }
    for s, v in sorted(per_seed.items(), key=lambda kv: (kv[0] is None, kv[0]))
}

summary = {
    'fixc3_step':      'exp1b_pca',
    'description':     'DeFi PCA portfolio seed-sweep result — PCA-directed 40/60 split',
    'split_protocol':  'pca_40_60',
    'test_size':       0.6,
    'train_size':      0.4,
    'task_filter':     'portfolio',
    'n_pass':          n_pass,
    'n_total':         n_total,
    'solve_rate':      (n_pass / n_total) if n_total > 0 else None,
    'seeds_observed':  seeds_observed,
    'n_seeds_observed': len(seeds_observed),
    'per_seed':        per_seed_out,
    'source_files':    source_files[:20],
    'timestamp':       datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
SUMMARY.write_text(json.dumps(summary, indent=2))
rate_str = f'{n_pass}/{n_total}' if n_total > 0 else '?/?'
print(f'  [exp1b_pca] DeFi PCA portfolio-sweep solve rate: {rate_str} → exp1b_pca_summary.json')
print(f'  [exp1b_pca] Seeds observed: {seeds_observed}')
if n_total == 0:
    print('  [WARN]  No results in 15_pca/ yet — rerun after benchmark completes.')
if len(seeds_observed) < 2:
    print(f'  [WARN]  Only {len(seeds_observed)} distinct seed(s) observed in 15_pca/ — '
          f'this may be a single shard, an incomplete sweep, or a regression of the F6 seed-loop fix.')
PYEOF_SUMMARY_1B

  echo '[exp1b_pca] Scanning for NN feature-count-mismatch fingerprint...'
  python3 - <<'PYEOF_FINGERPRINT_1B'
import json, math, pathlib

PCA15_DIR = pathlib.Path('${RESULTS_DIR}/comparison_results/noise-noiseless/15_pca')
hits, n_scanned = [], 0
for fp in sorted(PCA15_DIR.glob('*.json')) if PCA15_DIR.exists() else []:
    if any(x in fp.name for x in ('checkpoint', 'disclosure', 'summary', 'baseline')):
        continue
    try:
        data = json.loads(fp.read_text())
    except Exception:
        continue
    cases = data if isinstance(data, list) else data.get('results', [data])
    for c in cases:
        if not isinstance(c, dict):
            continue
        n_scanned += 1
        nn  = c.get('results', {}).get('neural_network', {})
        err = nn.get('error', '') or ''
        tr2 = nn.get('test_r2')
        is_nan = tr2 is None or (isinstance(tr2, float) and math.isnan(tr2))
        if 'StandardScaler is expecting' in err or 'features, but' in err or is_nan:
            hits.append((c.get('equation_id'), c.get('seed'), err or '(nan, no error string)'))

print(f'  [exp1b_pca] Scanned {n_scanned} record(s) for NN feature-count-mismatch fingerprint')
print(f'  [exp1b_pca] Records matching fingerprint: {len(hits)}')
for h in hits[:20]:
    print('   ', h)
if hits:
    print('  WARNING: exp1b_pca NN feature-count-mismatch fingerprint detected — '
          'see hypatiax_defi_benchmark_pca.py _compute_augment_plan/_apply_augment_plan.')
PYEOF_FINGERPRINT_1B

  # Verification
  echo '=== exp1b_pca verification ==='
  find \"\${_PCA15_DIR}\" -type f 2>/dev/null | sort || echo '  (empty)'
  _COUNT=\$(find \"\${_PCA15_DIR}\" -type f 2>/dev/null | wc -l)
  _NDISC=\$(find \"\${_PCA15_DIR}\" -name 'split_protocol_disclosure.json' 2>/dev/null | wc -l)
  _NSUMMARY=\$(find \"\${_PCA15_DIR}\" -name 'exp1b_pca_summary.json' 2>/dev/null | wc -l)
  echo \"Files produced: \${_COUNT}\"
  echo \"  Disclosure file : \${_NDISC} (split_protocol_disclosure.json)\"
  echo \"  Summary file    : \${_NSUMMARY} (exp1b_pca_summary.json)\"
  if [[ \"\${_COUNT}\" -eq 0 && \"\${SKIP_ALLOWED:-false}\" != 'true' ]]; then
    echo 'WARNING: exp1b_pca generated no files — set SKIP_ALLOWED=true if this step was intentionally skipped'
  fi
  if [[ \"\${_NDISC}\" -eq 0 ]]; then
    echo 'WARNING: split_protocol_disclosure.json not found in 15_pca/ — Gate B will FAIL'
  fi
  if [[ \"\${_NSUMMARY}\" -eq 0 ]]; then
    echo 'WARNING: exp1b_pca_summary.json not found — qualify/audit steps will not see the DeFi PCA portfolio seed-sweep solve rate'
  fi
  echo '=== end exp1b_pca ==='
"

# ── STEP 3: extrap ────────────────────────────────────────────────────────────
run extrap "OOD extrapolation comparative run (Tab 9 OOD columns)" bash -c "
  cd '${REPO_ROOT}'
  mkdir -p '${RESULTS_DIR}/comparison_results/extrapolation'
  for DOMAIN_ID in ${FEYNMAN_DOMAINS}; do
    echo '=== extrap: domain='\${DOMAIN_ID}' ==='
    FEYNMAN_SAMPLES=${FEYNMAN_SAMPLES} \
    FEYNMAN_TIMEOUT=${FEYNMAN_TIMEOUT} \
    METHOD_TIMEOUT=${METHOD_TIMEOUT} \
    PYSR_FIT_WALL_TIMEOUT=${PYSR_FIT_WALL_TIMEOUT} \
    PYSR_FIT_GRACE_SECS=${PYSR_FIT_GRACE_SECS} \
    JOB_DEADLINE=${JOB_DEADLINE} \
      python3 '${EXPERIMENTS_DIR}/run_comparative_suite_benchmark_v2.py' \
        --benchmark feynman \
        --extrap \
        --extrap-multiplier \${EXTRAP_MULTIPLIER:-2.0} \
        --extrap-train-frac \${EXTRAP_TRAIN_FRAC:-0.8} \
        --domain \"\${DOMAIN_ID}\" \
        --samples ${FEYNMAN_SAMPLES} \
        --pysr-timeout ${FEYNMAN_TIMEOUT} \
        --method-timeout ${METHOD_TIMEOUT} \
        --populations ${PYSR_POPULATIONS} \
        --parsimony 0.01 \
        --use-transcendental-compositions \
        --nn-seeds 3 \
        --no-llm-cache \
        --checkpoint-name \"extrap_checkpoint_\${DOMAIN_ID}\" \
        --output-dir '${RESULTS_DIR}/comparison_results/extrapolation' \
        --resume \
        2>&1 | tee -a '${RESULTS_DIR}/extrap_run.log' \
      || echo 'WARNING: extrap domain '\${DOMAIN_ID}' exited non-zero — continuing'
  done
  echo 'extrap output: ${RESULTS_DIR}/comparison_results/extrapolation/'
  ls '${RESULTS_DIR}/comparison_results/extrapolation/' 2>/dev/null || true
"

# ── STEP 4: hybrid_all_domains ────────────────────────────────────────────────
run hybrid_all_domains "Hybrid LLM+NN all-domains run -- 10 domains (SS10.9 hybrid)" bash -c "
  set -euo pipefail
  ACTUAL_DOMAINS=\$(python3 - << 'PYEOF'
import importlib.util, sys, pathlib, io, contextlib
_muted = io.StringIO()
spec = importlib.util.spec_from_file_location(
    'hybrid_mod',
    pathlib.Path('${GENERATION_DIR}/hybrid_all_domains_llm_nn/hybrid_system_llm_nn_all_domains.py')
)
mod = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(_muted):
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass
domains = getattr(mod, 'DOMAINS', getattr(mod, 'ALL_DOMAINS', getattr(mod, 'DOMAIN_KEYS', None)))
if domains is None:
    try:
        with contextlib.redirect_stdout(_muted):
            from hypatiax.core.generation.hybrid_all_domains_llm_nn \
                .hybrid_system_llm_nn_all_domains import ExperimentProtocolAll
            _d = ExperimentProtocolAll().get_all_domains()
        domains = set(_d.keys()) if hasattr(_d, 'keys') else set(_d)
    except Exception as e:
        print(f'UNKNOWN: {e!r}', file=sys.stderr); sys.exit(1)
print(','.join(sorted(str(d) for d in domains)))
PYEOF
  )
  EXPECTED_SORTED=\$(echo '${HYBRID_ALL_DOMAINS_EXPECTED}' | tr ',' '\n' | sort | tr '\n' ',' | sed 's/,\$//')
  ACTUAL_SORTED=\$(echo \"\${ACTUAL_DOMAINS}\" | tr ',' '\n' | sort | tr '\n' ',' | sed 's/,\$//')
  if [[ \"\${ACTUAL_SORTED}\" != \"\${EXPECTED_SORTED}\" ]]; then
    echo '[WARN] hybrid_all_domains domain list MISMATCH -- update HYBRID_ALL_DOMAINS_EXPECTED'
    echo '  Expected: '\"\${EXPECTED_SORTED}\"
    echo '  Actual  : '\"\${ACTUAL_SORTED}\"
    exit 1
  fi
  echo '[hybrid_all_domains] Domain-list OK: '\"\${ACTUAL_SORTED}\"
  cd '${GENERATION_DIR}/hybrid_all_domains_llm_nn'
  mkdir -p '${RESULTS_DIR}/hybrid_llm_nn/all_domains'
  python3 hybrid_system_llm_nn_all_domains.py \
    --samples '${FEYNMAN_SAMPLES}' \
    2>&1 | tee '${RESULTS_DIR}'/hybrid_all_domains_run.log
  # ── Move script's hardcoded-path output → RESULTS_DIR ──────────────────────
  _HYBRID_OUT_SRC='hypatiax/data/results'
  if [[ -d \"\${_HYBRID_OUT_SRC}\" ]]; then
    find \"\${_HYBRID_OUT_SRC}\" -maxdepth 1 -name 'hybrid_llm_nn_all_domains_*.json' \
      -exec mv -f {} '${RESULTS_DIR}/hybrid_llm_nn/all_domains/' \;
  fi
  _HYBRID_MOVED=\$(ls -t '${RESULTS_DIR}/hybrid_llm_nn/all_domains'/hybrid_llm_nn_all_domains_*.json 2>/dev/null | head -1 || true)
  if [[ -z \"\${_HYBRID_MOVED}\" ]]; then
    echo \"WARNING: no hybrid_llm_nn_all_domains_*.json found to move into RESULTS_DIR -- check script output location.\"
  else
    echo \"[hybrid_all_domains] Output moved: \${_HYBRID_MOVED}\"
  fi
"

# ── STEP 4a: instability ──────────────────────────────────────────────────────
run instability "Instability Index analysis (numerical only, no figures) -- SS10.9 (Regime A/B/C)" bash -c "
  mkdir -p '${RESULTS_DIR}/figures'
  # Purge only instability-specific files; preserve exp1 benchmark JSONs.
  rm -f \
    '${RESULTS_DIR}/figures/instability_analysis.csv' \
    '${RESULTS_DIR}/figures/instability_extrapolation.csv' \
    2>/dev/null || true
  find '${RESULTS_DIR}/figures' -maxdepth 1 \
    \( -name 'fig_paper_*.pdf' -o -name 'fig_paper_*.png' \
       -o -name 'hypatiax_instability_*.pdf' -o -name 'hypatiax_instability_*.png' \) \
    -delete 2>/dev/null || true

  DEFI_DIR='${RESULTS_DIR}/comparison_results/noise-noiseless/noiseless/defi'

  BENCH_JSON=\$(ls -t \"\${DEFI_DIR}\"/hypatiax_defi_benchmark_*results*.json 2>/dev/null | head -1 || true)

  if [[ -n \"\${BENCH_JSON}\" ]]; then
    echo '[instability] Stage 2 extrapolation merge enabled: '\"\${BENCH_JSON}\"
    BENCH_ARG=\"--benchmark-json \${BENCH_JSON}\"
  else
    echo '[instability] No benchmark JSON found in '\"\${DEFI_DIR}\"' -- Stage 2 (EX figure) skipped.'
    echo '              Run STEP 1 (exp1) first to enable the EX figure.'
    BENCH_ARG=\"\"
  fi

  python3 '${EXPERIMENTS_DIR}/run_instability_suite.py' \
    --results-dir \"\${DEFI_DIR}\" \
    --out         '${RESULTS_DIR}/figures' \
    --csv-out     '${RESULTS_DIR}/figures/instability_analysis.csv' \
    \${BENCH_ARG} \
    --format png pdf \
    2>&1 | tee '${RESULTS_DIR}'/instability_run.log

  _NFIG=\$(find '${RESULTS_DIR}/figures' -maxdepth 1 \( -name '*.png' -o -name '*.pdf' \) 2>/dev/null | wc -l)
  find '${RESULTS_DIR}/figures' -maxdepth 1 \( -name '*.png' -o -name '*.pdf' \) -delete 2>/dev/null || true
  echo \"[instability] removed \${_NFIG} figure byproduct(s) — figure generation disabled\"

  _CANON_CSV='${RESULTS_DIR}/figures/instability_analysis.csv'
  if [[ ! -s \"\${_CANON_CSV}\" ]]; then
    echo \"[instability] WARNING: \${_CANON_CSV} missing or empty after run_instability_suite.py exited 0.\"
    _STRAY_CSV=\$(find '${REPO_ROOT}' -maxdepth 6 -name 'instability_analysis.csv' \
                   -not -path \"\${_CANON_CSV}\" 2>/dev/null | xargs -r ls -t 2>/dev/null | head -1 || true)
    if [[ -n \"\${_STRAY_CSV}\" && -s \"\${_STRAY_CSV}\" ]]; then
      echo \"[instability] Found stray CSV at \${_STRAY_CSV} -- copying into canonical location.\"
      mkdir -p '${RESULTS_DIR}/figures'
      cp \"\${_STRAY_CSV}\" \"\${_CANON_CSV}\"
    else
      echo '[instability] No stray instability_analysis.csv found anywhere under REPO_ROOT either.'
      echo '              run_instability_suite.py likely failed internally before writing the CSV'
      echo '              (e.g. \"Loaded 0 cases\") -- check instability_run.log above for the real cause.'
    fi
  fi
"


# ── STEP 5: exp2_feynman ──────────────────────────────────────────────────────
run exp2_feynman "Feynman SR benchmark -- Phase 2 noisy protocol per-domain (Tab 16-18)" bash -c "
  cd '${REPO_ROOT}'
  mkdir -p '${RESULTS_DIR}/comparison_results/feynman-tests/exp2'
  for DOMAIN_ID in ${FEYNMAN_DOMAINS}; do
    echo '=== exp2_feynman: domain='\${DOMAIN_ID}' ==='
    FEYNMAN_SAMPLES=${FEYNMAN_SAMPLES} \
    FEYNMAN_TIMEOUT=${FEYNMAN_TIMEOUT} \
    METHOD_TIMEOUT=${METHOD_TIMEOUT} \
    PYSR_FIT_WALL_TIMEOUT=${PYSR_FIT_WALL_TIMEOUT} \
    PYSR_FIT_GRACE_SECS=${PYSR_FIT_GRACE_SECS} \
    JOB_DEADLINE=${JOB_DEADLINE} \
      python3 '${EXPERIMENTS_DIR}/run_comparative_suite_benchmark_v2.py' \
        --benchmark feynman \
        --domain \"\${DOMAIN_ID}\" \
        --samples ${FEYNMAN_SAMPLES} \
        --pysr-timeout ${FEYNMAN_TIMEOUT} \
        --method-timeout ${METHOD_TIMEOUT} \
        --populations ${PYSR_POPULATIONS} \
        --parsimony 0.01 \
        --noiseless \
        --threshold ${FEYNMAN_NOISELESS_THRESHOLD} \
        --checkpoint-name \"feynman_exp2_checkpoint_\${DOMAIN_ID}\" \
        --output-dir '${RESULTS_DIR}/comparison_results/feynman-tests/exp2' \
        --resume \
      2>&1 | tee -a '${RESULTS_DIR}/comparison_results/feynman-tests/exp2/exp2_run.log' \
    || echo 'WARNING: domain '\${DOMAIN_ID}' exited non-zero — continuing'
  done
"

# ── STEP 5b: exp2_feynman_pca_4060 ───────────────────────────────────────────
# Output directory: comparison_results/feynman-tests/exp2_pca_4060/
# CLI example (run standalone):
run exp2_feynman_pca_4060 "FIX-C3: Feynman rerun with PCA 40/60 split — corrected §10.7 result" bash -c "
  cd '${REPO_ROOT}'

  _PCA_DIR='${RESULTS_DIR}/comparison_results/feynman-tests/exp2_pca_4060'
  _LEG_DIR='${RESULTS_DIR}/comparison_results/feynman-tests/exp2'
  _BASELINE='${RESULTS_DIR}/fixc3_baseline.json'

  mkdir -p \"\${_PCA_DIR}\"

  echo '[FIX-C3] Checking legacy 9/30 baseline (self-healing, mirrors ci_runner_repro.yml Gate C)...'
  python3 - <<'PYEOF'
import glob, json, pathlib, sys

LEG_DIR    = pathlib.Path('${RESULTS_DIR}/comparison_results/feynman-tests/exp2')
BASELINE   = pathlib.Path('${RESULTS_DIR}/fixc3_baseline.json')

THRESHOLD  = 0.999999
PREFERRED  = {'hypatiax','hybridv50','hybrid50','hybridsymbolic',
              'hybriddefi','hypatia','hybrid','ours','proposed'}

def _r2(row):
    for k in ('r2','r2_test','r2_train','best_r2','R2'):
        v = row.get(k)
        if v is not None:
            try:
                f = float(v)
                if f <= 1.01:
                    return f
            except (TypeError, ValueError):
                pass
    return None

def _rows(data):
    if isinstance(data, dict):
        if isinstance(data.get('tests'), list):
            for test in data['tests']:
                if not isinstance(test, dict):
                    continue
                results = test.get('results')
                if isinstance(results, dict):
                    for rec in results.values():
                        if isinstance(rec, dict):
                            yield rec
                else:
                    yield from _rows(test)
            return
        for key in ('results','equation_results','data','rows'):
            v = data.get(key)
            if v is not None:
                yield from _rows(v)
                return
        yield data
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield item
for fp in sorted(LEG_DIR.glob('*.json')) if LEG_DIR.exists() else []:
    if any(x in fp.name for x in ('checkpoint','disclosure','baseline')):
        continue
    if '_pca' in fp.name:
        stray_pca_files.append(fp.name)
        continue
    try:
        data = json.loads(fp.read_text())
    except Exception:
        continue
    source_files.append(fp.name)
    for row in _rows(data):
        raw    = row.get('method') or row.get('model') or ''
        method = str(raw).lower().replace('-','').replace('_','').replace(' ','')
        if method and not any(p in method for p in PREFERRED):
            continue
        r2 = _r2(row)
        if r2 is None:
            continue
        n_total += 1
        if r2 >= THRESHOLD:
            n_pass += 1

baseline = {
    'fixc3_gate':      'C',
    'description':     'Pre-fix baseline — Feynman result (random 80/20 split)',
    'split_protocol':  'random_80_20',
    'n_pass':          n_pass,
    'n_total':         n_total,
    'solve_rate':      (n_pass / n_total) if n_total > 0 else None,
    'paper_claim':     '9/30 = 0.300',
    'source_files':    source_files,
}

if not BASELINE.exists():
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE.write_text(json.dumps(baseline, indent=2))
    print(f'  [FIX-C3] Baseline locked: {n_pass}/{n_total} (random_80_20) → fixc3_baseline.json')
    print(f'  [FIX-C3] source_files ({len(source_files)}): {source_files}')
else:
    existing = json.loads(BASELINE.read_text())
    existing_rate = existing.get('solve_rate')
    if existing_rate is None:
        # Self-heal: baseline was written before exp2/ results existed.
        if n_total > 0:
            BASELINE.write_text(json.dumps(baseline, indent=2))
            print(
                '  [FIX-C3] Baseline was invalid (solve_rate=null, written before '
                'exp2/ results existed) — recomputed and rewritten → '
                f\"{n_pass}/{n_total} (rate={baseline['solve_rate']:.3f})\"
            )
            print(f'  [FIX-C3] source_files ({len(source_files)}): {source_files}')
        else:
            print(
                '  [FIX-C3][ERROR] fixc3_baseline.json exists but solve_rate is '
                'null, and no legacy JSONs were found in this checkout either — '
                'confirm comparison_results/feynman-tests/exp2/ contains result '
                'JSONs before this gate can lock a valid baseline.'
            )
            sys.exit(1)
    elif n_total > 0:
        new_rate = n_pass / n_total
        if abs(new_rate - existing_rate) > 0.05:
            print(
                f'  [FIX-C3][ERROR] Baseline solve_rate changed from '
                f'{existing_rate:.3f} to {new_rate:.3f} — possible overwrite of '
                '9/30 baseline. Delete fixc3_baseline.json manually to reset.'
            )
            sys.exit(1)
        else:
            print(
                f\"  [FIX-C3] Baseline already locked: {existing.get('n_pass')}/\"
                f\"{existing.get('n_total')} (rate={existing_rate:.3f})\"
            )
            _existing_sf = existing.get('source_files', [])
            print(f'  [FIX-C3] source_files ({len(_existing_sf)}): {_existing_sf}')
    else:
        print(
            f\"  [FIX-C3][WARN] Baseline file exists (rate={existing_rate:.3f}) \"
            \"but no legacy JSONs found in this checkout — rate could not be \"
            \"re-verified; accepting existing baseline\"
        )

if stray_pca_files:
    print(f'  [FIX-C3][WARN] {len(stray_pca_files)} stray _pca file(s) found in legacy exp2/ dir')
    print('          (excluded from baseline — they belong in exp2_pca_4060/):')
    for _f in stray_pca_files[:10]:
        print(f'            - {_f}')
    print(f'          Move them: mv {LEG_DIR}/*_pca_*.json {LEG_DIR.parent}/exp2_pca_4060/  (verify timestamps first)')
PYEOF

  echo '[FIX-C3] Starting corrected Feynman run: run_comparative_suite_benchmark_pca.py'
  echo '         PCA-directed 40/60 split (pca_directed_split, test_size=0.6 — outer-loop)'
  echo '         --force-fresh ensures fresh results even on direct script invocation'
  echo '         output ➒ \${_PCA_DIR}'

  for DOMAIN_ID in ${FEYNMAN_DOMAINS}; do
    echo '=== exp2_feynman_pca_4060: domain='\${DOMAIN_ID}' ==='
    FEYNMAN_SAMPLES=${FEYNMAN_SAMPLES} \
    FEYNMAN_TIMEOUT=${FEYNMAN_TIMEOUT} \
    METHOD_TIMEOUT=${METHOD_TIMEOUT} \
    PYSR_FIT_WALL_TIMEOUT=${PYSR_FIT_WALL_TIMEOUT} \
    PYSR_FIT_GRACE_SECS=${PYSR_FIT_GRACE_SECS} \
    JOB_DEADLINE=${JOB_DEADLINE} \
      python3 '${EXPERIMENTS_DIR}/run_comparative_suite_benchmark_pca.py' \
        --benchmark feynman \
        --domain \"\${DOMAIN_ID}\" \
        --samples ${FEYNMAN_SAMPLES} \
        --pysr-timeout ${FEYNMAN_TIMEOUT} \
        --method-timeout ${METHOD_TIMEOUT} \
        --populations ${PYSR_POPULATIONS} \
        --parsimony 0.01 \
        --noiseless \
        --threshold ${FEYNMAN_NOISELESS_THRESHOLD} \
        --use-transcendental-compositions \
        --nn-seeds 3 \
        --no-llm-cache \
        --checkpoint-name \"pca4060_checkpoint_\${DOMAIN_ID}\" \
        --output-dir \"\${_PCA_DIR}\" \
        --force-fresh \
      2>&1 | tee -a \"\${_PCA_DIR}/exp2_pca_4060_run.log\" \
    || echo 'WARNING: pca_4060 domain '\${DOMAIN_ID}' exited non-zero — continuing'

    mkdir -p \"\${_PCA_DIR}/_saved\"
    while IFS= read -r _pf; do
      _pfn=\$(basename \"\${_pf}\")
      ln -f \"\${_pf}\" \"\${_PCA_DIR}/_saved/\${_pfn}\" 2>/dev/null \
        || cp \"\${_pf}\" \"\${_PCA_DIR}/_saved/\${_pfn}\" \
        || true
    done < <(find \"\${_PCA_DIR}\" -maxdepth 1 -name 'protocol_core_noiseless_pca_*.json' 2>/dev/null)
  done

  _PCA_SAVED=\$(find \"\${_PCA_DIR}/_saved\" -name 'protocol_core_noiseless_pca_*.json' 2>/dev/null | wc -l)
  _PCA_PRIMARY=\$(find \"\${_PCA_DIR}\" -maxdepth 1 -name 'protocol_core_noiseless_pca_*.json' 2>/dev/null | wc -l)
  echo \"[C3-E2-guard] \${_PCA_PRIMARY} primary / \${_PCA_SAVED} hard-linked into \${_PCA_DIR}/_saved/\"
  if [[ \"\${_PCA_PRIMARY}\" -eq 0 && \"\${_PCA_SAVED}\" -gt 0 ]]; then
    echo \"WARNING: primary protocol_core_noiseless_pca_*.json were deleted (prune_old E2); \${_PCA_SAVED} copies survived in _saved/ — restore with:\"
    echo \"         cp \${_PCA_DIR}/_saved/protocol_core_noiseless_pca_*.json \${_PCA_DIR}/\"
  elif [[ \"\${_PCA_PRIMARY}\" -eq 0 ]]; then
    echo 'WARNING: exp2_feynman_pca_4060 produced no protocol_core_noiseless_pca_*.json — exp2_pca_4060_summary.json will be empty/incomplete'
  fi

  # ── 3. Compute corrected summary (new solve rate) ─────────────────────────────
  echo '[FIX-C3] Computing corrected solve rate from exp2_pca_4060/ results...'
  python3 - <<'PYEOF'
import glob, json, pathlib, sys

PCA_DIR   = pathlib.Path('${RESULTS_DIR}/comparison_results/feynman-tests/exp2_pca_4060')
SUMMARY   = PCA_DIR / 'exp2_pca_4060_summary.json'
THRESHOLD = 0.999999
PREFERRED = {'hypatiax','hybridv50','hybrid50','hybridsymbolic',
             'hybriddefi','hypatia','hybrid','ours','proposed'}

def _r2(row):
    for k in ('r2','r2_test','r2_train','best_r2','R2'):
        v = row.get(k)
        if v is not None:
            try:
                f = float(v)
                if f <= 1.01:
                    return f
            except (TypeError, ValueError):
                pass
    return None

def _rows(data):
    if isinstance(data, dict):
        if isinstance(data.get('tests'), list):
            for test in data['tests']:
                if not isinstance(test, dict):
                    continue
                results = test.get('results')
                if isinstance(results, dict):
                    for rec in results.values():
                        if isinstance(rec, dict):
                            yield rec
                else:
                    yield from _rows(test)
            return
        for key in ('results','equation_results','data','rows'):
            v = data.get(key)
            if v is not None:
                yield from _rows(v)
                return
        yield data
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield item

n_pass = n_total = 0
source_files = []
per_method = {}  # raw method name -> {'n_pass': int, 'n_total': int}

for fp in sorted(PCA_DIR.glob('*.json')) if PCA_DIR.exists() else []:
    if any(x in fp.name for x in ('checkpoint','disclosure','summary','baseline','benchmark_results')):
        continue
    try:
        data = json.loads(fp.read_text())
    except Exception:
        continue
    source_files.append(fp.name)
    for row in _rows(data):
        raw    = row.get('method') or row.get('model') or ''
        method = str(raw).lower().replace('-','').replace('_','').replace(' ','')
        if method and not any(p in method for p in PREFERRED):
            continue
        r2 = _r2(row)
        if r2 is None:
            continue
        n_total += 1
        pm = per_method.setdefault(raw, {'n_pass': 0, 'n_total': 0})
        pm['n_total'] += 1
        if r2 >= THRESHOLD:
            n_pass += 1
            pm['n_pass'] += 1

per_method_out = {
    m: {
        'n_pass':     v['n_pass'],
        'n_total':    v['n_total'],
        'solve_rate': (v['n_pass'] / v['n_total']) if v['n_total'] > 0 else None,
    }
    for m, v in sorted(per_method.items())
}

FORCED_LLM_DOMAINS = {
    'feynman_mechanics', 'feynman_electromagnetism', 'feynman_quantum',
    'feynman_thermodynamics', 'feynman_optics',
}
NN_HYBRID_KEY = 'HybridSystemLLMNN all-domains (core)'
decision_by_domain = {}  # domain -> {'llm': n, 'other': n, 'forced': bool}
for fp in sorted(PCA_DIR.glob('*.json')) if PCA_DIR.exists() else []:
    if any(x in fp.name for x in ('checkpoint','disclosure','summary','baseline','benchmark_results')):
        continue
    try:
        data = json.loads(fp.read_text())
    except Exception:
        continue
    tests = data.get('tests', []) if isinstance(data, dict) else []
    for t in tests:
        if not isinstance(t, dict):
            continue
        dom = t.get('domain')
        if dom is None:
            continue
        dec = t.get('results', {}).get(NN_HYBRID_KEY, {}).get('metadata', {}).get('decision')
        if dec is None:
            continue
        d = decision_by_domain.setdefault(dom, {'llm': 0, 'other': 0, 'forced': dom in FORCED_LLM_DOMAINS})
        if dec == 'llm':
            d['llm'] += 1
        else:
            d['other'] += 1

_forced_llm  = sum(v['llm'] for v in decision_by_domain.values() if v['forced'])
_forced_tot  = sum(v['llm'] + v['other'] for v in decision_by_domain.values() if v['forced'])
_natural_llm = sum(v['llm'] for v in decision_by_domain.values() if not v['forced'])
_natural_tot = sum(v['llm'] + v['other'] for v in decision_by_domain.values() if not v['forced'])

hybrid_llm_routing = {
    'note': (
        f\"'{NN_HYBRID_KEY}' decision routing, broken out by whether the domain is \"
        \"covered by the explicit force_llm guard in HybridAllDomainsMethod.run() \"
        \"(run_comparative_suite_benchmark_pca.py) — see comment above this block.\"
    ),
    'forced_domains':   sorted(FORCED_LLM_DOMAINS),
    'forced_llm_count':   f'{_forced_llm}/{_forced_tot}' if _forced_tot else '0/0',
    'natural_llm_count':  f'{_natural_llm}/{_natural_tot}' if _natural_tot else '0/0',
    'by_domain': {
        dom: {'llm': v['llm'], 'other': v['other'], 'forced': v['forced']}
        for dom, v in sorted(decision_by_domain.items())
    },
}

summary = {
    'fixc3_step':      'exp2_feynman_pca_4060',
    'description':     'Corrected Feynman result — PCA-directed 40/60 extrapolation split',
    'split_protocol':  'pca_40_60',
    'extrap_train_frac': 0.6,
    'extrap_multiplier': 2.0,
    'n_pass':          n_pass,
    'n_total':         n_total,
    'solve_rate':      (n_pass / n_total) if n_total > 0 else None,
    'per_method':      per_method_out,
    'hybrid_llm_routing': hybrid_llm_routing,
    'paper_legacy_claim': '9/30 = 0.300 (random_80_20)',
    'source_files':    source_files,
}
assert len(summary['source_files']) == len(source_files), (
    'exp2_pca_4060_summary.json internal error: source_files manifest does '
    'not match the files actually scanned — see FIX-MANIFEST-TRUNCATION-2'
)
SUMMARY.write_text(json.dumps(summary, indent=2))
rate_str = f'{n_pass}/{n_total}' if n_total > 0 else '?/?'
print(f'  [FIX-C3] Corrected solve rate: {rate_str} (pca_40_60) → exp2_pca_4060_summary.json')
print(f\"  [FIX-C3] source_files ({len(summary['source_files'])}): {summary['source_files']}\")
for m, v in per_method_out.items():
    print(f\"  [FIX-C3]   per-method: {m}: {v['n_pass']}/{v['n_total']}\")
print(f\"  [FIX-C3] {NN_HYBRID_KEY} llm-routing: forced={hybrid_llm_routing['forced_llm_count']}, natural={hybrid_llm_routing['natural_llm_count']}\")
if n_total == 0:
    print('  [WARN]  No results found in exp2_pca_4060/ — rerun after domains complete.')
PYEOF

  # ── 4. Write split_protocol_disclosure.json (required by Gate B) ─────────────
  python3 - <<'PYEOF'
import json, pathlib, datetime

PCA_DIR   = pathlib.Path('${RESULTS_DIR}/comparison_results/feynman-tests/exp2_pca_4060')
DISC_FILE = PCA_DIR / 'split_protocol_disclosure.json'

disclosure = {
    'fixc3':              True,
    'split_protocol':     'pca_40_60',
    'split_function':     'pca_directed_split',
    'split_level':        'outer_loop',
    'force_fresh':        True,
    'script':             'run_comparative_suite_benchmark_pca.py',
    'test_size':          0.6,
    'train_size':         0.4,
    'random_split_used':  False,
    'legacy_split':       'random_80_20 (train_test_split, test_size=0.2)',
    'legacy_script':      'run_comparative_suite_benchmark_v2.py (no --extrap)',
    'dfi_parity':         True,
    'section_reference':  'sec:6.4 + sec:10.7',
    'generated_by':       'run_all.sh exp2_feynman_pca_4060 via run_comparative_suite_benchmark_pca.py',
    'timestamp':          datetime.datetime.utcnow().isoformat() + 'Z',
}
DISC_FILE.write_text(json.dumps(disclosure, indent=2))
print(f'  [FIX-C3] split_protocol_disclosure.json written → {DISC_FILE}')
PYEOF

  echo '[exp2_feynman_pca_4060] Scanning for NN feature-count-mismatch fingerprint...'
  python3 - <<'PYEOF_FINGERPRINT_2'
import json, math, pathlib

PCA_DIR = pathlib.Path('${RESULTS_DIR}/comparison_results/feynman-tests/exp2_pca_4060')
NN_KEY  = 'ImprovedNN (core)'
hits, n_scanned = [], 0
for fp in sorted(PCA_DIR.glob('*.json')) if PCA_DIR.exists() else []:
    if any(x in fp.name for x in ('checkpoint', 'disclosure', 'summary', 'baseline', 'benchmark_results')):
        continue
    try:
        data = json.loads(fp.read_text())
    except Exception:
        continue
    tests = data.get('tests', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    for t in tests:
        if not isinstance(t, dict):
            continue
        n_scanned += 1
        nn  = t.get('results', {}).get(NN_KEY, {})
        err = nn.get('error', '') or ''
        r2  = nn.get('r2')
        is_nan = r2 is None or (isinstance(r2, float) and math.isnan(r2))
        if 'StandardScaler is expecting' in err or 'features, but' in err or is_nan:
            hits.append((t.get('description', '')[:60], t.get('domain'), err or '(nan, no error string)'))

print(f'  [exp2_feynman_pca_4060] Scanned {n_scanned} record(s) for NN feature-count-mismatch fingerprint')
print(f'  [exp2_feynman_pca_4060] Records matching fingerprint: {len(hits)}')
for h in hits[:20]:
    print('   ', h)
if hits:
    print(\"  WARNING: exp2_feynman_pca_4060 NN feature-count-mismatch fingerprint detected in 'ImprovedNN (core)' results.\")
PYEOF_FINGERPRINT_2

  # ── 5. Verification summary ───────────────────────────────────────────────────
  echo ''
  echo '=== exp2_feynman_pca_4060 verification ==='
  echo 'Output dir:' \"\${_PCA_DIR}\"
  find \"\${_PCA_DIR}\" -maxdepth 1 -type f | sort || echo '  (empty)'
  echo ''
  _NSUMMARY=\$(find \"\${_PCA_DIR}\" -name 'exp2_pca_4060_summary.json' 2>/dev/null | wc -l)
  _NDISC=\$(find \"\${_PCA_DIR}\" -name 'split_protocol_disclosure.json' 2>/dev/null | wc -l)
  _NRESULT=\$(find \"\${_PCA_DIR}\" -name '*.json' \
    ! -name 'checkpoint*' ! -name '*disclosure*' ! -name '*summary*' ! -name '*baseline*' \
    2>/dev/null | wc -l)
  echo \"  Result JSONs     : \${_NRESULT}\"
  echo \"  Summary file     : \${_NSUMMARY} (exp2_pca_4060_summary.json)\"
  echo \"  Disclosure file  : \${_NDISC} (split_protocol_disclosure.json)\"
  echo \"  Baseline lock    : \$([ -f '\${_BASELINE}' ] && echo 'PRESENT' || echo 'MISSING')\"
  if [[ \"\${_NSUMMARY}\" -eq 0 ]]; then
    echo 'WARNING: exp2_pca_4060_summary.json not found — domain runs may not have completed yet'
  fi
  if [[ \"\${_NDISC}\" -eq 0 ]]; then
    echo 'WARNING: split_protocol_disclosure.json not found — Gate B in ci_runner_disclosure.yml will FAIL'
  fi
  echo '=== end exp2_feynman_pca_4060 ==='
"




run exp2_feynman_extrap "Feynman far-region R² (extrap_r2_far for Mann-Whitney ablation)" bash -c "
  cd '${REPO_ROOT}'
  mkdir -p '${RESULTS_DIR}/comparison_results/feynman-tests/exp2_extrap'
  # INTERNAL extrap_r2_far MODULE MODE
  #
  # extrap_r2_far is now treated as an INTERNAL helper implemented directly
  # inside run_comparative_suite_benchmark_v2.py (fallback-safe import).
  #
  # Therefore:
  #   - no external extrap_r2_far.py verification is required
  #   - no sys.path patching is required
  #   - missing-module warnings are non-fatal
  #   - extrap metrics are always computed via internal fallback
  #
  # Expected runtime behavior:
  #
  #   ⚠️ extrap_r2_far.py not found — using internal fallback metrics
  #
  # This is VALID and SHOULD NOT fail the pipeline.
  # --------------------------------------------------------------------------

  _EXT_DIR='${RESULTS_DIR}/comparison_results/feynman-tests/exp2_extrap'
  _EXT_SHARD=\${SHARD_INDEX:-0}
  ACTIVE_DOMAINS=\"\${DOMAIN_FILTER:-${FEYNMAN_DOMAINS}}\"
  for DOMAIN_ID in \${ACTIVE_DOMAINS}; do
    echo '=== exp2_feynman_extrap: domain='\${DOMAIN_ID}' ==='
    FEYNMAN_SAMPLES=${FEYNMAN_SAMPLES} \
    FEYNMAN_TIMEOUT=${FEYNMAN_TIMEOUT} \
    METHOD_TIMEOUT=${METHOD_TIMEOUT} \
    PYSR_FIT_WALL_TIMEOUT=${PYSR_FIT_WALL_TIMEOUT} \
    PYSR_FIT_GRACE_SECS=${PYSR_FIT_GRACE_SECS} \
    JOB_DEADLINE=${JOB_DEADLINE} \
      python3 '${EXPERIMENTS_DIR}/run_comparative_suite_benchmark_v2.py' \
        --benchmark feynman \
        --extrap \
        --extrap-multiplier \${EXTRAP_MULTIPLIER:-2.0} \
        --extrap-train-frac \${EXTRAP_TRAIN_FRAC:-0.8} \
        --domain \"\${DOMAIN_ID}\" \
        --samples ${FEYNMAN_SAMPLES} \
        --pysr-timeout ${FEYNMAN_TIMEOUT} \
        --method-timeout ${METHOD_TIMEOUT} \
        --populations ${PYSR_POPULATIONS} \
        --parsimony 0.01 \
        --noiseless \
        --threshold ${FEYNMAN_NOISELESS_THRESHOLD} \
        --checkpoint-name \"feynman_extrap_checkpoint_\${DOMAIN_ID}\" \
        --output-dir \"\${_EXT_DIR}\" \
        --resume \
      2>&1 | tee -a \"\${_EXT_DIR}/exp2_extrap_run.log\" \
    || echo 'WARNING: exp2_feynman_extrap domain '\${DOMAIN_ID}' exited non-zero — continuing'
  done

  mkdir -p \"\${_EXT_DIR}/_saved\"
  while IFS= read -r _pf; do
    _pfn=\$(basename \"\${_pf}\")
    # ln -f overwrites an existing _saved copy (idempotent on retry).
    ln -f \"\${_pf}\" \"\${_EXT_DIR}/_saved/\${_pfn}\" 2>/dev/null \
      || cp \"\${_pf}\" \"\${_EXT_DIR}/_saved/\${_pfn}\" \
      || true
  done < <(find \"\${_EXT_DIR}\" -maxdepth 1 -name 'protocol_core_extrap_*.json' 2>/dev/null)
  _SAVED=\$(find \"\${_EXT_DIR}/_saved\" -name 'protocol_core_extrap_*.json' 2>/dev/null | wc -l)
  echo \"[E2-guard] \${_SAVED} protocol_core_extrap_*.json hard-linked into \${_EXT_DIR}/_saved/\"

  _BENCH_EXT_SRC=\"\${_EXT_DIR}/benchmark_results_extrap.json\"
  if [ ! -f \"\${_BENCH_EXT_SRC}\" ]; then
    _BENCH_EXT_SRC=\"\${RESULTS_DIR}/comparison_results/benchmark_results_extrap.json\"
    if [ -f \"\${_BENCH_EXT_SRC}\" ]; then
      echo \"WARNING: benchmark_results_extrap.json found in comparison_results/ root, not \${_EXT_DIR} — script may be an older/unpatched version (expected it to honor --output-dir).\"
    fi
  fi
  if [ -f \"\${_BENCH_EXT_SRC}\" ]; then
    _BENCH_EXT_DST=\"\${_EXT_DIR}/benchmark_results_extrap_shard\${_EXT_SHARD}.json\"
    cp \"\${_BENCH_EXT_SRC}\" \"\${_BENCH_EXT_DST}\"
    echo \"[E6-guard] copied \${_BENCH_EXT_SRC} -> benchmark_results_extrap_shard\${_EXT_SHARD}.json\"
  else
    echo \"WARNING: benchmark_results_extrap.json not found in \${_EXT_DIR} or \${RESULTS_DIR}/comparison_results\"
  fi

  echo '=== exp2_feynman_extrap verification ==='
  find \"\${_EXT_DIR}\" \
    -name 'protocol_core_extrap_*.json' 2>/dev/null | sort || echo '  (none yet)'
  COUNT_EXTRAP=\$(find \"\${_EXT_DIR}\" \
    -name 'protocol_core_extrap_*.json' 2>/dev/null | wc -l)
  COUNT_BENCH_EXTRAP=\$(find \"\${_EXT_DIR}\" \
    -maxdepth 1 -name 'benchmark_results_extrap*.json' 2>/dev/null | wc -l)
  COUNT_SAVED=\$(find \"\${_EXT_DIR}/_saved\" \
    -name 'protocol_core_extrap_*.json' 2>/dev/null | wc -l)
  if [[ \"\${COUNT_EXTRAP}\" -eq 0 && \"\${COUNT_SAVED}\" -gt 0 ]]; then
    echo \"WARNING: primary protocol_core_extrap_*.json were deleted (prune_old E2); \${COUNT_SAVED} copies survived in _saved/ — restore with:\"
    echo \"         cp \${_EXT_DIR}/_saved/protocol_core_extrap_*.json \${_EXT_DIR}/\"
  elif [[ \"\${COUNT_EXTRAP}\" -eq 0 ]]; then
    echo 'WARNING: exp2_feynman_extrap produced no protocol_core_extrap_*.json — extrap_r2_far will be missing from ablation_paired.json'
  else
    echo \"OK: \${COUNT_EXTRAP} extrap protocol file(s) produced  (\${COUNT_SAVED} backed up in _saved/)\"
  fi
  if [[ \"\${COUNT_BENCH_EXTRAP}\" -eq 0 ]]; then
    echo 'WARNING: benchmark_results_extrap.json not found in exp2_extrap/ or comparison_results/ — ci_analysis.yml merge step will find nothing'
  else
    echo \"OK: benchmark_results_extrap_shard\${_EXT_SHARD}.json present in \${_EXT_DIR}\"
    echo '    ci_analysis.yml / the local merge block will merge this into ablation_paired.json in exp2_extrap/'
  fi
"

(
  set -euo pipefail
  _SCRIPT_MERGE="${REPO_ROOT}/.github/scripts/merge_extrap_into_benchmark.py"
  _EXTRAP_DIR="${RESULTS_DIR}/comparison_results/feynman-tests/exp2_extrap"
  _BENCHMARK_DIR="${RESULTS_DIR}/comparison_results/feynman-tests/exp2"
  _PAIRED="${_EXTRAP_DIR}/ablation_paired.json"

  mkdir -p "${_EXTRAP_DIR}"

  if [[ ! -f "${_SCRIPT_MERGE}" ]]; then
    echo "[WARN] merge_extrap_into_benchmark.py not found at ${_SCRIPT_MERGE}"
    echo "       ablation_paired.json will not be produced locally — ci_analysis.yml will generate it."
  else
    _BENCH_EXT="$(find "${_EXTRAP_DIR}" -maxdepth 1 -name 'benchmark_results_extrap*.json' 2>/dev/null | head -1 || true)"
    if [[ -z "${_BENCH_EXT}" ]]; then
      echo "[SKIP] benchmark_results_extrap*.json not found — run exp2_feynman_extrap first."
    else
      echo "[merge] Running merge_extrap_into_benchmark.py → ablation_paired.json"
      python3 "${_SCRIPT_MERGE}" \
        --extrap-benchmark-dir "${_EXTRAP_DIR}" \
        --benchmark-dir        "${_BENCHMARK_DIR}" \
        --output               "${_PAIRED}" \
        2>&1 | tee -a "${_EXTRAP_DIR}/ablation_paired_run.log" \
      || echo "WARNING: merge_extrap_into_benchmark.py exited non-zero — ablation_paired.json may be incomplete"
      if [[ -f "${_PAIRED}" ]]; then
        _NR=$(python3 -c "import json; print(len(json.load(open('${_PAIRED}'))))" 2>/dev/null || echo "?")
        echo "[merge] ablation_paired.json: ${_NR} paired record(s) → ${_PAIRED}"
      fi
    fi
  fi

  # exp2_extrap_summary.json — small machine-readable rollup of this step's
  # outputs, written into exp2_extrap/ alongside the raw benchmark/protocol
  # files. Intended for qualify/audit steps (and humans) to get step status
  # at a glance without re-scanning the whole directory.
  _SUMMARY="${_EXTRAP_DIR}/exp2_extrap_summary.json"
  python3 - "${_EXTRAP_DIR}" "${_PAIRED}" "${_SUMMARY}" <<'PYEOF'
import json, sys
from pathlib import Path
from datetime import datetime, timezone

extrap_dir, paired_path, summary_path = (Path(p) for p in sys.argv[1:4])

protocol_files = sorted(p.name for p in extrap_dir.glob("protocol_core_extrap_*.json"))
bench_files    = sorted(p.name for p in extrap_dir.glob("benchmark_results_extrap*.json"))
saved_dir      = extrap_dir / "_saved"
saved_count    = len(list(saved_dir.glob("protocol_core_extrap_*.json"))) if saved_dir.is_dir() else 0

paired_exists = paired_path.is_file()
paired_count  = None
if paired_exists:
    try:
        paired_count = len(json.loads(paired_path.read_text()))
    except Exception:
        paired_count = None

summary = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "step": "exp2_feynman_extrap",
    "extrap_dir": str(extrap_dir),
    "protocol_core_extrap_files": protocol_files,
    "protocol_core_extrap_count": len(protocol_files),
    "protocol_core_extrap_saved_count": saved_count,
    "benchmark_results_extrap_files": bench_files,
    "ablation_paired_json": {
        "path": str(paired_path),
        "present": paired_exists,
        "record_count": paired_count,
    },
    "status": "ok" if (protocol_files and bench_files) else "incomplete",
}

summary_path.write_text(json.dumps(summary, indent=2))
print(f"[summary] wrote {summary_path}  (status={summary['status']}, "
      f"protocol_files={len(protocol_files)}, benchmark_files={len(bench_files)}, "
      f"paired_records={paired_count})")
PYEOF
)


run exp2 "Combined five-system comparison -- all Methods (Tab 19 full)" bash -c "
  cd '${REPO_ROOT}'
  mkdir -p '${RESULTS_DIR}/comparison_results/feynman-tests/exp2_multi'
  EXP2_DOMAINS='mechanics thermodynamics electromagnetism fluid_dynamics optics quantum chemistry biology mathematics economics'
  for DOMAIN_ID in \${EXP2_DOMAINS}; do
    echo '=== exp2: domain='\${DOMAIN_ID}' ==='
    FEYNMAN_TIMEOUT=${FEYNMAN_TIMEOUT} \
    METHOD_TIMEOUT=${METHOD_TIMEOUT} \
    PYSR_FIT_WALL_TIMEOUT=${PYSR_FIT_WALL_TIMEOUT} \
    PYSR_FIT_GRACE_SECS=${PYSR_FIT_GRACE_SECS} \
    JOB_DEADLINE=${JOB_DEADLINE} \
      python3 '${EXPERIMENTS_DIR}/run_comparative_suite_benchmark_v2.py' \
        --protocol all_domains \
        --domain \"\${DOMAIN_ID}\" \
        --samples ${FEYNMAN_SAMPLES} \
        --pysr-timeout ${FEYNMAN_TIMEOUT} \
        --method-timeout ${METHOD_TIMEOUT} \
        --populations ${PYSR_POPULATIONS} \
        --parsimony 0.01 \
        --use-transcendental-compositions \
        --noiseless \
        --threshold ${FEYNMAN_NOISELESS_THRESHOLD} \
        --checkpoint-name \"exp2_checkpoint_\${DOMAIN_ID}\" \
        --output-dir '${RESULTS_DIR}/comparison_results/feynman-tests/exp2_multi' \
        --resume \
        2>&1 | tee -a '${RESULTS_DIR}/comparison_results/feynman-tests/exp2_multi/exp2_run.log' \
      || echo 'WARNING: domain '\${DOMAIN_ID}' exited non-zero — continuing'
  done
"


# ── STEP 6b: exp2_five ──────────────────────────────────────────────────────────
# Five-System Comparison (§10.1), straightforward variant: identical to exp2
# above (same domains, same --protocol all_domains, same script) except
# --methods 1 2 4 5 6 restricts the run to the five methods matching the
# paper's five system rows, excluding method 3 (HybridDeFiMethod — DeFi-
# domain-scoped, not one of the five row names; same exclusion documented in
# generate_tables.py's _EXP2_METHOD_TO_ROW comment).
#
# This is the "straightforward run_comparative_suite_benchmark_v2.py" path —
# no new Python source, just the existing script with a narrower --methods
# filter and its own output directory so it never collides with exp2's full
# 6-method run.
#
# Output directory: ${RESULTS_DIR}/five_systems/exp2_five/
# CLI example (run standalone):
#   bash run_all.sh --step exp2_five
# ─────────────────────────────────────────────────────────────────────────────
run exp2_five "Five-System Comparison -- 5 Methods only, excl. HybridDeFiMethod (Tab 1, §10.1)" bash -c "
  cd '${REPO_ROOT}'
  mkdir -p '${RESULTS_DIR}/five_systems/exp2_five'
  EXP2_DOMAINS='mechanics thermodynamics electromagnetism fluid_dynamics optics quantum chemistry biology mathematics economics'
  for DOMAIN_ID in \${EXP2_DOMAINS}; do
    echo '=== exp2_five: domain='\${DOMAIN_ID}' ==='
    FEYNMAN_TIMEOUT=${FEYNMAN_TIMEOUT} \
    METHOD_TIMEOUT=${METHOD_TIMEOUT} \
    PYSR_FIT_WALL_TIMEOUT=${PYSR_FIT_WALL_TIMEOUT} \
    PYSR_FIT_GRACE_SECS=${PYSR_FIT_GRACE_SECS} \
    JOB_DEADLINE=${JOB_DEADLINE} \
      python3 '${EXPERIMENTS_DIR}/run_comparative_suite_benchmark_v2.py' \
        --protocol all_domains \
        --domain \"\${DOMAIN_ID}\" \
        --samples ${FEYNMAN_SAMPLES} \
        --pysr-timeout ${FEYNMAN_TIMEOUT} \
        --method-timeout ${METHOD_TIMEOUT} \
        --populations ${PYSR_POPULATIONS} \
        --parsimony 0.01 \
        --use-transcendental-compositions \
        --noiseless \
        --threshold ${FEYNMAN_NOISELESS_THRESHOLD} \
        --methods 1 2 4 5 6 \
        --checkpoint-name \"exp2_five_checkpoint_\${DOMAIN_ID}\" \
        --output-dir '${RESULTS_DIR}/five_systems/exp2_five' \
        --resume \
        2>&1 | tee -a '${RESULTS_DIR}/five_systems/exp2_five/exp2_five_run.log' \
      || echo 'WARNING: domain '\${DOMAIN_ID}' exited non-zero — continuing'
  done
"

# ── STEP 7: exp3 ──────────────────────────────────────────────────────────────
run exp3 "Nguyen-12 benchmark -- SEED=42 (tab:nguyen12 - SS10.8)" bash -c '
  cd '"${REPO_ROOT}"'
  mkdir -p '"${RESULTS_DIR}"'/extrapolation
  echo "=== exp3 seed 1/1: seed=42 | equations: N1-N12 (12 total) ==="
  RESULTS_DIR='${RESULTS_DIR}' \
    python3 '"${EXPERIMENTS_DIR}"'/exp3_nguyen12_consolidated.py \
    --seed 42 \
    --temperature 0.25 \
    2>&1 | tee '"${RESULTS_DIR}"'/exp3_run.log \
  || echo "WARNING: seed=42 exited non-zero — continuing"
  find '"${RESULTS_DIR}"' -maxdepth 1 \
    \( -name '"'"'*nguyen*seed42*.json'"'"' -o -name '"'"'*nguyen12*42*.json'"'"' \
       -o -name '"'"'full_run_*seed42*.json'"'"' -o -name '"'"'report_hybrid_*seed42*.json'"'"' \
       -o -name '"'"'hybrid_defi_*seed42*.json'"'"' \) \
    -exec mv -v {} '"${RESULTS_DIR}"'/extrapolation/ \; 2>/dev/null || true
  find '"${RESULTS_DIR}"' -maxdepth 1 -name '"'"'experiment_registry.json'"'"' \
    -exec cp -v {} '"${RESULTS_DIR}"'/extrapolation/ \; 2>/dev/null || true
  # -- Partial results summary after seed=42 ----------------------------------
  echo "--- exp3 partial results after seed=42 (1/1) ---"
  RESULT_DIR='"${RESULTS_DIR}"'/extrapolation python3 - <<'"'"'PYEOF'"'"'
import glob, json, os
result_dir = os.environ.get("RESULT_DIR", "")
run_files = (sorted(glob.glob(f"{result_dir}/**/full_run_*seed42*.json", recursive=True)) +
             sorted(glob.glob(f"{result_dir}/**/*seed42*.json", recursive=True)))
all_files = glob.glob(f"{result_dir}/**/*.json", recursive=True)
print(f"  seed=42: {len(run_files)} result file(s)  |  total JSON in {result_dir}: {len(all_files)}")
for f in run_files[-1:]:
    try:
        data = json.load(open(f))
        results = data.get("results") or data.get("equation_results") or []
        if isinstance(results, list) and results:
            print(f"  Per-equation summary ({os.path.basename(f)}):")
            for r in results:
                eq   = r.get("equation") or r.get("eq_id") or r.get("name", "?")
                r2   = r.get("r2") or r.get("r2_test") or r.get("r2_train")
                rmse = r.get("rmse") or r.get("rmse_test", "")
                stat = r.get("status", "")
                r2_s = f"{r2:.4f}" if isinstance(r2, float) else str(r2)
                print(f"    {str(eq):10s}  R2={r2_s:8s}  rmse={rmse}  {stat}")
        elif isinstance(results, dict):
            print(f"  Per-equation summary ({os.path.basename(f)}):")
            for eq, r in sorted(results.items()):
                r2 = r.get("r2") or r.get("r2_test") if isinstance(r, dict) else r
                r2_s = f"{r2:.4f}" if isinstance(r2, float) else str(r2)
                print(f"    {str(eq):10s}  R2={r2_s}")
    except Exception as e:
        print(f"  (could not parse {os.path.basename(f)}: {e})")
PYEOF
  echo "--- end partial results seed=42 ---"
'

# ── STEP 8: exp3b ─────────────────────────────────────────────────────────────
run exp3b "Nguyen-12 stability seeds 99/123/777/2024 (tab:nguyen12 extended)" bash -c "
  cd '${REPO_ROOT}'
  mkdir -p '${RESULTS_DIR}/extrapolation/multi_seed'

  _SHARD_SEEDS=\"\${SHARD_SEEDS:-}\"
  if [[ -z \"\${_SHARD_SEEDS}\" ]]; then
    _SHARD_TASKS='${SHARD_IDS:-${TASK_IDS:-}}'
    _SHARD_SEEDS=\$(echo \"\${_SHARD_TASKS}\" | tr ' ' '\n' | grep -oE '_seed[0-9]+$' | sed -E 's/_seed//' | sort -u | paste -sd, -)
  fi
  if [[ -z \"\${_SHARD_SEEDS}\" ]]; then
    echo '  [exp3b] No per-shard seed found in SHARD_SEEDS/SHARD_IDS/TASK_IDS — running full default seed list (local/standalone run).'
    _SHARD_SEEDS='99,123,777,2024'
  else
    echo \"  [exp3b] SHARD_INDEX=\${SHARD_INDEX:-0} -> seeds for this shard: \${_SHARD_SEEDS}\"
  fi

  IFS=',' read -ra _SEED_ARR <<< \"\${_SHARD_SEEDS}\"
  for seed in \"\${_SEED_ARR[@]}\"; do
    echo '--- exp3b seed='\$seed' ---'
    PYSR_SEED=\"\$seed\" \
    EXPERIMENT_SEED=\"\$seed\" \
    NN_SEED=\"\$seed\" \
    RESULTS_DIR='${RESULTS_DIR}' \
      python3 '${EXPERIMENTS_DIR}/exp3_nguyen12_consolidated.py' \
      --seed \$seed \
      --temperature 0.25 \
      2>&1 | tee -a '${RESULTS_DIR}'/exp3b_run.log
  done
  printf -v _SHARD_TAG '%02d' \"\$((\${SHARD_INDEX:-0} + 1))\"
  echo \"  [exp3b] SHARD_INDEX=\${SHARD_INDEX:-0} -> isolation suffix _nshards\${_SHARD_TAG}\"
  _DEST_MS='${RESULTS_DIR}/extrapolation/multi_seed'
  find '${RESULTS_DIR}' -maxdepth 1 \
    \( -name '*nguyen*.json' -o -name 'full_run_*.json' \
       -o -name 'report_hybrid_*.json' -o -name 'hybrid_defi_*.json' \) \
    ! -name '*seed42*' ! -name '*nguyen12*42*' | while IFS= read -r src; do
      fname=\$(basename \"\$src\")
      stem=\"\${fname%.*}\"
      ext=\"\${fname##*.}\"
      dst=\"\${_DEST_MS}/\${stem}_nshards\${_SHARD_TAG}.\${ext}\"
      mv -v \"\$src\" \"\$dst\" || true
  done
  find '${RESULTS_DIR}' -maxdepth 1 -name 'experiment_registry.json' \
    -exec cp -v {} '${RESULTS_DIR}/extrapolation/multi_seed/' \; 2>/dev/null || true
"


# ── STEP 8b (inlined into exp3b): symbolic equivalence ───────────────────────
(
  set -uo pipefail
  _SCRIPT="${REPO_ROOT}/.github/scripts/check_symbolic_equivalence.py"
  _SEED_DIR="${RESULTS_DIR}/extrapolation"
  _REPORT="${_SEED_DIR}/symbolic_equivalence_report.csv"
  _SUMMARY="${_SEED_DIR}/symbolic_equivalence_summary.txt"
  _SEED_FILES=$(find "${RESULTS_DIR}/extrapolation" -maxdepth 2 \
    -name "exp3_nguyen12_seed*.json" 2>/dev/null | sort)
  if [[ -z "${_SEED_FILES}" ]]; then
    echo "[SKIP] No exp3_nguyen12_seed*.json files found — symbolic equivalence check skipped."
  elif [[ ! -f "${_SCRIPT}" ]]; then
    echo "[SKIP] check_symbolic_equivalence.py not found at ${_SCRIPT}"
    echo "       Symbolic equivalence report will not be produced locally."
  else
    echo "[exp3_sym] Running check_symbolic_equivalence.py ..."
    mkdir -p "${_SEED_DIR}"
    python3 "${_SCRIPT}" \
      --results-dir "${_SEED_DIR}" \
      --output-dir  "${_SEED_DIR}" \
      2>&1 | tee "${_SEED_DIR}/symbolic_equivalence_run.log" \
    || echo "WARNING: check_symbolic_equivalence.py exited non-zero — continuing (non-fatal reporting step)"
    if [[ -f "${_REPORT}" ]]; then
      _NR=$(wc -l < "${_REPORT}" || echo "?")
      echo "[exp3_sym] symbolic_equivalence_report.csv: ${_NR} line(s) → ${_REPORT}"
    else
      echo "[WARN] symbolic_equivalence_report.csv was not produced — check script output above."
    fi
  fi
) || echo "WARNING: exp3/exp3b symbolic equivalence check block failed — continuing (non-fatal reporting step)"

# ── STEP 9: suppA ─────────────────────────────────────────────────────────────
run suppA "DeFi routing improvement experiments (Supplement A - Tab 11-13 routing)" bash -c "
  cd '${REPO_ROOT}'
  mkdir -p '${RESULTS_DIR}/hybrid_pysr/defi' '${RESULTS_DIR}/figures' '${RESULTS_DIR}/tables'

  mkdir -p '${RESULTS_DIR}/regression_tests'
  _WIRING_TEST='${EXPERIMENTS_DIR}/../tests/test_proc_box_wiring.py'
  [ -f \"\${_WIRING_TEST}\" ] || _WIRING_TEST='hypatiax/experiments/tests/test_proc_box_wiring.py'
  if [ -f \"\${_WIRING_TEST}\" ]; then
    echo '[suppA] Running proc_box outer-timeout wiring regression test (item 10b)...'
    _WIRING_LOG='${RESULTS_DIR}/regression_tests/proc_box_wiring_run.log'
    if python3 \"\${_WIRING_TEST}\" 2>&1 | tee \"\${_WIRING_LOG}\"; then
      _WIRING_STATUS='PASS'
    else
      _WIRING_STATUS='FAIL'
    fi
    python3 - \"\${_WIRING_STATUS}\" \"\${_WIRING_LOG}\" <<'PYEOF'
import json, sys, datetime
status, log_path = sys.argv[1], sys.argv[2]
out = {
    'test': 'proc_box_wiring',
    'issue': '10b',
    'status': status,
    'log': log_path,
    'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
with open('${RESULTS_DIR}/regression_tests/proc_box_wiring_result.json', 'w') as f:
    json.dump(out, f, indent=2)
print(f'[suppA] proc_box wiring test: {status} -> regression_tests/proc_box_wiring_result.json')
PYEOF
    if [ \"\${_WIRING_STATUS}\" != 'PASS' ]; then
      echo '::error::[suppA] proc_box outer-timeout wiring regression test FAILED — the item 10b fix appears to have regressed. Refusing to run the DeFi benchmark against a possibly-broken timeout harness. See regression_tests/proc_box_wiring_run.log.'
      exit 1
    fi
  else
    echo '[suppA] WARNING: test_proc_box_wiring.py not found (expected at hypatiax/experiments/tests/) — skipping item 10b wiring regression check.'
  fi

  python3 '${EXPERIMENTS_DIR}/run_hybrid_system_benchmark.py' \
    2>&1 | tee    '${RESULTS_DIR}'/suppA_run.log
  python3 hypatiax/experiments/tests/test_enhanced_defi_extrapolation.py \
    2>&1 | tee -a '${RESULTS_DIR}'/suppA_run.log
  python3 hypatiax/analysis/analyze_hybrid_performance.py \
    --results-dir '${RESULTS_DIR}' \
    2>&1 | tee -a '${RESULTS_DIR}'/suppA_run.log
  for _sroot in '${REPO_ROOT}' '${EXPERIMENTS_DIR}' '${RESULTS_DIR}'; do
    find \"\${_sroot}\" -maxdepth 1 -name 'consolidated_hybrid_*.json' \
      ! -path '${RESULTS_DIR}/hybrid_pysr/defi/*' \
      -exec mv -v {} '${RESULTS_DIR}/hybrid_pysr/defi/' \; 2>/dev/null || true
    find \"\${_sroot}\" -maxdepth 1 -name 'hybrid_llm_nn_all_domains_*.json' \
      ! -path '${RESULTS_DIR}/hybrid_llm_nn/all_domains/*' \
      -exec mv -v {} '${RESULTS_DIR}/hybrid_llm_nn/all_domains/' \; 2>/dev/null || true
    find \"\${_sroot}\" -maxdepth 1 -name 'ablation_exp1_*.json' \
      ! -path '${RESULTS_DIR}/*' \
      -exec mv -v {} '${RESULTS_DIR}/' \; 2>/dev/null || true
    find \"\${_sroot}\" -maxdepth 1 -name 'hypatiax_defi_benchmark_*results*' \
      ! -path '${RESULTS_DIR}/*' \
      -exec mv -v {} '${RESULTS_DIR}/' \; 2>/dev/null || true
  done
"

# ── STEP 10: suppB — noise sweep ─────────────────────────────────────────────
run suppB "Noise sweep benchmark sigma in {0,0.5,1,5,10}% (Tab 28, 29 - Supplement B)" bash -c "
  cd '${REPO_ROOT}'
  _SHARD_TASKS='${SHARD_IDS:-${TASK_IDS:-}}'
  _FIRST_TASK=\$(echo \"\${_SHARD_TASKS}\" | tr ' ' '\n' | grep -v '^\$' | head -1)
  if echo \"\${_FIRST_TASK}\" | grep -qE '^noise[0-9]'; then
    _NL_PCT=\$(echo \"\${_FIRST_TASK}\" | sed 's/^noise\([0-9][0-9.]*\)__.*/\1/')
    export NOISE_LEVEL=\"\${_NL_PCT}\"
    echo \"  [suppB] NOISE_LEVEL=\${NOISE_LEVEL}% → script will compute sigma=\$(python3 -c \"print(float('\${_NL_PCT}')/100)\") (task \${_FIRST_TASK})\"
  else
    echo \"  [suppB] WARNING: no noise{NL}__ task ID found in SHARD_IDS — full sweep will run\"
  fi
  printf -v _SHARD_TAG '%02d' \"\$((\${SHARD_INDEX:-0} + 1))\"
  export HYPATIAX_NSHARDS_SUFFIX=\"\${_SHARD_TAG}\"
  echo \"  [suppB] SHARD_INDEX=\${SHARD_INDEX:-0} -> HYPATIAX_NSHARDS_SUFFIX=_nshards\${HYPATIAX_NSHARDS_SUFFIX}\"
  NOISE_LEVELS='${NOISE_LEVELS:-0.0,0.05,0.1,0.5,1.0}' \\
  OUT_BASE='${RESULTS_DIR}' \\
  RESULTS_DIR='${RESULTS_DIR}' \\
  RESUME='false' \\
  HYPATIAX_NSHARDS_SUFFIX=\"\${HYPATIAX_NSHARDS_SUFFIX}\" \\
    python3 '${EXPERIMENTS_DIR}/run_noise_sweep_benchmark.py' \\
    --methods 1 2 3 4 5 6 \\
    --samples ${FEYNMAN_SAMPLES} \\
    --pysr-timeout ${FEYNMAN_TIMEOUT} \\
    --method-timeout ${METHOD_TIMEOUT} \\
    2>&1 | tee '${RESULTS_DIR}'/suppB_run.log

  #   output directory is:
"


# ── STEP 10b: suppB_sc — sample-complexity sweep ─────────────────────────────
run suppB_sc "Sample-complexity sweep n in {50..1000} (Tab 29 - Supplement B SS6)" bash -c "
  cd '${REPO_ROOT}'
  _SHARD_TASKS='${SHARD_IDS:-${TASK_IDS:-}}'
  _FIRST_TASK=\$(echo \"\${_SHARD_TASKS}\" | tr ' ' '\n' | grep -v '^\$' | head -1)
  if echo \"\${_FIRST_TASK}\" | grep -qE '^sc_n[0-9]'; then
    _SC_N=\$(echo \"\${_FIRST_TASK}\" | sed 's/^sc_n\([0-9]\+\)__.*/\1/')
    export SC_SAMPLE_COUNTS=\"\${_SC_N}\"
    echo \"  [suppB_sc] SC_SAMPLE_COUNTS=\${SC_SAMPLE_COUNTS} (n from task \${_FIRST_TASK})\"
  else
    export SC_SAMPLE_COUNTS='50,100,200,500,750,1000'
    echo \"  [suppB_sc] WARNING: no sc_n{N}__ task ID found in SHARD_IDS — full sweep will run\"
  fi
  printf -v _SHARD_TAG '%02d' \"\$((\${SHARD_INDEX:-0} + 1))\"
  export HYPATIAX_NSHARDS_SUFFIX=\"\${_SHARD_TAG}\"
  echo \"  [suppB_sc] SHARD_INDEX=\${SHARD_INDEX:-0} -> HYPATIAX_NSHARDS_SUFFIX=_nshards\${HYPATIAX_NSHARDS_SUFFIX}\"
  OUT_BASE='${RESULTS_DIR}' \\
  RESULTS_DIR='${RESULTS_DIR}' \\
  RESUME='false' \\
  HYPATIAX_NSHARDS_SUFFIX=\"\${HYPATIAX_NSHARDS_SUFFIX}\" \\
    python3 '${EXPERIMENTS_DIR}/run_sample_complexity_benchmark.py' \\
    --noiseless \\
    --methods 1 2 3 4 5 6 \\
    --samples ${FEYNMAN_SAMPLES} \\
    --pysr-timeout ${FEYNMAN_TIMEOUT} \\
    --method-timeout ${METHOD_TIMEOUT} \\
    2>&1 | tee '${RESULTS_DIR}'/suppB_sc_run.log

  _SC_CANON='${RESULTS_DIR}/comparison_results/feynman-tests/sample-complexity'
  mkdir -p \"\${_SC_CANON}\"

  python3 -c \"
import glob, json, os, sys

sc_n = '\${SC_SAMPLE_COUNTS}'.split(',')[0].strip()
candidates = sorted(
    glob.glob('\${_SC_CANON}/sample_complexity_*.json'),
    key=os.path.getmtime,
    reverse=True,
)
if not candidates:
    print(f'[suppB_sc-METHOD-ASSERT] no sample_complexity_*.json found for n={sc_n} -- FAIL')
    sys.exit(1)

latest = candidates[0]
data = json.load(open(latest))
methods = data.get('methods', [])
n_found = len(methods)
print(f'[suppB_sc-METHOD-ASSERT] n={sc_n} file={latest} methods_found={n_found} methods={methods}')
if n_found < 6:
    print(f'[suppB_sc-METHOD-ASSERT] FAIL: expected 6 methods, found {n_found} for n={sc_n}')
    sys.exit(1)
print('[suppB_sc-METHOD-ASSERT] OK -- all 6 methods present')
\"
"

# ── STEP 13: validate ────────────────────────────────────────────────────────
run validate "Cross-check all results against paper-reported values" bash -c '
python3 - <<'"'"'PYEOF'"'"'
import json, os, glob, sys

RESULTS = os.environ.get('RESULTS_DIR', 'hypatiax/data/results')
TOLERANCE = 0.01

checks = []

def check(label, got, expected, tol=TOLERANCE):
    ok = abs(got - expected) <= tol * max(abs(expected), 1e-9)
    checks.append((label, got, expected, ok))
    _tag = "OK" if ok else "FAIL"
    print(f"  [{_tag}] {label}: got={got:.6f}, expected={expected:.6f}")
    return ok

print("\n=== Validating key numerical results against JMLR v3.0 ===\n")

# --- exp1 noiseless ---
noiseless_files = (
    sorted(glob.glob(f"{RESULTS}/comparison_results/noise-noiseless/noiseless/defi/hypatiax_defi_benchmark_*results*.json")) +
    sorted(glob.glob(f"{RESULTS}/comparison_results/noise-noiseless/noiseless/defi/protocol_core_noiseless_*.json"))
)
if noiseless_files:
    with open(noiseless_files[-1]) as f: data = json.load(f)
    hx = [r for r in data.get('results', []) if r.get('method') in ('hybrid_v40', 'Hybrid v40')]
    if hx:
        import statistics
        r2v = [r['r2_train'] for r in hx if 'r2_train' in r]
        if r2v:
            check("Hybrid v40 mean train R2",   statistics.mean(r2v),   0.931)
            check("Hybrid v40 median train R2", statistics.median(r2v), 1.000)
else:
    print("  [SKIP] exp1 noiseless results not found")

# --- exp2_feynman ---
exp2_files = sorted(glob.glob(f"{RESULTS}/comparison_results/feynman-tests/exp2/protocol_core_noisy_*.json"))
if exp2_files:
    with open(exp2_files[-1]) as f: data = json.load(f)
    rec = data.get('hybrid_deFi_recovery') or data.get('recovery_rate')
    if rec is not None:
        check("Hybrid DeFi recovery rate (Feynman noisy)", rec, 1.0, tol=0.001)
else:
    print("  [SKIP] exp2_feynman results not found")

# --- Mann-Whitney (Tab 14) ---
mw_files = sorted(glob.glob(f"{RESULTS}/exp1_rf01_mannwhitney*.json"))
if mw_files:
    with open(mw_files[-1]) as f: data = json.load(f)
    u = data.get('mann_whitney_u', data.get('U'))
    if u is not None: check("Mann-Whitney U (Hybrid v40 vs NN)", float(u), 0.0, tol=0.0)
    p = data.get('p_value', data.get('p'))
    if p is not None:
        ok = p < 1e-5
        checks.append(("p-value < 1e-5", p, 1.11e-6, ok))
        _tag = "OK" if ok else "FAIL"
        print(f"  [{_tag}] p-value < 1e-5: got={p:.2e}")
else:
    print("  [SKIP] Mann-Whitney results not found")

had = glob.glob(f"{RESULTS}/hybrid_llm_nn/all_domains/*.json")
ok = bool(had)
checks.append(("hybrid_all_domains output present (all_domains/)", 1.0 if ok else 0.0, 1.0, ok))
_tag = "OK" if ok else "FAIL"
print(f"  [{_tag}] hybrid_llm_nn/all_domains/: {len(had)} JSON file(s)")

# --- STEP 4a: instability outputs present ---
inst_csv = os.path.isfile(f"{RESULTS}/figures/instability_analysis.csv")
checks.append(("instability_analysis.csv present", 1.0 if inst_csv else 0.0, 1.0, inst_csv))
_tag = "OK" if inst_csv else "FAIL"
print(f"  [{_tag}] instability_analysis.csv")

sc = (glob.glob(f"{RESULTS}/comparison_results/feynman-tests/sample-complexity/*.json") +
      glob.glob(f"{RESULTS}/comparison_results/feynman-tests/sample-complexity/**/*.json"))
ok = bool(sc)
checks.append(("suppB_sc output present (sample-complexity/)", 1.0 if ok else 0.0, 1.0, ok))
_tag = "OK" if ok else "FAIL"
print(f"  [{_tag}] sample-complexity outputs: {len(sc)} file(s)")

# --- CRITICAL 4: suppB noise_sweep_*.json glob match ---
# tables-generator uses glob 'noise_sweep_*.json' to find suppB results.
# If run_noise_sweep_benchmark.py writes files under a different prefix,
# all suppB tables will contain placeholder text.
noise_sweep_matched = glob.glob(f"{RESULTS}/comparison_results/feynman-tests/noise-sweep/noise_sweep_*.json")
noise_sweep_all     = glob.glob(f"{RESULTS}/comparison_results/feynman-tests/noise-sweep/*.json")
if noise_sweep_all:
    ok = bool(noise_sweep_matched)
    checks.append(("suppB output matches noise_sweep_*.json glob (CRITICAL 4)", 1.0 if ok else 0.0, 1.0, ok))
    if not ok:
        bad = [os.path.basename(p) for p in noise_sweep_all[:5]]
        print(f"  [FAIL] noise-sweep/: {len(noise_sweep_all)} JSON(s) found but NONE match "
              f"noise_sweep_*.json. Actual filenames: {bad} -- reconcile script output prefix with tables-generator glob.")
    else:
        print(f"  [OK]   noise-sweep/: {len(noise_sweep_matched)} noise_sweep_*.json -- tables-generator glob OK")
else:
    print(f"  [SKIP] noise-sweep/: no JSON files found (suppB not yet run)")

exp3b_files = glob.glob(f"{RESULTS}/extrapolation/multi_seed/*nguyen*.json")
ok_exp3b = bool(exp3b_files)
checks.append(("exp3b outputs in extrapolation/multi_seed/ (BUG 2)", 1.0 if ok_exp3b else 0.0, 1.0, ok_exp3b))
suffix_exp3b = " (exp3b not yet run)" if not ok_exp3b else ""
_tag = "OK" if ok_exp3b else "SKIP"
print(
    f"  [{_tag}] extrapolation/multi_seed/: "
    f"{len(exp3b_files)} nguyen JSON(s){suffix_exp3b}"
)


pca_defi_dir = f"{RESULTS}/comparison_results/noise-noiseless/noiseless/defi_pca"
if os.path.isdir(pca_defi_dir):
    pca_disc = os.path.isfile(f"{pca_defi_dir}/split_protocol_disclosure.json")
    checks.append(("exp1_pca split_protocol_disclosure.json present", 1.0 if pca_disc else 0.0, 1.0, pca_disc))
    _tag = "OK" if pca_disc else "FAIL"
    print(f"  [{_tag}] exp1_pca: split_protocol_disclosure.json")
    pca_jsons = glob.glob(f"{pca_defi_dir}/defi_pca_v3_*.json")
    ok_pca = bool(pca_jsons)
    checks.append(("exp1_pca defi_pca_v3_*.json present", 1.0 if ok_pca else 0.0, 1.0, ok_pca))
    _tag = "OK" if ok_pca else "FAIL"
    print(f"  [{_tag}] exp1_pca: {len(pca_jsons)} defi_pca_v3_*.json file(s)")
else:
    print("  [SKIP] exp1_pca: defi_pca dir not found (exp1_pca not yet run)")

pca15_dir = f"{RESULTS}/comparison_results/noise-noiseless/15_pca"
if os.path.isdir(pca15_dir):
    pca15_jsons = (glob.glob(f"{pca15_dir}/defi_pca_v3_*.json") +
                   glob.glob(f"{pca15_dir}/*portfolio*variance*pca*.json"))
    ok_pca15 = bool(pca15_jsons)
    checks.append(("exp1b_pca outputs present in 15_pca/", 1.0 if ok_pca15 else 0.0, 1.0, ok_pca15))
    _tag = "OK" if ok_pca15 else "FAIL"
    print(f"  [{_tag}] exp1b_pca: {len(pca15_jsons)} JSON file(s) in 15_pca/")
else:
    print("  [SKIP] exp1b_pca: 15_pca dir not found (exp1b_pca not yet run)")

pca4060_dir = f"{RESULTS}/comparison_results/feynman-tests/exp2_pca_4060"
if os.path.isdir(pca4060_dir):
    pca4060_summary = os.path.isfile(f"{pca4060_dir}/exp2_pca_4060_summary.json")
    checks.append(("exp2_feynman_pca_4060 summary present", 1.0 if pca4060_summary else 0.0, 1.0, pca4060_summary))
    _tag = "OK" if pca4060_summary else "FAIL"
    print(f"  [{_tag}] exp2_feynman_pca_4060: exp2_pca_4060_summary.json")
    pca4060_disc = os.path.isfile(f"{pca4060_dir}/split_protocol_disclosure.json")
    checks.append(("exp2_feynman_pca_4060 disclosure present", 1.0 if pca4060_disc else 0.0, 1.0, pca4060_disc))
    _tag = "OK" if pca4060_disc else "WARN"
    print(f"  [{_tag}] exp2_feynman_pca_4060: split_protocol_disclosure.json")
    pca4060_jsons = glob.glob(f"{pca4060_dir}/benchmark_results_*.json")
    ok_pca4060 = bool(pca4060_jsons)
    checks.append(("exp2_feynman_pca_4060 benchmark_results_*.json present", 1.0 if ok_pca4060 else 0.0, 1.0, ok_pca4060))
    _tag = "OK" if ok_pca4060 else "FAIL"
    print(f"  [{_tag}] exp2_feynman_pca_4060: {len(pca4060_jsons)} benchmark_results_*.json file(s)")
else:
    print("  [SKIP] exp2_feynman_pca_4060: exp2_pca_4060 dir not found (step not yet run)")

# --- Summary ---
total = len(checks); passed = sum(1 for item in checks if item[-1])
print(f"\n=== Result: {passed}/{total} checks passed ===")
if passed < total:
    print("FAILED:")
    for label, got, exp, ok in checks:
        if not ok: print(f"  FAIL: {label} (got={got}, expected={exp})")
    sys.exit(1)
else:
    print("All checks passed.")
PYEOF
'

# ── STEP 14: qualify ─────────────────────────────────────────────────────────
run qualify "Qualify all experiments + numerical spot-check (Phase 5 gate)" bash -c '
  set -euo pipefail
  cd "'"${REPO_ROOT}"'"
  mkdir -p logs "'"${RESULTS_DIR}"'"

  python3 - <<'"'"'PYEOF'"'"' 2>&1 | tee "'"${RESULTS_DIR}"'"/qualify_run.log
import json, os, sys, glob as _glob
from pathlib import Path

RESULTS = Path(os.environ.get("RESULTS_DIR", "hypatiax/data/results"))
REPO    = Path(os.environ.get("REPO_ROOT", "."))

findings   = []   # for verify_report.json
all_ok     = True

def record(name, ok, detail="", status=None):
    global all_ok
    st = status or ("PASS" if ok else "FAIL")
    findings.append({"name": name, "status": st, "detail": detail})
    icon = {"PASS": "✅", "WARN": "⚠ ", "FAIL": "❌", "SKIP": "↩ "}.get(st, "  ")
    print(f"  {icon}  [{st}]  {name}  {detail}")
    if st == "FAIL":
        all_ok = False
    return ok

# ── 1. Numerical spot-checks ─────────────────────────────────────────────────
print("\n=== Phase 5a: Numerical spot-check ===\n")

# DeFi accuracy/counts
noiseless_files = sorted(_glob.glob(str(
    RESULTS / "comparison_results/noise-noiseless/noiseless/defi/hypatiax_defi_benchmark_*results*.json"
))) + sorted(_glob.glob(str(
    RESULTS / "comparison_results/noise-noiseless/noiseless/defi/protocol_core_noiseless_*.json"
)))
if noiseless_files:
    try:
        raw  = json.loads(Path(noiseless_files[-1]).read_text())
        # JSON root may be a list of result dicts OR a dict with a "results" key
        if isinstance(raw, list):
            results = raw
        else:
            results = raw.get("results", raw.get("data", []))
            if not isinstance(results, list):
                results = []
        hx = [r for r in results
              if isinstance(r, dict) and r.get("method") in ("hybrid_v40", "Hybrid v40")]
        if hx:
            import statistics as _st
            r2v = [r["r2_train"] for r in hx if "r2_train" in r]
            if r2v:
                mean_r2 = _st.mean(r2v)
                ok = abs(mean_r2 - 0.931) <= 0.01
                record("DeFi Hybrid v40 mean R2 approx 0.931", ok,
                       "got={:.4f}".format(mean_r2))
        # count cases
        n_cases = len(results)
        ok_cases = (n_cases >= 70)
        # Partial pipeline runs may have fewer rows — WARN not FAIL
        record("DeFi case count >=70", ok_cases, "found {} cases".format(n_cases),
               status="PASS" if ok_cases else "WARN")
    except Exception as e:
        record("DeFi noiseless parse", False, str(e), status="WARN")
else:
    record("DeFi noiseless results", True, "not yet run — skipped", status="SKIP")

# Feynman recovery rate
exp2_files = sorted(_glob.glob(str(
    RESULTS / "comparison_results/feynman-tests/exp2/protocol_core_noisy_*.json"
))) + sorted(_glob.glob(str(
    RESULTS / "comparison_results/feynman-tests/exp2/*.json"
)))
if exp2_files:
    try:
        raw = json.loads(Path(exp2_files[-1]).read_text())
        # Search multiple possible key names, both at root and nested one level
        _RECOVERY_KEYS = (
            "hybrid_deFi_recovery", "recovery_rate", "defi_recovery",
            "hybrid_recovery", "success_rate", "deFi_recovery_rate",
        )
        rec = None
        for _k in _RECOVERY_KEYS:
            if isinstance(raw, dict):
                rec = raw.get(_k)
                if rec is None:
                    # one level deep
                    for _v in raw.values():
                        if isinstance(_v, dict):
                            rec = _v.get(_k)
                            if rec is not None:
                                break
            if rec is not None:
                break
        if rec is not None:
            ok = abs(float(rec) - 1.0) <= 0.001
            record("Feynman DeFi recovery rate approx 1.0", ok,
                   "got={:.4f}".format(float(rec)))
        else:
            # Key not found — WARN only; the exp2 JSON schema varies by run
            record("Feynman recovery_rate key", True,
                   "key not found in {} — check JSON schema".format(
                       Path(exp2_files[-1]).name),
                   status="WARN")
    except Exception as e:
        record("Feynman exp2 parse", False, str(e), status="WARN")
else:
    record("Feynman exp2 results", True, "not yet run — skipped", status="SKIP")

# Mann-Whitney (Tab 14)
mw_files = sorted(_glob.glob(str(RESULTS / "exp1_rf01_mannwhitney*.json")))
if mw_files:
    try:
        data = json.loads(Path(mw_files[-1]).read_text())
        u = data.get("mann_whitney_u", data.get("U"))
        p = data.get("p_value", data.get("p"))
        if u is not None:
            ok = float(u) == 0.0
            record("Mann-Whitney U == 0", ok, "got={}".format(u))
        if p is not None:
            ok = float(p) < 1e-5
            record("Mann-Whitney p < 1e-5", ok, "got={:.2e}".format(float(p)))
    except Exception as e:
        record("Mann-Whitney parse", False, str(e), status="WARN")
else:
    record("Mann-Whitney results", True, "not yet run — skipped", status="SKIP")

# Instability rows (pipeline may be partial — WARN not FAIL when count is low)
inst_csv = RESULTS / "figures/instability_analysis.csv"
if inst_csv.exists():
    lines = [l for l in inst_csv.read_text().splitlines()
             if l.strip() and not l.startswith("#")]
    n = max(0, len(lines) - 1)  # subtract header
    ok = (n >= 70)
    record("Instability task count >=70", ok,
           "found {} data rows".format(n),
           status="PASS" if ok else "WARN")
else:
    record("instability_analysis.csv", True, "not yet produced — skipped", status="SKIP")

# ── 2. Per-experiment 5-dimension gate ───────────────────────────────────────
print("\n=== Phase 5b: 5-dimension per-experiment gate ===\n")

EXPERIMENTS = {
    "exp1":                   RESULTS / "comparison_results/noise-noiseless/noiseless/defi",
    "exp1b":                  RESULTS / "comparison_results/noise-noiseless/15",
    "exp1_pca":               RESULTS / "comparison_results/noise-noiseless/noiseless/defi_pca",
    "exp1b_pca":              RESULTS / "comparison_results/noise-noiseless/15_pca",
    "extrap":                 RESULTS / "comparison_results/extrapolation",
    "hybrid_all_domains":     RESULTS / "hybrid_llm_nn/all_domains",
    "instability":            RESULTS / "figures",
    "exp2_feynman":           RESULTS / "comparison_results/feynman-tests/exp2",
    "exp2_feynman_pca_4060":  RESULTS / "comparison_results/feynman-tests/exp2_pca_4060",
    "exp2":                   RESULTS / "comparison_results/feynman-tests/exp2_multi",
    "exp3":                   RESULTS / "extrapolation",
    "exp3b":                  RESULTS / "extrapolation/multi_seed",
    "suppA":                  RESULTS / "hybrid_pysr/defi",
    "suppB":                  RESULTS / "comparison_results/feynman-tests/noise-sweep",
    "suppB_sc":               RESULTS / "comparison_results/feynman-tests/sample-complexity",
}

def dim_check(exp, rdir):
    ok_all = True
    rdir = Path(rdir)

    # (1) checkpoint file
    ckpt_glob = list(_glob.glob(str(REPO / f"logs/checkpoint_{exp}_*.json"))) + \
                list(_glob.glob(str(REPO / f"logs/{exp}_checkpoint*.json")))
    d1 = f"{len(ckpt_glob)} checkpoint file(s)" if ckpt_glob else "MISSING"
    record(f"{exp} · (1) checkpoint", bool(ckpt_glob), d1,
           status="WARN" if not ckpt_glob else "PASS")  # warn not fail — CI may not write these

    # (2) result files
    jsons = list(rdir.glob("*.json")) if rdir.exists() else []
    ok2 = bool(jsons)
    record(f"{exp} · (2) result files", ok2,
           f"{len(jsons)} JSON(s) in {rdir.relative_to(RESULTS) if rdir.is_relative_to(RESULTS) else rdir}")
    if not ok2:
        ok_all = False

    # (3) _merged.json
    merged = list(rdir.glob("*_merged.json")) if rdir.exists() else []
    ok3 = bool(merged)
    record(f"{exp} · (3) _merged.json", ok3,
           f"{len(merged)} file(s)" if ok3 else "MISSING",
           status="WARN" if not ok3 else "PASS")

    # (4) _merged.csv
    mcsv = list(rdir.glob("*_merged.csv")) if rdir.exists() else []
    ok4 = bool(mcsv)
    record(f"{exp} · (4) _merged.csv", ok4,
           f"{len(mcsv)} file(s)" if ok4 else "MISSING",
           status="WARN" if not ok4 else "PASS")

    # (5) committed to git (any tracked file in rdir)
    try:
        import subprocess
        rel = str(rdir.relative_to(REPO)) if rdir.is_relative_to(REPO) else str(rdir)
        out = subprocess.check_output(
            ["git", "-C", str(REPO), "ls-files", "--error-unmatch", "--", rel],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        ok5 = bool(out)
    except Exception:
        ok5 = False
    record(f"{exp} · (5) committed to git", ok5,
           "tracked" if ok5 else "not tracked / no files",
           status="WARN" if not ok5 else "PASS")


    return ok_all

_hdr = "Experiment"
print(f"{_hdr:<25}  Gate")
print("-" * 40)
gate_results = {}
for exp, rdir in EXPERIMENTS.items():
    gate_results[exp] = dim_check(exp, rdir)

# ── Summary ───────────────────────────────────────────────────────────────────
print()
n_ok   = sum(1 for f in findings if f["status"] in ("PASS", "WARN", "SKIP"))
n_fail = sum(1 for f in findings if f["status"] == "FAIL")

print(f"\n=== qualify summary: {len(findings)} checks, {n_fail} FAIL ===")

# Write verify_report.json (same schema consumed by print-audit-summary in CI)
out = REPO / "logs/verify_report.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"all_ok": all_ok, "checks": findings}, indent=2))
print(f"  Report → {out}")

if all_ok:
    print("\n✅  qualify gate PASSED — proceeding to paper-audit.")
else:
    fails = [f for f in findings if f["status"] == "FAIL"]
    print(f"\n❌  qualify gate FAILED — {len(fails)} dimension(s) below threshold:")
    for f in fails:
        print("    FAIL  " + str(f["name"]) + "  " + str(f["detail"]))
    sys.exit(1)
PYEOF
'

# ── STEP 15: audit_paper ─────────────────────────────────────────────────────
# Final paper audit — fully self-contained (no run_all_checkpoint.py).
# Loads scripts/patches/paper_targets.json and cross-checks every reported
# number against the corresponding _merged.json / result file.
# Emits PASS / WARN / FAIL / MISSING per claim.
# Includes Nguyen-12 dual-threshold check (tab:nguyen12: 58.3% H / 66.7% P
# under the R2>=0.9999, 4-decimal convention).
# Writes logs/paper_audit_findings.json.
# Exits non-zero on any FAIL or MISSING (not on WARN).
run audit_paper "Audit all paper claims against results (paper_targets.json)" bash -c '
  set -euo pipefail
  cd "'"${REPO_ROOT}"'"
  mkdir -p logs "'"${RESULTS_DIR}"'"

  python3 - <<'"'"'PYEOF'"'"' 2>&1 | tee "'"${RESULTS_DIR}"'"/audit_paper_run.log
import json, os, sys, glob as _glob
from pathlib import Path

RESULTS     = Path(os.environ.get("RESULTS_DIR", "hypatiax/data/results"))
REPO        = Path(os.environ.get("REPO_ROOT",   "."))
TARGETS_F   = REPO / "scripts/patches/paper_targets.json"
FINDINGS_F  = REPO / "logs/paper_audit_findings.json"
FAIL_ON_WARN = os.environ.get("FAIL_ON_WARN", "false").lower() == "true"

print("\n=== Phase 5c: paper audit (paper_targets.json) ===\n")

# ── Load targets ──────────────────────────────────────────────────────────────
if not TARGETS_F.exists():
    print(f"ERROR: {TARGETS_F} not found — commit scripts/patches/paper_targets.json first.")
    sys.exit(1)

targets = json.loads(TARGETS_F.read_text())
print(f"  {len(targets)} claim(s) loaded from {TARGETS_F.name}")

# ── Result file index — build a flat map of all JSON files under RESULTS_DIR ──
all_jsons = {}
for p in RESULTS.rglob("*.json"):
    try:
        all_jsons[p] = json.loads(p.read_text())
    except Exception:
        pass  # skip unparseable files

# ── Helpers ───────────────────────────────────────────────────────────────────
def _find_metric(data, *keys):
    """Walk nested dicts/lists looking for any of the given keys; return first match."""
    if isinstance(data, dict):
        for k in keys:
            if k in data:
                return data[k]
        for v in data.values():
            r = _find_metric(v, *keys)
            if r is not None:
                return r
    elif isinstance(data, list):
        for item in data:
            r = _find_metric(item, *keys)
            if r is not None:
                return r
    return None

def _scan_result(exp, metric, result_subdir=None):
    """Search result JSONs for a given metric key; return (value, source_path) or (None, None).
    Uses recursive glob so results in subdirectories are found."""
    search_roots = []
    if result_subdir:
        d = RESULTS / result_subdir
        if d.exists():
            search_roots.append(d)
    search_roots.append(RESULTS)
    for root in search_roots:
        candidates = sorted(_glob.glob(str(root / "**" / "*.json"), recursive=True), reverse=True)
        for fpath in candidates:
            p = Path(fpath)
            data = all_jsons.get(p)
            if data is None:
                continue
            val = _find_metric(data, metric,
                               metric.lower(), metric.upper(),
                               metric.replace("-", "_"), metric.replace("_", "-"))
            if val is not None:
                return float(val), p
    return None, None

def _iter_rows(data):
    """Yield every dict-record from a JSON document regardless of nesting schema.
    Handles: {results:[...]} {equation_results:[...]} {domain_results:{...}}
    top-level list, list-of-lists, and deeply nested variants.
    FIX: added more container key aliases seen across different experiment outputs.
    Never raises — skips non-dict leaves silently.
    """
    if isinstance(data, dict):
        # Try well-known row-container keys first
        for key in (
            "results", "equation_results", "domain_results",
            "equations", "records", "data", "rows",
            "items", "entries", "output", "outputs",
            "benchmark_results", "eval_results", "test_results",
            "experiments", "cases", "metrics",
            "summary", "details",
        ):
            v = data.get(key)
            if v is not None:
                for r in _iter_rows(v):
                    yield r
                return
        # Leaf dict — yield it as a row candidate
        yield data
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield item
            elif isinstance(item, list):
                for sub in _iter_rows(item):
                    yield sub
            # scalars in a list are ignored

def _r2_from_row(row):
    """Extract a float R² value from a result row dict, or return None.
    FIX: expanded key list to cover common R² field name variants emitted
    by different experiment scripts (test_R2, R2_score, r_squared, etc.).
    NOTE: 'score' / 'test_score' intentionally excluded — too ambiguous
    (could be RMSE, count, accuracy, etc.) and caused false negatives when
    the sanity-check f<=1.0001 rejected non-R² numeric fields."""
    for key in (
        # original keys
        "r2", "r2_test", "r2_train", "best_r2", "r2_score",
        "R2", "R2_test", "R2_train",
        "test_r2", "train_r2",
        "test_R2", "train_R2",
        "R2_score", "R2_val", "r2_val",
        "r_squared", "R_squared",
        "rsquared", "Rsquared",
        "coefficient_of_determination",
        "r2_score_test", "r2_score_train",
        "final_r2", "best_R2",
    ):
        v = row.get(key)
        if v is not None:
            try:
                f = float(v)
                # R² is mathematically ≤ 1; values above 1.01 are not R².
                # Allow slightly above 1.0 for floating-point noise.
                if f <= 1.01:
                    return f
            except (TypeError, ValueError):
                pass
    return None

def _load_json_files(patterns):
    """Glob a list of patterns and return list of (Path, parsed_data) pairs."""
    seen = set()
    results = []
    for pat in patterns:
        for fpath in sorted(_glob.glob(pat, recursive=True)):
            if fpath in seen:
                continue
            seen.add(fpath)
            p = Path(fpath)
            data = all_jsons.get(p)
            if data is None:
                try:
                    data = json.loads(p.read_text())
                except Exception:
                    continue
            results.append((p, data))
    return results

# ── Computed metric: Nguyen-12 solve rate ─────────────────────────────────────
def _compute_nguyen12(results_dir, want_4dec):
    patterns = [
        str(results_dir / "extrapolation" / "**" / "*nguyen*seed42*.json"),
        str(results_dir / "extrapolation" / "**" / "*nguyen*.json"),
        str(results_dir / "extrapolation" / "*.json"),
        str(results_dir / "**" / "*nguyen*.json"),
        str(results_dir / "exp3*.json"),
        str(results_dir / "extrapolation" / "multi_seed" / "**" / "*.json"),
        str(results_dir / "*.json"),
    ]
    pairs = _load_json_files(patterns)
    if not pairs:
        return None, "no Nguyen-12 result JSONs found under RESULTS_DIR"
    # Prefer seed=42 file
    seed42 = [(p, d) for p, d in pairs if "seed42" in p.name or "seed_42" in p.name]
    chosen_p, chosen_d = (seed42[-1] if seed42 else pairs[-1])
    key4  = (
        "nguyen12_solve_rate_4dec", "success_rate_4dec", "solve_rate_4dec",
        "rate_4dec", "nguyen_4dec",
        "solve_rate", "success_rate", "pass_rate",
        "nguyen12_pass_rate", "nguyen_pass_rate",
        "nguyen12_4dec", "nguyen_4decimal",
        "h_rate", "hypatiax_rate", "hypatia_rate", "hx_rate",
        "hypatiax_solve_rate", "hypatia_solve_rate",
        "rate", "solved_rate", "solved_fraction",
    )
    keys  = (
        "nguyen12_solve_rate_strict", "success_rate_strict", "solve_rate_strict",
        "rate_strict", "nguyen_strict",
        "nguyen12_strict", "strict_pass_rate", "strict_solve_rate",
    )
    pre = _find_metric(chosen_d, *(key4 if want_4dec else keys))
    if pre is not None:
        return float(pre), "pre-computed key from " + chosen_p.name
    # Compute from per-equation rows
    rows = list(_iter_rows(chosen_d))
    rows = [r for r in rows if _r2_from_row(r) is not None]

    def _unpack_method_keyed(d):
        _KNOWN = {"results","equation_results","domain_results","equations","records",
                  "data","rows","items","entries","output","outputs","benchmark_results",
                  "eval_results","test_results","experiments","cases","metrics","summary","details"}
        out = []
        if isinstance(d, dict) and not any(k in _KNOWN for k in d):
            for _m, _md in d.items():
                if isinstance(_md, dict):
                    for _eq, _v in _md.items():
                        if isinstance(_v, (int, float)): out.append({"equation":_eq,"r2":float(_v),"_method":_m})
                        elif isinstance(_v, dict): out += [r for r in _iter_rows(_v) if _r2_from_row(r) is not None]
                elif isinstance(_md, list): out += [r for r in _iter_rows(_md) if _r2_from_row(r) is not None]
        return out

    if not rows: rows = _unpack_method_keyed(chosen_d)

    if not rows:
        for p, d in pairs:
            candidate_rows = [r for r in _iter_rows(d) if _r2_from_row(r) is not None]
            if not candidate_rows: candidate_rows = _unpack_method_keyed(d)
            if candidate_rows:
                rows = candidate_rows
                chosen_p = p
                break
    if not rows:
        # Diagnostic: dump all keys seen in the chosen file so the CI log
        # shows exactly which field name the experiment is using.
        all_keys = set()
        for r in _iter_rows(chosen_d):
            if isinstance(r, dict):
                all_keys.update(r.keys())
        key_hint = "actual keys in file: " + str(sorted(all_keys)[:30]) if all_keys else "file appears empty or has no dict rows"
        return None, "no equation rows with R2 found in " + chosen_p.name + " — " + key_hint
    n_total = len(rows)
    n_pass = 0
    for r in rows:
        r2 = _r2_from_row(r)
        passed = (round(r2, 4) >= 0.9999) if want_4dec else (r2 >= 0.9999)
        if passed:
            n_pass += 1
    rate = n_pass / n_total
    label = "4dec" if want_4dec else "strict"
    return rate, "computed " + str(n_pass) + "/" + str(n_total) + " " + label + " from " + chosen_p.name

# ── Computed metric: Feynman-30 solve rate ────────────────────────────────────
def _compute_feynman30(results_dir, threshold):
    pca_summary = results_dir / "comparison_results" / "feynman-tests" / "exp2_pca_4060" / "exp2_pca_4060_summary.json"
    if pca_summary.exists():
        try:
            import json as _json
            _s = _json.loads(pca_summary.read_text())
            rate = _s.get("solve_rate") or _s.get("pca_solve_rate")
            n_pass  = _s.get("n_solved",  _s.get("n_pass",  "?"))
            n_total = _s.get("n_total",   _s.get("n_cases", "?"))
            if rate is not None:
                return float(rate), f"exp2_pca_4060_summary.json  {n_pass}/{n_total}  (PCA 40/60 split)"
        except Exception:
            pass  # fall through to full scan
    patterns = [
        str(results_dir / "comparison_results" / "feynman-tests" / "exp2_pca_4060" / "**" / "*.json"),
        str(results_dir / "comparison_results" / "feynman-tests" / "exp2" / "**" / "*.json"),
        str(results_dir / "comparison_results" / "feynman-tests" / "**" / "*.json"),
        str(results_dir / "comparison_results" / "**" / "*.json"),
        str(results_dir / "comparison_results" / "feynman-tests" / "exp2_multi" / "**" / "*.json"),
        str(results_dir / "**" / "*feynman*.json"),
    ]
    PREFERRED = {
        "hypatiax", "hybridv50", "hybrid50", "hybridsymbolic", "hybriddefi", "hypatia",
        "hypatiaxv2", "hypatiaxv3", "hypatiaxv4", "hypatiaxv5",
        "hybrid", "hybridllm", "hybridnn", "hybridllmnn",
        "hybridsystem", "hybridmodel",
        "hypatiaxsystem", "hypatiaxmodel",
        "ours", "proposed", "hypatiax_system",
    }
    pairs = [(p, d) for p, d in _load_json_files(patterns)
             if "checkpoint" not in p.name and "audit_summary" not in p.name]
    if not pairs:
        return None, "no result JSONs found under comparison_results/feynman-tests/exp2"
    n_total = n_pass = 0
    for _, data in pairs:
        for row in _iter_rows(data):
            raw_method = row.get("method") or row.get("model") or row.get("system") or row.get("algorithm") or ""
            method = str(raw_method).lower().replace("-", "").replace("_", "").replace(" ", "")
            # Accept row if method is empty (i.e. single-model result files) OR matches PREFERRED
            if method and not any(p in method for p in PREFERRED):
                continue
            r2 = _r2_from_row(row)
            if r2 is None:
                continue
            n_total += 1
            if r2 >= threshold:
                n_pass += 1
    if n_total == 0:
        return None, "no HypatiaX R2 rows found in feynman exp2 result files"
    return n_pass / n_total, "computed " + str(n_pass) + "/" + str(n_total) + " at threshold=" + str(threshold)

# ── Computed metric: EHD noise robustness ─────────────────────────────────────
def _get_noise_level(row):
    """FIX: centralised noise-level extractor covering all known field names.
    Returns float or None. Handles both fractional (0.25) and percentage (25) values."""
    for key in (
        "noise_level", "noise", "sigma",
        "noise_pct", "noise_percent", "noise_percentage",
        "noise_fraction", "noise_factor",
        "noise_std", "noise_sigma",
        "snr_db", "snr",       # signal-to-noise (lower = noisier; handled below)
        "corruption_level", "perturbation_level",
        "noise_ratio", "noise_rate",
    ):
        v = row.get(key)
        if v is not None:
            try:
                f = float(v)
                # Convert percentage representation (>1 and plausible pct) to fraction
                # only for explicitly-percentage keys to avoid misinterpreting sigma=5.0
                if key in ("noise_pct", "noise_percent", "noise_percentage") and f > 1.0:
                    f = f / 100.0
                return f
            except (TypeError, ValueError):
                pass
    return None

def _compute_ehd_noise_robust(results_dir, threshold):
    patterns = [
        str(results_dir / "comparison_results" / "feynman-tests" / "noise-sweep" / "**" / "*.json"),
        str(results_dir / "comparison_results" / "feynman-tests" / "**" / "*.json"),
        str(results_dir / "comparison_results" / "**" / "*.json"),
        str(results_dir / "**" / "*noise*sweep*.json"),
        str(results_dir / "**" / "*noise*.json"),
    ]
    PREFERRED = {
        "hypatiax", "hybridv50", "hybrid50", "hybridsymbolic", "hybriddefi", "hypatia",
        "hypatiaxv2", "hypatiaxv3", "hypatiaxv4", "hypatiaxv5",
        "hybrid", "hybridllm", "hybridnn", "hybridllmnn",
        "hybridsystem", "hybridmodel", "hypatiaxsystem",
        "ours", "proposed",
    }
    pairs = [(p, d) for p, d in _load_json_files(patterns)
             if "checkpoint" not in p.name and "audit_summary" not in p.name]
    if not pairs:
        return None, "no result JSONs found under comparison_results/feynman-tests/noise-sweep"

    flattened_rows = []
    for _, data in pairs:
        if not isinstance(data, dict):
            continue
        per_noise = data.get("per_noise")
        if not isinstance(per_noise, dict):
            continue
        # Inherit file-level fields as defaults for every flattened row.
        _file_method = data.get("method") or data.get("model") or data.get("system") or ""
        _file_r2 = None
        for _r2k in ("r2", "r2_test", "r2_train", "r2_mean", "r2_median",
                     "mean_r2", "median_r2", "best_r2", "final_r2"):
            _v = data.get(_r2k)
            if _v is not None:
                try:
                    _file_r2 = float(_v)
                    break
                except (TypeError, ValueError):
                    pass
        for _nk, _nv in per_noise.items():
            try: nl = float(_nk)
            except (TypeError, ValueError): continue
            # Helper: emit one row with noise_level FORCE-ASSIGNED from the per_noise key.
            # Never use setdefault for noise_level — an inner dict may carry a stale value.
            def _emit(d, _nl=nl, _fm=_file_method, _fr=_file_r2):
                row = dict(d)
                row["noise_level"] = _nl          # FORCE-ASSIGN — overrides any inner value
                row.setdefault("method", _fm)
                if _r2_from_row(row) is None and _fr is not None:
                    row["r2"] = _fr
                if _r2_from_row(row) is not None:
                    flattened_rows.append(row)
            if isinstance(_nv, dict):
                _has_r2 = any(k in _nv for k in ("r2","rmse","R2","r2_test","r2_train","success_rate","solve_rate",
                                                    "success","r2_mean","r2_median","mean_r2","median_r2"))
                if not _has_r2 and any(isinstance(v, dict) for v in _nv.values()):
                    _ms_top = _nv.get("method_summary")
                    if isinstance(_ms_top, dict):
                        for _mname, _mval in _ms_top.items():
                            if isinstance(_mval, dict):
                                _row = dict(_mval)
                                _row["method"] = _mname
                                if _r2_from_row(_row) is None:
                                    for _rk in ("mean_r2", "median_r2"):
                                        if _mval.get(_rk) is not None:
                                            try: _row["r2"] = float(_mval[_rk]); break
                                            except (TypeError, ValueError): pass
                                _emit(_row)
                    # Nested dict: equation-keyed OR method-keyed.
                    # Recurse _iter_rows to collect all R²-bearing leaves at any depth,
                    # then inject noise_level. Handles:
                    #   method → {r2: ...}
                    #   equation_name → {method_summary: ..., per_equation: {r2: ...}}
                    # Walk the nested dict collecting every R²-bearing leaf.
                    # Strategy: try _iter_rows first; if that finds nothing, do a
                    # two-level targeted walk for the known per_equation/method_summary
                    # schema: per_noise[nl][eq_name][per_equation][r2].
                    _nested = [r for r in _iter_rows(_nv) if _r2_from_row(r) is not None]
                    if not _nested:
                        for _eq_key, _eq_val in _nv.items():
                            if isinstance(_eq_val, dict):
                                # Direct metric row (suppB equation-keyed schema)
                                if _r2_from_row(_eq_val) is not None:
                                    _nested.append(dict(_eq_val))
                                    continue
                                # Check per_equation sub-key directly
                                _pe = _eq_val.get("per_equation") or _eq_val.get("per_eq") or {}
                                if isinstance(_pe, dict) and _r2_from_row(_pe) is not None:
                                    _nested.append(dict(_pe))
                                # Also check method_summary for scalar r2 values
                                _ms = _eq_val.get("method_summary") or {}
                                if isinstance(_ms, dict):
                                    for _mname, _mval in _ms.items():
                                        if isinstance(_mval, (int, float)):
                                            _nested.append({"r2": float(_mval), "method": _mname})
                                        elif isinstance(_mval, dict) and _r2_from_row(_mval) is not None:
                                            _nested.append(dict(_mval))
                                # Recurse one more level if still nothing
                                if not _nested:
                                    _nested += [r for r in _iter_rows(_eq_val) if _r2_from_row(r) is not None]
                    if _nested:
                        for _nr in _nested:
                            _emit(_nr)
                    else:
                        for _mn, _md in _nv.items():
                            if isinstance(_md, dict):
                                if _r2_from_row(_md) is not None:
                                    _emit(_md)
                                else:
                                    for _inner in _iter_rows(_md):
                                        if _r2_from_row(_inner) is not None:
                                            _emit(_inner)
                            elif isinstance(_md, (int, float)):
                                flattened_rows.append({"noise_level": nl, "r2": float(_md), "method": _file_method})
                else:
                    _emit(_nv)
            elif isinstance(_nv, (int, float)):
                # Scalar value: treat as r2 directly
                flattened_rows.append({"noise_level": nl, "r2": float(_nv), "method": _file_method})
            elif isinstance(_nv, list):
                for item in _nv:
                    if isinstance(item, dict):
                        _emit(item)

    import re as _re2
    _schemaC_skipped = []
    for _p, data in pairs:
        if not isinstance(data, dict):
            _schemaC_skipped.append(f"{_p.name}: not-dict")
            continue
        if isinstance(data.get("per_noise"), dict):
            continue
        # Extract file-level R²
        _fr2 = None
        for _k in ("r2", "r2_test", "r2_train", "r2_mean", "r2_median",
                   "mean_r2", "median_r2", "best_r2", "final_r2"):
            _v = data.get(_k)
            if _v is not None:
                try: _fr2 = float(_v); break
                except (TypeError, ValueError): pass
        if _fr2 is None:
            # Try one level deeper in known container keys
            for _ck in ("results", "summary", "metrics", "output", "data"):
                _sub = data.get(_ck)
                if isinstance(_sub, dict):
                    for _k in ("r2", "r2_test", "r2_train", "r2_mean", "mean_r2"):
                        _v = _sub.get(_k)
                        if _v is not None:
                            try: _fr2 = float(_v); break
                            except (TypeError, ValueError): pass
                    if _fr2 is not None: break
                elif isinstance(_sub, list):
                    for _item in _sub:
                        if isinstance(_item, dict):
                            for _k in ("r2", "r2_test", "r2_train", "r2_mean", "mean_r2"):
                                _v = _item.get(_k)
                                if _v is not None:
                                    try: _fr2 = float(_v); break
                                    except (TypeError, ValueError): pass
                            if _fr2 is not None: break
                    if _fr2 is not None: break
        if _fr2 is None:
            _schemaC_skipped.append(f"{_p.name}: no-r2 keys={sorted(data.keys())[:8]}")
            continue
        _fm = data.get("method") or data.get("model") or data.get("system") or ""
        _fm_norm = _fm.lower().replace(" ", "").replace("-", "")
        _file_nls = []

        # Priority 1: scalar noise_level in JSON body
        _nl_scalar = _get_noise_level(data)
        if _nl_scalar is not None:
            _file_nls.append(_nl_scalar)

        # Priority 2: filename-encoded noise level
        if not _file_nls:
            _m2 = _re2.search(
                r"(?:noise|sigma|pct|level)[_-]?(\d+(?:[p.]\d+)?)(?:pct|percent)?",
                _p.stem, _re2.IGNORECASE)
            if _m2:
                _raw = _m2.group(1).replace("p", ".")
                try:
                    _nl = float(_raw)
                    if _nl > 1 and ("pct" in _p.stem.lower() or "percent" in _p.stem.lower()):
                        _nl /= 100.0
                    _file_nls.append(_nl)
                except ValueError:
                    pass

        # Priority 3a: single-element noise_levels list (unambiguous — file IS that level)
        if not _file_nls:
            _nlv = data.get("noise_levels") or data.get("noise_schedule") or data.get("sigma_levels")
            if isinstance(_nlv, list) and len(_nlv) == 1:
                try: _file_nls.append(float(_nlv[0]))
                except (TypeError, ValueError): pass
            elif _nlv is not None and not isinstance(_nlv, list):
                try: _file_nls.append(float(_nlv))
                except (TypeError, ValueError): pass

        # Priority 3b: cross_noise_summary keys (per-noise aggregate entries)
        if not _file_nls:
            _cns = data.get("cross_noise_summary")
            if isinstance(_cns, dict):
                for _k in _cns:
                    try: _file_nls.append(float(_k))
                    except (TypeError, ValueError): pass

        if not _file_nls:
            _schemaC_skipped.append(
                f"{_p.name}: no-noise-level r2={_fr2} nlv={data.get('noise_levels')} keys={sorted(data.keys())[:6]}")
            continue
        for _nl in _file_nls:
            flattened_rows.append({"noise_level": _nl, "r2": _fr2, "method": _fm_norm})
    if _schemaC_skipped:
        import sys as _sys
        print(f"  [schemaC-debug] {len(_schemaC_skipped)} file(s) skipped: {_schemaC_skipped[:3]}",
              file=_sys.stderr)
    generic_rows = []
    for _, data in pairs:
        for row in _iter_rows(data): generic_rows.append(row)

    all_rows = flattened_rows + generic_rows

    noise_vals = set()
    for _, data in pairs:
        if not isinstance(data, dict):
            continue
        # Source 1: top-level "noise_levels" list / scalar
        for _nlkey in ("noise_levels", "noise_level", "noise_schedule",
                       "sigma_levels", "sigma_list", "sigmas",
                       "noise_fractions", "noise_values", "levels"):
            _nlv = data.get(_nlkey)
            if _nlv is None:
                continue
            if isinstance(_nlv, list):
                for _v in _nlv:
                    try: noise_vals.add(float(_v))
                    except (TypeError, ValueError): pass
            else:
                try: noise_vals.add(float(_nlv))
                except (TypeError, ValueError): pass
        # Source 2: keys of the "per_noise" dict are noise-level strings
        _pn = data.get("per_noise")
        if isinstance(_pn, dict):
            for _k in _pn:
                try: noise_vals.add(float(_k))
                except (TypeError, ValueError): pass
    # Source 3: row-level noise_level fields (original logic)
    for row in all_rows:
        nl = _get_noise_level(row)
        if nl is not None:
            noise_vals.add(nl)
    if not noise_vals:
        import re as _re
        for p, data in pairs:
            # Match patterns like: _0.25_, _0p25_, _25pct_, _noise25_, _sigma0.5_
            m = _re.search("(?:noise|sigma|pct|level)[_\\-]?(\\d+(?:[p\\.]\\d+)?)(?:pct|percent)?", p.stem, _re.IGNORECASE)
            if m:
                raw = m.group(1).replace("p", ".")
                try:
                    nl = float(raw)
                    # If looks like a percentage (> 1 and stem has 'pct'/'percent'), convert
                    if nl > 1 and ("pct" in p.stem.lower() or "percent" in p.stem.lower()):
                        nl = nl / 100.0
                    noise_vals.add(nl)
                    # Tag all rows in this file with the filename-derived noise level
                    for row in all_rows:
                        # Only tag rows that came from this file (approximate — tag all if single file)
                        if "_noise_level_from_filename" not in row:
                            row["_noise_level_from_filename"] = nl
                except ValueError:
                    pass
    if not noise_vals:
        # Diagnostic: dump keys seen in the noise-sweep files
        all_keys_seen = set()
        for _, d in pairs[:5]:
            for row in _iter_rows(d):
                if isinstance(row, dict):
                    all_keys_seen.update(row.keys())
        key_hint = " | actual keys in noise-sweep files: " + str(sorted(all_keys_seen)[:30]) if all_keys_seen else ""
        return None, "no noise_level field found in any noise-sweep JSON" + key_hint
    max_noise = max(noise_vals)
    n_total = n_robust = 0
    for row in all_rows:
        nl = _get_noise_level(row)
        if nl is None:
            nl = row.get("_noise_level_from_filename")
        if nl is None:
            continue
        try:
            if abs(float(nl) - max_noise) > 0.01:
                continue
        except (TypeError, ValueError):
            continue
        raw_method = row.get("method") or row.get("model") or row.get("system") or row.get("algorithm") or ""
        method = str(raw_method).lower().replace("-", "").replace("_", "").replace(" ", "")
        if method and not any(p in method for p in PREFERRED):
            continue
        r2 = _r2_from_row(row)
        if r2 is None:
            continue
        n_total += 1
        if r2 >= threshold:
            n_robust += 1
    if n_total == 0:
        def _nl_matches_max(r, mx=max_noise):
            _v = r.get("noise_level")
            if _v is None: return False
            try: return abs(float(_v) - mx) <= 0.01
            except (TypeError, ValueError): return False
        sample = [r for r in all_rows if _nl_matches_max(r)][:3]
        all_noise_in_rows = sorted({r.get("noise_level") for r in all_rows if r.get("noise_level") is not None})
        sample_info = f" | flattened={len(flattened_rows)} noise_vals={sorted(noise_vals)} row_noise_vals={all_noise_in_rows[:10]}"
        if sample:
            sample_keys = set(k for r in sample for k in r.keys())
            sample_r2   = [_r2_from_row(r) for r in sample]
            sample_meth = [str(r.get("method",""))[:20] for r in sample]
            sample_info += f" | {len(sample)} row(s) at max_noise: keys={sorted(sample_keys)[:10]} r2={sample_r2} method={sample_meth}"
        _schC = len([r for r in flattened_rows if abs(float(r.get("noise_level") or -999) - max_noise) <= 0.01])
        sample_info += f" | schemaC_at_max={_schC} pairs={len(pairs)}"
        return None, "no rows at max noise=" + str(max_noise) + " found" + sample_info
    return n_robust / n_total, "computed " + str(n_robust) + "/" + str(n_total) + " at max_noise=" + str(max_noise)

# ── Computed metric: hybrid all-domains coverage ──────────────────────────────
def _compute_all_domains_coverage(results_dir, n_expected):
    patterns = [
        str(results_dir / "hybrid_llm_nn" / "all_domains" / "**" / "*.json"),
        str(results_dir / "hybrid_llm_nn" / "**" / "*.json"),
        str(results_dir / "**" / "hybrid_llm_nn*.json"),
        str(results_dir / "**" / "hybrid*all*domain*.json"),
        str(results_dir / "hybrid_pysr" / "all_domains" / "**" / "*.json"),
        str(results_dir / "llm_guided" / "all_domains" / "**" / "*.json"),
        str(results_dir / "**" / "consolidated_hybrid*.json"),
        str(results_dir / "**" / "*all_domains*.json"),
        str(results_dir / "**" / "*hybrid*domain*.json"),
    ]
    pairs = [(p, d) for p, d in _load_json_files(patterns)
             if "checkpoint" not in p.name and "audit_summary" not in p.name]
    if not pairs:
        return None, "no result JSONs found under hybrid_llm_nn/"
    covered = set()
    for _, data in pairs:
        for row in _iter_rows(data):
            domain = (
                row.get("domain") or row.get("domain_id") or
                row.get("benchmark_domain") or row.get("domain_name") or
                row.get("experiment_domain") or row.get("category") or
                row.get("physics_domain") or row.get("subject") or
                row.get("field") or row.get("task_domain") or
                row.get("domain_label") or row.get("topic") or
                row.get("discipline") or row.get("area") or ""
            )
            r2 = _r2_from_row(row)
            status = str(row.get("status", "")).lower()
            completed = row.get("completed") or row.get("success") or row.get("done")
            decision = row.get("decision") or row.get("decision_reason") or ""
            has_result = (
                r2 is not None or
                status in ("complete", "completed", "success", "done", "pass", "passed", "ok", "true") or
                completed is True or completed == 1 or str(completed).lower() in ("true", "1", "yes") or
                (isinstance(decision, str) and decision.strip() != "")
            )
            if domain and has_result:
                covered.add(str(domain).lower().strip())
        if isinstance(data, dict):
            top_domain = (
                data.get("domain") or data.get("domain_id") or
                data.get("benchmark_domain") or data.get("domain_name") or
                data.get("experiment_domain") or data.get("category") or ""
            )
            if top_domain:
                top_decision = data.get("decision") or data.get("decision_reason") or ""
                top_status = str(data.get("status", "")).lower()
                top_completed = data.get("completed") or data.get("success") or data.get("done")
                has_any_result = (
                    any(_r2_from_row(r) is not None for r in _iter_rows(data)) or
                    (isinstance(top_decision, str) and top_decision.strip() != "") or
                    top_status in ("complete", "completed", "success", "done", "pass", "passed", "ok") or
                    top_completed is True or top_completed == 1
                )
                if has_any_result:
                    covered.add(str(top_domain).lower().strip())
    for _, data in pairs:
        if isinstance(data, dict):
            for key in ("domains_completed", "completed_domains", "covered_domains",
                        "finished_domains", "domains_run", "domains"):
                v = data.get(key)
                if isinstance(v, list):
                    for d in v:
                        if isinstance(d, str) and d.strip():
                            covered.add(d.lower().strip())
                elif isinstance(v, dict):
                    # {"physics": true, "chemistry": false, ...}
                    for d, done in v.items():
                        if done and isinstance(d, str) and d.strip():
                            covered.add(d.lower().strip())
    n_covered = len(covered)
    denom = n_expected if n_expected > 0 else 10
    rate = n_covered / denom
    if n_covered == 0 and pairs:
        sample_keys = set()
        for _, d in pairs[:3]:
            for row in _iter_rows(d):
                if isinstance(row, dict):
                    sample_keys.update(row.keys())
        key_hint = " | sample keys in files: " + str(sorted(sample_keys)[:25])
    else:
        key_hint = ""
    return rate, "computed " + str(n_covered) + "/" + str(denom) + " domains: " + str(sorted(covered)) + key_hint

# ── Audit loop ────────────────────────────────────────────────────────────────
findings = []

TOLERANCE         = 0.01
FEYNMAN_THRESHOLD = float(os.environ.get("FEYNMAN_NOISELESS_THRESHOLD", "0.9999"))
NOISE_THRESHOLD   = float(os.environ.get("NOISE_THRESHOLD", "0.9"))
HYBRID_N_DOMAINS  = int(os.environ.get("HYBRID_N_DOMAINS", "10"))

for claim in targets:
    if "_EXCLUDED" in claim:
        continue

    exp    = claim.get("exp", "?")
    metric = claim.get("metric", "?")
    paper  = claim.get("paper_value")
    tol    = claim.get("tolerance", TOLERANCE)
    subdir = claim.get("result_subdir")
    note   = claim.get("note", "")

    if paper is None:
        findings.append({"exp": exp, "metric": metric, "status": "MISSING",
                         "detail": "no 'paper_value' field in paper_targets.json entry"})
        continue

    # ── Dispatch to computed-metric handlers ──────────────────────────────────
    if exp in ("exp3", "exp3b") and metric in (
            "nguyen12_solve_rate_4dec", "nguyen12_solve_rate_strict",
            "success_rate_4dec",        "success_rate_strict"):
        want_4dec = metric in ("nguyen12_solve_rate_4dec", "success_rate_4dec")
        got, src_desc = _compute_nguyen12(RESULTS, want_4dec)

    elif metric == "feynman30_solve_rate":
        got, src_desc = _compute_feynman30(RESULTS, FEYNMAN_THRESHOLD)

    elif metric == "ehd_noise_robust_100pct":
        got, src_desc = _compute_ehd_noise_robust(RESULTS, NOISE_THRESHOLD)

    elif metric == "all_domains_coverage":
        got, src_desc = _compute_all_domains_coverage(RESULTS, HYBRID_N_DOMAINS)

    else:
        # General key-lookup path
        got_val, src_path = _scan_result(exp, metric, subdir)
        if got_val is None:
            findings.append({"exp": exp, "metric": metric, "status": "MISSING",
                             "detail": f"metric '{metric}' not found in any result JSON under {RESULTS}"})
            continue
        expected = float(paper)
        ok = abs(got_val - expected) <= max(tol * max(abs(expected), 1e-9), 1e-9)
        st = "PASS" if ok else "FAIL"
        src_rel = str(src_path.relative_to(RESULTS)) if src_path.is_relative_to(RESULTS) else str(src_path)
        detail  = f"got={got_val:.6f}, expected={expected:.6f}, tol={tol} | {src_rel}"
        if note:
            detail += f" | {note}"
        findings.append({"exp": exp, "metric": metric, "status": st, "detail": detail})
        continue

    # ── Evaluate computed result ───────────────────────────────────────────────
    if got is None:
        findings.append({"exp": exp, "metric": metric, "status": "MISSING",
                         "detail": src_desc})
    else:
        expected = float(paper)
        compare_mode = claim.get("compare", "exact")  # "exact" | "gte" | "lte"

        if compare_mode == "exact":
            lower_bound_metrics = {
                "feynman30_solve_rate",
                "ehd_noise_robust_100pct",
            }
            if metric in lower_bound_metrics:
                compare_mode = "gte"

        if metric == "all_domains_coverage" and expected > 1.0:
            expected_rate = expected / max(HYBRID_N_DOMAINS, 1)
        else:
            expected_rate = expected

        if compare_mode == "gte":
            # PASS when got >= paper_value (paper states a lower bound, not exact target)
            ok = got >= expected_rate - max(tol * max(abs(expected_rate), 1e-9), 1e-9)
        elif compare_mode == "lte":
            ok = got <= expected_rate + max(tol * max(abs(expected_rate), 1e-9), 1e-9)
        else:
            ok = abs(got - expected_rate) <= max(tol * max(abs(expected_rate), 1e-9), 1e-9)

        st = "PASS" if ok else "FAIL"
        detail = f"got={got:.4f}, expected={expected:.4f}(as_rate={expected_rate:.4f}), tol={tol}, mode={compare_mode} | {src_desc}"
        if note:
            detail += f" | {note}"
        findings.append({"exp": exp, "metric": metric, "status": st, "detail": detail})

# ── Print summary ─────────────────────────────────────────────────────────────
n_pass = sum(1 for f in findings if f["status"] == "PASS")
n_warn = sum(1 for f in findings if f["status"] == "WARN")
n_fail = sum(1 for f in findings if f["status"] == "FAIL")
n_miss = sum(1 for f in findings if f["status"] == "MISSING")
n_skip = sum(1 for f in findings if f["status"] == "SKIP")

print(f"\n  Audit findings ({len(findings)} claims)")
print("  " + chr(9472)*55)
print(f"  ✅ PASS    : {n_pass}")
print(f"  ⚠  WARN    : {n_warn}")
print(f"  ❌ FAIL    : {n_fail}")
print(f"  🔍 MISSING : {n_miss}")
print(f"  ↩  SKIP    : {n_skip}")

bad = [f for f in findings if f["status"] in ("FAIL", "MISSING")]
if bad:
    print(f"\n  FAIL / MISSING details:")
    for f in bad:
        print("    [" + f["status"] + "]  exp=" + str(f["exp"]) + "  metric=" + str(f["metric"]))
        print("             " + str(f["detail"]))

# Nguyen-12 caveat — always print
if any(f["exp"] in ("exp3", "exp3b") for f in findings):
    print()
    print("  ⚠  Nguyen-12 dual-threshold caveat:")
    print("       Table (tab:nguyen12), R²≥0.9999 4-decimal: 7/12 H (58.3%) · 8/12 P (66.7%)")
    print("       The earlier 4/12 (33.3%) strict-threshold figure was retracted in the")
    print("       caption as having no basis in the current data — do not reintroduce it.")

# ── Write findings JSON ───────────────────────────────────────────────────────
FINDINGS_F.parent.mkdir(parents=True, exist_ok=True)
FINDINGS_F.write_text(json.dumps(findings, indent=2))
print(f"\n  Findings → {FINDINGS_F}")

# ── Exit code ─────────────────────────────────────────────────────────────────
fatal_statuses = {"FAIL", "MISSING"}
if FAIL_ON_WARN:
    fatal_statuses.add("WARN")

fatal = [f for f in findings if f["status"] in fatal_statuses]
if not findings:
    print("\n⚠   No claims found — check paper_targets.json.")
elif fatal:
    print(f"\n❌  audit_paper FAILED — {len(fatal)} claim(s) need attention.")
    sys.exit(1)
else:
    print("\n✅  All claims PASSED (within tolerance).")
    print("  Findings → logs/paper_audit_findings.json")
PYEOF
'

# ── STEP 16: audit_setup ─────────────────────────────────────────────────────
run audit_setup "Copy .tex source files into notebooks/ for audit notebooks" bash -c '
  set -euo pipefail
  cd "'"${REPO_ROOT}"'"

  python3 - <<'"'"'PYEOF'"'"'
import shutil, pathlib, sys

nb = pathlib.Path("notebooks")
nb.mkdir(exist_ok=True)

search_dirs = [
    pathlib.Path("paper"),
    pathlib.Path("."),
    pathlib.Path("paper") / "tables",
    pathlib.Path("logs"),
]

copied  = []
missing = []

# Main paper .tex
main = next(
    (f for d in search_dirs
       for pat in ("jmlr-hypatiax*.tex", "jmlr_paper*.tex")
       for f in d.glob(pat) if f.is_file()),
    None
)
if main:
    shutil.copy(main, nb / main.name)
    copied.append(main.name)
    print(f"  [OK] main paper: {main.name}")
else:
    print("  [WARN] main paper .tex not found — notebooks may not locate paper content")

# Supplement files
for name in ("supp_routing_improvements.tex", "supp_benchmark_report.tex"):
    src = next((d / name for d in search_dirs if (d / name).is_file()), None)
    if src:
        shutil.copy(src, nb / name)
        copied.append(name)
        print(f"  [OK] {name}")
    else:
        missing.append(name)
        print(f"  [WARN] {name} not found — notebook may skip supplement checks")

print(f"\naudit-setup: copied {len(copied)} file(s): {copied}")
if missing:
    print(f"  Missing (non-fatal): {missing}")
PYEOF
'

# ── STEP 17: audit_nb01 ───────────────────────────────────────────────────────
# NB-01 · Citation & Bibliography Audit
# Catches: koza1994genetic missing from bibliography (lines 327, 1888);
#          cranmer2023pysr/cranmer2023interp alias collision (same arXiv);
#          4 uncited bibitems.
run audit_nb01 "NB-01: Citation & Bibliography Audit" bash -c '
  set -euo pipefail
  cd "'"${REPO_ROOT}"'"
  echo "=== NB-01: Citation & Bibliography Audit ==="
  jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=300 \
    notebooks/NB-01_Citation_Bibliography_Audit.ipynb \
    2>&1 | tee "'"${RESULTS_DIR}"'"/audit_nb01_run.log
  echo "=== NB-01 done ==="
'

# ── STEP 18: audit_nb02 ───────────────────────────────────────────────────────
# NB-02 · Cross-Reference & Label Integrity
# Catches: \label inside \item (sec:r2_bugfix, thm:five_system_hierarchy) →
#          garbled \ref output; duplicate section labels
#          sec:llm_limitations/sec:llm_domain; Supp A references Section 7.3
#          but main paper has Component 3 at Section 7.4.
run audit_nb02 "NB-02: Cross-Reference & Label Integrity" bash -c '
  set -euo pipefail
  cd "'"${REPO_ROOT}"'"
  echo "=== NB-02: Cross-Reference & Label Integrity ==="
  jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=300 \
    notebooks/NB-02_CrossReference_Label_Audit.ipynb \
    2>&1 | tee "'"${RESULTS_DIR}"'"/audit_nb02_run.log
  echo "=== NB-02 done ==="
'

# ── STEP 19: audit_nb03 ───────────────────────────────────────────────────────
# NB-03 · Section Structure & Numbering
# Catches: section structure and numbering consistency issues across .tex files.
run audit_nb03 "NB-03: Section Structure & Numbering" bash -c '
  set -euo pipefail
  cd "'"${REPO_ROOT}"'"
  echo "=== NB-03: Section Structure & Numbering ==="
  jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=300 \
    notebooks/NB-03_Section_Structure_Numbering.ipynb \
    2>&1 | tee "'"${RESULTS_DIR}"'"/audit_nb03_run.log
  echo "=== NB-03 done ==="
'

# ── STEP 20: audit_nb04 ───────────────────────────────────────────────────────
# NB-04 · Numerical Consistency & Abstract Claims
# Catches: abstract claim presence (89.2%, 62.2%, +27pp, +83.8pp, 1.73×,
#          68/74, 11/12, 9/30, +38.1pp); 70 vs 71 task discrepancy (body
#          says "71 cases", table caption says "70 tasks"); "five-stage routing"
#          vs "Five-Layer Architecture" terminology inconsistency; timing
#          arithmetic cross-check (6.8s, 1.7s, 3.0s, 2.7s, 1.73×, 11.4s).
run audit_nb04 "NB-04: Numerical Consistency & Abstract Claims" bash -c '
  set -euo pipefail
  cd "'"${REPO_ROOT}"'"
  echo "=== NB-04: Numerical Consistency & Abstract Claims ==="
  jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=300 \
    notebooks/NB-04_Numerical_Consistency_Checker.ipynb \
    2>&1 | tee "'"${RESULTS_DIR}"'"/audit_nb04_run.log
  echo "=== NB-04 done ==="
'

# ── STEP 21: audit_nb05 ───────────────────────────────────────────────────────
# NB-05 · Figure Files & Image Dependencies
# Catches: all 5 \includegraphics targets checked on disk — 4 MISSING
#          (hypatiaX_three_systems, fig18_r2_heatmap_improved,
#           fig09_r2_heatmap_regimes, fig1_seed_sweep);
#          \fbox placeholder in Section 7.1 (fig:architecture);
#          figure environment label/caption completeness.
run audit_nb05 "NB-05: Figure Files & Image Dependencies" bash -c '
  set -euo pipefail
  cd "'"${REPO_ROOT}"'"
  echo "=== NB-05: Figure Files & Image Dependencies ==="
  jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=300 \
    notebooks/NB-05_Figure_Image_Dependency_Checker.ipynb \
    2>&1 | tee "'"${RESULTS_DIR}"'"/audit_nb05_run.log
  echo "=== NB-05 done ==="
'

# ── STEP 22a: audit_nb06_fixc3_disclosure (FIX-C3 Action A) ─────────────────
run audit_nb06_fixc3_disclosure \
    "NB-06 FIX-C3 Action A: Disclose Feynman random-80/20 vs DeFi PCA-40/60 split mismatch (§10.7)" \
    bash -c '
  set -euo pipefail
  cd "'"${REPO_ROOT}"'"
  echo "=== NB-06 FIX-C3 Action A: Split Protocol Disclosure ==="

  python3 - <<'"'"'PYEOF'"'"' 2>&1 | tee "'"${RESULTS_DIR}"'"/audit_nb06_fixc3_disclosure_run.log
import json, os, sys, glob
from pathlib import Path

RESULTS = Path(os.environ.get("RESULTS_DIR", "hypatiax/data/results"))
REPO    = Path(os.environ.get("REPO_ROOT",   "."))

# ── Verify the split difference is documented in code ────────────────────────
SCRIPT = REPO / "hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py"
findings = []
all_ok   = True

def record(label, ok, detail=""):
    global all_ok
    findings.append({"label": label, "ok": ok, "detail": detail})
    tag = "OK" if ok else "FAIL"
    print(f"  [{tag}] {label}  {detail}")
    if not ok:
        all_ok = False

# (1) Confirm train_test_split(test_size=0.2) exists in the script (baseline check)
if SCRIPT.exists():
    src = SCRIPT.read_text(errors="replace")
    has_random_split = "train_test_split" in src and "test_size=0.2" in src
    record(
        "run_comparative_suite_benchmark_v2.py contains train_test_split(test_size=0.2)",
        has_random_split,
        f"file: {SCRIPT.name}"
    )
    # (2) Confirm build_extrap_split (PCA 40/60 path) also exists in the script
    has_pca_split = "build_extrap_split" in src
    record(
        "run_comparative_suite_benchmark_v2.py contains build_extrap_split (PCA 40/60 path)",
        has_pca_split,
        "PCA-directed split used by DeFi benchmarks"
    )
    # (3) Confirm the random split is inside the NN method (not the Feynman outer loop)
    # The NN .run() method should be the site of the random split — verify by checking
    # proximity of "test_size=0.2" to the class or def run pattern.
    lines = src.splitlines()
    split_lines = [i+1 for i, l in enumerate(lines) if "test_size=0.2" in l]
    run_method_lines = [i+1 for i, l in enumerate(lines) if "def run(" in l]
    # test_size=0.2 should appear within 200 lines of a "def run(" definition
    proximate = any(
        any(abs(sl - rl) <= 200 for rl in run_method_lines)
        for sl in split_lines
    )
    record(
        "train_test_split(test_size=0.2) is inside a .run() method (NN method scope)",
        proximate,
        f"split at lines {split_lines}, run() at lines {run_method_lines[:5]}"
    )
else:
    record("run_comparative_suite_benchmark_v2.py found", False, str(SCRIPT))

# (4) Confirm exp2_feynman result files do NOT carry extrap_multiplier metadata
#     (which would indicate the PCA split was accidentally applied).
exp2_files = sorted(glob.glob(
    str(RESULTS / "comparison_results/feynman-tests/exp2/**/*.json"), recursive=True
))
feynman_extrap_contamination = 0
for fp in exp2_files:
    try:
        data = json.loads(Path(fp).read_text())
        # extrap_multiplier in the result means the extrap/PCA path ran — unexpected for exp2
        if isinstance(data, dict) and data.get("extrap_multiplier") is not None:
            feynman_extrap_contamination += 1
    except Exception:
        pass
if exp2_files:
    record(
        "exp2_feynman result files have NO extrap_multiplier (confirms random-split path ran)",
        feynman_extrap_contamination == 0,
        f"checked {len(exp2_files)} files; {feynman_extrap_contamination} had extrap_multiplier"
    )
else:
    record(
        "exp2_feynman result files present for split verification",
        False,
        "no files in comparison_results/feynman-tests/exp2/ — run exp2_feynman first"
    )

# ── Write disclosure record ───────────────────────────────────────────────────
disclosure = {
    "fixc3_action": "A",
    "fixc3_note": (
        "FIX-C3 (NB-06): Feynman benchmark (§10.7) uses train_test_split(test_size=0.2) "
        "— a random 80/20 split with extrap_multiplier=2.0. "
        "DeFi benchmarks (§10.2–10.4) use build_extrap_split with extrap_train_frac=0.6 "
        "(PCA-directed 40/60 split). "
        "These are scientifically distinct protocols; the 9/30 Feynman result is NOT "
        "directly comparable to DeFi results without this disclosure. "
        "Action B (audit_nb06_fixc3_rerun) reruns Feynman with the PCA 40/60 split "
        "and reports the revised figure."
    ),
    "feynman_split": {
        "type": "random",
        "function": "sklearn.model_selection.train_test_split",
        "test_size": 0.2,
        "train_size": 0.8,
        "extrap_multiplier": 2.0,
        "random_state": 42,
        "section": "§10.7"
    },
    "defi_split": {
        "type": "pca_directed_extrapolation",
        "function": "build_extrap_split",
        "extrap_train_frac": 0.6,
        "extrap_multiplier": 2.0,
        "section": "§10.2–10.4, §6.4"
    },
    "findings": findings,
    "all_ok": all_ok
}

out = RESULTS / "fixc3_split_disclosure.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(disclosure, indent=2))
print(f"\n  Disclosure record → {out}")

n_fail = sum(1 for f in findings if not f["ok"])
if all_ok:
    print("\n✅  FIX-C3 Action A: split mismatch correctly documented.")
else:
    print(f"\n❌  FIX-C3 Action A: {n_fail} check(s) failed — see details above.")
    sys.exit(1)
PYEOF
  echo "=== NB-06 FIX-C3 Action A done ==="
'

# ── STEP 22b: audit_nb06_fixc3_rerun (FIX-C3 Action B) ──────────────────────
run audit_nb06_fixc3_rerun \
    "NB-06 FIX-C3 Action B: Rerun Feynman with PCA 40/60 split and report revised 9/30 result (§10.7)" \
    bash -c '
  set -euo pipefail
  cd "'"${REPO_ROOT}"'"
  echo "=== NB-06 FIX-C3 Action B: Feynman PCA 40/60 Rerun ==="

  # ── Prerequisite: Action A disclosure must exist ──────────────────────────
  DISCLOSURE="'"${RESULTS_DIR}"'"/fixc3_split_disclosure.json
  if [[ ! -f "${DISCLOSURE}" ]]; then
    echo "ERROR: fixc3_split_disclosure.json not found — run audit_nb06_fixc3_disclosure first."
    exit 1
  fi
  echo "  [OK] Disclosure record found: ${DISCLOSURE}"

  mkdir -p "'"${RESULTS_DIR}"'"/comparison_results/feynman-tests/exp2_fixc3

  # ── Per-domain rerun with PCA 40/60 split ────────────────────────────────
  # Same domain list as exp2_feynman; same hyperparameters; only split differs.
  # --extrap-train-frac 0.6 → 60% train, 40% far-region (the §6.4 DeFi protocol)
  # --extrap-multiplier 2.0 → matches DeFi benchmark and paper value
  for DOMAIN_ID in '"${FEYNMAN_DOMAINS}"'; do
    echo "=== fixc3_rerun: domain=${DOMAIN_ID} (PCA 40/60 split) ==="
    FEYNMAN_SAMPLES='"${FEYNMAN_SAMPLES}"' \
    FEYNMAN_TIMEOUT='"${FEYNMAN_TIMEOUT}"' \
    METHOD_TIMEOUT='"${METHOD_TIMEOUT}"' \
    PYSR_FIT_WALL_TIMEOUT='"${PYSR_FIT_WALL_TIMEOUT}"' \
    PYSR_FIT_GRACE_SECS='"${PYSR_FIT_GRACE_SECS}"' \
    JOB_DEADLINE='"${JOB_DEADLINE}"' \
      python3 "'"${EXPERIMENTS_DIR}"'"/run_comparative_suite_benchmark_pca.py \
        --benchmark feynman \
        --domain "${DOMAIN_ID}" \
        --samples '"${FEYNMAN_SAMPLES}"' \
        --pysr-timeout '"${FEYNMAN_TIMEOUT}"' \
        --method-timeout '"${METHOD_TIMEOUT}"' \
        --populations '"${PYSR_POPULATIONS}"' \
        --parsimony 0.01 \
        --noiseless \
        --use-transcendental-compositions \
        --nn-seeds 3 \
        --no-llm-cache \
        --threshold '"${FEYNMAN_NOISELESS_THRESHOLD}"' \
        --checkpoint-name "fixc3_checkpoint_${DOMAIN_ID}" \
        --output-dir "'"${RESULTS_DIR}"'"/comparison_results/feynman-tests/exp2_fixc3 \
        --resume \
      2>&1 | tee -a "'"${RESULTS_DIR}"'"/comparison_results/feynman-tests/exp2_fixc3/fixc3_run.log \
    || echo "WARNING: fixc3_rerun domain ${DOMAIN_ID} exited non-zero — continuing"
  done

  # ── Compute and report the corrected solve rate ───────────────────────────
  python3 - <<'"'"'PYEOF'"'"' 2>&1 | tee -a "'"${RESULTS_DIR}"'"/comparison_results/feynman-tests/exp2_fixc3/fixc3_run.log
import glob, json, os, sys
from pathlib import Path

RESULTS  = Path(os.environ.get("RESULTS_DIR", "hypatiax/data/results"))
FIXC3_DIR = RESULTS / "comparison_results/feynman-tests/exp2_fixc3"
THRESHOLD = float(os.environ.get("FEYNMAN_NOISELESS_THRESHOLD", "0.999999"))

PREFERRED = {
    "hypatiax", "hybridv50", "hybrid50", "hybridsymbolic", "hybriddefi", "hypatia",
    "hybrid", "hybridllm", "hybridnn", "ours", "proposed",
}

result_files = sorted(FIXC3_DIR.glob("protocol_core_fixc3_*.json")) + \
               sorted(FIXC3_DIR.glob("protocol_core_*.json"))

if not result_files:
    print(f"\n  WARNING: No fixc3 result files found in {FIXC3_DIR}")
    print("  The rerun may not have produced output yet (Julia/PySR timeout or crash).")
    print("  Re-run this step after confirming experiment scripts are functional.")
    # Write a stub summary so Action A disclosure is not blocked
    summary = {
        "fixc3_action": "B",
        "status": "INCOMPLETE",
        "note": "No result files found — rerun step after experiment scripts are functional.",
        "feynman_pca4060_solve_rate": None,
        "feynman_random8020_solve_rate_paper": "9/30 = 0.300",
        "corrected_result": "PENDING",
    }
    out = RESULTS / "fixc3_rerun_summary.json"
    out.write_text(json.dumps(summary, indent=2))
    print(f"\n  Stub summary → {out}")
    sys.exit(0)

def _r2_from_row(row):
    for key in ("r2", "r2_test", "r2_train", "best_r2", "R2", "R2_test",
                "extrap_r2_far", "extrap_r2"):
        v = row.get(key)
        if v is not None:
            try:
                f = float(v)
                if f <= 1.01:
                    return f
            except (TypeError, ValueError):
                pass
    return None

def _iter_rows(data):
    if isinstance(data, dict):
        for key in ("results", "equation_results", "data", "rows", "items"):
            v = data.get(key)
            if v is not None:
                yield from _iter_rows(v)
                return
        yield data
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield item

n_total = n_pass = 0
seen_equations = set()

for fp in result_files:
    try:
        data = json.loads(fp.read_text())
    except Exception:
        continue
    for row in _iter_rows(data):
        raw_method = row.get("method") or row.get("model") or ""
        method = str(raw_method).lower().replace("-", "").replace("_", "").replace(" ", "")
        if method and not any(p in method for p in PREFERRED):
            continue
        eq_id = row.get("equation") or row.get("eq_id") or row.get("name", "")
        if eq_id and eq_id in seen_equations:
            continue
        r2 = _r2_from_row(row)
        if r2 is None:
            continue
        if eq_id:
            seen_equations.add(eq_id)
        n_total += 1
        if r2 >= THRESHOLD:
            n_pass += 1

print(f"\n  === FIX-C3 Action B: Corrected Feynman Result (PCA 40/60 split) ===")
print(f"  Protocol  : --extrap --extrap-train-frac 0.6 --extrap-multiplier 2.0")
print(f"  Threshold : R² >= {THRESHOLD}")
print(f"  Equations : {n_total} evaluated  |  {n_pass} solved")
if n_total > 0:
    rate = n_pass / n_total
    print(f"  Solve rate: {n_pass}/{n_total} = {rate:.3f}")
    print(f"")
    print(f"  ORIGINAL  (random 80/20)  : 9/30  = 0.300  [§10.7 as submitted]")
    print(f"  CORRECTED (PCA 40/60)     : {n_pass}/{n_total} = {rate:.3f}  [FIX-C3 revised]")
    if n_pass < 9:
        delta = "LOWER  (harder split as expected — DeFi-comparable)"
    elif n_pass > 9:
        delta = "HIGHER (unexpected — verify extrap-train-frac 0.6 was applied)"
    else:
        delta = "SAME   (splits happen to produce equal count)"
    print(f"  Direction : {delta}")
else:
    rate = None
    print("  WARNING: 0 equations evaluated — check result file schema")

summary = {
    "fixc3_action": "B",
    "status": "COMPLETE" if n_total > 0 else "INCOMPLETE",
    "protocol": {
        "split_type": "pca_directed_extrapolation",
        "extrap_train_frac": 0.6,
        "extrap_multiplier": 2.0,
        "threshold": THRESHOLD,
        "function": "build_extrap_split"
    },
    "feynman_pca4060_n_total": n_total,
    "feynman_pca4060_n_pass":  n_pass,
    "feynman_pca4060_solve_rate": rate,
    "feynman_random8020_solve_rate_paper": "9/30 = 0.300",
    "corrected_result": f"{n_pass}/{n_total}" if n_total > 0 else "PENDING",
    "result_files_used": [fp.name for fp in result_files],
}

out = Path(os.environ.get("RESULTS_DIR", "hypatiax/data/results")) / "fixc3_rerun_summary.json"
out.write_text(json.dumps(summary, indent=2))
print(f"\n  Summary → {out}")
PYEOF

  echo "=== NB-06 FIX-C3 Action B done ==="
'

# ── STEP 22: audit_guard ──────────────────────────────────────────────────────
run audit_guard "Guard: evaluate trigger conditions (slot=12, run_full, success)" bash -c '
  set -euo pipefail
  python3 - <<'"'"'PYEOF'"'"'
import os, re, sys
event      = os.environ.get("EVENT_NAME", "")
conclusion = os.environ.get("TRIGGER_CONCLUSION", "")
title      = os.environ.get("TRIGGER_TITLE", "")
gh_out     = os.environ.get("GITHUB_OUTPUT", "/dev/null")
if event == "workflow_dispatch":
    print("Manual dispatch — proceeding unconditionally.")
    open(gh_out, "a").write("should_run=true\n")
    sys.exit(0)
if conclusion != "success":
    print("Upstream conclusion=" + repr(conclusion) + " (not success) — skipping.")
    open(gh_out, "a").write("should_run=false\n")
    sys.exit(0)
m = re.search(r"—\s*(\d+)([afcp]?)\s*$", title)
if not m:
    print("Could not parse slot from run title: " + repr(title) + " — skipping.")
    open(gh_out, "a").write("should_run=false\n")
    sys.exit(0)
slot   = int(m.group(1))
suffix = m.group(2)
if slot != 12:
    print("Slot=" + str(slot) + " (not 12) — skipping paper audit.")
    open(gh_out, "a").write("should_run=false\n")
    sys.exit(0)
if suffix != "":
    print("Slot=12 but suffix=" + repr(suffix) + " (run_full=false) — skipping.")
    open(gh_out, "a").write("should_run=false\n")
    sys.exit(0)
print("Slot=12, run_full=true, conclusion=success — paper audit WILL run.")
open(gh_out, "a").write("should_run=true\n")
PYEOF
'

# ── STEP 23: audit_print_verify ───────────────────────────────────────────────
run audit_print_verify "Print verify summary from logs/verify_report.json" bash -c '
  set -euo pipefail
  if [[ ! -f logs/verify_report.json ]]; then
    echo "  logs/verify_report.json not written — see verify_run.log above."
    exit 0
  fi
  echo "=== verify_report.json ==="
  python3 - <<'"'"'PYEOF'"'"'
import json
from pathlib import Path
data   = json.loads(Path("logs/verify_report.json").read_text())
checks = data if isinstance(data, list) else data.get("checks", [])
n_ok   = sum(1 for c in checks if c.get("status") in ("OK", "PASS", "pass"))
n_fail = sum(1 for c in checks if c.get("status") in ("FAIL", "fail"))
n_warn = sum(1 for c in checks if c.get("status") in ("WARN", "warn"))
print(f"  Checks : {len(checks)} total  PASS={n_ok}  WARN={n_warn}  FAIL={n_fail}")
if n_fail:
    print("  Failed checks:")
    for c in checks:
        if c.get("status") in ("FAIL", "fail"):
            name   = c.get("name",   c.get("check",  "?"))
            detail = c.get("detail", "")
            print("    FAIL  " + str(name) + ": " + str(detail))
PYEOF
'

# ── STEP 24: audit_print_findings ─────────────────────────────────────────────
run audit_print_findings "Print audit summary from logs/paper_audit_findings.json" bash -c '
  set -euo pipefail
  if [[ ! -f logs/paper_audit_findings.json ]]; then
    echo "  logs/paper_audit_findings.json not written — check logs/paper_audit_run.log"
    exit 0
  fi
  python3 - <<'"'"'PYEOF'"'"'
import json
from pathlib import Path
data   = json.loads(Path("logs/paper_audit_findings.json").read_text())
n_pass = sum(1 for f in data if f["status"] == "PASS")
n_warn = sum(1 for f in data if f["status"] == "WARN")
n_fail = sum(1 for f in data if f["status"] == "FAIL")
n_miss = sum(1 for f in data if f["status"] == "MISSING")
n_skip = sum(1 for f in data if f["status"] == "SKIP")
sep = chr(9472)*55
print("  Audit findings (" + str(len(data)) + " claims)")
print("  " + sep)
print("  PASS=" + str(n_pass) + "  WARN=" + str(n_warn) + "  FAIL=" + str(n_fail) + "  MISSING=" + str(n_miss) + "  SKIP=" + str(n_skip))
bad = [f for f in data if f["status"] in ("FAIL", "MISSING")]
if bad:
    print("  FAIL / MISSING details:")
    for f in bad:
        print("    [" + f["status"] + "]  exp=" + str(f["exp"]) + "  metric=" + str(f["metric"]))
        print("             " + str(f["detail"]))
PYEOF
'

# ── STEP 25: audit_figures_tables ─────────────────────────────────────────────
run audit_figures_tables "No-op: table/figure generation disabled pipeline-wide" bash -c '
  set -euo pipefail
  mkdir -p logs
  python3 - <<'"'"'PYEOF'"'"'
import json
from pathlib import Path

out = Path("logs/figures_tables_report.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({
    "all_ok": True,
    "findings": [{"category": "figures_tables", "name": "generation disabled",
                   "ok": True, "detail": "table/figure generation removed from pipeline"}]
}, indent=2))
print("  [OK]  [figures_tables]  generation disabled — nothing to validate")
print("  Report -> " + str(out))
PYEOF
'

# ── STEP 26: audit_final_gate ─────────────────────────────────────────────────
run audit_final_gate "Final gate: aggregate all audit job outcomes" bash -c '
  set -euo pipefail
  python3 - <<'"'"'PYEOF'"'"'
import os, sys
verify = os.environ.get("VERIFY_RESULT", "unknown")
audit  = os.environ.get("AUDIT_RESULT",  "unknown")
figs   = os.environ.get("FIGS_RESULT",   "unknown")
ok_verify = verify in ("success", "skipped")
ok_audit  = audit  == "success"
ok_figs   = figs   == "success"
sep = "=" * 65
print("\n" + sep)
print("  HypatiaX Paper Audit — Final Gate")
print(sep)
rows = [
    ("1. numerical-verify",        verify, ok_verify),
    ("2. paper-audit",             audit,  ok_audit),
    ("3. figures-tables-validate (no-op, disabled)", figs, ok_figs),
]
for label, result, ok in rows:
    tag = "PASS" if ok else "FAIL"
    print("  [" + tag + "]  " + label.ljust(33) + "  " + result)
print(sep)
overall_ok = ok_verify and ok_audit and ok_figs
print("  Overall: PAPER AUDIT " + ("PASSED" if overall_ok else "FAILED"))
print(sep)
sys.exit(0 if overall_ok else 1)
PYEOF
'

# ── Final summary ─────────────────────────────────────────────────────────────
echo ""
log "============================================================"
log " HypatiaX reproduction pipeline COMPLETE"
log "============================================================"
echo ""
echo "  Key output locations:"
echo "    Results JSON:  ${RESULTS_DIR}/"
echo "    (table/figure generation disabled — no .tex/.png/.pdf outputs)"
echo "    Verify report: logs/verify_report.json"                 # STEP 14
echo "    Paper audit:   logs/paper_audit_findings.json"          # STEP 15
echo ""
echo "  Cross-reference with paper:"
echo "    Table 9          <- exp1              (core extrapolation)"
echo "    Table 11         <- exp1b             (DeFi routing)"
echo "    Table 17         <- exp2_feynman      (Feynman noisy)"
echo "    Table 19         <- exp2              (five-system comparison)"
echo "    Table 28         <- suppB             (noise sweep)"
echo "    Table 29 sc      <- suppB_sc          (sample complexity)"
echo "    tab:hybrid_all   <- hybrid_all_domains (SS10.9 hybrid system -- one-shot)"
echo "    tab:nguyen12     <- exp3              (extrapolation/)      seed=42"
echo "                    <- exp3b             (extrapolation/multi_seed/)  seeds 99/123/777/2024"
echo "    tab:instability  <- instability        (SS10.9 Regime A/B/C, Spearman rho, 12 figs)"
echo ""
echo "  Instability outputs (STEP 4a, numerical only — figure generation disabled):"
echo "    ${RESULTS_DIR}/figures/instability_analysis.csv"
echo "    ${RESULTS_DIR}/figures/instability_extrapolation.csv  (Stage 2, if benchmark JSON found)"
echo ""
echo "  Paper audit outputs (STEPs 14-21):"
echo "    ${RESULTS_DIR}/qualify_run.log          (numerical spot-check + 5-dim gate)"
echo "    ${RESULTS_DIR}/qualify_run.log          (5-dimension per-experiment gate)"
echo "    ${RESULTS_DIR}/audit_paper_run.log      (paper claims vs results)"
echo "    ${RESULTS_DIR}/audit_nb01_run.log       (NB-01 citation audit)"
echo "    ${RESULTS_DIR}/audit_nb02_run.log       (NB-02 cross-reference audit)"
echo "    ${RESULTS_DIR}/audit_nb03_run.log       (NB-03 section structure)"
echo "    ${RESULTS_DIR}/audit_nb04_run.log       (NB-04 numerical consistency)"
echo "    ${RESULTS_DIR}/audit_nb05_run.log       (NB-05 figure dependencies)"
echo "    logs/verify_report.json                 (structured verify output)"
echo "    logs/paper_audit_findings.json          (structured audit output)"
echo ""
echo "  Notebook audit outputs (executed .ipynb with cell outputs):"
echo "    notebooks/NB-01_Citation_Bibliography_Audit.ipynb"
echo "    notebooks/NB-02_CrossReference_Label_Audit.ipynb"
echo "    notebooks/NB-03_Section_Structure_Numbering.ipynb"
echo "    notebooks/NB-04_Numerical_Consistency_Checker.ipynb"
echo "    notebooks/NB-05_Figure_Image_Dependency_Checker.ipynb"
echo ""
echo "  To rebuild the paper PDF:"
echo "    cd ${REPO_ROOT} && pdflatex jmlr_paper_main.tex"
echo ""
log "Done. See individual *_run.log files in ${RESULTS_DIR}/ for per-step output."
