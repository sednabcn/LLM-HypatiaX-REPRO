# Uncertainty methods: architecture and roadmap

## Design principles

- One output contract, multiple estimators.
- Estimation and calibration are separate stages.
- Interval semantics and assumptions are explicit.
- Unsupported values are null/absent, not zero.
- Every result preserves method, domain, direction, distance, and coverage.
- Infrastructure never launches experiments, training jobs, benchmarks, or LLM requests implicitly.

## Architecture

```text
Data split and provenance
        |
        v
UncertaintyMethod (fit -> estimate)
        |
        v
UncertaintyEstimate
        |
        +--------------------+
        |                    |
        v                    v
CalibrationMethod       Diagnostics
        |                    |
        +---------+----------+
                  v
             Evaluation
                  |
                  v
       UncertaintyResult / JSON
                  |
                  v
       Existing horizon curves
```

The estimator layer is independent of Feynman adapters and horizon generation.
A future horizon adapter should simply call the common estimate interface for
each existing scenario and retain scenario provenance.

## Recommended lifecycle

1. Define training, validation, calibration, in-domain test, boundary test,
   and extra-domain test roles before fitting.
2. Fit on training data only.
3. Select methods/settings using validation only.
4. Calibrate on a separate calibration split where required.
5. Freeze all choices.
6. Estimate on untouched evaluation slices.
7. Evaluate point metrics, interval coverage/width, and diagnostics separately
   by domain, direction, distance, and nominal level.
8. Export versioned records with assumptions and split provenance.

Use blocked, grouped, temporal, or spatial splits where observations are
dependent; do not presume random exchangeability.

## Future method extension map (not implemented)

| Module | Intended role | Caveat |
|---|---|---|
| `bayesian.py` | Posterior and posterior-predictive summaries | Credible intervals depend on model and prior |
| `ensemble.py` | Across-member predictions and disagreement | Disagreement is not automatically calibrated |
| `bootstrap.py` | Resampling-based prediction distributions | Resampling unit must match dependence structure |
| `quantile.py` | Conditional quantile predictions | Check quantile crossing and tail extrapolation |
| `shift_aware.py` | Weighted/local/group calibration and shift diagnostics | Requires assumptions and support overlap |
| `calibration.py` | Shared calibration adapters and split metadata | Calibration is not itself an uncertainty estimator |

## Implementation phases

- **Phase 0 (this change):** contracts, estimate container, registries,
  evaluation, JSON schema, documentation.
- **Phase 1:** adapters for supplied ensemble/bootstrap samples and quantile
  outputs; common cross-method contract tests.
- **Phase 2:** Bayesian linear/GP adapters and posterior-predictive summaries.
- **Phase 3:** weighted/local/group conformal with effective sample size,
  overlap, and support diagnostics.
- **Phase 4:** integrate estimates with existing horizon scenarios and compare
  coverage/width against distance.

## Acceptance criteria for future methods

Each method PR should implement the common contract; document capability and
interval semantics; preserve data separation; expose assumptions and guarantee
scope; handle invalid/missing outputs explicitly; emit schema-compatible
records; include deterministic offline tests where possible; and avoid hidden
fitting, tuning, or expensive jobs during reporting.

## Non-goals of this change

No Bayesian inference, ensemble training, bootstrap resampling, quantile
regression, shift-aware calibration, automatic uncertainty estimation,
confidence-interval construction, or horizon orchestration is implemented.
The current split-conformal baseline remains unchanged.
