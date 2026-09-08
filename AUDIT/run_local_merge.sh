#!/usr/bin/env bash
#
# run_local_merge.sh
#
# Merges 4 downloaded targeted-rerun artifacts into the real
# hypatiax/data/results/extrapolation/multi_seed/ result files, WITHOUT
# re-triggering the nguyen12_targeted_rerun_and_merge.yml CI workflow.
#
# This mirrors the CI's "Merge targeted reruns into the real result files"
# step exactly -- same AUDIT/merge_targeted_rerun.py, same --task-ids per
# seed, same --target files -- just pointed at artifact zips on disk
# instead of a fresh in-CI rerun. Run this from the repo root.
#
# USAGE:
#   1. Download the 4 artifact zips from the GitHub Actions run
#      (nguyen12-rerun-seed-99-*, -123-*, -777-*, -2024-*) into one
#      directory, e.g. ~/Downloads/nguyen12-artifacts/
#   2. From the repo root:
#        ./run_local_merge.sh ~/Downloads/nguyen12-artifacts --dry-run
#      Review the diff output, then:
#        ./run_local_merge.sh ~/Downloads/nguyen12-artifacts --write
#
# Each artifact zip is expected to contain (at minimum)
# exp3_nguyen12_seed{N}.json -- exactly what merge_targeted_rerun.py's
# --source expects, same as when RESULTS_DIR pointed the CI job there.

set -euo pipefail

if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <artifact_dir> [--dry-run|--write]" >&2
    exit 1
fi

ARTIFACT_DIR="$1"
MODE="${2:---dry-run}"

if [[ "$MODE" != "--dry-run" && "$MODE" != "--write" ]]; then
    echo "Second argument must be --dry-run or --write, got: $MODE" >&2
    exit 1
fi

WRITE_FLAG=()
if [[ "$MODE" == "--write" ]]; then
    WRITE_FLAG=(--write)
fi

if [[ ! -f AUDIT/merge_targeted_rerun.py ]]; then
    echo "ERROR: AUDIT/merge_targeted_rerun.py not found -- run this from the repo root." >&2
    exit 1
fi

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

echo "== Unzipping artifacts from $ARTIFACT_DIR into $WORKDIR =="
for zf in "$ARTIFACT_DIR"/nguyen12-rerun-seed-*.zip; do
    [[ -e "$zf" ]] || { echo "No nguyen12-rerun-seed-*.zip files found in $ARTIFACT_DIR" >&2; exit 1; }
    base="$(basename "$zf")"
    seed="$(echo "$base" | sed -E 's/nguyen12-rerun-seed-([0-9]+)-.*/\1/')"
    mkdir -p "$WORKDIR/seed$seed"
    unzip -o -q "$zf" -d "$WORKDIR/seed$seed"
    echo "  seed$seed <- $base"
done

# Same 4 pairs the CI step uses -- seed, nshards target, task-ids
declare -a SEEDS=(99 123 777 2024)
declare -a TARGETS=(
    "hypatiax/data/results/extrapolation/multi_seed/exp3_nguyen12_seed99_nshards01.json"
    "hypatiax/data/results/extrapolation/multi_seed/exp3_nguyen12_seed123_nshards02.json"
    "hypatiax/data/results/extrapolation/multi_seed/exp3_nguyen12_seed777_nshards03.json"
    "hypatiax/data/results/extrapolation/multi_seed/exp3_nguyen12_seed2024_nshards04.json"
)
declare -a TASK_IDS=("N12" "N4" "N7 N12" "N7 N8 N9")

echo
echo "== Merging (mode: $MODE) =="
for i in "${!SEEDS[@]}"; do
    seed="${SEEDS[$i]}"
    target="${TARGETS[$i]}"
    ids="${TASK_IDS[$i]}"
    source_file="$WORKDIR/seed$seed/exp3_nguyen12_seed${seed}.json"

    if [[ ! -f "$source_file" ]]; then
        echo "  [seed $seed] SKIP -- $source_file not found in artifact"
        continue
    fi
    if [[ ! -f "$target" ]]; then
        echo "  [seed $seed] ERROR -- target $target not found; are you in the repo root?" >&2
        exit 1
    fi

    echo "--- seed $seed (task-ids: $ids) ---"
    # shellcheck disable=SC2086
    python3 AUDIT/merge_targeted_rerun.py \
        --source "$source_file" \
        --target "$target" \
        --task-ids $ids "${WRITE_FLAG[@]}"
    echo
done

if [[ "$MODE" == "--write" ]]; then
    echo "== Post-merge trajectory check (same as CI's write-mode validation) =="
    FAIL=0
    for target in "${TARGETS[@]}"; do
        echo "--- $target ---"
        python3 AUDIT/fix_expression_trajectory_mismatch.py "$target" || FAIL=1
        echo
    done
    if [[ "$FAIL" -eq 1 ]]; then
        echo "WARNING: unresolved records remain -- see output above before trusting these files."
        exit 1
    fi
    echo "All targets clean."
else
    echo "Dry run only -- nothing was written, so the trajectory check is skipped"
    echo "(it would only be validating the files' pre-existing state, not this merge's"
    echo "result -- same reason CI's own check step only runs when write=true)."
    echo "Re-run with --write once the diffs above look right."
fi
