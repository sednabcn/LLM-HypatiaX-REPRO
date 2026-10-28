#!/usr/bin/env bash
# phase2_finalize.sh -- cleanup, decision log, closure re-run and tag for Phase 2.
#
# SCOPE (read this first): this closes Phase 2a = PySR-only vs HDS v50_2, WITH CAVEATS.
# It does NOT close the Pure LLM baseline arm of Option 3's Phase 2. That arm has no
# runner and no result rows yet; the script records it as an OPEN item, not as done.
#
# Usage (from the repo root):
#   bash phase2_finalize.sh            # dry run: read-only checks + prints what it WOULD change
#   bash phase2_finalize.sh --apply    # performs the changes (local commits and tag only)
#   bash phase2_finalize.sh --apply --push   # also pushes branch and tag
#   --known-fail NODEID   deselect a pytest test you have diagnosed as out of scope; it is
#                         recorded as an OPEN item in the closure record (repeatable)
set -euo pipefail

# ---------------------------------------------------------------- settings
BASE_BRANCH="${BASE_BRANCH:-audit/step1-cleanup}"
FIX_BRANCH="${FIX_BRANCH:-phase2-fix-labels}"
P1_TAG="phase1-closed"; P1_SHA="9d56d8c"
CLOSE_TAG="phase2-closed-with-caveats"
CAP_S=1400                     # PySR-only budget the HDS rows are compared against
TODAY="$(date +%F)"

# ---- DECISIONS: recommended values. Edit before --apply if you disagree. ----
# D3 (prompt inputs): settled from the code, clean flag -> domain, variable names,
#     data-pattern statistics, constants block; equation name withheld. Already in YAML.
# D5 (parity): Pure LLM arm also returns the same number of candidates as HDS, and
#     the winner is picked on TRAINING R2 only (never on extrapolation R2).
D5_CANDIDATES=3
D5_SELECTION="training R2 only"
# Values read from the HDS stage (temperature, max_tokens). The Pure LLM runner must match.
CFG_TEMPERATURE=0.3
CFG_MAX_TOKENS=2000
CFG_MAX_CALLS=1                # CONFIRM against HDS code: LLM calls per case (3 candidates per call)

APPLY=0; PUSH=0; KNOWN_FAIL=()
usage(){ sed -n '2,16p' "$0"; }
while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1;; --push) PUSH=1;; -h|--help) usage; exit 0;;
    --known-fail) shift; [ $# -gt 0 ] || { echo "--known-fail needs a pytest node id"; exit 1; }; KNOWN_FAIL+=("$1");;
    *) echo "unknown option: $1"; usage; exit 1;;
  esac
  shift
done

say(){ printf '\n==> %s\n' "$*"; }
warn(){ printf 'WARN: %s\n' "$*" >&2; WARNINGS+=("$*"); }
die(){ printf 'ERROR: %s\n' "$*" >&2; exit 1; }
run(){ if [ "$APPLY" -eq 1 ]; then echo "+ $*"; "$@"; else echo "[dry-run] $*"; fi; }
WARNINGS=()
[ "$APPLY" -eq 1 ] && echo "MODE: APPLY" || echo "MODE: dry run (nothing is changed; add --apply)"

# ---------------------------------------------------------------- 0. preflight
say "0. Preflight"
git rev-parse --show-toplevel >/dev/null 2>&1 || die "not inside a git repository"
cd "$(git rev-parse --show-toplevel)"
command -v python3 >/dev/null || die "python3 not found"
for f in scripts/phase2_close.py scripts/reflatten_fields.py; do
  [ -f "$f" ] || die "missing $f"
done
[ -d p2 ] || die "missing p2/ (the Phase 2 rows must be present)"
if ! git diff --quiet || ! git diff --cached --quiet; then
  die "uncommitted changes to tracked files; commit or stash them first"
