# Core-295 candidate discovery batch 21: Physics elasticity, buckling and beam vibration

**Status:** primary-source and modern-equation tracing only. No equation is accepted or counted toward the 59 Physics target.

## 1. Euler elastica (1744)

**Primary source:** Leonhard Euler, Additamentum I, “De curvis elasticis,” in *Methodus inveniendi lineas curvas maximi minimive proprietate gaudentes* (1744). [Euler archive record and downloadable text](https://scholarlycommons.pacific.edu/euler-works/174/). A modern historical reconstruction is available in [Bistafa (2023)](https://doi.org/10.56031/2693-9908.1055).

The planar inextensible elastica is a variational equilibrium of an elastic rod. In modern notation, the constitutive moment-curvature relation is:

\[
M(s)=EI\kappa(s)=EI\frac{d\theta}{ds},
\]

and, for a rod under a constant end force \(F\) with no distributed couple, one common angle form is:

\[
EI\frac{d^2\theta}{ds^2}+F\sin\theta=0,
\]

with sign depending on the force/angle convention. This is a nonlinear boundary-value problem; end positions, end tangents, applied moments and inextensibility constraints determine the solution.

**Boundary:** the displayed angle equation is a modern form of the elastica equilibrium, not a verbatim equation copied from Euler's 1744 Latin text. The historical derivation uses variational quantities and its own notation. Preserve the exact force geometry and end conditions when transcribing. Different loading and boundary conditions yield different elastica solutions, not automatically distinct equation families.

## 2. Euler column buckling (1759)

**Primary source:** Euler, “Sur la force des colonnes,” *Mémoires de l’Académie des sciences de Berlin* 13 (1759), 252–282. [Euler archive record](https://scholarlycommons.pacific.edu/euler-works/238/).

The familiar modern critical-load expression is:

\[
P_{cr}=\frac{\pi^2EI}{(KL)^2},
\]

where \(E\) is Young's modulus, \(I\) the second moment of area, \(L\) the member length and \(K\) the effective-length factor determined by end restraints. For a pin-ended column, \(K=1\); for a fixed-free cantilever, \(K=2\), giving \(P_{cr}=\pi^2EI/(4L^2)\).

Euler's original notation uses a flexural-rigidity coefficient and treats specific end constraints; the modern effective-length factor is a later unifying convention. The historical source should be transcribed with its actual boundary condition before using a general K-factor form.

**Boundary:** the critical load is an eigenvalue/stability threshold for a slender elastic column under centered axial compression. It assumes linear-elastic material response, small deflection up to instability, idealized end supports and a sufficiently slender member. Inelastic buckling, initial curvature, eccentricity and local buckling are outside the classical formula.

## 3. Timoshenko beam vibration and shear deformation (1921 onward)

**Primary source:** S. P. Timoshenko, “On the correction for shear of the differential equation for transverse vibrations of prismatic bars,” *Philosophical Magazine* 41(245) (1921), 744–746, DOI [10.1080/14786442108636264](https://doi.org/10.1080/14786442108636264). A modern equation transcription with kinematics and boundary conditions is given by [TU Delft's Timoshenko beam theory notes](https://teachbooks.tudelft.nl/computational-modelling/structural_linear/timoshenko.html).

The Timoshenko beam model uses transverse displacement \(w(x,t)\) and cross-section rotation \(\theta(x,t)\) as independent fields. The shear strain is \(\gamma=w_x-\theta\), with constitutive relations:

\[
M=EI\theta_x,
\qquad
V=\kappa GA(w_x-\theta),
\]

where \(M\) is bending moment, \(V\) shear force, \(G\) shear modulus and \(\kappa\) a shear-correction factor. In dynamic form, the coupled balances are:

\[
\rho A w_{tt}=\partial_x\left[\kappa GA(w_x-\theta)\right]+q,
\]

\[
\rho I\theta_{tt}=\partial_x(EI\theta_x)+\kappa GA(w_x-\theta)+m.
\]

The model retains shear deformation and rotary inertia, which the Euler–Bernoulli slender-beam model neglects.

**Boundary:** the 1921 paper addresses a shear correction in transverse vibration; the full modern two-field Timoshenko beam equations should be cited to a later derivation and checked against the historical development. Euler–Bernoulli is a limiting approximation as shear stiffness becomes large and rotary inertia is negligible. Do not count the two models as independent without a declared model-family and validity-range distinction.

## Source-family and overlap controls

- Euler elastica and Euler column buckling share elastic-curve mechanics. Buckling is a stability/eigenvalue problem built from an elastic-column model; the critical load is not a new constitutive law.
- The Euler–Bernoulli beam equation, Timoshenko beam equations and Euler elastica are related structural-mechanics models but differ in kinematic assumptions and state variables. Record the model hierarchy and approximation limits.
- End-condition factors in Euler buckling, beam mode shapes, natural frequencies and critical loads are derived consequences of the same governing beam/column model.
- Timoshenko's shear-correction paper and modern coupled-field beam equations are not interchangeable source records. Preserve primary-source history and modern equation derivation separately.
- Core-15 exclusions remain active; no kinetic-energy or gravitational-force equation is added as a separate candidate.

## Acceptance requirements

For elastica, specify rod inextensibility, bending stiffness, load geometry, arc-length parameter, end conditions and distributed forces/couples. For Euler buckling, specify material linearity, cross-section inertia, length, end-restraint factor, axial-load eccentricity and slenderness range. For Timoshenko beams, specify shear coefficient, shear modulus, rotary inertia, cross-section geometry, load/moment, initial and boundary conditions, and whether dynamic or static equations are used.

All records remain candidates. No Physics entry is accepted; no experiment or workflow has been run.
