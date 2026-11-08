# Portfolio VaR: PCA sweep and random-holdout comparison

**Branch:** `audit-master`  
**Case:** `risk_var` / Portfolio VaR for two correlated assets  
**Prepared:** 2026-11-08  
**Purpose:** Consolidate the existing PCA-directed seed sweep and independent random-holdout validation without conflating their protocols or score semantics.

## Executive summary

Two separate validation experiments are complete:

1. The PCA-directed sweep completed for five model/experiment seeds on **one fixed, transductive PC1-directed partition**. Every run reported `train_r2=1.0` and `far_r2=1.0`.
2. The random-holdout control completed for five independently sampled 40/60 partitions with the model seed fixed at 42. The selected neural-network route achieved mean test R² **0.999709** (sample SD **0.000121**); all five partitions exceeded 0.99.

The random-holdout control shows excellent interpolation performance (mean test R² = 0.999709 across five partitions). In contrast, the NN-only evaluation on the PCA-directed tail partition has test R² = -3.151808 and MAE = 25,335.68, despite train R² = 0.999740. The model underpredicts throughout the test region, with error increasing across PC1 deciles. It does outperform the training-mean baseline (MAE ratio 0.693; R² improvement 3.015), but both test R² values are strongly negative. The PCA ranking diagnostic further shows that any one feature alone reproduces the PC1 order and exact partition. Finally, this NN-only result conflicts with the earlier seed-sweep report of far R² = 1.0; those score paths must be reconciled before the seed-sweep result can be treated as evidence of successful tail prediction.

## Experiment A — PCA-directed seed sweep

