#!/usr/bin/env bash
# Run the full audit check series from the repo root:
#   bash scripts/audit_checks/00_run_all_checks.sh ['RESULTS_GLOB'] ['TARGETS...']
# Writes audit/checks_report.txt. Exit 1 if any check fails.
D="$(cd "$(dirname "$0")" && pwd)"
RES="${1:-hypatiax/data/results/**/*.json}"
shift 2>/dev/null
mkdir -p audit
OUT=audit/checks_report.txt
: > "$OUT"
declare -A RC
run() { # name, command...
  local n="$1"; shift
  echo "=== $n" | tee -a "$OUT"
  "$@" 2>&1 | tee -a "$OUT" | tail -n 40
  RC[$n]=${PIPESTATUS[0]}
}
run 01_provenance_gate     python3 "$D/01_provenance_gate.py" "$RES"
run 02_static_checks       python3 "$D/02_static_checks.py"
run 03_r2_policy_selftest  python3 "$D/03_r2_policy_selftest.py" "$@"
run 04_decision_logic      python3 "$D/04_decision_logic_repro.py"
run 05_null_census         python3 "$D/05_null_census.py" "$RES"
run 06_pipeline            bash    "$D/06_pipeline_consistency.sh"
run 07_ledger_dry_run      python3 "$D/07_update_ledger.py"

echo; echo "SUMMARY (0 = clean)" | tee -a "$OUT"
bad=0
for k in $(printf '%s\n' "${!RC[@]}" | sort); do
  printf '%-26s exit %s\n' "$k" "${RC[$k]}" | tee -a "$OUT"
  [ "$k" = 05_null_census ] || [ "$k" = 07_ledger_dry_run ] || [ "${RC[$k]}" = 0 ] || bad=1
done
echo; echo "--- FAIL / MISSING lines (full report: $OUT)" | tee -a "$OUT"
grep -E "^(FAIL|MISSING)" "$OUT" | sort -u | head -80
echo "Manual items not automatable: caller of method 4 in extrap mode (train-only X?),"
echo "exp1_llm_contribution.py usage in run_all.sh, Fix 4 text decision, REL_TOL decision." | tee -a "$OUT"
exit $bad
