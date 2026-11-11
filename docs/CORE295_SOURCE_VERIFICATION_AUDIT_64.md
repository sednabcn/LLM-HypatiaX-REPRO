# Core-295 source verification audit 64: Acerbi–Tasche coherent expected shortfall and normal closed form

**Date:** 2026-11-11  
**Status:** verification of the author-pool normal expected-shortfall lead; source RISK-ACERBI-TASCHE-2002 is registered as candidate_reference. No equation is added to the formal catalogue or counted toward 295.

## 1. Primary source

Carlo Acerbi and Dirk Tasche, “On the Coherence of Expected Shortfall,” *Journal of Banking & Finance*, 26(7), 1487–1503 (July 2002), DOI 10.1016/S0378-4266(02)00283-2.

The paper distinguishes several quantities that are often conflated: expected shortfall, tail conditional expectation, worst conditional expectation, conditional VaR and tail mean. It gives a quantile-integral representation of coherent expected shortfall and explains why naive conditional expectation beyond VaR can fail to be coherent for discontinuous loss distributions.

## 2. Coherent expected-shortfall definition

For a loss random variable \(L\) with finite expectation and confidence level \(\alpha\in(0,1)\), the quantile-integral form is:
\[
ES_\alpha(L)=\frac{1}{1-\alpha}
\int_\alpha^1 VaR_u(L)\,du.
\]
This is the average of the upper-tail quantiles over the worst \(1-\alpha\) probability mass. It is not merely the \(\alpha\)-quantile \(VaR_\alpha\).

For continuous loss distributions, this coincides with:
\[
ES_\alpha(L)=E[L\mid L\geq VaR_\alpha(L)].
\]
For distributions with atoms at the quantile, the naive conditional-expectation expression can differ and may lose coherence. The Acerbi–Tasche definition includes the required quantile-mass correction. A Core-295 adapter must therefore declare whether its loss distribution is assumed continuous or whether it implements the general quantile-integral definition.

## 3. Normal-distribution closed form

For \(L\sim\mathcal N(\mu,\sigma^2)\), the distribution is continuous. Let \(z_\alpha=\Phi^{-1}(\alpha)\), and let \(\phi,\Phi\) denote the standard normal density and CDF. Then:
\[
VaR_\alpha(L)=\mu+\sigma z_\alpha,
\]
and integrating the upper normal tail gives:
\[
ES_\alpha(L)=
\mu+\sigma\frac{\phi(z_\alpha)}{1-\alpha}.
\]
This is a derived normal specialization of the general ES definition, not a separate primary equation in Acerbi–Tasche. The sign changes if the input is a return rather than a loss; the benchmark must freeze the loss convention.

## 4. Structural classification

Expected shortfall is structurally distinct from VaR:
- VaR is a quantile functional;
- ES averages the quantile function across the tail and is sensitive to the magnitude of losses beyond VaR;
- the normal ES formula is a parametric specialization of the general ES functional.

The conditional-tail-mean form, quantile-integral form, CVaR terminology and normal closed form must not be counted as separate independent equation samples. ES is not automatically excluded by the Core-15 VaR exclusion, but the policy must state whether the exclusion covers only the VaR quantile or the broader parametric-tail-risk family.

## 5. DeFi adapter and limitations

A DeFi risk adapter must define the loss variable (e.g. protocol portfolio loss, collateral shortfall, liquidation loss), valuation horizon, confidence level, loss sign convention, sampling frequency, distribution assumption and handling of discontinuities/default atoms. A normal approximation may be poor for jump-driven cryptoasset losses, oracle discontinuities, MEV and liquidation cascades. The closed form should not be treated as a universal crypto-risk distribution.

## 6. Decision

**Disposition:** retain expected shortfall as a strong DeFi Risk statistical-measure lead, distinct from VaR but linked through the same tail-risk distribution. Source RISK-ACERBI-TASCHE-2002 is registered as candidate_reference. Hold the normal ES equation pending the Core-15 VaR-family exclusion ruling and a DeFi loss-variable/horizon contract. Do not count ES definitions, CVaR synonyms, normal specialization and quantile-integral rearrangements separately.

No formal equation-catalogue record was added or accepted. The source register count is 132, with 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, risk estimates, calibrations, data downloads, validators, solvers, workflows, paid compute, API calls or on-chain reads were run. This is source and mathematical review only.
