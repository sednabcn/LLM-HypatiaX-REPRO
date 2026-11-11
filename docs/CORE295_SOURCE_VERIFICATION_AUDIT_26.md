# Core-295 source verification audit 26: Fick 1855 one-dimensional diffusion flux and cross-domain transport equivalence

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** proposed record CHEM-FICK-FLUX-001 and primary source CHEM-FICK-1855.

## 1. Original source transcription

Adolf Fick, *Ueber Diffusion*, Annalen der Physik 170(1) (1855), 59–86, DOI 10.1002/andp.18551700105.

On original printed p. 66, Fick states that for a horizontal elemental layer at position (x) with concentration (y), the amount of salt crossing from that layer into the next layer during (dt) is
[
dM=-Q,k\,\frac{dy}{dx}\,dt,
]
where (Q) is the layer's cross-sectional area and (k) is a substance-dependent constant. The original OCR scan is imperfect in the printed symbols, but the equation and its surrounding definitions are legible enough to confirm the local constitutive relation. Dividing by (Q,dt) gives the modern one-dimensional flux form:
[
J=-D\frac{dC}{dx},
]
with the modern diffusivity (D) corresponding to the source's proportionality coefficient under the selected concentration/mass convention.

Fick explicitly motivates the law by analogy with Fourier's law for heat conduction and Ohm's law for electrical conduction. He then combines the local transfer law with conservation to derive the diffusion PDE. The original source therefore directly supports both the local gradient-flux relation and its lineage as a transport-law analogue.

## 2. Mathematical and dimensional boundary

For a mass or molar concentration (C) in amount per volume, (D) has dimensions of length squared per time, and (J) has dimensions of amount per area per time. The sign convention is down-gradient transport. The benchmark must fix:
- species and medium;
- concentration basis (mass or molar);
- spatial coordinate and positive direction;
- one-dimensional geometry and cross-sectional interpretation;
- constant diffusivity over the sampled local range;
- no bulk advection, source/sink or anisotropic transport in the selected constitutive law.

The original paper's second-order diffusion equation is derived by combining this first-law flux with conservation and a specified geometry. It is not an independent candidate from the same local flux law. The constant-cross-section PDE specialization is likewise a geometry-specific reduction.

## 3. Structural-equivalence ruling required

The original source itself identifies the analogy to Fourier heat conduction and Ohm electrical conduction. In modern notation, all three are linear constitutive transport relations:
[
\text{flux}=-\text{transport coefficient}\times\text{driving-field gradient}.
]
Their physical fields and units differ, but their normalized functional structure is the same. This is exactly the distinction Core-295 must resolve:
- if the unit is a structurally distinct equation form, Fick flux, Fourier heat flux and Ohm current-density laws belong to one linear-gradient transport family and cannot automatically count as separate equations;
- if the unit is a distinct physical mechanism, they may be eligible as different domain instantiations, but that rule must be applied consistently to Henry/Raoult, Langmuir/Michaelis–Menten and other cross-domain analogues.

The source-family label CHEM-FICK-DIFFUSION-FLUX does not by itself settle cross-domain mathematical equivalence.

## 4. Decision

**Disposition:** original source and modern flux transcription verified. Retain as a valid diffusion constitutive law, but hold from formal acceptance pending the cross-domain linear-gradient transport policy. Do not count the derived second law, constant-area PDE, Fourier/Ohm analogues, coordinate changes or algebraic rearrangements as extra candidates under a strict structural rule.

No catalogue record or status was changed. The formal catalogue remains at 128 source records, 19 proposed records and zero accepted records; the sampling frame remains unfrozen.

No experiments, solvers, validators, workflows, paid compute, API calls or diffusion measurements were run. This is historical source review and dimensional analysis only.
