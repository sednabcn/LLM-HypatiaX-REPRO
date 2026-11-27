# DeFi PCA 40/60 vs random 40/60 benchmark evaluation

**Evaluation date:** 2026-11-27  
**Repository:** `sednabcn/LLM-HypatiaX-REPRO`  
**Branch:** `research/defi-pca-random-4060-comparison`  
**Scope:** Three supplied GitHub Actions runs: `exp1_pca`, `exp1b_pca`, and `exp1_4060_seeds`.

## Executive summary

All three workflow runs completed successfully. The strongest comparable performance evidence is the five-seed `exp1b_pca` PCA-directed benchmark versus the five-seed `exp1_4060_seeds` random 40/60 benchmark.

The random 40/60 experiment has a substantially higher mean held-out hybrid R² in the per-seed logs (approximately **0.816**, versus **0.083** in the PCA pooled report). The PCA experiment does, however, produce **35/365** finite case-seed hybrid scores at or above the exceptionally strict threshold (R^2 \ge 0.999999) (**9.59%**), while the random experiment reports **0/370** at that same threshold. These findings are not contradictory: a small number of near-perfect PCA cases coexist with a much poorer overall PCA score distribution.

**Interpretation:** on the available aggregate evidence, random 40/60 is the stronger and more stable broad predictive split. PCA-directed 40/60 appears to create a harder tail/generalisation problem, with a small subset of near-perfect outcomes but poor aggregate held-out performance. The strict-threshold pass count alone should not be used to claim PCA superiority.

## 1. Workflow execution and provenance

| Experiment | Run | Workflow conclusion | Execution evidence |
|---|---|---:|---|
| `exp1_pca` | [46056848315](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/46056848315) | Success | Five worker shards succeeded; aggregate validation succeeded; manifest records 370 validated records across seeds 42, 99, 123, 777, 2024 |
| `exp1b_pca` | [46054046731](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/46054046731) | Success | Five-seed PCA 40/60 run completed; summary validates 370 case records |
| `exp1_4060_seeds` | [46054191107](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/46054191107) | Success | Five isolated random-split workers succeeded; aggregate validation succeeded; 370 records |

### Important seed-input discrepancy

The `exp1_pca` run URL was described as “seed=42”, but the run's committed `pca_seed_aggregate_manifest.json` records all five expected and validated seeds: **42, 99, 123, 777, 2024**, with 74 cases per seed (370 records total). The Actions job list likewise shows five PCA worker shards. Therefore this workflow dispatch did **not** execute seed 42 alone; it executed the five-seed sweep.

The manifest is tied to run `46056848315` and commit `bb5dd6a5553fab75182e6cb77f95ae19a6b6ea32`. The nearby `exp1_pca_summary.json` in the result directory has a timestamp of 2026-09-19 and is stale relative to this 2026-11-27 run. Its historical 51/74 result is **not** treated as a metric for run 46056848315.

## 2. Comparable five-seed metric results

### PCA-directed 40/60: `exp1b_pca`

Source: `hypatiax/data/results/comparison_results/noise-noiseless/15_pca/exp1b_pca_summary.json`, plus `hypatiax_defi_benchmark_pca_pooled_seed_report.json`.

- Split: PCA-directed 40% train / 60% test.
- Seeds: 42, 99, 123, 777, 2024.
- Records validated: 370 (74 per seed).
- Finite hybrid held-out R² values: 365 (73 per seed).
- One case per seed, “Optimal LP Position (Kelly)”, has undefined R² because the target is constant; these five undefined values are excluded from the denominator.
- Threshold used by the validator: hybrid held-out (R^2 \ge 0.999999). This is a near-perfect predictive-R² threshold, **not** symbolic equivalence.

| Seed | Near-perfect cases | Finite cases | Rate |
|---:|---:|---:|---:|
| 42 | 8 | 73 | 10.96% |
| 99 | 7 | 73 | 9.59% |
| 123 | 5 | 73 | 6.85% |
| 777 | 7 | 73 | 9.59% |
| 2024 | 8 | 73 | 10.96% |
| **Total** | **35** | **365** | **9.59%** |

