# fix_paper_issues report

## Issue 1 - split variant behind the accuracy results
  seed-42 copy: ../LLM-HypatiaX-DEV/hypatiax/data/results/comparison_results/noise-noiseless/noiseless/defi/hypatiax_defi_benchmark_v3_results_seed42.json  md5=cbf503d0b3985b4c1bccf7ed18e0316b
  hypatiax_defi_benchmark_v3_results_seed42.json: 74 task records

  Loader validation on hypatiax_defi_benchmark_v3_results_seed42.json (md5 cbf503d0..., paper cites cbf503d0...):
  PASS: all four rows of tab:main_results are reproduced from the file.
  skipped: _checkpoint_shard0.json: unreadable (cannot locate per-task records; structure is {"completed": ["str", "... 10 items)
  skipped: _checkpoint_shard1.json: unreadable (cannot locate per-task records; structure is {"completed": ["str", "... 10 items)
  skipped: _checkpoint_shard2.json: unreadable (cannot locate per-task records; structure is {"completed": ["str", "... 10 items)
  skipped: _checkpoint_shard3.json: unreadable (cannot locate per-task records; structure is {"completed": ["str", "... 10 items)
  skipped: _checkpoint_shard4.json: unreadable (cannot locate per-task records; structure is {"completed": ["str", "... 10 items)
  skipped: exp1_pca_summary.json: unreadable (cannot locate per-task records; structure is {"fixc3_step": "str", "description")
  skipped: fixc3_baseline.json: unreadable (cannot locate per-task records; structure is {"fixc3_gate": "str", "description")
  skipped: fixc3_baseline__shard0_rescued_1790894334.json: unreadable (cannot locate per-task records; structure is {"fixc3_gate": "str", "description")
  skipped: fixc3_baseline__shard2_rescued_1790894314.json: unreadable (cannot locate per-task records; structure is {"fixc3_gate": "str", "description")
  skipped: fixc3_baseline__shard3_rescued_1790894333.json: unreadable (cannot locate per-task records; structure is {"fixc3_gate": "str", "description")
  skipped: fixc3_baseline__shard4_rescued_1790894333.json: unreadable (cannot locate per-task records; structure is {"fixc3_gate": "str", "description")
  skipped: _checkpoint_shard0.json: unreadable (cannot locate per-task records; structure is {"completed": ["str", "... 10 items)
  skipped: _checkpoint_shard1.json: unreadable (cannot locate per-task records; structure is {"completed": ["str", "... 10 items)
  skipped: _checkpoint_shard2.json: unreadable (cannot locate per-task records; structure is {"completed": ["str", "... 10 items)
  skipped: _checkpoint_shard3.json: unreadable (cannot locate per-task records; structure is {"completed": ["str", "... 10 items)
  skipped: _checkpoint_shard4.json: unreadable (cannot locate per-task records; structure is {"completed": ["str", "... 10 items)
  skipped: fixc3_baseline.json: unreadable (cannot locate per-task records; structure is {"fixc3_gate": "str", "description")
  skipped: fixc3_baseline__shard0_rescued_1790894334.json: unreadable (cannot locate per-task records; structure is {"fixc3_gate": "str", "description")
  skipped: fixc3_baseline__shard2_rescued_1790894314.json: unreadable (cannot locate per-task records; structure is {"fixc3_gate": "str", "description")
  skipped: fixc3_baseline__shard3_rescued_1790894333.json: unreadable (cannot locate per-task records; structure is {"fixc3_gate": "str", "description")
  skipped: fixc3_baseline__shard4_rescued_1790894333.json: unreadable (cannot locate per-task records; structure is {"fixc3_gate": "str", "description")
  skipped: split_protocol_disclosure.json: unreadable (cannot locate per-task records; structure is {"fixc3": "bool", "split_protocol":)
  Multiple 74-task PCA files for the same seed; pass --pca-files explicitly: {"42": ["../LLM-HypatiaX-DEV/hypatiax/data/results/comparison_results/noise-noiseless/noiseless/defi_pca/hypatiax_defi_benchmark_pca_results.json", "../LLM-HypatiaX-DEV/hypatiax/data/results/comparison_results/noise-noiseless/noiseless/defi_pca/hypatiax_defi_benchmark_pca_results_seed42.json"], "123": ["../LLM-HypatiaX-DEV/hypatiax/data/results/comparison_results/noise-noiseless/noiseless/defi_pca/hypatiax_defi_benchmark_pca_results_seed123.json", "../LLM-HypatiaX-DEV/hypatiax/data/results/comparison_results/noise-noiseless/noiseless/defi_pca/multi-seeds/hypatiax_defi_benchmark_pca_results_seed123.json"], "2024": ["../LLM-HypatiaX-DEV/hypatiax/data/results/comparison_results/noise-noiseless/noiseless/defi_pca/hypatiax_defi_benchmark_pca_results_seed2024.json", "../LLM-HypatiaX-DEV/hypatiax/data/results/comparison_results/noise-noiseless/noiseless/defi_pca/multi-seeds/hypatiax_defi_benchmark_pca_results_seed2024.json"], "77": ["../LLM-HypatiaX-DEV/hypatiax/data/results/comparison_results/noise-noiseless/noiseless/defi_pca/hypatiax_defi_benchmark_pca_results_seed77.json", "../LLM-HypatiaX-DEV/hypatiax/data/results/comparison_results/noise-noiseless/noiseless/defi_pca/multi-seeds/hypatiax_defi_benchmark_pca_results_seed77.json"], "99": ["../LLM-HypatiaX-DEV/hypatiax/data/results/comparison_results/noise-noiseless/noiseless/defi_pca/hypatiax_defi_benchmark_pca_results_seed99.json", "../LLM-HypatiaX-DEV/hypatiax/data/results/comparison_results/noise-noiseless/noiseless/defi_pca/multi-seeds/hypatiax_defi_benchmark_pca_results_seed99.json"]}
  No variant and no PCA table available: caveat left unchanged.

## Issue 2 - Mann-Whitney regime label
Paper-internal evidence for the far regime:
  * the appendix medians (2415.2 % Hybrid, 13283.9 % NN) are the same numbers as the main paper's
    tab:five_systems_full, whose caption defines the metric as 100*extrap_rmse_far/train_rmse;
  * n=12 / n=15 equal the finite-value counts that table reports before its Tukey-fence
    trimming ('Hybrid keeps 10 of 12, Neural Network 12 of 15');
  * U=74.0 with n=12/15 gives one-tailed p=0.2247 (normal approximation, continuity
    correction), matching the appendix's 2.25e-01, so those three numbers are mutually consistent.
  * the 2x multiplier is the medium regime (supplement S2 lists 1.2x, 2x, 5x); the far regime is 5x.

  Data check: ../LLM-HypatiaX-DEV/hypatiax/data/results/five_systems/exp1_five/exp1_five_results.json
  regime | n_hyb n_nn | median_hyb  median_nn |     U   p(one-tailed, hyb<nn)
  near   |    12   15 |       55.4      297.8 |   56.0   0.0511
  medium |    11   15 |      225.9     2888.4 |   46.0   0.0309
  far    |    12   15 |     2415.2    13283.9 |   74.0   0.2247
  Appendix reports: n=12/15, medians 2415.2 / 13283.9, U=74.0, p=0.225.  Regime reproducing U and n: ['far']

## Issue 3 - tables labelled Unverified

### tab:portfolio_seed_sweep
  arithmetic in the table: mean P -31.953, mean H -6.261, strict wins 4/5, win column consistent: True
  several candidates, trying each in turn (override with --sweep-json): ../LLM-HypatiaX-DEV/hypatiax/data/results/comparison_results/noise-noiseless/15/portfolio_variance_seed_sweep.json, ../LLM-HypatiaX-DEV/hypatiax/data/results/comparison_results/noise-noiseless/15/portfolio_variance_seed_sweep__shard0_rescued_1790358671.json, ../LLM-HypatiaX-DEV/hypatiax/data/results/comparison_results/noise-noiseless/15/portfolio_variance_seed_sweep__shard1_rescued_1790358642.json, ../LLM-HypatiaX-DEV/hypatiax/data/results/comparison_results/noise-noiseless/15/portfolio_variance_seed_sweep__shard2_rescued_1790358639.json, ../LLM-HypatiaX-DEV/hypatiax/data/results/comparison_results/noise-noiseless/15/portfolio_variance_seed_sweep__shard3_rescued_1790358616.json, ../LLM-HypatiaX-DEV/hypatiax/data/results/portfolio_variance_audit/portfolio_variance_defi_seed_sweep_seed123.json, ../LLM-HypatiaX-DEV/hypatiax/data/results/portfolio_variance_audit/portfolio_variance_defi_seed_sweep_seed2024.json, ../LLM-HypatiaX-DEV/hypatiax/data/results/portfolio_variance_audit/portfolio_variance_defi_seed_sweep_seed42.json, ../LLM-HypatiaX-DEV/hypatiax/data/results/portfolio_variance_audit/portfolio_variance_defi_seed_sweep_seed777.json, ../LLM-HypatiaX-DEV/hypatiax/data/results/portfolio_variance_audit/portfolio_variance_defi_seed_sweep_seed99.json, ../LLM-HypatiaX-DEV/hypatiax/data/results/portfolio_variance_audit/portfolio_variance_seed_sweep.json
  VERIFIED far-R2 values against ../LLM-HypatiaX-DEV/hypatiax/data/results/comparison_results/noise-noiseless/15/portfolio_variance_seed_sweep.json (md5 4c6189bb...): all five seeds match.
  Not checkable automatically: the 'H formula' and 'H recovers?' columns. Per-seed HypatiaX expression stored in the file, for a manual check against the table:
    seed 42: H far-R2=-0.023 timed_out(H/P)=False/False expr=(s1 + s2)*(rho*0.24280846 + 0.73828906)
    seed 99: H far-R2=-15.191 timed_out(H/P)=False/False expr=(rho*s1 + s1 + s2)/1.3949639
    seed 123: H far-R2=-18.090 timed_out(H/P)=False/False expr=(rho*s1 + s1 + s2)/exp(s1 + 0.19797014)
    seed 777: H far-R2=1.000 timed_out(H/P)=False/False expr=sqrt(s1**2 + s2*(2*rho*s1 + s2))
    seed 2024: H far-R2=1.000 timed_out(H/P)=False/False expr=sqrt(s1*(2*rho*s2 + s1) + s2**2)

### tab:arch
  could not parse the percentages; skipped.

### tab:noise_sensitivity
  parsed 0 rows, expected 7; skipped.

## Edits
  [applied] supp: Mann-Whitney regime label (medium 2x -> far 5x)
  [applied] main: cross-reference to the Mann-Whitney test (medium -> far)
  [ANCHOR NOT FOUND - not changed] main: tab:portfolio_seed_sweep tag replaced (far-R2 values verified)

Patched copies written to fix_out/patched (originals untouched).
