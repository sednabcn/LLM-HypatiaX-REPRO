# HypatiaX publication-readiness review

**Review date:** 2026-11-08  
**Repository:** `sednabcn/LLM-HypatiaX-REPRO`, reviewed from `master`  
**Status:** preliminary audit; **not yet cleared for submission**

## Executive assessment

The repository contains substantial experiments, a maintained reproducibility pipeline, and a manuscript that already acknowledges important negative findings. The current evidence supports a balanced paper about a hybrid symbolic/neural system with task-dependent strengths and material limitations. It does not support a broad claim that the hybrid consistently outperforms its baselines or that routing eliminates catastrophic failures.

The immediate risk is **manuscript and evidence reconciliation**: the main-paper source is only present under `archive/`, its referenced bibliography and several named figure assets are absent from the current tree, and the main-paper abstract conflicts with a supplementary statement about Nguyen-12. The Phase 2 report also retains open items. Resolve these before submission.

This review now incorporates the **HypatiaX Submission-Blocker Report dated 13 October 2026**, which was prepared from the three PDFs in full and recomputed arithmetic from their printed tables. That report's scope limitation matters: its PDF-level findings are not, by themselves, source-code or result-file verification. Repository checks below should be treated as a separate evidence layer. Where the two layers have not yet been reconciled, the item remains open.

## 1. What is already in place

- `README.md` documents experiment and CI entry points.
- `ci_runner_repro.yml` dispatches experiments; `ci_pipeline_check.yml` provides completion and qualification checks.
- Main-paper and supplementary TeX sources exist under `archive/patches/fix_out/patched/`.
- Result families cover DeFi, Core-15, Protocol-30, Nguyen-12, ablations, noise/sample-complexity, and portfolio audits.
- The portfolio PCA/random-holdout case now has a clear publication boundary and route-specific metrics. Further portfolio investigations are future work, not blockers for that case.
- The main-paper source acknowledges that corrected DeFi near-perfect recovery ties the Pure-LLM baseline, catastrophic failures remain, and runtime is higher than the neural baseline.
- A historical provenance audit exists at `archive/audit/audit_out/`. Its summary reports 52 contaminated, 196 no-provenance, and 6 unreadable unique files in its historical scope. This is a warning, **not a current classification of every result on master**; rerun it against the exact evidence selected for submission.

## 2. Consolidated blocker register from the PDF audit

The following identifiers preserve the October report's A/B/C taxonomy. They should be used in issue tracking, manuscript edits, and the final close-out checklist.

### Part A — claims contradicted by the papers' own evidence

| ID | Required action | Submission action |
|---|---|---|
| A1 — stale gains and mechanism framing | REWRITE | Remove claims that gains are largest on hardest tasks, that the hybrid exceeds Pure LLM on the corrected 59.5% measure, or that the cascade eliminated/detected failures or established distance-dependent error mechanisms. State the corrected zero-pp tier gains and the measured 3.8–11.2x slowdown versus NN. |
| A2 — unsupported instability claims | REMOVE unless the multi-run study is run and reported | Remove run-to-run Instability Index, 30-independent-runs, Regime C, instability/extrapolation correlation, and claims that Stage 2 predicts instability. The paper itself says no multi-run Instability Index is reported. |
| A3 — Supplement B recovery rates and thresholds | REWRITE / RECOMPUTE | Correct EHSDeFi's 96.7% noisy recovery where Table 9 reports it; correct 96.7% sample-size results; select one threshold policy and recompute every rate. Table 25's fixed 0.99 policy is the proposed consistent basis, subject to verifying the underlying files. |
| A4 — Supplement A gains, checklist, and evaluator contradiction | REMOVE / FIX-RERUN | Delete untraceable +6/+5/+1/+1 pp lines; correct checklist claims about 96.7%, Cohen's d, and figure availability. Inspect Listing 8 against the claimed relative-threshold Fix 5; rerun affected DeFi results if code still uses `ss_tot > 1e-10`. |
| A5 — Supplement B appendices contradict main results | REMOVE / REBUILD | Remove or rebuild Appendix H/I claims that conflict with main tables: perfect recoveries for incomplete equations, Gravitational Force failure, Henderson-Hasselbalch scores/rescue, ideal-gas constant provenance, 4.3x speedup, DeFi 100%, and unsupported 131-test claims. |
| A6 — unsourced main Section 3 / Supplement A D.1 | REMOVE / REBUILD | Replace the GPT-4/40-task narrative and unsupported scores/mechanism with a description derived from pinned DeFi Tables 20/21. Reconcile the VaR sign-error claim with the reported VaR-95 result. |

### Part B — integrity-sensitive items

| ID | Required action | Submission action |
|---|---|---|
| B1 — synthetic data statement | REMOVE, THEN AUDIT | Delete the statement that synthetic versions match reported statistics exactly. Verify no synthetic file contributed to a table or figure and none is shipped in the release. |
| B2 — PureLLM bypass and M4 auditability | FIX/RERUN or REMOVE HEADLINE | Store formulas and rerun baseline/hybrids with bypass disabled; report both bypass-on and bypass-off results. If not completed, remove M4 exact/zero-variance/READY claims and M3-vs-M4 win-rate narrative. Remove M3's exact symbolic interpretability claim where ensemble-first routing blends an NN. |
| B3 — circular attribution correction | REWRITE; ideally FIX/RERUN | Do not call the attribution issue a proven bug or claim a tier-by-tier tie as an empirical finding when the corrected metric substitutes a separate Pure-LLM score by construction. Store and re-score the hybrid's own formula on the same split. Until then label the 23 cases unverifiable from stored records; remove masked-failure inferences. Explain identical raw hybrid counts and timing discrepancy. |
| B4 — test-information leakage and benchmark tuning | REWRITE / FIX | Fix or remove use of `X_test` in Fix 4's blend-weight calculation. Disclose that routing fixes were tuned on the same DeFi tasks used for evaluation. Reconcile the intractable Impermanent Loss Breakeven label with its reported perfect score and the claimed zero intractable cases. |
| B5 — noise-sweep validity | FIX/EXPLAIN | Establish whether R² is measured against clean or noisy targets and verify noise was applied as specified. Reconcile the 5% sample-size sweep versus noiseless descriptions and the claim that all main experiments use 5% noise versus noiseless DeFi/Protocol-30 runs. |

### Part C — provenance and specification inconsistencies

