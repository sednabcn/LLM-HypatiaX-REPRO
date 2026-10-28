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

## Addendum 2026-10-28 (after tag phase2-closed-2026-10-28, a02211e)

Closure outputs, P rows, run log and sizing scripts are in a02211e (guard patch 4c00a79 is an ancestor). The tag is not moved. Published result files are not regenerated.

1. Guard patch (4c00a79), future runs only.
   - LLM-formula path: _execute_formula returns None above 10% non-finite predictions and median-imputes below, so r2_checked never receives non-finite LLM predictions. Commit ddf17c7 replaces np.isnan with not np.isfinite at the LLM-eval fallback (v3c line 843, pca line 746) as a defensive change; behaviour is unchanged on reachable inputs.
   - NN path: a non-finite NN prediction would now give r2 = -inf (previously NaN, dropped by _r2s), i.e. catastrophic (clip -10). _train_and_eval_nn has no sanitising step, so this is possible in principle. In the published pca files all 74 NN and all 74 hybrid test_r2 values are finite in seeds 42 and 99, so no published pca NN or hybrid score would change; v3c2 was not checked.
   - Extrapolation probe (v3c line 624): a non-finite NN probe prediction now gives an infinite gap, which routes to the LLM when llm_trustworthy and decision in (nn, ensemble); previously 0.0. A degenerate probe target now gives gap 0.0 (previously gap = train_r2, which routed to the LLM).
2. Case 47 "Optimal LP Position (Kelly)": constant test target, so NN and hybrid test_r2 = 0.0 mean "undefined". No other exact-zero test_r2 in v3c2 or pca seeds 42 and 99.
3. The test harness flags six cases extrapolation_intractable. Three exist in the benchmark under exact names (Options Delta, Kelly, Black-Scholes Call Price). AMM arbitrage profit has no benchmark counterpart; "Impermanent loss breakeven" and "Put option intrinsic" do not match "Impermanent loss breakeven fee rate" (idx 23) or "Call option intrinsic" (idx 69) on name, difficulty and formula type (formula bodies not compared). The flag is in neither benchmark catalogue (v3c docstring line 18 says IL Breakeven is flagged; catalogue carries no flag). All 74 cases are in every aggregate. Excluding the three matched cases is a post-hoc sensitivity; all-case numbers are primary.
4. p2_pure_llm_status_relabel.json: 45 rows, 43 ok. Two rows (Michaelis-Menten, seeds 42 and 99) have raw status failed:no_calls with n_calls = 3 and display label "all candidates produced non-finite training R2"; "no_calls" is a misnomer. The file relabels display only.
5. pca result files (last written by CI commits of 2026-09-25): success is a fit-quality gate, not an execution flag. Across seeds 42 and 99 every finite success=False test_r2 lies below every finite success=True one for each method (pure_llm ok >= 1.000 / failed <= 0.246; NN ok >= 0.538 / failed <= 0.385; hybrid ok >= 0.659 / failed <= 0.453). In hypatiax_defi_benchmark_pca.py as of a2cae37 (parent of the 2026-09-15 deletion a4d77f5), FIX 11 sets pure_llm success = executed and finite and r2 > 0.5 (lines 1361-1374). The NN and hybrid cutoffs are consistent with the same 0.5 gate by the data; the code lines were not confirmed at the time of writing. The script was absent from the tree between a4d77f5 (2026-09-15) and 195f2cb (2026-09-28), which spans the 2026-09-25 CI result commits, so which script version produced the published files is inferred from the data, not established. The current script (195f2cb onward, patched by 4c00a79) does not carry FIX 11: pure_llm success comes from evaluation alone (line 1286) and NN success is finiteness (line 1305), so regenerated pca files would use a different success meaning. _generate_report in the current script does not filter on success; pca aggregates are test_r2 statistics (non-finite dropped, clipped at -10).
