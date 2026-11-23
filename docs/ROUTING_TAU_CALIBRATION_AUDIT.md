# Routing degradation-tau calibration audit

**Audit date:** 2026-11-22  
**Code reviewed:** `master` at `86f2cf0cde43da615a82d50e1074cefb8fb6519c`  
**Saved data reviewed:** Exp1 seed-42 artifact from workflow run `45030107321`, artifact `14756779267` (source commit `7b07f560386bcaf8111ce01a678d537e5bd140ad`).  
**Scope:** static code review and analysis of saved training-only diagnostics. No experiment, model/API call, or new seed run was launched.

## Decision

**The saved diagnostics do not support setting `degradation_tau` for the pure-LLM route. Keep `routing_policy.degradation_tau: null` and retain the fail-closed ensemble behavior.**

The main issue is a target mismatch: the diagnostic named `degradation_probe` measures the edge degradation of a newly trained neural network, while the routing policy uses that value as a gate for selecting the LLM formula. It does not measure the LLM formula's own edge degradation. A threshold estimated from this distribution would therefore not calibrate the risk of the route it controls.

## What the implementation measures

In `hypatiax/experiments/benchmarks/hypatiax_defi_benchmark_v3c.py`, `_extrapolation_probe`:

1. Uses only the outer training partition.
2. Splits its covariates into a central PCA region and both edge tails using `training_edge_split_indices`.
3. Trains a fresh NN on the central region (`epochs=200`, hidden layers `[64, 32]`).
4. Computes `delta = NN_R2_core - NN_R2_edge`.

The routing decision then passes this NN-derived delta, together with the LLM formula's training R² and structural-risk flags, to `route_decision_from_diagnostics`. The pure-LLM route requires a passing trust gate, no structural-risk tokens, and `delta <= tau`. The code/configuration correctly fail closed when tau is absent; `config/fresh_rerun.yaml` explicitly marks tau as null and requiring separate training-only calibration.

## Saved-data findings

The canonical seed-42 result contains 74 equation records:

- 51 records have a successful `degradation_probe`; 23 are `trust_gate_failed`.
- Every successful probe used 68 core rows and 12 edge rows.
- Successful-probe delta: median **0.00407**, mean **0.11255**, standard deviation **0.22089**, range **−0.01525 to 0.92499**.
- The distribution is strongly right-skewed: the 90th percentile is **0.26863** and the 95th percentile is **0.66259**.
- At illustrative thresholds, the numbers of successful probes with delta at or below tau are: 30/51 at 0.01, 34/51 at 0.05, 37/51 at 0.10, 42/51 at 0.20, and 46/51 at 0.30.

These are descriptive coverage counts for the **NN probe only**, not candidate tau recommendations. Choosing a quantile would merely choose how many NN probes pass; it would not establish an acceptable false-acceptance rate for pure-LLM routing.

The artifact also contains seed-99, seed-123, seed-777, and seed-2024 result files, but their hybrid records do not include `degradation_probe`, `degradation_tau`, or route-reason diagnostics. They cannot be pooled to estimate cross-seed calibration variability. The seed-42 artifact is therefore the only complete saved routing-diagnostic cohort reviewed here.

## Why the current data cannot calibrate the LLM gate

- The probe's fitted predictor is an NN, not the LLM formula.
- A single seed provides only 51 successful probe records, with only 10 hard-difficulty records.
- The edge sets contain 12 observations each, so individual edge R² values can be unstable.
- The saved LLM training R² values do not provide an independent LLM edge score. Re-evaluating the saved formula on a subset of the same training rows would not be a clean holdout if those rows were available to the formula-generation prompt.
- No predeclared acceptable degradation criterion or independent calibration/evaluation cohort is recorded.

## Required calibration protocol

Before assigning a non-null tau:

1. **Define the estimand:** use the LLM formula's own `delta_llm = R2_core - R2_edge`, not the NN probe delta, if the policy is intended to certify pure-LLM extrapolation.
2. **Prevent leakage:** for each calibration equation, generate or fit the formula using only the central training rows. Keep both edge tails and their labels unavailable to formula generation and fitting. Evaluate the frozen formula on core and edge separately.
3. **Separate calibration from evaluation:** select tau on a predeclared calibration cohort of equations; evaluate the resulting fixed policy on distinct equations and, where appropriate, distinct seeds. Do not tune tau against held-out benchmark test metrics.
4. **Predeclare the acceptance objective:** specify the tolerated edge-degradation risk and uncertainty criterion before looking at the calibration distribution. Do not select tau solely to achieve a desired pass fraction.
5. **Report coverage and uncertainty:** publish sample counts, per-difficulty results, confidence intervals or bootstrap uncertainty at the equation level, failed/undefined probes, and the resulting route counts.
6. **Preserve provenance:** store the split indices or deterministic split specification, formula-generation inputs/provenance, core and edge R², delta, calibration cohort identity, tau, and calibration protocol version in every result record.

The current NN edge probe may remain useful as a separate NN robustness diagnostic. It should not be represented as an LLM-specific degradation measurement.

## Next gate

No code change to routing and no tau value is recommended by this audit. A valid LLM-specific calibration requires formulas generated without access to the edge labels. That entails a separately approved calibration run and may incur LLM API costs. Until that is authorized and completed, leave tau null.
