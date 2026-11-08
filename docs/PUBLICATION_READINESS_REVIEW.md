# HypatiaX publication-readiness review

**Review date:** 2026-11-08  
**Repository:** `sednabcn/LLM-HypatiaX-REPRO`, reviewed from `master`  
**Status:** preliminary audit; **not yet cleared for submission**

## Executive assessment

The repository contains substantial experiments, a maintained reproducibility pipeline, and a manuscript that already acknowledges important negative findings. The current evidence supports a balanced paper about a hybrid symbolic/neural system with task-dependent strengths and material limitations. It does not support a broad claim that the hybrid consistently outperforms its baselines or that routing eliminates catastrophic failures.

The immediate risk is not a need for more experiments. It is **manuscript and evidence reconciliation**: the main-paper source is only present under `archive/`, its referenced bibliography and several named figure assets are absent from the current tree, and the main-paper abstract conflicts with a supplementary statement about Nguyen-12. The Phase 2 report also retains open items. Resolve these before submission.

This is a preliminary repository-level review, not a line-by-line audit of every result file or final scientific sign-off.

## 1. What is already in place

- `README.md` documents experiment and CI entry points.
- `ci_runner_repro.yml` dispatches experiments; `ci_pipeline_check.yml` provides completion and qualification checks.
- Main-paper and supplementary TeX sources exist under `archive/patches/fix_out/patched/`.
- Result families cover DeFi, Core-15, Protocol-30, Nguyen-12, ablations, noise/sample-complexity, and portfolio audits.
- The portfolio PCA/random-holdout case now has a clear publication boundary and route-specific metrics. Further portfolio investigations are future work, not blockers for that case.
- The main-paper source acknowledges that corrected DeFi near-perfect recovery ties the Pure-LLM baseline, catastrophic failures remain, and runtime is higher than the neural baseline.
- A historical provenance audit exists at `archive/audit/audit_out/`. Its summary reports 52 contaminated, 196 no-provenance, and 6 unreadable unique files in its historical scope. This is a warning, **not a current classification of every result on master**; rerun it against the exact evidence selected for submission.

## 2. Submission blockers

### B1 — Establish one authoritative manuscript package

The only main-paper source found is `archive/patches/fix_out/patched/jmlr_paper_main_cleaned.tex`; the supplementary source is `archive/patches/fix_out/patched/supp_benchmark_report_cleaned.tex`. There is no obvious active manuscript directory under `docs/` or at repository root.

The main TeX calls `\\bibliography{references}`, but the current repository tree contains no `.bib` file. It also references figure assets including `hypatiax_three_systems`, `hypatiax_algorithm1_routing_cascade_v2`, `fig1_seed_sweep`, and `fig18_r2_heatmap_improved`; none of those assets was found in the current tree.

**Required:** establish the authoritative submission source directory; restore/include the exact bibliography, figure assets, style files, and supplementary sources; document a reproducible clean-build command. Do not submit from an ambiguously archived source.

### B2 — Reconcile Nguyen-12 claims

The main-paper abstract reports 51/60 HypatiaX versus 49/60 PySR-only over five seeds. The supplementary report's cross-reference note says HypatiaX fails Nguyen-12 on all five seeds because the LLM gate rejects all candidates and the run aborts before search.

Those statements cannot both describe the same run, method configuration, and success definition without further qualification.

**Required:** trace both statements to exact result files, workflow/run provenance, commit, model version, and score threshold. Correct the stale statement or explain precisely why the evaluations differ. Hold the Nguyen-12 five-seed headline claim until reconciled.

### B3 — Reconcile Phase 2 status with paper claims

`docs/phase2_report.tex` says the PySR-only versus HDS comparison is closed with caveats, but the Pure-LLM comparison specified by Option 3 was not run. Its open-items list still calls for prompt matching, sampling/retry decisions, a dry run, and the full Pure-LLM run. It also lists manual Supplement A Listing 8 verification and confirmation of whether runtime includes LLM time and retries.