fi
got="$(git rev-parse "$P1_TAG^{commit}" 2>/dev/null || true)"
case "$got" in
  "$P1_SHA"*) echo "OK: $P1_TAG -> ${got:0:7}";;
  "") die "tag $P1_TAG not found";;
  *) die "tag $P1_TAG points at ${got:0:7}, expected $P1_SHA";;
esac

# ---------------------------------------------------------------- 1. merge label fix
say "1. Merge $FIX_BRANCH into $BASE_BRANCH"
git rev-parse --verify -q "$FIX_BRANCH" >/dev/null || run git fetch origin "$FIX_BRANCH:$FIX_BRANCH"
run git checkout "$BASE_BRANCH"
if git merge-base --is-ancestor "$FIX_BRANCH" "$BASE_BRANCH" 2>/dev/null; then
  echo "already merged"
else
  run git merge --no-ff "$FIX_BRANCH" -m "Merge $FIX_BRANCH: fix better/worse labels for lower-is-better metrics"
fi

# ---------------------------------------------------------------- 2. YAML placement
say "2. Config must not live in .github/workflows/"
if [ -f .github/workflows/phase2_pure_llm_config.yaml ]; then
  run git mv .github/workflows/phase2_pure_llm_config.yaml phase2_pure_llm_config.yaml
else
  echo "nothing in .github/workflows/ to move"
fi

# ---------------------------------------------------------------- 3. cleanup
say "3. Cleanup of superseded scripts (reversible: git history keeps everything)"
if [ -f scripts/phase2_close_v2.py ]; then
  same_as_history=0
  if cmp -s scripts/phase2_close.py scripts/phase2_close_v2.py; then same_as_history=1; else
    for h in $(git log --format=%H -- scripts/phase2_close.py); do
      if git show "$h:scripts/phase2_close.py" 2>/dev/null | cmp -s - scripts/phase2_close_v2.py; then same_as_history=1; break; fi
    done
  fi
  if [ "$same_as_history" -eq 1 ]; then
    run git rm -q scripts/phase2_close_v2.py
  else
    warn "scripts/phase2_close_v2.py matches no version of phase2_close.py; left in place"
  fi
fi
run mkdir -p scripts/archive
while IFS= read -r f; do
  [ -n "$f" ] || continue
  name="$(basename "$f" .py)"
  refs="$(git grep -lw "$name" -- . ':!scripts/flatten_results*' ':!scripts/archive' || true)"
  if [ -z "$refs" ]; then
    run git mv "$f" "scripts/archive/$(basename "$f")"
  else
    warn "$f is still referenced by: $(echo "$refs" | tr '\n' ' ')- left in place"
  fi
done < <(git ls-files 'scripts/flatten_results*.py')
[ -f scripts/phase3_close.py ] && warn "scripts/phase3_close.py not reviewed; left untouched"

# ---------------------------------------------------------------- 4. tests
say "4. Test suite"
if python3 -m pytest --version >/dev/null 2>&1; then
  DESEL=(); for k in "${KNOWN_FAIL[@]:-}"; do [ -n "$k" ] && DESEL+=(--deselect "$k") && warn "known failing test deselected: $k"; done
  if ! python3 -m pytest -q "${DESEL[@]}"; then
    if [ "$APPLY" -eq 1 ]; then die "tests failed; stop before closing (diagnose, fix, or pass --known-fail NODEID)"
    else warn "tests failed (an --apply run would stop here)"; fi
  fi
else
  warn "pytest not installed; tests NOT run"
fi

# ---------------------------------------------------------------- 5. data checks (read-only)
say "5. Data integrity checks"
python3 scripts/reflatten_fields.py --check-only || die "r2 != extrap_r2_far for some rows (see exit code 2/3 in reflatten_fields.py --help)"

