#!/usr/bin/env bash
# Safe, read-only inventory + LOCAL recovery refs for LLM-HypatiaX-REPRO.
# Does not merge, cherry-pick, edit tracked files, push, or delete branches.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "ERROR: run this inside the LLM-HypatiaX-REPRO Git checkout." >&2
  exit 1
}
cd "$REPO_ROOT"

REMOTE="${1:-origin}"
BASE="${2:-master}"
BASE_REF="refs/remotes/${REMOTE}/${BASE}"

branches=(
  "audit-main"
  "audit-master"
  "ci/update-smoke"
  "dependabot/pip/build-1.6.1"
  "dependabot/pip/cachetools-7.3.0"
  "dependabot/pip/kagglesdk-0.1.28"
  "dependabot/pip/nltk-3.10.4"
  "dependabot/pip/platformdirs-4.12.4"
  "dependabot/pip/pure-eval-0.2.4"
  "enable-fresh-rerun-dispatch"
  "fix/hybriddiscovery-timeout-repair"
  "fix/rerun-blockers"
  "integration/ci-workflow-fixes"
  "integration/consolidated-work"
  "promotion/rerun-code-review"
  "publication-readiness-review"
  "rerun/integration"
  "sync/hypatiax-package-to-master"
)

if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
  echo "ERROR: remote '$REMOTE' does not exist." >&2
  exit 1
fi

echo "Fetching remote branch tips (no prune; no remote changes)..."
git fetch "$REMOTE" "+refs/heads/*:refs/remotes/${REMOTE}/*"

if ! git show-ref --verify --quiet "$BASE_REF"; then
  echo "ERROR: base ref $BASE_REF is missing." >&2
  exit 1
fi

OUT="$REPO_ROOT/recovery-inventory-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$OUT"
printf 'branch\ttip_sha\trecovery_ref\tstatus\n' > "$OUT/branch-tips.tsv"
printf 'branch\tcommit_sha\tauthor_date\tcommitter_date\tsubject\n' > "$OUT/branch-commits.tsv"
printf 'branch\tcommit_sha\tchange_status\tpath\n' > "$OUT/commit-paths.tsv"
printf 'branch\tbase_sha\ttip_sha\tstat\n' > "$OUT/branch-diffstats.tsv"

BASE_SHA="$(git rev-parse "$BASE_REF")"
echo "Base: $REMOTE/$BASE at $BASE_SHA"
echo "Inventory output: $OUT"

for branch in "${branches[@]}"; do
  remote_ref="refs/remotes/${REMOTE}/${branch}"
  recovery_branch="recovery/${branch}"

  if ! git show-ref --verify --quiet "$remote_ref"; then
    echo "ERROR: missing remote-tracking ref $remote_ref; stopping safely." >&2
    exit 1
  fi

  tip="$(git rev-parse "$remote_ref")"
  local_ref="refs/heads/${recovery_branch}"

  if git show-ref --verify --quiet "$local_ref"; then
    existing="$(git rev-parse "$local_ref")"
    if [[ "$existing" != "$tip" ]]; then
      echo "ERROR: $recovery_branch already exists at $existing, expected $tip." >&2
      echo "No ref was moved. Resolve this manually before rerunning." >&2
      exit 1
    fi
    status="already-present-same-tip"
  else
    git branch "$recovery_branch" "$remote_ref"
    status="created-local-recovery-ref"
  fi

  printf '%s\t%s\t%s\t%s\n' "$branch" "$tip" "$recovery_branch" "$status" \
    >> "$OUT/branch-tips.tsv"

  git log --reverse --date=iso-strict \
    --format="${branch}%x09%H%x09%aI%x09%cI%x09%s" \
    "${BASE_REF}..${remote_ref}" >> "$OUT/branch-commits.tsv"

  git diff --stat "${BASE_REF}...${remote_ref}" \
    > "$OUT/diffstat-${branch//\//_}.txt" || true

  stat_line="$(git diff --shortstat "${BASE_REF}...${remote_ref}" || true)"
  printf '%s\t%s\t%s\t%s\n' "$branch" "$BASE_SHA" "$tip" "$stat_line" \
    >> "$OUT/branch-diffstats.tsv"

  while IFS= read -r sha; do
    [[ -n "$sha" ]] || continue
    git diff-tree --no-commit-id --name-status -r "$sha" |
      while IFS=$'\t' read -r change path; do
        [[ -n "${path:-}" ]] || continue
        printf '%s\t%s\t%s\t%s\n' "$branch" "$sha" "$change" "$path"
      done >> "$OUT/commit-paths.tsv"
  done < <(git rev-list --reverse "${BASE_REF}..${remote_ref}")

  echo "Recorded $branch ($tip)"
done

echo
echo "Completed. Local recovery refs and inventory files are in:"
echo "$OUT"
echo "No remote branches were created, moved, or deleted."
echo "No cherry-picks, merges, resets, or tracked-file edits were performed."