The pooled report gives the mean of per-seed mean held-out R² values:

| Model arm | Mean of seed means (raw R²) | SD across seed means |
|---|---:|---:|
| Pure LLM | -324,054.313 | 340,727.858 |
| Neural network | -31.441 | 17.778 |
| Hybrid | **0.0832** | **0.0162** |

The very negative pure-LLM and neural-network means indicate severe failures/outliers on some held-out cases; raw R² is unbounded below, so means can be dominated by catastrophic cases. The hybrid arm is markedly better than those two arms, but its mean held-out R² remains low.

### Random 40/60: `exp1_4060_seeds`

Sources: `exp1_4060_seeds_summary.json` and the five per-seed run logs under `hypatiax/data/results/comparison_results/noise-noiseless/noiseless/defi_random_4060/`.

- Split: seeded random 40% train / 60% test.
- Seeds: 42, 99, 123, 777, 2024.
- Records: 370 finite hybrid held-out R² values (74 per seed).
- At the same strict threshold (R^2 \ge 0.999999): **0/370**.
- The workflow summary explicitly defines this threshold metric as a predictive score, not symbolic equivalence.

The per-seed logs print hybrid test R² to four decimal places. The approximate per-seed mean values computed from those displayed log values are:

| Seed | Mean hybrid test R² (approx.) | Cases with displayed R² ≥ 0.99 |
|---:|---:|---:|
| 42 | 0.8535 | 50/74 |
| 99 | 0.8153 | 50/74 |
| 123 | 0.7946 | 50/74 |
| 777 | 0.8681 | 52/74 |
| 2024 | 0.7497 | 46/74 |
| **Mean across seed means** | **0.8162** | **248/370 (67.03%)** |

The ≥0.99 counts above are based on four-decimal log output and are descriptive only. The authoritative exact aggregate in the committed summary is the strict (R^2 \ge 0.999999) count of 0/370.

## 3. Head-to-head interpretation

### Overall held-out fit

The PCA pooled hybrid mean of seed means is approximately **0.0832**. The random-split mean calculated from rounded per-seed log output is approximately **0.8162**. This is a large difference in favour of random 40/60 on average held-out predictive fit.

The comparison is not perfectly precision-matched: the PCA mean comes from a JSON aggregate, while the random mean is reconstructed from log values rounded to four decimals. It is nevertheless sufficiently large to support a directional conclusion, not a fine-grained significance claim.

### Near-perfect tail of the score distribution

At the strict (R^2 \ge 0.999999) threshold:
- PCA-directed: 35/365 = **9.59%**.
- Random: 0/370 = **0%**.

This metric captures the fraction of cases reaching an almost exact predictive fit. It does not measure the typical case and is not symbolic-equivalence validation. PCA has a small near-perfect subset, but that subset does not offset its poor mean hybrid R².

### Seed sensitivity

The PCA strict-threshold rate ranges from 6.85% to 10.96% across the five seeds. Random-split mean hybrid R² ranges approximately from 0.750 to 0.868 across seeds. The random results show higher average test fit in every seed's reported mean; the PCA summary's per-seed pass rates are comparatively low and narrow.

### What the runs do and do not establish

- They establish successful execution and complete five-seed record coverage for the PCA and random experiments.
- They support a descriptive comparison of the hybrid held-out R² distributions using the metrics above.
- They do not establish statistical significance; there are five seeds and no paired bootstrap or confidence interval for this full 74-equation comparison.
- They do not establish symbolic recovery or equation equivalence. Predictive R² and symbolic correctness are different outcomes.
- The random logs' four-decimal precision prevents exact recomputation of thresholds such as 0.99 from those logs; use the persisted raw JSON records for exact distributional analysis.
- The current `exp1_pca` run's aggregate manifest proves 370 records were validated, but its colocated summary JSON is stale. Do not quote the historical 51/74 summary as the current run's result.

## 4. Conclusions

