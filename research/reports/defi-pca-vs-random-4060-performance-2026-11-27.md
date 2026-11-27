# DeFi PCA 40/60 vs random 40/60 benchmark evaluation

**Evaluation date:** 2026-11-27  
**Repository:** `sednabcn/LLM-HypatiaX-REPRO`  
**Branch:** `research/defi-pca-random-4060-comparison`  
**Scope:** Three supplied GitHub Actions runs: `exp1_pca`, `exp1b_pca`, and `exp1_4060_seeds`.

## Executive summary

All three workflow runs completed successfully. The strongest comparable performance evidence is the five-seed `exp1b_pca` PCA-directed benchmark versus the five-seed `exp1_4060_seeds` random 40/60 benchmark.

The random 40/60 experiment has a substantially higher mean held-out hybrid R² in the per-seed logs (approximately **0.816**, versus **0.083** in the PCA pooled report). The PCA experiment does, however, produce **35/365** finite case-seed hybrid scores at or above the exceptionally strict threshold (R^2 \ge 0.999999) (**9.59%**), while the random experiment reports **0/370** at that same threshold. These findings are not contradictory: a small number of near-perfect PCA cases coexist with a much poorer overall PCA score distribution.

**Interpretation:** on the available aggregate evidence, random 40/60 is the stronger and more stable broad predictive split. PCA-directed 40/60 appears to create a harder tail/generalisation problem, with a small subset of near-perfect outcomes but poor aggregate held-out performance. The strict-threshold pass count alone should not be used to claim PCA superiority.

## 1. Workflow execution and provenance

| Experiment | Run | Workflow conclusion | Execution evidence |
|---|---|---:|---|
| `exp1_pca` | [46056848315](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/46056848315) | Success | Five worker shards succeeded; aggregate validation succeeded; manifest records 370 validated records across seeds 42, 99, 123, 777, 2024 |
| `exp1b_pca` | [46054046731](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/46054046731) | Success | Five-seed PCA 40/60 run completed; summary validates 370 case records |
| `exp1_4060_seeds` | [46054191107](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/46054191107) | Success | Five isolated random-split workers succeeded; aggregate validation succeeded; 370 records |

### Important seed-input discrepancy

The `exp1_pca` run URL was described as “seed=42”, but the run's committed `pca_seed_aggregate_manifest.json` records all five expected and validated seeds: **42, 99, 123, 777, 2024**, with 74 cases per seed (370 records total). The Actions job list likewise shows five PCA worker shards. Therefore this workflow dispatch did **not** execute seed 42 alone; it executed the five-seed sweep.

The manifest is tied to run `46056848315` and commit `bb5dd6a5553fab75182e6cb77f95ae19a6b6ea32`. The nearby `exp1_pca_summary.json` in the result directory has a timestamp of 2026-09-19 and is stale relative to this 2026-11-27 run. Its historical 51/74 result is **not** treated as a metric for run 46056848315.

## 2. Comparable five-seed metric results

### PCA-directed 40/60: `exp1b_pca`

Source: `hypatiax/data/results/comparison_results/noise-noiseless/15_pca/exp1b_pca_summary.json`, plus `hypatiax_defi_benchmark_pca_pooled_seed_report.json`.

- Split: PCA-directed 40% train / 60% test.
- Seeds: 42, 99, 123, 777, 2024.
- Records validated: 370 (74 per seed).
- Finite hybrid held-out R² values: 365 (73 per seed).
- One case per seed, “Optimal LP Position (Kelly)”, has undefined R² because the target is constant; these five undefined values are excluded from the denominator.
- Threshold used by the validator: hybrid held-out (R^2 \ge 0.999999). This is a near-perfect predictive-R² threshold, **not** symbolic equivalence.

| Seed | Near-perfect cases | Finite cases | Rate |
|---:|---:|---:|---:|
| 42 | 8 | 73 | 10.96% |
| 99 | 7 | 73 | 9.59% |
| 123 | 5 | 73 | 6.85% |
| 777 | 7 | 73 | 9.59% |
| 2024 | 8 | 73 | 10.96% |
| **Total** | **35** | **365** | **9.59%** |

The pooled report gives the mean of per-seed mean held-out R² values:

| Model arm | Mean of seed means (raw R²) | SD across seed means |
|---|---:|---:|
| Pure LLM | -324,054.313 | 340,727.858 |
| Neural network | -31.441 | 17.778 |
| Hybrid | **0.0832** | **0.0162** |

The very negative pure-LLM and neural-network means indicate severe failures/outliers on some held-out cases; raw R² is unbounded below, so means can be dominated by catastrophic cases. The hybrid arm is markedly better than those two arms, but its mean held-out R² remains low.

### Random 40/60: `exp1_4060_seeds`

Sources: `exp1_4060_seeds_summary.json` and the five per-seed run logs under `hypatiax/data/results/comparison_results/noise-noiseless/noiseless/defi_random_4060/`.

