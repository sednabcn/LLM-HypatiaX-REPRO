# Offline replay audit: LLM edge-degradation calibration

**Status: partial replay; not suitable for selecting routing tau.**

## Provenance

- Source calibration run: [45038667467](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/45038667467)
- Source commit: `107fcd6da06fe15833ecdf37c6d2284da84256c8`
- Source artifact: `llm-edge-degradation-calibration`, artifact ID `14760901742`
- Replay workflow: [45040681088](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/45040681088)
- Replay artifact: `llm-edge-calibration-replay`, artifact ID `14761447754`
- Replay code regenerates the 74-case protocol in catalogue order, checks saved split indices and data hashes, then evaluates saved formulas with the restricted formula interpreter. No LLM/provider calls are made.

The benchmark, protocol generator, and edge-split source files used by the replay have the same Git blob hashes at the source calibration commit and the replay revision. Nevertheless, **13 cases did not reproduce their saved data hashes**. Matching row counts, split indices, and outer-split metadata are not sufficient to establish data identity. Those 13 cases are excluded from all replay score summaries.

## Replay coverage

| Cohort | Total | Input verified | Scored | Score undefined | No saved formula | Hash mismatch |
|---|---:|---:|---:|---:|---:|---:|
| Calibration | 44 | 34 | 18 | 14 | 2 | 10 |
| Evaluation | 30 | 27 | 22 | 3 | 2 | 3 |
| **Total** | **74** | **61** | **40** | **17** | **4** | **13** |

The 17 verified-but-undefined formula rows failed the restricted formula execution/valid-output check on both partitions. Four generation failures had no saved formula. The current evaluator reports a generic execution/invalid-output reason for these rows; it does not yet distinguish parser, runtime, shape, or finite-value causes.

Hash-mismatched cases:

- Spot price from AMM
- Reserve ratio
- Borrowing Interest
- Compounding Staking Returns
- APY calculation
- Funding rate cost (extended)
- Spot price from AMM reserve
- Black-Scholes Call Price
- Black-Scholes Put Price
- Component ES
- Gamma of option
- Vega of option
- Constant product formula (multivariate)

For all 13, row counts and saved split indices matched. Most had a core and/or edge data hash mismatch; the multivariate constant-product case also differed in outer-split metadata. The source artifact stores hashes and indices, not the original feature/target arrays, so these records cannot be safely rescored from the artifact alone. The reason for the mismatches remains unresolved.

## Scores on the 40 input-verified formulas

All 40 replayed R² values exactly match the corresponding stored R² values in the original calibration artifact (maximum absolute difference: 0.0). The diagnostics below are therefore a verified re-evaluation of those 40 rows only.

| Metric | Calibration (n=18) | Evaluation (n=22) |
|---|---:|---:|
| Mean `R²_core - R²_edge` | -4,227,897,213.804 | -23.5292 |
| Median `R²_core - R²_edge` | 0 | 0 |
| 10th percentile | -0.8948 | -0.3032 |
| 90th percentile | 0 | 0 |
| Zero deltas | 16 | 16 |
| Negative deltas | 2 | 5 |
| Positive deltas | 0 | 1 |
| Median `NRMSE_edge - NRMSE_core` (both scaled by core target SD) | 0 | 0 |

The means are dominated by extreme poor-fit cases. The zero-heavy medians do not indicate a healthy calibration cohort: 2/18 calibration formulas and 6/22 evaluation formulas have at least one partition with R² below 0.99. Five formulas have R² below -1 on both partitions (two calibration, three evaluation).

## Important failure modes

- **LP fee earnings (calibration):** core R² = -102,499,284,817; edge R² = -26,397,134,972. Core/edge normalized RMSE on the common core-target scale is approximately 320,155 / 101,476. Target SDs are approximately 702 / 439, while predictions range into the hundreds of millions. The saved expression repeatedly multiplies liquidity-share factors and is not a credible implementation of the intended fee-earnings relationship. This is a formula-quality failure, not evidence of a useful negative degradation signal.
- **Impermanent loss breakeven fee rate (evaluation):** core/edge R² = -520.99 / -20.34; normalized RMSE = 22.85 / 28.49. The fit is poor on both partitions, and edge error is worse on the common scale even though the R² delta is strongly negative.
- **Effective Leverage (evaluation):** core/edge R² = -18.97 / -1.17; normalized RMSE = 4.47 / 2.50. Both fits are poor; the edge partition happens to be less bad.
- **Concentrated liquidity position width v2 (calibration):** core/edge R² = -5.45 / -2.47; normalized RMSE = 2.54 / 3.17. R² delta is negative, but the common-scale error is worse on the edge.
- **Portfolio Expected Shortfall for correlated (evaluation):** R² improves from 0.452 to 0.776, while common-scale normalized RMSE worsens from 0.740 to 0.892. The different target variances across partitions can make R² comparisons point in a different direction from a common-scale error comparison.

These examples show why a finite R² difference alone is not a reliable degradation statistic. In particular, a negative `R²_core - R²_edge` can coexist with a poor core fit, a poor edge fit, or worsening common-scale error.

## Decision

1. **Do not select or deploy tau from this artifact.** The replay is partial (13/74 source-data hash mismatches), and the formula population has substantial undefined and poor-fit cases.
2. Keep `tau = null` and retain the existing fail-closed ensemble route.
3. Preserve all poor finite scores in descriptive reporting; do not clip, winsorize, or discard them to improve a threshold.
4. Before a new calibration attempt, freeze an acceptable-fit/bad-route definition and update the generation artifact format to retain exact core/edge arrays (or an immutable content-addressed dataset snapshot), not just hashes. Also record detailed formula execution failure reasons.
5. Investigate the 13 hash mismatches before treating a future replay as complete. A hash match, not just matching indices and sizes, is the replay acceptance criterion.

This report does not change the benchmark baseline, routing policy, or `tau`.