**Workflow:** [Run #199](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/42410055833)  
**Aggregate source:** [PCA seed aggregate JSON](../../data/results/portfolio_variance_audit/portfolio_variance_pca_seed_aggregate.json)

| Item | Value |
|---|---:|
| Protocol | `pca_40_60_pc1` |
| Samples | 200 |
| Train / test | 80 / 120 |
| Test fraction | 60% |
| Model/experiment seeds | 42, 99, 123, 777, 2024 |
| Split random state | 42 for every run |
| Feature scaling | None; raw, unstandardized features |
| PCA fitting | On all 200 feature rows before partitioning |
| Transductive | Yes |
| PC1 explained-variance ratio | 1.000 |
| Reported train R² | 1.000 for all five seeds |
| Reported far R² | 1.000 for all five seeds |
| Successful runs | 5/5 |

The five runs reuse the same partition metadata. They are five seed runs on one fixed partition, not five independent partitions.

PC1 loadings were approximately 0.857493 for `var_asset1`, 0.514496 for `var_asset2`, and 0.00002668 for `correlation`. Thus the split direction is dominated by the two asset-variance features; correlation contributes negligibly. The protocol is transductive because PCA is fitted using the complete feature matrix before splitting.

## Experiment B — independent random-holdout control

**Workflow:** [Run #7](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/42421397598)  
**Result source:** [Random-holdout validation JSON](../../data/results/portfolio_variance_audit/portfolio_variance_random_holdout_validation.json)  
**Runner documentation:** [Partition validation protocol](PORTFOLIO_PARTITION_VALIDATION.md)

| Item | Value |
|---|---:|
| Protocol | `independent_random_holdout_40_60` |
| Samples | 200 |
| Train / test per partition | 80 / 120 |
| Partition seeds | 11, 23, 42, 77, 101 |
| Model seed | Fixed at 42 |
| Partition method | Shuffled row-index `train_test_split` |
| Transductive | No |
| Selected score route | Neural network (`nn`) for all five |
| Mean test R² | 0.999708553 |
| Sample SD of test R² | 0.0001207579 |
| Minimum / maximum test R² | 0.999529949 / 0.999801792 |
| Partitions above 0.99 | 5/5 |

The five partition seeds produce five independently sampled random holdouts; they do not represent five independent model initializations because the model seed is held fixed.

### Score-field clarification

The schema-v2 field `llm_train_r2` refers only to the LLM formula's training R². It is NaN in these records because no valid LLM formula training score was available. It is **not** the neural network's training R² and does not indicate failed NN training.

The reported `test_r2` is the test score from the selected route, recorded as `test_r2_source`; here that route is `nn`. The success count is specifically the number of partitions with test R² greater than 0.99. The benchmark helper does not currently expose NN training R².

## Side-by-side protocol comparison

| Dimension | PCA-directed sweep | Random-holdout control |
|---|---|---|
| Evaluation intent | PC1-directed tail / far-range test | Random-holdout interpolation control |
| Partition count | One fixed partition | Five independent partitions |
| Varying seed | Model/experiment seed | Partition seed |
| Fixed seed | Split state 42 | Model seed 42 |
| Split construction | PCA on raw features, then ordered 40/60 split | Shuffled row-index 40/60 split |
| Transductive | Yes | No |
| Primary reported test metric | `far_r2` | `test_r2` |
| Observed result | 5/5 far R² = 1.000 | Mean test R² = 0.999709; 5/5 > 0.99 |

**Do not pool or average the PCA `far_r2` values with random-holdout `test_r2` values.** They come from different partition protocols and have different evaluation meanings. The PCA results are not five independent partition replications, while the random-holdout results are not evidence of PC1-tail extrapolation.


## Experiment C — feature-ranking and PCA cutoff diagnostic

**Diagnostic:** `portfolio_variance_feature_ranking_diagnostic.py`  
**Output:** `portfolio_variance_feature_ranking_diagnostic.json`  
**Generated:** 2026-11-08 11:28:42 UTC

This descriptive diagnostic fits one-component PCA on all 200 raw, unstandardized feature rows and compares the PC1 ordering and lower-40% training membership with the ordering produced by each feature individually. It does not train a model or alter the benchmark split.

| Feature | Spearman correlation with PC1 score | Train-membership Jaccard | Rows differing from PC1 split |
|---|---:|---:|---:|
| `var_asset1` | 1.000 | 1.000 | 0 |
| `var_asset2` | 1.000 | 1.000 | 0 |
| `correlation` | 1.000 | 1.000 | 0 |

All three individual feature rankings reproduce the PC1 ranking exactly, including exactly the same 80 training rows. PC1 explains 100% of the variance in the supplied feature matrix. Its oriented loadings are 0.857493 (`var_asset1`), 0.514496 (`var_asset2`), and 0.00002668 (`correlation`). Although the correlation loading is negligible, the correlation feature itself is also perfectly rank-aligned with PC1 in this dataset.

The PC1 cutoff is between scores -5406.0835 (last training row) and -5142.3722 (first test row), a gap of 263.7114. The displayed rows on either side progress smoothly; no obvious discontinuity is visible at this boundary.

**Interpretation:** for this generated dataset, the PCA split does not create a distinct multivariate ordering. Each single feature independently induces exactly the same partition. The data therefore behave as a one-dimensional ordered trajectory for ranking purposes. This is a property of this dataset, not a general conclusion about PCA. The analysis is descriptive and transductive because PCA and feature rankings use all rows.

## Experiment D — NN tail prediction-error diagnostic

**Runner:** `portfolio_variance_pca_tail_error_diagnostic.py`  
**Output:** `portfolio_variance_pca_tail_error_diagnostic.json`  
**Generated:** 2026-11-08 11:41:28 UTC

This diagnostic evaluates the benchmark NN helper on the existing PCA 40/60 partition. It uses the same 200 raw feature rows, with 80 training rows and 120 upper-tail test rows. The NN seed was 2024. No LLM call was made and no benchmark source was modified. The result is NN-only and does not independently reproduce LLM/hybrid routing.

| Metric | NN | Training-target-mean baseline |
|---|---:|---:|
| Train R² | 0.999740 | — |
| Test R² | -3.151808 | -6.167132 |
| Test MAE | 25,335.68 | 36,551.54 |
| Test RMSE | 29,990.43 | 39,403.67 |
| Mean signed error (prediction − actual) | -25,335.68 | -36,551.54 |
| Median absolute error | 24,771.58 | 35,871.31 |

The NN improves on the baseline: its R² is higher by 3.015323 and its MAE is 69.3% of baseline MAE (a 30.7% reduction). However, its test R² remains substantially below zero, so the model still performs poorly on this tail test. The equality of MAE and mean signed error indicates systematic underprediction in the aggregate; the signed error is negative.

### Error progression across PC1 test deciles

| Test decile | Target mean | Prediction mean | MAE |
|---:|---:|---:|---:|
| 1 | 29,629.80 | 27,763.18 | 1,866.62 |
| 2 | 34,039.58 | 28,195.65 | 5,843.93 |
| 3 | 38,633.12 | 27,735.59 | 10,897.53 |
| 4 | 43,403.62 | 27,056.24 | 16,347.38 |
| 5 | 48,344.99 | 26,400.52 | 21,944.47 |
| 6 | 53,451.71 | 25,829.45 | 27,622.26 |
| 7 | 58,718.76 | 25,346.19 | 33,372.57 |
| 8 | 64,141.52 | 24,938.96 | 39,202.57 |
| 9 | 69,715.77 | 24,594.12 | 45,121.64 |
| 10 | 75,437.58 | 24,299.75 | 51,137.82 |

The target mean rises steadily from approximately 29,630 in the first test decile to 75,438 in the tenth. In contrast, the NN prediction mean declines from approximately 27,763 to 24,300. MAE rises monotonically from approximately 1,867 to 51,138. This is a clear systematic failure to track the target trend across the ordered tail, not merely a few isolated outliers.

### Important score discrepancy to resolve

The earlier PCA seed-sweep report records `far_r2 = 1.0` for all five seeds, including seed 2024. This standalone NN-only diagnostic, using the benchmark NN helper and NN seed 2024 on the same stated PCA 40/60 partition, reports `test_r2 = -3.151808`. These results are materially inconsistent. They must not be silently combined or treated as equivalent metrics. Before publication or final claims, inspect the seed-sweep score calculation, data/target transformations, route-specific evaluation, and exact model-seed mapping to establish why the reported values differ.

**Interpretation:** the current diagnostic provides strong evidence that this NN configuration does not extrapolate the upper PC1-ordered tail, despite near-perfect training fit. It is better than the training-mean baseline but remains poor in absolute predictive terms. Given the feature-ranking result, this is a tail extrapolation test along an ordering that any single feature already reproduces; it does not demonstrate a special benefit of PCA as a multivariate split.

## Interpretation and limitations

- The random-holdout interpolation control is excellent, but the direct NN PCA-tail diagnostic reports poor upper-tail extrapolation; these are different evaluation regimes.
- The random-holdout results demonstrate stability across the five tested random partitions for a fixed model seed, under the selected NN route.
- The PCA seed sweep reports train/far R² = 1.0 across five model seeds on one fixed transductive split, but the direct NN tail-error diagnostic reports test R² = -3.151808 for NN seed 2024. This unresolved discrepancy must be audited before relying on the seed-sweep far R² claim.
- The PCA protocol uses raw feature scales. Its first component is effectively dominated by the two variance features, with negligible correlation loading. The feature-ranking diagnostic further shows that all three individual feature rankings exactly reproduce the PC1 ranking and the same 80/120 partition.
- The random-holdout protocol is a control for interpolation, not a substitute for the PCA-directed tail test.
- These results concern one case and should not be generalized to other domains or cases without additional experiments.
- The PCA workflow ran in sweep-only mode; these results do not imply downstream paper tables, LaTeX exports, or figures were generated.
- The bootstrap PCA sensitivity run previously produced five identical partitions despite distinct bootstrap samples, with tail test R² = -3.151809 for all five replicates; this is a negative sensitivity result, not successful validation.
- The NN tail diagnostic exposes NN training R² (0.999740), but this should not be conflated with the separate random-holdout report's unavailable `llm_train_r2` field.
- No claim is made here about independent PCA partitions or statistical significance.

## Reproducibility sources

- PCA workflow run: [42410055833](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/42410055833)
- Random-holdout workflow run: [42421397598](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/42421397598)
- PCA aggregate: `hypatiax/data/results/portfolio_variance_audit/portfolio_variance_pca_seed_aggregate.json`
- Random-holdout results: `hypatiax/data/results/portfolio_variance_audit/portfolio_variance_random_holdout_validation.json`
- Random-holdout protocol notes: `hypatiax/experiments/benchmarks/PORTFOLIO_PARTITION_VALIDATION.md`
- Feature-ranking diagnostic: `hypatiax/data/results/portfolio_variance_audit/portfolio_variance_feature_ranking_diagnostic.json`
- Tail-error diagnostic runner: `hypatiax/experiments/benchmarks/portfolio_variance_pca_tail_error_diagnostic.py`
- Tail-error diagnostic output: `hypatiax/data/results/portfolio_variance_audit/portfolio_variance_pca_tail_error_diagnostic.json`
