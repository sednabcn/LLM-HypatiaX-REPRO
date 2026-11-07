# Portfolio Variance PCA seed-sweep aggregate

**Branch:** `audit-master`  
**Workflow:** [Run #199](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/42410055833) — completed successfully  
**Case:** `risk_var` / Portfolio VaR for two correlated assets  
**Protocol:** `pca_40_60_pc1` (raw, unstandardized, transductive PCA split)

## Aggregate

| Seed | Train R² | Far R² | Success | Runtime (s) |
|---:|---:|---:|:---:|---:|
| 42 | 1.000 | 1.000 | Yes | 1.368 |
| 99 | 1.000 | 1.000 | Yes | 1.360 |
| 123 | 1.000 | 1.000 | Yes | 1.875 |
| 777 | 1.000 | 1.000 | Yes | 1.433 |
| 2024 | 1.000 | 1.000 | Yes | 1.335 |
| **Mean** | **1.000** | **1.000** | **5/5 (100%)** | **1.474** |
| **Sample SD** | **0.000** | **0.000** | — | **0.227** |

## Protocol audit

- 200 samples: 80 train / 120 test (40/60).
- PCA fit on raw, unstandardized features; no scaling.
- Split random state is **42 in every seed file**. The five runs vary the model/experiment seed, not the train/test partition.
- The split is **transductive**: PCA is fitted using all 200 feature rows before the split.
- PC1 explained-variance ratio: **1.000**.
- PC1 loadings: `var_asset1=0.857493`, `var_asset2=0.514496`, `correlation=0.00002668`. The direction is overwhelmingly driven by the two asset-variance features.

## Interpretation

All five configured seeds succeeded with exact reported train and far R². This is a consistent result for this case under the selected PCA protocol and fixed partition. It is **not** evidence of robustness across independently randomized partitions, nor should it be conflated with the legacy first-feature split.

The portfolio workflow was run in sweep-only mode. This aggregate does not claim that downstream paper tables, LaTeX exports, or figures were generated. The existing portfolio export section uses legacy seed-sweep inputs and assumptions; it should not be run unchanged against these PCA seed files.

## Raw inputs

- `portfolio_variance_defi_seed_sweep_seed42.json`
- `portfolio_variance_defi_seed_sweep_seed99.json`
- `portfolio_variance_defi_seed_sweep_seed123.json`
- `portfolio_variance_defi_seed_sweep_seed777.json`
- `portfolio_variance_defi_seed_sweep_seed2024.json`

Machine-readable companion: [portfolio_variance_pca_seed_aggregate.json](portfolio_variance_pca_seed_aggregate.json).
