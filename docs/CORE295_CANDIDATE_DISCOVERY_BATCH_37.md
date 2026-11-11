# Core-295 candidate discovery batch 37: stochastic volatility and reserve-ruin risk

**Date:** 2026-11-11  
**Status:** discovery-only source leads. No equation is added to the formal catalogue or counted toward 295.  
**Domain focus:** DeFi Risk / financial risk.

## 1. Heston stochastic-volatility process

**Primary source:** Steven L. Heston (1993), *A Closed-Form Solution for Options with Stochastic Volatility with Applications to Bond and Currency Options*, Review of Financial Studies 6(2), 327–343, DOI 10.1093/rfs/6.2.327.

Under the physical measure, a common Heston process representation is:
\[
\frac{dS_t}{S_t}=\mu\,dt+\sqrt{V_t}\,dW_t^S,
\]
\[
dV_t=\kappa(\theta-V_t)dt+\xi\sqrt{V_t}\,dW_t^V,
\qquad
dW_t^S\,dW_t^V=\rho\,dt.
\]
Here \(S_t\) is the asset price, \(V_t\) instantaneous variance, \(\kappa\) mean-reversion speed, \(\theta\) long-run variance, \(\xi\) volatility of variance, and \(\rho\) correlation between the Brownian drivers.

**Structural value:** a coupled price/variance stochastic system with correlated noise and state-dependent variance diffusion. It is not simply a CIR variance process plus a fixed-volatility GBM; the correlation couples price shocks and variance shocks. Heston's closed-form option-price characteristic function is a derived pricing result, not a separate stochastic-process equation.

**Boundary and risks:** distinguish physical and risk-neutral measures; ensure \(V_t\geq0\); specify Feller condition \(2\kappa\theta\geq\xi^2\) if strict positivity is required; freeze correlation, time scale, drift/risk-free rate, dividend/yield convention and initial variance. The Heston model's variance component is CIR-like; do not count that component separately from the full Heston system if the chosen unit is the coupled model.

**DeFi-risk use:** potential stochastic-volatility model for token returns and options, but not a deterministic protocol borrow-rate model. Domain eligibility depends on including token-market risk.

**Initial disposition:** high-value stochastic system lead; hold pending measure, calibration and coupled-SDE adapter.

## 2. Cramér–Lundberg reserve process and ruin probability

**Sources:** classical Lundberg/Cramér collective-risk model; authoritative modern actuarial risk literature. The model is directly relevant as an analogue for a protocol insurance/coverage reserve exposed to random payouts.

The reserve process is:
\[
U_t=u+ct-\sum_{k=1}^{N_t}X_k,
\]
where \(u\geq0\) is initial reserve, \(c>0\) continuous premium/income rate, \(N_t\) a Poisson claim-count process with intensity \(\lambda\), and \(X_k\) i.i.d. nonnegative claim/payout sizes independent of \(N_t\).

The ruin time and infinite-horizon ruin probability are:
\[
\tau_u=\inf\{t\geq0:U_t<0\},
\qquad
\psi(u)=\Pr(\tau_u<\infty).
\]
The net-profit condition is \(c>\lambda E[X]\). For exponentially distributed claim sizes with mean \(\mu\) and relative premium loading \(\vartheta=c/(\lambda\mu)-1>0\), the exact ruin probability is:
\[
\psi(u)=\frac{1}{1+\vartheta}
\exp\left[-\frac{\vartheta u}{(1+\vartheta)\mu}\right].
\]

**Structural value:** a reserve process with deterministic premium inflow and compound-Poisson jump outflows; the ruin probability is a first-passage risk functional of the complete process. It is not an ordinary expected-loss calculation.

**Boundary and risks:** claims/payouts are independent and identically distributed; claim arrivals are Poisson; premium/income flow is continuous and constant; claim amounts are independent of arrivals. DeFi protocol liquidations may be clustered and correlated with asset prices, violating these assumptions. The exponential-claim closed form is one distribution-specific result, not a generic ruin formula.

**DeFi-risk use:** potential solvency model for protocol insurance funds, backstop reserves or coverage pools under random payouts. It must not be presented as a model of all liquidation risk without validating claim-arrival and payout assumptions.

**Initial disposition:** strong reserve-solvency lead; hold pending definition of premium/income and claim/payout events, event dependence, claim-size distribution and stochastic first-passage adapter.

## 3. Family and independence notes

| Lead | Structure | Related families | Initial decision |
|---|---|---|---|
| Heston | Coupled price and square-root stochastic variance with correlated Brownian shocks | CIR variance process, GBM price process, stochastic-volatility models | Hold; consider as one complete system |
| Cramér–Lundberg | Linear reserve drift plus compound-Poisson payout jumps; first-passage ruin probability | Hawkes/Poisson event models, Merton jump processes, insurance solvency models | Hold; consider as one reserve-risk system |

Heston's CIR variance component, Heston option-pricing solution and no-stochastic-volatility limits are not separate candidates. Cramér–Lundberg's reserve equation, ruin time and distribution-specific closed-form ruin probability are components/results of one reserve-risk family, not separate independent units.

## 4. Catalogue status and work not performed

No source-register or equation-catalogue record was changed. The formal manifest remains 128 source records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, validators, solvers, workflows, paid compute, API calls, market-data retrieval or stochastic simulations were run. This is source discovery only.
