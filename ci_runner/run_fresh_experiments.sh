#!/usr/bin/env bash
# Run the experiment stages against a fresh, isolated output directory.
# Deliberately excludes validate/qualify/audit_* stages that compare against
# historical paper targets. New results are assessed separately after the run.
set -Eeuo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
RUN_ALL="${RUN_ALL:-${REPO_ROOT}/run_all.sh}"
PROTOCOL="${REPRO_CFG:-${REPO_ROOT}/config/fresh_rerun.yaml}"
[[ -f "$PROTOCOL" ]] || { echo "ERROR: fresh protocol not found: $PROTOCOL" >&2; exit 2; }
PROTOCOL="$(cd "$(dirname "$PROTOCOL")" && pwd -P)/$(basename "$PROTOCOL")"
export REPRO_CFG="$PROTOCOL"

# Primary fresh run: deferred instability diagnostics and Phase 2/3 ablations are excluded.
STAGES=(
  env_check
  gt_leak_guard
  exp1
  exp1b
  portfolio
  portfolio_random_holdout
  portfolio_bootstrap_pca
  portfolio_feature_ranking
  portfolio_pca_tail_error
  exp1_ablation
  exp1_ablation_aggregate
  exp1_four_way_matched
  exp1_pca
  exp1b_pca
  extrap
  hybrid_all_domains
  exp2_feynman
  exp2_feynman_pca_4060
  exp2_feynman_extrap
  exp2_protocol30_random_8020
  exp2_protocol30_pca_4060
  exp2
  exp2_five
  exp3
  exp3b
  suppA
  suppB
  suppB_sc
)

usage() {
  cat <<'USAGE'
Usage:
  bash ci_runner/run_fresh_experiments.sh --list
  bash ci_runner/run_fresh_experiments.sh --dry-run
  RESULTS_DIR=/absolute/path/outside/repo bash ci_runner/run_fresh_experiments.sh

The real run requires the pinned experiment dependencies, Julia 1.11/PySR,
and ANTHROPIC_API_KEY. It performs one live LLM API preflight call and a tiny
synthetic PySR warm-up before benchmarks; neither is counted as experiment data.
RESULTS_DIR must be a new or empty directory outside the repository. Outputs,
logs, Python freeze, Julia status, and Julia manifests are kept there; nothing
is committed.

Historical comparison stages (validate, qualify, audit_paper, audit_*) are
intentionally excluded. Pure-LLM Phase 2 and Phase 3 are also deferred until their
fresh-input protocols and gates are complete; historical p2/ or phase2_out/ rows
must never be substituted.
USAGE
}

case "${1:-}" in
  --help|-h) usage; exit 0 ;;
  --list)
    printf '%s\n' "${STAGES[@]}"
    exit 0
    ;;
  --dry-run)
    [[ -f "$RUN_ALL" ]] || { echo "ERROR: run_all.sh not found: $RUN_ALL" >&2; exit 2; }
    for stage in "${STAGES[@]}"; do
      echo "===== DRY RUN: $stage ====="
      bash "$RUN_ALL" --dry-run --step "$stage"
    done
    exit 0
    ;;
  "") ;;
  *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
esac

