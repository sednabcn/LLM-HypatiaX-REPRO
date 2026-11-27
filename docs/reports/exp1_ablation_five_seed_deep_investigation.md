# Exp1 Core-15: five-seed deep performance investigation

**Status:** completed retrospective analysis; no benchmark was launched  
**Data commit:** [11ee474](https://github.com/sednabcn/LLM-HypatiaX-REPRO/commit/11ee474)  
**Parent workflow:** [run 45915400809](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/45915400809)  
**Source benchmark revision recorded in results:** `1bb4c9d7ccf4813b10014fc85a67b4a28d8f18c4`  
**Benchmark script SHA-256:** `5a5eae79a57eeee3d0fcfd01f2dcf48fb2bfe5c924560db1a278891fa0d70`

## Executive finding

The five-seed run confirms strong typical in-distribution performance, but it does **not** establish that HypatiaX is more accurate or more robust than PySR. The more important finding is a repeatable extrapolation failure pattern: HypatiaX and HypatiaX-noLLM both have catastrophic far-OOD results on **all five Arrhenius seeds and all five Impermanent Loss seeds**, plus one Ideal Gas Law seed. These eleven cases per hybrid arm are represented as null in the headline far-OOD field while the raw values remain in the JSON. Additional finite but very poor far-OOD scores occur for Kinetic Energy, Gravitational Force, Logistic Growth and Michaelis-Menten.

The expression-level evidence points to a discovery/selection problem, not simply a numerical-reporting issue. Several selected expressions approximate the training/test domain but have the wrong functional form, omit required variables, or introduce high powers, nested exponentials, logarithms or variable exponents that become unstable outside the sampled range.

The LLM ablation is also weaker than a simple “LLM helps” narrative: HypatiaX and noLLM select the exact same final expression in 34/75 matched equation-seed cases; their test R² values are identical to numerical tolerance in 37/75 cases. Enabling the LLM does not reliably repair the extrapolation failures.

## 1. Dataset, protocol and integrity

The parent workflow completed five child runs for seeds **42, 99, 123, 777 and 2024**. The gatherer validated 15 equation families and three arms per seed, giving 75 equation-seed units and 225 arm records.

| Item | Verified value |
|---|---:|
| Equation families | 15 |
| Seeds | 5 |
| Equation-seed units | 75 |
| Arms | 3 |
| Arm records | 225 |
| Completed/successful primary records | 225/225 |
| Symbolic engine | 5.4 |
| PySR populations | 30 |
| Iterations | 1,000 |
| LLM model recorded | claude-sonnet-4-6 |
| Primary test scope | untouched outer test |

The 75 equation-seed units are repeated measurements of **15 equation families**, not 75 independent equations. Five seeds measure sensitivity to stochastic initialization; they do not increase the number of distinct scientific problems from 15 to 75.

All 225 records have successful fit/evaluation status. That is a pipeline-completion indicator, not a scientific-quality guarantee: a model can complete successfully and still have poor test R² or catastrophic extrapolation.

The source summary records a clean run, engine version 5.4, 30 populations and 1,000 iterations. The analysis uses the committed seed result JSONs as the primary source because they preserve the discovered expression, raw extrapolation scores, status fields, LLM routing metadata, complexity and timing. The case-level CSV is useful for aggregation but does not expose all the forensic fields.

## 2. Overall results

Values below are computed across 75 equation-seed records per arm. Median far-OOD R² is calculated only over records whose far-OOD value is finite; catastrophic records are counted separately and must not be silently interpreted as missing-at-random.

| Metric | PySR only | HypatiaX | HypatiaX noLLM |
|---|---:|---:|---:|
| Primary success | 75/75 | 75/75 | 75/75 |
| Median test R² | **0.996999** | 0.996966 | 0.996992 |
| Mean test R² | 0.983464 | 0.968705 | 0.965451 |
| Finite far-OOD records | 71/75 | 64/75 | 64/75 |
| Catastrophic far-OOD status | 4/75 | **11/75** | **11/75** |
| Median finite far-OOD R² | 0.999633 | **0.999732** | 0.999151 |
| Mean finite far-OOD R² | -5.0312 | -1.2472 | 0.1644 |
| Median recorded runtime (s) | 1101.32 | 375.37 | 407.35 |
| Median expression complexity | 7 | 33 | 34 |

### Interpretation

- The three test-R² medians are practically indistinguishable at the precision shown. The mean is lower for both hybrid arms because a small number of difficult outcomes have a large effect.
- The finite-only far-OOD medians look excellent, but they exclude 11/75 hybrid outcomes. This is a serious selection effect. The finite-only mean is also not a robust summary of a heavy-tailed metric.
- PySR has four catastrophic far-OOD outcomes; both hybrid arms have eleven. The additional hybrid failures are concentrated in Arrhenius and Impermanent Loss.
- The hybrid methods produce more complex expressions (median complexity 33–34 versus 7). Greater complexity has not translated into better typical test R² or better robustness.
- The recorded runtime medians are not a controlled speed comparison. The PySR-only arm records a 1,400-second budget and one allowed attempt, whereas the hybrid arms record a 3,600-second budget and up to three attempts. The hybrid runtime distribution also includes direct LLM-only acceptances that finish in roughly 4–15 seconds. These are materially different search policies.

## 3. Seed sensitivity

The source report gives the following seed-level means. Far-OOD means are conditional on finite far-OOD records; the finite counts are shown to make the exclusion explicit.

| Seed | Arm | Mean test R² | Mean finite far-OOD R² | Finite far n/15 | Mean runtime (s) |
|---:|---|---:|---:|---:|---:|
| 42 | PySR | 0.9783 | -4.7821 | 15 | 1104.4 |
| 42 | HypatiaX | 0.9929 | 0.2885 | 13 | 350.9 |
| 42 | noLLM | 0.9924 | 0.5742 | 13 | 469.8 |
| 99 | PySR | 0.9711 | -4.2666 | 13 | 1079.4 |
| 99 | HypatiaX | 0.9365 | -0.2703 | 13 | 404.6 |
| 99 | noLLM | 0.9365 | -0.2713 | 13 | 567.6 |
| 123 | PySR | 0.9860 | -4.3811 | 15 | 1063.5 |
| 123 | HypatiaX | 0.9939 | 0.9988 | 13 | 334.0 |
| 123 | noLLM | 0.9942 | 0.5326 | 13 | 430.7 |
| 777 | PySR | 0.9964 | -6.3955 | 14 | 1061.2 |
| 777 | HypatiaX | 0.9343 | -6.8519 | 12 | 603.9 |
| 777 | noLLM | 0.9169 | -1.0575 | 12 | 698.9 |
| 2024 | PySR | 0.9855 | -5.3403 | 14 | 1105.5 |
| 2024 | HypatiaX | 0.9859 | -0.8321 | 13 | 376.0 |
| 2024 | noLLM | 0.9873 | 0.9502 | 13 | 475.3 |

Seeds 99 and 777 expose hybrid instability. At seed 99, both hybrid arms have mean test R² around 0.9365; at seed 777, HypatiaX falls to 0.9343 and noLLM to 0.9169. PySR's seed-777 mean test R² is 0.9964. The low hybrid means are not a uniform degradation across all equations: they are driven by a small number of severe cases, especially Ideal Gas Law, Kinetic Energy and Gravitational Force.

Averages across seeds should therefore be accompanied by equation-level minima and failure counts. Reporting only a median across 75 records would conceal the seed-specific failures.

## 4. Equation-level robustness

The table reports HypatiaX's median test R² across five seeds, its worst test R², and the number of seeds with catastrophic far-OOD status. The minimum far-OOD values include finite negative scores as well as raw values retained for catastrophic records.

| Equation | Median test R² | Minimum test R² | Catastrophic far-OOD |
|---|---:|---:|---:|
| Arrhenius | 0.996791 | 0.996421 | **5/5** |
| Henderson–Hasselbalch | 0.997151 | 0.996186 | 0/5 |
| Rate Law | 0.997170 | 0.995398 | 0/5 |
| Allometric Scaling | 0.997216 | 0.996397 | 0/5 |
| Michaelis–Menten | 0.997445 | 0.996965 | 0/5 |
| Logistic Growth | 0.996797 | 0.967177 | 0/5 |
| Kinetic Energy | 0.998108 | 0.859731 | 0/5 |
| Gravitational Force | 0.946971 | 0.701415 | 0/5 |
| Ideal Gas Law | 0.994782 | **0.198111** | **1/5** |
| Impermanent Loss | 0.997258 | 0.995352 | **5/5** |
| Price Impact | 0.997594 | 0.995757 | 0/5 |
| Constant Product | 0.992054 | 0.971402 | 0/5 |
| Value at Risk | 0.995878 | 0.995621 | 0/5 |
| Liquidation Price | 0.996845 | 0.995629 | 0/5 |
| Portfolio Std Dev | 0.997102 | 0.995732 | 0/5 |

The median test score is misleading for Ideal Gas Law and Kinetic Energy: one seed is severely degraded while the other four remain strong. Gravitational Force is not merely a single-seed anomaly; its median test R² is materially lower than the other families.

### Far-OOD failure concentration

- **Arrhenius:** all five HypatiaX and noLLM results are catastrophic. Raw far-OOD R² ranges down to approximately -1.56×10¹².
- **Impermanent Loss:** all five HypatiaX and noLLM results are catastrophic. The worst raw far-OOD R² is approximately -416.43.
- **Ideal Gas Law:** seed 777 is catastrophic, with raw far-OOD R² approximately -5.81×10¹⁵.
- **Kinetic Energy:** seed 777 has a finite but very poor far-OOD R² of -82.12. The status remains “ok” because the value is finite; scientifically it is still a major failure.
- **Logistic Growth:** seed 2024 has far-OOD R² of -22.15.
- **Gravitational Force:** multiple seeds have negative far-OOD R², with HypatiaX reaching -8.60.
- **Michaelis–Menten:** HypatiaX reaches -0.486 in one seed despite a strong test score.

The word “catastrophic” above refers to the result JSON's explicit far-OOD status. It is not synonymous with every poor negative R². A finite R² below zero is still a poor extrapolation result even if the status is “ok”.

## 5. Expression-level forensic findings

### 5.1 Arrhenius: a repeatable wrong-form extrapolation

The Arrhenius relationship has exponential dependence on reciprocal absolute temperature, conventionally written (k=A\exp(-E_a/(RT))). HypatiaX's selected expressions across seeds instead include high-power temperature laws such as:

`(T / 434.67657) ^ 12.908299`

`(T * 0.0022998452) ^ 12.932167`

`(T / 435.83212) ^ 13.172349`

and a nested exponential expression:

`21.519812 / exp(exp(413.86047 / (T + -148.8998)))`

All five HypatiaX and noLLM far-OOD scores are catastrophic, despite test R² values around 0.9964–0.9971. This is a textbook case of an expression fitting the observed range without recovering the correct functional dependence. The LLM proposals recorded for these runs (for example, expressions proportional to (k_B T/q_e)) were not selected; the routing mode generally records `hybrid_pysr_better` or `hybrid_structural_risk_pysr`. The LLM did not rescue the final expression.

### 5.2 Impermanent Loss: stable interpolation, unstable extrapolation

Across all five seeds, HypatiaX and noLLM have catastrophic far-OOD status while test R² remains approximately 0.9954–0.9975. Selected formulas include combinations of inverse and linear terms in the price ratio (r), for example:

`((r * -11.67686) + (-11.684317 / r)) - -23.330292`

The coefficients and form can approximate a narrow training interval, but the results do not extrapolate reliably. PySR-only also has very poor finite far-OOD scores for this family (roughly -58 to -68), so this is not a problem unique to the hybrid method. The hybrid's raw scores are worse in magnitude and become marked catastrophic.

### 5.3 Ideal Gas Law: missing-variable failure at seed 777

The selected seed-777 expression is:

`sqrt(n * 5.4327)`

It omits both temperature and volume. Its test R² is 0.1981 and raw far-OOD R² is approximately -5.81×10¹⁵. The LLM proposal recorded for this case was `n * T / V`, which at least contains the relevant variable structure, but the route was `hybrid_structural_risk_pysr` and the selected expression remained the PySR result. This suggests the routing/acceptance policy did not turn a potentially useful proposal into a valid final model. It does **not** prove the LLM proposal was correct or sufficiently calibrated; it does show the final candidate should have failed a stronger variable-coverage or scientific-structure gate.

### 5.4 Kinetic Energy: a structurally implausible seed-777 expression

At seed 777 the selected HypatiaX expression is:

`log((((v * sqrt(m)) * 0.5100047) + -0.8729826) + (-0.04662489 / (m + -2.0693998)))`

This contains a logarithm and a denominator that approaches a singularity near a particular mass value. It is not the expected proportional structure (E_k\propto mv^2). The LLM proposal was `0.5 * m * v**2`, but the route again selected the PySR path under `hybrid_structural_risk_pysr`. Test R² falls to 0.8597 and far-OOD R² to -82.12. The noLLM result is also poor (test R² 0.7061; far-OOD -17.33).

By contrast, in seeds 42, 99, 123 and 2024, the LLM-only route selects `0.5 * m * v**2` and completes in about five seconds with very high scores. This sharp difference demonstrates that the route/selection policy is central to the outcome, not just the underlying equation.

### 5.5 Gravitational Force: weak equation recovery

The Newtonian form is (F=Gm_1m_2/r^2). Several selected formulas instead include variable exponents, logarithms or exponential transforms of masses and distance. For example, seed 777 selects:

`log(m1 * ((m2 * 0.121897295) / r)) ^ (1.5134895 ^ r)`

and seed 2024 selects:

`((m1 * 0.22206146) ^ m2) / (r ^ r)`

These are not credible recoveries of the expected inverse-square law. The LLM proposals recorded in these cases are close to the known physical structure, but some are not accepted. The median HypatiaX test R² is only 0.9470, and its minimum is 0.7014. This equation should be treated as a primary scientific-validity failure, not as a minor metric fluctuation.

## 6. Does the LLM change the answer?

The matched HypatiaX versus noLLM comparison is the cleanest available ablation for incremental LLM contribution.

| Matched outcome across 75 equation-seed units | Count |
|---|---:|
| Identical final expression | **34** |
| Identical test R² to 1e-12 tolerance | **37** |
| Identical far-OOD R² field | **38** |
| HypatiaX test R² higher | 22 |
| HypatiaX test R² lower | 16 |
| Test R² tied within tolerance | 37 |
| HypatiaX raw far-OOD R² higher | 26 |
| HypatiaX raw far-OOD R² lower | 12 |
| Raw far-OOD tied within tolerance | 37 |

The paired median difference in test R² is zero. The paired median raw far-OOD difference is also zero. These are descriptive paired counts, not independent-sample tests.

The HypatiaX routing breakdown is:

| Selected route | Cases | Catastrophic far-OOD |
|---|---:|---:|
| `hybrid_llm_only` | 22 | 0 |
| `hybrid_pysr_better` | 44 | 9 |
| `hybrid_structural_risk_pysr` | 9 | 2 |

The LLM-only cases are a selected subset, so their perfect catastrophic-failure count cannot be interpreted as a causal treatment effect. Routing depends on model confidence, candidate quality and validation logic. Still, the result suggests the LLM can be highly useful when the system accepts a structurally correct closed-form proposal, but the fallback/search path remains vulnerable when the LLM proposal is rejected.

The noLLM comparison also shows that many failures are inherited from the shared symbolic search/selection path: Arrhenius is identical across arms in all five seeds, and Impermanent Loss is identical in four of five seeds. The LLM does not systematically fix these cases.

## 7. Runtime and complexity: why the speed claim needs qualification

The median recorded runtime is 1,101 seconds for PySR-only, 375 seconds for HypatiaX and 407 seconds for noLLM. This is a real observed difference in the recorded run, but it is not an apples-to-apples speedup experiment:

1. PySR-only records a 1,400-second wall-clock budget and one allowed PySR attempt.
2. Hybrid arms record a 3,600-second budget and up to three attempts.
3. Twenty-two HypatiaX cases use an LLM-only route and finish in roughly 4–15 seconds.
4. Some hybrid cases consume more time than PySR-only (up to roughly 1,837 seconds for HypatiaX and 2,058 seconds for noLLM).

The correct conclusion is that **the hybrid pipeline often returns a candidate faster under its current routing policy**, not that it is computationally more efficient under equal search budgets. A fair speed study should match hardware, timeout, search iterations, number of restarts, candidate evaluation budget and stopping criteria, and should report both wall-clock and CPU/GPU time.

Complexity is also higher in the hybrid arms (median 33–34 versus 7). Complexity is not automatically bad, but the extra expression complexity has not delivered systematic improvements in test or far-OOD accuracy. A complexity-penalised, dimensionally constrained selection stage is warranted.

## 8. Statistical interpretation and limitations

This is a descriptive replication, not a confirmatory hypothesis test. There are 15 equation families, five repeated seeds and three methods. Treating 75 equation-seed records as 75 independent scientific problems would inflate the effective sample size. Any inferential analysis should preserve the repeated-measures structure, with equation family as the primary cluster and seed as a repeated stochastic replicate.

A few cautions are especially important:

- **Censored/flagged far-OOD scores:** 11/75 hybrid scores per arm are represented as null in `extrap_r2_far`, but raw values and catastrophic status are retained. Excluding them from finite-only means and medians creates an optimistic conditional summary. Report failure incidence alongside conditional performance.
- **R² is not a scale-free scientific-validity test:** R² can be high on a narrow range while the formula is physically wrong and unstable outside it. Report RMSE/MAE in original units, variable coverage, dimensional consistency and expression plausibility.
- **Repeated equations:** seed-level repetitions do not make each equation an independent unit. Do not run naive tests on 75 observations as though they were unrelated.
- **Routing selection:** comparing LLM-only versus PySR fallback is confounded by the route-selection mechanism.
- **Runtime budgets:** different attempt counts and wall-clock budgets invalidate a simple speedup claim.
- **Formula pathology flags:** the examples above warrant stronger scientific checks. The current per-record `formula_pathology_reasons` field is empty for the highlighted selected expressions, so the current pathology detector/validator is not sufficient to catch these cases.

No new benchmark, rerun or expensive computation was launched for this investigation.

## 9. Recommended next actions (historical recommendations; see Section 11 for implementation status)

### Priority 1 — fix scientific acceptance gates before more large runs

1. Add equation-aware variable coverage checks. For Ideal Gas Law, a candidate that omits (T) or (V) should be rejected or flagged.
2. Add dimensional-analysis checks for physical equations, especially Gravitational Force and Kinetic Energy.
3. Add structural constraints or risk scoring for variable exponents, nested exponentials, logs of dimensional quantities, and denominators with poles in/near the evaluation domain.
4. Require extrapolation sanity checks at multiple ranges before accepting a candidate as robust. Preserve raw metrics and mark the run scientifically failed when far-OOD is catastrophic.
5. Make the final report distinguish pipeline success, test success and scientific robustness.

### Priority 2 — investigate exact failures without a full benchmark

1. Re-evaluate the stored expressions on the existing train/test/near/medium/far arrays.
2. Plot prediction versus ground truth by range for the six problem families highlighted above.
3. Inspect the split boundaries and variable ranges, particularly for Arrhenius and Impermanent Loss.
4. Compare the selected expression, LLM proposal, and rejected candidates with their validation scores and routing reasons.
5. Add regression tests using the already stored examples; no expensive search is needed.

### Priority 3 — run a fair confirmatory study only after approval

1. Use matched per-equation seeds and identical compute budgets.
2. Pre-register primary metrics: failure-aware far-OOD success rate, test RMSE, far-OOD RMSE and formula-validity rate.
3. Report all 15 equation families separately and use a hierarchical or cluster-aware analysis.
4. Include confidence intervals over equation families and seeds; do not count non-finite/catastrophic results as missing-at-random.
5. Separate LLM proposal quality from the effect of the routing/acceptance policy.

## 10. Reproducibility pointers

- [Parent workflow run](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/45915400809)
- [Committed multi-seed report](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/11ee474/hypatiax/data/results/ablation/exp1_ablation_multiseed/exp1_ablation_multiseed_report.md)
- [Committed multi-seed summary JSON](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/11ee474/hypatiax/data/results/ablation/exp1_ablation_multiseed/exp1_ablation_multiseed_summary.json)
- [Committed case/seed CSV](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/11ee474/hypatiax/data/results/ablation/exp1_ablation_multiseed/exp1_ablation_multiseed_case_seed_records.csv)
- [Benchmark source](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/1bb4c9d7ccf4813b10014fc85a67b4a28d8f18c4/hypatiax/experiments/benchmarks/exp1_ablation.py)

## 11. Post-merge remediation review and targeted investigation (27 November 2026)

### Merge and CI verification

PR [#411](https://github.com/sednabcn/LLM-HypatiaX-REPRO/pull/411) (this report) and PR [#412](https://github.com/sednabcn/LLM-HypatiaX-REPRO/pull/412) (Core-15 scientific candidate gates) are merged. The latter is in master commit [dd9eef5](https://github.com/sednabcn/LLM-HypatiaX-REPRO/commit/dd9eef58fb4a666ed0ffb3632b27562d3567e74d).

Post-merge checks on that commit:
- [Runner smoke](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/45982952869): success.
- [R2 policy, metrics API and recovery evaluator](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/45982953065): success.
- Full pinned-Python 3.12 suite: **1,419 passed, 3 skipped, 0 failed**.
- R2 policy/workflow cleanup: 85 passed; PCA split protocol: 7 passed; experiment artifact/workflow contracts: success.

This verifies the merged code against CI. It does not prove the historical scientific failures have disappeared from new benchmark results.

### What the Core-15 gates now do

PR #412 adds hard required-variable and finite-training-domain checks, output-sign screens, and equation-specific structural checks:
- Arrhenius: exponential dependence on reciprocal temperature; reject nested exponentials.
- Impermanent Loss: square-root price-ratio structure, reciprocal symmetry and non-positive output.
- Ideal Gas Law: linear amount and temperature dependence, inverse volume dependence, fixed exponents.
- Kinetic Energy: linear mass, approximately quadratic velocity, no logarithm or variable exponents.
- Gravitational Force: linear dependence on both masses, inverse-square distance, no logarithms or variable exponents.
- Logistic Growth: quadratic population term and sampled increasing/concave shape.
- Michaelis–Menten: saturation denominator and sampled increasing/concave shape.

HypatiaX candidate selection uses two training-only validation folds and does not launch a second PySR configuration sweep. Held-out and far-OOD targets are excluded from selection. Candidate-level validation and a separate post-selection status are recorded. The PySR-only arm receives a post-selection audit, which labels its expression but does not alter its prediction or metric.

Limitations remain: these are structural and finite-sample screens, not continuous-domain proofs; they do not provide full dimensional analysis (Core-15 unit metadata is empty); and not all 15 equations have bespoke equation-specific contracts. A passing contract is not proof of unique correctness or extrapolation success. No new five-seed Exp1 ablation has been run after PR #412.

### Historical failure disposition

| Finding | Safeguard now present | Empirical status |
|---|---|---|
| Arrhenius: catastrophic far-OOD in 5/5 hybrid seeds | Reciprocal-temperature exponential and nested-exponential checks | **Unverified pending replication** |
| Impermanent Loss: catastrophic far-OOD in 5/5 hybrid seeds | Square-root, reciprocal-symmetry and sign checks | **Unverified pending replication** |
| Ideal Gas Law: omitted T and V at seed 777 | Required variables, fixed powers, linear n/T, inverse V | **Unverified pending replication** |
| Kinetic Energy: implausible logarithmic formula | Mass/velocity powers, log prohibition, fixed exponents | **Unverified pending replication** |
| Gravitational Force: weak recovery and variable exponents | Linear mass powers, inverse-square distance and exponent checks | **Unverified pending replication** |
| Logistic Growth: unstable growth forms | Quadratic population and sampled shape checks | **Unverified pending replication** |
| Michaelis–Menten: saturation instability | Saturation denominator and sampled shape checks | **Unverified pending replication** |

The merged regression tests exercise representative valid and invalid expressions. This is evidence for gate logic, not outcome evidence from rerunning stochastic discovery. Historical results remain unchanged.

### Targeted investigation: five Kelly NN metric failures in exp1b_pca

The five-seed PCA run [#45970544339](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/45970544339) completed 74 cases per seed (42, 99, 123, 777, 2024), 370 records total. It reported 365 finite hybrid test-R2 values and five missing values, all for **Optimal LP Position (Kelly)**. The run log reports undefined_train_or_test_metric for this case in all five seeds.

This is not a scaler feature-count mismatch. Reproducing the committed protocol and split gives:
- 200 rows; expected APY is drawn from 0.05–0.18 and 0.22–0.30, shuffled with seed 44; risk ranges from 0.05–0.25.
- Target: f* = min(APY / (2 × risk²), 1).
- PCA is fit on the raw, unstandardized two-feature matrix; lowest 40% of PC1 is train and highest 60% is test.
- PC1 loadings are approximately (0.9969, 0.0784), explaining 65.16% of feature variance.
- The 80-row training target has 10 distinct values; **all 120/120 test targets equal exactly 1.0** because the Kelly cap is active throughout the test partition.

The canonical R2 policy correctly returns NaN with status degenerate_target for a zero-variance target. The missing test R2 is mathematically correct for this split, not proof of failed NN fitting or scaler failure. The benchmark collapses this into undefined_train_or_test_metric and does not persist the detailed R2 status in the serialized NN record.

A second issue is diagnostic labeling: exp1b_pca_seed_outputs.py and run_all.sh classify every missing NN test-R2 value as part of the feature-mismatch fingerprint. These five Kelly records have no scaler mismatch message; they are false positives for that category.

**Recommended correction before another PCA run:**
1. Redesign the Kelly held-out distribution/split so its target has meaningful variance while preserving the directional question; do not randomize merely to make R2 finite.
2. Persist train_r2_status, test_r2_status and failure_reason; distinguish degenerate_target from fit, timeout, scaler and prediction failures.
3. Restrict the feature-mismatch fingerprint to actual scaler/feature-count error signatures; report missing/undefined metrics separately.
4. Report 370 attempted records, 365 finite hybrid scores and five degenerate-target records explicitly.

This investigation used the deterministic protocol and split code only. No benchmark, model-training run or expensive search was launched.

### Current disposition

The engineering remediation is merged and CI-verified. The Kelly warning is explained by a degenerate test-target design plus an over-broad diagnostic label. The scientific effectiveness of the Core-15 gates remains **not empirically verified**. The next confirmatory step is a fresh five-seed Core-15 ablation under the merged gates, compared failure-aware against the historical 225-record baseline. Correct the separate exp1b_pca Kelly split and metric reporting before interpreting its NN scorecard. No benchmark was launched for this report update.

**Bottom line:** HypatiaX is competitive on typical in-distribution cases and can be very fast when a correct LLM-only expression is accepted. The historical five-seed evidence does not establish general superiority over PySR. PR #412 now adds equation-aware scientific candidate safeguards, but their empirical effectiveness remains unknown until a fresh replication. The separate Kelly PCA split has a degenerate held-out target and needs a protocol/reporting correction before its NN metric can be interpreted.
