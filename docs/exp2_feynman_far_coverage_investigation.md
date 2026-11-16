# Exp2 Feynman far-region coverage investigation and remediation

Date: 2026-11-16  
Scope: REPRO benchmark implementation and reproducibility artifacts. No experiment was launched as part of this change.

## Baseline observation

The 16 November 2026 smoke run ([Actions run 43946438261](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/43946438261)) completed successfully and validated the three-equation × six-method artifact contract. The run summary indicated 10/18 far-region R² and RMSE values were available (55.6%). A successful workflow means the artifact contract passed; it does not mean every method supplied a far-region predictor or achieved good extrapolation.

The earlier log review attributed six nulls to two NN/black-box method outputs per equation, and identified two additional unexplained nulls for PureLLM and EnhancedHybrid on Newton's gravitational-force equation. Those two nulls were not conclusively diagnosed from the old logs because the far evaluator discarded exceptions. Re-count from the archived artifact JSON before treating 10/18 as a definitive baseline.

## Root causes and distinctions

1. **Predictor-only methods were skipped.** The far evaluator treated architecture labels such as `ImprovedNN(...)` and `[NN fallback...` as unsupported, even though the benchmark's method result may retain a callable `_predict_fn`. This is a coverage limitation, not evidence of poor predictive quality.
2. **Formula evaluation failures were opaque.** Formula evaluation can return `None` or raise, and the far evaluator previously collapsed these outcomes to null without a reason.
3. **A null score is not a poor score.** Negative finite R² is a valid score and must remain visible. Coverage is separate from predictive quality.
4. **Extrapolation error percentage is a separate metric.** It requires a valid far RMSE and a valid, non-zero training RMSE. Its absence must not erase a valid far R²/RMSE.

## Remediation applied

- Prefer an already-fitted `_predict_fn` when available, so NN/hybrid methods can be evaluated on held-out far features without fitting on the far region. The retained predictor receives the original feature schema, consistent with the independent external-holdout path; symbolic formulas continue to receive the engineered feature matrix.
- Preserve formula evaluator diagnostics and classify method failures, missing formulas, unsupported architecture tags, predictor exceptions, prediction length mismatches, non-finite predictions, metric failures, and successful scores.
- Persist per-method diagnostics in the protocol result and flat extrapolation rows.
- Keep R² and RMSE availability separate from `extrap_error_pct`; preserve finite negative R² values and never fabricate scores.

## Scientific validity safeguards

The adapter only invokes an already-fitted inference function on held-out far features; it does not train or tune on the far region. It does not substitute a ground-truth equation, change the split, increase sample counts, or convert missing scores into numbers. A higher coverage percentage alone is not evidence of better extrapolation; inspect diagnostics and score quality separately.

## Remaining work / acceptance

- Review the code and its CI before relying on the new adapter. No local tests were run and no experiment was dispatched as part of this change.
- Run the manually dispatched Exp2 smoke workflow after review, then inspect its artifact JSON. Report R² coverage, RMSE coverage, error-percentage coverage, and per-method diagnostic reasons separately.
- If a retained predictor is absent, the corresponding NN outcome remains explicitly `unsupported_predictor`; do not silently substitute an unrelated formula or retrain on the far region.
