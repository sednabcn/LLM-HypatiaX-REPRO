# FinanceMath overlap: canonical Core-15 and recovered historical formula comparison

**FinanceMath source pin:** `yale-nlp/FinanceMath@bdc2b6b04252aa09630b66ec1e2a5c98e5a2794c`  
**Repository baseline:** `9d4a71f8a7bcbaaaeee8a5938b9ca5d38b721058`  
**Scope:** compare all 34 keyword-screened FinanceMath records against the exact Core-15 canonical formula definitions and the four historical-74 formulas recovered from the historical protocol source. This is a source-expression audit, not a full historical-74 audit: the 70 formulas stored only in the historical workflow artifact are not reproduced in this repository document and remain to be checked individually.

## Canonical references

Core-15 definitions are read from `hypatiax/experiments/benchmarks/exp1_ablation.py`:

- **Value at Risk:** `P * sigma * 1.645` (zero-mean, one-day parametric normal VaR).
- **Portfolio Std Dev:** `sqrt(s1**2 + s2**2 + 2*rho*s1*s2)`.

The historical-74 review in PR #333 identifies four artifact-missing formulas recovered from `hypatiax/protocols/experiment_protocol_defi.py` at pinned source commit `107fcd6da06fe15833ecdf37c6d2284da84256c8`:

- **Capital efficiency:** `P_upper / (P_upper - P_lower)`.
- **Incremental VaR:** `sqrt(v1**2 + v2**2 + 2*rho*v1*v2) - v1`.
- **Options Delta:** `clip(0.5 + m/(2*vol*sqrt(T)), 0, 1)`.
- **Theta of option:** `-(S*norm_pdf(d1)*sigma)/(2*sqrt(T)) - r*K*exp(-r*T)*norm_cdf(d2)`, using source-defined Black–Scholes `d1` and `d2`.

These four are protocol-source recoveries, not formulas stored in the historical result artifact.

## Candidate-by-candidate comparison