| ID | Required action | Submission action |
|---|---|---|
| C1 — data provenance and run comparability | FIX | Create one archived, DOI-bearing snapshot of exact result files and a table-to-file manifest. Reconcile multiple DeFi seed-42 files, v4 source-of-truth path, m27 versus seed42 citation, 2026-08-12 versus 2026-03 source generations, mixed-run tables, environment dates, unequal Phase 3 timeouts, extreme Arrhenius runtime, HDSv50_2 runtime aggregation, and model identity/disclosure. |
| C2 — inconsistent method specification | REWRITE to one specification | Define one authoritative routing and model specification: Stage 2 trigger/token set, Stage 3 degradation metric and action, ensemble weighting, OOD estimator, NN architecture/training budget, PySR settings, and prompting determinism/temperature/seeding. Conform main and both supplements to it. |
| C3 — system identity | REWRITE | Name the system that is the paper's contribution. Distinguish HybridDiscoverySystem v50_2, EHSDeFi (M3), and HLLMNN (M4) as separate systems or baselines where appropriate; ensure Algorithm 1 and figures describe the named contribution. |
| C4 — Core-15 incomplete equations | FIX/RERUN | Diagnose and rerun the five non-completing equations and Constant Product's extreme score. Do not present engineering failures or NaNs as scientific ablation results; reconcile Appendix H. |
| C5 — Proposition 11 and empirical “proofs” | REWRITE / DEMOTE | Correct numbering and statement/figure mismatch; either supply a valid proof under the actual phase budgets or present as a design remark. Apply the same standard to empirical findings and Appendix A intuition. |
| C6 — validation-layer percentages | REMOVE unless supported | Remove percentages whose stated n=15 denominator is arithmetically impossible, relabel shares of rejections if that is what they represent, correct Wilson intervals, and remove unsupported “no incorrect expression passed all four layers” claim. Reconcile V1–V4 with the five-stage router. |

### Part D — credibility and editorial removals

Remove revision-history and internal audit narrative from the journal manuscript and supplements: earlier-version/retracted/superseded wording, internal data-provenance notes, filenames, hashes, commit IDs, CI run numbers, FIX-C3 labels, and source filenames in prose. Put any necessary correction in a concise errata note.

Also remove or relocate the specific material flagged in the October report: Supplement B readiness/version notes, JMLR readiness assessment and READY labels, CI dashboard/exp2 baseline-lock discussion, citation-key/SNIP notes, corrected-value annotations, and unsupported or misleading published-baseline comparisons. Remove Supplement A's stale roadmap, post-submission references, unsupported training-exposure counts, operation-count comparison that omits PySR/LLM latency, and statements that the hybrids addressed all three needs. Recheck the cited literature and the listed typos/definition inconsistencies.

## 3. Arithmetic checks reported as consistent

The October PDF audit reports that the following arithmetic was recomputed and consistent with the printed tables:

- Pure LLM DeFi: 5 catastrophic cases, 18 NaNs, 44/74 (59.5%) with R² > 0.99, and 45/74 (60.8%) with R² > 0.9.
- Table 3 means: Pure LLM -0.3048 over 56 tasks and corrected HypatiaX -0.3203 over 62 tasks.
- Protocol-30 Table 26 pass counts: HDSv50_2 21/30, EnhancedHybridSystemDeFi 23/30, HLLMNN 30/30, PureLLM 29/30, ImprovedNN 0/30.
- Tables 13/14 routing counts 140/150, 123/150, 27/150, and combined tie rate 294/330 (89.1%).
- Nguyen-12 per-seed totals 51/60 and 49/60, Table 32 per-equation counts, and seed-42 table.
- Core-15 tally: 1 HypatiaX-better, 4 PySR-better, 6 ties, 4 NaNs.

These are **PDF-table arithmetic checks**, not independent validation of the underlying runs, provenance, or method validity. In particular, the Nguyen-12 aggregate arithmetic being consistent does not by itself resolve what the N-12 gate-abort note means or whether it refers to the same configuration and success definition.

## 4. Defensible claim boundary after correction

The October report proposes a narrower contribution that is consistent with the negative findings:

1. A 74-task DeFi benchmark and an audit method for hybrid-LLM systems, including hardcoding and success-attribution checks.
2. On that benchmark, the hybrid's self-reported success is unverifiable from stored records, and corrected aggregate performance is not shown to exceed the LLM component. Runtime is 3.8–11.2x worse than the NN.
3. Two rescue cases (Arrhenius and Portfolio Variance, 2/5 seeds) may be described as observations, not mechanisms.
4. Nguyen-12 may be reported as 51/60 versus 49/60, with no significance claim, while explicitly reporting the N-12 gate abort and resolving its relationship to the aggregate result.
5. Protocol-30 may be reported as HypatiaX 21/30 random and 13/30 PCA held-out, with the custom-set status and PureLLM bypass disclosed. Symbolic and hybrid methods beat the NN in the reported comparison.

M3/M4 sweeps should remain exploratory unless B2 and A3 are resolved. Do not claim general hybrid superiority, elimination of catastrophic failures, proven instability mechanisms, or broad generalization beyond the tested protocols.

## 5. Earlier repository-level blockers and package checks

The following repository checks remain relevant. They are separate from the October PDF report's A/B/C identifiers.

### R1 — Establish one authoritative manuscript package

The only main-paper source found is `archive/patches/fix_out/patched/jmlr_paper_main_cleaned.tex`; the supplementary source is `archive/patches/fix_out/patched/supp_benchmark_report_cleaned.tex`. There is no obvious active manuscript directory under `docs/` or at repository root.

The main TeX calls `\\bibliography{references}`, but the current repository tree contains no `.bib` file. It also references figure assets including `hypatiax_three_systems`, `hypatiax_algorithm1_routing_cascade_v2`, `fig1_seed_sweep`, and `fig18_r2_heatmap_improved`; none of those assets was found in the current tree.

**Required:** establish the authoritative submission source directory; restore/include the exact bibliography, figure assets, style files, and supplementary sources; document a reproducible clean-build command.

### R2 — Reconcile Nguyen-12 claims and gate semantics

The main-paper abstract reports 51/60 HypatiaX versus 49/60 PySR-only over five seeds. The supplementary report's cross-reference note says HypatiaX fails Nguyen-12 on all five seeds because the LLM gate rejects all candidates and the run aborts before search. The October PDF audit confirms the printed per-seed totals and Table 32 arithmetic, but this does not settle whether the gate-abort note refers to a different configuration, stage, or definition of success.

**Required:** trace both statements to exact result files, workflow/run provenance, commit, model version, configuration, and score threshold. Explain the N-12 gate-abort behavior alongside the reported aggregate; correct stale wording if necessary. Make no significance claim.

### R3 — Reconcile Phase 2 status with paper claims

`docs/phase2_report.tex` says the PySR-only versus HDS comparison is closed with caveats, but the Pure-LLM comparison specified by Option 3 was not run. Its open-items list still calls for prompt matching, sampling/retry decisions, a dry run, and the full Pure-LLM run. It also lists manual Supplement A Listing 8 verification and confirmation of whether runtime includes LLM time and retries.

**Required:** remove claims that depend on the unrun comparison, or complete and close those items with evidence. Do not present a planned comparison as completed.

### R4 — Run a current, scoped provenance audit

The historical audit is not enough for a submission decision. The repository has multiple generations of outputs, rescued shard files, checkpoints, exploratory/pre-fix results, and consolidated results.

