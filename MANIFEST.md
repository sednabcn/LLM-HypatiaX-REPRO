# Extracted inline scripts (21 total)

All are Python heredocs (`python3 - <<'PYEOF' ... PYEOF`) embedded directly in `run:` steps. 
None of the 5 uploaded YAML files contain inline content for the file-path-referenced scripts 
(e.g. `.github/scripts/run_analysis.py`, `scripts/generate_figures.py`) — those are invoked by path 
but their bodies aren't embedded here, so there's nothing to extract for them. All extracted files 
below are placed flat under `scripts/`.

| # | Extracted file | Source YAML | Lines | Job | Step |
|---|---|---|---|---|---|
| 1 | `ci_runner__job-plan__step01-split.py` | ci_runner.yml | 474-805 | plan | Compute pending task list and shard split |
| 2 | `ci_runner__job-worker__step02-precompile_julia_symbolicregression_if_needed.py` | ci_runner.yml | 928-961 | worker | Precompile Julia / SymbolicRegression (if needed) |
| 3 | `ci_runner__job-worker__step03-resolve_ids.py` | ci_runner.yml | 1063-1084 | worker | Resolve this shard's pending IDs |
| 4 | `ci_runner__job-worker__step04-resolve_ids.py` | ci_runner.yml | 1095-1144 | worker | Validate hybrid_all_domains domain list |
| 5 | `ci_runner__job-worker__step05-resolve_ids.py` | ci_runner.yml | 1325-1432 | worker | Safety-net - rescue results from shard checkpoint (FIX-G5) |
| 6 | `ci_runner__job-worker__step06-resolve_ids.py` | ci_runner.yml | 1889-2046 | worker | Save shard checkpoint |
| 7 | `ci_runner__job-pca_run_exp2_feynman__step07-check_exp2.py` | ci_runner.yml | 2403-2431 | pca_run_exp2_feynman | Precompile Julia / SymbolicRegression |
| 8 | `ci_runner__job-pca_run_exp1__step08-check_exp1.py` | ci_runner.yml | 2585-2613 | pca_run_exp1 | Precompile Julia / SymbolicRegression |
| 9 | `ci_runner__job-pca_run_exp1b__step09-check_exp1b.py` | ci_runner.yml | 2753-2781 | pca_run_exp1b | Precompile Julia / SymbolicRegression |
| 10 | `ci_runner__job-gate_a_split_protocol_test__step10-gate_a_split_protocol_test.py` | ci_runner.yml | 2907-3093 | gate_a_split_protocol_test | Gate A — split_protocol_test |
| 11 | `ci_runner__job-gate_b_protocol_parity_test__step11-gate_b_protocol_parity_test.py` | ci_runner.yml | 3134-3280 | gate_b_protocol_parity_test | Gate B — protocol_parity_test |
| 12 | `ci_runner__job-gate_c_baseline_lock_test__step12-gate_c_baseline_lock_test.py` | ci_runner.yml | 3322-3518 | gate_c_baseline_lock_test | Gate C — baseline_lock_test |
| 13 | `ci_pipeline_check__job-check__step01-check.py` | ci_pipeline_check.yml | 213-370 | check | Check committed outputs for every experiment |
| 14 | `ci_pipeline_check__job-complete__step02-complete.py` | ci_pipeline_check.yml | 410-634 | complete | Compute completion gaps |
| 15 | `ci_pipeline_check__job-qualify__step03-qualify.py` | ci_pipeline_check.yml | 685-959 | qualify | Qualify experiments (7-dimension gate) |
| 16 | `ci_pipeline_check__job-qualify__step04-qualify.py` | ci_pipeline_check.yml | 985-1069 | qualify | Move root figures/tables into per-experiment subdirs |
| 17 | `ci_pipeline_check__job-audit__step05-audit.py` | ci_pipeline_check.yml | 1165-1522 | audit | Audit results against paper claims |
| 18 | `ci_pipeline_check__job-summary__step06-print_consolidated_summary_and_set_exit_code.py` | ci_pipeline_check.yml | 1573-1707 | summary | Print consolidated summary and set exit code |
| 19 | `ci_pipeline_check__job-dispatch__step07-dispatch_experiments_with_0_done_tasks.py` | ci_pipeline_check.yml | 1748-1814 | dispatch | Dispatch experiments with 0 done tasks |
| 20 | `ci_pipeline_public__job-resolve__step01-parse.py` | ci_pipeline_public.yml | 181-240 | resolve | Parse experiment index and phase |
| 21 | `ci_pipeline_public__job-diagnose__step02-diagnose.py` | ci_pipeline_public.yml | 282-442 | diagnose | Inspect repository state |