[[ -f "$RUN_ALL" ]] || { echo "ERROR: run_all.sh not found: $RUN_ALL" >&2; exit 2; }
[[ -f "$PROTOCOL" ]] || { echo "ERROR: fresh protocol not found: $PROTOCOL" >&2; exit 2; }
[[ "${HYPATIAX_ALLOW_LEGACY:-0}" != "1" ]] || {
  echo "ERROR: legacy mode is forbidden for fresh reruns" >&2
  exit 2
}
[[ -n "${RESULTS_DIR:-}" ]] || {
  echo "ERROR: set RESULTS_DIR to a new absolute path outside the repository" >&2
  exit 2
}
[[ "$RESULTS_DIR" == /* ]] || {
  echo "ERROR: RESULTS_DIR must be an absolute path: $RESULTS_DIR" >&2
  exit 2
}

mkdir -p "$(dirname "$RESULTS_DIR")"
if [[ -e "$RESULTS_DIR" ]]; then
  [[ -d "$RESULTS_DIR" ]] || { echo "ERROR: RESULTS_DIR exists and is not a directory" >&2; exit 2; }
  if find "$RESULTS_DIR" -mindepth 1 -maxdepth 1 -print -quit | grep -q .; then
    echo "ERROR: RESULTS_DIR is not empty; refusing to reuse old results/checkpoints: $RESULTS_DIR" >&2
    exit 2
  fi
else
  mkdir -p "$RESULTS_DIR"
fi
RESULTS_DIR="$(cd "$RESULTS_DIR" && pwd -P)"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"
case "$RESULTS_DIR/" in
  "$REPO_ROOT/"*)
    echo "ERROR: RESULTS_DIR must be outside the repository to prevent output contamination" >&2
    exit 2
    ;;
esac

if [[ -n "$(git -C "$REPO_ROOT" status --porcelain --untracked-files=all)" ]]; then
  echo "ERROR: repository checkout is not clean; refusing to start" >&2
  git -C "$REPO_ROOT" status --short
  exit 2
fi

# Results are git-ignored in this repository, so also fingerprint the historical
# results tree and refuse to continue if any old file is added, removed or changed.
historical_results_fingerprint() {
  local historical_dir="$REPO_ROOT/hypatiax/data/results"
  if [[ -d "$historical_dir" ]]; then
    # Hash file contents as well as relative paths; size/mtime alone can miss
    # edits that preserve both metadata fields.
    (
      cd "$historical_dir"
      find . -type f -print0 | LC_ALL=C sort -z | xargs -0 -r sha256sum
    ) | sha256sum | awk '{print $1}'
  else
    printf 'absent\n'
  fi
}
HISTORICAL_RESULTS_BASELINE="$(historical_results_fingerprint)"
printf '%s\n' "$HISTORICAL_RESULTS_BASELINE" > "$RESULTS_DIR/historical-results-baseline.sha256"

# Force the clean live-LLM path. Remove any inherited replay/cache configuration:
# every LLM request in this run must be a live API call, not a historical replay.
export HYPATIAX_DISABLE_HARDCODED=1
export HYPATIAX_DISABLE_PROMPT_HINTS=1
export HYPATIAX_R2_SIGN_FLIP=0
export HYPATIAX_STRICT=1
export PYTHONHASHSEED="${PYTHONHASHSEED:-0}"
export RESULTS_DIR
export HYPATIAX_RESULTS_DIR="$RESULTS_DIR"
export OUT_BASE="$RESULTS_DIR"
export REPRO_CFG="$PROTOCOL"
unset HYPATIAX_LLM_CACHE_DIR HYPATIAX_LLM_REPLAY_DIR HYPATIAX_LLM_FREEZE_CACHE
unset CLEAR_CHECKPOINT
unset LLM_TEMPERATURE LLM_MODEL HYPATIAX_LLM_MODEL
mapfile -t _FRESH_LLM_SETTINGS < <(python3 - "$PROTOCOL" <<'PY'
import sys, yaml
cfg = yaml.safe_load(open(sys.argv[1], encoding="utf-8")) or {}
print(cfg.get("llm_model", "claude-sonnet-4-6"))
print(cfg.get("llm_temperature", 0.25))
routing = cfg.get("routing_policy") or {}
tau = routing.get("degradation_tau")
print("" if tau is None else tau)
print(routing.get("training_edge_fraction", 0.15))
PY
)
if [[ "${#_FRESH_LLM_SETTINGS[@]}" -lt 4 ]]; then
  echo "ERROR: could not read model/temperature/routing settings from fresh protocol" >&2
  exit 2
fi
export HYPATIAX_LLM_MODEL="${_FRESH_LLM_SETTINGS[0]}"
export LLM_MODEL="${_FRESH_LLM_SETTINGS[0]}"
export LLM_TEMPERATURE="${_FRESH_LLM_SETTINGS[1]}"
if [[ -n "${_FRESH_LLM_SETTINGS[2]:-}" ]]; then
  export HYPATIAX_ROUTING_DELTA_TAU="${_FRESH_LLM_SETTINGS[2]}"
else
  unset HYPATIAX_ROUTING_DELTA_TAU
fi
export HYPATIAX_ROUTING_EDGE_FRACTION="${_FRESH_LLM_SETTINGS[3]}"
unset _FRESH_LLM_SETTINGS
mkdir -p "$RESULTS_DIR/logs"
cp "$PROTOCOL" "$RESULTS_DIR/protocol.yaml"

MANIFEST="$RESULTS_DIR/run_manifest.json"
python3 - "$MANIFEST" "$REPO_ROOT" "$PROTOCOL" "$RESULTS_DIR" <<'PY'
import datetime, hashlib, json, os, platform, subprocess, sys
from pathlib import Path
import yaml

manifest_path, repo, protocol, results_dir = map(Path, sys.argv[1:])
cfg = yaml.safe_load(protocol.read_text(encoding="utf-8")) or {}
if any("expected" in section for section in (cfg.get("benchmarks") or {}).values()):
    raise SystemExit("fresh protocol must not contain historical expected-result targets")
def git(*args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()

try:
    protocol_reference = str(protocol.relative_to(repo))
except ValueError:
    # REPRO_CFG may intentionally point outside the checkout. Preserve its
    # absolute location rather than failing manifest creation before stage 1.
    protocol_reference = str(protocol)

manifest = {
    "status": "started",
    "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "repository_commit": git("rev-parse", "HEAD"),
    "repository_branch": git("branch", "--show-current"),
    "repository_clean_at_start": True,
    "python": sys.version,
    "platform": platform.platform(),
    "protocol_file": protocol_reference,
    "protocol_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(),
    "protocol": {
        "run_id": cfg.get("run_id"),
        "seeds": cfg.get("seeds"),
        "llm_model": cfg.get("llm_model"),
        "llm_temperature": cfg.get("llm_temperature"),
        "routing_policy": cfg.get("routing_policy"),
        "llm_retries": cfg.get("llm_retries"),
        "llm_k_runs": cfg.get("llm_k_runs"),
        "timeouts": cfg.get("timeouts"),
        "pysr": cfg.get("pysr"),
        "fresh_run_controls": cfg.get("fresh_run_controls"),
        "deferred_experiments": cfg.get("deferred_experiments"),
    },
    "results_dir": str(results_dir),
    "api_key_present": bool(os.environ.get("ANTHROPIC_API_KEY")),
    "clean_run_flags": {
        "HYPATIAX_DISABLE_HARDCODED": os.environ.get("HYPATIAX_DISABLE_HARDCODED"),
        "HYPATIAX_DISABLE_PROMPT_HINTS": os.environ.get("HYPATIAX_DISABLE_PROMPT_HINTS"),
        "HYPATIAX_R2_SIGN_FLIP": os.environ.get("HYPATIAX_R2_SIGN_FLIP"),
        "HYPATIAX_STRICT": os.environ.get("HYPATIAX_STRICT"),
    },
    "cache_roots": {
        "HYPATIAX_LLM_CACHE_DIR": os.environ.get("HYPATIAX_LLM_CACHE_DIR"),
        "HYPATIAX_LLM_REPLAY_DIR": os.environ.get("HYPATIAX_LLM_REPLAY_DIR"),
    },
    "historical_result_comparison": False,
    "historical_cache_reuse": False,
    "excluded_stages": ["validate", "qualify", "audit_paper", "pure_llm_phase2", "phase3_ablation", "instability", "audit_setup", "audit_nb01", "audit_nb02", "audit_nb03", "audit_nb04", "audit_nb05", "audit_nb06_fixc3_disclosure", "audit_nb06_fixc3_rerun", "audit_guard", "audit_print_verify", "audit_print_findings", "audit_figures_tables", "audit_final_gate"],
    "stages": [],
}
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
PY

record_stage() {
  python3 - "$MANIFEST" "$1" "$2" <<'PY'
import datetime, json, sys
path, stage, status = sys.argv[1:]
data = json.load(open(path, encoding="utf-8"))
data.setdefault("stages", []).append({
    "stage": stage,
    "status": status,
    "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
})
data["status"] = "failed" if status == "failed" else data["status"]
if status == "failed":
    data["failed_stage"] = stage
json.dump(data, open(path, "w", encoding="utf-8"), indent=2)
with open(path, "a", encoding="utf-8") as stream:
    stream.write("\n")
PY
}

for stage in "${STAGES[@]}"; do
  echo "===== FRESH EXPERIMENT STAGE: $stage ====="
  if bash "$RUN_ALL" --step "$stage" 2>&1 | tee "$RESULTS_DIR/logs/$stage.log"; then
    record_stage "$stage" "passed"
  else
    record_stage "$stage" "failed"
    echo "ERROR: stage '$stage' failed; partial outputs retained in $RESULTS_DIR" >&2
    exit 1
  fi

  if [[ "$stage" == "env_check" ]]; then
    echo "Performing a live API round-trip with the protocol model/temperature..."
    if python3 "$REPO_ROOT/config/check_key_status.py" 2>&1 | tee "$RESULTS_DIR/logs/live-llm-preflight.log"; then
      record_stage "live_llm_preflight" "passed"
    else
      record_stage "live_llm_preflight" "failed"
      echo "ERROR: live LLM preflight failed; no benchmark stages will run" >&2
      exit 1
    fi
    echo "Warming PySR/Julia with a tiny synthetic fit (not a benchmark result)..."
    if timeout 900s python3 - "$RESULTS_DIR" <<'PY' > "$RESULTS_DIR/logs/pysr-warmup.log" 2>&1
import sys
from pathlib import Path
import numpy as np
from pysr import PySRRegressor

out = Path(sys.argv[1]) / "pysr_warmup"
out.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(0)
X = rng.normal(size=(20, 1))
y = 2.0 * X[:, 0] + 1.0
model = PySRRegressor(
    niterations=5,
    populations=1,
    maxsize=7,
    verbosity=0,
    progress=False,
    tempdir=str(out),
)
model.fit(X, y)
print("PySR/Julia warm-up OK; this synthetic fit is excluded from experiment outputs.")
PY
    then
      record_stage "pysr_warmup" "passed"
    else
      warmup_rc=$?
      record_stage "pysr_warmup" "failed"
      echo "ERROR: PySR/Julia warm-up failed (exit $warmup_rc); see $RESULTS_DIR/logs/pysr-warmup.log" >&2
      exit "$warmup_rc"
    fi
    echo "Capturing exact Python and Julia runtime provenance..."
    python3 -m pip freeze --all > "$RESULTS_DIR/python-environment-freeze.txt"
    python3 - <<'PY' > "$RESULTS_DIR/python-runtime-versions.txt"
from importlib.metadata import version
import platform, sys
if sys.version_info[:2] != (3, 12):
    raise SystemExit(f"fresh rerun requires Python 3.12.x, got {sys.version}")
print("python", sys.version)
print("platform", platform.platform())
expected = {
    "pysr": "2.0.0a1",
    "anthropic": "0.73.0",
    "torch": "2.12.1+cpu",
    "numpy": "2.3.5",
    "scipy": "1.16.3",
    "sympy": "1.14.0",
    "pandas": "2.3.3",
    "scikit-learn": "1.7.2",
    "PyYAML": "6.0.3",
}
for package, wanted in expected.items():
    actual = version(package)
    print(package, actual)
    if actual != wanted:
        raise SystemExit(f"{package} version mismatch: expected {wanted}, got {actual}")
PY
    if ! command -v julia >/dev/null 2>&1; then
      echo "ERROR: Julia is not on PATH; the fresh run requires Julia 1.11.x" >&2
      record_stage "$stage" "failed"
      exit 1
    fi
    julia --version | tee "$RESULTS_DIR/julia-version.txt"
    if ! grep -Eq '1\.11\.' "$RESULTS_DIR/julia-version.txt"; then
      echo "ERROR: fresh rerun requires Julia 1.11.x" >&2
      record_stage "$stage" "failed"
      exit 1
    fi
    julia -e 'using Pkg; Pkg.status()' > "$RESULTS_DIR/julia-package-status.txt" 2>&1
    mkdir -p "$RESULTS_DIR/julia-manifests"
    while IFS= read -r -d '' manifest; do
      rel="${manifest#"$HOME/.julia/"}"
      dest="$RESULTS_DIR/julia-manifests/${rel//\//_}"
      cp "$manifest" "$dest"
    done < <(find "$HOME/.julia" -maxdepth 5 -type f -name Manifest.toml -print0 2>/dev/null)
    if ! find "$RESULTS_DIR/julia-manifests" -type f -name '*Manifest.toml' -print -quit | grep -q .; then
      echo "ERROR: no Julia Manifest.toml found after environment preflight" >&2
      record_stage "$stage" "failed"
      exit 1
    fi
    (cd "$RESULTS_DIR/julia-manifests" && sha256sum *Manifest.toml > SHA256SUMS)
  fi

  if [[ -n "$(git -C "$REPO_ROOT" status --porcelain --untracked-files=all)" ]]; then
    record_stage "$stage" "failed"
    echo "ERROR: stage '$stage' wrote files into the repository checkout; stopping to protect source/history" >&2
    git -C "$REPO_ROOT" status --short
    exit 1
  fi
  if [[ "$(historical_results_fingerprint)" != "$HISTORICAL_RESULTS_BASELINE" ]]; then
    record_stage "$stage" "failed"
    echo "ERROR: stage '$stage' touched hypatiax/data/results; stopping to protect historical outputs/checkpoints" >&2
    exit 1
  fi
done

python3 - "$MANIFEST" <<'PY'
import datetime, json, sys
path = sys.argv[1]
data = json.load(open(path, encoding="utf-8"))
data["status"] = "completed"
data["historical_results_unchanged"] = True
data["completed_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
json.dump(data, open(path, "w", encoding="utf-8"), indent=2)
with open(path, "a", encoding="utf-8") as stream:
    stream.write("\n")
PY

echo "Fresh experiment stages completed. Outputs: $RESULTS_DIR"
echo "Manifest: $MANIFEST"
