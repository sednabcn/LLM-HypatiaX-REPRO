# Independent partition validation

The PCA seed sweep used one fixed, transductive PC1-tail split. The
`portfolio_variance_partition_validation.py` runner adds a separate
random-holdout control with independently sampled 40/60 partitions.

Run from the repository root on `audit-master`:

```bash
MODEL_SEED=42 PARTITION_SEEDS=11,23,42,77,101 \
  python hypatiax/experiments/benchmarks/portfolio_variance_partition_validation.py
```

The runner uses the same Portfolio VaR case and the benchmark's
`_hybrid_predict_and_eval` implementation. It fixes the model seed at 42
while varying only the row-partition seed, and writes:

`hypatiax/data/results/portfolio_variance_audit/portfolio_variance_random_holdout_validation.json`

This is a **random-holdout interpolation/control**, not PC1-directed
far-range extrapolation. Report its scores separately from the
`pca_40_60_pc1` results. It is non-transductive because no PCA fit on the
full feature matrix is used to construct these holdouts.

The runner is opt-in and is not dispatched automatically by the existing
portfolio workflow. It does not modify the historical split default or
replace the existing PCA sweep.