**Required:** remove claims that depend on the unrun comparison, or complete and close those items with evidence. Do not present a planned comparison as completed.

### B4 — Run a current, scoped provenance audit

The historical audit is not enough for a submission decision. The repository has multiple generations of outputs, rescued shard files, checkpoints, exploratory/pre-fix results, and consolidated results.

**Required:** define the exact submission evidence set, then rerun provenance checks on that set. For every headline table/figure, record source path, run ID, commit SHA, experiment configuration, split protocol, seed, metric definition, and bypass/cache/fallback flags. Exclude or label pre-fix, exploratory, duplicate, rescued, and unverified files.

### B5 — Build and inspect the complete paper package

The current tree does not contain the referenced bibliography or the named figure assets, and no complete self-contained submission bundle was established.

**Required:** verify every `\\input`, `\\include`, bibliography, figure, table, and supplementary cross-reference from the authoritative source directory; compile from a clean checkout and inspect the PDF. Record compiler, style/package dependencies, and build output.

## 3. Scientific claims supportable with careful wording

| Topic | Evidence visible in the repository | Wording boundary |
|---|---|---|
| DeFi 74-task benchmark | Main-paper source documents corrected attribution: 44/74 (59.5%) near-perfect, tying Pure LLM; five catastrophic failures remain. | Present as task-specific. Do not claim aggregate hybrid superiority or elimination of catastrophic failures. |
| Core-15 comparison | Stored Mann–Whitney result reports no significant far-extrapolation advantage (p=0.2175; n=13); two equations excluded for non-finite/missing scores. | Report non-significance and exclusions; avoid superiority claims. |
| Nguyen-12 | Abstract says 51/60 vs 49/60, but supplementary text contradicts it. | Hold headline claim pending B2. |
| Protocol-30 | A custom 30-equation set, not a subset of the standard AI Feynman 100-equation suite. Supplementary notes report 11 Pure-LLM bypass rows in one noiseless run. | Label as custom; disclose bypass/hardcoded/fitted rows and distinguish method-reported from held-out scores. Avoid direct SOTA equivalence. |
| Portfolio PCA case | Five LLM-formula seed runs on one fixed transductive partition; five random-holdout NN partitions; direct NN tail test is poor. | Use the committed portfolio publication boundary. Do not conflate formula R² with NN R² or generalize from one case. |
| Runtime | Main-paper source describes a mechanical timing audit and reports hybrid slower than neural baseline. | Keep scope and routed subset explicit; verify inclusion of LLM calls, retries, and overhead. |
| Ablations/instability | Results exist, but older provenance audit flagged broad historical result areas and supplementary source retains verification notes. | Include only after source/run/configuration/scoring checks. |

## 4. Post-investigation work — not automatic blockers

1. More genuinely multivariate portfolio cases and non-transductive PCA/tail protocols.
2. Broader NN extrapolation methods and additional bootstrap sensitivity work.
3. Expanded cross-domain experiments beyond the current case catalogue.
4. Additional ablations not needed to substantiate bounded manuscript claims.

Do not hold the paper for these investigations if the manuscript accurately states the limits of existing evidence.

## 5. Recommended close-out sequence

1. **Freeze the submission claim set:** map every abstract/contribution claim to its exact table, figure, and result artifact.
2. **Resolve B1–B3:** establish the active manuscript package and reconcile Nguyen-12 and Phase 2 statements.
3. **Run B4:** audit only selected submission artifacts and produce a provenance manifest with pass/fail/hold status.
4. **Run B5:** build the paper and supplement from a clean checkout; verify all assets and references.
5. **Editorial pass:** check terminology, split protocols, thresholds, seeds, sample units, baseline names, negative results, bypass disclosures, and limitations.
6. **Submission freeze:** tag the exact commit and archive the built PDF plus source/evidence manifest.

## 6. Current decision

**Not yet submission-cleared.** The immediate work is source/package integrity and reconciliation of existing claims, not another experiment. The portfolio case can remain frozen at its current publication boundary. No new portfolio investigation is required to proceed with this review.

---

## Evidence inspected

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
