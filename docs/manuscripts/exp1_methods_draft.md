# Exp1 manuscript draft — methods and reproducibility

> **Status: working draft, not publication-ready.** This text is derived from the exp1 implementation on PR #313, branch `fix/exp1-llm-attempt-provenance`. It is not evidence that the benchmark was executed, and it contains explicit author-verification items. No experiment, benchmark, or live LLM request was run to prepare this draft.

## 1. Benchmark design

Exp1 evaluates formula learning and extrapolative prediction on a collection of decentralised-finance (DeFi) mathematical tasks. The canonical runner is `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py`. Each configured test case specifies a quantity description, DeFi domain, difficulty, formula family, sample count, and split configuration. The case definitions currently specify 200 samples per case.

The principal comparison represented in the runner is between a neural-network predictor and a hybrid method that combines an LLM-generated candidate formula with a neural network. The runner does not include a separate standalone pure-LLM comparison arm in its current result/report path. The LLM is used inside the hybrid pipeline.

**Source-level denominator audit:** the current `_get_test_cases()` catalogue contains 74 entries. None of those entries sets `extrapolation_intractable`, so `_INTRACTABLE_NAMES` is empty and `_STANDARD_TOTAL` resolves to 74 in this source revision. This resolves the code-level catalogue/denominator count; it does not prove that a particular saved run contains all 74 cases. Before publishing any aggregate result, verify that the canonical run artifact contains the intended 74 unique cases, with no omissions or duplicates, and that its recorded protocol/configuration matches this source revision. Task inclusion rules and sample-generation distributions still require protocol-source verification.

## 2. Extrapolation split

For each case, the runner requests an aggressive 40/60 train/test partition. The configured primary-feature split selects the feature column identified by the case configuration and computes the 40th percentile of that feature. Rows at or below the threshold form the training partition; the remaining rows form the held-out test partition. The split audit records the requested and realized split method, selected feature, threshold/quantile, selection rule, fallback status and reason, and realized partition sizes.

A compatibility fallback is retained for cases where the primary-feature percentile partition would contain fewer than 20 rows. In that condition, the implementation uses the historical row-index 40/60 partition and labels it explicitly as a `row_index_fallback`, with the reason `percentile_partition_has_fewer_than_20_rows`. The fallback is not silently described as a feature-based extrapolation split. Both the primary and fallback paths preserve the 40/60 target sizes where the configured sample count permits it.

The case artifact records the split protocol and explicit train/test sizes. This makes the realized split auditable and supports rescoring on the same partition.

## 3. Neural-network predictor

The benchmark's self-contained neural network is a multilayer perceptron with hidden widths 128, 64, and 32, using linear layers, layer normalization, and SiLU activations, followed by a scalar output layer. The implementation also includes optional physics-informed feature augmentation (logarithmic, square-root, and, for two-feature inputs, ratio features). The transform-eligibility schema is fitted from training rows and then applied consistently to the test rows; held-out rows do not determine which transforms are included.

Training uses an Adam optimizer (learning rate 0.001) and mean-squared-error loss for up to 300 epochs, with hidden widths [128, 64, 32]. Inputs and targets are standardized using scalers fitted on the training partition. The default neural-network seed is derived from the experiment seed (seed 42 gives NN seed 2024); NumPy and PyTorch are re-seeded for each fit. The implementation applies a 120-second wall-clock cap, checked every 25 epochs, and records whether the cap was reached. Physics-informed log, square-root, and (for two-feature inputs) ratio features are enabled by default; transform eligibility is determined from training rows only. The routing edge probe is a separate fit with 200 epochs and hidden widths [64, 32], using the outer training partition only. Actual per-case timeout counts still require the canonical run artifacts.

## 4. LLM formula generation and trust assessment

Within the hybrid method, the LLM receives the task description, domain, variable names, and any declared constants, and is asked to return a Python function named `formula`. The prompt is constructed without passing the ground-truth formula. The configured model identifier in the runner is `claude-sonnet-4-6`. The request timeout is controlled by `LLM_METHOD_TIMEOUT` (default 120 seconds), and the Anthropic client is configured with SDK retries disabled (`max_retries=0`), so the runner records a single attempted request rather than silently retrying through the SDK.

A generated formula is evaluated on training data before it can be trusted. The current trust gate requires a valid evaluated formula, training (R^2 \geq 0.5), and absence of the implementation's specified pathological code patterns. Structural-risk detection has priority and sends flagged formulas to the ensemble path. When the formula is not trusted, the neural-network fallback path is used.

