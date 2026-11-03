#!/usr/bin/env bash
# tidy_root_dryrun.sh
# Move audit / phase2 / triage history out of the repo root into archive/.
#
#   ./tidy_root_dryrun.sh            dry run: prints each move and any path
#                                    references in tracked files that would break
#   ./tidy_root_dryrun.sh --apply    performs the moves (git mv when tracked)
#
# Run from the repo root. Nothing is deleted.

set -u
APPLY=0
[[ "${1:-}" == "--apply" ]] && APPLY=1

if [[ ! -f pyproject.toml || ! -d hypatiax ]]; then
  echo "Run this from the repo root (pyproject.toml and hypatiax/ expected)." >&2
  exit 1
fi

# source|destination  (AUDIT/audit/audit_out get distinct targets so the
# audit vs AUDIT case collision on macOS/Windows cannot bite)
MOVES=(
  # audit
  "audit|archive/audit/patches_audit"
  "AUDIT|archive/audit/manifests"
  "audit_out|archive/audit/audit_out"
  "bypass_audit.csv|archive/audit/bypass_audit.csv"
  "audit_results_manifest.py|archive/audit/audit_results_manifest.py"
  # phase 2
  "phase2_out|archive/phase2/phase2_out_root"
  "phase2_finish_out|archive/phase2/phase2_finish_out"
  "p2|archive/phase2/p2"
  "p2_dry|archive/phase2/p2_dry"
  "phase2_a3_p_kwargs.json|archive/phase2/phase2_a3_p_kwargs.json"
  "phase2_row_schema.json|archive/phase2/phase2_row_schema.json"
  "p2_pure_llm_status_relabel.json|archive/phase2/p2_pure_llm_status_relabel.json"
  "phase2_pure_llm_amendments.md|archive/phase2/phase2_pure_llm_amendments.md"
  "phase2_pure_llm_config.yaml|archive/phase2/phase2_pure_llm_config.yaml"
  # triage
  "triage_out|archive/triage/triage_out"
  # stray results
  "exp1_ablation_results.json|archive/results_snapshots/root_strays/exp1_ablation_results.json"
  "exp1_llm_contribution.json|archive/results_snapshots/root_strays/exp1_llm_contribution.json"
  "exp1_rf01_mannwhitney.json|archive/results_snapshots/root_strays/exp1_rf01_mannwhitney.json"
  "wall_clock_flags.json|archive/results_snapshots/root_strays/wall_clock_flags.json"
  "exploratory|archive/results_snapshots/exploratory"
  # one-off scripts
  "fix_swallow.py|archive/one_off_scripts/fix_swallow.py"
  "llm_model_probe.py|archive/one_off_scripts/llm_model_probe.py"
)

is_tracked() { git ls-files --error-unmatch -- "$1" >/dev/null 2>&1; }

echo "=== Planned moves ($([[ $APPLY -eq 1 ]] && echo APPLY || echo DRY RUN)) ==="
for entry in "${MOVES[@]}"; do
  src="${entry%%|*}"; dst="${entry##*|}"
  if [[ ! -e "$src" ]]; then echo "SKIP (missing): $src"; continue; fi
  if [[ -e "$dst" ]]; then echo "SKIP (target exists): $dst"; continue; fi
  if is_tracked "$src"; then cmd="git mv"; else cmd="mv"; fi
  echo "$cmd $src $dst"
  if [[ $APPLY -eq 1 ]]; then
    mkdir -p "$(dirname "$dst")"
    $cmd "$src" "$dst"
  fi
done

echo
echo "=== References that may break (tracked files outside archive/) ==="
# git grep needs a repo; fall back to grep -r if not one
total=0
for entry in "${MOVES[@]}"; do
  src="${entry%%|*}"
  esc=$(printf '%s' "$src" | sed 's/[.[\*^$()+?{|]/\\&/g')
  if [[ -d "$src" ]]; then
    pat="(^|[^A-Za-z0-9_])${esc}(/|[\"'])"
  else
    pat="(^|[^A-Za-z0-9_/])${esc}($|[^A-Za-z0-9_])"
  fi
  if git rev-parse --git-dir >/dev/null 2>&1; then
    hits=$(git grep -nE "$pat" -- . ':!archive' ':!tree_cleanup.txt' ':!*.jsonl' \
             ':!hypatiax/data/results' ':!*.pyc' 2>/dev/null | grep -v "^tidy_root_dryrun.sh:")
  else
    hits=$(grep -rnE "$pat" --include='*.py' --include='*.sh' --include='*.yaml' \
             --include='*.yml' --include='*.toml' --include='*.md' --include='*.tex' . 2>/dev/null \
             | grep -v -e '^./archive/' -e '^./tidy_root_dryrun.sh' -e '^./tree_cleanup.txt')
  fi
  if [[ -n "$hits" ]]; then
    n=$(printf '%s\n' "$hits" | wc -l); total=$((total + n))
    echo "--- $src  ($n reference(s))"
    printf '%s\n' "$hits" | head -20
    [[ $n -gt 20 ]] && echo "    ... $((n - 20)) more"
  fi
done
echo
echo "Total possibly-breaking references: $total"

echo
echo "=== Duplicate check: root test_no_equation_hints.py vs tests copy ==="
if [[ -f test_no_equation_hints.py && -f hypatiax/experiments/tests/test_no_equation_hints.py ]]; then
  if diff -q test_no_equation_hints.py hypatiax/experiments/tests/test_no_equation_hints.py >/dev/null; then
    echo "Identical: the root copy is safe to remove."
  else
    echo "Files differ: review with  diff test_no_equation_hints.py hypatiax/experiments/tests/test_no_equation_hints.py"
  fi
fi

echo
echo "=== Not moved (suggest .gitignore instead) ==="
echo "outputs/   run.log   **/__pycache__/   **/hall_of_fame.csv.bak"
echo
[[ $APPLY -eq 0 ]] && echo "Dry run only. Fix any references above, then re-run with --apply."
