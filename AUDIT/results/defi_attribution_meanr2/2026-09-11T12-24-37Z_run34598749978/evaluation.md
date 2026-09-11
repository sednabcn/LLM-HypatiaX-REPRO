# FIX-D2 DeFi Mean R2 evaluation

**Verdict: SIGN_REVERSAL_FAILS**

Attribution-corrected Mean R2 (-2.0665) is negative on the 5-seed average, undercutting the paper's claimed sign reversal (negative -> +0.8721). Raw Mean R2 was outside tolerance of the printed figure, but the sign-reversal claim itself does not survive attribution correction.

| | Paper (printed) | FIX-D2 raw | FIX-D2 corrected |
|---|---:|---:|---:|
| Mean R2 | 0.8721 | 0.8989 | -2.0665 |

- Raw matches paper within tolerance (0.01): **False**
- Sign reversal holds (corrected > 0): **False**
- Aggregation check (mean-of-seed-means vs micro-average): identical (A=B=0.8989 -- not the explanation for any gap)
- Seed source dir: `hypatiax/data/results/comparison_results/noise-noiseless/15_pca`
- Filename pattern: `hypatiax_defi_benchmark_pca_results_seed%s.json`
- Seeds scored: [42, 99, 123, 777, 2024]
- Workflow run: https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/34598749978
- Commit: 0b391627b47321a3d8d4f37cec2c67f659a6cacd
