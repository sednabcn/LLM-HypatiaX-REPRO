# Exp2 final-predictor consistency and error-ratio coverage

## Status and purpose

This document specifies the investigation and proposed repair for missing
`error_pct` values in the Exp2 Feynman extrapolation evaluation, especially
for methods that contain a neural-network (NN) component.

It is a design and implementation guide, not a claim that the repair is already
implemented. The current 3-equation × 6-method smoke result of 6/18 non-null
`error_pct` values is historical evidence that motivated this work. It is not
a post-fix result and must not be used to assess the later shared-core changes.

The immediate objective is to increase *valid metric coverage* by ensuring
that the exact final fitted method can be evaluated on both the extrapolation
training rows and the far rows. The objective is not to force all 18 ratios to
be non-null: some ratios are mathematically undefined, notably when training
RMSE is zero.

No far-region fitting, retraining, tuning, synthetic prediction reconstruction,
or substitution of ground-truth equations is permitted to increase coverage.

## 1. Metric definition and interpretation

The existing metric is

```text
error_pct = 100 * RMSE_far / RMSE_train
```

where both RMSE values must be computed from predictions made by the same
method/predictor, with the same fitted state and compatible input semantics.

This metric is a far-to-training RMSE ratio expressed as a percentage. It is
not conventional percentage prediction error, MAPE, or a percentage of
individual targets.

Interpretation:

- `error_pct = 100`: far RMSE equals training RMSE.
- `error_pct > 100`: far RMSE is larger than training RMSE.
- `error_pct < 100`: far RMSE is smaller than training RMSE.
- `error_pct = 0`: far predictions are exact, provided the denominator is
  positive.
- `error_pct = null`: the ratio could not validly be computed; inspect the
  status rather than treating every null as the same failure.

