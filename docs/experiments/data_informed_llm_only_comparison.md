# Data-informed LLM-only comparison

## Motivation and observed zero-shot result

The Core-15 four-way smoke for Allometric Scaling (case 3; run
[43742199866](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/43742199866))
completed the Hybrid LLM+PySR, PySR-only, and NN-only arms successfully. The
strict LLM-only arm returned:

```python
def formula(M):
    import numpy as np
    result = 3.4 * np.power(M, 0.75)
    return result
```

The benchmark's synthetic target is `0.1 * M**0.75`. The exponent was
correct, but the coefficient was 34 times too large. On the 40-point outer
test set, all targets and predictions were finite; raw R-squared was
-5913.024851913015, RMSE 64.66101396777347, and MAE 58.41497101266508.
Canonical R-squared classified this as catastrophic (below -100), so the
existing scoring policy correctly marked the arm unsuccessful.

This is an information-regime limitation, not evidence that the LLM cannot
recognize the functional family. The strict zero-shot prompt contains the
task description and declared input variables, but no training observations
or data-derived parameter information. The hidden coefficient cannot in
general be recovered from that description. The baseline must remain
unchanged and must continue to report this result as a failure.

## Proposed comparison arms

Retain the existing `llm_only_zero_shot` arm as the control. Add three
separately named data-informed LLM-only treatments. Each treatment must
generate a formula with the LLM; none may call PySR, sklearn, OLS, curve
fitting, symbolic regression, or any other external parameter-fitting
routine.

1. **`llm_only_fewshot_train`** — one LLM call. Supply a deterministic,
   predeclared subset of training input/output pairs (for example, 12 rows
   selected by evenly spaced indices after sorting by the first input).
   Do not supply test or extrapolation rows. Ask for one explicit formula
   with the exact declared input signature and numeric coefficients.
2. **`llm_only_train_summary`** — one LLM call. Supply training-only
   descriptive statistics (sample count, per-feature min/max/mean/std and
   fixed quantiles, target statistics, and where applicable feature/target
   correlations) but no raw rows. Ask the LLM to infer a formula and numeric
   coefficients from those summaries. Statistics must be computed from
   `X_train, y_train` only.
3. **`llm_only_train_feedback`** — two LLM calls maximum. First, request a
   formula using the same fixed training sample as the few-shot arm. Evaluate
   that formula on training rows only and return a compact training-only
   error report (RMSE, MAE, and R-squared) to the LLM for one revision.
   The second response is the final formula. No coefficient optimizer or
   automatic formula search may run between calls; the LLM itself must make
   the revision. If the first formula cannot be evaluated safely, record a
   failure rather than repairing it with fitted values.

## Shared controls and fairness requirements

- Use the same model, temperature (0.25), API wrapper, token limit, and
  system/developer instruction policy as the existing pure-LLM baseline.
- Keep the strict zero-shot arm unchanged. Record each data-informed arm's
  information regime and prompt hash separately.
- The LLM receives only the task description, domain, declared input names,
  and its arm's explicitly listed training-only information. Do not expose
  ground-truth formulas, equation catalog source, test data, or near/medium/far
  extrapolation data.
- Preserve the exact ordered input signature. Coefficients not represented
  by input columns must be numeric constants in the returned expression.
  Never invent missing input values or silently inject zeros/defaults.
- Evaluate the final formula with the same safe evaluator and the same
  canonical R-squared / RMSE / MAE policy as the zero-shot arm. Do not relax
  the catastrophic-R-squared threshold.
- Score every final formula on the shared outer test and near/medium/far
  extrapolation partitions only after generation is complete. These
  partitions are evaluation-only and must never be fed back to the LLM.
- Record API call count, prompt and response hashes, formula text/hash,
  training-only diagnostics, outer-test diagnostics, extrapolation
  diagnostics, elapsed time, and explicit success/failure reason.
- Keep all five strategy outcomes in the denominator. Report paired
  comparisons only on common successful cases and publish the paired
  denominator and coverage fraction.
- Keep the variants in separate method keys; do not relabel them as the
  original zero-shot baseline or as the Hybrid LLM+PySR arm.

## Suggested execution sequence

1. Implement and review the new arms and leakage/provenance regression tests.
2. Run the one-case Allometric pilot first. This is a strategy sanity check,
   not a replacement for the official Core-15 result.
