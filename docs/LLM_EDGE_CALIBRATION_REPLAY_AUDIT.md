# Offline replay audit: LLM edge-degradation calibration

**Status: complete, input-integrity verified; not suitable for selecting routing tau.**

## Provenance

- Source calibration run: [45038667467](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/45038667467)
- Source commit: `107fcd6da06fe15833ecdf37c6d2284da84256c8`
- Source artifact: `llm-edge-degradation-calibration`, artifact ID `14760901742`
- Successful replay workflow: [45040940383](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/45040940383)
- Replay artifact: `llm-edge-calibration-replay`, artifact ID `14761712384`
- Replay commit: `c89135ebf106368ec5e70ab2fb2a8c89e6381cd3`
- Replay regenerates the 74-case protocol in catalogue order, checks saved split indices and SHA-256 hashes, then evaluates saved formulas with the restricted formula interpreter. No LLM/provider calls are made.

The benchmark, protocol generator, and edge-split source files used by the replay have the same Git blob hashes at the source calibration commit and the replay revision. The successful replay verified all saved core/edge indices, row counts, outer-split metadata, and data hashes.

## Replay coverage

| Cohort | Total | Input verified | Scored | Score undefined | No saved formula | Hash mismatch |
|---|---:|---:|---:|---:|---:|---:|
| Calibration | 44 | 44 | 23 | 19 | 2 | 0 |
| Evaluation | 30 | 30 | 24 | 4 | 2 | 0 |
| **Total** | **74** | **74** | **47** | **23** | **4** | **0** |

All 47 formulas that scored in the original artifact were replayed. Their core and edge R² values exactly match the original stored values (maximum absolute difference: 0.0 for both partitions).

The 23 verified-but-undefined formula rows failed the restricted formula execution/valid-output check on both partitions in the original saved artifact. The original artifact predates categorized execution diagnostics, so those historical failures cannot now be reliably split into parser, runtime, shape, or finite-value causes. Four generation failures had no saved formula.

## Scores on the 47 input-verified formulas

| Metric | Calibration (n=23) | Evaluation (n=24) |
|---|---:|---:|
| Mean `R²_core - R²_edge` | -3,308,789,123.847 | -21.5685 |
| Median `R²_core - R²_edge` | 0 | 0 |
| 10th percentile | 0 | -0.2603 |
| 90th percentile | 0 | 0 |
| Zero deltas | 21 | 18 |
| Negative deltas | 2 | 5 |
| Positive deltas | 0 | 1 |
| Median `NRMSE_edge - NRMSE_core` (both scaled by core target SD) | 0 | 0 |

The means are dominated by extreme poor-fit cases. The zero-heavy medians do not indicate a healthy calibration cohort: 2/23 calibration formulas and 6/24 evaluation formulas have at least one partition with R² below 0.99. Five formulas have R² below -1 on both partitions (two calibration, three evaluation).

## Important failure modes

- **LP fee earnings (calibration):** core R² = -102,499,284,817; edge R² = -26,397,134,972. Core/edge normalized RMSE on the common core-target scale is approximately 320,155 / 101,476. Target SDs are approximately 702 / 439, while predictions range into the hundreds of millions. The saved expression repeatedly multiplies liquidity-share factors and is not a credible implementation of the intended fee-earnings relationship. This is a formula-quality failure, not evidence of a useful negative degradation signal.
- **Impermanent loss breakeven fee rate (evaluation):** core/edge R² = -520.99 / -20.34; normalized RMSE = 22.85 / 28.49. The fit is poor on both partitions, and edge error is worse on the common scale even though the R² delta is strongly negative.
- **Effective Leverage (evaluation):** core/edge R² = -18.97 / -1.17; normalized RMSE = 4.47 / 2.50. Both fits are poor; the edge partition happens to be less bad.
- **Price slippage percentage (evaluation):** core/edge R² = -2.70 / -3.96; normalized RMSE = 1.92 / 2.44. The edge error worsens, but both fits are poor.
- **Concentrated liquidity position width v2 (calibration):** core/edge R² = -5.45 / -2.47; normalized RMSE = 2.54 / 3.17. R² delta is negative, but the common-scale error is worse on the edge.
- **Portfolio Expected Shortfall for correlated (evaluation):** R² improves from 0.452 to 0.776, while common-scale normalized RMSE worsens from 0.740 to 0.892. The different target variances across partitions can make R² comparisons point in a different direction from a common-scale error comparison.

These examples show why a finite R² difference alone is not a reliable degradation statistic. In particular, a negative `R²_core - R²_edge` can coexist with a poor core fit, a poor edge fit, or worsening common-scale error.

## Follow-up implementation and CI verification

The calibration evaluator now calls the benchmark's diagnostic formula-execution API and stores partition-level failure reasons and execution metadata instead of collapsing all failures into a generic invalid-output status. Covered failure classes include invalid input/shape, non-finite input, parse errors, execution errors, invalid output type/shape, excessive or unrepaired non-finite predictions, and constant predictions. The legacy benchmark wrapper retains its original `None`/array contract.

The normalization regression test was updated to mock this diagnostic API. The duplicate root-level test module was removed, leaving the canonical test under `hypatiax/experiments/tests/`.

Verified on `master` at commit `aed17e5c5f6c6419a7fc2bebbb45dabd38ea1743`:

- [R2 policy gate run 45045119964](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/45045119964): all three jobs passed; full pytest suite **931 passed**.
- [Runner smoke run 45045120024](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/45045120024): completed successfully, including offline smoke checks.

These runs supersede the earlier failed R2 gate #1947 and cancelled smoke attempt #2198. They establish CI correctness for this code revision; they do not change the scientific interpretation of the saved calibration artifact.

## Decision

1. **Do not select or deploy tau from this artifact.** Although replay is complete and input-integrity verified, the formula population has substantial undefined and poor-fit cases, and no acceptable-fit criterion was predeclared.
2. Keep `tau = null` and retain the existing fail-closed ensemble route.
3. Preserve all poor finite scores in descriptive reporting; do not clip, winsorize, or discard them to improve a threshold.
4. Use the separate protocol in [LLM-specific training-only tau calibration protocol](LLM_TAU_TRAINING_ONLY_PROTOCOL.md) before any future threshold selection.
5. Continue reporting calibration and independent evaluation cohorts separately; do not tune a threshold on the evaluation cohort.

This report does not change the benchmark baseline, routing policy, or `tau`. No new LLM/provider calls were made for this audit or its CI verification.