**Required:** define the exact submission evidence set, then rerun provenance checks on that set. For every headline table/figure, record source path, run ID, commit SHA, experiment configuration, split protocol, seed, metric definition, and bypass/cache/fallback flags. Exclude or label pre-fix, exploratory, duplicate, rescued, and unverified files.

### R5 — Build and inspect the complete paper package

The current tree does not contain the referenced bibliography or the named figure assets, and no complete self-contained submission bundle was established.

**Required:** verify every `\\input`, `\\include`, bibliography, figure, table, and supplementary cross-reference from the authoritative source directory; compile from a clean checkout and inspect the PDF. Record compiler, style/package dependencies, and build output.

## 6. Portfolio case publication boundary

The portfolio PCA/random-holdout work is frozen for the current publication cycle. Its current evidence supports only the bounded claims recorded in the committed comparison report:

- Five random-holdout partitions yield mean NN test R² 0.999709 (sample SD 0.000121; all five above 0.99).
- Five PCA-directed seed-sweep runs use one fixed transductive split and select the LLM/formula route; their R² must not be described as NN performance.
- The separate NN PCA-tail diagnostic has train R² about 0.999740 but test R² about -3.151809, with systematic upper-tail underprediction.
- Each individual feature reproduces the same PC1 ordering and training membership in this dataset.

No general PCA advantage or general NN extrapolation claim follows. Further multivariate portfolio, bootstrap, and cross-domain investigations are post-investigation work, not immediate submission blockers.

## 7. Recommended close-out sequence

1. **Freeze the claim set:** map every abstract/contribution claim to its exact table, figure, and result artifact. Apply A1/A2/A3/A5/A6 and Part D text corrections where the evidence is already decisive.
2. **Unify the method and system specification:** resolve C2/C3, then reconcile the main paper and both supplements to one implementation description.
3. **Inspect code-sensitive contradictions:** Listing 8/Fix 5 (A4), Fix 4 test leakage (B4), and the noise implementation/scoring (B5).
4. **Resolve integrity-sensitive evidence:** B1 synthetic-file audit; B2 bypass-off reruns or remove M4 headline; B3 same-split hybrid formula re-scoring or withdraw unsupported attribution claims; C4 Core-15 diagnosis/reruns.
5. **Resolve provenance and budgets:** C1 snapshot/manifest/model identity/equal timeouts; R4 scoped audit.
6. **Reconcile Nguyen-12 and Phase 2:** R2/R3, preserving the distinction between arithmetic consistency and gate behavior.
7. **Build and inspect:** R1/R5, clean compilation, PDF inspection, then repeat the cross-document consistency review.
8. **Submission freeze:** tag the exact commit and archive the built PDFs, source package, and evidence manifest.

## 8. Current decision

**Not yet submission-cleared.** The highest-priority work is correction of unsupported claims, method/specification reconciliation, integrity-sensitive reruns or claim removal, and release provenance. Do not expand the experiment catalogue merely to make the paper appear more positive. Preserve the negative findings; they define the defensible contribution.

---

## Evidence inspected

Repository-level review:
- `README.md`, `MANIFEST.md`
- `docs/phase2_report.tex`, `docs/phase2_closure_record.md`
- `archive/patches/fix_out/patched/jmlr_paper_main_cleaned.tex`
- `archive/patches/fix_out/patched/supp_benchmark_report_cleaned.tex`
- `hypatiax/data/results/ablation/exp1_ablation/exp1_llm_contribution.json`
- `hypatiax/data/results/ablation/exp1_ablation/exp1_rf01_mannwhitney.json`
- `hypatiax/data/results/ablation/exp1_ablation/exp1_instability_stats.json`
- `hypatiax/data/results/ablation/exp1_ablation/fixc3_baseline.json`
- `archive/audit/audit_out/manifest_summary_v2.txt`
- `hypatiax/data/results/portfolio_variance_audit/portfolio_variance_pca_vs_random_holdout_comparison.md`

October PDF audit supplied by the user:
- Main paper PDF, Supplement A (routing improvements), Supplement B (benchmark, noise, sample complexity), read in full by the report author.
- Scope: cross-document consistency and arithmetic recomputation from printed PDF tables; no result JSONs or repository access were available to that audit author. Findings requiring code/data inspection are therefore retained as FIX/RERUN items, not marked verified.


## 9. Code inspection round 1 — A4 and B4

This pass inspected the current `master` implementation and workflow sources. It does not modify `master`.

### A4 — R² evaluator contradiction: current implementation mostly resolves the runtime side; manuscript provenance remains open

**Verified in current source:**

- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py` imports `r2_checked` from `hypatiax.core.r2_canonical`. Its `_compute_metrics` and `_eval_formula_r2` route reported formula/NN scores through that canonical scorer.
- `hypatiax/core/r2_canonical.py` uses a spread-relative degeneracy test: `ss_tot <= 1e-24 * max(sum(y_true**2), 1e-300)` is undefined (NaN/status `degenerate_target`). It does not use the old absolute `ss_tot > 1e-10` gate.
- `hypatiax/core/generation/hybrid_defi_system/hybrid_system_nn_defi_domain.py` delegates its checked R² function to the same canonical helper.
- `hypatiax/core/generation/hybrid_all_domains_llm_nn/hybrid_system_llm_nn_all_domains.py` also delegates to the canonical helper.
- `hypatiax/experiments/tests/test_r2_policy.py` tests tiny-scale varying targets, degenerate targets, failure handling, migration of central scorers, and guards against new local R² implementations.

**Important distinction:** Supplement B's tracked TeX still documents an older Fix 5 implementation using an offset/magnitude-relative tolerance, while the current canonical scorer uses a spread-relative degeneracy rule. Both avoid the original absolute floor, but they are not the same policy. The manuscript and supplement must describe the current policy precisely, including the treatment of constant/near-constant targets as undefined rather than assigning 0 or 1.

**Unresolved evidence gap:** the repository tree contains the main-paper TeX and Supplement B TeX, but no Supplement A source file. The reported Supplement A Listing 8 cannot therefore be checked line-for-line against the current source from this checkout. The PDF-level contradiction remains a manuscript packaging/reconciliation task until the exact Supplement A source used to generate the PDF is supplied or restored.

**Test-harness configuration checked:** the initial concern that `RECOVERY_EVAL` was unset in CI was incorrect. `hypatiax/experiments/tests/conftest.py` sets the default to `hypatiax.core.recovery_eval:recovery_r2`, while still allowing an override. The workflow invokes `test_recovery_evaluator.py`, and the test resolves to the repository's canonical evaluator through that fixture. Do not treat a missing environment-variable setting in the workflow YAML alone as a defect. A successful R2-policy run observed during this pass was PR-triggered on branch `fix/rerun-blockers` (run #201), not a master-branch run, so it is not evidence of a master CI result.
 
**A4 disposition:** current principal benchmark code is migrated to the canonical relative scorer, but the PDF listing discrepancy, stale Supplement B explanation, absent Supplement A source, and non-self-contained recovery-test invocation still need closure. Do not rerun the DeFi benchmark solely on the basis of the old listing until the exact historical Listing 8 and the result-producing code revision are matched.

### B4 — Fix 4 test-information claim: code confirms input-dependent use of the test batch

**Verified in current source:**

- `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py` defines `_distance_llm_weight(X_test, X_train, base_weight=0.3)`.
- It calculates the fraction of test rows with at least one feature outside the per-feature training min/max range, then returns `base_weight + (1 - base_weight) * outside`.
- In the ensemble route, `_hybrid_predict_and_eval` calls this helper with `X_test`; if every test row is outside at least one training feature range, the returned LLM blend weight is 1.0.
- The source comments explicitly acknowledge that the final blend weight uses `X_test` inputs and no `y_test` labels, and that the manuscript's “training data only” statement must be amended.
- The same function uses training residuals for uncertainty estimation; that does not remove the separate test-covariate dependence in the distance gate.

**Interpretation:** this is not target-label leakage because the code does not read `y_test` to set the blend weight. It is nevertheless test-batch/covariate-aware routing, so the stronger manuscript claim that routing uses training data only is false for this implementation. If the benchmark is intended to simulate a batch of known query inputs, describe the method as transductive/input-range-aware and disclose the batch-level dependence. If a strictly inductive protocol is required, replace the test-batch statistic with a per-query rule or a training-only threshold and rerun affected results.

**B4 disposition:** confirmed manuscript/specification mismatch. The reported “rho approximately 1” behavior should be recomputed from the exact pinned run outputs before stating how often the weight reached 1.0; the source formula alone establishes the possibility, not the observed frequency.

### Next code-audit targets

1. B2 — inspect generator bypass flags, formula persistence, and M4 result schema; determine exactly which stored rows can be audited.
2. B3 — inspect the corrected attribution calculation and whether hybrid formulas/predictions can be recovered for same-split rescoring.
3. B5/A3 — trace noise injection, target arrays used for R², and threshold configuration across noise and sample-size runners.
4. C2/C3 — map the actual runner implementation to the paper's Stage 2/3, ensemble, NN, PySR, and system-identity descriptions.


## 10. Code inspection round 2 — B2 and B5

### B2 — bypass removal is present in current generator code; historical M4 headline remains unusable

**Verified in current source:**

- `hypatiax/core/base_pure_llm/baseline_pure_llm_defi_discovery.py` documents an input-parity prompt with no equation-specific ground-truth formula, code template, or data-derived hints.
- Its `_try_hardcoded_formula(...)` is an explicit no-op returning `None`; the prior hardcoded and OLS-fit branches are deleted.
- The generator removes metadata keys such as `ground_truth`, `formula`, `hint`, and data-statistic fields before prompt construction. It records `bypass_kind="live"`, prompt hash, model source, and bypass flags.
- The disable switches are fail-closed: unset means clean mode unless legacy mode is explicitly allowed. `run_all.sh` exports both hardcoded and prompt-hint disable flags as enabled by default and blocks legacy mode in GitHub Actions.
- `HybridSystemLLMNN` delegates to `PureLLMBaseline`; the `force_llm` guard skips NN training when a valid LLM formula is available. That is an LLM-versus-NN routing decision, not itself evidence that the LLM call was bypassed.
- The stored M4 records in the inspected Protocol-30 files have `formula="N/A"`, R²=1.0, and no `llm_called` field. They are marked `provenance_status="unverified_no_formula"` and `exclude_from_reported_results=true`. In the inspected `exp2_multi` JSON, all three M4 rows are excluded and the per-test comparison score/ranking fields no longer include M4.
- The repository contains `mark_m4_unverified.py`, `close_m4_exclusion.py`, and a regression test for excluding M4 from comparisons.

**Remaining gap:** exclusion is not yet complete for all derived outputs. The inspected sample-complexity JSON (`sample_complexity_20260812_180007_nshards02.json`) still reports M4 aggregate recovery of 100% and carries per-equation M4 values without formulas or the exclusion flag. The current `close_m4_exclusion.py` updates per-test comparison fields and adds exclusion columns to noise/sample-complexity CSVs, but it does not rewrite the JSON `method_summary` / `per_n` aggregates. The current sample-complexity and noise-sweep orchestrators also still list M4 among the methods they can run; no fresh bypass-off M4 rerun artifact was established in this pass.

**B2 disposition:** current generator-side hardcoded/prompt bypasses have been removed, and several old M4 rows are correctly excluded. That does not validate the old M4 100% headline. Until every M4-derived table/JSON aggregate is either recomputed excluding unverified rows or replaced by a fresh run that stores formulas and per-row provenance, remove the M4 exact/zero-variance/READY claims and the M3-vs-M4 win-rate narrative. Treat M4 as unverified, not as a failed or successful model, where its formula/provenance is absent.

### B5 — current noise protocol is explicit, but the historical headline files do not prove it was followed

**Verified in current source:**

- `run_comparative_suite_benchmark_v2.py` reads `HYPATIAX_NOISE_LEVEL` and, for positive sigma in noisy mode, adds Gaussian noise with standard deviation `sigma * std(y)` to each target vector before the train/test split.
- The noise stream is derived from the equation description and, when supplied, `EXPERIMENT_SEED`; the runner records the number of perturbed equations and noise seed.
- The output protocol declares the noise definition and `scored_on="noisy targets (train and test)"` for positive sigma; it also records the theoretical R² ceiling.
- `run_noise_sweep_benchmark.py` now specifies a single default recovery threshold of 0.99 (plus exact recovery at 0.999999), checks that selected result files match the launched sigma/seed, and flags scores above the noisy-target R² ceiling.
- `run_sample_complexity_benchmark.py` also has a single default 0.99 threshold, an optional exact threshold, result matching by sigma and sample size, and a noise-ceiling check.
- The current `run_all.sh` `suppB_sc` step explicitly passes `--noiseless`. The stored sample-complexity JSON inspected (`sample_complexity_20260812_180007_nshards02.json`) declares `mode="noiseless"`; its threshold map is the old per-sample ladder (0.999, 0.9995, 0.9999, ...), not the current unified threshold policy.

**Historical output problem:** the inspected 1%-noise sweep JSON from 2026-08-12 reports median R² around 0.9999998 for M3/M4, above the theoretical ceiling for scoring against targets perturbed at 1% of their standard deviation (approximately 0.99990001). That file has no per-run protocol block showing `noise_definition`, `scored_on`, `noise_injected_equations`, or `noise_seed`. It therefore cannot establish that noise was applied and that R² was scored against noisy targets. The current code's audit logic does not retroactively validate this older file.

**B5 disposition:** current implementation contains an explicit injection/scoring protocol and a ceiling audit, but the old headline outputs do not carry the metadata needed to verify the protocol and their scores exceed the noisy-target ceiling. Do not use those historical numbers as noisy-target recovery results. Regenerate the noise sweep with the current runner and archive the resulting protocol metadata. For sample complexity, either report the current pipeline's noiseless protocol consistently or deliberately run a noisy sample-size sweep; do not mix the two descriptions. Recompute recovery rates under the single 0.99 policy after the rerun.



## 11. Code inspection round 3 — C2 and C3 method/system identity

### C2 — the tracked DeFi implementation does not match the manuscript's five-stage description

The current 74-task runner `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py` was compared with the main-paper routing description.

| Component | Main-paper description | Current v3c implementation |
|---|---|---|
| Stage 2 token set | `exp, log, Phi, sin, cos, erf`; triggers ensemble mode | `exp, log, sqrt, norm.cdf, norm.pdf, scipy.stats, maximum/minimum, max/min, sin/cos, fractional powers`; if formula is trustworthy, decision is changed to **LLM** |
| Stage 3 degradation | LLM formula train R² minus LLM formula edge R²; large degradation triggers ensemble | Trains an MLP on the first 85% of the ordered training rows and probes the last 15%; computes MLP train R² minus probe R²; threshold is hard-coded at 0.15; if exceeded, decision is changed to **LLM** |
| Stage 4 OOD | KDE on training projections estimates OOD probability | `_distance_llm_weight` uses the fraction of `X_test` rows outside the per-feature min/max training range |
| Stage 5 ensemble | Main-paper equations describe OOD-probability weighting and confidence-normalised weights | Current code first derives an input-range LLM weight from the test batch, then combines LLM and NN using training residual uncertainty and training R² values |

This is a substantive method mismatch, not just a wording difference. The same route cannot simultaneously use the paper's LLM-formula edge score/KDE/ensemble trigger and the code's MLP probe/range-based test-batch gate/LLM override.

**Required:** decide whether the manuscript is intended to describe the current v3c runner or another historical implementation. If v3c is authoritative, rewrite the method, pseudocode, equations, figures, and ablation interpretations to match it. If the paper's five-stage method is authoritative, implement that method in a pinned runner and rerun all affected results. Do not combine descriptions from different versions.

### C3 — the repository contains several distinct system implementations

The current tree and benchmark sources distinguish at least:
- the 74-task DeFi runner in `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py`;
- `EnhancedHybridSystemDeFi (core)`;
- `HybridSystemLLMNN all-domains (core)`;
- `HybridDiscoverySystem v50_2 (tools)`;
- `SymbolicEngineWithLLM (tools)`.

The all-domains M4 implementation delegates formula generation to `PureLLMBaseline`, has a `force_llm` branch that can skip NN training, and has its own fallback prompt and ensemble/refinement path. That is not interchangeable with the self-contained v3c DeFi cascade. The method names in result files are therefore not cosmetic labels.

**Required:** name one system/version as the paper's primary contribution, map each result table to the exact implementation and commit, and describe M3/M4 and other engines as separate systems or baselines where appropriate. Algorithm 1 and Figure 2 must describe the same implementation used to produce the reported results.

### Additional implementation details to pin

- The current v3c MLP defaults to hidden layers [128, 64, 32], LayerNorm + SiLU, Adam learning rate 0.001, and a 120-second wall-clock cap; the Stage 3 probe explicitly overrides the network to [64, 32] for 200 epochs. These are not the same as the Supplement B M4 [64, 32, 1] ReLU / 0.01 / 200-epoch description. State which implementation each table uses.
- The v3c built-in formula call explicitly sends temperature 0.0. The Nguyen-12 path in the main paper describes a different model and temperature (Sonnet 5, 0.25, unseeded sampling). “Deterministic prompting” cannot be a global statement; specify model, temperature, cache, and seed policy per experiment.
- The current `run_all.sh` configures PySR with 10,000 generations and 30 populations by default, while the main/supplement descriptions and historical experiment configs cite different budgets. Tie each published result to the exact run configuration rather than presenting one global PySR setting.

**C2/C3 disposition:** confirmed open blockers. A single authoritative method/version map is required before manuscript rewriting or additional reruns; otherwise reruns may simply generate another incompatible result family.


## 12. Code inspection round 4 — B3 attribution correction

The tracked DeFi benchmark code and main-paper source clarify the correction mechanism:

- `run_comparative_suite_benchmark_v2.py` maps the hybrid decision `"llm"` to the separate `pure_llm` result, and `"nn"`/`"nn_fallback"` to the separate `neural_network` result.
- When the hybrid reports success but its named sub-method reports failure, the code sets `decision_attribution_corrected=True`, preserves the raw status in `success_raw`, records a correction reason, and downgrades the hybrid success flag. It does **not** re-evaluate the hybrid's own formula or replace the hybrid's numeric R² with a new score.
- The main-paper source says the hybrid and Pure-LLM arms make independent LLM calls, so their formulas for a task are independent samples. It also says the original hybrid formulas were not stored and that the paired Pure-LLM checker rerun used re-sampled formulas rather than the original formulas.
- The main-paper text itself says all corrected near-perfect successes in the relevant seed route through `decision="llm"`, making the corrected count equal the Pure-LLM count by construction under this corroboration rule.

**Interpretation:** the code correction is an internal-consistency/provenance filter, not a same-formula validation of the hybrid's own LLM output. A Pure-LLM success flag from an independent LLM call cannot establish that the hybrid's independently generated formula was the same or valid. Conversely, a Pure-LLM failure does not prove the hybrid's own formula failed. The 23 cases should therefore be described as **unverifiable from the stored records**, not as confirmed hybrid formula failures or as successes rescued by the Pure-LLM arm.

**B3 disposition:** the report's requested rewrite is warranted. Keep the conservative corrected count only if it is explicitly labelled as a decision-aligned corroboration proxy, not an independently validated hybrid score. Remove “bug” as a causal label unless the paper narrows it to a bookkeeping/attribution inconsistency; remove “masked failures” and the tier-by-tier tie as a scientific performance finding. The decisive remedy remains to persist the hybrid formula, its predictions, decision provenance, and exact data split, then re-score that formula on the same split used for the hybrid result.


## 13. Nguyen-12 reconciliation — R2 resolved at the result-file level

The apparent conflict between the 51/60 aggregate and the N-12 gate-abort note is resolved: **the gate-abort statement is specific to equation N-12, not to the entire 12-equation suite.** The five seed result files independently support both statements.

### Recomputed directly from the five result JSONs

| Seed | HypatiaX recovered | PySR-only recovered | HypatiaX N-12 | PySR-only N-12 |
|---:|---:|---:|---|---|
| 42 | 10/12 | 10/12 | gate abort | passes |
| 99 | 10/12 | 9/12 | gate abort | passes |
| 123 | 11/12 | 10/12 | gate abort | passes |
| 777 | 10/12 | 12/12 | gate abort | passes |
| 2024 | 10/12 | 8/12 | gate abort | passes |
| **Total** | **51/60** | **49/60** | **0/5** | **5/5** |

The recovery criterion is `evaluation.r2_extrap >= 0.9999`, matching the manuscript's table note. The five files carry the same run configuration: 1,000 PySR iterations, 30 populations, 1,100-second timeout, LLM temperature 0.25, eight LLM candidates, LLM gate minimum R² 0.95, `llm_require_valid_guess=true`, sparse-seed mode off, run index 1.

For HypatiaX N-12 in each file:
- `llm_gate_failed=true`;
- stored expression is `FAILED`;
- `evaluation.r2_extrap` is null;
- elapsed time is approximately 10–13 microseconds, consistent with abort before PySR search.

PySR-only's N-12 result passes the 0.9999 threshold in all five files. The per-seed totals and per-equation pattern therefore agree with the main-paper table and the October PDF audit's arithmetic check.

### Exact result files inspected

- `hypatiax/data/results/extrapolation/exp3_nguyen12_seed42.json` — blob `a3c7e4e959600435c7dc385fd8f289b954a95372`
- `hypatiax/data/results/extrapolation/multi_seed/exp3_nguyen12_seed99_nshards01.json` — blob `033934812df4f471556181b5c4a7dca0d6a7fb80`
- `hypatiax/data/results/extrapolation/multi_seed/exp3_nguyen12_seed123_nshards02.json` — blob `c39b9b6c7f03deae674706ab0c42a04952c9604d`
- `hypatiax/data/results/extrapolation/multi_seed/exp3_nguyen12_seed777_nshards03.json` — blob `5a4893fb09fb9d5f4c68e28ab8c3eab98e2575f1`
- `hypatiax/data/results/extrapolation/multi_seed/exp3_nguyen12_seed2024_nshards04.json` — blob `23e151f668c01f4995f1925bcb8e99aa6801fb9a`

### Manuscript wording correction

No result rerun is required to resolve this particular ambiguity. Make the scope explicit wherever the note appears:

> Across five seeds, HypatiaX recovers 51/60 equation–seed cases versus 49/60 for PySR-only. However, HypatiaX's LLM warm-start gate aborts before search on N-12 in all five seeds, while PySR-only recovers N-12 in all five. The five-seed aggregate is descriptive and has not been tested for statistical significance.

Do not say that HypatiaX fails the entire Nguyen-12 suite. Do not imply that the 51/60 aggregate demonstrates a statistically significant advantage. The N-12 gate failure is a genuine, repeatable limitation and should remain visible.

**R2 disposition:** result-file arithmetic and the N-12-specific gate behavior are reconciled. Remaining release work is to ensure the manuscript, supplement, and provenance manifest all cite these exact five files and the same configuration.


## 14. Code inspection round 5 — C4 Core-15 source reconciliation

The October audit's C4 finding was checked against the tracked Core-15 result families and the main-paper source.

### What the manuscript actually reports

The main-paper Core-15 table says five HypatiaX far-extrapolation cells are non-finite or unavailable: Gravitational Force (`-inf`), Henderson–Hasselbalch, Logistic Growth, Michaelis–Menten, and Rate Law (`nan`). It separately reports a finite but extreme Constant Product far-`R^2` of approximately `-4.46e4`.

This is more precise than saying that five whole equations never completed: the table contains training metrics and some near/medium extrapolation metrics. The failure is specifically in the reported far-extrapolation outputs (and in some cases earlier extrapolation regimes), not necessarily in the entire task execution.

### Two tracked result families do not reproduce the manuscript table

1. `hypatiax/data/results/five_systems/exp1_five/exp1_five_results.json`
   - The accompanying provenance map dates the run to 2026-08-12, seed 42, 30 populations, 900-second method timeout, and 1,100-second PySR timeout.
   - Its runner log says all 15 equations completed for all five methods.
   - The `Hybrid v50_2` far-`R^2` values differ materially from the manuscript table. Examples: Arrhenius is `-inf`, Allometric Scaling is about `0.9707`, Logistic Growth about `0.9840`, Michaelis–Menten about `0.2415`, and Constant Product about `0.9451`; several other rows are null/non-finite.
   - This file therefore cannot be treated as the exact source for the manuscript's reported Arrhenius `0.9028`, Allometric Scaling `-0.7001`, Logistic Growth `nan`, and Constant Product `-44589.6` values.

2. `hypatiax/data/results/ablation/exp1_ablation/exp1_ablation_results.json`
   - This is a separate direct `HybridDiscoverySystem v5.4` ablation path, not the five-system `exp1_five` path. It stores the HypatiaX condition under a different schema.
   - Its per-equation far scores also differ from the manuscript table; for example Henderson–Hasselbalch and Rate Law have finite far scores, while Gravitational Force is finite and Constant Product is about `0.9996`.
   - It is not a substitute for the missing table-source artifact.

The manuscript says the table values come from an underlying `_merged.json` file, but the exact merged source matching the printed table was not located among the tracked result files inspected in this pass. The two files above must not be silently substituted for it.

### C4 disposition

**Still a submission blocker; exact source reconciliation comes before rerunning.**

Required sequence:

1. Recover the exact `_merged.json` (or the source shards and merge procedure) used to produce the printed Core-15 table. Record its path, blob SHA, generating workflow/run, commit, method implementation, seed, split, and evaluator.
2. Recompute the manuscript's Table 10 values directly from that source and verify all 15 equations, all extrapolation regimes, and the Constant Product extreme score.
3. Compare the recovered table source with both tracked result families above. Explain whether they represent different methods, versions, seeds, or splits; do not pool them.
4. Only after identifying the authoritative method and protocol, run a clean Core-15 reproduction with per-equation formulas, predictions, evaluation status, timeout status, and provenance persisted. Include the five problematic far-extrapolation cases and Constant Product.
5. If the exact historical source cannot be recovered, withdraw the table's unreproducible values and replace the Core-15 comparison with a clearly labelled new run; retain the old numbers only as historical exploratory results if their provenance can be established.

**Important interpretation:** the October audit's concern remains valid. The current repository contains different Core-15 result families, and the one that should support the manuscript table has not yet been identified. The newer v5.4 ablation's 15/15 task completion does not repair or invalidate the separate five-system table; it is a different experiment path.

### Evidence inspected

- `archive/patches/fix_out/patched/jmlr_paper_main_cleaned.tex`, Core-15 table and explanatory text (around lines 1,830–1,875).
- `hypatiax/data/results/five_systems/exp1_five/exp1_five_results.json` and `exp1_five_extrapolation.json`.
- `hypatiax/data/results/five_systems/exp1_five/provenance_map_exp1_five.json` and `exp1_five_run.log`.
- `hypatiax/data/results/ablation/exp1_ablation/exp1_ablation_results.json`.
- `hypatiax/experiments/benchmarks/exp1_ablation.py` and `exp1_five_system.py` (experiment-path distinction).


## 15. A4 follow-up — evaluator policy and CI harness correction

A second, exact comparison of the tracked Supplement B TeX and current scorer sharpens the A4 finding.

- Supplement B Section 8.4 prints an evaluator using
  `_tol = 1e-10 * max(abs(y_true))**2 * len(y_true)`, and assigns `0` when `ss_tot` is below that tolerance.
- The current `hypatiax/core/r2_canonical.py` instead sets `REL_TOL = 1e-24`, compares `ss_tot` with `REL_TOL * max(sum(y_true**2), 1e-300)`, and returns `(NaN, "degenerate_target")` for a constant or near-constant target. It returns `-inf` for non-finite predictions or a bad shape.
- The current 74-task v3c runner imports `r2_checked` from this canonical module. Thus the current principal runner no longer uses the absolute `ss_tot > 1e-10` gate described in the older Listing 8 claim, but the Supplement B printed implementation is not the current canonical policy either. Calling both simply “the relative threshold” hides a material difference in tolerance and degenerate-target semantics.
- `hypatiax/experiments/tests/conftest.py` supplies the `RECOVERY_EVAL` default. The previous note that the test was not self-contained is withdrawn. A successful workflow run #201 was found, but it was a pull-request run on `fix/rerun-blockers`, not a master run.

**A4 revised disposition:** the current v3c benchmark's use of the canonical scorer is verified. The manuscript and both supplements still need to print the exact canonical policy, including `REL_TOL=1e-24`, the relative scale definition, and NaN/`-inf` status semantics. The exact Supplement A Listing 8 source is still absent from the tracked repository, so its historical implementation cannot be compared line-for-line. Match the exact result-producing commit and evaluator to each DeFi result family before deciding whether any historical table requires rerunning.

**Required manuscript correction:** replace the Supplement B Section 8.4 pseudocode with the actual canonical implementation or a faithful concise specification. Do not retain the older `1e-10` formula or claim that below-threshold variance returns zero. Explain that near-constant targets have undefined R² and are excluded from recovery counts, while failed predictions are treated as failures.



## 16. Code inspection round 6 — B1 synthetic supplementary-material claim

The Supplement B source was checked against the current reproduction repository.

### What is established

- Supplement B contains the sentence: “All supplementary materials are provided in both synthetic versions (matching reported statistics exactly) and real experimental versions (direct from JSON logs).”
- The same section lists S1–S8 files, including per-equation results, validation logs, discovered expressions, timing data, domain analysis, failure taxonomy, and figure source CSVs.
- Exact-name repository searches in LLM-HypatiaX-REPRO found none of the listed S1–S8 artifacts.
- The supplementary source directs readers to the separate LLM-HypatiaX-DEV post-processing/pre-submission repository for processed results and tables; raw benchmark runs are said to live in this reproduction repository.
- The current v2 and PCA comparative runners explicitly log that synthetic reconstruction of missing y_pred has been disabled. The Phase 1 closure record also describes removal of the prior algebraic reconstruction path. Synthetic fixtures used to test audit scripts are separately identified as fixtures, not experimental observations.

### What cannot yet be certified

- The reproduction repository contains a binary hypatiax/data/results.zip; its contents were not inspectable through the text-only repository-file interface in this pass.
- The separate LLM-HypatiaX-DEV repository was not inspected here. The current repository therefore does not establish whether synthetic S1–S8 variants exist there, whether they were used in any manuscript table/figure, or whether they are included in the intended release bundle.
- Absence of the named S1–S8 files from the searchable text tree is not proof that no such files exist inside the binary archive or the separate DEV repository.

### B1 disposition

**The sentence should be removed from the journal supplement now.** It is ambiguous about whether “synthetic versions” are simulated data, fabricated table replicas, or test fixtures, and “matching reported statistics exactly” is particularly damaging to reviewer confidence.

Before release, inspect results.zip and the actual DEV/release bundle; inventory every synthetic or fixture file; trace every table and figure to its source; and record whether any synthetic data entered reported results. If synthetic fixtures are retained for software tests, place them in a clearly labelled test-fixture directory and state that they are not used in reported experiments. Do not claim that no synthetic material ships until the binary archive and intended release bundle have been checked.


### DEV-repository cross-check

The supplementary source points to the public repository sednabcn/LLM-HypatiaX-DEV; its master branch was inspected as well.

- Exact-name searches in DEV also found none of the listed S1–S8 data files. DEV's audit_report.md specifically records S3_validation_logs.json as a missing path.
- DEV's paper/post_submission_report.tex states that synthetic records were used for table-generator layout/regression testing only and that no synthetic value entered the paper. This is useful corroboration for the generator-test fixtures, but it does not explain the separate supplement sentence claiming that full synthetic and real S1–S8 material is provided.
- DEV contains the source PDFs and TeX files, generated paper tables, and a 4.4 MB submission archive at submissions/HypatiaX_JMLR_submission.zip (blob SHA fd8ec1eb6b7dbaaf5afcba70bcb179a5e2a4dd8c). The archive is binary and its contents were not inspected in this pass.

**Updated B1 assessment:** the evidence now supports that synthetic records were used for generator regression tests and that the post-submission audit says no synthetic value entered the paper. The S1–S8 files advertised by the supplement are nevertheless absent from both searchable repository trees, and the actual submission ZIP remains uninspected. Remove the ambiguous sentence, then inspect the ZIP before making a definitive statement about what ships. Do not label the paper's numerical results synthetic on the basis of test fixtures alone.


## 17. Code-package readiness decision — rerun before rewriting claims

This is a separate decision from manuscript submission readiness. The package is assessed as a research execution system, not as evidence that any historical paper claim is correct.

### Decision

**READY FOR A CONTROLLED, INSTRUMENTED RERUN**

The strongest current candidate is the tested code state at commit `f4336f14b224820690f119e50c09dac8e64e3b7c` on branch `fix/rerun-blockers`. It is **not** the current `master` checkout. Do not cite the test results below as validation of master until the candidate is promoted or its changes are reconciled and the checks rerun on the promoted SHA.

### Evidence supporting rerun readiness

All checks below completed successfully on the same candidate SHA, 2026-11-08:

| Gate | Evidence | Result |
|---|---|---|
| Full Python test suite | 593 tests, Python 3.12, torch CPU, Anthropic SDK, SymPy | PASS |
| Shell/YAML preflight | runner syntax and workflow validation | PASS |
| run_all smoke | shell syntax, step registry, required files, failure ledger, dry-run-all, CLI contract, clean-run guards, ground-truth leak guard, Python preflight, Phase 2 closure | PASS |
| Bypass audit | 103 DeFi tasks and 30 Feynman tasks; 0 bypasses in either suite | PASS for invariant I1 only |
| Exp3 strict/fallback smoke | N5, N9, N10, N11, N12 at seed 42; strict/fallback paths exercised | PASS; fallback recovers four strict-gate failures, N11 passes both |
| R² policy / metrics / recovery evaluator | dedicated policy workflow | PASS |

Workflow evidence:
- Full tests: https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/42492526303 (593 passed in 13.29 s; artifact 13622600671).
- Bypass audit: https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/42492526662 (103 DeFi + 30 Feynman, 0 bypass; artifact 13622202617).
- Runner smoke: https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/42492526468 (10 wiring/guard stages passed; script-help and live-LLM stages intentionally skipped; artifact 13622455851).
- Exp3 gate smoke: https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/42492526298 (five named Nguyen tasks; smoke settings, not production budgets).
- R² policy: https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/42492526472.

The bypass-audit workflow explicitly reports that no baseline CSV was available; it therefore checked only invariant I1. Its pass must not be represented as a complete comparison against a historical baseline. The smoke workflows validate wiring and selected control paths, not full benchmark performance.

### Scope of the declaration

The package is ready to start a controlled rerun under the tested CI environment and clean-run safeguards. This does **not** mean:
- the full DeFi, Core-15, Nguyen-12, Protocol-30, noise, instability, or Feynman experiment matrix has been rerun;
- the historical result files have passed the new provenance gate;
- all bypass or fallback questions are closed;
- the package is already a frozen, portable release;
- any prior manuscript table or claim has been validated.

### Promotion and environment controls before the first headline rerun

1. **Promote one exact source revision.** PR #95 currently targets `audit-main`, not `master`; PR #92 is separately open to bring the runner-smoke pipeline from `audit-main` into `master`. These branches have substantial divergence. Do not merge either branch wholesale without a deliberate three-way reconciliation. The tested SHA must be the SHA actually used for the rerun.
2. **Freeze the Python environment.** The package metadata says Python `>=3.8`, while the verified CI test environment is Python 3.12 and the pinned requirements include dependencies that may not support 3.8. The experiment workflow installs a different dependency set from `requirements.txt` (for example, it pins pandas 2.2.3 while requirements pins pandas 2.3.3, and leaves several core packages unpinned). Produce one authoritative lock/constraints file and use it in both local setup and CI. Until then, the verified environment is Python 3.12 in the workflow, not a generic Python 3.8+ install.
3. **Freeze Julia/PySR.** The experiment workflow uses Julia 1.11 and `pysr==2.0.0a1`, but the Julia `SymbolicRegression.jl` environment is installed/precompiled dynamically. Record the resolved Julia package version/manifest and runtime platform in each result manifest.
4. **Run a real live-LLM preflight.** The run_all smoke deliberately skipped the live API round-trip. Before any headline rerun, perform one explicitly budgeted live call using the intended model ID, temperature behavior, retries, and provenance fields. Store the provider/model identifiers and whether a request was actually sent; never store credentials.
5. **Use a clean output namespace.** New runs must write to a fresh, commit-tagged results directory. Do not resume from old checkpoints or mix historical result shards. Keep `HYPATIAX_DISABLE_HARDCODED=1`, `HYPATIAX_DISABLE_PROMPT_HINTS=1`, `HYPATIAX_R2_SIGN_FLIP=0`, and strict exception handling enabled. Preserve the exact seeds, split indices/fingerprints, timeout budgets, route decisions, formula strings, and per-task failures.
6. **Run a staged reproduction, not the whole suite at once.** First run one representative task per method/route with full provenance; then the Core-15 and Nguyen-12 targeted reruns; then the 74-task DeFi suite; then the benchmark-specific noise/sample-complexity and Feynman/Protocol-30 suites. Apply the same frozen protocol to all arms being compared.
7. **Qualify artifacts before analysis.** Every task must have an explicit status (success, failure, timeout, skipped/intractable), source/model provenance, formula/prediction artifact where applicable, evaluator version, and input/split fingerprint. A missing formula or unknown LLM source is an audit failure, not an inferred success.

### Recommended claim-writing rule

Do not revise the manuscript by trying to make old claims fit old tables. Freeze the rerun protocol first; execute it; compute all metrics from the new raw outputs; then write a new claim set from those results. Retain historical numbers only when they are explicitly labelled as historical and their provenance is recoverable. The manuscript should not determine the rerun outcome or the thresholds after seeing the data.

**Final code-package judgment:** HypatiaX is ready for a controlled rerun on the tested candidate revision, subject to source promotion/reconciliation and the environment/live-call controls above. It is not yet a fully frozen release and the current master branch is not certified by the candidate-branch test results.


## 18. Promotion-path audit — no wholesale merge approved

A fresh GitHub compare was performed before changing any source branch. The results confirm that the tested rerun candidate cannot safely be promoted by merging either existing long-lived branch wholesale.

### Current graph facts

- `master...audit-main`: diverged; `audit-main` is 102 commits ahead and 167 commits behind `master`, with 175 changed paths in the comparison.
- `master...fix/rerun-blockers`: diverged; candidate is 131 commits ahead and 167 commits behind `master`, with 211 changed paths.
- `audit-main...fix/rerun-blockers`: diverged; candidate is 30 commits ahead and 1 commit behind `audit-main`, with 88 changed paths.
- The tested candidate remains exact SHA `f4336f14b224820690f119e50c09dac8e64e3b7c`. The earlier successful CI evidence applies to this SHA only.

### What the diff says

The candidate includes genuine rerun-relevant code and tests: unified LLM-call wrapper, hybrid/Pure-LLM path changes, checkpoint-clearing behavior, provenance/bypass tests, protocol/runner changes, and runner workflows. However, the branch comparisons also include many historical experiment outputs, checkpoints, logs, audit artifacts, manuscript-adjacent files, and unrelated workflow changes. The compare API reports many generated/result paths with zero text-line changes because these are structured/binary or metadata changes; they still count as changed paths and must not be treated as harmless.

The candidate workflow also carries a broad experiment-dispatch surface and CI behavior, including automatic commits/pushes of generated baseline artifacts. Those behaviors need an explicit review before a production rerun is dispatched. The candidate is therefore a valid tested source snapshot, not a clean promotion patch.

### Promotion decision

**Do not merge PR #95 or PR #92 wholesale into `master`. Do not retarget PR #95 directly to `master`. Do not move `master` to the candidate SHA.**

The safe path is a new promotion branch based on the current `master` head, followed by a selective, file-level port of only the code, tests, and minimal CI wiring required for the rerun. Exclude committed result/checkpoint/log trees and unrelated paper/audit changes. Preserve the candidate SHA and its CI run links as the evidence baseline. Then:

1. Create a promotion branch from the current `master` SHA.
2. Port the minimum code/test set from the candidate, reviewing each file against both current `master` and the tested candidate.
3. Add only the required runner smoke/preflight workflow wiring; remove or disable automatic result/baseline commits unless explicitly required and reviewed.
4. Resolve dependency/lockfile and Julia/PySR environment pinning on that branch.
5. Run the full tests, runner smoke, bypass audit with its baseline limitation addressed, Exp3 smoke, and R² policy checks on the promotion branch's resulting SHA.
6. Run the live-LLM preflight and verify a fresh output namespace before launching the full staged experiment matrix.

The current branch graph and the 30-commit delta between `audit-main` and the tested candidate suggest the promotion work should be a deliberate patch port, not a merge operation. No source branch was modified and `master` remains untouched by this promotion audit.

**Updated decision:** the candidate is still approved for a controlled rerun as an isolated tested snapshot. A rerun from `master` or from a newly promoted branch is not approved until that exact resulting SHA passes the required checks.
