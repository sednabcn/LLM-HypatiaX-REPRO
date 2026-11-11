# Core-295 source verification audit 31: GHK diffusion potential and the full revised Starling steady-state model

**Date:** 2026-11-11  
**Status:** verification/correction of discovery-batch 36 leads only. No equation is added to the formal catalogue or counted toward 295.

## 1. Goldman–Hodgkin–Katz membrane diffusion potential

### Source lineage and exact model interpretation

David E. Goldman (1943), *Potential, impedance, and rectification in membranes*, Journal of General Physiology 27(1), 37–60, DOI 10.1085/jgp.27.1.37, derives membrane ion-motion equations from diffusion and electrical forces and solves two simplified cases, including a constant-electric-field membrane model. The 1943 paper's abstract explicitly identifies the constant-field assumption and applies the model to membrane potentials.

Hodgkin and Katz (1949), *The effect of sodium ions on the electrical activity of the giant axon of the squid*, Journal of Physiology 108(1), 37–77, DOI 10.1113/jphysiol.1949.sp004310, applies the permeability-weighted constant-field model to the squid giant axon and the principal K+, Na+ and Cl− ions. The commonly used three-ion voltage expression is:
[
V_m=\frac{RT}{F}\ln
\frac{
P_K[K^+]_o+P_{Na}[Na^+]_o+P_{Cl}[Cl^-]_i
}{
P_K[K^+]_i+P_{Na}[Na^+]_i+P_{Cl}[Cl^-]_o
}.
]
The chloride concentrations are reversed because chloride is an anion. A modern review of the constant-field equation traces the original Goldman derivation and the Hodgkin–Katz multi-ion use.

### Critical terminology correction

This is a **steady-state zero-current diffusion potential under the constant-field assumption**, not a thermodynamic equilibrium potential in the Nernst sense. The Nernst equation describes the equilibrium potential for one permeant ion; GHK combines multiple permeant ions and their relative permeabilities. In the one-permeant-ion limit, GHK reduces to the Nernst form.

The GHK current equation and GHK voltage equation are related expressions from the same constant-field model. The voltage expression sets net current to zero; it is not an independent model from the current equation. The three-ion formula is not a verbatim statement of the 1943 Goldman two-ion example; the Hodgkin–Katz extension and later notation must be cited accurately.

**Disposition:** model and formula lineage verified; exact page-level transcription of the three-ion formula from Hodgkin–Katz (1949) remains to be completed. Keep as one GHK constant-field family, discovery-only, pending primary page transcription, permeability/valence contract and membrane-state adapter.

## 2. Revised Starling principle: distinguish the force balance from the full steady-state law

### Modern source and equations

Levick and Michel (2010), *Microvascular fluid exchange and the revised Starling principle*, Cardiovascular Research 87(2), 198–210, DOI 10.1093/cvr/cvq062, explicitly distinguishes:
- the general single-solute membrane flux relation (their Eq. 1a);
- the multi-solute extension (Eq. 1b);
- the conventional Starling expression using interstitial oncotic pressure (Pi_i) (Eq. 1c);
- the revised glycocalyx model, in which the effective downstream oncotic pressure is the subglycocalyx value (Pi_g), not bulk interstitial (Pi_i).

The generalized membrane relation is:
[
\frac{J_v}{A}=L_p(\Delta P-\sigma\Delta\Pi).
]
The conventional Starling expression is:
[
\frac{J_v}{A}=L_p\{(P_c-P_i)-\sigma(\Pi_p-\Pi_i)\}.
]
The revised glycocalyx force balance replaces the downstream oncotic term by (Pi_g):
[
\frac{J_v}{A}=L_p\{(P_c-P_i)-\sigma(\Pi_p-\Pi_g)\},
]
but this is not by itself a closed steady-state prediction if (Pi_g) is unknown.

### Full steady-state model

The review derives an implicit steady-state filtration relation (Eq. 3):
[
\frac{J_v}{A}
=L_p\left[
\Delta P
-\sigma^2\Pi_p
\left(\frac{1-e^{-Pe}}{1-\sigma e^{-Pe}}\right)
\right],
]
where
[
Pe=\frac{J_v(1-\sigma)}{p_d A}.
]
Here (p_d) is the diffusional permeability of the capillary barrier to the macromolecule. Since (J_v) appears on both sides through (Pe), the equation is implicit and must be solved for (J_v/A). It represents the coupled glycocalyx filtration and protein-concentration/convective-washout effect. The review emphasizes that the classical (Pi_i)-based equation is not an adequate steady-state description for most continuous capillaries.

### Decision and correction

The simple revised expression with (Pi_g) is a force-balance component, not the complete revised steady-state model. Discovery batch 36 should therefore:
- retain the (Pi_g)-based force balance as an explanatory relation;
- use the implicit Eq. (3) if the intended candidate is the full revised steady-state filtration model;
- not count classical Eq. (1c), the (Pi_g) force-balance substitution and Eq. (3) as three independent equations;
- freeze (L_p,A,sigma,Pi_p,Delta P,p_d), the macromolecular transport assumptions, and the vascular-bed conditions.

The revised principle is a model lineage, not a universal equation valid for every vascular bed. The review documents exceptions where local epithelial fluid transport permits sustained absorption.

**Disposition:** full revised Starling steady-state model source-verified at the review equation level; hold pending a choice between force-balance component and implicit steady-state model, parameter units, vascular-bed scope and a deterministic implicit-solver adapter.

## 3. Catalogue status and work not performed

No source-register or equation-catalogue record was changed. The formal manifest remains 128 source records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, membrane measurements or microvascular filtration experiments were run. This is literature/source review only.
