# Feynman mechanics horizon integration

This adapter connects the generic extrapolation-horizon tools to three Exp2
mechanics equations:

| Feynman ID | Equation | Features |
|---|---|---|
| I.12.1 | Newton gravity: G m1 m2 / r² | m1, m2, r |
| FEY_MECH_KE | Classical kinetic energy: m v² / 2 | m, v |
| I.18.4 | Reduced mass: m1 m2 / (m1 + m2) | m1, m2 |

## API

    from hypatiax.tools import evaluate_feynman_horizon_curves
    from hypatiax.tools import write_results_json, plot_horizon_curves

    records = evaluate_feynman_horizon_curves(
        equation_id="I.12.1",
        X_train=X_train,  # exact in-domain training split
        y_train=y_train,
        predictors={
            "PureLLM": purellm_predict_fn,
            "HybridDiscovery": hybrid_predict_fn,
        },  # already-fitted callables only
        distances=(0.25, 0.5, 1.0, 2.0, 4.0),
        n_points=120,
    )
    write_results_json(records, "newton_horizon.json")
    plot_horizon_curves(records, "normalized_far_rmse", "newton_rmse.png")

The return value is a flat list of versioned records, one per method,
strategy/direction, and distance. The adapter emits single-feature upper/lower
rays and explicit multifeature directions. Newton gravity includes simultaneous
increases in both masses and decreases in separation.

## Scientific and leakage constraints

- The caller supplies the exact training split and already-fitted predictors.
  No fitting, tuning, retraining, LLM call, or experiment launch occurs.
- Ground truth is evaluated from the analytical equation.
- All features in these three equations must be strictly positive. Generated
  points outside the physical domain are excluded; each record reports
  generated count, valid count, and valid fraction. Fewer than two valid
  points are marked unscored rather than evaluated through singularities or
  nonphysical regions.
- Distances are multiples of each feature's training-range width. Combination
  directions are declared in this adapter, not inferred from far outcomes.
- Optional interval predictors return lower and upper bounds. Coverage is
  empirical and is not a calibration guarantee under distribution shift.
- These are controlled synthetic equation checks; they do not establish
  generalization to noisy observations or every physically admissible path.

## Metrics

Each scored record includes far R², far RMSE, training-target-normalized far
RMSE, and far/train RMSE ratio when its denominator is positive. Metric
availability is independent: zero training RMSE makes only the ratio
undefined. Predictor and interval exceptions are recorded per method and
scenario so one failure does not erase other curves.
