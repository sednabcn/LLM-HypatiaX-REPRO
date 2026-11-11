# Core-295 candidate discovery batch 10: Physics fluid and thermal transport

**Status:** source-backed discovery only. No equation is accepted or counted toward the 59 Physics target.

## Source map

| Family | Exact source location | Candidate relation | Review boundary |
|---|---|---|---|
| Mass continuity in fluid flow | OpenStax University Physics Vol. 1, §14.5 and Ch. 14 key equations, [Fluid Mechanics](https://openstax.org/books/university-physics-volume-1/pages/14-key-equations) | \(\rho_1A_1v_1=\rho_2A_2v_2\); incompressible special case \(A_1v_1=A_2v_2\). | The constant-density form is a special case, not a second family. It is a conservation statement; specify cross-section averaging, steady flow and whether density varies. |
| Bernoulli flow relation | OpenStax University Physics Vol. 1, §14.6, [Bernoulli’s Equation](https://openstax.org/books/university-physics-volume-1/pages/14-6-bernoullis-equation), Eq. 14.16 | \(p+\frac12\rho v^2+\rho gy=\text{constant}\) along a streamline. | Derived from mechanical-energy conservation for steady, incompressible, frictionless flow. Its kinetic-energy-density and gravitational-potential terms are not independent equations. Treat Bernoulli and constant-height Bernoulli principle as one family; do not use outside assumptions or across arbitrary streamlines. |
| Poiseuille laminar pipe flow | OpenStax University Physics Vol. 1, §14.7 and Ch. 14 key equations | \(Q=\frac{(p_1-p_2)\pi r^4}{8\eta l}\), with hydraulic resistance \(R=\frac{8\eta l}{\pi r^4}\). | A distinct constitutive transport relation for steady laminar Newtonian flow through a cylindrical tube. Flow-rate and resistance forms are reciprocal representations of the same law. Define tube radius/length, viscosity, pressure drop, no-slip boundary and laminar regime. |
| Fourier conductive heat transfer | OpenStax University Physics Vol. 2, §1.6 and Ch. 1 key equations, [Mechanisms of Heat Transfer](https://openstax.org/books/university-physics-volume-2/pages/1-6-mechanisms-of-heat-transfer) | For a uniform slab at steady state, \(P=\frac{kA(T_h-T_c)}{d}\). | This is a one-dimensional steady geometry reduction of Fourier’s heat-conduction law. Do not count the general flux law, slab reduction and rearrangements as separate equations. Specify conductivity, area, thickness, boundary temperatures and absence of internal heat generation. |
| Stefan–Boltzmann radiation | OpenStax University Physics Vol. 2, §1.6, same source | Emitted power \(P=\sigma eAT^4\); net radiative transfer to an environment is proportional to \(\sigma eA(T_{object}^4-T_{environment}^4)\). | Emission and net-transfer forms belong to one radiation family. State absolute temperature, emissivity, surface area, environment temperature and idealized grey/diffuse assumptions. |
| Damped harmonic oscillator | OpenStax University Physics Vol. 1, §15.5, [Damped Oscillations](https://openstax.org/books/university-physics-volume-1/pages/15-5-damped-oscillations), Eqs. 15.23–15.25 | \(m\ddot x+b\dot x+kx=0\); underdamped solution \(x(t)=A_0e^{-bt/(2m)}\cos(\omega t+\phi)\), with \(\omega=\sqrt{k/m-(b/(2m))^2}\). | The ODE, underdamped solution and damped frequency are one source family. The solution changes by damping regime; require positive mass/stiffness, damping regime and initial conditions. Do not count the same ODE's underdamped, critical and overdamped cases as independent equations. |

## Cross-family and Core-15 overlap controls

- Continuity and Bernoulli are conservation-law statements; the latter is an energy integral under ideal-flow assumptions. Their simplified forms are not independent statistical units.
- Poiseuille flow is a more specific viscous transport law and should not be confused with Bernoulli's inviscid relation. The resistance expression is the reciprocal parameterization of the same flow law.
- Fourier slab conduction and the general heat-flux law are one constitutive transport family; geometry-specific reductions are not new families.
- Stefan–Boltzmann emitted power and net radiative transfer share one temperature-fourth-power law.
- Damped oscillator ODE, solution, frequency and damping-regime cases are linked. A fitted time series is benchmarkable only after initial conditions, units and regime are specified.
- Core-15 exclusions remain active. Bernoulli's energy-density terms do not justify adding the excluded kinetic-energy formula as a separate candidate.

## Benchmarkability requirements

For fluid laws, specify fluid model, flow regime, geometry, boundary conditions and whether density is constant. For thermal laws, specify material properties, geometry, emissivity and thermal boundary conditions. For oscillators, specify mass, stiffness, damping, initial displacement/velocity and time range. Every candidate needs exact equation transcription, units, validity regime and source-family/independence metadata.

All records remain candidates. No Physics entry is accepted; no experiment or workflow has been run.
