# Exp2 PCA holdout: historical audit and evaluation correction

## Purpose

This note records why the historical Exp2 PCA headline of **71/90 (78.9%)** was not a valid estimate of the two intended methods' held-out performance, what PR [#124](https://github.com/sednabcn/LLM-HypatiaX-REPRO/pull/124) changed, and what evidence is still needed before making a recovery-rate claim.

PR #124 was merged into `master` on 2026-11-16. Merge commit:
`b805680202c5e37a9d9526a6e4220e82bb4adad7`.

## 1. Why the historical 71/90 headline was invalid

The historical PCA summary reported 71/90 = 78.9% at the strict recovery threshold R² ≥ 0.999999. Its three contributing method counts were:

| Historical summary entry | Passes | Eligibility |
|---|---:|---|
| Enhanced Hybrid | 23/30 | Eligible method |
| Hybrid Discovery v50.2 | 18/30 | Eligible method |
| HybridSystemLLMNN all-domains | 30/30 | **Ineligible**: marked `unverified_no_formula` and `exclude_from_reported_results=true` |
| **Historical headline** | **71/90** | **Invalid as a headline for the two eligible methods** |

The summary aggregation selected a generic `hybrid` method name, which also matched the all-domains HybridSystemLLMNN record. It did not apply the row-level exclusion/provenance flags. The resulting 71/90 combined numerator and denominator therefore included 30 unverified records.

The defensible historical counts for the two intended methods are **23/30 Enhanced Hybrid** and **18/30 Hybrid Discovery v50.2**. They should be shown as separate method rates, not combined into a new pooled percentage unless a pooled estimand is explicitly justified.

There was a second, more fundamental measurement issue: the previous summary scan could prefer the per-method `r2` field, which represents the method's ordinary evaluation result, rather than the explicit `pca_test_r2` score for the PCA holdout. A headline derived from the wrong score field is not evidence of generalization to the PCA holdout.

Historical sources:
- [Historical PCA summary](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/master/hypatiax/data/results/comparison_results/feynman-tests/exp2_pca_4060/exp2_pca_4060_summary.json)
- [Historical PCA result rows](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/master/hypatiax/data/results/comparison_results/feynman-tests/exp2_pca_4060/benchmark_results_pca_4060.json)
- [PCA split disclosure](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/master/hypatiax/data/results/comparison_results/feynman-tests/exp2_pca_4060/split_protocol_disclosure.json)

## 2. Split metadata correction

The historical split disclosure specifies **40% training and 60% test/holdout**. The prior summary's `extrap_train_frac: 0.6` was inconsistent with that disclosure. PR #124 corrects the summary metadata to represent 40% training and 60% PCA holdout.

Do not pool these PCA results with the separate Exp2 extrapolation run: that run uses a different protocol (80/20 train/test with extrapolation multiplier 2.0).

## 3. Changes merged in PR #124

### 3.1 Score the actual PCA holdout

The PCA summary now reads the per-equation `pca_test_r2[method]` value. It no longer treats the ordinary `r2` field as a substitute for the PCA holdout score.

For each eligible method:
- Keep the expected equation denominator fixed.
- Count missing, failed, or non-finite holdout scores as failures.
- Require complete method coverage before declaring the protocol complete.
- Reject duplicate equation records within a source file.
- When historical rerun files overlap, retain the latest timestamped record for each domain/equation pair and disclose how many earlier records were superseded.
- Report Enhanced Hybrid and Hybrid Discovery v50.2 as the target comparison; exclude the unverified all-domains/no-formula entry.

The flat results export now includes PCA holdout score, split details, external-holdout status/error, provenance status, and exclusion status.

### 3.2 Make Enhanced Hybrid's holdout prediction replayable

The adapter now attempts to preserve the route selected by EnhancedHybridSystemDeFi on training data:
- fitted symbolic formula;
- fitted neural network with its training scalers; or
- formula/NN ensemble using the selected blend weights.

The former synthetic reconstruction of predictions from summary metrics (R²/RMSE) is removed. The holdout must be scored by applying the selected predictor to the held-out feature matrix. If a reusable predictor is unavailable or cannot be evaluated, that is reported as unavailable/failure rather than silently manufacturing a score.

### 3.3 Expand and disclose Hybrid Discovery v50.2 search

The v50.2 PySR grammar now includes the binary power operator `^`, in addition to `+`, `-`, `*`, and `/`, with `sqrt` as the configured unary operator.

The bounded search configuration allows up to two attempts of 325 seconds each under the existing 900-second method ceiling, and records the effective iteration/time/retry/operator configuration in result metadata. This is a search-budget and grammar improvement, not a guarantee that every equation will be recovered.

## 4. What this does—and does not—establish

PR #124 corrects the measurement path and changes the method implementations so that the intended predictors can be evaluated on the actual PCA holdout. It does **not** establish that either method now reaches 100%.

No new 30-equation PCA experiment was launched as part of the PR. Regression tests were added, but the PR's code changes and CI checks are not a substitute for a full pipeline result.

The official evidence for any improvement must come from the full PCA pipeline rerun with:
1. a fresh, isolated output/checkpoint location (avoid stale `--resume` artifacts);
2. all 30 expected equations;
3. complete per-method coverage for both eligible methods;
4. per-equation PCA holdout R², failure reasons, and provenance;
5. the fixed R² ≥ 0.999999 threshold reported alongside secondary thresholds if desired;
6. no test/holdout leakage into formula discovery, fitting, model selection, or tuning.

Report each method's `n_pass / n_total` separately. A 100% claim requires **30/30 finite, eligible PCA holdout scores at or above the predeclared threshold**, with all exclusions and failures visible. Do not change the threshold, remove difficult equations, or use training R² to reach that number.

## 5. Key repository references

- [PR #124 — Fix PCA holdout evaluation and improve symbolic search](https://github.com/sednabcn/LLM-HypatiaX-REPRO/pull/124)
- [Merged implementation commit](https://github.com/sednabcn/LLM-HypatiaX-REPRO/commit/b805680202c5e37a9d9526a6e4220e82bb4adad7)
- [PCA holdout summary utility](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/master/scripts/ci/summarize_pca_holdout.py)
- [PCA benchmark adapter](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/master/hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_pca.py)
- [PCA holdout regression tests](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/master/hypatiax/experiments/tests/test_pca_holdout_contract.py)

---
*Documentation status: historical audit and implementation record. The post-fix 30-equation performance remains unmeasured until the official full PCA pipeline rerun completes.*
