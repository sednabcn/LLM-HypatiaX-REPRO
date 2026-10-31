#!/usr/bin/env bash
# close_phase3.sh - preflight + close Phase 3 (leave-one-gate-out ablation).
#
# Put it in scripts/ and run from anywhere inside the repo:
#     bash scripts/close_phase3.sh
#
# Settings (environment variables, all optional):
#     OUT         results dir of run_phase3_ablation.py       [results/phase3]
#     CLOSE_OUT   where the closure manifest/CSV/marker go    [phase3_closure_out]
#     P_ROWS      glob of the P-arm rows used for G1          [archive/phase2/p2/pure_llm_seed*.jsonl]
#     MANIFEST    phase2_closure.json for the Phase 2 tie-in  [empty = tie-in skipped, non-blocking]
#     EVAL_SHA    expected sha256 prefix of r2_canonical.py   [7d5395ed]
#     SKIP_TESTS  1 = skip the pre-launch tests               [0]
# Extra arguments are passed straight to phase3_close.py (e.g. --require-phase2 --llm-optional probe).
#
# It never edits rows, never commits, and exits non-zero unless Phase 3 is CLOSED.
set -uo pipefail

OUT="${OUT:-results/phase3}"
CLOSE_OUT="${CLOSE_OUT:-phase3_closure_out}"
P_ROWS="${P_ROWS:-archive/phase2/p2/pure_llm_seed*.jsonl}"
MANIFEST="${MANIFEST:-}"
EVAL_SHA="${EVAL_SHA:-7d5395ed}"
SKIP_TESTS="${SKIP_TESTS:-0}"

die()  { echo "STOP: $*" >&2; exit 2; }
step() { echo; echo "== $*"; }

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || die "not inside a git repo"
cd "$ROOT"

# ---------------------------------------------------------------- 1. environment
step "1. environment"
[ -z "${P3_ALLOW_SAFE_R2:-}" ] && [ -z "${P3_ALLOW_UNKNOWN_META:-}" ] \
  || die "P3_ALLOW_SAFE_R2 / P3_ALLOW_UNKNOWN_META are set: those are smoke-test overrides, rows made with them cannot close Phase 3 (unset them)"
BRANCH="$(git branch --show-current)"; HEAD_SHA="$(git rev-parse HEAD)"
echo "branch: ${BRANCH:-<detached>}   HEAD: ${HEAD_SHA:0:12}"
[ -f scripts/phase3_close.py ] || die "scripts/phase3_close.py not found"
[ -f hypatiax/core/r2_canonical.py ] || die "hypatiax/core/r2_canonical.py not found"
ACTUAL_EVAL="$(sha256sum hypatiax/core/r2_canonical.py | cut -c1-8)"
echo "r2_canonical.py sha256 prefix: $ACTUAL_EVAL   (expected: $EVAL_SHA)"
[ "$ACTUAL_EVAL" = "${EVAL_SHA:0:8}" ] || die "evaluator changed since the plan ($ACTUAL_EVAL != $EVAL_SHA); rows would not match the declared evaluator"

# ---------------------------------------------------------------- 2. clean tree (same rule as the runner's git_state)
step "2. clean tree (G8)"
DIRTY="$(git status --porcelain | grep -vE "^.. \"?(${OUT%/}/|${CLOSE_OUT%/}/|p2_|phase3_out|phase3_closure_out)" || true)"
if [ -n "$DIRTY" ]; then echo "$DIRTY" | head -20; die "working tree is dirty; commit or move these (G8)"; fi
echo "clean"

# ---------------------------------------------------------------- 3. tests
if [ "$SKIP_TESTS" != "1" ]; then
  step "3. pre-launch tests"
  T=hypatiax/experiments/tests
  PYTHONPATH=".:$T" python -m pytest -q "$T/test_guess_sanitizer.py" "$T/test_engine_seed_audit.py" 2>&1 | tail -3
  [ "${PIPESTATUS[0]}" -eq 0 ] || die "tests failed"
  [ -z "$(git status --porcelain | grep -vE "^.. \"?(${OUT%/}/|${CLOSE_OUT%/}/)" || true)" ] || die "tests dirtied the tree"
fi

# ---------------------------------------------------------------- 4. result files and row sanity
step "4. result rows"
RESULTS=()
for c in full llm_acceptance pysr_prior; do
  f="$OUT/$c.jsonl"
  [ -s "$f" ] || die "missing or empty: $f"
  RESULTS+=("$f")
