#!/usr/bin/env bash
# Phase 2 closure for the Pure LLM arm. One command, no flags to remember.
# Adapts a TEMP copy of the P rows to the closure schema (p2/ is never edited),
# verifies the evaluator is identical across arms, runs scripts/phase2_close.py,
# cross-checks n / catastrophic / nan_or_missing against an independent computation,
# and keeps the manifest + adapted rows under OUT so the manifest's paths resolve.
set -euo pipefail
OUT="${1:-archive/phase2/phase2_pure_llm_closure}"
python scripts/check_closure_nonfinite.py --run-closure --pipeline --a-name pure_llm \
  --pure-llm "${P2_PURE_LLM_GLOB:-p2/pure_llm_*.jsonl}" --hds "${P2_HDS_GLOB:-p2/hds_*.jsonl}" \
  --out-dir "$OUT" --write-sidecar "$OUT/p2_pure_llm_status_relabel.json"
