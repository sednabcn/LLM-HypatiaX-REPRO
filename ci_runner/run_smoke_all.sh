#!/usr/bin/env bash
# ci_runner/run_smoke_all.sh -- fast smoke pipeline for run_all.sh
#
# Goal: catch broken wiring in minutes, for free. NO API key, NO Julia/PySR, NO LLM calls.
# It never executes an experiment step; it validates run_all.sh itself and its guard rails.
#
# Usage:  ./ci_runner/run_smoke_all.sh [--only s1,s2] [--keep-going] [--list]
# Env:    RUN_ALL=<path>        run_all.sh location (default: ci_runner/run_all.sh, then ./run_all.sh)
#         SMOKE_OUT=<dir>       logs + summary (default: <repo>/smoke_outputs)
#         SMOKE_HELP=auto|1|0   run `python3 <script> --help` on benchmark scripts (auto = only if torch+pysr import)
#         SMOKE_LIVE=1          also do ONE live API round-trip (needs ANTHROPIC_API_KEY, config/check_key_status.py)
#         STAGE_TIMEOUT=300     seconds per stage
#
# Stages: bash_syntax step_registry required_files failure_ledger dry_run_all cli_contract
#         clean_run_guards gt_leak_guard py_preflight script_help phase2_closure live_llm
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
cd "$REPO_ROOT"
SELF="${BASH_SOURCE[0]}"
STAGES=(bash_syntax step_registry required_files failure_ledger dry_run_all cli_contract clean_run_guards gt_leak_guard py_preflight script_help phase2_closure live_llm)

# --list / --help must work without a run_all.sh or a repo checkout
for _a in "$@"; do
  case "$_a" in
    --list) printf '%s\n' "${STAGES[@]}"; exit 0;;
    -h|--help) sed -n '2,/^set -/{/^set -/!p}' "$SELF"; exit 0;;
  esac
done


if [[ -z "${RUN_ALL:-}" ]]; then
  for c in ci_runner/run_all.sh run_all.sh; do [[ -f "$c" ]] && RUN_ALL="$c" && break; done
fi
[[ -f "${RUN_ALL:-}" ]] || { echo "ERROR: run_all.sh not found (set RUN_ALL=)" >&2; exit 2; }

SMOKE_OUT="${SMOKE_OUT:-$REPO_ROOT/smoke_outputs}"
STAGE_TIMEOUT="${STAGE_TIMEOUT:-300}"
SMOKE_HELP="${SMOKE_HELP:-auto}"
SMOKE_LIVE="${SMOKE_LIVE:-0}"
mkdir -p "$SMOKE_OUT/logs"
SCRATCH="$(mktemp -d)"; trap 'rm -rf "$SCRATCH"' EXIT

# Smoke must behave like CI and must never reuse real results.
export GITHUB_ACTIONS="${GITHUB_ACTIONS:-true}"
unset HYPATIAX_ALLOW_LEGACY HYPATIAX_R2_SIGN_FLIP LEGACY_RESULTS_DIR
export MPLBACKEND=Agg

STEP_ORDER="$(grep -m1 '^_STEP_ORDER=' "$RUN_ALL" | sed -E 's/^_STEP_ORDER="(.*)"[[:space:]]*$/\1/')"

# Benchmark entry points (same list the real workflow runs); missing files are reported, not fatal.
SCRIPTS=(
  hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py
  hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_pca.py
  hypatiax/experiments/benchmarks/portfolio_variance_v3c2.py
  hypatiax/experiments/benchmarks/exp1_ablation.py
  hypatiax/experiments/benchmarks/exp1_five_system.py
  hypatiax/experiments/benchmarks/exp1_llm_sens.py
  hypatiax/experiments/benchmarks/exp3_nguyen12_consolidated.py
  hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py
  hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py
  hypatiax/experiments/benchmarks/run_hybrid_system_benchmark.py
  hypatiax/experiments/benchmarks/run_noise_sweep_benchmark.py
  hypatiax/experiments/benchmarks/run_sample_complexity_benchmark.py
  hypatiax/experiments/benchmarks/run_instability_suite.py
  hypatiax/core/generation/hybrid_all_domains_llm_nn/hybrid_system_llm_nn_all_domains.py
)

SKIP=77
# fresh, isolated results dir per run_all.sh invocation
ra() { RESULTS_DIR="$(mktemp -d -p "$SCRATCH")/results" bash "$RUN_ALL" "$@"; }

