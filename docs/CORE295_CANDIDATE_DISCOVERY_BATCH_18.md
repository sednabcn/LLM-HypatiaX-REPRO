# Core-295 candidate discovery batch 18: Physics viscous-fluid dynamics and blackbody radiation

**Status:** primary-source tracing only. No equation is accepted or counted toward the 59 Physics target.

## 1. Navier–Stokes momentum equation: Navier (1822/1823) and Stokes (1845)

**Primary source trail:**
- Navier, “Mémoire sur les lois du mouvement des fluides,” read 18 March 1822 and published in *Mémoires de l’Académie royale des sciences* 6 (1823), 389–416. [Bibliographic catalogue record](https://ccfr.bnf.fr/portailccfr/ark:/16871/0018999898).
- Stokes, “On the theories of the internal friction of fluids in motion, and of the equilibrium and motion of elastic solids,” read 14 April 1845, *Transactions of the Cambridge Philosophical Society* 8, 287–319 (published 1849); [Cambridge reprint](https://doi.org/10.1017/CBO9780511702242.005).

For an incompressible Newtonian fluid with constant viscosity, the modern vector form is:

\[
\rho\left(\frac{\partial\mathbf u}{\partial t}
+(\mathbf u\cdot\nabla)\mathbf u\right)
=-\nabla p+\mu\nabla^2\mathbf u+\rho\mathbf f,
\qquad \nabla\cdot\mathbf u=0.
\]

Here \(\rho\) is density, \(\mathbf u\) velocity, \(p\) pressure, \(\mu\) dynamic viscosity and \(\mathbf f\) body force per unit mass.

**Historical boundary:** the modern compact vector form is a later synthesis of momentum conservation and Newtonian viscous stress. Navier's original molecular-force derivation and Stokes's internal-friction formulation should not be presented as identical verbatim equations. The source family requires a clear lineage note and a specific fluid constitutive assumption.

**Overlap:** Poiseuille flow (Batch 10) is a special steady laminar pipe-flow solution of the viscous momentum equations. It is not an independent sample from Navier–Stokes if generated from the same assumptions. Bernoulli's equation is a different inviscid energy integral and should be kept distinct but within the broader fluid-mechanics cluster.

## 2. Planck blackbody radiation law (1900/1901)

**Primary source:** Max Planck, “Ueber das Gesetz der Energieverteilung im Normalspectrum,” *Annalen der Physik* 309(3) (1901), 553–563, DOI [10.1002/andp.19013090310](https://doi.org/10.1002/andp.19013090310). The result was first communicated to the German Physical Society in October and December 1900. The energy-distribution formula appears as equation (8), p. 554.

A modern SI wavelength form for blackbody spectral energy density is:

\[
u_\lambda(T)=
\frac{8\pi hc}{\lambda^5}
\frac{1}{\exp\left(\frac{hc}{\lambda k_BT}\right)-1}.
\]

The corresponding spectral exitance/intensity convention used by OpenStax is:

\[
M_\lambda(T)=
\frac{2\pi hc^2}{\lambda^5}
\frac{1}{\exp\left(\frac{hc}{\lambda k_BT}\right)-1},
\]

with \(M_\lambda=(c/4)u_\lambda\) for isotropic radiation in a blackbody cavity. OpenStax University Physics Vol. 3 §6.1, Eq. 6.11, prints the latter wavelength intensity form.

**Boundary:** do not mix spectral radiance, spectral exitance and energy density without their angular and unit conventions. Planck's original notation and constants differ from modern SI notation; equation (8) should be transcribed in its original spectral convention before acceptance.

**Overlap:** Wien's displacement law follows by maximizing the spectral distribution; Stefan–Boltzmann's law follows by integrating over wavelength. They are derived consequences of the same Planck spectrum and are not separate independent equation families. Stefan's law is already listed in Batch 10; cluster it here with the parent spectrum.

## Cross-family and benchmark controls

- Navier–Stokes is a vector PDE system. The incompressibility constraint is part of the system, not an independent scalar formula. Define domain geometry, initial and boundary conditions, fluid properties, body forces and the velocity/pressure observable.
- Poiseuille flow is a special solution of Navier–Stokes for a cylindrical pipe under steady, laminar, fully developed conditions. Do not count both as independent statistical units if one is derived from the other.
- Bernoulli is the inviscid energy relation; Navier–Stokes retains viscous stress. The assumptions and model classes must remain explicit.
- Planck spectral energy density, spectral radiance/exitance, Wien displacement and Stefan–Boltzmann total power are linked by angular conversion, maximization or integration. Keep one blackbody-radiation source family.
- Core-15 exclusions remain active; no kinetic-energy equation or gravitational-force formula is introduced through the fluid momentum model.

## Acceptance requirements

For Navier–Stokes, specify compressibility, viscosity law, fluid density, body force, geometry, boundary/initial conditions and pressure gauge. For Planck radiation, specify spectral variable (frequency or wavelength), radiometric quantity, angular convention, absolute temperature and SI constants. Exact primary-source notation and modern-unit conversions must be independently checked before acceptance.

All records remain candidates. No Physics entry is accepted; no experiment or workflow has been run.
