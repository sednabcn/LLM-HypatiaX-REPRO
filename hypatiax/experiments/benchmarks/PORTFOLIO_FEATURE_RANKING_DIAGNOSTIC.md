# Portfolio VaR feature-ranking diagnostic

## Purpose

Investigate why distinct bootstrap samples produced the same PC1 ranking and
40/60 partition. The diagnostic compares the full-data raw-feature PC1
ordering with the ordering produced by each original feature separately.

It is descriptive only: it does not train a model, modify the benchmark, or
change an existing split protocol.

## Method

1. Load the exact `risk_var` case, `Portfolio VaR for two correlated assets`.
2. Fit one-component PCA on all raw, unstandardized feature rows.
3. Orient PC1 so its largest-absolute loading is positive.
4. Rank observations ascending by PC1 score; the lower 40% form the training set.
5. Independently rank observations ascending by each original feature, using
   the same training fraction.
6. For each feature, calculate Spearman correlation with PC1 scores, Jaccard
   similarity of lower-40% training membership, and overall row-membership
   agreement.
7. Record rows immediately around the PC1 cutoff, including their PC1 scores,
   original feature values, and targets.

Stable ascending sorting uses original row index to break ties.

## Run locally

From the repository root:

```bash
python hypatiax/experiments/benchmarks/portfolio_variance_feature_ranking_diagnostic.py
```

Optional settings:

```bash
FEATURE_RANKING_TRAIN_FRACTION=0.4 \
FEATURE_RANKING_BOUNDARY_ROWS=5 \
python hypatiax/experiments/benchmarks/portfolio_variance_feature_ranking_diagnostic.py
```

Output:

`hypatiax/data/results/portfolio_variance_audit/portfolio_variance_feature_ranking_diagnostic.json`

## Interpretation

- Spearman correlation near +1 means the feature's ascending ordering closely
  matches PC1; near -1 means it is nearly reversed.
- Train-membership Jaccard of 1 means the feature alone selects exactly the
  same lower-40% training rows as PC1.
- Row-membership agreement counts agreement on both training and test rows.
- The PC1 cutoff gap and nearby rows help assess how sharply separated the
  observations are around the split boundary.

This is a transductive descriptive analysis, not independent validation or
causal attribution of model performance. Interpret loadings, rank
correlations, and membership metrics together.
