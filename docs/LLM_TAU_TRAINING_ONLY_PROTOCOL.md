# LLM-specific training-only degradation-tau calibration protocol

**Status: repository-approved risk constants aligned; operational calibration manifest remains incomplete and no run is authorized by this specification alone.**  
**Policy state: `degradation_tau: null`; pure-LLM routing remains fail-closed.**  
**Cost boundary: no LLM/provider calls, paid calibration, or workflow dispatch is authorized by this document.**

The numeric risk constants below are read from the repository's existing `config/tau_calibration_manifest.json` validator and are the repository's approved constants. They supersede the provisional 10%/95%-Bonferroni proposal in an earlier revision of this document. They are not empirical guarantees. The equation/category manifest, candidate thresholds, bad-route evaluator, and provenance must still be completed and validated before a run.

## 1. Purpose and estimand

The routing gate is intended to assess whether a generated LLM formula remains reliable outside the central training region. Its calibration statistic must therefore measure the **LLM formula itself**, not the existing NN extrapolation probe.

For each equation, generate and freeze one formula using only the central training subset. Then evaluate that exact frozen formula independently on:

- the central/core subset; and
- the withheld edge subset, consisting of the predeclared low- and high-tail regions.

Primary degradation statistic:

`delta_llm = R2_core - R2_edge`

Larger positive values indicate a greater decline in edge R². Retain the sign and all finite values; do not clip or winsorize.

R² is not sufficient by itself. Also report core-scale normalized RMSE on both partitions and:

`delta_nrmse = NRMSE_edge_core_scale - NRMSE_core_core_scale`

where both RMSE values are divided by the standard deviation of the core target. This common scale makes error changes more interpretable when core and edge target variances differ.

## 2. Leakage controls and per-equation procedure

1. Freeze the equation catalogue, cohort assignment, random seeds, feature/target definitions, edge-split algorithm, and split parameters before generation.
2. Create the core/edge split using training covariates only. Persist exact row indices and hashes of the ordered core and edge inputs/targets.
3. **Withhold all edge rows and edge labels from formula generation, prompt construction, model selection, constant estimation, and any fitting or repair step.** The formula-generation process receives only the core training data and the equation specification that is legitimately available at deployment.
4. Generate the formula once, record the exact prompt/template version, provider/model identifier, request parameters, response, timestamp, and provenance. Do not regenerate a formula because its edge score is poor.
5. Freeze the formula and constants. Run the restricted formula interpreter on core and edge separately. No parameter fitting, expression rewriting, or constant recalibration is allowed after edge data are revealed.
6. Score both partitions with the same metric implementation. Record R², MAE, RMSE, core-scale NRMSE, target standard deviations/ranges, prediction ranges, execution mode, non-finite repair fraction, and all failure diagnostics.
7. Only after the formula and its metadata are immutable may the evaluator reveal edge labels and calculate edge metrics.

The edge covariates may be used by the evaluator to produce predictions after formula freeze. They must not be included in generation prompts or any pre-freeze formula-selection process.

## 3. Cohorts and unit of analysis

- **Unit of analysis:** one equation, not one row, prompt retry, or individual prediction.
- **Calibration cohort:** a fixed, versioned set of equations used to select the threshold.
- **Independent evaluation cohort:** distinct equations not used for threshold selection, with a separately locked manifest. Where practical, include a distinct seed/domain slice to test transportability.
- Keep all equations assigned to their cohort before any generation begins. No moving equations between cohorts after observing outcomes.
- Report results by overall cohort and by predeclared difficulty/domain strata. Do not let a large easy stratum conceal a small but high-risk stratum.
- A failed generation, parse, execution, shape check, or metric computation remains in the denominator for coverage and failure-rate reporting. It is not silently dropped from the risk accounting.

The previous 44/30 split is too small and its saved artifact is already inspected; it must not be recycled as a fresh untouched calibration/evaluation split.

**Repository-approved planning floor:** at least 59 independent equation/family units in every declared calibration category, even in the zero-failure case. This follows the exact one-sided binomial requirement for tolerated bad-route probability ε = 0.05 and family-wise error δ = 0.05: `ceil(log(0.05) / log(1 - 0.05)) = 59`. Repeated seeds, noise levels, prompts, or reruns of one equation do not create independent units. The independent evaluation cohort must be a separately locked set of distinct equation/family units; its required size and precision target must be specified in the run manifest before any generation. Do not treat the existing 44/30 split as satisfying the per-category calibration minimum.

