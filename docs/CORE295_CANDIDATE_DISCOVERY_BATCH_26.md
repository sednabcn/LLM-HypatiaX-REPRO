# Core-295 candidate discovery batch 26: discrete ecological interactions, age-structured populations and evolutionary dynamics

**Date:** 2026-11-11  
**Status:** discovery-only source leads. No relation is added to the formal catalogue or counted toward the 295 target.  
**Domain focus:** Biology. This batch prioritizes complete discrete-time or vector-valued population systems rather than further scalar growth-curve variants.

## 1. Nicholson–Bailey host–parasitoid discrete-generation system

**Primary source:** A. J. Nicholson and V. A. Bailey (1935), *The Balance of Animal Populations—Part I*, Proceedings of the Zoological Society of London 105(3), 551–598, DOI 10.1111/j.1096-3642.1935.tb01680.x.  
**Equation locator used for discovery:** ETH Zürich theoretical biology lecture script, §1.3.2, which reproduces the classical equations and explains the random-encounter/Poisson-survival interpretation.

[
H_{t+1}=R H_t e^{-aP_t},
qquad
P_{t+1}=cH_t(1-e^{-aP_t}).
]
(H_t) and (P_t) are host and parasitoid densities at generation (t); (R) is host reproduction in the absence of parasitism; (a) is parasitoid searching/encounter efficiency; (c) is parasitoid production per parasitized host. The term (e^{-aP_t}) is the probability a host escapes parasitism under the random-search approximation.

**Structural value:** a coupled nonlinear discrete-time interaction system, not a continuous Lotka–Volterra ODE. It is a complete two-state model; its host and parasitoid equations must not be counted separately.

**Risks:** the classical model has an unstable positive equilibrium for (R>1) and unbounded oscillatory growth away from that equilibrium. This is a scientifically meaningful limitation, not a reason to silently add density dependence. The source equation needs direct original-page transcription before source verification. A deterministic adapter must preserve generation timing and nonnegative population states.

**Initial disposition:** high-value complete-system lead; hold for primary equation-page transcription and full-system adapter.

## 2. Leslie age-structured population projection matrix

**Primary source:** P. H. Leslie (1945), *On the use of matrices in certain population mathematics*, Biometrika 33(3), 183–212, DOI 10.1093/biomet/33.3.183. Original PDF is accessible.

Leslie derives the age-structured recurrence:
[
mathbf n_{t+1}=Mmathbf n_t,
]
where (mathbf n_t) is the vector of female population counts by age class. The first row of (M) contains age-specific daughter fertility values (F_x); the subdiagonal contains survival probabilities (P_x); other entries are zero in the standard age-class model. The original paper gives (0<P_x<1), (F_xgeq0), and explains that (M^tmathbf n_0) gives the projected age distribution.

**Structural value:** a complete age-structured linear population system with explicit fertility/survival architecture. It is not a scalar growth law and should not be flattened into a total-population recurrence without a predeclared derivation and proof of state sufficiency.

**Risks:** age interval and time step must match; fertility must count daughters surviving into the first age class; survival rates must map age class (x) to (x+1). The exact matrix dimension and terminal age class are species-specific. The total-population projection is an output of the vector state system, not another independent equation.

**Initial disposition:** strong primary-source system lead; hold pending an age-structured deterministic adapter and a policy decision on matrix systems under the scalar Core-15 runner.

## 3. Replicator dynamics for evolutionary strategy frequencies

**Primary source:** P. D. Taylor and L. B. Jonker (1978), *Evolutionarily stable strategies and game dynamics*, Mathematical Biosciences 40(1–2), 145–156, DOI 10.1016/0025-5564(78)90077-9. The paper abstract confirms continuous nonlinear differential-equation and discrete difference-equation dynamics for strategy frequencies in matrix games. A modern evolutionary-game-dynamics text reproduces the canonical continuous replicator system:
[
dot x_i=x_ileft((Ax)_i-x^TAxight),
qquad i=1,ldots,n,
]
where (x_i) is the population share using strategy (i), (A) is the payoff matrix, and (x^TAx) is mean population payoff.

**Structural value:** a nonlinear frequency-dependent evolutionary system on the probability simplex, with payoff-dependent selection and a simplex-preserving flow. It differs from Lotka–Volterra population-abundance dynamics in state interpretation and conservation constraint.

**Risks:** the primary paper's exact notation and assumptions still need page-level transcription. Payoff matrix symmetry, strategy count, simplex constraints and time scaling must be frozen. The equation is a vector system; component equations are not independent entries.

**Initial disposition:** promising full-system lead; hold pending primary equation verification and a complete simplex-constrained system adapter.

## 4. Beverton–Holt stock–recruitment relation: saturation-family caution

**Primary source:** R. J. H. Beverton and S. J. Holt (1957), *On the Dynamics of Exploited Fish Populations*, Fisheries Investigations Series II, Vol. XIX. The classic stock–recruitment form is commonly written:
[
\mathbb E[R\mid S]=\frac{aS}{1+bS},
]
where (S) is spawning stock and (R) expected recruitment.

This is a rational saturating relation. It is physically motivated by density-dependent juvenile mortality and asymptotic recruitment, but its normalized algebraic form is the same one-site hyperbolic saturation shape as Langmuir/Michaelis–Menten:
[
\frac{aS}{1+bS}=\frac{a}{b}\frac{S}{1/b+S}.
]
The original 1957 book's exact equation-page transcription remains outstanding; current equation support is secondary/technical.

**Initial disposition:** source lead only, not an independent structural candidate under a strict function-form policy. Retain as a cross-domain structural-equivalence example; do not add to the candidate count merely because it is a distinct ecological mechanism.

## 5. Batch-level decisions

| Lead | Model type | Principal issue | Initial decision |
|---|---|---|---|
| Nicholson–Bailey | Coupled discrete-time host–parasitoid system | Original equation-page transcription; unstable classical dynamics; full-system adapter | Hold; high priority |
| Leslie | Age-structured matrix recurrence | Vector state, species-specific age/fertility/survival contract | Hold; high priority |
| Replicator | Nonlinear simplex-constrained evolutionary ODE | Primary equation transcription; payoff-matrix and simplex contract | Hold; high priority |
| Beverton–Holt | Scalar rational stock–recruitment saturation | Same functional saturation structure as Langmuir/MM; original page transcription | Do not count separately under strict structural policy |

The batch provides four source leads, not four independent equations. Nicholson–Bailey, Leslie and replicator dynamics are complete systems requiring a reviewed interface beyond a scalar function. Beverton–Holt is retained as a structural-equivalence warning.

## 6. Catalogue status and work not performed

No source-register or equation-catalogue record was changed. The formal manifest remains 128 source records, 19 proposed equation records, zero accepted equations, and an unfrozen sampling frame.

No experiments, validators, solvers, workflows, paid compute, API calls or biological measurements were run. This is source discovery only.
