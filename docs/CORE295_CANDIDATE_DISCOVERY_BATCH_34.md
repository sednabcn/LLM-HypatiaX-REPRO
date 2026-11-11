# Core-295 candidate discovery batch 34: spatial population waves and activator–inhibitor morphogenesis

**Date:** 2026-11-11  
**Status:** discovery-only source leads. No equation is added to the formal catalogue or counted toward 295.  
**Domain focus:** Biology.

## 1. Fisher 1937 wave-of-advance reaction–diffusion equation

**Primary source:** R. A. Fisher (1937), *The wave of advance of advantageous genes*, Annals of Eugenics 7(4), 355–369, DOI 10.1111/j.1469-1809.1937.tb02153.x. The original paper is available as a scan.

Fisher defines (p(x,t)) as the frequency of an advantageous allele and (q=1-p) as the alternative allele frequency. In the simplest one-dimensional homogeneous habitat, he writes the diffusion-selection equation:
[
\frac{\partial p}{\partial t}
=k\frac{\partial^2p}{\partial x^2}+mpq
=k\frac{\partial^2p}{\partial x^2}+mp(1-p),
]
where (k) is a diffusion coefficient and (m) the selection intensity.

The source explicitly assumes small dispersal distances per generation relative to the wave length and constant selection advantage. It notes that real systems may have spatially varying diffusion, population density and selective advantage, and asymmetric dispersal.

**Structural value:** a spatial reaction–diffusion PDE with local logistic selection and spatial diffusion. It produces a travelling wave of gene-frequency advance; the original paper derives a wave speed in its model.

**Overlap warning:** the reaction term (mp(1-p)) is the logistic-growth term, which is excluded in Core-15. The PDE adds a spatial diffusion operator and is not algebraically identical to the scalar logistic ODE, but it is a spatial extension of the same local growth family. It must not be counted as a separate equation unless the benchmark policy explicitly permits a complete spatial system to count separately from its local reaction law.

**Initial disposition:** primary source and equation verified; hold pending spatial-PDE adapter, spatial domain/boundary conditions and a family-level ruling against the Core-15 logistic exclusion.

## 2. Gierer–Meinhardt activator–inhibitor reaction–diffusion system

**Primary source:** A. Gierer and H. Meinhardt (1972), *A theory of biological pattern formation*, Kybernetik 12, 30–39, DOI 10.1007/BF00289234. The original paper and a later 1974 application paper are available as scans.

The 1972 paper develops short-range autocatalytic activation coupled to longer-range inhibition. The original model distinguishes activator and inhibitor concentrations and their sources; the 1974 paper writes explicit coupled reaction–diffusion equations for activator (a(x,t)) and inhibitor (h(x,t)). A commonly used Gierer–Meinhardt activator–inhibitor form is:
[
\frac{\partial a}{\partial t}
=\rho_a\frac{a^2}{h}-\mu_a a+D_a\nabla^2a+\rho_a^0,
]
[
\frac{\partial h}{\partial t}
=\rho_h a^2-\mu_h h+D_h\nabla^2h.
]

The exact original-paper parameterization and equation-page transcription remain to be checked before formal source registration. Do not present the common modern form above as a verbatim transcription of the 1972 source.

**Structural value:** a coupled nonlinear two-field reaction–diffusion system with autocatalytic activator production, inhibitor production, differential degradation and different diffusion scales. It is a more specific kinetic model than Turing's generic linear-stability framework.

**Overlap warning:** this belongs to the broad Turing reaction–diffusion/morphogenesis family, but its nonlinear activator–inhibitor kinetics differ from Turing's generic two-species reaction terms. It is one coupled PDE system, not separate equations for activator, inhibitor, diffusion and degradation. Whether it is a separate structural unit from the already registered Turing system depends on whether the catalogue counts distinct reaction kinetics within a shared PDE family.

**Initial disposition:** high-value source lead; hold for original equation transcription, parameter mapping, domain/boundary conditions and family-level comparison with Turing 1952.

## 3. Chemostat/Monod system: exclusion and overlap warning

The classical chemostat couples biomass and limiting substrate balances:
[
\frac{dX}{dt}=(\mu(S)-D)X,
qquad
\frac{dS}{dt}=D(S_{in}-S)-\frac{1}{Y}\mu(S)X,
]
with Monod growth (mu(S)=mu_{max}S/(K_S+S)).

This is a complete bioreactor system, but the Monod saturation term is structurally the same rational saturation form as the Michaelis–Menten/Langmuir-one family. It also requires coupled biomass/substrate state constraints and a dilution-rate contract. It is retained here as a family-boundary example, not an automatic new candidate.

**Initial disposition:** do not count the Monod term separately from the excluded MM saturation family; consider the complete chemostat system only if the benchmark explicitly permits system-level models and distinguishes it from the excluded scalar saturation law.

## 4. Batch-level structural decisions

| Lead | Model type | Main issue | Initial decision |
|---|---|---|---|
| Fisher–KPP | Scalar spatial reaction–diffusion PDE with logistic reaction | Spatial extension of Core-15-excluded logistic growth | Hold; family ruling |
| Gierer–Meinhardt | Coupled nonlinear activator–inhibitor PDE system | Distinct kinetics within Turing/morphogenesis family; exact primary transcription pending | Hold; high priority |
| Chemostat–Monod | Coupled biomass/substrate ODE system | MM/Monod saturation overlap; full-system interface | Do not count scalar Monod separately; hold system |

The batch supplies three leads, not three independent equations. Fisher's reaction term, diffusion term and travelling-wave speed are not separate candidates; Gierer–Meinhardt's two field equations are one system; chemostat state equations and the Monod term must be treated as one coupled model.

## 5. Catalogue status and work not performed

No source-register or equation-catalogue record was changed. The formal manifest remains 128 source records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, validators, solvers, workflows, paid compute, API calls, gene-frequency observations or cell-culture measurements were run. This is source discovery only.