OBS="$(python3 - "$CAP_S" <<'PY'
import glob, json, math, statistics, sys
cap = float(sys.argv[1])
rows = [json.loads(l) for f in sorted(glob.glob("p2/hds_*.jsonl")) for l in open(f) if l.strip()]
if not rows: sys.exit("no HDS rows found in p2/")
t = [r["runtime_s"] for r in rows]
over = sum(v > cap for v in t)
extra = [k for k in rows[0] if "attempt" in k.lower() or "retr" in k.lower()]
note = "attempt-count field(s): %s" % extra if extra else "no attempt/retry field in rows; runtime_s may cover only the final attempt"
print("observed: %d/%d HDS rows exceeded %d s (max %.0f s, median %.0f s); cap %s (%s)"
      % (over, len(t), cap, max(t), statistics.median(t), "did not bind" if over == 0 else "BOUND", note))
PY
)"
echo "$OBS"

echo "Non-finite / catastrophic HDS rows (HDS should not produce -inf):"
python3 - <<'PY'
import glob, json, math
bad = []
for f in sorted(glob.glob("p2/hds_*.jsonl")):
    for l in open(f):
        if not l.strip(): continue
        r = json.loads(l); v = r.get("r2")
        if v is None or (isinstance(v, float) and (math.isinf(v) or math.isnan(v))) or (isinstance(v, (int, float)) and v < -10):
            bad.append({k: r.get(k) for k in ("equation", "case", "seed", "r2", "generation_path") if k in r})
print("  none" if not bad else "\n".join("  %s" % b for b in bad))
PY

# ---------------------------------------------------------------- 6. closure runs
say "6. Re-run closure on primary (far) and sensitivity (medium, train) fields"
DECLARE="HDS: 3 attempts x 1100 s + 300 s = 3600 s; PySR-only: 1 attempt x 1100 s + 300 s = 1400 s. ${OBS}"
if [ "$APPLY" -eq 1 ]; then python3 scripts/reflatten_fields.py --force; else echo "[dry-run] python3 scripts/reflatten_fields.py --force"; fi
close(){ # <rows dir> <out dir>
  run python3 scripts/phase2_close.py --pure-llm "$1"/pysr_*.jsonl --hds "$1"/hds_*.jsonl \
    --a-name pysr_only --out-dir "$2" --declare-unequal-timeout "$DECLARE"
}
close p2        phase2_out          # PRIMARY: extrap_r2_far
close p2_med    phase2_out_p2_med   # sensitivity
close p2_train  phase2_out_p2_train # sensitivity

# ---------------------------------------------------------------- 7. decisions + config
say "7. Decision log and config values"
if [ "$APPLY" -eq 1 ]; then
  if [ -f phase2_pure_llm_config.yaml ]; then
    python3 - phase2_pure_llm_config.yaml "temperature=$CFG_TEMPERATURE" "max_tokens=$CFG_MAX_TOKENS" "max_calls_per_case=$CFG_MAX_CALLS" <<'PY'
import re, sys
p = sys.argv[1]; s = open(p).read()
for kv in sys.argv[2:]:
    k, v = kv.split("=", 1)
    s, n = re.subn(r'(?m)^(\s*%s\s*:\s*)null(\s*(#.*)?)$' % re.escape(k), r'\g<1>%s\g<2>' % v, s)
    print("  %-20s %s" % (k, "set to %s" % v if n else "not null or not found; unchanged"))
open(p, "w").write(s)
PY
  else
    warn "phase2_pure_llm_config.yaml not found at repo root"
  fi
  if ! grep -q "Amendment A1" phase2_pure_llm_amendments.md 2>/dev/null; then
    cat >> phase2_pure_llm_amendments.md <<EOF
# Phase 2 Pure LLM run: amendments log