done
OUT="$OUT" HEAD_SHA="$HEAD_SHA" python - <<'PY' || exit 2
import json, os, sys, collections
out, head = os.environ["OUT"], os.environ["HEAD_SHA"]
bad, commits, dirty, errs, counts, keys = [], set(), 0, 0, {}, {}
for c in ("full", "llm_acceptance", "pysr_prior"):
    rows = [json.loads(l) for l in open(f"{out}/{c}.jsonl") if l.strip()]
    counts[c] = collections.Counter(r.get("status") for r in rows)
    keys[c] = {(r["equation"], int(r["seed"])) for r in rows}
    for r in rows:
        commits.add(r.get("git_commit"))
        dirty += r.get("code_dirty") is not False
        errs += r.get("status") == "error"
        if r.get("model_id") in (None, "unknown") or r.get("prompt_template_sha256") in (None, "unknown"):
            bad.append((c, r["equation"], r["seed"], "unknown model_id/prompt hash"))
        if "guesses_requested" not in r:
            bad.append((c, r["equation"], r["seed"], "no seed record"))
for c, n in counts.items():
    print(f"  {c:15s} rows={sum(n.values()):4d}  {dict(n)}")
if keys["llm_acceptance"] != keys["full"] or keys["pysr_prior"] != keys["full"]:
    print("  WARNING: arms do not cover the same (equation, seed) set; unpaired rows are dropped or fail G-checks")
print(f"  git_commit values: {sorted(str(c)[:12] for c in commits)}  (HEAD {head[:12]})")
msgs = []
if len(commits) != 1: msgs.append("rows come from more than one git_commit (G8)")
if dirty: msgs.append(f"{dirty} rows have code_dirty != False")
if errs: msgs.append(f"{errs} rows have status=error: rerun with run_phase3_ablation.py --retry-errors")
if bad: msgs.append(f"{len(bad)} rows with placeholder metadata or no seed record, first: {bad[:3]}")
if msgs:
    print("STOP: " + "; ".join(msgs), file=sys.stderr); sys.exit(1)
if commits != {head}:
    print("  note: rows were produced at an earlier commit than HEAD; fine only if the commits since touch no code")
PY
[ $? -eq 0 ] || die "row sanity failed (see above)"

# ---------------------------------------------------------------- 5. closure
step "5. phase3_close.py"
ARGS=(--results "${RESULTS[@]}" --out-dir "$CLOSE_OUT" --expected-evaluator-sha "$EVAL_SHA"
      --omit "probe:exists only in hypatiax_defi_benchmark_v3c.py, not in HDS v50_2"
      --omit "nn_augmentation:exists only in hypatiax_defi_benchmark_v3c.py, not in HDS v50_2"
      --omit "blend_weight:exists only in hypatiax_defi_benchmark_v3c.py, not in HDS v50_2"
      --omit "complexity_routing:the only complexity gate is 'if False and ...', already off in the full config")
shopt -s nullglob
PFILES=( $P_ROWS )
shopt -u nullglob
if [ "${#PFILES[@]}" -gt 0 ]; then ARGS+=(--p-rows "${PFILES[@]}"); echo "P-arm rows: ${#PFILES[@]} files"
else echo "WARNING: no files match P_ROWS='$P_ROWS'; the G1 data-hash comparison will not run"; fi
if [ -n "$MANIFEST" ]; then
  [ -f "$MANIFEST" ] || die "MANIFEST not found: $MANIFEST"
  ARGS+=(--phase2-manifest "$MANIFEST")
fi
python scripts/phase3_close.py "${ARGS[@]}" "$@"
RC=$?

# ---------------------------------------------------------------- 6. verdict
step "6. verdict"
if [ "$RC" -eq 0 ] && [ -f "$CLOSE_OUT/PHASE3_CLOSED" ]; then
  echo "PHASE 3 CLOSED"
  echo "  manifest: $CLOSE_OUT/phase3_closure.json"
  echo "  table:    $CLOSE_OUT/phase3_components.csv"
  echo "  marker:   $CLOSE_OUT/PHASE3_CLOSED"
  echo "Record it:  git add -f $CLOSE_OUT && git commit -m 'Phase 3 closure at ${HEAD_SHA:0:7}'"
  echo "            (committing results moves HEAD: do it only after every row is final)"
  exit 0
fi
echo "PHASE 3 NOT CLOSED (exit $RC). Fix the blocking checks above and rerun; no rows were modified."
exit 1
