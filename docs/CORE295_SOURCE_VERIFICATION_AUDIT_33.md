# Core-295 source verification audit 33: Kepler orbital period, Lorentz force and Bragg diffraction

**Date:** 2026-11-11  
**Status:** verification of discovery-batch 27 leads only. No equation is added to the formal catalogue or counted toward 295.

## 1. Kepler third-law orbital period relation

OpenStax University Physics Volume 1 §13.5, Eq. 13.11, derives:
\[
T^2=\frac{4\pi^2}{GM}a^3
\]
for a body of negligible mass orbiting a central mass \(M\) on a Keplerian ellipse with semi-major axis \(a\). The more general two-body expression replaces \(M\) with \(M+m\).

The source derives the circular-orbit form from Newtonian gravity and extends it to elliptical orbits by replacing the circular radius with the semi-major axis. The relation assumes an isolated Newtonian two-body system, inverse-square gravity, and no perturbations or non-gravitational forces.

**Structural boundary:** the period–semi-major-axis power law is not an algebraic rearrangement of the force law \(F=GMm/r^2\), but it is a derived consequence of the same inverse-square central-force model. Keep it linked to Newtonian orbital dynamics and do not count circular-orbit, elliptical-orbit, negligible-secondary-mass and exact-two-body forms as independent candidates.

**Disposition:** modern textbook equation and assumptions verified. Hold pending the policy for derived orbital relations and the statistical unit for a two-body system.

## 2. Lorentz force law

OpenStax University Physics Volume 2 §16.1, Eq. 16.12, gives the force on a charge \(q\) moving with velocity \(\mathbf v\) in electric and magnetic fields:
\[
\mathbf F=q(\mathbf E+\mathbf v\times\mathbf B).
\]
This is a vector law in SI units. The electric contribution is \(q\mathbf E\); the magnetic contribution is perpendicular to both \(\mathbf v\) and \(\mathbf B\). The magnetic force does no instantaneous work because \(\mathbf v\cdot(\mathbf v\times\mathbf B)=0\).

The law describes the force on charged matter from electromagnetic fields. It is not one of Maxwell's field equations, which determine how fields are generated and evolve. It is coupled to the field system but is not derived from Maxwell's equations alone.

**Adapter boundary:** preserve the three-vector output and vector cross product. A scalar magnitude requires the angle between \(\mathbf v\) and \(\mathbf B\), plus the relative orientation of the electric and magnetic force vectors. A single component or norm-only target loses information unless the geometry is explicitly frozen. Do not count electric and magnetic terms as separate candidates.

**Disposition:** equation and vector interpretation verified. Retain as a strong Physics source lead, discovery-only, pending vector-valued adapter and explicit field/particle interface.

## 3. Bragg crystal-diffraction condition

OpenStax University Physics Volume 3 §4.6, Eq. 4.6, gives the constructive-interference condition for X-rays reflected from adjacent crystal planes:
\[
m\lambda=2d\sin\theta,\qquad m=1,2,3,\ldots
\]
where \(d\) is the interplanar spacing and \(\theta\) is measured relative to the crystal plane in the source's convention. The path difference between rays reflected from adjacent planes is \(2d\sin\theta\).

**Structural boundary:** Bragg's law is a crystal-plane geometry condition, but its normalized mathematical structure is the same integer path-difference constructive-interference condition as double-slit and diffraction-grating maxima. The factor of two is from the two-leg reflection geometry. If the unit is structural equation form, keep these in one wave-interference family; a physical-mechanism policy may distinguish crystal diffraction from slit/grating geometry but must be declared consistently.

**Disposition:** exact textbook equation and angle convention verified. Hold pending the cross-geometry interference-family policy and crystal geometry/range contract.

## 4. Cross-lead conclusion

Kepler, Lorentz and Bragg are different physical relations, but only Lorentz has a clearly distinct force-law structure among the three without an immediate derivation/functional-equivalence blocker:
- Kepler third law is a derived orbital consequence of Newtonian inverse-square dynamics;
- Lorentz force is a vector matter–field coupling law;
- Bragg is a crystal-specific path-difference interference condition.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, orbital observations, force measurements or diffraction experiments were run. This is source review only.
