# exp1b Portfolio VaR fallback: offline diagnosis

**Status:** post-run forensic audit of the retained seed-99 shard artifact. This document records an offline calculation only; it does not change routing, tau, cohort assignments, or experiment outputs.

## Evidence inspected

Pinned repository state: `f260226532d5b1cfb94f73b1a5ca739793df0bdc`.

Primary artifact:

`hypatiax/data/results/comparison_results/noise-noiseless/15/portfolio_variance_defi_seed_sweep_seed99_shard0.json`

The artifact identifies the case as **Portfolio VaR for two correlated assets**, with ground truth

`sqrt(var1**2 + var2**2 + 2*rho*var1*var2)`.

It retains the exact train/test arrays under `audit_data`, the generated formula, route metadata, and selected-predictor metrics. The recorded split is `first_feature_percentile_40_60`, with 80 training rows and 120 held-out rows.

## What happened

The generated formula was:

```python
def formula(var_asset1, var_asset2, correlation):
    return np.sqrt(var_asset1**2 + var_asset2**2 + 2 * correlation * var_asset1 * var_asset2)
```

The saved result records `llm_called=true` and `llm_train_r2=1.0`. An independent offline recomputation from the retained `X_test` and `y_test` arrays gives formula-only held-out `R²=1.0`, `RMSE=0`, and `MAE=0`. This is a post-run audit calculation, not a routing input, threshold calibration, or evidence of generalization to independent equation families.

Despite that exact formula fit, the selected hybrid result is:

- `decision=nn_abstention_fallback`
- `route_reason=degradation_probe_or_tau_unavailable`
- `train_r2_source=nn_abstention_training_mean`
- selected-predictor `test_r2=far_r2=-6.167131634880697`
- `success=false` under the runner's strict selected-predictor `test_r2 > 0.99` criterion.

The selected score therefore belongs to the replacement training-mean predictor, **not** to the generated formula. The formula's training and held-out scores must not be conflated with the selected-predictor score.

## Why the replacement was selected

The route policy in `hypatiax/core/routing.py` deliberately returns `ensemble` when either the degradation delta or calibrated tau is unavailable. In this run, tau remains unavailable by design: no valid independent-family LLM degradation calibration has established it. The benchmark then enters its ensemble path.

The NN quality gate independently abstains when the NN's training-only directional edge-validation R² is negative and no eligible positive edge-validated log-Ridge alternative is available. The artifact records:

- `nn_edge_r2=-0.8975481069699327`
- `ridge_edge_r2=null`
- `nn_selected_model=training_mean`.

The log-Ridge candidate is eligible only when **all** training features and targets are positive. In the retained 80-row training matrix, the correlation feature ranges from -0.5 to approximately 0.05578; 72 of its 80 values are negative. Thus the current positivity gate excludes log-Ridge for this case, even though the two variance features and target are positive.

When the NN abstains, the ensemble branch explicitly selects the replacement predictor and does not blend in the LLM formula. That is why the selected-predictor score is very poor even though the recorded formula itself exactly matches this case's target on the retained split.

## Diagnosis and safe next steps

This is not evidence that the LLM formula failed. It exposes two separate conservative gates:

1. **LLM route gate:** correctly remains fail-closed while `delta_llm` and a scientifically calibrated tau are unavailable.
2. **NN replacement gate:** rejects the MLP on negative edge-validation R²; the log-Ridge fallback is unavailable because one feature (correlation) can be negative; the training mean is then selected.

Do not fix this by using held-out labels to route to the formula, hard-coding a tau, relaxing the NN edge gate, or treating the NN degradation probe as `delta_llm`. Any alternative fallback model must be designed and validated using training-only procedures, with its feature-domain assumptions made explicit. Any LLM route change still requires the independent-family calibration and frozen-tau protocol.

The next safe work is an offline design review of a sign-safe, training-only alternative to the positivity-constrained log-Ridge candidate, plus regression tests that distinguish formula-only metrics from selected-predictor metrics. No new model fitting, provider calls, paid calls, seed sweep, or rerun is authorized by this audit.
