# Core-295 candidate discovery batch 28: market volatility and structural credit-risk models

**Date:** 2026-11-11  
**Status:** discovery-only source leads. No equation is added to the formal catalogue or counted toward the 295 target.  
**Domain focus:** DeFi Risk / financial risk. These are general financial-risk methods; their eligibility depends on whether the DeFi Risk domain contract includes token-market and portfolio credit risk in addition to protocol-specific safety rules.

## 1. Parkinson high-low range variance estimator

**Primary source:** Michael Parkinson (1980), *The Extreme Value Method for Estimating the Variance of the Rate of Return*, Journal of Business 53(1), 61–65, DOI 10.1086/296071. The paper is accessible as a scan.

For (n) equally spaced observation intervals, with (H_i) and (L_i) the high and low prices in interval (i), Parkinson's variance estimator is
[
\widehat{\sigma}^2_P
=\frac{1}{4n\ln 2}
\sum_{i=1}^{n}
\left[\ln\left(\frac{H_i}{L_i}\right)\right]^2.
]
The original paper derives the range statistic under a one-dimensional continuous random walk with zero drift, then applies it to log prices and financial return variance. It reports the single-interval relation (E[l^2]=4\ln(2)D), where (l=\ln(H/L)) and (D) is the diffusion/variance parameter per unit interval.

**Boundary and risks:** high and low must be positive and from the same interval; sampling intervals must be equally defined; the estimator assumes a driftless continuous diffusion and does not capture opening jumps/overnight gaps. It can be biased under drift, jumps, microstructure noise or non-continuous trading. Do not count the equivalent coefficient (0.361), standard-deviation square root, annualization or unit conversions as new equations.

**Initial disposition:** strong source lead for range-based market volatility; hold pending token-market domain scope, sampling interval, price-source and drift/jump assumptions.

## 2. GARCH(1,1) conditional variance recursion

**Primary source:** Tim Bollerslev (1986), *Generalized autoregressive conditional heteroskedasticity*, Journal of Econometrics 31(3), 307–327, DOI 10.1016/0304-4076(86)90063-1.

The canonical GARCH(1,1) variance recursion is
[
\sigma_t^2=\omega+\alpha\epsilon_{t-1}^2+\beta\sigma_{t-1}^2,
]
where (epsilon_t) is the innovation and (sigma_t^2) its conditional variance. The model generalizes ARCH by including lagged conditional variance. The original paper derives stationarity and autocorrelation conditions; a common covariance-stationary parameter contract is (omega>0), (alpha,eta\geq0), (alpha+eta<1), under the standard innovation assumptions.

**Boundary and risks:** the recursion is one time-series model family, not an instantaneous risk formula. A deterministic adapter must define the innovation distribution, initialization, time index, return convention, likelihood/forecast target and stationarity domain. Do not count GARCH(p,q), parameter variants or one-step forecasts as independent equation structures without a predeclared model-family rule.

**Initial disposition:** high-value financial risk model lead; verify exact original notation and freeze return/innovation and stationarity contract.

## 3. RiskMetrics EWMA conditional variance

**Source:** RiskMetrics Technical Document, Fourth Edition, December 1996.

The standard EWMA variance recursion is
[
\sigma_t^2=\lambda\sigma_{t-1}^2+(1-\lambda)r_{t-1}^2,
qquad 0<\lambda<1.
]
The RiskMetrics document uses a daily decay factor of 0.94 as its standard daily setting and describes the effective historical weighting/observation horizon.

**Structural warning:** EWMA is an integrated special case of GARCH(1,1) with (omega=0), (alpha=1-lambda), (eta=lambda), so (alpha+eta=1). It is therefore not a second structurally independent model under a strict equation-family rule. It also differs from covariance-stationary GARCH because it is an IGARCH boundary case with no mean reversion in variance.

**Initial disposition:** retain as an implementation/configuration member of the GARCH/conditional-variance family, not a separate candidate count.

## 4. Normal-distribution expected shortfall