- Split: seeded random 40% train / 60% test.
- Seeds: 42, 99, 123, 777, 2024.
- Records: 370 finite hybrid held-out R² values (74 per seed).
- At the same strict threshold (R^2 \ge 0.999999): **0/370**.
- The workflow summary explicitly defines this threshold metric as a predictive score, not symbolic equivalence.

The per-seed logs print hybrid test R² to four decimal places. The approximate per-seed mean values computed from those displayed log values are:

| Seed | Mean hybrid test R² (approx.) | Cases with displayed R² ≥ 0.99 |
|---:|---:|---:|
| 42 | 0.8535 | 50/74 |
| 99 | 0.8153 | 50/74 |
| 123 | 0.7946 | 50/74 |
| 777 | 0.8681 | 52/74 |
| 2024 | 0.7497 | 46/74 |
| **Mean across seed means** | **0.8162** | **248/370 (67.03%)** |

The ≥0.99 counts above are based on four-decimal log output and are descriptive only. The authoritative exact aggregate in the committed summary is the strict (R^2 \ge 0.999999) count of 0/370.

## 3. Head-to-head interpretation

### Overall held-out fit

The PCA pooled hybrid mean of seed means is approximately **0.0832**. The random-split mean calculated from rounded per-seed log output is approximately **0.8162**. This is a large difference in favour of random 40/60 on average held-out predictive fit.

The comparison is not perfectly precision-matched: the PCA mean comes from a JSON aggregate, while the random mean is reconstructed from log values rounded to four decimals. It is nevertheless sufficiently large to support a directional conclusion, not a fine-grained significance claim.

### Near-perfect tail of the score distribution

At the strict (R^2 \ge 0.999999) threshold:
- PCA-directed: 35/365 = **9.59%**.
- Random: 0/370 = **0%**.

This metric captures the fraction of cases reaching an almost exact predictive fit. It does not measure the typical case and is not symbolic-equivalence validation. PCA has a small near-perfect subset, but that subset does not offset its poor mean hybrid R².

### Seed sensitivity

The PCA strict-threshold rate ranges from 6.85% to 10.96% across the five seeds. Random-split mean hybrid R² ranges approximately from 0.750 to 0.868 across seeds. The random results show higher average test fit in every seed's reported mean; the PCA summary's per-seed pass rates are comparatively low and narrow.

### What the runs do and do not establish

- They establish successful execution and complete five-seed record coverage for the PCA and random experiments.
- They support a descriptive comparison of the hybrid held-out R² distributions using the metrics above.
- They do not establish statistical significance; there are five seeds and no paired bootstrap or confidence interval for this full 74-equation comparison.
- They do not establish symbolic recovery or equation equivalence. Predictive R² and symbolic correctness are different outcomes.
- The random logs' four-decimal precision prevents exact recomputation of thresholds such as 0.99 from those logs; use the persisted raw JSON records for exact distributional analysis.
- The current `exp1_pca` run's aggregate manifest proves 370 records were validated, but its colocated summary JSON is stale. Do not quote the historical 51/74 summary as the current run's result.

## 4. Conclusions

1. **Random 40/60 is the stronger default generalisation benchmark** on the current aggregate hybrid-R² evidence: its mean held-out score is substantially higher than the PCA-directed result.
2. **PCA-directed 40/60 is a useful stress test**, likely exposing difficult tail/extrapolation behaviour. Its 9.59% near-perfect fraction should be reported alongside—not instead of—the full score distribution.
3. **Do not interpret the strict-threshold pass rate as symbolic solve rate.** Rename this quantity in future reports to “near-perfect held-out R² rate” and separately measure symbolic equivalence.
4. **Fix the `exp1_pca` seed dispatch contract.** The requested seed=42 was not honoured by the observed five-shard workflow; either wire the input seed list through the planner or label the dispatch as a five-seed sweep.
5. **Regenerate a current `exp1_pca` metric summary** from the run 46056848315 result records. Keep the run manifest, per-seed metrics, undefined-metric accounting, and exact score distributions together.

## 5. Reproducibility sources

- [Run 46056848315 — exp1_pca](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/46056848315)
- [Run 46054046731 — exp1b_pca](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/46054046731)
- [Run 46054191107 — exp1_4060_seeds](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/46054191107)
- [PCA aggregate summary](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/master/hypatiax/data/results/comparison_results/noise-noiseless/15_pca/exp1b_pca_summary.json)
- [PCA pooled seed report](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/master/hypatiax/data/results/comparison_results/noise-noiseless/15_pca/hypatiax_defi_benchmark_pca_pooled_seed_report.json)
- [Random 40/60 aggregate summary](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/master/hypatiax/data/results/comparison_results/noise-noiseless/noiseless/defi_random_4060/exp1_4060_seeds_summary.json)
- [PCA five-seed manifest for run 46056848315](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/master/hypatiax/data/results/comparison_results/noise-noiseless/noiseless/defi_pca/pca_seed_aggregate_manifest.json)

---
*Prepared from the committed run metadata, experiment summaries, pooled report, split disclosures, and per-seed random-run logs available on 2026-11-27. Approximate values and known provenance limitations are explicitly identified above.*