| FinanceMath record(s) | Retained mathematical expression / structure | Core-15 comparison | Recovered historical-74 comparison | Disposition |
|---|---|---|---|---|
| `validation-4`, `test-461` | (P z\sqrt{T}\sqrt{v_{daily}}), with (v_{daily}) supplied as variance | Same parametric VaR family as (P\sigma z), with square-root-of-time scaling and (sigma=\sqrt{v}) | No direct match to the four recovered expressions | One same-family source cluster; do not count twice |
| `validation-48`, `validation-186` | (z\,|\Delta|\,S\,\sigma) | Same VaR formula with effective exposure (P_{eff}=|\Delta|S) | No direct match to the four recovered expressions | Same equation family and duplicate pair |
| `validation-172`, `test-126`, `test-279`, `test-575` | (z\,S\,\text{net delta}\,\sigma\sqrt{T}) | Same delta-normal VaR family with effective portfolio exposure and horizon scaling | No direct match to the four recovered expressions | One broad delta-exposure family, not four independent units |
| `validation-180` | Dollar-duration exposure × yield volatility × normal quantile | Same parametric normal VaR structure with dollar-duration as effective exposure | No direct match to the four recovered expressions | Same broad VaR family; different risk-factor parameterization |
| `test-283` | (z\sigma-\mu) (loss-sign convention) | Same normal parametric VaR family with nonzero-mean adjustment; not literal identity to the zero-mean Core-15 instance | No direct match to the four recovered expressions | Same family, parameterization differs |
| `test-535` | Square root of two delta-normal VaR components squared plus correlation cross-term, then (sqrt{T}) | Multivariate/correlated extension of parametric VaR; shares covariance aggregation structure with Core-15 Portfolio Std Dev | Shares the covariance-quadratic core of recovered Incremental VaR, but not its subtract-old-risk output | Component/family overlap; do not treat as independent from portfolio-risk families |
| `test-367` | (sqrt{w_1^2\sigma_1^2+w_2^2\sigma_2^2+2w_1w_2\rho\sigma_1\sigma_2}) | Algebraically the Core-15 Portfolio Std Dev equation after substituting (s_1=w_1\sigma_1), (s_2=w_2\sigma_2) | Shares the portfolio-risk quadratic core in recovered Incremental VaR, but does not subtract the old portfolio risk | Direct same-family match to Core-15 Portfolio Std Dev; component overlap with Incremental VaR |
| `validation-171` | Component VaR amounts and one component's percentage contribution | Related VaR decomposition; not the canonical total-VaR equation | No direct match to the four recovered expressions | Component/decomposition calculation, not a new independent VaR family |
| `test-30` | Difference between two daily parametric VaR values after portfolio reweighting | Uses the VaR family as a subcalculation; outer expression is a reweighting-difference wrapper | Related in output form to incremental-risk comparisons, but does not implement the recovered Incremental VaR formula | Related calculation; not exact formula equivalence |
| `test-97` | Difference between supplied portfolio VaR and supplied asset VaR | VaR difference wrapper; no canonical VaR formula is computed | Related difference concept, not the recovered Incremental VaR equation | Related concept only |
| `test-945` | Sum of two supplied VaRs under perfect correlation | Boundary-case aggregation of VaR components; not the Core-15 single-exposure VaR formula | Not the recovered Incremental VaR expression | Related aggregation case |
| `validation-193` | (Delta(-\Delta S)+\frac12\Gamma(\Delta S)^2) | Delta-gamma nonlinear risk approximation; not the Core-15 linear parametric VaR equation | No direct match to the four recovered expressions | Related risk measure; distinct equation family |
| `test-152` | (-D\Delta y+\frac12 C(\Delta y)^2) | Duration-convexity bond-price approximation, not VaR | No direct match to the four recovered expressions | Related rate-risk concept, different target and equation |
| `test-181`, `test-333` | Expected binomial exceedances plus a normal-quantile multiple of binomial standard deviation | VaR backtesting acceptance bound, not the VaR equation itself | No direct match to the four recovered expressions | One backtest-bound family, not independent VaR formula units |
| `test-301`, `test-582` | Tail probability × observation count | Expected exception count, not VaR | No direct match to the four recovered expressions | One expected-exceedance family |
| `test-340` | Linear interpolation between empirical order statistics | Historical quantile interpolation, not parametric normal VaR | No direct match to the four recovered expressions | Distinct empirical-quantile method |
| `test-243`, `test-345` | Notional less a simplified expected credit loss | Credit-loss calculation, not the Core-15 parametric VaR equation | No direct match to the four recovered expressions | Related credit-risk concepts; not formula-equivalent |
| `test-257`, `test-310` | Sample standard deviation divided by square root of sample size | Standard error of a sample mean, not VaR | No direct match to the four recovered expressions | Distinct statistical quantity |
| `test-271` | Returns the stated mean as a constant | Does not implement expected shortfall or Core-15 VaR | No direct match to the four recovered expressions | Invalid as an ES formula reference; do not classify as a validated ES family |
| `test-613`, `test-624` | (sqrt{SR_B^2+IR^2}) | No matching Core-15 formula | No direct match to the four recovered expressions | One Sharpe/information-ratio family |
| `test-94` | ((IR/IC)^2/TC) | No matching Core-15 formula | No direct match to the four recovered expressions | Active-management breadth relation |
| `test-129` | Retention rate × ROE | No matching Core-15 formula | No direct match to the four recovered expressions | Keyword false positive: sustainable growth |
| `test-735` | Assets − liabilities | No matching Core-15 formula | No direct match to the four recovered expressions | Keyword false positive: economic net worth |
| `test-911` | Minimum of LTV and DSCR loan caps | No matching Core-15 formula | No direct match to the four recovered expressions | Loan-sizing constraint, not a risk equation |

## Key adjudications

1. **Core-15 Value at Risk overlap is real at the equation-family level.** The annual, delta-normal option/forward, duration-based, and nonzero-mean parametric records are reparameterizations or horizon/risk-factor extensions of (P\sigma z). This does not mean every such record is literally the same expression or the same independent equation family as every other record.
2. **Core-15 Portfolio Std Dev overlap is direct.** `test-367` reduces exactly to the canonical two-asset portfolio standard-deviation equation by absorbing portfolio weights into the component volatilities.
3. **Historical Incremental VaR has a shared covariance-quadratic core.** `test-535` and `test-367` contain that core; `test-30` and `test-97` are related difference wrappers. None is a literal match to the full recovered Incremental VaR output (\sqrt{v_1^2+v_2^2+2\rho v_1v_2}-v_1).
4. **The other three recovered historical formulas have no direct candidate match among these 34 records.** This statement is limited to the four recovered expressions, not the 70 artifact-stored historical formulas.

## Remaining work and non-claims

- The historical artifact contains 70 stored formulas. A row-by-row comparison of all 34 candidates against those 70 expressions is still required before any final historical-74 exclusion decision. The current repository document does not embed those 70 expressions, and this audit does not infer their content from formula names.
- The candidate-to-Core-15 findings above are formula-family comparisons; borderline cases should receive a second independent reviewer.
- Do not populate registry family IDs, change cohort assignments, or treat source train/validation/test labels as family independence.
- Do not modify calibration manifests, routing, or tau. Keep `degradation_tau: null`; no formula generation, provider calls, experiments, or seed sweeps are part of this audit.