1. **Random 40/60 is the stronger default generalisation benchmark** on the current aggregate hybrid-R² evidence: its mean held-out score is substantially higher than the PCA-directed result.
2. **PCA-directed 40/60 is a useful stress test**, likely exposing difficult tail/extrapolation behaviour. Its 9.59% near-perfect fraction should be reported alongside—not instead of—the full score distribution.
3. **Do not interpret the strict-threshold pass rate as symbolic solve rate.** Rename this quantity in future reports to “near-perfect held-out R² rate” and separately measure symbolic equivalence.
4. **Fix the `exp1_pca` seed dispatch contract.** The requested seed=42 was not honoured by the observed five-shard workflow; either wire the input seed list through the planner or label the dispatch as a five-seed sweep.
5. **Regenerate a current `exp1_pca` metric summary** from the run 46056848315 result records. Keep the run manifest, per-seed metrics, undefined-metric accounting, and exact score distributions together.

## 5. Reproducibility sources

- [Run 46056848315 — exp1_pca](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/46056848315)
- [Run 46054046731 — exp1b_pca](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/46054046731)
- [Run 46054191107 — exp1_4060_seeds](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/46054191107)
- [PCA aggregate summary](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/master/hypatiax/data/results/comparison_results/noise-noiseless/15_pca/exp1b_pca_summary.json)
- [PCA pooled seed report](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/master/hypatiax/data/results/comparison_results/noise-noiseless/15_pca/hypatiax_defi_benchmark_pca_pooled_seed_report.json)
- [Random 40/60 aggregate summary](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/master/hypatiax/data/results/comparison_results/noise-noiseless/noiseless/defi_random_4060/exp1_4060_seeds_summary.json)
- [PCA five-seed manifest for run 46056848315](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/master/hypatiax/data/results/comparison_results/noise-noiseless/noiseless/defi_pca/pca_seed_aggregate_manifest.json)

---
*Prepared from the committed run metadata, experiment summaries, pooled report, split disclosures, and per-seed random-run logs available on 2026-11-27. Approximate values and known provenance limitations are explicitly identified above.*


## 6. Symbolic-equivalence and measurement-integrity follow-up

The later measurement-integrity work changes how the 40/60 results should be interpreted. The strict (R^2 \ge 0.999999) count is a **near-perfect held-out predictive-R² rate**, not a symbolic solve/recovery rate.

