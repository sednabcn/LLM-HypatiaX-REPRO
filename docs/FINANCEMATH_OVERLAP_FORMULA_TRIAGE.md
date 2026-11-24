# FinanceMath 34-record overlap formula review

**Source pin:** `yale-nlp/FinanceMath` revision `bdc2b6b04252aa09630b66ec1e2a5c98e5a2794c`.  
**Repository baseline:** `master` at `34ff61989da65beca18c9c891b509d46b6609198`.  
**Scope:** inspect the exact question and retained `python_solution` for the 34 records raised by the provisional Core-15/historical-74 keyword screen. This is a formula-level triage of the source candidates against one another. It is not a completed comparison against every canonical Core-15 and historical-74 expression.

## Outcome

The 34 records do not represent 34 independent equations. Several are clear same-family matches within FinanceMath itself, including two pairs with the same numerical inputs and same calculation, and other clusters that differ only by values, asset labels, or horizon. Several other records are merely adjacent risk concepts, and two flagged records are clear keyword false positives.

**No record is promoted to calibration or evaluation.** The provisional overlap screen is retained as a lead list, not an exclusion oracle. Final Core-15/historical-74 decisions still require a row-by-row comparison against the pinned canonical formula definitions and source-recovered historical expressions.

## Same-family clusters within the 34-record review set

| Provisional family | Records | Formula-level reason | Handling |
|---|---|---|---|
| Annual VaR from daily variance/volatility | `validation-4`, `test-461` | Same market value, daily variance, 250-day horizon, 95% z-score, square-root-of-time scaling, and same resulting annual VaR expression. Wording differs, calculation and inputs coincide. | Treat as one source item for any family count; retain both IDs as duplicate provenance. |
| Delta-normal single-option VaR | `validation-48`, `validation-186` | Same at-the-money put delta magnitude 0.5, share price 26, daily volatility 1.5%, z=1.645, one-day horizon, and same absolute delta × price × volatility × z expression. | Treat as one source item for any family count; retain both IDs as duplicate provenance. |
| Delta-exposure option/forward VaR | `validation-172`, `test-126`, `test-279`, `test-575` | All calculate a delta-equivalent exposure multiplied by underlying price, volatility, normal quantile, and square-root-of-time. Position aggregation and horizon scaling differ, but the underlying delta-normal family is shared. | One broad family, not four independent units. Keep parameterization and instrument mix as subtypes only if a predeclared taxonomy justifies it. |
| Correlated multi-asset delta-normal VaR | `test-535` | Combines per-asset delta-normal risk contributions with a covariance/correlation cross-term and horizon scaling. | Related to delta-normal VaR, but preserve as a multivariate aggregation subtype; do not count it as independent merely because there are two assets. |
| Duration-based interest-rate VaR | `validation-180` | Dollar-duration exposure multiplied by yield volatility and a normal quantile. | Distinct risk-factor representation; compare canonical duration/rate-risk equations before deciding overlap. |
| Delta-gamma risk approximation | `validation-193` | Uses first- and second-order price-shift terms, including one-half gamma times squared price shift. | Distinct nonlinear approximation; exact canonical comparison still required. |
| Duration-convexity price change | `test-152` | Uses duration times yield change plus one-half convexity times squared yield change. | Related to duration risk but not the same output or calculation as duration-only VaR. Review component overlap rather than auto-exclude. |
| Portfolio variance/volatility | `test-367` | Computes weighted variances plus the two-asset covariance term, then square-roots the result. | One portfolio-moment family; exact comparison to canonical portfolio variance formula required. |
| Component contribution to VaR | `validation-171` | Calculates each asset's value-weighted marginal VaR, sums components, and takes one component's percentage share. | Related to portfolio VaR but a contribution/decomposition equation, not the same as total VaR. |
| Perfect-correlation VaR aggregation | `test-945` | Adds two standalone VaRs under perfect correlation. | Aggregation boundary case; review against canonical aggregation formula, do not treat as independent from portfolio VaR solely due to a separate question. |
| VaR change after portfolio reweighting | `test-30` | Computes two portfolio VaRs from supplied mean/volatility summaries and subtracts them. | Related to portfolio VaR; a comparison/difference wrapper, not a new risk equation. |
| Normal parametric VaR | `test-283` | Computes a normal-quantile loss measure from mean and standard deviation. | Broad parametric VaR family; exact sign convention and canonical formula comparison required. |
| VaR backtest acceptance bound | `test-181`, `test-333` | Both use expected exceedances plus a z-score times a binomial standard-deviation term, then integer truncation. Horizons and tail probabilities differ. | One binomial acceptance-bound family, not two independent units. |
| Expected VaR exceedance count | `test-301`, `test-582` | Both compute tail probability multiplied by observation count. | One expected-exceedance family, not two independent units. |
| Sharpe ratio after combining benchmark and active fund | `test-613`, `test-624` | Both use square-root of benchmark Sharpe squared plus information ratio squared. Inputs differ, equation family is the same. | One family, not two independent units. |