## Amendment A1 (${TODAY})
- D3 settled: prompt inputs are domain, variable names, data-pattern statistics and constants block; equation name withheld.
- D5 decided: Pure LLM arm returns ${D5_CANDIDATES} candidates (matching HDS) and the winner is chosen on ${D5_SELECTION}. If the runner cannot do this, the difference must be labelled in the report.
- Config: temperature=${CFG_TEMPERATURE}, max_tokens=${CFG_MAX_TOKENS}, max_calls_per_case=${CFG_MAX_CALLS} (CONFIRM max_calls_per_case against the HDS code).
- OPEN (blocks any Pure LLM run): PureLLMBaseline sends no temperature and uses max_tokens=4000, while the HDS stage reads 0.3 / 2000. Confirm what is actually sent and align or label it.
- OPEN: PureLLMBaseline prompt not yet compared with the HDS prompt; prompt_template_sha256 not frozen.
- OPEN: D6 (see spec) not recorded here; settle it in the spec itself.
EOF
  else
    echo "Amendment A1 already present"
  fi
else
  echo "[dry-run] would fill null config values and write phase2_pure_llm_amendments.md (A1)"
fi

# ---------------------------------------------------------------- 8. closure record, commit, tag
say "8. Closure record, commit, tag"
if [ "$APPLY" -eq 1 ]; then
  mkdir -p docs
  cat > docs/phase2_closure_record.md <<EOF
# Phase 2 closure record (${TODAY})

**Status: CLOSED WITH CAVEATS. Scope is PySR-only vs HDS v50_2 only. The Pure LLM arm is NOT done.**

- Branch: ${BASE_BRANCH} @ $(git rev-parse --short HEAD) (before this commit)
- Primary field: extrap_r2_far (closure in phase2_out/); sensitivity: extrap_r2_medium (phase2_out_p2_med/), train_r2 (phase2_out_p2_train/)
- Result: HDS ahead on recovery, but intervals include zero and sign tests are underpowered; a suggestive direction, not a demonstrated improvement. Do not report mean R2 (-inf rows).
- Time budgets declared unequal (3600 s vs 1400 s). ${OBS}
- Medium adds no independent evidence; train R2 is noise-capped near 0.9975.

## Open items
1. Pure LLM baseline: no runner, no rows. Needs D5 parity, prompt parity check, temperature/max_tokens alignment, frozen prompt hash.
2. Phase 1 evaluator row (Listing 8 vs r2_checked) still "Unverified" in AUDIT/phase1_audit.json; manual comparison required.
3. runtime_s accounting: confirm it includes LLM time and all retries.
4. Phase 3 ablations: no result files; runners must log config_diff, r2_raw and r2_status.
5. scripts/phase3_close.py not reviewed.
$(for k in "${KNOWN_FAIL[@]:-}"; do [ -n "$k" ] && echo "6. Known failing test, deselected: $k"; done)
EOF
  git add -A docs/phase2_closure_record.md phase2_pure_llm_amendments.md phase2_pure_llm_config.yaml \
            phase2_out phase2_out_p2_med phase2_out_p2_train p2_med p2_train scripts 2>/dev/null || true
  if git diff --cached --quiet; then echo "nothing to commit"; else
    git commit -q -m "Phase 2 (PySR-only vs HDS): close with caveats; cleanup, decision log, closure re-run"
  fi
  if git rev-parse -q --verify "refs/tags/$CLOSE_TAG" >/dev/null; then echo "tag $CLOSE_TAG already exists"; else
    git tag -a "$CLOSE_TAG" -m "Phase 2a closed with caveats (PySR-only vs HDS). Pure LLM arm open."
  fi
  [ "$PUSH" -eq 1 ] && git push origin "$BASE_BRANCH" "$CLOSE_TAG"
else
  echo "[dry-run] would write docs/phase2_closure_record.md, commit, tag $CLOSE_TAG"
fi

say "Done"
if [ "${#WARNINGS[@]}" -gt 0 ]; then
  echo "Warnings (${#WARNINGS[@]}):"; printf '  - %s\n' "${WARNINGS[@]}"
fi
[ "$APPLY" -eq 1 ] && [ "$PUSH" -eq 0 ] && echo "Local only. Push with: git push origin $BASE_BRANCH $CLOSE_TAG"
echo "Reminder: the Pure LLM baseline is still open, so Phase 2 is closed only for PySR-only vs HDS."
