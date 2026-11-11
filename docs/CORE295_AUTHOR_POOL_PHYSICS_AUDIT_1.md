# Core-295 author-pool Physics audit 1

**Status:** static discovery-pool audit only. No equation is accepted or imported into the formal catalogue by this review.

**Input:** user-supplied `author_pool.py`, Physics block (75 rows). The file header explicitly states that formulas were assistant-written from generic textbook forms, have not been human-verified, and lack reliable row-level primary citations. Its default extrapolation rule `(hi, 5*hi)` is not a physical validity rule. The script was not executed; no solver, generator, validator or experiment was run.

## Executive assessment

The 75 rows are a broad introductory-physics formula collection, not 75 independently sourced equation models. Several rows are rearrangements, derived observables, special cases, or components of the same governing model. The most obvious clusters are:

- **Kinematics/projectiles:** constant-acceleration displacement and final-speed relations; projectile range and maximum height; projectile motion is one idealized trajectory with shared launch variables and assumptions.
- **Gravity/orbits:** Newtonian gravitational field, potential energy, Kepler period, orbital angular momentum and tidal acceleration share Newtonian gravitation/orbit mechanics; Kepler's law is derived from inverse-square gravity under a two-body/circular-orbit approximation.
- **Circular motion:** centripetal force is mass times centripetal acceleration, not a separate structure.
- **Oscillations/circuits:** damped oscillator response, driven resonance and circuit transients/impedance share linear dynamical-system structure in different physical realizations. RC charge/discharge are complementary responses of one first-order RC model.
- **Thermal radiation:** Planck spectrum, Wien displacement, Stefan–Boltzmann total exitance and Rayleigh–Jeans approximation are one blackbody-radiation family; Rayleigh–Jeans is a limiting approximation to Planck.
- **Nuclear/quantum:** radioactive activity is the derivative/rate observable of exponential decay; Bohr energy and radius are linked outputs of one hydrogenic model; matter-wave kinetic energy and particle-in-a-box expressions are linked through de Broglie/quantum mechanics.
- **Fluid mechanics:** quadratic drag and its terminal-speed balance are linked; Stokes drag is a distinct low-Reynolds-number regime of fluid drag; Torricelli outflow is a Bernoulli special case; hydrostatic pressure is the static-fluid limit of the same continuum mechanics.
- **Wave optics/acoustics:** double-slit and single-slit expressions are distinct interference/diffraction structures but share wave-optics assumptions; travelling waves, beats, standing-wave frequencies and wave energy/intensity share wave kinematics and energy transport.
- **Electromagnetism:** Faraday induction, wire force, magnetic moment, solenoid energy, coaxial capacitance, Hall voltage, skin depth and Poynting flux are not interchangeable, but several are consequences/solutions of Maxwell equations and constitutive laws. Their exact geometry/material conventions need to be specified.
- **Mechanics/materials:** elastic/inelastic collision velocities are special outcomes of momentum/energy conservation under different collision assumptions; beam deflection is a boundary-condition-specific Euler–Bernoulli solution.

These are family-level flags, not automatic exclusions. A distinct physical mechanism can survive even when it shares a broad mathematical operator or parent theory. The catalogue policy must decide whether equivalence is assessed on the complete equation, the governing model, or a derived observable.

## Row-by-row static screening

