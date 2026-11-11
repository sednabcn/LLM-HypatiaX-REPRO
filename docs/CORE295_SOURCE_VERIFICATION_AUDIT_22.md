# Core-295 source verification audit 22: thin-lens imaging and Hagen–Poiseuille tube flow

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** proposed records PHYS-THIN-LENS-001 and PHYS-POISEUILLE-001.

## 1. Thin-lens imaging relation

OpenStax University Physics Volume 3 §2.4 derives the thin-lens equation by taking the thin-lens limit of refraction at the two lens surfaces. It prints:
[
\frac{1}{d_o}+\frac{1}{d_i}=\frac{1}{f}
\qquad\text{(Eq. 2.19)}.
]
The source defines (d_o) as object distance, (d_i) as image distance and (f) as focal length. It explicitly gives the sign convention:
- (d_i>0) for a real image on the side opposite the object, (d_i<0) for a virtual image;
- (f>0) for a converging lens, (f<0) for a diverging lens.

The proposed rearrangement
[
d_i=\frac{f d_o}{d_o-f}
]
is algebraically equivalent, not a second equation. The singular case (d_o=f) corresponds to an image at infinity and must not be treated as a finite-valued sample.

OpenStax also derives the lens-maker equation:
[
\frac{1}{f}
=\left(\frac{n_2}{n_1}-1\right)
\left(\frac{1}{R_1}-\frac{1}{R_2}\right).
]
It is a related but distinct relation connecting focal length to refractive indices and surface curvatures. The current proposed record is only the imaging equation; do not silently expand it into a second candidate. Keep both, if ever sampled, in one geometric-optics family and resolve whether they are separate structural units under the benchmark policy.

The thin-lens approximation requires lens thickness small relative to the radii of curvature and the relevant internal image distance; the derivation uses paraxial/geometric optics. Chromatic aberration, thick-lens effects and non-paraxial behavior are outside this model.

**Disposition:** exact modern equation, derivation and sign convention verified. Retain as a credible Physics candidate, held pending a complete signed-distance generator and physical range contract.

## 2. Hagen–Poiseuille laminar tube-flow relation

OpenStax University Physics Volume 1 §14.7 prints the flow resistance for an incompressible fluid of viscosity (eta) in a horizontal tube of uniform radius (r) and length (l):
[
R=\frac{8\eta l}{\pi r^4}
\qquad\text{(Eq. 14.18)}.
]
Combining this with (Q=(p_2-p_1)/R) gives:
[
Q=\frac{(p_2-p_1)\pi r^4}{8\eta l}
\qquad\text{(Eq. 14.19)}.
]
The source identifies the model as laminar tube flow, with flow from higher pressure (p_2) to lower pressure (p_1). The proposed equation is the correct viscosity-explicit form. The resistance identity and pressure-flow relation are its derivation components, not separate independent equations.

The current record should not attribute the complete modern viscosity-explicit expression solely to Poiseuille's original empirical work. The proposed source is OpenStax's modern textbook statement; historical lineage and the distinction between Poiseuille's original empirical law and later viscosity-explicit derivation are documented in the earlier proposal audit.

The benchmark must enforce:
- (p_2>p_1), (r>0), (eta>0), (l>0);
- incompressible Newtonian fluid and constant dynamic viscosity;
- straight rigid cylindrical tube, uniform radius, no-slip wall and fully developed flow;
- laminar Reynolds-number regime, not merely positive parameter values;
- negligible entrance/exit effects and a horizontal tube under the stated derivation.

A sample outside the laminar regime is invalid even if the algebraic expression returns a number.

**Disposition:** exact equation and assumptions verified against OpenStax Eq. 14.19. Retain as a credible Physics candidate, held pending a physically constrained Reynolds-number and geometry generator.

## 3. Family and catalogue decision

Thin-lens imaging and laminar tube flow are physically and mathematically distinct. Within geometric optics, the thin-lens equation is related to the lens-maker equation and other paraxial relations; within viscous fluid mechanics, Poiseuille flow is related to the resistance representation and Navier–Stokes special solutions. Do not count algebraic rearrangements, component relations or parameter variations as independent equations.

No catalogue record, source status, proposed count or accepted count was changed. The formal catalogue remains at 128 source records, 19 proposed records and zero accepted records; the sampling frame remains unfrozen.

No experiments, solvers, validators, workflows, paid compute, API calls, optical measurements or fluid-flow experiments were run. This is source review only.