# ---------------------------------------------------------------- stages ----
s_bash_syntax() {
  bash -n "$RUN_ALL"  && echo "OK bash -n $RUN_ALL"
  bash -n "$SELF"     && echo "OK bash -n $SELF"
  if [[ -f scripts/run_phase2_closure.sh ]]; then
    bash -n scripts/run_phase2_closure.sh && echo "OK bash -n scripts/run_phase2_closure.sh"
  fi
  if command -v shellcheck >/dev/null; then
    shellcheck -S error "$RUN_ALL" && echo "OK shellcheck (errors only)"
  else echo "shellcheck not installed - skipped"; fi
}

s_step_registry() {
  # every step in _STEP_ORDER must have a `run <step> ...` call, and vice versa
  [[ -n "$STEP_ORDER" ]] || { echo "could not parse _STEP_ORDER"; return 1; }
  local declared called
  declared="$(tr ' ' '\n' <<<"$STEP_ORDER" | sed '/^$/d' | sort -u)"
  called="$(grep -oE '^run [A-Za-z0-9_]+' "$RUN_ALL" | awk '{print $2}' | sort -u)"
  echo "steps in _STEP_ORDER: $(wc -l <<<"$declared")   run-calls: $(wc -l <<<"$called")"
  local a b rc=0
  a="$(comm -23 <(echo "$declared") <(echo "$called"))"
  b="$(comm -13 <(echo "$declared") <(echo "$called"))"
  [[ -z "$a" ]] || { echo "in _STEP_ORDER but no run call:"; echo "$a"; rc=1; }
  [[ -z "$b" ]] || { echo "run call but not in _STEP_ORDER:"; echo "$b"; rc=1; }
  [[ -z "$(tr ' ' '\n' <<<"$STEP_ORDER" | sed '/^$/d' | sort | uniq -d)" ]] || { echo "duplicate step names"; rc=1; }
  # phase2_closure is opt-in and must stay last so `--from phase2_closure` selects only it
  [[ "${STEP_ORDER##* }" == "phase2_closure" ]] || { echo "phase2_closure is no longer the last step in _STEP_ORDER"; rc=1; }
  return $rc
}

s_required_files() {
  # Files that run_all.sh turns into a hard error when absent (FAIL) vs. ones whose absence
  # only warns or silently degrades a step (WARN). Paths mirror run_all.sh defaults.
  local rc=0 f
  local bench=hypatiax/experiments/benchmarks
  for f in scripts/patches/paper_targets.json scripts/run_phase2_closure.sh; do
    if [[ -f "$f" ]]; then echo "OK   $f"; else echo "FAIL missing (step errors without it): $f"; rc=1; fi
  done
  # exp1_llm_sens needs ablation_conditions.py beside it (only checked if the runner exists)
  if [[ -f "$bench/exp1_llm_sens.py" ]]; then
    if [[ -f "$bench/ablation_conditions.py" ]]; then echo "OK   $bench/ablation_conditions.py"
    else echo "FAIL missing (exp1_llm_sens needs it): $bench/ablation_conditions.py"; rc=1; fi
  fi
  for f in \
      config/repro.yaml \
      scripts/phase2_close.py \
      hypatiax/core/r2_canonical.py \
      hypatiax/core/flags.py \
      hypatiax/protocols/experiment_protocol_defi_llm_sensitive.py \
      hypatiax/experiments/tests/test_proc_box_wiring.py \
      hypatiax/experiments/tests/test_enhanced_defi_extrapolation.py \
      notebooks/NB-01_Citation_Bibliography_Audit.ipynb \
      notebooks/NB-02_CrossReference_Label_Audit.ipynb \
      notebooks/NB-03_Section_Structure_Numbering.ipynb \
      notebooks/NB-04_Numerical_Consistency_Checker.ipynb \
      notebooks/NB-05_Figure_Image_Dependency_Checker.ipynb; do
    if [[ -f "$f" ]]; then echo "OK   $f"; else echo "WARN missing: $f"; fi
  done
  [[ $rc == 0 ]] && echo "required files OK"
  return $rc
}

