# Core-295 candidate discovery batch 36: membrane diffusion potential and revised capillary filtration

**Date:** 2026-11-11  
**Status:** discovery-only source leads. None is added to the formal catalogue or counted toward 295.  
**Domain focus:** Biology / physiology.

## 1. Goldman–Hodgkin–Katz zero-current membrane potential

**Primary source lineage:**
- D. E. Goldman (1943), *Potential, impedance, and rectification in membranes*, Journal of General Physiology 27(1), 37–60, DOI 10.1085/jgp.27.1.37.
- A. L. Hodgkin and B. Katz (1949), *The effect of sodium ions on the electrical activity of the giant axon of the squid*, Journal of Physiology 108(1), 37–77, DOI 10.1113/jphysiol.1949.sp004310.

For a membrane permeable to monovalent cations K+, Na+ and monovalent anion Cl−, the constant-field zero-current potential is commonly written:
[
V_m=\frac{RT}{F}\ln
\frac{
P_K[K^+]_o+P_{Na}[Na^+]_o+P_{Cl}[Cl^-]_i
}{
P_K[K^+]_i+P_{Na}[Na^+]_i+P_{Cl}[Cl^-]_o
}.
]
The chloride concentrations are reversed relative to the cation terms because chloride is negatively charged. (P_i) are relative permeabilities; subscripts (o,i) denote outside and inside.

**Boundary and risks:** constant electric field across the membrane, steady state and zero net current, specified permeant ion species and valence, and concentrations at the membrane boundaries. The formula is not a universal equilibrium potential for arbitrary mixtures; non-constant field, active transport, multiple valences, channel gating and concentration gradients inside the membrane require extensions. The GHK current equation and GHK voltage equation are related forms of the same constant-field membrane-transport model.

**Structural value:** multi-ion permeability-weighted membrane potential; distinct from the single-ion Nernst equation, which is recovered in an appropriate one-ion limit. The original Goldman equation and Hodgkin–Katz permeability-weighted expression are in one GHK family, not separate entries.

**Initial disposition:** strong Biology candidate lead; hold pending exact equation-page transcription from the original papers, ion/permeability convention, temperature, concentration units and membrane-state adapter.

## 2. Revised Starling capillary filtration relation

**Historical source:** E. H. Starling (1896), *On the absorption of fluids from the connective tissue spaces*, Journal of Physiology 19, 312–326.  
**Modern sources:** Levick and Michel (2010), *Microvascular fluid exchange and the revised Starling principle*, Cardiovascular Research 87, 198–210; authoritative NCBI Bookshelf treatment of the revised Starling principle and glycocalyx.

The revised filtration expression is:
[
J_v=K_f\left[(P_c-P_i)-\sigma(\pi_c-\pi_g)\right],
]
where (J_v) is transvascular fluid filtration rate, (K_f) the filtration coefficient (surface area × hydraulic conductivity), (P_c,P_i) capillary and interstitial hydrostatic pressures, (pi_c) plasma oncotic pressure, (pi_g) subglycocalyx oncotic pressure, and (sigma) the protein reflection coefficient.

The classical Starling expression used interstitial oncotic pressure (pi_i) in place of the subglycocalyx value (pi_g). The revised principle emphasizes the endothelial glycocalyx as the effective semipermeable layer and does not predict sustained venous-end reabsorption under normal steady-state conditions; lymphatics return filtered fluid.

**Boundary and risks:** the revised model requires an intact glycocalyx and a defined subglycocalyx compartment; it is not a universal one-compartment pressure balance. (K_f), (sigma), and the oncotic-pressure terms vary by vascular bed and physiological state. The benchmark must not mix classical (pi_i) and revised (pi_g) conventions in one equation record.

**Structural value:** a pressure-driven transvascular filtration relation with a reflection coefficient and an effective oncotic gradient. It is distinct from Poiseuille tube flow and Fick cardiac-output measurement, though it is related to capillary transport and endothelial permeability.

**Initial disposition:** high-value physiology lead; hold pending a precise vascular-bed/steady-state contract, source-page verification and parameter ranges. The classical and revised Starling equations are one model lineage with different barrier assumptions, not independent candidate equations.

## 3. Batch-level structural decisions

| Lead | Model type | Main issue | Initial decision |
|---|---|---|---|
| GHK membrane potential | Constant-field, zero-current multi-ion voltage relation | Original Goldman/Hodgkin–Katz notation, ion valence and membrane-state contract | Hold; high priority |
| Revised Starling | Glycocalyx-aware transvascular filtration relation | Classical vs revised oncotic boundary, vascular-bed dependence | Hold; high priority |

These are two source leads, not two accepted equations. Do not count GHK voltage/current forms or individual ion terms separately. Do not count classical and revised Starling equations as independent structures.

## 4. Catalogue status and work not performed

No source-register or equation-catalogue record was changed. The formal manifest remains 128 source records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, validators, solvers, workflows, paid compute, API calls, membrane-potential measurements or capillary-filtration experiments were run. This is source discovery only.