## 4. Predeclared formula-quality and bad-route definitions

A degradation threshold is meaningful only among formulas that are usable on the core partition. Define two outcomes separately:

- **Formula-generation/execution coverage:** proportion of all assigned equations for which a formula is generated and both core and edge predictions are valid under the frozen evaluator.
- **Bad accepted route:** an equation that the proposed pure-LLM rule would accept but whose frozen formula fails the predeclared edge-quality criteria.

The following constants are fixed in `scripts/validate_tau_calibration_manifest.py` and `config/tau_calibration_manifest.json`:

| Criterion | Repository-approved value |
|---|---:|
| Minimum edge R² | 0.99 |
| Minimum relative margin against ensemble | 0.00 |
| Maximum tolerated bad-route probability (ε) | 5% |
| Family-wise error rate (δ) | 5% |
| Confidence level | One-sided 95% |
| Minimum independent units per calibration category if zero failures | 59 |

The manifest defines the edge region as the upper 20% of training rows ordered by projection onto the first PCA direction. The exact edge construction and evaluator must be frozen and hash-pinned before calibration. The bad-route rule must implement both the absolute edge R² floor and the comparison against the ensemble using the manifest's `relative_margin_against_ensemble` definition. Missing/invalid scores fail closed and are never treated as successful routes.

Threshold selection must use the manifest's **fixed-sequence exact binomial** procedure, testing candidates from strictest to laxest at family-wise `δ = 0.05` against `ε = 0.05`. Stop at the first candidate that is not certified; select the last candidate that passed. If none passes, keep `tau = null`. Candidate tau values must be finite, non-negative, unique, and declared in strictly increasing order before outcomes are examined. The validator requires a non-empty candidate list and a minimum of 59 independent units in every declared category even in the zero-failure case.

These constants are not inferred from the 74-case replay or the earlier calibration distribution. The validator is authoritative for the constants and sample-size calculation. Do not substitute the provisional core/edge NRMSE cutoffs, 10% risk target, Bonferroni grid, or 100-per-cohort proposal from the superseded draft.
A formula that is poor on core and edge is a formula-quality failure, not a useful positive or negative degradation observation. Preserve its metrics, count it against coverage, and do not use its delta to justify accepting the route. Undefined scores and generation failures also count against coverage and are never treated as safe.

## 5. Threshold selection on calibration only

1. Apply the already-frozen core trust gate and formula-quality eligibility criteria.
2. For each candidate `tau`, define the accepted set exactly as production routing will: eligible formula, all existing structural-risk checks passed, and `delta_llm <= tau`.
3. Define the bad-route indicator using the ratified edge-quality criteria. Report accepted count, accepted coverage, bad-route count/rate, and uncertainty.
4. Select the **largest** candidate `tau` whose predeclared risk constraint is met, thereby maximizing coverage subject to the risk limit. If no candidate meets the constraint, select no threshold and retain `tau = null`.
5. Because the threshold is selected adaptively from calibration data, use a predeclared simultaneous one-sided confidence procedure over the complete candidate-threshold set (or an equivalently conservative nested equation-level resampling procedure). Do not report an ordinary pointwise interval as if the threshold had been fixed in advance.
6. Freeze the selected threshold, cohort manifest, code commit, evaluator version, and protocol version before opening the independent evaluation results.

Do not optimize the threshold against aggregate benchmark test R², the held-out evaluation cohort, or a desired pure-LLM route percentage. Do not change the threshold after seeing evaluation results.

## 6. Independent evaluation and go/no-go

Apply the frozen threshold and all frozen gates unchanged to the independent evaluation cohort. Report:

- assigned equations, formula-generation coverage, valid-scoring coverage, and abstention/failure counts;
- accepted-route count and coverage;
- bad accepted routes and the one-sided confidence bound;
- core and edge fit distributions, `delta_llm`, and `delta_nrmse`;
- generation/execution failure reasons;
- domain and difficulty slices;
- confidence intervals using equations as the resampling unit;
- exact manifests, hashes, prompts/templates, model/provider provenance, and code/config versions.

**Go** only if the independent evaluation cohort satisfies its predeclared sample-size/precision requirements, the one-sided 95% bad-route upper confidence bound is below the 5% risk target, all predeclared integrity/leakage checks pass, and the frozen policy's coverage is reported against predeclared minima. Evaluation uses the single frozen tau selected on calibration; do not retune it on evaluation.