s_failure_ledger() {
  # Result-producing steps must call record_failure when they swallow a non-zero exit, and the
  # ledger must turn the run red at the end.
  local rc=0 bad
  grep -q '^export -f record_failure' "$RUN_ALL" || { echo "FAIL: record_failure is not exported"; rc=1; }
  grep -q 'HYPATIAX_FAILED_LOG' "$RUN_ALL"       || { echo "FAIL: HYPATIAX_FAILED_LOG not found"; rc=1; }
  # every swallowed "exited non-zero" must record a failure (explicit non-fatal reporting steps excepted)
  bad="$(grep -n 'exited non-zero' "$RUN_ALL" | grep -v 'record_failure' | grep -v 'non-fatal' || true)"
  if [[ -n "$bad" ]]; then echo "swallowed failures without record_failure:"; echo "$bad"; rc=1; fi

  # functional: inject one record_failure just before the final summary; the run must exit 1
  local inj="$SCRATCH/run_all_injected.sh" out
  awk '/^log "Done\. See/{print "record_failure smoke_injected"} {print}' "$RUN_ALL" > "$inj"
  if ! grep -q smoke_injected "$inj"; then
    echo "FAIL: could not locate the final 'Done. See' log line to inject a failure"; rc=1
  else
    out="$(RESULTS_DIR="$(mktemp -d -p "$SCRATCH")/results" bash "$inj" --dry-run 2>&1)"; local r=$?
    [[ $r -eq 1 ]]                          || { echo "FAIL: injected failure gave exit $r (expected 1)"; rc=1; }
    grep -q 'FAILED STEPS' <<<"$out"        || { echo "FAIL: no FAILED STEPS banner"; rc=1; }
    grep -q 'smoke_injected' <<<"$out"      || { echo "FAIL: injected failure not listed"; rc=1; }
  fi
  [[ $rc == 0 ]] && echo "failure ledger OK"
  return $rc
}

s_dry_run_all() {
  # full pipeline in --dry-run: executes no step body but exercises env setup, flag
  # enforcement, arg parsing and every `run` gate; must exit 0 and announce every step
  local out="$SCRATCH/dry.log" s rc=0
  ra --dry-run >"$out" 2>&1 || { tail -40 "$out"; echo "dry-run exited non-zero"; return 1; }
  for s in $STEP_ORDER; do
    grep -q "=== STEP: ${s} " "$out" || { echo "step not reached in dry-run: $s"; rc=1; }
  done
  echo "dry-run reached $(grep -c '=== STEP:' "$out")/$(wc -w <<<"$STEP_ORDER") steps"
  return $rc
}

s_cli_contract() {
  local rc=0 s
  # --step / --from / bare step name accepted
  ra --dry-run --step exp1       >/dev/null 2>&1 || { echo "FAIL --step exp1"; rc=1; }
  ra --dry-run --from exp3       >/dev/null 2>&1 || { echo "FAIL --from exp3"; rc=1; }
  ra --dry-run suppB_sc          >/dev/null 2>&1 || { echo "FAIL bare step name"; rc=1; }
  # every step name is accepted as a bare arg (catches a step missing from the case/arg check)
  for s in $STEP_ORDER; do
    ra --dry-run "$s" >/dev/null 2>&1 || { echo "FAIL bare step name rejected: $s"; rc=1; }
  done
  # unknown arg must be rejected
  if ra --dry-run definitely_not_a_step >/dev/null 2>&1; then echo "FAIL unknown arg accepted"; rc=1; fi
  # --step runs ONLY that step
  local n; n="$(ra --dry-run --step exp1 2>&1 | grep -c '=== STEP:')"
  [[ "$n" == 1 ]] || { echo "FAIL --step exp1 announced $n steps"; rc=1; }
  # phase2_closure is opt-in: reached via --from (not --step) it must be skipped, not executed
  local out; out="$(ra --from phase2_closure 2>&1)" || { echo "FAIL --from phase2_closure exited non-zero"; echo "$out" | tail -20; rc=1; }
  grep -q 'opt-in step, skipped' <<<"$out" || { echo "FAIL: phase2_closure ran outside --step/bare invocation"; rc=1; }
  [[ $rc == 0 ]] && echo "CLI contract OK"
  return $rc
}

