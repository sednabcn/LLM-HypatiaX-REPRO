# FinanceMath candidates against the 70 artifact-stored historical formulas

**FinanceMath source:** `yale-nlp/FinanceMath@bdc2b6b04252aa09630b66ec1e2a5c98e5a2794c`  
**Historical artifact:** workflow run `45038667467`, artifact `14760901742`, file `routing_tau_calibration.json`  
**Artifact SHA-256:** `ddfc8fdc28a12db6615005629d01141d369d1978c5fe685e69c750b20f2aa5db`  
**Historical protocol source:** `hypatiax/protocols/experiment_protocol_defi.py` at `107fcd6da06fe15833ecdf37c6d2284da84256c8`.

## Method and scope

Downloaded and verified the exact workflow artifact by SHA-256. It contains 74 records: 70 with a stored `formula` and four with `formula=null`. This pass compares every one of the 34 FinanceMath candidates from the prior triage against the 70 non-null artifact expressions. The four missing historical formulas are handled separately in the source-recovery audit (PR #333) and the Core-15 comparison (PR #364).

Comparison distinguishes (a) identical or algebraically equivalent equation forms, (b) same mathematical family with changed inputs, parameters, or horizon, (c) shared subexpressions / wrappers, and (d) broad topical similarity only. A matching equation form does not establish independent samples, benchmark independence, or identical financial semantics.

## Candidate-to-historical findings

| FinanceMath candidate(s) | Historical artifact record(s) | Relationship | Adjudication |
|---|---|---|---|
| `test-535` | `Correlated Portfolio VaR`; `Portfolio VaR for two correlated` | The two historical formulas are exactly the same covariance-quadratic aggregator as the inner expression in FinanceMath `test-535`; the FinanceMath formula then applies a 5-day `sqrt(5)` scaling factor. | Direct equation-family overlap. Count as one shared covariance-aggregation family, not an independent new equation family. |
| `test-367` | `Correlated Portfolio VaR`; `Portfolio VaR for two correlated` | After substituting weighted component volatilities (s_1=w_1\sigma_1), (s_2=w_2\sigma_2), the FinanceMath portfolio-volatility equation is the same two-component covariance quadratic. | Direct algebraic equation-family overlap. The target is volatility rather than VaR; preserve the semantic distinction while flagging the common equation. |
| `test-535`, `test-367` | `Portfolio Expected Shortfall for correlated` | Same square-root covariance-aggregation form, with ES components rather than VaR or volatility components. | Same aggregation equation form; different risk metric inputs/semantics. Do not call the outputs equivalent. |
| `validation-4`, `test-461` | `Value at Risk at 95%`; `Value at Risk at 99%`; `Multi-day Value at Risk` | Parametric normal VaR with (\sigma=\sqrt{v_{daily}}), a normal quantile, and square-root-of-time scaling. Historical one-day VaR uses (P\sigma z); the multi-day record supplies the horizon multiplier. | Same parametric VaR family; parameter/horizon variants, not independent families. |
| `validation-48`, `validation-186` | `Value at Risk at 95%`; `Value at Risk at 99%`; `Multi-day Value at Risk` | Delta-normal option VaR is the same parametric VaR form with effective exposure (P_{eff}=|\Delta|S). | Same VaR family with option-delta exposure; not an exact full-expression match. |
| `validation-172`, `test-126`, `test-279`, `test-575` | `Value at Risk at 95%`; `Value at Risk at 99%`; `Multi-day Value at Risk` | Delta-exposure VaR with net position delta, underlying price, volatility, normal quantile, and (where applicable) horizon scaling. | Same parametric VaR family with portfolio exposure/horizon variants. The four records are not four independent formula families. |
| `validation-180` | `Value at Risk at 95%`; `Value at Risk at 99%` | Duration-based yield-risk estimate has the normal-quantile × exposure × volatility structure, with dollar duration as exposure. | Same broad parametric VaR construction; distinct risk-factor parameterization. |
| `test-283` | `Value at Risk at 95%`; `Value at Risk at 99%` | Normal parametric VaR with a nonzero-mean/loss-sign adjustment. | Same normal VaR family, not literal identity to the historical zero-mean formulas. |
| `test-30`, `test-97` | No exact historical formula; conceptually adjacent to recovered `Incremental VaR` | FinanceMath records compute differences between supplied or separately calculated VaR values. The recovered historical expression computes combined covariance risk and subtracts the original risk. | Related incremental-risk/difference concept, not equivalent full equation. |
| `test-613`, `test-624` | `Portfolio Sharpe Ratio` | All concern Sharpe ratio. Historical record computes ((R_p-r_f)/\sigma_p); FinanceMath records combine benchmark Sharpe and information ratio by a root-sum-square relation. | Same metric family, distinct equations and input assumptions. |
| `test-94` | `Information ratio` | FinanceMath uses information ratio as an input to the breadth relation; historical formula calculates information ratio as active return divided by tracking error. | Related metric dependency only; not equation overlap. |
| `test-271` | `Expected Shortfall at 95%`; `Expected Shortfall at 99%`; `Portfolio Expected Shortfall for correlated` | FinanceMath implementation returns a constant stated mean and does not calculate expected shortfall. | Topic/label overlap only; do not treat as a valid ES implementation or matching family. |
| `test-243`, `test-345` | `Value at Risk at 95%`; `Value at Risk at 99%`; ES records | FinanceMath records use simplified default-probability/expected-loss calculations for credit exposures, not the historical parametric market-risk VaR/ES equations. | Related risk domain only; distinct equations and assumptions. |
| `validation-193` | `Gamma of option`; `Convexity Adjustment` | FinanceMath is a delta-gamma P&L approximation. Historical Gamma is the Black–Scholes second derivative; historical Convexity Adjustment is an AMM price-impact adjustment, not bond/option convexity. | Related vocabulary, not equation equivalence. |
| `test-152` | `Convexity Adjustment` | FinanceMath is a duration-convexity bond-price change approximation; historical Convexity Adjustment is (S(1+\Delta x/(2D))), an AMM trade-price adjustment. | Keyword collision; distinct formulas and domains. |
| `test-340` | `Value at Risk at 95%`; `Value at Risk at 99%` | FinanceMath interpolates empirical order statistics for a historical/hybrid quantile; historical formulas use parametric normal quantiles. | Same risk-measure topic, distinct estimator/formula family. |
| `test-181`, `test-333`, `test-301`, `test-582` | VaR and ES records | FinanceMath computes backtest acceptance bounds or expected exception counts; historical VaR/ES formulas calculate risk quantiles/expected shortfall. | Related VaR validation concepts, not the same equation family. |
| `validation-171` | `Portfolio Expected Shortfall for correlated`; correlated VaR records | FinanceMath computes a component's percentage contribution using weighted marginal VaR amounts. Historical formulas aggregate two risk components by a covariance quadratic. | Portfolio-risk decomposition vs portfolio aggregation; no direct formula match. |
| `test-257`, `test-310` | `Annualised Portfolio tracking error` | Both use square-root sample-size scaling in a standard-error calculation; historical tracking error multiplies daily tracking error by (\sqrt{252}). | Shared scaling pattern only; different statistical quantities. |
| `test-30` | `Multi-day Value at Risk` | The candidate computes two daily VaRs from annualized mean/volatility inputs and compares portfolio weights; historical formula scales an already-computed one-day VaR by (\sqrt{T}). | Shared horizon-scaling component, not the same outer equation. |

The remaining candidates from the 34-record set were also inspected against the complete 70-formula list and had no direct or meaningful equation-family match: `test-129`, `test-735`, `test-911`, `test-243` and `test-345` are separately characterized above where only topical similarity exists; `test-126` etc are covered in the VaR rows. In particular, `test-129` is sustainable growth (the word “Kelly” is a person's name), `test-735` is economic net worth, and `test-911` is LTV/DSCR loan sizing. None is a match to the historical formulas.

## Summary decision

- The 70-formula cross-check confirms material overlap in the **parametric VaR family** and in the **two-component covariance aggregation equation**. These are not newly independent FinanceMath families relative to the historical artifact.
- The clearest direct expression overlap is FinanceMath `test-535` with the historical correlated VaR aggregators, and FinanceMath `test-367` with that same covariance-quadratic equation after absorbing portfolio weights into component volatilities.
- Historical correlated ES uses the same algebraic aggregation shape but has different input semantics; it is flagged as shared equation form, not identical risk metric.
- Several candidates are related to historical risk metrics at the family or wrapper level (VaR variants, Sharpe, incremental-risk differences) without being exact formula duplicates.
- Topic words such as “VaR”, “convexity”, “Kelly”, or “Sharpe” are not sufficient to infer formula equivalence.

## Limitations and safeguards

- This is formula-source comparison, not adjudication of statistical independence or benchmark leakage.
- Candidate records are not counted as independent units merely because inputs, labels, question wording, or source splits differ.
- The historical artifact formulas were model-generated outputs; their presence does not prove the formula is mathematically correct. For example, FinanceMath `test-271` itself returns a mean rather than computing ES.
- Four historical formulas absent from the artifact remain source-recovered with distinct provenance as documented in PR #333; they are not silently represented as artifact-stored.
- No registry family IDs, cohort assignments, independence statuses, calibration manifests, routing, or tau values are changed. Keep `degradation_tau: null`. No formula-generation calls, experiments, provider calls, or seed sweeps are part of this audit.