The routing policy also computes a training-only neural-network edge-degradation probe. This probe partitions only the outer training data into a central fit subset and two edge subsets, fits the probe model on the central subset, and compares its training-region and edge-region (R^2). The canonical `config/fresh_rerun.yaml` currently sets `routing_policy.degradation_tau: null` and marks it as requiring separate training-only calibration. In that configuration the LLM-only route fails closed and the ensemble route is used; the manuscript must not imply that a calibrated LLM-only route was evaluated. A non-null environment override would need to be evidenced by the specific run manifest before describing a different routing policy.

## 5. OOD diagnostics and held-out covariate access

The hybrid method fits its kernel-density OOD reference using (X_{train}) and queries the fitted diagnostic using (X_{test}) at prediction time. The resulting per-query OOD probabilities determine the blend weights:

\[
w_{LLM}(x)=0.3+0.7p_{OOD}(x),\qquad
w_{NN}(x)=1-w_{LLM}(x).
\]

If the returned per-query probabilities are missing, mis-sized, non-finite, or outside ([0,1]), the implementation substitutes zero OOD probability for those queries, corresponding to the in-distribution LLM-weight floor of 0.3.

This is **query-time covariate access to held-out (X_{test})**. It is not a fully covariate-blind evaluation and should not be described as strictly inductive with respect to test covariates. The routing and blend-weight logic does not use (y_{test}). Held-out labels are used for final predictive evaluation metrics, not to select the route or query-level blend weights. The saved audit payload retains both train and test arrays, including (y_{test}), to support independent rescoring; retention in the artifact should not be confused with use in routing.

## 6. Evaluation and recorded provenance

The implementation computes (R^2), mean absolute error, root mean squared error, and mean absolute percentage error for predictions. The benchmark report emphasizes test (R^2), including per-case and difficulty-level summaries. Failed or unavailable metrics must remain identifiable as failures rather than being silently converted into successful scores.

For each case, the saved record includes the method results, realized split metadata and sizes, formula context (variable names, declared constants, and model identifier), the train/test audit arrays, and the seed. Hybrid records also retain the generated formula when available, training fit information, route/decision information, OOD diagnostics and query-time covariate protocol metadata. LLM provenance includes whether a request was actually attempted, bypass classification, source, timeout, requested/sent temperature information, and any available formula. The outer exception path preserves attempt provenance if a later hybrid operation fails.

## 7. Reproducibility and limitations

The current implementation and offline regression tests establish software-level contracts for split auditing, OOD covariate-scope metadata, request-attempt provenance, and persistence of that metadata in case artifacts. These checks do not establish benchmark performance and do not replace an actual, protocol-compliant experiment run. No performance result, aggregate score, runtime comparison, or superiority claim should be inserted into the manuscript without the corresponding verified experiment artifacts and analysis.

The present method has an explicit transductive/query-time covariate component: the fitted OOD diagnostic is queried with held-out feature vectors. This access must be disclosed. The held-out target labels are excluded from routing and blending but are used for final scoring and are retained in the audit artifact.

## 8. Items to complete before submission

1. Source-level count is verified as 74 catalogue entries, zero flagged intractable, and `_STANDARD_TOTAL = 74`. Still verify 74 unique case records in the canonical run artifact and confirm that the artifact was generated from this protocol revision.
2. Confirm the data-generation distributions, units, constants, and feature definitions for every task from the protocol source; add a table of cases and mathematical ground-truth definitions where appropriate.
3. The source-level neural-network settings are now documented above; extract per-case timeout/failure counts from the canonical run artifacts before submission.
4. The checked-in fresh-rerun configuration sets `degradation_tau` to null, so the default fresh-rerun policy is ensemble-only. If the reported run used an environment override, its value and training-only calibration provenance must be recovered from that run's manifest; otherwise explicitly report that the calibrated LLM-only route was not evaluated.
5. Verify the exact software versions, hardware, seed(s), and environment variables from the run manifest/logs.
6. Add results only from the canonical, verified experiment artifacts. The offline CI tests are protocol/software checks, not experimental results.
7. Ensure the manuscript consistently describes KDE as fitted on (X_{train}) and queried with (X_{test}) covariates, without claiming that all held-out information is inaccessible.

## Implementation and verification references

- Canonical runner: `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py`
- Offline protocol/provenance tests: `hypatiax/experiments/tests/test_exp1_submission_blockers.py` and `hypatiax/experiments/tests/test_exp1_llm_attempt_provenance.py`
- Exp1 PR: https://github.com/sednabcn/LLM-HypatiaX-REPRO/pull/313
- Latest previously verified dedicated exp1 CI step: 13 passed, 1 deselected (workflow run 44899296673). This is an offline test result, not a benchmark result.
