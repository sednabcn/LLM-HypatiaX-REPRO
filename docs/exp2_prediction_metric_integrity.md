# Exp2 prediction-metric integrity

## Problem

Some method adapters accepted backend-reported aggregate R²/RMSE even when
row-level predictions were present. In the DeFi adapter, metrics were only
recomputed when the reported R² was exactly zero. This made nonzero but stale
or inconsistent backend metrics survive despite having the predictions needed
to calculate the metrics directly.

The DeFi path also had a synthetic-prediction fallback derived from aggregate
R²/RMSE. Such a vector is not a model prediction and must not be used for
residual fitting or reported as an observed prediction route.

## Corrected policy

For EnhancedHybridSystemDeFi and HybridSystemLLMNN:

1. Prefer actual row-level predictions from the selected evaluation result,
   then top-level result predictions, then a replayable symbolic formula where
   that is the method's real prediction route.
2. Require exactly one prediction per target row and finite targets and
   predictions.
3. Recompute R² with the canonical R² scorer and RMSE from the same aligned
   target/prediction vectors. Do this even when backend R² is nonzero.
4. When a residual correction is accepted, recompute both metrics from the
   corrected in-sample predictions, after checking shape and finiteness.
5. Never reconstruct or fabricate a prediction vector from aggregate R²/RMSE.
6. If row-level predictions are unavailable but finite aggregate metrics were
   reported, preserve them with metric_verification_status set to
   reported_without_row_predictions. They are explicitly unverified, not
   silently described as recomputed.
7. If row-level predictions are malformed, do not fall back to backend
   aggregate values as though they had been verified. Invalid metrics remain
   unavailable or the method result is marked unavailable.

The flat extrapolation artifact carries metric_verification_status so
consumers can distinguish recomputed metrics from unverified backend values.

## Scope

This change does not launch experiments, fit models beyond the method's
existing explicitly invoked residual-correction path, call an LLM, or alter
the far-region split/scorer. It corrects the reported in-sample method metrics
when actual predictions are available and makes unverifiable cases explicit.

Offline tests cover canonical R²/RMSE recomputation, shape mismatch, and
non-finite inputs. CI is the verification mechanism; no local tests were run
while preparing this change.