**No-go** if any condition fails, if sample counts are inadequate, if confidence bounds are too wide, or if a required stratum is underpowered. A no-go leaves `tau = null` and the fail-closed ensemble route unchanged. Do not repair the result by dropping difficult equations, changing cutoffs, or recalibrating on the evaluation cohort.

## 7. Required artifact schema

Each equation record should include at least:

- protocol/version, equation ID, cohort, difficulty/domain, seed;
- ordered core/edge indices, split parameters, row counts, and input/target hashes;
- prompt/template version, model/provider provenance, generation timestamp, response hash, and whether a provider call occurred;
- frozen formula text/hash and constants/hash;
- core and edge execution status, failure reason, execution mode, output shape, non-finite fraction, and diagnostic detail;
- core/edge R², MAE, RMSE, target scale/range, prediction scale/range, core-scale NRMSE, `delta_llm`, and `delta_nrmse`;
- quality eligibility, bad-route label, threshold decision, and route reason;
- calibration manifest ID, selected threshold (if any), confidence procedure/version, and evaluator commit.

Never store API keys, credentials, or other secrets in artifacts.

## 8. Cohort feasibility and evaluation precision

The offline repository inventory is recorded in [LLM tau calibration cohort feasibility audit](LLM_TAU_COHORT_FEASIBILITY_AUDIT.md). It found no currently available, unused, provenance-pinned registry large enough to satisfy the approved independent-unit requirements. Do not populate the manifest by combining registry row counts without canonical equation-family adjudication, and do not reuse the historical 74-case calibration cohort.

The exact zero-failure sample minimum of 59 applies to the calibration category and, for an independent evaluation claim at the same 5% risk target and one-sided 95% confidence, to the number of **accepted/evaluable independent evaluation units per category**. Assigned evaluation equations must be increased to account for abstentions, invalid formulas, generation failures, and undefined scores. If there are bad accepted routes, compute the exact one-sided bound using the observed failures; 59 is not sufficient in that case. The evaluation manifest must be disjoint from calibration, Core-15, and all families in the historical 74-case LLM calibration artifact.

A future evaluation validator must enforce this accepted-route precision requirement as well as manifest disjointness. A calibration manifest passing `--require-ready` alone does not establish evaluation readiness.

## 9. Preflight checklist and authorization boundary

A future run is blocked until all of the following are true:

- [x] Repository-approved edge-fit, relative-margin, risk, confidence, and minimum calibration sample-size constants are pinned to the validator/manifest.
- [ ] Candidate tau values, category list, independent equation/family IDs, source/formula/training-data hashes, edge evaluator, and calibration data-manifest hash are populated and pass `scripts/validate_tau_calibration_manifest.py --require-ready`.
- [ ] Independent evaluation cohort is disjoint from calibration, Core-15, and the historical 74-case cohort; its accepted-route precision plan is frozen and validated.
- [ ] Calibration and independent evaluation equation manifests are frozen and disjoint.
- [ ] Sample-size/precision analysis is approved.
- [ ] Prompt/template and model/provider settings are frozen.
- [ ] Edge data isolation is tested (generation input contains no edge rows or labels).
- [ ] The evaluator and artifact schema pass offline tests.
- [ ] A cost estimate and explicit authorization for any paid LLM/provider calls are obtained.
- [ ] The run uses a new output directory and does not overwrite historical artifacts or the protected baseline.

This document does not authorize any provider calls or workflow dispatch. Until the manifest passes `--require-ready`, the independent evaluation design is frozen, and the run-specific cost/call cap is explicitly approved, do not run calibration, do not spend API credits, and do not modify routing configuration. Keep `config/fresh_rerun.yaml` at `degradation_tau: null`.

## 10. Relationship to existing diagnostics

The existing NN-derived `_extrapolation_probe` remains a separate NN robustness diagnostic. Its delta must not be substituted for `delta_llm`. The LLM-specific formula diagnostic API now provides categorized parse/execution/output failures while preserving the legacy evaluator contract; use that API for all future calibration scoring.

The replayed 74-case artifact remains a historical audit input only. Its 47 exact replay matches establish reproducibility of those saved scores, not that the formula cohort is suitable for threshold calibration.
