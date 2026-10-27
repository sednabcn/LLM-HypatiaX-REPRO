# Phase 2 closure record (2026-10-27)

**Status: CLOSED WITH CAVEATS. Scope is PySR-only vs HDS v50_2 only. The Pure LLM arm is NOT done.**

- Branch: audit/step1-cleanup @ 7fcb619 (before this commit)
- Primary field: extrap_r2_far (closure in phase2_out/); sensitivity: extrap_r2_medium (phase2_out_p2_med/), train_r2 (phase2_out_p2_train/)
- Result: HDS ahead on recovery, but intervals include zero and sign tests are underpowered; a suggestive direction, not a demonstrated improvement. Do not report mean R2 (-inf rows).
- Time budgets declared unequal (3600 s vs 1400 s). observed: 0/45 HDS rows exceeded 1400 s (max 729 s, median 128 s); cap did not bind (no attempt/retry field in rows; runtime_s may cover only the final attempt)
- Medium adds no independent evidence; train R2 is noise-capped near 0.9975.

## Open items
1. Pure LLM baseline: no runner, no rows. Needs D5 parity, prompt parity check, temperature/max_tokens alignment, frozen prompt hash.
2. Phase 1 evaluator row (Listing 8 vs r2_checked) still "Unverified" in AUDIT/phase1_audit.json; manual comparison required.
3. runtime_s accounting: confirm it includes LLM time and all retries.
4. Phase 3 ablations: no result files; runners must log config_diff, r2_raw and r2_status.
5. scripts/phase3_close.py not reviewed.
6. Known failing test, deselected: hypatiax/core/base_pure_llm/test_baseline_regressions.py::test_error_row_is_not_counted_as_llm_call_and_keeps_hint_status

Update (2026-10-27): item 6 resolved (stale test updated, see amendment A2). Tag phase2-closed-with-caveats left in place.
