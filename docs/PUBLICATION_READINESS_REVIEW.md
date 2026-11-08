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

**Test-harness issue found:** `test_recovery_evaluator.py` requires the environment variable `RECOVERY_EVAL=module:function`; without it, its tests deliberately fail. The tracked `.github/workflows/ci_r2_policy.yml` invokes that test file but does not set `RECOVERY_EVAL`. Unless a separate runner-level environment injection exists (not established by the workflow source), this CI step is not self-contained. Set the variable to the intended canonical function or change the test to import the canonical scorer directly, then verify the workflow run. Do not describe this gate as passing until the actual run is checked.

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