| Candidate row | Initial disposition | Main issue before it can become a proposed record |
|---|---|---|
| `pendulum_period` | Hold | Small-angle simple-pendulum approximation; period depends on length and local gravity; finite-amplitude correction excluded from this formula. |
| `kepler_period` | Family overlap / hold | Derived from Newtonian inverse-square gravity for a two-body orbit; current expression hard-codes G and omits total-mass/barycentric convention. |
| `gravity_field` | Hold | Inverse-square point/spherically symmetric mass field; source, test location, units and validity outside extended bodies required. |
| `grav_potential_energy` | Family overlap / hold | Same Newtonian gravitation family as field and orbital expressions; sign/reference convention and point-mass assumptions required. |
| `projectile_range` | Family overlap / hold | Ideal projectile, negligible drag, equal launch/landing elevation; derived trajectory observable. |
| `projectile_height` | Family overlap / hold | Maximum-height observable from same ideal projectile trajectory; not an independent family from range. |
| `displacement` | Family overlap / hold | Constant-acceleration kinematics; vector/scalar sign convention and constant acceleration required. |
| `final_speed` | Family overlap / hold | Energy/kinematic rearrangement for constant acceleration; requires nonnegative radicand and signed acceleration/displacement convention. |
| `centripetal_accel` | Hold | Uniform circular-motion relation; speed/radius definitions and uniform-speed assumption. |
| `centripetal_force` | Derived output / overlap | Exactly mass times centripetal acceleration; do not count separately. |
| `damped_oscillation` | Hold / source repair | Underdamped free response only; damping convention, natural frequency, initial conditions and dimensional definitions missing. |
| `driven_resonance_amp` | Hold / source repair | Steady-state forced oscillator amplitude; denominator requires a specified damping convention and angular-frequency units. |
| `doppler` | Hold / incomplete | Moving source / stationary observer one-dimensional classical form only; sign convention and observer/source motion cases omitted. |
| `sound_level_db` | Hold / repair | Sound intensity level should use (10\log_{10}(I/I_0)); formula is equivalent only if reference intensity is exactly 10^-12 W m^-2 and intensity is positive. |
| `parallel_resistors` | Hold / possible low novelty | Equivalent resistance identity for two ideal resistors; basic network reduction, not a general physical law. |
| `rc_charge` | Family overlap / hold | First-order RC step response; linked to discharge and one linear circuit ODE. |
| `rc_discharge` | Family overlap / hold | Complementary initial-value response of same RC model; not separate from charge response. |
| `lc_frequency` | Hold / source repair | Ideal undamped LC natural frequency; parasitic resistance and component definitions omitted. |
| `rlc_impedance` | Hold / repair | Series-RLC impedance magnitude; topology and angular frequency required; expression is not general for arbitrary circuits. |
| `ac_power` | Hold / repair | Appears to be resistor real power in a series impedance circuit; voltage must be RMS and X/topology convention stated. |
| `faraday_emf` | Hold / repair | Sinusoidal rotating-coil generator result; orientation, peak vs instantaneous EMF and flux convention required. |
| `lens_maker` | Hold / repair | Thin lens in air form; sign convention, lens shape, refractive index relative to surrounding medium and paraxial/thin-lens assumptions missing. |
| `fresnel_reflectance` | Hold / repair | Normal-incidence intensity reflectance only; oblique s/p polarization and complex refractive indices omitted. |
| `brewster_angle` | Hold / repair | For incidence from medium 1 to 2, angle is arctan(n2/n1); assumes lossless dielectric and p-polarized zero reflection. |
| `wien_law` | Derived consequence / overlap | Wien displacement law is an extremum of Planck spectrum; not independent if Planck family counted. |
| `stefan_boltzmann` | Derived consequence / overlap | Integrated blackbody exitance; requires emissivity for real surfaces and absolute temperature. Derived from Planck spectrum. |
| `rayleigh_jeans` | Limiting case / overlap | Long-wavelength/high-temperature limit of Planck law; spectral variable/frequency-vs-wavelength convention must be fixed. |
| `photoelectric_ke` | Hold / repair | Einstein photoelectric relation; requires electron charge/work-function units consistent with photon energy and threshold condition; formula may return negative values below threshold. |
| `bohr_levels` | Family overlap / repair | Hydrogenic bound-state energy with fixed 13.6 eV; missing nuclear charge/reduced mass and energy unit annotation. |
| `bohr_radius_n` | Family overlap / repair | Bohr-model orbit radius; linked to same hydrogenic model as energy levels; assumes hydrogen and fixed Bohr radius. |
| `particle_in_box` | Hold / repair | 1D infinite square well energy; hbar constant hard-coded, but boundary conditions, dimensionality and mass/energy units need explicit declaration. |
| `relativistic_ke` | Hold / repair | Relativistic kinetic energy written in momentum form; hard-coded c and rest mass; verify numerical stability and unit convention. |
| `mass_energy` | Hold / overlap | Rest energy E=mc²; fundamental relation but overlaps relativistic energy family and may be too elementary/identity-like for the benchmark. |
| `radioactive_decay` | Family overlap / hold | Exponential decay with half-life parameterization; half-life and decay-constant forms are equivalent parameterizations. |
| `decay_activity` | Derived observable / overlap | Activity is λN(t), a derived rate from the same exponential-decay state; do not count separately. |
| `thermal_expansion` | Hold / repair | Linear expansion approximation for small temperature changes; coefficient and reference temperature/material range needed. |
| `heat_conduction` | Hold / repair | One-dimensional steady slab Fourier conduction; `dT` and `d` are finite differences, not local derivatives; boundary and constant-k assumptions. |
| `newton_cooling` | Hold / repair | Lumped-capacitance exponential cooling; heat-transfer coefficient/capacity folded into k; requires Biot-number validity and constant ambient temperature. |
| `adiabatic_pressure` | Hold / repair | Reversible ideal-gas adiabatic relation with fixed γ=1.4; only for diatomic-like gas under specified temperature range; variable heat capacities ignored. |
| `isothermal_work` | Hold / repair | Reversible ideal-gas work; sign convention and volume ratio must be positive; not generic irreversible work. |
| `entropy_expansion` | Family overlap / repair | Ideal-gas isothermal entropy change; same process family as isothermal work, but different state function; require reversible/equilibrium endpoints and volume ratio. |
| `boltzmann_factor` | Hold / repair | Relative canonical-state weight exp(-E/kBT), not normalized probability by itself; energy must be relative to stated reference. |
| `drag_force` | Hold / repair | Quadratic drag with empirical Cd; depends on geometry, Reynolds/Mach regime and reference area. |
| `terminal_velocity` | Derived balance / overlap | Solves weight = quadratic drag; only for vertical fall with buoyancy neglected and constant Cd; not independent from drag-force model. |
| `stokes_drag` | Hold / distinct regime | Linear Stokes drag on a sphere at low Reynolds number; specify no-slip continuum, spherical particle and low-Re regime. |
| `hydrostatic_pressure` | Hold / overlap | Static-fluid pressure at depth for constant density; related to Bernoulli static limit; absolute/gauge pressure convention. |
| `torricelli` | Special case / overlap | Ideal efflux speed derived from Bernoulli; negligible viscosity, large reservoir, same elevation reference. |
| `standing_wave` | Hold / repair | Harmonic frequencies for a string/open-closed resonator depend on boundary conditions; supplied formula assumes a particular mode convention not stated. |
| `elastic_collision_v1` | Derived special case / hold | 1D elastic collision with second body initially at rest; incomplete general collision solution and assumes conservation of kinetic energy. |
| `inelastic_final_v` | Derived special case / hold | Perfectly inelastic common velocity from momentum conservation; collision class and isolated-system assumption required. |
| `friction_work` | Hold / repair | Constant kinetic-friction work magnitude on a horizontal path; sign and normal force on incline/variable surfaces need treatment. |
| `incline_accel` | Hold / repair | Block sliding down incline with kinetic friction; direction/sign and condition for motion must be specified. |
| `beam_deflection` | Hold / repair | Cantilever end-load Euler–Bernoulli deflection; geometry, boundary conditions, small-deflection/linear-elastic assumptions and I units required. |
| `hall_voltage` | Hold / repair | Hall voltage for rectangular conductor; n is carrier number density and t thickness; sign/charge convention and carrier type missing. |
| `skin_depth` | Hold / repair | Good-conductor, nonmagnetic/linear material convention; angular-frequency vs frequency factor and permeability convention must be explicit. |
| `wire_force` | Hold / repair | Magnetic force on straight current segment; angle is between current direction and B; vector direction/sign omitted. |
| `matter_wave_ke` | Family overlap / repair | Nonrelativistic kinetic energy using de Broglie wavelength; derived from p=h/λ, linked to quantum wave mechanics; hard-coded h. |
| `malus_law` | Hold / repair | Ideal linear polarizer intensity law; angle between incident polarization and transmission axis; unpolarized input needs separate treatment. |
| `double_slit_intensity` | Hold / repair | Ideal equal coherent slits under far-field/small-angle approximation; finite slit envelope and phase/path geometry omitted. |
| `single_slit_intensity` | Hold / repair | Single-slit Fraunhofer envelope; b must represent the half-phase variable; removable b=0 singularity needs stable sinc form. |
| `kinetic_pressure` | Hold / repair | Kinetic-theory pressure relation assumes isotropic equilibrium gas; n must be number density and v RMS speed; distinguish from ideal-gas law. |
| `gyro_precession` | Hold / repair | Steady gyroscopic precession Ω=Mgr/(Iω); torque geometry, fast-spin approximation and moment-of-inertia axis required. |
| `orbital_angular_momentum` | Family overlap / repair | Circular-orbit angular momentum under Newtonian gravity; shares Kepler/orbit/gravity assumptions; circular orbit and central mass convention. |
| `rocket_equation` | Hold / repair | Ideal Tsiolkovsky equation; constant exhaust speed, no gravity/drag and correct initial/final mass ordering. |
| `physical_pendulum` | Hold / repair | Small-angle physical-pendulum period; centre-of-mass distance and moment of inertia about pivot; overlaps pendulum oscillation family. |
| `traveling_wave` | Hold / repair | Generic harmonic travelling-wave solution; phase convention, units and 1D homogeneous nondispersive medium context. |
| `beats` | Family overlap / repair | Superposition identity for two nearby sinusoidal frequencies; beat envelope is derived from wave superposition, not independent governing law. |
| `string_wave_energy` | Hold / repair | Average power/energy transport for sinusoidal transverse string wave; formula should be checked against peak/RMS and angular-frequency convention. |
| `sound_intensity` | Hold / repair | Plane progressive sinusoidal sound-wave intensity; pressure/displacement amplitude convention and medium density/sound speed units needed. |
| `magnetic_moment_energy` | Hold / repair | Dipole potential energy in uniform magnetic field; m must be magnetic dipole moment, not mass; symbol ambiguity and vector convention. |
| `coax_capacitance` | Hold / repair | Coaxial capacitor capacitance; formula uses vacuum permittivity; requires long coaxial geometry, negligible fringing and radii b>a. |
| `solenoid_energy` | Hold / repair | Magnetic energy from ideal solenoid inductance; n is turns per length, A cross-section, l length; permeability hard-coded as μ0. |
| `poynting_flux` | Hold / repair | Plane-wave average intensity in vacuum inferred from E-field amplitude; peak vs RMS convention and vacuum impedance required. |
| `tidal_acceleration` | Hold / repair | First-order differential acceleration across separation d in point-mass field; orientation/radial approximation and sign omitted. |
| `synchrotron_power` | Hold / reject current transcription | Numerical prefactor and units are unexplained; classical relativistic synchrotron power depends on charge, mass, Lorentz factor and field; current E²B² sketch is not a traceable general formula. |

