# LLM-specific training-only degradation-tau calibration protocol

**Status: protocol specification only — not executed.**  
**Policy state: `degradation_tau: null`; pure-LLM routing remains fail-closed.**  
**Cost boundary: no LLM/provider calls, paid calibration, or workflow dispatch is authorized by this document.**

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

**Planning floor (proposed, not yet approved):** target at least 100 equations in the calibration cohort and 100 in the independent evaluation cohort, with at least 30 per reported primary difficulty stratum where the catalogue permits. If the available catalogue cannot meet these counts, report the shortfall and treat the study as exploratory; do not relax criteria after seeing outcomes. A formal power/precision analysis should be completed against the expected bad-route prevalence before committing spend.

## 4. Predeclared formula-quality and bad-route definitions

A degradation threshold is meaningful only among formulas that are usable on the core partition. Define two outcomes separately:

- **Formula-generation/execution coverage:** proportion of all assigned equations for which a formula is generated and both core and edge predictions are valid under the frozen evaluator.
- **Bad accepted route:** an equation that the proposed pure-LLM rule would accept but whose frozen formula fails the predeclared edge-quality criteria.

Before any generation, the study owner must ratify and record numeric cutoffs for:

- minimum acceptable core fit (R² and/or core-scale NRMSE);
- minimum acceptable edge fit (R² and/or core-scale NRMSE);
- maximum acceptable edge error increase;
- maximum acceptable bad-route risk and confidence level;
- minimum overall and per-stratum coverage.

Do not infer these cutoffs from the observed calibration distribution. The existing routing values `pure_llm_train_r2_min = 0.95` and `trust_gate_r2_min = 0.5` are current policy settings, not evidence that a particular edge-fit cutoff is scientifically acceptable.

**Operational recommendation for the risk constraint:** define the maximum tolerated bad-route probability as a policy-level target (for example, 10%) and require a one-sided 95% upper confidence bound to remain below it. The 10% value is a proposal for explicit owner approval, not an approved scientific fact. The edge-quality definition and risk target must be frozen together.

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

**Go** only if the independently evaluated bad-route upper confidence bound satisfies the ratified risk target, coverage meets its predeclared minimum overall and in required strata, and no predeclared integrity or leakage check fails.

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

## 8. Preflight checklist and authorization boundary

A future run is blocked until all of the following are true:

- [ ] Numeric core-fit, edge-fit, error-increase, risk, and coverage criteria are ratified and versioned.
- [ ] Calibration and independent evaluation equation manifests are frozen and disjoint.
- [ ] Sample-size/precision analysis is approved.
- [ ] Prompt/template and model/provider settings are frozen.
- [ ] Edge data isolation is tested (generation input contains no edge rows or labels).
- [ ] The evaluator and artifact schema pass offline tests.
- [ ] A cost estimate and explicit authorization for any paid LLM/provider calls are obtained.
- [ ] The run uses a new output directory and does not overwrite historical artifacts or the protected baseline.

This document does not authorize any provider calls or workflow dispatch. Until a separate explicit approval is given and the preflight is complete, do not run calibration, do not spend API credits, and do not modify routing configuration. Keep `config/fresh_rerun.yaml` at `degradation_tau: null`.

## 9. Relationship to existing diagnostics

The existing NN-derived `_extrapolation_probe` remains a separate NN robustness diagnostic. Its delta must not be substituted for `delta_llm`. The LLM-specific formula diagnostic API now provides categorized parse/execution/output failures while preserving the legacy evaluator contract; use that API for all future calibration scoring.

The replayed 74-case artifact remains a historical audit input only. Its 47 exact replay matches establish reproducibility of those saved scores, not that the formula cohort is suitable for threshold calibration.
