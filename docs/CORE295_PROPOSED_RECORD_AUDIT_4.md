# Core-295 proposed-record audit 4: Hagen–Poiseuille formula provenance and Navier–Stokes lineage

**Date:** 2026-11-11  
**Status:** provenance and family audit only. No equation is accepted by this audit.

## 1. PHYS-POISEUILLE-001 — modern formula versus Poiseuille's original empirical law

The current proposed record is
[
Q=\frac{(p_2-p_1)\pi r^4}{8\eta L}.
]
Its manifest source is OpenStax *University Physics, Volume 1*, §14.7, Eq. 14.19. The formula is a valid modern Hagen–Poiseuille expression for steady laminar flow in a straight cylindrical tube of a Newtonian fluid, subject to the stated no-slip, fully developed-flow assumptions.

However, this viscosity-explicit expression should not be presented as a verbatim equation from Poiseuille's original experimental work. The historical analysis by Sutera and Skalak, “The history of Poiseuille's law,” *Annual Review of Fluid Mechanics* 25 (1993), 1–19, distinguishes Poiseuille's empirical relation
[
Q=K\frac{\Delta P D^4}{L},
]
where the empirical coefficient depends on the liquid and temperature, from the later viscosity-explicit form. Their review states that Poiseuille did not formulate the relation in terms of viscosity; the more usual viscosity-explicit equation was derived later, commonly attributed to Hagenbach (1860), with related derivations by Jacobson/Neumann and others. The review also discusses Stokes's 1845 fluid equations and the later derivation history. See [Sutera & Skalak (1993)](https://doi.org/10.1146/annurev.fl.25.010193.000245) and the accessible text [here](https://djvu.online/file/bYloi0BlQQOnd).

A separate historical account likewise records Poiseuille's empirical (K\Delta P D^4/L) form and notes that neither Poiseuille nor Hagen wrote the coefficient explicitly as viscosity in their empirical formulas; see [A brief history of arterial wave mechanics](https://pmc.ncbi.nlm.nih.gov/articles/PMC2644374/). The current OpenStax equation remains a suitable authoritative modern equation source, but its historical naming/provenance must be stated accurately.

**Required correction:** use the display name **Hagen–Poiseuille laminar tube-flow relation** and describe it as the modern viscosity-explicit relation, not as a verbatim Poiseuille 1840 equation. If the benchmark intends to represent Poiseuille's original empirical law instead, that is a different parameterization with an empirical (K), and it requires a separate decision about whether the viscosity-explicit derivation is a distinct equation or merely a mechanistic refinement.

## 2. Navier–Stokes derivation-family overlap

The Hagen–Poiseuille profile/flow relation is a special fully developed laminar pipe-flow solution of the viscous-fluid momentum equations. The provisional Physics family map already groups Navier–Stokes and Poiseuille under fluid mechanics and notes the special-solution relationship.

This is not a claim that the scalar flow-rate formula is algebraically identical to the full vector PDE. It is a derivation-parent relationship. The catalogue must decide whether a special analytical solution of a broader PDE counts as a distinct equation for Option 2, and apply that rule consistently to other domains (for example, reduced ODEs or special solutions of field equations). If the policy permits such reductions, retain the parent link and do not treat the two as independent statistical units without a separate sampling argument.

## 3. Technical conditions to preserve

The proposed assumptions are broadly appropriate but should be made operational:
- steady, incompressible, Newtonian flow;
- straight, rigid, circular tube of constant radius;
- no-slip boundary at the wall;
- fully developed laminar velocity profile;
- pressure drop measured between the tube ends;
- entrance effects, compliance, non-Newtonian rheology and turbulence excluded.

Generated samples must satisfy a declared laminarity condition (including a consistent Reynolds-number definition), positive radius, viscosity and length, and positive pressure drop. Train/extrapolation ranges and deterministic generator remain pending.

## 4. Required resolution before acceptance

1. Rename the candidate to **Hagen–Poiseuille laminar tube-flow relation** and distinguish the modern viscosity-explicit expression from Poiseuille's empirical original.
2. Preserve OpenStax §14.7 Eq. 14.19 as the direct modern equation source; add exact historical provenance only when the primary derivation source and exact location are verified.
3. Decide and document how special solutions of broader PDEs are counted under structural distinctness; preserve the Navier–Stokes derivation parent and shared source-family/independence metadata.
4. Freeze a Reynolds-number-valid input domain, units, pressure convention and deterministic generator.

The manifest entry remains **proposed**. This audit does not change its status, count it toward Physics's 59, or authorize shard planning.

## 5. Audit boundary

No catalogue validator, experiment, paid compute, live API/protocol call or GitHub Actions workflow was run. No experiment results are implied by this source review.