**Sources:** Basel Committee, *Minimum capital requirements for market risk* (MAR 33); authoritative risk-management references for the normal parametric closed form.

For a loss variable (L\sim\mathcal N(\mu,\sigma^2)), confidence level (alpha), standard normal density (phi) and quantile (z_\alpha=\Phi^{-1}(\alpha)):
[
ES_\alpha
=\mu+\sigma\frac{\phi(z_\alpha)}{1-\alpha}.
]
For returns rather than losses, the sign and mean convention changes; do not copy the loss formula into a return convention without an explicit sign transformation.

**Structural value:** expected shortfall is the conditional mean of the loss tail, not the quantile used by VaR. Core-15 excludes VaR, but that does not automatically exclude ES; the formula has a different functional dependence on the normal density and tail probability. It is nevertheless derived from the same normal distribution and shares (mu,sigma,alpha) inputs with parametric VaR.

**Boundary and risks:** the closed form requires normal losses and a continuous distribution; it is not a generic empirical/historical ES estimator. Freeze loss sign, confidence level, horizon, mean and standard-deviation units. Do not count VaR and ES as independent observations if the statistical unit is a common portfolio/distribution instance.

**Initial disposition:** credible distinct tail-risk functional; hold pending authoritative source page and explicit Core-15 VaR exclusion interpretation.

## 5. Merton structural credit-risk model and distance-to-default

**Primary source:** Robert C. Merton (1974), *On the Pricing of Corporate Debt: The Risk Structure of Interest Rates*, Journal of Finance 29(2), 449–470, DOI 10.1111/j.1540-6261.1974.tb03058.x.

Merton models firm asset value (V_t) as a diffusion and treats equity as a call option on firm assets with strike equal to promised debt (B) at maturity (T). The default event at maturity is (V_T<B). The paper derives the risky-debt value and equity option value from this structural model.

A commonly used derived distance-to-default statistic is
[
DD=
\frac{\ln(V_0/B)+(\mu_V-\tfrac12\sigma_V^2)T}
{\sigma_V\sqrt{T}},
]
with the precise drift convention depending on whether the model uses physical expected asset return or risk-neutral drift. This statistic is not printed as the single defining equation in Merton's paper; it is a standardized asset-to-default-boundary distance derived from the asset process.

**Boundary and risks:** assets and debt are not directly observed in many firms; asset volatility and drift require estimation; capital structure is simplified to a single zero-coupon debt claim in the canonical model. The benchmark must not conflate physical default probability with risk-neutral debt pricing. The full Merton model is a structural credit system; DD is a derived summary statistic, not an independent second equation.

**Initial disposition:** high-value structural credit-risk source lead; hold pending explicit selection of full model vs derived DD output, drift measure, liability boundary and data-generation contract.

## 6. Batch-level structural decisions

| Lead | Mathematical structure | Relationship | Initial decision |
|---|---|---|---|
| Parkinson range variance | Sum of squared log high/low ranges | Distinct range-based estimator; related to Brownian diffusion assumptions | Hold; consider |
| GARCH(1,1) | Conditional variance recursion with lagged squared innovation and lagged variance | ARCH generalization; one conditional-variance family | Hold; consider |
| EWMA | Exponentially weighted variance recursion | GARCH(1,1) IGARCH boundary special case | Do not count separately |
| Normal ES | Normal density at tail quantile divided by tail probability | Distinct from VaR, but same distribution/portfolio unit | Hold; consider |
| Merton structural credit | Asset-value diffusion with default boundary | DD is a derived statistic; full model is one structural credit family | Hold; consider |

The batch provides five source leads, not five independent equations. GARCH and EWMA are one family; Merton's full structural model and DD are not separate entries. The DeFi Risk scope must be defined before importing general financial market-risk models.

## 7. Catalogue status and work not performed

No source-register or equation-catalogue record was changed. The formal manifest remains 128 source records, 19 proposed equation records, zero accepted equations, and an unfrozen sampling frame.

No experiments, validators, solvers, workflows, paid compute, API calls, market-data retrieval or risk-model fitting were run. This is source discovery only.
