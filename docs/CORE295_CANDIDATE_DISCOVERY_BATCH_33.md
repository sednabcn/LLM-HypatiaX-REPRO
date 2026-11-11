# Core-295 candidate discovery batch 33: mean-reverting diffusions and self-exciting/jump risk processes

**Date:** 2026-11-11  
**Status:** discovery-only source leads. No equation is added to the formal catalogue or counted toward 295.  
**Domain focus:** DeFi Risk / financial risk. These general stochastic processes may model token depeg deviations, rates, returns and clustered liquidation events only if the DeFi Risk scope explicitly includes stochastic market/event risk.

## 1. Ornstein–Uhlenbeck mean-reverting diffusion

**Primary source:** G. E. Uhlenbeck and L. S. Ornstein (1930), *On the theory of the Brownian motion*, Physical Review 36, 823–841, DOI 10.1103/PhysRev.36.823.

The canonical process is:
[
dX_t=\kappa(\theta-X_t)dt+\sigma dW_t,
]
where (kappa>0) is the mean-reversion speed, (	heta) the long-run mean, (sigma>0) the diffusion scale and (W_t) standard Brownian motion.

The process is Gaussian and mean-reverting, with conditional mean:
[
E[X_t\mid X_s]=\theta+(X_s-\theta)e^{-\kappa(t-s)}.
]
Its exact discrete-time transition is Gaussian:
[
X_{t+\Delta}=\theta+(X_t-\theta)e^{-\kappa\Delta}
+\sigma\sqrt{\frac{1-e^{-2\kappa\Delta}}{2\kappa}}\,Z,
quad Z\sim\mathcal N(0,1).
]

**DeFi-risk use:** model a log price deviation or log basis from a stable peg/reference value, not an unconstrained raw token price. The state (X_t=ln(P_t/P^*)) may be negative or positive while the price remains positive after exponentiation.

**Boundary:** constant mean, linear drift, constant diffusion, Brownian shocks, time-homogeneous parameters. A regime-switching peg or jump process requires extensions. Do not count the exact transition distribution and SDE as independent equations.

**Initial disposition:** strong stochastic-process lead; hold pending a declared depeg/basis state, sampling interval, parameter estimation convention and stochastic-system adapter.

## 2. Cox–Ingersoll–Ross square-root diffusion

**Primary source:** J. C. Cox, J. E. Ingersoll Jr. and S. A. Ross (1985), *A Theory of the Term Structure of Interest Rates*, Econometrica 53(2), 385–407, DOI 10.2307/1911242.

The short-rate process is:
[
dr_t=\kappa(\theta-r_t)dt+\sigma\sqrt{r_t}\,dW_t,
]
with (kappa,	heta,sigma>0). The drift mean-reverts toward (	heta), while volatility falls as (r_t) approaches zero. The Feller condition (2\kappa\theta\geq\sigma^2) ensures strict positivity; without it, the process remains nonnegative but may reach zero.

**DeFi-risk use:** potentially useful for nonnegative market reference rates, yield curves or external funding rates. It is not a model of the protocol's utilization-based borrow-rate function, which is a deterministic state-dependent curve; do not substitute CIR for the Compound/Aave protocol rate rule.

**Boundary:** define the physical vs risk-neutral measure, short-rate unit, parameter calibration, Feller condition and time scale. The bond-pricing PDE and affine bond-price solution are derived outputs of the process, not separate process equations.

**Initial disposition:** strong financial-risk process lead, held pending confirmation that external rate risk belongs in DeFi Risk and a full stochastic adapter.

## 3. Hawkes self-exciting point process for clustered events

**Primary source:** A. G. Hawkes (1971), *Spectra of some self-exciting and mutually exciting point processes*, Biometrika 58(1), 83–90, DOI 10.1093/biomet/58.1.83.

Hawkes defines a conditional event intensity:
[
\lambda(t)=\nu+\int_{-\infty}^{t}g(t-u)\,dN(u),
]
where (N(t)) counts events, (
u>0) is baseline intensity and (g(v)\geq0) is the excitation kernel, zero for (v<0). The original paper gives the exponential-kernel case:
[
g(v)=\alpha e^{-\beta v},\qquad v>0.
]
For a stationary univariate process, the original paper requires:
[
\int_0^\infty g(v)dv<1,
]
which becomes (alpha/\beta<1) for the exponential kernel.

**DeFi-risk use:** candidate model for clustered liquidation events, oracle-triggered liquidations, or correlated protocol stress events. This is a statistical event-intensity model, not a deterministic liquidation-price equation.

**Boundary:** choose event definition (liquidation, forced deleveraging, oracle update), time resolution, event deduplication, kernel form and stationarity/branching-ratio condition. Hawkes's original paper explicitly notes that second-order properties may not distinguish self-exciting and certain doubly stochastic processes; identification is a statistical design issue.

**Initial disposition:** high-value event-risk lead; hold pending event definition, data source and a counting-process simulator/adapter.

## 4. Merton jump-diffusion return process

**Primary source:** Robert C. Merton (1976), *Option Pricing When Underlying Stock Returns Are Discontinuous*, Journal of Financial Economics 3, 125–144, DOI 10.1016/0304-405X(76)90022-2.

The original paper's Eq. (2) specifies:
[
\frac{dS}{S}=(\alpha-\lambda k)dt+\sigma dZ+dq,
]
where (Z) is a Wiener process, (q) is a Poisson-driven jump process with intensity (lambda), and (k=E[Y-1]) is the expected proportional jump size. At a jump, (S) is multiplied by a random factor (Y\geq0). The Brownian and Poisson components are independent. Eq. (3) gives the finite-horizon stock-price distribution as a lognormal diffusion component multiplied by the product of jump factors, with the number of jumps Poisson distributed.

**DeFi-risk use:** potential model for token-price discontinuities, depeg shocks or liquidation-gap risk. The model explicitly allows large jumps at arbitrarily short time intervals, unlike continuous-path GBM.

**Boundary:** distinguish physical expected-return measure from risk-neutral pricing measure; define jump intensity, jump-size distribution, compensator (k), diffusion volatility and whether jump factors are lognormal. (lambda=0) reduces to the continuous diffusion model and is not a separate candidate.

**Initial disposition:** strong source lead; hold pending token-market scope, jump-size distribution, parameter calibration and stochastic adapter.

## 5. Batch-level family map

| Lead | Process class | Relationship | Initial decision |
|---|---|---|---|
| Ornstein–Uhlenbeck | Gaussian mean-reverting diffusion with constant volatility | Log-depeg/basis model; distinct from CIR's state-dependent volatility | Hold; consider |
| CIR | Nonnegative square-root mean-reverting diffusion | Interest-rate risk; distinct from OU but same broad mean-reverting diffusion family | Hold; consider |
| Hawkes | Self-exciting point process | Clustered event risk; exponential kernel is one special kernel | Hold; high priority |
| Merton jump diffusion | Brownian diffusion plus Poisson jumps | Continuous GBM is λ=0 special case; jump-size variants share one family | Hold; consider |

These are four source leads, not four independent equations. Their relevance depends on the DeFi Risk domain boundary. Do not count exact transition distributions, bond-pricing PDEs, jump-free limits, kernel parameterizations or different event labels as new equation structures.

## 6. Catalogue status and work not performed

No source-register or equation-catalogue record was changed. The formal manifest remains 128 source records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, validators, solvers, workflows, paid compute, API calls, market-data retrieval or stochastic simulations were run. This is source discovery only.