## Source and domain research

The OpenStax projectile-motion chapter explicitly assumes negligible air resistance and separates horizontal/vertical motion under constant gravitational acceleration; its listed kinematic relations show why the two projectile outputs and constant-acceleration rows must be treated as a linked model family ([OpenStax §5.3](https://openstax.org/books/physics/pages/5-3-projectile-motion)). OpenStax also states that quadratic drag depends on empirical drag coefficient and that the terminal-speed formula is obtained by balancing weight and drag; it distinguishes Stokes' linear drag for small/slow objects ([OpenStax University Physics Vol. 1 §6.4](https://openstax.org/books/university-physics-volume-1/pages/6-4-drag-force-and-terminal-speed)). Its Bernoulli derivation assumes incompressible, frictionless flow along a streamline, with hydrostatics as the zero-velocity limit ([OpenStax University Physics Vol. 1 §14.6](https://openstax.org/books/university-physics-volume-1/pages/14-6-bernoullis-equation)). These references substantiate assumptions and derivation relationships; they do not establish acceptance of any author-pool row.

The existing source register has 25 Physics source records. That is a source-discovery count, not 25 accepted equations. Existing source leads include Planck/blackbody, thin lens, Schrödinger, Poiseuille, Navier–Stokes/Stokes, Euler/Timoshenko, and OpenStax heat-transfer material. They still require exact equation/page transcription, scope, and structural-family review.

## Cross-domain implications

- Newtonian inverse-square gravity and kinetic-energy expressions are explicit Core-15 exclusion risks; verify the frozen exclusion registry before drafting any related Physics record.
- Fourier heat conduction, electromagnetic constitutive laws and transport analogues require the same cross-domain operator comparison already raised for Fick flux.
- RC transients and first-order exponential kinetics share a broad mathematical form; whether physical mechanism is sufficient to distinguish domains must be decided by the global policy, not ad hoc per-domain.
- Planck/Wien/Stefan/Rayleigh–Jeans are a particularly clear derivation/limit family.
- Bio hemodynamics and Physics fluid mechanics share Poiseuille/Navier–Stokes parentage; source-domain labels do not create independent structure.

## Required policy decisions before acceptance

1. Define the unit of comparison: complete closed-form equation, governing ODE/PDE/system, or derived observable. Apply it consistently.
2. Specify whether a distinct physical mechanism can qualify when the normalized scalar function is the same (for example RC exponential vs first-order chemical kinetics).
3. Decide how special solutions of a broader governing system are treated (for example Poiseuille from Navier–Stokes; Torricelli from Bernoulli).
4. Decide whether PDEs, vector systems, eigenproblems and coupled systems are eligible as single benchmark units. Never split their components into pseudo-independent scalar equations.
5. Require SI dimensional analysis, named constants, sign conventions, assumptions, physical input constraints and train/extrapolation ranges derived from a cited regime—not generic multiples of upper bounds.
6. Resolve all Core-15 exclusions and cross-domain normalized-operator overlaps before counting.

**Outcome:** all 75 Physics author-pool rows are screened as discovery leads. No row is accepted. Several may later seed proposed records after exact-source reconstruction; the generic pool expressions/ranges must not be copied into the formal catalogue.



## Source-register expansion addendum (2026-11-11)

After this row-level audit, the Physics source register was expanded from 25 to 43 candidate-reference records (+18), and the consolidated bibliography received corresponding entries 123–140. These section-level OpenStax leads cover collision mechanics, variable-mass rocket propulsion, Kepler orbits, pendulums, forced oscillations, standing waves, Doppler shift, sound intensity, capacitance, RC circuits, Faraday induction, AC resonance, photoelectric effect, Compton scattering, Bohr hydrogen, de Broglie matter waves, the infinite square well and Young double-slit interference. The new references improve traceability and source coverage; they do not validate or accept any author-pool row and do not add 18 equation entries. Section URLs were checked and corrected against official OpenStax pages where needed.
