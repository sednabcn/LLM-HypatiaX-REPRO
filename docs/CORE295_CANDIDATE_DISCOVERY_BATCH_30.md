# Core-295 candidate discovery batch 30: electrochemical kinetics and ionic transport

**Date:** 2026-11-11  
**Status:** discovery-only source leads. No equation is added to the formal catalogue or counted toward 295.  
**Domain focus:** Chemistry. These leads complement batch 25's equilibrium Nernst relation; they describe non-equilibrium electrode kinetics and ionic mass transport.

## 1. Butler–Volmer electrode current–overpotential relation

**Historical source lineage:** Butler's 1924 papers developed a kinetic interpretation of the Nernst equilibrium potential and transition-state ideas, but did not derive the general modern electrode-rate equation. Erdey–Grüz and Volmer (1930) treated reversible anodic and cathodic contributions for a hydrogen-electrode rate-determining step; later Butler work and engineering conventions contributed to the current forms. See Dickinson and Wain (2020), *The Butler–Volmer equation in electrochemical theory: Origins, value, and practical application*, for the historical and notational review.

Under the 2020 review's engineer's convention, a common current-density form is:
\[
i=i_0\left[
\exp\left(\frac{\alpha_a F\eta}{RT}\right)
-
\exp\left(-\frac{\alpha_c F\eta}{RT}\right)
\right],
\]
where \(i_0\) is exchange current density, \(\eta=E-E_{eq}\) is overpotential, \(\alpha_a,\alpha_c\) are anodic/cathodic transfer coefficients, \(F\) is Faraday's constant, \(R\) the gas constant and \(T\) absolute temperature. In this convention the transfer coefficients are **not multiplied by the total electron number \(n\)**. Older textbook forms sometimes place \(nF\) in the exponent; those use a different coefficient convention and must not be mixed. For a simple one-electron step \(n=1\); \(\alpha_a+\alpha_c=1\) is a common special convention, not a universal constraint.

**Boundary and risks:** the surface concentrations and reference condition must be defined; mass-transfer limitation can make bulk concentrations differ from surface concentrations. The zero-overpotential point has equal and opposite partial currents and zero net current. At large positive/negative overpotential, one exponential dominates and the equation reduces to a Tafel asymptote. Tafel law is a limiting approximation, not another independent candidate. The Nernst equation gives equilibrium potential; Butler–Volmer describes the non-equilibrium current response about that equilibrium.

**Initial disposition:** high-value electrochemical kinetics lead. Hold pending original equation-page transcription, transfer-coefficient convention, surface concentration model and a defined kinetic regime. Keep anodic/cathodic partial currents and Tafel limits in one family.

## 2. Nernst–Planck ionic flux relation

**Sources:** authoritative electrochemical transport treatments, including the Newman–Thomas-Alyea electrochemical systems text and the Nernst–Planck formulation used in electrochemical modeling; see also the 2026 tutorial review *Mass transport in electrochemical systems*.

For ionic species (i), the full dilute-solution flux including convection is:
[
\mathbf J_i
=-D_i\nabla c_i
-\frac{z_i F D_i}{RT}c_i\nabla\phi
+c_i\mathbf v,
]
where (D_i) is diffusivity, (c_i) concentration, (z_i) charge number, (phi) electric potential and (mathbf v) solvent velocity. The first term is Fickian diffusion, the second electromigration, and the third convection.

The species balance is
[
\frac{\partial c_i}{\partial t}
=-\nabla\cdot\mathbf J_i+R_i,
]
where (R_i) is a source/sink from chemical reactions. Coupling the flux/balance equations to Poisson's equation or an electroneutrality constraint gives a Poisson–Nernst–Planck or electroneutral transport system.

**Boundary and risks:** the ideal Nernst–Planck form assumes dilute-solution electrochemical potentials and neglects short-range ion-ion interactions; concentrated electrolytes require activity-gradient corrections and more advanced transport models. If convection is omitted, that omission must be explicit. Potential and concentrations are coupled across species, so the system cannot generally be solved as independent scalar flux functions. The Nernst–Planck flux includes Fick's law as one component; do not count the diffusion, migration and convection terms as three equations.

**Initial disposition:** strong ionic-transport system lead, distinct from pure Fick diffusion because the electric-potential migration term couples charged species. Hold pending source/version selection, activity convention, electroneutrality vs Poisson closure, boundary conditions and a full vector/PDE adapter.

## 3. Structural-family boundary

| Lead | Type | Relationship | Initial decision |
|---|---|---|---|
| Butler–Volmer | Nonlinear current–overpotential kinetic relation with opposing exponentials | Nernst equilibrium is the zero-net-current reference; Tafel laws are high-overpotential limits; Marcus is a different electron-transfer theory | Hold; consider |
| Nernst–Planck | Ionic flux constitutive law with diffusion, migration and convection | Contains Fick flux as one term; full PNP/electroneutral models are coupled systems | Hold; consider |

These are not separate entries for each term or limiting case. Butler–Volmer and Nernst–Planck describe distinct mechanisms (interfacial charge transfer and bulk ionic transport) but may be coupled in a complete electrochemical cell model.

## 4. Catalogue status and work not performed

No source-register or equation-catalogue record was changed. The formal manifest remains 128 source records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, validators, solvers, workflows, paid compute, API calls, electrode measurements or transport experiments were run. This is source discovery only.
