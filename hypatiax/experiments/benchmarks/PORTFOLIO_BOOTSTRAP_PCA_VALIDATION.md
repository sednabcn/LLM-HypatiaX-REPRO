# Portfolio bootstrap-PCA partition validation

This experiment addresses the limitation of the original PCA seed sweep: all
five model-seed runs reused one fixed full-data PCA partition. It varies the
estimated PC1 direction through repeated row-bootstrap samples while holding
the model seed fixed.

## Protocol

For each bootstrap seed:

1. Draw a bootstrap sample with replacement. By default its size is n; set
   `BOOTSTRAP_PCA_SAMPLE_FRACTION` below 1 to run an explicitly labeled
   m-out-of-n bootstrap sensitivity variant.
2. Fit one-component PCA on that bootstrap sample, using raw unstandardized features.
3. Project all n feature rows onto the fitted PC1 direction.
4. Orient PC1 so its largest-absolute loading is positive, then stably sort all rows.
5. Use the lower 40% for training and upper 60% for testing.
6. Reset the model seed to the same fixed value and evaluate with the existing benchmark helper.

Because the full feature matrix is projected and ranked, this remains a **transductive** split-design procedure. The bootstrap replicates are distinct stochastic estimates of the PC1 direction; they are not statistically independent datasets, and this experiment should be described as a bootstrap sensitivity analysis rather than independent external validation.

## Run locally

From the repository root on `audit-master`:

```bash
MODEL_SEED=42 BOOTSTRAP_PCA_SEEDS=11,23,42,77,101 \
  python hypatiax/experiments/benchmarks/portfolio_variance_bootstrap_pca_validation.py
```

To keep the standard size-n bootstrap:

```bash
MODEL_SEED=42 BOOTSTRAP_PCA_SEEDS=11,23,42,77,101 \
  BOOTSTRAP_PCA_SAMPLE_FRACTION=1.0 \
  python hypatiax/experiments/benchmarks/portfolio_variance_bootstrap_pca_validation.py
```

To test a smaller m-out-of-n resample (for example, 70% of the rows):

```bash
MODEL_SEED=42 BOOTSTRAP_PCA_SEEDS=11,23,42,77,101 \
  BOOTSTRAP_PCA_SAMPLE_FRACTION=0.7 \
  python hypatiax/experiments/benchmarks/portfolio_variance_bootstrap_pca_validation.py
```

The output records both the bootstrap-sample fingerprint and final partition
fingerprint, plus PC1 rank correlation, loading distance, and train-membership
Jaccard similarity against the first replicate. Thus different bootstrap draws
can be distinguished from genuinely different PC1 rankings and partitions.

Output:

`hypatiax/data/results/portfolio_variance_audit/portfolio_variance_bootstrap_pca_validation.json`

## Run manually in GitHub Actions

Use **Actions → Portfolio bootstrap PCA validation → Run workflow** on
`audit-master`. The workflow is manual-only and is not dispatched by this
change. Defaults are bootstrap seeds `11,23,42,77,101` and model seed `42`.

## Score semantics and interpretation

- `tail_test_r2` is the test R² from the selected benchmark route, recorded in `test_r2_source`.
- `llm_train_r2` is the LLM formula's training R² only. NaN means unavailable/invalid and is not neural-network training failure.
- `success_tail_test_r2_gt_0_99` records whether tail test R² exceeds 0.99.
- Do not pool these results with random-holdout interpolation scores.
- Compare the distribution of bootstrap-PC1 tail scores with the original fixed-PC1 result, while reporting that the split estimator has changed.
- This experiment does not replace the original PCA sweep or change any historical split default.
