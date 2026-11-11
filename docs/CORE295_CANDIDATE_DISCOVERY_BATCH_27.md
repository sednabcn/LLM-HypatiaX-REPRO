# Core-295 candidate discovery batch 27: orbital dynamics, electromagnetic force and crystal diffraction

**Date:** 2026-11-11  
**Status:** discovery-only source leads. None is added to the formal catalogue or counted toward 295.  
**Domain focus:** Physics. This batch records three further relations with explicit derivation-family and interface warnings.

## 1. Kepler third-law orbital period relation

**Source:** OpenStax University Physics Volume 1 §13.5, Eq. 13.11.

For a body of negligible mass orbiting a central mass (M) on a Keplerian ellipse with semi-major axis (a):
[
T^2=\frac{4\pi^2}{GM}a^3.
]
The source derives this from the circular-orbit period relation and extends it to an ellipse by replacing orbital radius with semi-major axis. It explicitly notes that the same law applies to satellites orbiting any sufficiently massive central body in the stated approximation.

**Assumptions:** Newtonian inverse-square gravity, isolated two-body system, orbiting mass negligible relative to central mass in the simplified form, no perturbing bodies or non-gravitational forces. For comparable masses, use the total mass (M+m) in the exact two-body form.

**Structural/derivation issue:** this is a scalar period–semi-major-axis relation, not the Newtonian force law itself. It is derived from the inverse-square central-force model and Kepler's orbital geometry, so retain the derivation parent and treat its source-family dependence separately from structural form. It is not an algebraic rearrangement of (F=GMm/r^2), but it is not an independent source mechanism either.

**Initial disposition:** promising Physics relation; hold pending explicit derivation-family and statistical-unit policy, plus a generator that respects the central mass, orbital regime and Keplerian assumptions.

## 2. Lorentz force law for a charged particle

**Source:** OpenStax University Physics Volume 2 §16.1, Eq. 16.12.

The electric and magnetic force on a particle with charge (q), velocity (mathbf v), electric field (mathbf E) and magnetic field (mathbf B) is
[
mathbf F=q(mathbf E+mathbf v\timesmathbf B).
]
The source presents this after Maxwell's four field equations and states that it gives the force exerted by the fields on a charged particle.

**Assumptions and interface:** SI units; nonrelativistic three-vector form; charge and fields defined at the particle position/time; magnetic contribution perpendicular to velocity and magnetic field. The full vector output must be retained. A scalar magnitude adapter requires the angle between (mathbf v) and (mathbf B) and the relative orientation of electric and magnetic forces; it must not be replaced by an arbitrary single component.

**Structural/derivation issue:** Lorentz force is a matter–field coupling law, not one of Maxwell's field equations. It belongs to the broader electromagnetism source family and depends on the fields supplied by the field model, but it is not derived from Maxwell's equations alone. Do not count the electric-force and magnetic-force terms as separate equations if the complete Lorentz law is the chosen model.

**Initial disposition:** strong source lead, held pending full-vector adapter and explicit separation from the Maxwell field-system family.

## 3. Bragg crystal-diffraction condition

**Source:** OpenStax University Physics Volume 3 §4.6, Eq. 4.6.

For constructive interference from X-rays reflected by adjacent crystal planes:
[
m\lambda=2d\sin\theta,
qquad m=1,2,3,\ldots
]
where (d) is interplanar spacing and (	heta) is measured relative to the crystal plane surface (not the normal) in the OpenStax convention.

**Assumptions and interface:** coherent scattering from periodic crystal planes; path-length difference (2dsin\theta) is an integer wavelength; crystal-plane spacing and wavelength are positive; distinguish the incident/reflected angle convention from conventional optics angles.

**Structural/derivation issue:** the equation is a crystal-plane geometry condition, but its normalized form is the same path-difference constructive-interference relation used in double-slit and diffraction-grating equations. The factor of two comes from the two-leg reflection geometry. Under a strict equation-form policy, cluster Bragg, double-slit and grating maxima as one interference/path-difference family rather than count them as independent equations. A physical-mechanism policy may distinguish crystal scattering from slit/grating geometry, but must be explicit.

**Initial disposition:** authoritative textbook equation verified; hold as a separate count pending the wave-interference structural-equivalence ruling.

## 4. Batch-level decision

| Lead | Structure | Main blocker | Initial decision |
|---|---|---|---|
| Kepler third law | (T^2\propto a^3/M) | Derived from Newtonian central-force dynamics; dependence unit/validity domain | Hold; consider |
| Lorentz force | Vector field-to-particle force with cross product | Full vector output; relationship to Maxwell field-system family | Hold; high priority |
| Bragg condition | Integer path-difference constructive interference | Same normalized path-difference structure as double-slit/grating maxima | Hold; likely one wave-interference family |

These are three source leads, not three independent equations. Do not count the three Lorentz-force terms, Kepler derivation steps, or Bragg order values as separate entries.

## 5. Catalogue status and work not performed

No source-register or equation-catalogue record was changed. The formal manifest remains 128 source records, 19 proposed equation records, zero accepted equations, and an unfrozen sampling frame.

No experiments, validators, solvers, workflows, paid compute, API calls, orbital observations, electromagnetic measurements or diffraction experiments were run. This is source discovery only.