s_clean_run_guards() {
  # the clean-live-LLM enforcement must hold even against a hostile caller env
  local rc=0 out
  # 1) legacy mode is forbidden in CI
  if GITHUB_ACTIONS=true HYPATIAX_ALLOW_LEGACY=1 LEGACY_RESULTS_DIR="$SCRATCH/leg" ra --dry-run >/dev/null 2>&1; then
    echo "FAIL: HYPATIAX_ALLOW_LEGACY=1 not rejected in CI"; rc=1
  fi
  # 1b) outside CI, legacy mode needs LEGACY_RESULTS_DIR so it never mixes with headline results
  if env -u GITHUB_ACTIONS HYPATIAX_ALLOW_LEGACY=1 bash -c 'unset LEGACY_RESULTS_DIR; RESULTS_DIR="'"$SCRATCH"'/l1/results" bash "'"$RUN_ALL"'" --dry-run' >/dev/null 2>&1; then
    echo "FAIL: legacy mode accepted without LEGACY_RESULTS_DIR"; rc=1
  fi
  # 1c) outside CI, legacy mode with LEGACY_RESULTS_DIR is allowed and may enable the sign-flip
  if ! env -u GITHUB_ACTIONS HYPATIAX_ALLOW_LEGACY=1 HYPATIAX_R2_SIGN_FLIP=1 LEGACY_RESULTS_DIR="$SCRATCH/leg_ok" \
        RESULTS_DIR="$SCRATCH/l2/results" bash "$RUN_ALL" --dry-run >/dev/null 2>&1; then
    echo "FAIL: deliberate legacy run (LEGACY_RESULTS_DIR set, outside CI) was rejected"; rc=1
  fi
  # 2) bypass flags forced back to 1 (a NOTICE is printed)
  out="$(HYPATIAX_DISABLE_HARDCODED=0 HYPATIAX_DISABLE_PROMPT_HINTS=0 ra --dry-run --step env_check 2>&1)" \
    || { echo "FAIL dry-run with hostile flags"; rc=1; }
  grep -q 'overridden -> 1' <<<"$out" || { echo "FAIL: bypass flags not overridden"; rc=1; }
  # 3) HYPATIAX_STRICT=0 must abort
  if HYPATIAX_STRICT=0 ra --dry-run >/dev/null 2>&1; then echo "FAIL: HYPATIAX_STRICT=0 accepted"; rc=1; fi
  # 4) R2 sign-flip needs legacy mode
  if HYPATIAX_R2_SIGN_FLIP=1 ra --dry-run >/dev/null 2>&1; then echo "FAIL: R2_SIGN_FLIP=1 accepted"; rc=1; fi
  [[ $rc == 0 ]] && echo "clean-run guards OK"
  return $rc
}

s_gt_leak_guard() {
  # real (non-dry) step: pure grep over the hybrid prompt paths, no key needed
  ra --step gt_leak_guard
}

s_py_preflight() {
  # mirrors the workflow preflight: no NUL bytes in any tracked .py; every benchmark script parses;
  # the standalone python heredocs embedded in run_all.sh (provenance + shard merge) parse too
  python3 - "${SCRIPTS[@]}" <<'PY'
import ast, os, re, subprocess, sys
bad, missing = [], []
try:
    tracked = subprocess.run(["git","ls-files","*.py"],capture_output=True,text=True,check=True).stdout.split()
except (OSError, subprocess.CalledProcessError):
    # not a git checkout: fall back to walking the tree
    tracked = [os.path.join(r, n) for r, ds, fs in os.walk(".") for n in fs if n.endswith(".py")
               if not any(x in r.split(os.sep) for x in (".git", ".venv", "venv", "node_modules", "__pycache__"))]
for f in tracked:
    d = open(f,"rb").read()
    if b"\x00" in d: bad.append((f,"NUL byte(s)"))
for f in sys.argv[1:]:
    try: d = open(f,"rb").read()
    except OSError: missing.append(f); continue
    try: ast.parse(d, filename=f)
    except SyntaxError as e: bad.append((f,f"SyntaxError line {e.lineno}: {e.msg}"))
# every quoted python heredoc in run_all.sh (no shell interpolation, so valid python as written)
ra = os.environ.get("RUN_ALL", "")
n_emb = 0
if ra and os.path.isfile(ra):
    src = open(ra, errors="replace").read()
    for dash, tag, body in re.findall(r"^[^\n#]*python3?[^\n]*<<(-?)[ \t]*'(\w+)'[^\n]*\n(.*?)\n[ \t]*\2[ \t]*$", src, re.S | re.M):
        n_emb += 1
        if dash: body = re.sub(r"(?m)^\t+", "", body)   # <<- strips leading tabs
        try: ast.parse(body, filename=f"{ra}:{tag}")
        except SyntaxError as e:
            # heredocs nested in a double-quoted bash -c "..." string are unescaped by the outer
            # shell (\" -> ", \$ -> $, \\ -> \) before python sees them: retry in that form
            try: ast.parse(re.sub(r'\\([\\"$`])', r'\1', body), filename=f"{ra}:{tag}")
            except SyntaxError: bad.append((f"{ra}:{tag}", f"SyntaxError line {e.lineno}: {e.msg}"))
if ra and n_emb == 0: print("WARN no embedded python heredocs found in", ra)
for f in missing: print("WARN missing script:", f)
for f,r in bad: print("FAIL", f, r)
print(f"{len(tracked)} tracked .py checked; {len(sys.argv)-1-len(missing)} benchmark scripts parsed; {n_emb} embedded heredoc(s) parsed")
sys.exit(1 if bad else 0)
PY
}

