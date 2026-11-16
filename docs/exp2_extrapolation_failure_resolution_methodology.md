# Methodology for diagnosing and repairing extrapolation-scoring failures

## Purpose

This document defines a repeatable, evidence-led method for diagnosing missing or invalid far-region extrapolation metrics in Exp2-style benchmark runs. It records the general engineering principles behind the far-region diagnostics and predictor/formula evaluation improvements in PRs #140 and #141.

The objective is to improve score coverage without manufacturing scores, changing the scientific target, retraining on the far region, or confusing successful execution with good extrapolative performance.

## Scope and terminology

- **Normal/in-domain metrics** are computed on the benchmark's normal evaluation split.
- **Far-region metrics** are computed on the separately defined extrapolation region.
- **Coverage** is the fraction of expected method/equation outcomes for which a metric was successfully computed.
- **Predictive quality** describes the value of a computed metric (for example, far-region R² or RMSE). Coverage and quality must be reported separately.
- **Unsupported** means a method does not expose a predictor or symbolic representation that the scoring contract can evaluate. It is not the same as a runtime failure.
- **Evaluation failure** means an evaluation was attempted but could not produce a valid score.

The far region must remain an evaluation-only region. Do not fit, tune, select, or retrain a model using far-region targets.

## Core principles

1. Preserve the experiment's data split and scientific target.
2. Prefer evaluating the exact fitted model or formula produced by the method.
3. Reuse retained fitted predictors; do not retrain on far-region data to fill missing scores.
4. Map symbolic formula arguments to input features explicitly when names are available.
5. Never substitute a ground-truth equation, an expected answer, or a fabricated value for a missing prediction.
6. Make failure reasons observable and machine-readable; avoid broad silent exception handling.
7. Keep score availability distinct from score quality. A negative R² is a valid result, not a missing score.
8. Keep implementation copies and canonical helpers consistent where the repository's parity tests require it.

## Repeatable diagnostic and repair workflow

### 1. Establish the expected scoring contract

Before changing code, record:

- equation/problem identifier;
- method identifier;
- expected normal and far-region metrics;
- the exact evaluation split and feature schema;
- whether the method is expected to expose a symbolic formula, a fitted predictor, both, or neither;
- the benchmark commit, configuration, and run identifier.

Do not infer a missing score's cause from the normal-region score. A method can perform well in-domain and still fail during far-region evaluation.

### 2. Measure coverage before interpreting quality

For each equation and method, report independently:

- whether normal-region metrics exist;
- whether far-region R² exists;
- whether far-region RMSE exists;
- whether any secondary metric (such as percentage error) exists;
- the reason a metric is unavailable.

Use explicit denominators. For example, 16 scored outcomes out of 18 expected outcomes is 88.9% coverage. Do not describe this as 16/18 successful predictions unless the scoring contract defines that equivalence.

Keep negative and low R² values. They indicate poor extrapolation, not a scoring-system failure. Do not turn them into nulls or clamp them to zero.

### 3. Diagnose each missing metric with structured reasons

At minimum, distinguish these categories:

| Category | Meaning | Appropriate next action |
|---|---|---|
| `unsupported_method` | No eligible formula or predictor is exposed | Report as unsupported; consider a documented method adapter only if a genuine fitted predictor exists |
| `formula_missing` | A symbolic method was expected but supplied no formula | Inspect method result contract and upstream result |
| `formula_parse_failed` | Formula could not be parsed | Inspect formula serialization and parser compatibility |
| `formula_argument_mismatch` | Formula parameters cannot be mapped safely to available features | Inspect parameter names and feature schema; do not guess |
| `predictor_unavailable` | No retained fitted predictor is available | Inspect method adapter and result retention |
| `prediction_failed` | Formula or predictor raised during inference | Preserve exception type/message and inspect input contract |
| `prediction_shape_invalid` | Prediction count/shape does not match far-region rows | Inspect vectorisation and output shape |
| `prediction_non_finite` | Predictions contain NaN or infinity | Inspect numerical stability and preprocessing |
| `metric_computation_failed` | Predictions exist but metric computation failed | Inspect metric inputs and numerical edge cases |

Implementations may add more specific categories. They should not collapse materially different causes into one generic null result.

For every attempted evaluation, retain enough context to reproduce the interface failure: method/equation identifiers, formula text or safe formula identifier, parameter names, available feature names, input shape, prediction shape, exception class, and exception message. Avoid logging secrets or sensitive payloads.

### 4. Evaluate retained fitted predictors where available

For methods whose result object retains a fitted prediction callable:

1. Retrieve the predictor from the completed normal-region fit.
2. Apply the same feature construction, ordering, scaling, and preprocessing contract used by that fitted model.
3. Pass only the far-region feature rows to the retained predictor.
4. Validate output shape and finiteness.
5. Compute far-region metrics against the far-region targets.
6. Record the predictor evaluation route in diagnostics.

Do not fit or tune the predictor on far-region samples. If required preprocessing state was not retained, report the limitation rather than rebuilding it using far-region information.

### 5. Align symbolic formula arguments to features safely

