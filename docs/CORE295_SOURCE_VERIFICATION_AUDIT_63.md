# Core-295 source verification audit 63: Black–Cox first-passage structural default model

**Date:** 2026-11-11  
**Status:** new peer-reviewed primary research lead; no equation is added to the formal catalogue or counted toward 295.

## 1. Primary source

Fischer Black and John C. Cox, “Valuing Corporate Securities: Some Effects of Bond Indenture Provisions,” *The Journal of Finance*, 31(2), 351–367 (May 1976), DOI 10.1111/j.1540-6261.1976.tb01891.x.

The paper extends the Merton structural-credit model by allowing default/reorganization before debt maturity when firm value first reaches a safety-covenant barrier. It explicitly derives the risk-neutral distribution of firm value with an absorbing barrier and calls the resulting survival probability the complementary first-passage-time distribution.

## 2. Asset process and time-dependent barrier

In the geometric-diffusion specialization, firm asset value \(V_t\) follows:
\[
\frac{dV_t}{V_t}=(r-a)\,dt+\sigma\,dW_t,
\]
where \(r\) is the risk-free rate, \(a\) is the payout yield, and \(\sigma\) is asset volatility under the risk-neutral measure.

The safety-covenant boundary is:
\[
K(t)=C e^{-\gamma(T-t)}.
\]
Default/reorganization occurs at:
\[
\tau^*=\inf\{s\ge t:V_s\le K(s)\}.
\]
Unlike Merton's terminal-only default condition \(V_T<B\), this model triggers at the first barrier crossing during the life of the debt.

## 3. First-passage survival probability

Black and Cox's Eq. (7) gives the probability that the firm value at a future time \(\tau\) exceeds a level \(K\) and has not reached the covenant boundary in the meantime:
\[
\begin{aligned}
S(\tau;K)=&
\Phi\!\left(
\frac{\ln V-\ln K+(r-a-\tfrac12\sigma^2)(\tau-t)}
{\sigma\sqrt{\tau-t}}
\right)\\
&-\left(\frac{V}{C e^{-\gamma(T-t)}}\right)^{1-\frac{2(r-a-\gamma)}{\sigma^2}}
\Phi\!\left(
\frac{2\ln(Ce^{-\gamma(T-t)})-\ln V-\ln K
+(r-a-\tfrac12\sigma^2)(\tau-t)}
{\sigma\sqrt{\tau-t}}
\right).
\end{aligned}
\]
Setting \(K=C e^{-\gamma(T-\tau)}\) gives the risk-neutral probability of surviving without reorganization through time \(\tau\). The cumulative first-passage default probability is:
\[
PD_{BC}(\tau)=1-S(\tau;K(\tau)).
\]

For a constant barrier \(K\) (\(\gamma=0\)), define \(x=\ln(V/K)>0\), \(\nu=r-a-\tfrac12\sigma^2\), and \(\Delta=\tau-t\). The expression simplifies to:
\[
PD_{BC}(\Delta)=
\Phi\!\left(\frac{-x-\nu\Delta}{\sigma\sqrt{\Delta}}\right)
+\exp\!\left(-\frac{2\nu x}{\sigma^2}\right)
\Phi\!\left(\frac{-x+\nu\Delta}{\sigma\sqrt{\Delta}}\right).
\]
This is the standard reflection-principle first-passage probability for log asset value with a constant lower barrier.

## 4. Structural classification

The Black–Cox model is related to Merton (1974) through the same structural-credit/GBM family, but its default event is different:
- Merton: terminal default if \(V_T\) is below the debt face value;
- Black–Cox: default at any time if \(V_t\) first crosses a covenant barrier.

For the same process and comparable barrier, first-passage default probability is at least as large as terminal-only default probability because it includes paths that cross the barrier and later recover before maturity.

This is not a generic Brownian hitting-probability formula detached from credit structure: the barrier represents a debt covenant/reorganization threshold. A DeFi adaptation could use a liquidation/health boundary, but must account for protocol-specific partial liquidations, debt accrual, collateral changes and oracle updates; those dynamics are absent from the basic model.

## 5. Decision

**Disposition:** retain as a strong DeFi Risk first-passage model lead. Add Black–Cox (1976) to the source register as candidate_reference only. Keep it grouped with Merton structural credit models for source-family/independence purposes, while recording the terminal-default versus first-passage distinction. Hold pending a DeFi collateral/liquidation barrier mapping and the structural-equivalence rule; do not count the survival probability, default probability and debt valuation as separate equation entries.

No experiments, simulations, calibrations, data downloads, validators, solvers, workflows, paid compute, API calls, on-chain reads or transactions were run. This is primary-paper mathematical review only.