s_script_help() {
  if [[ "$SMOKE_HELP" == 0 ]]; then echo "SMOKE_HELP=0"; return $SKIP; fi
  if [[ "$SMOKE_HELP" == auto ]] && ! python3 -c "import torch, pysr" 2>/dev/null; then
    echo "torch/pysr not installed - skipping --help import check (SMOKE_HELP=1 to force)"; return $SKIP
  fi
  local f rc=0
  for f in "${SCRIPTS[@]}"; do
    [[ -f "$f" ]] || { echo "skip (absent): $f"; continue; }
    if timeout 120 python3 "$f" --help >/dev/null 2>"$SCRATCH/h.err"; then echo "OK   $f"
    else echo "FAIL $f"; tail -5 "$SCRATCH/h.err"; rc=1; fi
  done
  return $rc
}

s_phase2_closure() {
  # the one step that needs no key/Julia/PySR: runs on COMMITTED rows
  [[ -f scripts/run_phase2_closure.sh ]] && compgen -G "archive/phase2/p2/pure_llm_*.jsonl" >/dev/null \
    && compgen -G "archive/phase2/p2/hds_*.jsonl" >/dev/null \
    || { echo "scripts/run_phase2_closure.sh or archive/phase2/p2 rows absent"; return $SKIP; }
  PHASE2_CLOSURE_OUT="$SCRATCH/p2_closure" ra phase2_closure
}

s_live_llm() {
  [[ "$SMOKE_LIVE" == 1 ]] || { echo "SMOKE_LIVE!=1"; return $SKIP; }
  [[ -n "${ANTHROPIC_API_KEY:-}" ]] || { echo "ANTHROPIC_API_KEY not set"; return 1; }
  [[ -f config/check_key_status.py ]] || { echo "config/check_key_status.py missing"; return 1; }
  python3 config/check_key_status.py
}


# ---------------------------------------------------------------- driver ----
ONLY=""; KEEP_GOING=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --only) ONLY="$2"; shift 2;;
    --keep-going) KEEP_GOING=1; shift;;
    *) echo "Unknown arg: $1" >&2; exit 2;;
  esac
done

SUMMARY="$SMOKE_OUT/summary.md"
{ echo "# run_all.sh smoke summary"; echo; echo "- run_all: \`$RUN_ALL\`"; echo
  echo "| stage | status | secs |"; echo "|---|---|---|"; } > "$SUMMARY"

fail=0
for st in "${STAGES[@]}"; do
  [[ -n "$ONLY" && ",$ONLY," != *",$st,"* ]] && continue
  echo "::group::$st"
  t0=$SECONDS
  ( set -o pipefail; timeout "$STAGE_TIMEOUT" bash -c "$(declare -f); $(declare -p SCRIPTS STEP_ORDER RUN_ALL SELF SCRATCH SMOKE_HELP SMOKE_LIVE SKIP | sed 's/^declare -[a-zA-Z-]* //;s/^/export /' ); s_$st" 2>&1 | tee "$SMOKE_OUT/logs/$st.log" )
  rc=${PIPESTATUS[0]}
  echo "::endgroup::"
  case $rc in
    0)  status=PASS;;
    77) status=SKIP;;
    124) status="FAIL (timeout)"; fail=1;;
    *)  status=FAIL; fail=1;;
  esac
  echo "| $st | $status | $((SECONDS-t0)) |" >> "$SUMMARY"
  [[ $fail == 1 && $KEEP_GOING == 0 ]] && break
done

cat "$SUMMARY"
[[ -n "${GITHUB_STEP_SUMMARY:-}" ]] && cat "$SUMMARY" >> "$GITHUB_STEP_SUMMARY"
exit $fail