A symbolic formula may declare fewer arguments than the feature matrix contains because the matrix can include engineered or redundant features. Passing every matrix column positionally can therefore raise an argument-count error or, worse, silently bind values to the wrong variables.

Use this precedence:

1. Inspect the callable's declared parameter names.
2. If every required parameter name maps unambiguously to an available feature name, build arguments by name in the callable's declared order.
3. Ignore additional matrix columns that are not formula parameters; they are not implicit formula inputs.
4. If name-based mapping is not possible, allow positional evaluation only when the number of declared parameters exactly equals the number of supplied features and the positional order is part of the documented contract.
5. Otherwise fail explicitly with a `formula_argument_mismatch` diagnostic listing the missing/ambiguous parameters and available feature names.

Do not guess mappings from column positions when dimensions differ. Do not silently drop required parameters. Duplicate feature names or ambiguous aliases should be treated as mapping errors unless a deterministic alias policy is explicitly defined and tested.

### 6. Validate predictions before computing metrics

For both formula and predictor routes, verify:

- one prediction per far-region sample;
- compatible one-dimensional shape (or a documented conversion);
- numeric values;
- finite predictions;
- consistent row ordering;
- no accidental use of target values as model inputs.

Only compute metrics after these checks pass. Preserve the original exception and diagnostic context if validation fails.

### 7. Test the repair offline with a regression matrix

Add small deterministic tests that do not call external LLM APIs and do not launch scientific experiments. At minimum cover:

**Formula-to-feature mapping**
- same number of parameters and features in matching order;
- fewer formula parameters than features due to an engineered extra column;
- reordered feature columns with matching names;
- missing required parameter name;
- extra formula parameter not present in the feature schema;
- duplicate/ambiguous feature names;
- positional fallback with equal dimensions;
- positional fallback rejected when dimensions differ.

**Predictor evaluation**
- retained predictor returns one finite value per sample;
- predictor requires the fitted preprocessing transform;
- wrong output length or shape;
- NaN/infinite predictions;
- predictor raises an exception;
- no predictor is retained.

**Metric and reporting behaviour**
- negative R² remains a valid computed score;
- RMSE and R² coverage are tracked independently;
- unsupported methods are not counted as runtime exceptions;
- failure diagnostics survive serialization into protocol results and flat rows;
- canonical and copied evaluator implementations remain in parity where required.

Tests should assert both the metric outcome and the diagnostic category. Avoid tests that only assert that a run does not crash.

### 8. Verify at three levels

**Level A — unit/regression tests:** Exercise the failure mechanism and its edge cases with synthetic inputs. No LLM calls or benchmark run is needed.

**Level B — CI/contract tests:** Verify copy consistency, result serialization, artifact schemas, and the benchmark's validation contracts.

**Level C — controlled smoke benchmark:** Run the explicitly dispatched smoke workflow on the intended branch and inspect its artifact. Confirm expected equation/method combinations, score coverage, failure diagnostics, and the actual metric values. A green workflow only proves that the workflow and its validators completed; it does not by itself prove full score coverage or good extrapolation.

For a 3-equation × 6-method smoke run, the expected matrix contains 18 outcomes. Report the numerator, denominator, and per-equation/per-method breakdown. Investigate any remaining nulls by diagnostic reason. Do not generalise from this small matrix to all equations and methods without broader regression coverage.

## Acceptance criteria for a fix

A repair is ready for review when:

- the original failure is reproduced by a deterministic offline test;
- the test fails for the old behaviour and passes for the corrected behaviour;
- parameter/feature mapping is deterministic and rejects ambiguity;
- retained predictors are evaluated without far-region fitting or tuning;
- invalid predictions cannot be mistaken for valid scores;
- failures produce structured, persisted diagnostics;
- coverage and quality are reported separately;
- negative R² values are preserved;
- relevant implementation copies and schemas remain consistent;
- CI evidence is recorded accurately;
- any smoke benchmark evidence identifies its commit, run, configuration, and artifact.

A fix should be described as addressing the tested failure class, not as universally solving all extrapolation failures.

## Reporting template

For each run, record:

- Run URL and run ID:
- Branch and commit SHA:
- Configuration and sample count:
- Expected outcomes:
- Far R² coverage:
- Far RMSE coverage:
- Secondary-metric coverage:
- Breakdown by equation and method:
- Missing-score diagnostics:
- Negative/poor scores retained:
- Artifact URL:
- Unit/CI evidence:
- Known limitations and untested cases:

## Related implementation history

- **PR #140 — Improve Exp2 far-region score coverage diagnostics:** introduced structured far-region diagnostics, retained-predictor evaluation where available, and separate coverage reporting.
- **PR #141 — Fix Exp2 far-formula argument alignment:** aligned named formula parameters to matching feature columns and added regression coverage for augmented and reordered feature matrices.
- **Investigation note:** `docs/exp2_feynman_far_coverage_investigation.md` (if present in the target branch) records the original smoke-run coverage investigation.

These changes improve general failure handling, but they do not guarantee that every method exposes a scoreable predictor or that every formula is evaluable. Generalisation must be established through the regression matrix and additional representative benchmark cases.