Relevant repository changes:
- [PR #424 — make 4060 recovery measurement auditable](https://github.com/sednabcn/LLM-HypatiaX-REPRO/pull/424) renamed the threshold metric, records its definition, and adds ground-truth expression provenance plus original outer split row indices for future runs. It explicitly notes that historical records do not contain these new fields and cannot be retrospectively adjudicated.
- [PR #426 — independent symbolic equivalence and route audit](https://github.com/sednabcn/LLM-HypatiaX-REPRO/pull/426) adds a conservative offline adjudicator. Generated formulas are parsed through a restricted AST allowlist and converted to SymPy expressions without executing generated code. Variable aliases require explicit mappings; unmapped aliases are not assessable. This is formal symbolic identity under the declared mapping, not a proof of domain restrictions, branch equivalence, or singularity behaviour.
- [PR #429 — fix ground-truth parsing and persist PCA answer keys](https://github.com/sednabcn/LLM-HypatiaX-REPRO/pull/429) fixes ground-truth parsing and persists PCA answer-key context for offline evaluation, while explicitly excluding the answer key from the LLM prompt.

### Historical 740-record audit

The offline audit inspected five seed files for each of the two committed 40/60 protocols:

| Protocol | Records | Generated formula present | Route fields present | Ground-truth expression present |
|---|---:|---:|---:|---:|
| Random 40/60 | 370 | 370 | 370 | 0 |
| PCA 40/60 | 370 | 370 | 370 | 0 |
| **Total** | **740** | **740** | **740** | **0** |

All 740 historical records contain formula context, split protocol, audit data, generated hybrid formula, and core route fields, but none contains `formula_context.ground_truth_expression`. Their symbolic-audit status is therefore **ground-truth missing / not assessable**. This is neither evidence of symbolic success nor evidence of symbolic failure. No answer keys were guessed or backfilled from a potentially different protocol revision.

The 365 finite PCA scores (one undefined constant-target R² per seed) and 370 finite random scores also mean that the selected-predictor comparison below uses 365 matched seed-case observations.

## 7. Routing and selected-predictor audit

The 40/60 system is a **routed hybrid predictor**, not simply an LLM formula predictor. The LLM was called and a formula was saved for every case in both protocols, but the final selected predictor often came from a fallback or another route.

### Route counts across five seeds

| Route | Random 40/60 | PCA 40/60 |
|---|---:|---:|
| NN abstention / replacement fallback | 248 | 254 |
| Ensemble | 62 | 59 |
| NN route | 60 | 57 |
| LLM called and formula saved | 370 | 370 |
| Trust gate passed | 262 | 260 |

For ensemble-routed cases, mean per-query LLM weight was **0.630** for random and **0.968** for PCA. The source implementation uses query-wise OOD-dependent weighting:

- (w_{LLM} = 0.3 + 0.7p_{OOD})
- (w_{NN} = 1 - w_{LLM})

When the NN abstains, both blend weights are zero and a replacement predictor is selected. These are query-dependent weights, **not one global scalar \(\tau\)**. Do not attribute this specific 40/60 mechanism to the scalar-\(\tau\) Exp1 mechanism without a source-level experiment mapping.

### Selected-predictor test R²

The independent route audit reports the score of the predictor actually selected for each case:

| Statistic | Random 40/60 | PCA 40/60 |
|---|---:|---:|
| Finite selected-predictor scores | 370 | 365 |
| Median selected-predictor test R² | **0.9973** | **0.9661** |

On the 365 matched seed-case pairs, random had higher selected-predictor R² in **280** pairs and PCA in **85**. The median paired difference (PCA minus random) was **-0.0126**. The mean paired difference (-6.57) is dominated by extreme negative outliers and should not be used as a standalone summary. These are descriptive repeated-seed results, not an inferential test.

**Do not conflate these selected-predictor statistics with the hybrid held-out R² means in Sections 2–3.** They are different estimands: one describes the hybrid metric field used in the earlier benchmark summary; the other describes the predictor selected by the route logic. Their different distributions are not inherently contradictory. Future reports must label the metric source, predictor source, aggregation, and denominator explicitly.

## 8. Reconciliation with the EXP1 redesign document

The design baseline reviewed was [`docs/EXP1_SCIENTIFIC_VALUE_AND_REDESIGN.md`](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/docs/exp1-scientific-value-redesign-2026-11-25/docs/EXP1_SCIENTIFIC_VALUE_AND_REDESIGN.md) on branch `docs/exp1-scientific-value-redesign-2026-11-25`. The requested branch name without the `-2026-11-25` suffix was not the branch used for this comparison.

The design document identifies the standard DeFi random benchmark as **80/20** and its PCA counterpart as **40/60**. The present report compares **random 40/60** with **PCA 40/60**. Therefore:
- Random 40/60 is an additional, separately named protocol; it must not be silently substituted for the documented standard random 80/20 benchmark.
- The two 40/60 protocols align the nominal train/test fraction, but their split construction and test-set geometry still differ.
- Random 80/20, random 40/60, and PCA 40/60 should have separate protocol IDs, manifests, and cohort-specific summaries. Do not pool their R² values into one estimate.

The redesign document's broader principles remain applicable:
1. Separate task breadth from independent equation-family evidence; related tasks and repeated seeds do not create independent families.
2. Treat seeds as repeated measurements and aggregate within equation/family before cohort-level inference.
3. Preserve formula, NN, fallback, selected-predictor, and route-reason provenance.
4. Keep execution completion, provenance completion, scientific aggregation, and statistical analysis as distinct statuses.
5. Keep PCA and random protocols separate, and do not tune routing against test outcomes.
6. Treat the proposed independent 30-equation DeFi sensitivity cohort as **future work**, subject to a family-overlap audit and preregistration. The existing 21-sensitive-plus-6-control protocol is not the same cohort and must not be relabelled or padded to 30.
7. Keep Core-15 attribution, the existing LLM-sensitive cohort, fallback-model comparisons, and PCA protocols as separate scientific questions even if they share infrastructure.
8. Evaluate fallback candidates (including signed-feature Ridge, Lasso, and Elastic Net) with training-only fitting, validation-only selection, and untouched test evaluation.

## 9. Updated scientific interpretation

The strongest defensible description from the combined evidence is that HypatiaX 40/60 is a **routed hybrid prediction system**: it obtains candidate formulas from the LLM, applies trust/routing logic, and often selects a replacement or alternative predictor. The central scientific questions are therefore:

- When does the LLM-generated formula itself match the evaluator's ground truth under an explicit variable mapping?
- When does the LLM contribute useful predictive information to the final selected predictor?
- When does the system need NN abstention, ensemble blending, or replacement fallback?
- Does including the LLM improve the final predictor relative to an otherwise comparable no-LLM system?

The current 740 historical records cannot answer the first question because their ground-truth expression is absent. The route audit helps characterize the second and third questions descriptively, but does not establish causal LLM benefit. A properly controlled no-LLM comparison (including the relevant Core-15 or LLM-sensitive protocol) is needed for the fourth.

High predictive R², including a near-perfect held-out score, is not evidence of symbolic recovery. Symbolic statuses should be reported separately as **assessed-equivalent**, **assessed-non-equivalent**, **not-assessable**, or **evaluation-failed**, with parser/evaluator failures distinguished from mathematical non-equivalence.

## 10. Reporting and analysis actions

1. Keep the original hybrid-R² comparison and the selected-predictor route audit in separate tables, with exact field names and aggregation methods.
2. Use the term **near-perfect held-out predictive-R² rate** for the (R^2 \ge 0.999999) metric; never call it a solve or symbolic recovery rate.
3. Report symbolic-equivalence denominators and statuses separately, and do not classify historical ground-truth-missing records as failures.
4. Preserve query-wise OOD weights and route counts; do not describe this 40/60 implementation as using a global scalar \(\tau\).
5. Publish separate random 80/20, random 40/60, and PCA 40/60 protocol summaries.
6. Add exact raw-JSON distributional analysis and paired uncertainty estimates before making inferential claims. Five seeds and descriptive counts alone do not establish statistical significance.
7. Preserve the independent 30-family sensitivity cohort as proposed work until its inclusion ledger, overlap audit, and preregistration are complete.
8. Keep run provenance attached to every aggregate and do not use stale summaries as current-run evidence.

### Scope and execution boundary

This report update is a documentation-only synthesis of existing workflow records, committed artifacts, the offline 740-record audit, the referenced pull-request descriptions, and the EXP1 redesign document. **No benchmark, training job, LLM request, workflow dispatch, or merge was initiated for this update.**


## 11. Additional 17:00 workflow-result review and corrections

This section incorporates the subsequently supplied `nov27-1700-exp1-pca.txt` analysis. It adds a second set of run-level summaries and, importantly, corrects the interpretation of the earlier “exact solve” labels. Where this supplied analysis conflicts with the earlier artifact audit in Sections 2 and 6–7, the discrepancy is retained explicitly rather than silently choosing one denominator or dataset snapshot.

### 11.1 Runs and execution coverage in the supplied 17:00 analysis

| Workflow | Run number in supplied analysis | Reported outcome | Reported coverage |
|---|---:|---|---:|
| `exp1_4060_seeds` | #354 | Success | 5 seeds × 74 = 370 |
| `exp1b_pca` | #345 | Success | 5 seeds × 74 = 370 |
| `exp1_pca` | #344 | Success | 5 seeds × 74 = 370 |

The supplied analysis says that #354 is the corrected run reference (the initially supplied run ID had one extra trailing digit), and distinguishes it from earlier run #353, which did not actually launch the benchmark. It reports that all five random-split workers launched, processed 74 equations each, passed seed/protocol validation, and passed aggregation. This supports execution completion for that Actions run; it does not validate the scientific correctness of the “exact solve” label.

### 11.2 Correct interpretation of “0/370” and “35/365”

The supplied analysis identifies a concrete measurement error in `scripts/ci/exp1_4060_seed_outputs.py`: the validator reads `results.hybrid.test_r2` and counts a case as a “solve” when that predictive score reaches 0.999999. That is a near-perfect predictive-R² threshold, **not symbolic equivalence**.

Accordingly:
- The random result previously described as **0/370 exact symbolic solves** must be withdrawn as a symbolic-recovery claim. The defensible description is **zero cases reported at the hybrid held-out R² threshold by that validator**.
- The supplied source review identifies five intractable IL-breakeven cases excluded from finite R² scoring, so it says the threshold denominator should be **365**, with the five unscored cases reported separately. On that interpretation the result is **0/365 finite cases at the threshold**, not 0/370 symbolic solves.
- The PCA **35/365 (9.59%)** figure is the same type of near-perfect predictive-R² threshold count, not 35 symbolically equivalent equations. It must not be called an exact solve rate.
- Symbolic recovery for these historical runs remains **not established / not assessable** unless a separate symbolic-equivalence audit has the required ground truth, generated formula, explicit variable mapping, and valid audit context.

This correction is consistent with the measurement-integrity intent of PRs #424 and #426 and the historical 740-record audit in Section 6: the absence of ground-truth expressions in those records prevents a retrospective symbolic verdict. A successful workflow and a high R² threshold count cannot fill that evidence gap.

### 11.3 Denominator and snapshot inconsistencies requiring reconciliation

The supplied 17:00 analysis states that:
- Random 40/60 has 365 finite scored cases, with five intractable cases excluded.
- PCA 40/60 has one undefined Kelly metric per seed, which arithmetically implies 365 finite scores from 370 records.
- However, its performance table says PCA R² comparisons use **360** valid records, while its symbolic-threshold panel says **35/365**.

The PCA denominator statements are internally inconsistent: five undefined values out of 370 imply 365 finite values, not 360. The earlier audited artifact summary in this report also recorded 365 finite PCA hybrid R² values and 370 finite random values for its inspected snapshot. These differences may reflect distinct run outputs, metric fields, or artifact versions; the available supplied note does not resolve them.

Therefore, the 17:00 table below is preserved as a *reported summary*, not treated as a fully reconciled raw-record recomputation. Before publication, recompute denominators from the exact per-seed JSON files for runs #354 and #345, separately counting raw records, finite values, undefined values, and cases excluded by each metric. Do not mix these with the earlier artifact snapshot without matching run IDs and commit SHAs.

### 11.4 Reported predictive-performance comparison from the 17:00 analysis

The supplied analysis reports the following (its PCA denominator caveat above applies):

| Metric | Random 40/60 | PCA 40/60 |
|---|---:|---:|
| NN median test R², average of seed medians | **0.9961** | 0.8826 |
| Hybrid median test R², average of seed medians | **0.9970** | 0.9686 |
| NN test R² > 0.90 | 75.62% | 49.44% |
| Hybrid test R² > 0.90 | 81.64% | 60.83% |
| Hybrid test R² > 0.99 | 67.67% | 43.61% |
| Median NN runtime, average of seed medians | 0.340 s | 0.303 s |
| Median hybrid runtime, average of seed medians | 1.448 s | 1.348 s |

The supplied analysis additionally reports random-split mean test R² of approximately **0.804 for NN** and **0.822 for hybrid**, despite medians near 1. This is an important distributional warning: a strong median can coexist with a substantial catastrophic lower tail because R² is unbounded below.

Within this reported summary:
- The hybrid's median improvement over NN is small under random 40/60 (0.9961 to 0.9970).
- The hybrid's median improvement is much larger under PCA 40/60 (0.8826 to 0.9686).
- Hybrid median runtime is approximately **4.3×** NN under random 40/60 and **4.45×** under PCA 40/60.

These medians and percentages should be read as descriptive summaries from the supplied analysis, not inferential evidence. The full distributions, exact finite denominators, and run/commit provenance need to be reconciled before final publication.

### 11.5 Data-quality and orchestration issues raised by the supplied source review

The supplied analysis flags three implementation/reporting risks:

1. **Stale `exp1_pca_summary.json`:** the checked-in file is reported to have a 2026-09-19 timestamp and a 51/74 figure, whereas run #344's aggregate manifest reportedly validates 370 records. The stale summary must not be used as the metric summary for run #344. Regenerate a summary from the exact run artifacts and retain its provenance.
2. **Non-standard NaN in random raw JSON:** the supplied review says the 4060 raw result JSON contains NaN values accepted by the aggregate validator but rejected by strict JSON parsers. Normalize non-finite values to a standards-compliant representation (for example, null plus an explicit status) and make the validator enforce strict JSON.
3. **`run_all.sh` seed contract:** the supplied source review says the `run_all.sh` stage invokes `run_exp1_4060_seeds.sh` without setting `SEED` or looping over the five seeds, while the helper requires one explicit seed. If confirmed against the current branch, this means the local `run_all.sh` stage is not a valid five-seed invocation; a successful GitHub Actions matrix with explicit per-worker seeds does not prove that the `run_all.sh` stage works. The stage should either loop explicitly over the declared seed list or be renamed/documented as a single-seed operation with a required `SEED`.

The run_all.sh finding is recorded here as a source-review finding from the supplied analysis; it should be rechecked against the exact current commit before implementation or release sign-off.

### 11.6 Scientific findings when the new results are read together

The combined evidence supports a more careful, two-axis interpretation:

- **Predictive interpolation/generalisation:** the supplied median summaries favour random 40/60, while the PCA-directed split is harder and has lower NN and hybrid medians. The random mean-versus-median gap warns that its typical case is not representative of its lower tail.
- **Value of the hybrid:** the reported median gain is marginal on random 40/60 but substantial on PCA 40/60. This suggests the hybrid may be more useful where the NN baseline is weaker, but does not by itself establish that the LLM component caused the gain; the route audit shows that fallback and replacement predictors are common.
- **Symbolic discovery:** neither 0/365 nor 35/365 is a symbolic-recovery result. They are predictive-R² threshold outcomes. The historical symbolic status remains not assessable where ground truth is missing.
- **Protocol interpretation:** random and PCA 40/60 should be presented as different generalisation regimes, not as proof that one model is intrinsically superior. Random splitting is closer to same-distribution interpolation; the PCA-directed split is intended as a harder feature-space stress test.
- **Execution integrity:** run completion and worker coverage are positive operational evidence, but they do not validate metric semantics, denominators, JSON validity, or the separate `run_all.sh` orchestration path.

### 11.7 Required follow-up before publication

1. Recompute all reported metrics from run-ID-pinned raw JSON for #354 and #345, and resolve the 365-versus-360 PCA denominator discrepancy.
2. Report raw records, finite metric records, undefined metrics, and excluded/intractable cases separately for every metric.
3. Rename every (R^2 \ge 0.999999) count to **near-perfect predictive-R² threshold count/rate**; remove “exact solve” and “symbolic recovery” labels from those validator outputs.
4. Run the independent symbolic-equivalence evaluator only on artifacts with persisted ground truth and explicit variable mappings; keep historical missing-ground-truth cases as not assessable.
5. Verify and fix the `run_all.sh` seed invocation contract against the exact commit; test the orchestration contract without launching expensive benchmark work.
6. Enforce strict JSON output and regenerate the stale `exp1_pca` summary from run #344 artifacts.
7. Report median, mean, quantiles, lower-tail failures, and per-seed values together; add paired uncertainty analysis before inferential claims.
8. Keep hybrid R², selected-predictor R², and symbolic-equivalence outcomes in separate tables with field names and provenance.

**Updated overall conclusion:** the supplied 17:00 results strengthen the evidence that the hybrid can materially improve median predictive performance under the harder PCA-directed split, while random 40/60 has higher reported medians and a severe lower-tail caveat. They do **not** establish symbolic recovery rates. The earlier headline “0/370 exact solves” is invalid as a symbolic claim and should be withdrawn; the PCA “35/365 exact solve rate” is likewise a near-perfect predictive-R² threshold count, not symbolic equivalence. Exact denominators and run snapshots still require reconciliation.

### Scope note for this addendum

This addendum is a documentation synthesis of the user-supplied 17:00 analysis and the earlier report/audit context. It does not claim that the flagged source defects were fixed or that new benchmark data were generated. No benchmark, training job, LLM request, workflow dispatch, or merge was initiated for this update.
