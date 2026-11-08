# Portfolio VaR PCA-tail prediction-error diagnostic

## Purpose

Measure where the benchmark neural network succeeds or fails on the existing 40/60 PCA-directed Portfolio VaR split. Compare it with a constant baseline that predicts the mean target value from the training partition.

This is diagnostic-only. It does not alter the benchmark, change the split, or call the LLM. It reuses the benchmark's `_train_and_eval_nn` helper, including its train-derived feature augmentation and scaling.

## Run in Codespaces

From the repository root on `audit-master`:

```bash
python hypatiax/experiments/benchmarks/portfolio_variance_pca_tail_error_diagnostic.py
```

Optional output override:

```bash
PCA_ERROR_DIAGNOSTIC_OUTPUT=/tmp/portfolio_variance_pca_tail_error_diagnostic.json \
python hypatiax/experiments/benchmarks/portfolio_variance_pca_tail_error_diagnostic.py
```

## Output

`hypatiax/data/results/portfolio_variance_audit/portfolio_variance_pca_tail_error_diagnostic.json`

The JSON contains the PC1 split and loadings; NN seed, training score, test R², MAE, RMSE, bias and runtime; training-target-mean baseline and model-vs-baseline comparison; test error metrics by ascending PC1-score decile; and per-row actual/predicted targets, signed/absolute errors, PC1 scores and features.

## Interpretation

- Negative test R² means the model is worse than predicting the test-target mean; the explicit training-mean baseline is a stricter, deployable comparison.
- Positive mean signed error means overprediction; negative means underprediction.
- Decile-wise MAE/RMSE and signed error reveal where error grows along the PC1 tail.
- If the NN helper times out, that status is recorded and should be considered when interpreting the result.
- This is an NN-only diagnostic. It does not independently reproduce the LLM/hybrid router. It is appropriate for the previously observed `decision="nn"` path; if routing changes in a future run, revisit the diagnostic.

The split remains transductive because PCA is fitted on all feature rows before the train/test boundary is applied.