## Related risk concepts that should not be collapsed without a declared taxonomy

| Record | Retained calculation | Review note |
|---|---|---|
| `test-97` | Portfolio VaR minus asset-1 VaR | A simple difference of two supplied risk values. Related to VaR decomposition but not evidence of the underlying portfolio risk formula. |
| `test-243` | Notional minus expected loss from a default probability | Simplified credit-loss calculation. The text's perfect default correlation and confidence-level framing are not reflected in a full credit portfolio quantile calculation. |
| `test-345` | Annual default probability divided by 12, then expected loss subtracted from bond value | Simplified monthly expected-loss calculation; not automatically equivalent to credit VaR. |
| `test-340` | Linear interpolation between empirical order statistics | Historical/hybrid quantile interpolation, not the parametric normal VaR family. |
| `test-911` | Minimum of an LTV loan cap and a DSCR-derived loan cap | Includes component finance ratios, but the target is constrained loan sizing rather than a risk equation. |
| `test-271` | Returns a constant equal to the stated mean of a loss-intensity distribution | The solution does not implement an expected-shortfall quantile/integral calculation; treat as a questionable solution, not a validated ES formula. |
| `test-94` | Squares IR/IC to infer breadth | Active-management breadth relation, not VaR. |
| `test-257` and `test-310` are not in this 34-record overlap set; do not silently add them to the overlap count. | | |

## Provisional false positives

- `test-129` calculates sustainable growth as retained earnings rate multiplied by ROE. The word “Kelly” is a person name in the question; it is not the Kelly criterion.
- `test-735` subtracts liabilities from assets to calculate economic net worth. The candidate names and wording that triggered the lexical match do not make this a VaR or Core-15 equation.

## Final adjudication still required

The following must happen before any overlap status is finalized:

1. Compare each candidate's normalized mathematical expression—not only question wording or code text—to each applicable Core-15 canonical equation in `hypatiax/experiments/benchmarks/exp1_ablation.py`.
2. Compare against the exact historical-74 formula evidence, including formulas recovered from original source material. Record whether each comparison is exact, algebraically equivalent, same broad family, component overlap, related concept, or false positive.
3. Have a second reviewer independently adjudicate borderline cases, especially multivariate aggregation, duration/convexity, VaR contribution, and credit-loss calculations.
4. Assign one global family ID to all equivalent/reparameterized records across source splits. A question row, code variant, parameter change, prompt variation, or repeated seed is not a new independent equation family.
5. Keep the validation/test source split as provenance only. Do not infer family independence from the split. Do not populate calibration/evaluation manifests from this triage.

## Non-claims

This review does not certify the FinanceMath pool as independent, does not finalize Core-15/historical-74 exclusions, does not prove that any mathematical category has 59 eligible families, and does not authorize formula generation, model/provider calls, experiments, seed sweeps, or tau calibration. The fail-closed `degradation_tau: null` policy remains unchanged.
