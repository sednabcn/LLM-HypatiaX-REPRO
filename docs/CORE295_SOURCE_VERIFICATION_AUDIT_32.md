# Core-295 source verification audit 32: Heston stochastic-volatility process and Cramér–Lundberg reserve ruin

**Date:** 2026-11-11  
**Status:** verification of discovery-batch 37 leads only. No equation is added to the formal catalogue or counted toward 295.

## 1. Heston 1993 stochastic-volatility model

### Original equations

Steven L. Heston, *A Closed-Form Solution for Options with Stochastic Volatility with Applications to Bond and Currency Options*, Review of Financial Studies 6(2) (1993), 327–343, DOI 10.1093/rfs/6.2.327. The original paper PDF is accessible.

On printed p. 328, the original model gives:
\[
dS(t)=\mu S\,dt+\sqrt{v(t)}S\,dz_1(t) \tag{1}
\]
and then writes the variance process in the familiar square-root form:
\[
dv(t)=\kappa[\theta-v(t)]dt+\sigma\sqrt{v(t)}\,dz_2(t), \tag{4}
\]
where \(z_2(t)\) is a Wiener process correlated with \(z_1(t)\) by correlation \(\rho\). The paper's Eq. (3) derives this variance process from an Ornstein–Uhlenbeck process for \(\sqrt{v(t)}\).

The original paper then introduces a volatility-risk-premium parameter \(\lambda\). Under the risk-neutralized pricing probabilities, the variance process changes to Eq. (27):
\[
dv(t)=\kappa^*[\theta^*-v(t)]dt+\sigma\sqrt{v(t)}\,dz_2(t),
\]
with
\[
\kappa^*=\kappa+\lambda,\qquad
\theta^*=\frac{\kappa\theta}{\kappa+\lambda}.
\]
Thus the physical-measure process and risk-neutral pricing process must not be conflated. The price drift \(\mu\) in Eq. (1) is the physical drift; the pricing PDE and characteristic-function solution use risk-neutralized parameters.

### Structural boundary

Heston is one coupled price/variance system. The square-root variance component is CIR-like, and the no-stochastic-volatility limit is a nested special case; neither is an independent equation candidate when the selected unit is the complete Heston model. The option-pricing PDE, characteristic function and closed-form call-price integral are derived pricing machinery, not additional stochastic-process candidates.

**Disposition:** primary process equations and measure distinction verified. Retain as a strong discovery lead, pending a declared physical/risk-neutral adapter, correlation and positivity/stationarity constraints, and a domain ruling on stochastic token-market risk.

## 2. Cramér–Lundberg reserve process and exponential-claim ruin probability

### Process and assumptions

The classical collective-risk surplus process is
\[
U_t=u+ct-\sum_{k=1}^{N_t}X_k,
\]
where \(u\) is initial reserve, \(c\) constant premium/income rate, \(N_t\) a Poisson process with intensity \(\lambda\), and \(X_k\) i.i.d. claim sizes independent of arrivals. The net-profit condition is
\[
c>\lambda E[X].
\]
The ruin probability is
\[
\psi(u)=\Pr\left(\inf_{t\geq0}U_t<0\right).
\]

For exponential claim sizes with mean \(\mu\), and premium loading \(\vartheta\) defined by
\[
c=(1+\vartheta)\lambda\mu,\qquad \vartheta>0,
\]
the exact infinite-horizon ruin probability is
\[
\psi(u)=\frac{1}{1+\vartheta}
\exp\left[-\frac{\vartheta u}{(1+\vartheta)\mu}\right].
\]
This is the exponential-claim special case of the collective-risk model, not a general closed-form ruin probability for arbitrary claim-size distributions.

### DeFi applicability boundary

A protocol insurance fund or backstop reserve could be represented by \(U_t\) only if:
- the reserve receives a sufficiently constant income flow \(c\);
- covered payouts can reasonably be represented as a Poisson claim process;
- payout sizes are independent and identically distributed and independent of arrivals;
- the reserve is the correct solvency state and all inflows/outflows are measured in one numeraire.

Liquidation payouts are often correlated with token prices, market stress and event clustering; these conditions may fail precisely in the tail events of interest. A Hawkes process or common market factor may be required, which would no longer be the classical Cramér–Lundberg model.

**Disposition:** process structure and exponential-claim ruin expression verified against standard actuarial risk theory. Retain as a reserve-solvency lead, but hold pending a protocol-specific income/payout definition and validation of Poisson/i.i.d. assumptions. Do not count the reserve path, ruin time and exponential-claim closed form as separate equations.

## 3. Catalogue status and work not performed

No source-register or equation-catalogue record was changed. The formal manifest remains 128 source records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, market-data retrieval or stochastic simulations were run. This is original-source and mathematical-source review only.
