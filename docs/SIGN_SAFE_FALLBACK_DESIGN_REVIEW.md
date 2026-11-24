# Sign-safe fallback candidate: offline design review

**Status:** design proposal only. No model was fitted, no benchmark data were changed, and no route or threshold was modified.

## Problem established by the retained Portfolio VaR artifact

The current alternative is a log-linear Ridge model:

    Ridge(alpha=1.0).fit(np.log(X_fit), np.log(y_fit))

It is gated on every training feature and target being strictly positive. That assumption is inappropriate for a signed feature such as correlation. In the retained two-asset VaR training partition, correlation includes negative values, so the candidate is excluded before its predictive quality can be measured.

This is a domain restriction of the current log transform, not evidence that all Ridge-style alternatives are unsuitable.

## Candidate for a future controlled evaluation

Use a **training-fitted, sign-safe standardized Ridge candidate**:

1. Keep the existing deterministic directional edge split wholly inside the outer training partition.
2. Construct a predeclared feature map that does not require positivity: raw signed features, plus explicitly documented pairwise interaction terms where justified by the benchmark's feature schema. Do not add log or square-root transforms to signed variables.
3. Fit `StandardScaler` on the inner fit rows only; transform the inner edge-validation rows using that scaler.
4. Fit `Ridge(alpha=...)` on the scaled inner fit rows and score only on the inner edge-validation rows.
5. Mark the candidate eligible only when the training-only fit and edge score are finite and the edge score meets a predeclared positive-quality rule. Compare it with the NN on the same edge rows.
6. If selected, refit scaler and Ridge on the complete outer training partition, then predict the untouched outer test partition once.

The feature map, alpha-selection rule (if any), tie-breaking, and minimum validation-quality criterion must be fixed before inspecting outer test labels. If alpha is tuned, that tuning needs a nested training-only procedure or a predeclared small candidate set evaluated on the same inner validation protocol with appropriate selection safeguards.

## Portfolio VaR-specific caution

For the two-asset variance expression, a scientifically motivated basis might include the squared asset-volatility terms and the correlation-times-cross-product term. But the target is the square root of their sum. A generic linear Ridge model over raw features is therefore not guaranteed to represent the target, and a polynomial basis may still extrapolate poorly or produce invalid predictions.

Do not add a portfolio-specific feature map to the general-purpose fallback silently. It would need an explicit case/schema contract, independent tests, and a separate benchmark comparison. Do not use the generated LLM formula or held-out target labels to engineer, select, or validate this fallback.

## Acceptance and failure behavior

- Preserve the current NN abstention rule.
- Preserve fail-closed LLM routing while `delta_llm` and calibrated tau are unavailable.
- A candidate with nonfinite or non-positive edge-validation R² remains ineligible; do not fall back to training mean and call that a successful high-quality predictor.
- Keep the training-mean baseline visible as a last-resort diagnostic, with its own selected-model identity and score semantics.
- Add tests for negative and zero-valued features, positive and negative targets where supported, train-only scaler fitting, edge-only candidate selection, and no outer-test influence.
- Compare the candidate against the current NN, log-Ridge (when its domain assumptions hold), and training-mean baseline on fixed training-only validation partitions before any controlled rerun is considered.

## Decision

This is a plausible candidate architecture, not a validated replacement. The next implementation should be isolated behind an explicit model name and training-only quality gate. It must not change the LLM route, tau, calibration protocol, cohort assignments, or the existing NN acceptance threshold. No fitting, provider call, experiment, rerun, or seed sweep was performed for this review.