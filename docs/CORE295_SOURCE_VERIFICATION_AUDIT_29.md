# Core-295 source verification audit 29: Fisher 1937 reaction–diffusion wave and Gierer–Meinhardt 1972 activator–inhibitor system

**Date:** 2026-11-11  
**Status:** verification of discovery-batch leads only. No equation is added to the formal catalogue or counted toward 295.

## 1. Fisher 1937 wave-of-advance equation

### Primary transcription

R. A. Fisher, *The wave of advance of advantageous genes*, Annals of Eugenics 7(4) (1937), 355–369, DOI 10.1111/j.1469-1809.1937.tb02153.x. The original PDF is accessible.

On printed p. 355, Fisher defines (p(x,t)) as the frequency of the advantageous mutant gene and (q) as the frequency of its parent allele, assuming these are the only two alleles. He gives the local dispersal flux as (-k\,\partial p/\partial x) and derives Eq. (1):
[
\frac{\partial p}{\partial t}
=k\frac{\partial^2p}{\partial x^2}+mpq.
]
Since (p+q=1), the reaction term is (mp(1-p)). Here (k) is the diffusion coefficient and (m) the selection intensity, with time measured in generations.

Fisher explicitly limits the model to a uniform linear habitat, constant diffusion coefficient and constant selection advantage. He notes that real systems may have spatially varying (k), population density and selective advantage, asymmetric dispersal and multiple dispersal stages. The diffusion approximation is appropriate only when dispersal distances per generation are small relative to the wave length.

### Derived wave-speed result

Fisher's travelling-wave substitution gives Eq. (2) and establishes a minimum wave speed (2\sqrt{km}) in the continuous diffusion model; he later argues that stochastic discreteness at the wave front selects this minimum speed. This speed is a derived property of Eq. (1), not a second equation candidate.

### Decision

**Disposition:** original equation and assumptions verified. Keep as one complete spatial reaction–diffusion system, but hold from acceptance pending the structural rule for a spatial PDE whose local reaction term is the Core-15-excluded logistic law. Do not count the local logistic reaction, diffusion flux, travelling-wave ODE or minimum wave speed separately.

## 2. Gierer–Meinhardt 1972 activator–inhibitor model

### Primary source and exact model variant

A. Gierer and H. Meinhardt, *A theory of biological pattern formation*, Kybernetik 12 (1972), 30–39, DOI 10.1007/BF00289234. The original paper PDF is accessible.

The 1972 paper does not prescribe one universal two-field model. It develops a family of mechanisms with source densities, activator/inhibitor concentrations, diffusion and degradation, then gives several explicit variants. One explicit “Activator–Inhibitor Model with Different Sources” is Eq. (15a,b):
[
\frac{\partial a}{\partial t}
=Q_0Q(x)+cQ(x)\frac{a^2}{h}-\mu a
+D_a\frac{\partial^2a}{\partial x^2},
]
[
\frac{\partial h}{\partial t}
=c'Q'(x)a^2-vh
+D_h\frac{\partial^2h}{\partial x^2}.
]
Here (a(x,t)) is activator concentration, (h(x,t)) inhibitor concentration, (Q(x)) and (Q'(x)) are distinct source-density distributions, (D_a,D_h) are diffusion coefficients, and the other coefficients describe source production, autocatalytic activation, inhibition and first-order removal. The paper states that the activator activates both sources, while the inhibitor inhibits only activator sources in this model variant.

The source also provides other model variants (depletion model, common-source activator–inhibitor model, and saturation-limited forms). These are not interchangeable without changing the assumed molecular mechanism. The frequently quoted modern Gierer–Meinhardt form with constant production coefficients and no explicit source-density fields is a simplification, not a verbatim transcription of Eq. (15).

### Family boundary and assumptions

This is one coupled nonlinear reaction–diffusion system. Do not count:
- the activator and inhibitor PDEs as two separate equations;
- diffusion, production, autocatalysis, inhibition and degradation terms separately;
- Eq. (15) alongside its reduced/common-source or saturation-limited variants as independent samples without a declared mechanism-level policy;
- pattern wavelength, polarity, steady-state or stability conditions as additional equations.

The original paper's calculations use impermeable boundaries in its examples and emphasizes that source gradients, initial conditions and boundary conditions affect the resulting patterns. A benchmark adapter must freeze the selected mechanism variant, source distributions, spatial domain, boundary conditions, initial concentrations, diffusion coefficients and physically meaningful parameter ranges.

### Decision

**Disposition:** exact primary equations and model variant verified. Retain as a high-value complete-system Biology lead, discovery-only, pending a decision on whether distinct nonlinear kinetics within the Turing/morphogenesis PDE family are separate equation units and a full PDE adapter. Do not use the generic simplified formula as if it were the original Eq. (15).

## 3. Cross-model conclusion

Fisher–KPP and Gierer–Meinhardt are both spatial reaction–diffusion models, but their reaction kinetics and state structure differ:
- Fisher: one scalar allele-frequency field with logistic selection reaction and diffusion;
- Gierer–Meinhardt: coupled activator/inhibitor fields with nonlinear autocatalysis, cross-inhibition, source-density fields and different diffusion rates.

Fisher is linked to the Core-15 logistic-growth exclusion; Gierer–Meinhardt is linked to the Turing pattern-formation family but has a more specific nonlinear mechanism. Both require complete PDE interfaces and must not be flattened into unrelated scalar equation rows.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls or biological measurements were performed. This is original-source review only.