If `RMSE_train = 0), the ratio is undefined. Do not add an arbitrary epsilon,
replace the denominator, or silently clamp the result. Preserve far R² and
far RMSE if those metrics are valid.

## 2. The consistency invariant

For a method whose final fitted predictor is (f_{final}), calculate:

```text
yhat_train = f_final(X_train_exact)
yhat_far   = f_final(X_far)
RMSE_train = RMSE(y_train_exact, yhat_train)
RMSE_far   = RMSE(y_far, yhat_far)
error_pct  = 100 * RMSE_far / RMSE_train, if RMSE_train > 0
```

The same predictor object, model weights, preprocessing state, feature
ordering, feature transformations, output transformation, and row semantics
must be used for both calls.

The training baseline must use exactly the rows that formed the extrapolation
training partition. It must not use the far rows, external holdout rows, or
the full dataset if that includes held-out far observations.

For a composite method, `f_final` means the complete deployed composition,
not merely one component. For example:

```text
base prediction -> residual NN correction -> final prediction
```

Both training and far predictions must pass through that entire composition.

## 3. Findings from the current implementation

The following observations were made from the current shared core and the two
Exp2 runners during this documentation pass. They describe the code inspected
on the branch used for this document; they are not a substitute for future
runtime diagnostics.

### 3.1 Shared scorer

`hypatiax/experiments/benchmarks/exp2_extrapolation_core.py`:

- Prefers a caller-supplied `y_pred_train[method]` when present.
- Otherwise evaluates a retained `_predict_fn` on
  `X_train_predictor`.
- Uses the retained predictor for far evaluation when one is available.
- Reports separate `error_pct_status` values for unavailable, invalid,
  zero-denominator, and available cases.

A consistency risk remains: a supplied formula-derived training prediction
can take precedence over the retained final predictor. If far predictions
were produced by a hybrid predictor but training predictions were produced
from only its symbolic base formula, the numerator and denominator refer to
different predictors. That ratio is not method-consistent and should not be
accepted as the primary result.

### 3.2 Formula-only training prediction construction

Both
`run_comparative_suite_benchmark_v2.py` and
`run_comparative_suite_benchmark_pca.py` build `_y_pred_train` by
evaluating complete formula strings on the augmented training matrix.

That route deliberately excludes architecture labels such as
`ImprovedNN(...)` and `[NN fallback ...]`, as well as empty and `N/A`
formulas. Consequently, a formula-only route cannot supply training
predictions for an architecture-only method.

The shared scorer can fall back to `_predict_fn`, but only if the final
callable is actually retained and can accept the original-schema training
matrix.

### 3.3 Composite LLM + NN predictor retention

The LLM+NN runner builds a base predictor and, when residual correction is
accepted, a residual predictor. It constructs a composite callable only when
both components are callable. The final callable is retained on the method
result when available.

This lifecycle needs explicit verification for every branch:

- direct NN fit selected as the base predictor;
- symbolic/LLM base plus residual NN correction;
- residual correction rejected;
- residual correction accepted but one component is missing;
- perfect or near-perfect base predictions where correction is skipped;
- predictor construction or preprocessing failures.

A method must not claim that its final fitted predictor is reusable if the
complete inference path cannot be reproduced. If the method has valid
predictions on training rows but no callable for later inference, that is a
result-contract gap to repair at the method boundary.

### 3.4 PCA runner and feature transformations

The PCA runner has its own predictor composition and transformation path.
The same interface contract must apply, but it must not be assumed that its
input schema is identical to the v2 runner's schema.

The retained predictor must own or close over all fitted transforms needed
for inference (for example scaler, PCA transform, log-feature transform,
feature selection/order, and any output inverse transform). These transforms
must be fitted only on permitted training data and reused unchanged.

Do not reconstruct preprocessing state from far rows. Do not apply an
already-transformed matrix to a callable that expects original features, or
vice versa.

## 4. Required predictor contract

Every successful method result that claims reusable prediction capability
should expose one canonical final predictor with an explicit input contract.

Recommended conceptual contract:

```python
result.predictor_contract = {
    "available": True,
    "input_schema": "original_features",
    "feature_names": [...],
    "feature_count": ...,
    "preprocessing_included": True,
    "output_shape": "n_samples",
    "output_scale": "target_scale",
    "composition": ["base_model", "residual_correction"],
    "fitted_on_training_only": True,
}
result._predict_fn = final_predictor
```

This is illustrative metadata, not a claim that these exact fields already
exist. The implementation may choose a typed dataclass or another stable
representation.

The callable contract should require:

1. A two-dimensional numeric feature matrix with a documented schema.
2. One finite target-scale prediction per input row.
3. Deterministic row alignment and preserved input order.
4. No fitting, refitting, calibration, or state mutation during prediction.
5. All required fitted preprocessing and inverse transforms included.
6. Explicit errors for wrong feature count, missing features, invalid
   transforms, non-finite values, or incompatible shapes.
7. A stable method identity and route recorded in diagnostics.

If a method cannot provide a predictor, it must report that honestly. A
formula may be used as a predictor only when it represents the actual method
being scored and its inputs map unambiguously to the declared feature schema.

## 5. Scoring precedence

The intended scoring precedence should be:

1. If a retained *final fitted predictor* exists and its contract matches the
   original-schema train and far matrices, use it for both train and far.
2. If no retained predictor exists, use an evaluable symbolic formula only
   when the formula is the method's actual prediction representation and can
   be evaluated consistently on both partitions.
3. If neither route is valid, preserve any independently valid metrics and
   report the specific predictor/representation failure.

A caller-supplied training prediction array may be accepted only when its
provenance identifies the exact predictor/route that generated it and that
route is also used for far predictions. Formula-derived training predictions
must not silently override a retained final hybrid predictor.

The scorer should make the selected route explicit, for example:

- `retained_final_predictor`
- `symbolic_formula_fallback`
- `provided_predictions_verified`

The route should be stored for both training and far prediction diagnostics,
and should be identical for the ratio calculation.

## 6. Status and diagnostic taxonomy

Keep metric status separate from far-prediction status. Suggested
`error_pct_status` values:

| Status | Meaning | Action |
|---|---|---|
| `available` | Same valid predictor produced finite train/far predictions and positive training RMSE | Report ratio |
| `zero_or_invalid_training_rmse` | Training RMSE is zero or invalid | Keep ratio null; retain other metrics |
| `training_predictor_unavailable` | No consistent training prediction route | Repair predictor retention/adapter |
| `training_prediction_error` | Final predictor failed on exact training rows | Preserve exception and inspect preprocessing |
| `training_prediction_length_mismatch` | Prediction count differs from training row count | Fix shape/row alignment |
| `nonfinite_training_prediction` | Training predictions contain NaN or infinity | Inspect model and transforms |
| `training_metric_error` | Valid predictions exist but training RMSE computation failed | Inspect metric inputs |
| `predictor_route_mismatch` | Train and far predictions came from different method routes | Reject ratio and fix scorer precedence |
| `training_targets_unavailable` | Exact training targets were not supplied | Fix split/scoring inputs |

Also retain:

- predictor route and composition;
- input schema and feature count;
- preprocessing route/version;
- train/far input row counts;
- train/far prediction shapes;
- finite-value counts;
- exception type and message;
- whether the final callable was retained;
- whether the model was fitted only on the training partition.

Avoid a single generic null reason. Do not overwrite a more specific prediction
failure with a generic `scored` status for the far metrics.

## 7. NN and hybrid cases that must be covered

The offline regression matrix should include at least:

### A. Direct NN predictor

- Retained direct NN predictor is called on original-schema train and far
  matrices.
- Scaler and log transforms are reused from the fitted model.
- Predictor is not refitted during either scoring call.
- Wrong feature count and non-finite output are rejected with diagnostics.

### B. LLM/formula base plus residual NN

- Composite predictor invokes the base model and residual correction.
- Both components receive the correctly transformed inputs.
- Train and far predictions use the same composite callable.
- The formula-only base predictions do not override the composite training
  predictions.
- Missing base or residual component produces an explicit unavailable route.

### C. Residual correction rejected or skipped

- If the final method is the base predictor, retain and use that base predictor.
- Metadata states that NN correction was not applied.
- Training and far predictions use the same base route.

### D. PCA/hybrid route

- PCA/scaler/feature selection state is retained.
- The callable accepts the documented original feature schema and applies
  fitted transforms internally.
- Both partitions follow the same transform path.
- No PCA/scaler fit is performed during scoring.

### E. DeFi / symbolic hybrid

- If the final method is genuinely a symbolic formula, evaluate that formula
  on both partitions with name-based argument alignment.
- If it contains a learned correction, score the complete learned composition
  rather than the formula alone.
- A zero training RMSE leaves `error_pct` undefined.
- A nonzero training RMSE produces the expected ratio.

### F. Negative and failure cases

- Missing predictor and missing formula.
- Predictor exception on train but not far, and vice versa.
- Shape mismatch, NaN, infinity, and wrong feature order.
- Formula route and predictor route disagree.
- Training targets absent or misaligned.
- Far R² negative but valid.
- Far RMSE valid while error ratio is undefined.

Tests should assert prediction route, call order/inputs, metrics, and diagnostic
status. Synthetic stand-ins are appropriate for offline tests; they do not
replace the eventual controlled smoke run.

## 8. Coverage measurement and acceptance

For the 3-equation × 6-method smoke matrix, report 18 expected method/equation
outcomes. For each metric, calculate coverage independently:

```text
coverage(error_pct) =
    count(valid, mathematically defined error_pct) / 18