3. If the pilot produces valid, non-catastrophic formulas, run a matched
   Core-15 comparison using the same seed, noise, training size, model,
   temperature, and partitions as the existing run.
4. Report the strict zero-shot control alongside all data-informed variants;
   do not pool their results into the historical zero-shot estimates.

The current evidence is one Allometric case and one seed. It does not support
claims about the relative performance of these proposed strategies across
Core-15. Those claims require the matched comparison.


## Pilot results: Allometric Scaling (run 43771391296)

The isolated pilot completed successfully on 2026-11-15. The GitHub Actions
run is
[43771391296](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/43771391296).
Its uploaded artifact is
`data-informed-llm-only-pilot-run-43771391296` (artifact ID
`14184053313`). The run used case 3 (Allometric Scaling), seed 42, noise
level 0.05, 160 training rows, 40 outer-test rows, Claude Sonnet 4.6, and
temperature 0.25. All four variants completed; total API requests: five.

### Observed formulas and outer-test metrics

| Variant | Calls | Generated formula | Test R² | Test RMSE | Test MAE |
|---|---:|---|---:|---:|---:|
| `llm_only_zero_shot` | 1 | `3.4 * M**0.75` | Catastrophic | — | — |
| `llm_only_fewshot_train` | 1 | `0.0761 * M**0.81` | 0.989224 | 0.087284 | 0.078221 |
| `llm_only_train_summary` | 1 | `0.1 * M**0.75` | **0.997216** | **0.044361** | **0.035063** |
| `llm_only_train_feedback` | 2 | `0.080 * M**0.815` | 0.981576 | 0.114129 | 0.084273 |

The zero-shot row failed under the unchanged canonical scoring policy. The
generated expression had finite predictions, but the raw test R² was
-5913.024852 (catastrophic, below the -100 threshold); RMSE was 64.661014
and MAE was 58.414972. This is consistent with the earlier diagnostic:
the model recovered the exponent but not the hidden coefficient.

### Extrapolation metrics

| Variant | Near R² | Medium R² | Far R² |
|---|---:|---:|---:|
| Few-shot training examples | 0.963510 | 0.935457 | -0.255205 |
| Training summary statistics | 1.000000 | 1.000000 | 1.000000 |
| Training feedback + revision | -0.028447 | 0.724218 | -3.483860 |

The training-summary variant returned the exact generating expression
`0.1 * M**0.75` and therefore scored exactly on the generated
extrapolation partitions. This is an observed single-run result, not
evidence that summary statistics will generally identify hidden equations
or coefficients. The perfect extrapolation scores should be treated as a
pilot observation and tested across the matched benchmark, not generalized.

The feedback arm's first formula was `0.082 * M**0.81`; it received
training-only feedback (training R² 0.975786, RMSE 0.129766, MAE 0.102007)
and revised to `0.080 * M**0.815`. The revision did not improve the
outer-test result relative to few-shot or summary statistics.

### Interpretation and next step

For this one case and seed, training-summary statistics ranked first on
outer-test and extrapolation metrics, few-shot examples ranked second on
outer-test metrics, and one-step feedback ranked third. The unchanged
zero-shot control remained unsuccessful. The pilot used five LLM requests
in total (one each for zero-shot, few-shot, and summary; two for feedback).

This is a strategy-selection pilot only. It does not establish Core-15
performance, statistical significance, robustness across seeds, or
generalization to other equation families. Keep all four variants as
separate method keys and retain the zero-shot control. The next evidentiary
step is the pre-specified matched Core-15 comparison with the same
information-regime boundaries, common scoring, full assigned-case
denominators, paired coverage, and provenance reporting. Do not promote
the summary strategy as a general winner until that comparison is complete.

### Artifact provenance

- Workflow run: `43771391296`
- Artifact: `data-informed-llm-only-pilot-run-43771391296`
- Artifact ID: `14184053313`
- Training data SHA-256:
  `a21c3a23dad5d49d8936028a22ecc45e3cb557e048adb4d508416f664a3f5d58`
- Outer-test SHA-256:
  `698323421595e225fb92981e04acae72cf6d2d3321e2273593e1991549032cf9`
- Extrapolation split hashes are recorded in the pilot manifest and results
  JSON; prompt, response, and formula hashes are recorded per strategy.
- The artifact records that test and extrapolation data were not sent to
  the LLM, no external fitting or symbolic regression was used, and the
  ground-truth formula was not supplied.
