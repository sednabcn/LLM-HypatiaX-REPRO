# Core-295 Fick flux source and operator audit 1

Date: 2026-11-12

Candidate: `CHEM-FICK-FLUX-001`

## Primary source and exact law

Adolf Fick, “Ueber Diffusion,” *Annalen der Physik* 170(1) (1855), 59–86, DOI 10.1002/andp.18551700105. The Wiley publisher record verifies the original article and pagination. The original German scan text at printed p.66 states the local transfer relation

\[
dM=-Qk\frac{dy}{dx}dt,
\]

where Q is the cross-sectional area, k is a substance-dependent constant and y is concentration. The equation gives transferred amount through area Q over time dt, not a separately named modern flux variable. Dividing by Q dt and mapping original k,y to modern D,C gives the one-dimensional flux notation

\[
J=-D\frac{dC}{dx}.
\]

The English translation in *Philosophical Magazine* 10 (1855), 30–39, also preserves the original local transfer statement. The original paper then derives the diffusion evolution equation by a conservation argument. Its variable-cross-section PDE and constant-cross-section specialization are downstream balance equations, not separate local constitutive laws.

## Scope and dimensional contract

- One-dimensional local diffusive flux in a homogeneous medium.
- D is the constant diffusivity, m² s⁻¹.
- C is amount concentration, e.g. mol m⁻³; dC/dx is mol m⁻⁴.
- J is molar flux, mol m⁻² s⁻¹.
- The negative sign means flux points down the concentration gradient under the chosen positive x direction.
- No advection, convection, anisotropy, concentration-dependent diffusivity, or nonideal chemical-potential formulation is included.
- The original paper's k is not automatically identical in units to a modern SI diffusivity until the original concentration and length conventions are mapped consistently. This catalogue uses modern SI notation as an adapter.

The original experiments concern salt diffusion in aqueous solutions and Fick notes that the diffusion constant depends on the substance and increases with temperature in the measurements discussed. No universal D value or transferable training/extrapolation range is supported by this historical source alone.

## Structural-equivalence blocker

Fick explicitly develops his diffusion-flow equation by analogy with Fourier's heat-flow development. The normalized local operator is a scalar flux proportional to a first spatial gradient with a negative coefficient:

\[
\text{flux}=-\text{transport coefficient}\times\text{driving-field gradient}.
\]

The same operator topology appears in Fourier heat conduction (heat flux versus temperature gradient) and Ohmic conduction (current density versus electric-field/potential gradient, subject to constitutive convention). The transported quantity and physical mechanism differ, but the normalized constitutive structure is the same.

Under the draft Core-295 E0-E5 policy, this appears to be E3 (same normalized structure, different physical mechanism), which is not countable as structurally distinct unless the policy is explicitly revised. Source-family distinction does not solve this structural issue. The candidate must be compared against the physics-domain Poiseuille candidate and the frozen Core-15 exclusion registry as well.

## Catalogue disposition

Keep the candidate proposed and generator pending. Do not promote it or count it toward the 59 Chemistry equations until the cross-domain E3 decision is resolved. Keep numerical D and gradient sampling ranges unset; a future benchmark must name a specific solute/medium/temperature and source a measured diffusivity dataset. Fick's second law remains a derived conservation equation and is not a second row in this family.

## Sources

- Fick (1855), original publisher record and free-access article: https://onlinelibrary.wiley.com/doi/10.1002/andp.18551700105
- Fick (1855), Wiley original scan metadata and page 66 local transfer equation: https://onlinelibrary.wiley.com/doi/pdf/10.1002/andp.18551700105
- Fick (1855), English translation, *Philosophical Magazine* 10, 30–39: https://doi.org/10.1080/14786445508641925
- Fick (1855), scan text reproducing p.66 equation: https://de.scribd.com/document/647162659/Annalen-Der-Physik-1855-Fick-Ueber-Diffusion

No scripts, validators, tests, workflows, live experiments or scientific simulations were run.