```

Also report a second count for *predictor-evaluable coverage*, separating
methods that expose a consistent predictor from cases where the ratio is
mathematically undefined due to zero training RMSE.

The report must include:

- total expected outcomes;
- non-null `error_pct` count;
- undefined-zero-denominator count;
- predictor-unavailable count;
- prediction-error/invalid-output count;
- route-mismatch count;
- per-equation and per-method breakdown;
- far R² and RMSE coverage separately;
- actual metric values, including negative R²;
- run URL, commit, configuration, and artifact identity.

The engineering target is to eliminate avoidable nulls caused by missing
predictor retention, wrong preprocessing, or inconsistent scoring routes.
There is no requirement that the mathematical zero-denominator cases become
non-null. Do not set a target of 18/18 non-null ratios if that would require
changing the metric's meaning.

A valid improvement is demonstrated when formerly unavailable NN/hybrid
training predictions become available from the same final predictor, while
legitimate undefined ratios remain explicitly classified.

## 9. Implementation sequence after documentation

The recommended follow-up implementation should be split into reviewable
steps:

1. **Predictor lifecycle audit:** enumerate every successful Exp2 method path
   and establish whether its final inference callable is retained.
2. **Canonical final predictor:** make method adapters expose one callable
   that includes the full fitted composition and preprocessing.
3. **Scorer precedence correction:** when a final predictor exists, use it for
   both exact training and far rows; do not prefer an unrelated formula-only
   training array.
4. **Diagnostics and provenance:** record route, feature schema, transforms,
   and failure reason for both partitions.
5. **Offline regression tests:** cover direct NN, LLM+NN, PCA, DeFi, zero
   denominator, and invalid predictor cases.
6. **CI verification:** run targeted tests and relevant Exp2 contract tests.
7. **Controlled smoke:** only after explicit authorization, dispatch the
   3-equation × 6-method smoke on the reviewed commit and inspect the artifact.

No benchmark or experiment should be launched as part of the documentation
or offline implementation stages.

## 10. Relationship to existing work

This guide extends, rather than replaces, the following repository material:

- `docs/exp2_extrapolation_shared_core.md`: shared split and scoring core.
- `docs/exp2_extrapolation_failure_resolution_methodology.md`: general
  diagnosis and repair workflow.
- `docs/exp2_feynman_far_coverage_investigation.md`: original far-coverage
  investigation, where present.
- `hypatiax/experiments/benchmarks/exp2_extrapolation_core.py`: canonical
  scorer implementation.
- `hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py`
  and `run_comparative_suite_benchmark_pca.py`: method adapters and runner
  integration.

The shared core establishes the split and metric rules. This document adds
the missing method-level invariant: the training and far RMSEs used in a
single ratio must be produced by the same final fitted prediction route.
