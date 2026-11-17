# Shared Exp2 extrapolation evaluation core

## Purpose

The module `hypatiax/experiments/benchmarks/exp2_extrapolation_core.py` is the canonical, lightweight implementation for the Exp2 far-extrapolation split and scoring contract. The v2 Feynman runner, PCA Feynman runner, and legacy `extrap_r2_far.py` compatibility entry point import the same functions. They no longer carry independent copies of the scoring implementation.

The module is intentionally safe to import from tests and experiment runners: it does not seed global random-number generators, import PyTorch/Julia/Anthropic, fit models, launch workers, or call external APIs.

## Shared API

- `build_extrap_split(X, y, description, train_frac, multiplier)` sorts on the primary feature, creates a contiguous training region, applies the multiplier ceiling, and returns the train/far arrays plus split metadata. It rejects invalid inputs and splits with fewer than two rows in either region. The far targets are evaluation-only.
- `_runner_eval_formula(code, X, var_names)` evaluates a symbolic formula through the restricted formula interpreter. Named formula arguments are mapped to matching feature columns, including when engineered features add columns or reorder the feature schema.
- `compute_extrap_r2_far(...)` evaluates retained fitted predictors or symbolic formulas and reports far R², far RMSE, RMSE-ratio percentage, and per-method diagnostics. It never fits or retrains a method.
- `calculate_extrapolation_error` and `extrapolation_error_status` provide the shared RMSE-ratio and five-tier status calculation.

## Training baseline and leakage boundary

The RMSE-ratio denominator is computed on the exact training rows supplied to the runner. The runner passes `X` as `X_train_predictor` only after the outer extrapolation split has removed the far rows. A retained `_predict_fn` is authoritative: the scorer uses that same final fitted predictor for both far and training predictions, even if `y_pred_train` also contains formula-derived values. This prevents a hybrid's far error from being divided by the error of only its symbolic base component. Only when no retained predictor exists does the symbolic-formula fallback use runner-supplied `y_pred_train` (which preserves engineered feature columns).

The scorer does not use `X_far`, `y_far`, or external-holdout rows to construct the training baseline. It validates training prediction length and finiteness, and records `predictor_route`, `training_prediction_route`, and `error_pct_route_consistent` in per-method diagnostics. When training RMSE is zero or invalid, the ratio remains null and the diagnostics report `zero_or_invalid_training_rmse`; other far metrics remain available.

`error_pct` is the ratio `100 * RMSE_far / RMSE_train`, not conventional percentage prediction error. It is undefined when training RMSE is zero. Metric availability and predictive quality must be reported separately.

## Runner integration

Both `run_comparative_suite_benchmark_v2.py` and `run_comparative_suite_benchmark_pca.py` delegate split construction and far scoring to this module. Their split-preparation paths fail closed if the shared split cannot be built; there is no inline fallback with different split rules. The historical `extrap_r2_far.py` entry point re-exports the shared functions for existing imports.

## Verification scope

Offline regression tests cover formula argument alignment, split validation, far metric behavior, retained-predictor training baselines, zero-training-RMSE handling, diagnostics persistence, and runner delegation. These tests are committed for CI; they have not been run locally as part of this change.

No experiment, benchmark, worker, model fit, or LLM request is launched by this refactor.
