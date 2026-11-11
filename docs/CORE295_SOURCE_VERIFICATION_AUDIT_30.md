# Core-295 source verification audit 30: Hawkes self-exciting events and Merton jump-diffusion returns

**Date:** 2026-11-11  
**Status:** verification of discovery-batch leads only. No equation is added to the formal catalogue or counted toward 295.  
**Scope:** discovery batch 33 Hawkes and Merton processes; OU and CIR are source-status checked.

## 1. Hawkes 1971 self-exciting point process

### Primary transcription

A. G. Hawkes, *Spectra of some self-exciting and mutually exciting point processes*, Biometrika 58(1) (1971), 83–90, DOI 10.1093/biomet/58.1.83. The original PDF is accessible.

Hawkes defines a point process (N(t)) with conditional event probability over a small interval:
[
\Pr\{\Delta N(t)=1\mid N(s),s\leq t\}
=\Lambda(t)\Delta t+o(\Delta t),
]
and then defines the self-exciting intensity in Eq. (8):
[
\Lambda(t)=\nu+\int_{-\infty}^{t}g(t-u)\,dN(u).
]
The kernel satisfies (g(v)\geq0) and (g(v)=0) for (v<0). In the exponential-decay section, Eq. (12) uses:
[
g(v)=\alpha e^{-\beta v},\qquad v>0.
]
For stationarity, Hawkes derives (int_0^\infty g(v)dv<1), giving (alpha/\beta<1) for the exponential kernel.

### Model boundary

The process is self-exciting because past events raise future event intensity. It is a conditional-intensity point process, not simply a deterministic exponential decay or a Poisson process with a fixed rate. The kernel (g) is the excitation response to each past event. Hawkes also treats mutually exciting multivariate processes, but those are vector extensions of the same point-process family.

For DeFi-risk use, the event definition must be explicit (e.g., liquidation, oracle-triggered liquidation, forced deleveraging); the source does not itself establish that any particular DeFi event stream is Hawkes. Event timestamps, clustering, deduplication, baseline intensity, kernel, and stationarity must be specified.

**Disposition:** primary definition, exponential kernel and stationarity condition verified. Retain as a strong discovery lead, pending event-data/domain contract and a counting-process simulator.

## 2. Merton 1976 jump-diffusion stock-return process

### Primary transcription

Robert C. Merton, *Option Pricing When Underlying Stock Returns Are Discontinuous*, Journal of Financial Economics 3 (1976), 125–144, DOI 10.1016/0304-405X(76)90022-2. The original PDF is accessible.

Merton explicitly models ordinary continuous price changes by geometric Brownian motion and abnormal information arrivals by a Poisson-driven jump process. His Eq. (2) is:
[
\frac{dS}{S}=(\alpha-\lambda k)dt+\sigma dZ+dq,
]
where (alpha) is instantaneous expected return, (sigma^2) the continuous-component variance rate, (Z) a standard Wiener process, (q) the independent Poisson-driven jump process, (lambda) the mean event-arrival rate, and (k=E[Y-1]) the expected proportional jump size. Conditional on a jump, (S) is multiplied by a random factor (Y\geq0).

Eq. (3) gives the finite-horizon stock-price distribution as a diffusion factor multiplied by the product of jump factors, with the number of jumps Poisson distributed with parameter (lambda t).

### Measure and model boundary

The Eq. (2) drift (alpha) is the physical expected-return convention in the original stock-price dynamics. It must not be replaced by a risk-neutral drift (r) without specifying a pricing measure and the compensator convention. Merton's later option-pricing PDE is a derived pricing relation, not another return-process candidate.

The no-jump case (lambda=0) reduces to continuous geometric Brownian motion. Jump-size distributions (including lognormal jumps) are parameterizations of one jump-diffusion family, not separate equation candidates. For token-risk use, specify the return process, jump intensity, jump-size distribution, volatility and calibration horizon.

**Disposition:** original jump-diffusion dynamics and finite-horizon representation verified. Retain as a strong stochastic-risk lead, pending DeFi market scope, physical/risk-neutral measure, jump-size and calibration contract.

## 3. Ornstein–Uhlenbeck source-status note

Uhlenbeck and Ornstein (1930), *On the theory of the Brownian motion*, Physical Review 36, 823–841, DOI 10.1103/PhysRev.36.823, is confirmed as the primary source for the mean-reverting Brownian-motion model. The commonly used stochastic-calculus form
[
dX_t=\kappa(\theta-X_t)dt+\sigma dW_t
]
is a modern Wiener-process representation of their Langevin/mean-reverting random-force model, not a notation that should be claimed verbatim from the 1930 paper. The exact original random-force equation and white-noise limit still require page-level transcription if the source is to be marked primary-equation-verified.

**Disposition:** keep as a source lead; the modern SDE is well-established, but the primary-source equation transcription is incomplete.

## 4. Cox–Ingersoll–Ross source-status note

Cox, Ingersoll and Ross (1985), *A Theory of the Term Structure of Interest Rates*, Econometrica 53(2), 385–407, DOI 10.2307/1911242, is confirmed as the primary source for the square-root short-rate diffusion:
[
dr_t=\kappa(\theta-r_t)dt+\sigma\sqrt{r_t}\,dW_t.
]
The commonly cited Feller condition (2\kappa\theta\geq\sigma^2) ensures strict positivity; without it the process is nonnegative but may reach zero. This check did not obtain the original paper's equation-page transcription, so the modern equation remains supported by authoritative later treatments pending direct original-page verification.

**Disposition:** keep as a source lead; do not treat the Feller condition, affine bond-pricing formula or transition density as separate stochastic-process equations.

## 5. Cross-model conclusion and catalogue status

Hawkes is a self-exciting point process; Merton is a continuous diffusion plus compound-Poisson jump process. They are distinct stochastic model structures. OU and CIR are related mean-reverting diffusion models with different state-dependent diffusion coefficients; do not count them as separate independent statistical units merely because their SDEs differ.

All four remain discovery-only. No source-register or equation-catalogue record was changed. The formal manifest remains 128 source records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, market-data retrieval or stochastic simulations were run. This is original-source review only.
