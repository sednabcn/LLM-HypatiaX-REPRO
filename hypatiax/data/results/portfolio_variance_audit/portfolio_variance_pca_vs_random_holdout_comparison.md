# Portfolio VaR: PCA sweep and random-holdout comparison

**Branch:** `audit-master`  
**Case:** `risk_var` / Portfolio VaR for two correlated assets  
**Prepared:** 2026-11-08  
**Purpose:** Consolidate the existing PCA-directed seed sweep and independent random-holdout validation without conflating their protocols or score semantics.

## Executive summary

Two separate validation experiments are complete:

1. The PCA-directed sweep completed for five model/experiment seeds on **one fixed, transductive PC1-directed partition**. Every run reported `train_r2=1.0` and `far_r2=1.0`.
2. The random-holdout control completed for five independently sampled 40/60 partitions with the model seed fixed at 42. The selected neural-network route achieved mean test R² **0.999709** (sample SD **0.000121**); all five partitions exceeded 0.99.

The results support strong performance under the random-holdout protocol, but the previously reported PCA far-tail scores are now in tension with a separate bootstrap sensitivity result (tail R² = -3.1518 on one repeated partition). A feature-ranking diagnostic also shows that the PCA partition is exactly reproduced by sorting any one of the three input features. Therefore, the current PCA experiment should not be presented as evidence that PCA adds a distinct multivariate split or that tail extrapolation is robust. The prediction-error diagnostic described below is the remaining step before finalizing the PCA assessment.

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

## Pending diagnostic — NN tail prediction errors

The NN-only diagnostic `portfolio_variance_pca_tail_error_diagnostic.py` has been added to `audit-master`, but its output has not yet been supplied or reviewed. It reuses the benchmark NN helper on the existing PCA 40/60 split and compares predictions against the training-target-mean baseline. It reports test R², MAE, RMSE, signed error, error by PC1 decile, and per-row predictions.

This diagnostic is intended to explain the previously observed negative bootstrap tail score. It is NN-only and does not reproduce LLM/hybrid routing. The PCA assessment should remain provisional until these errors are inspected.

## Interpretation and limitations

- Both experiment suites report very high performance for this one selected Portfolio VaR case.
- The random-holdout results demonstrate stability across the five tested random partitions for a fixed model seed, under the selected NN route.
- The PCA sweep demonstrates consistent reported train/far scores across five experiment seeds on one fixed transductive PCA split.
- The PCA protocol uses raw feature scales. Its first component is effectively dominated by the two variance features, with negligible correlation loading. The feature-ranking diagnostic further shows that all three individual feature rankings exactly reproduce the PC1 ranking and the same 80/120 partition.
- The random-holdout protocol is a control for interpolation, not a substitute for the PCA-directed tail test.
- These results concern one case and should not be generalized to other domains or cases without additional experiments.
- The PCA workflow ran in sweep-only mode; these results do not imply downstream paper tables, LaTeX exports, or figures were generated.
- The bootstrap PCA sensitivity run previously produced five identical partitions despite distinct bootstrap samples, with tail test R² = -3.151809 for all five replicates; this is a negative sensitivity result, not successful validation.
- No claim is made here about independent PCA partitions, NN training R², or statistical significance.

## Reproducibility sources

- PCA workflow run: [42410055833](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/42410055833)
- Random-holdout workflow run: [42421397598](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/42421397598)
- PCA aggregate: `hypatiax/data/results/portfolio_variance_audit/portfolio_variance_pca_seed_aggregate.json`
- Random-holdout results: `hypatiax/data/results/portfolio_variance_audit/portfolio_variance_random_holdout_validation.json`
- Random-holdout protocol notes: `hypatiax/experiments/benchmarks/PORTFOLIO_PARTITION_VALIDATION.md`
- Feature-ranking diagnostic: `hypatiax/data/results/portfolio_variance_audit/portfolio_variance_feature_ranking_diagnostic.json`
- Tail-error diagnostic runner: `hypatiax/experiments/benchmarks/portfolio_variance_pca_tail_error_diagnostic.py`
