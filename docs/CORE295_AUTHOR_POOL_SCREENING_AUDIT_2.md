# Core-295 author_pool.py screening audit 2

**Status:** screening-only; no candidate accepted or imported into the formal catalogue.  
**Input:** user-supplied `author_pool.py`, statically parsed on 2026-11-11; the module was not imported or executed.  
**Scope:** all 54 Chemistry, 59 Biology and 75 Physics rows (188 candidates). This is a first-pass scientific/structural screen, not full source verification or validation of numerical generators.

## Provenance and disposition meanings

The source file itself says the equations were assistant-written from standard textbook/protocol-math forms, were not taken from a peer-reviewed benchmark, and have not been human-verified. Its `source` labels are generated strings, not traceable references. Every survivor needs an identifiable primary or authoritative source and equation location, variable definitions, units, assumptions, and defensible training/extrapolation ranges.

- **Reject as written:** a concrete transcription, dimensional, definition or schema defect must be corrected before reconsideration.
- **Family-blocked:** a rearrangement, derived quantity, component of a coupled model, or close member of a represented/excluded mathematical family. It does not count separately unless the structural-equivalence policy is explicitly revised.
- **Hold:** potentially usable form, but source, scope, assumptions, units, parameter constraints or ranges remain unresolved. Hold is not acceptance.

## Inventory

| Domain | Rows screened | Target | Difference |
|---|---:|---:|---:|
| Chemistry | 54 | 59 | -5 |
| Biology | 59 | 59 | 0 |
| Physics | 75 | 59 | +16 |
| **Total** | **188** | **177** | **+11** |

The 177 is the combined target for these three domains. Physics surplus cannot compensate for a Chemistry or other domain shortfall.

## Chemistry — 54 candidates

| First-pass disposition | Candidate IDs (suffix after `chemistry__`) |
|---|---|
| Reject as written | `fick_flux`, `polymer_Mn`, `enzyme_free_energy` |
| Family-blocked | `half_life_first`, `half_life_second`, `half_life_zero`, `weak_acid_H`, `gibbs_energy`, `K_from_dG`, `gas_density`, `combined_gas`, `dilution`, `arrhenius_two_point`, `hess_sum`, `diffusion_time`, `compressibility`, `langmuir_two_site` |
| Hold | `first_order_conc`, `second_order_conc`, `zero_order_conc`, `eyring_rate`, `vant_hoff_K`, `clausius_clapeyron`, `osmotic_pressure`, `raoult_pressure`, `boiling_elevation`, `pH_from_H`, `weak_acid_exact`, `ionic_strength`, `debye_huckel`, `gibbs_from_K`, `faraday_electrolysis`, `mole_fraction`, `transmittance`, `collision_theory_rate`, `langmuir_coverage`, `freundlich_uptake`, `calorimetry_mix`, `percent_composition`, `stokes_einstein`, `kohlrausch`, `antoine_vapor`, `vdw_pressure`, `virial_Z`, `solubility_cuberoot`, `consecutive_rxn_B`, `temp_jump_relax`, `catalytic_rate_ratio`, `activity_coeff_davies`, `buffer_capacity`, `chain_length_kinetic`, `viscosity_Andrade`, `heat_of_mixing_regular`, `band_gap_temp` |

**Principal findings**

1. First-, second- and zero-order concentration laws are distinct kinetic orders; their half-life formulas are derived outputs, not extra independent equations. Collision-theory and Arrhenius forms need source-specific prefactor conventions.
2. The exact weak-acid solution and square-root approximation belong to one equilibrium family. Single- and two-site Langmuir forms are one adsorption family. `enzyme_free_energy` has a likely sign reversal if `Kd` means dissociation constant: binding ΔG° is conventionally (RT\ln K_d) for dimensionless (K_d), not (-RT\ln K_d).
3. `gibbs_from_K` and `K_from_dG` are inverse forms of one relation. Mole fraction, dilution, compressibility, Hess summation and percentage composition are definitions/bookkeeping, not strong independent benchmark equations.
4. `fick_flux` uses `dx` but declares `x`. Its scalar linear-gradient structure also overlaps Fourier heat flux and Ohmic current density under the cross-domain policy. `diffusion_time` is a derived Brownian-diffusion relation.
5. Antoine, Andrade, Davies, Kohlrausch, Varshni, Freundlich and regular-solution expressions require material/electrolyte/solvent-specific constants, units and valid fit ranges. The van der Waals constants are not universal; virial truncation needs a validity range.
6. `solubility_cuberoot` assumes a particular 1:2 or 2:1 salt stoichiometry; `consecutive_rxn_B` omits the equal-rate limiting case; `catalytic_rate_ratio` assumes equal pre-exponential factors; and the polymer chain-length expression needs derivation for a named termination model.

## Biology — 59 candidates

| First-pass disposition | Candidate IDs (suffix after `biology__`) |
|---|---|
| Reject as written | `clearance_auc` |
| Family-blocked | `competitive_inhibition`, `noncompetitive_inhibition`, `uncompetitive_inhibition`, `substrate_inhibition`, `lineweaver_burk`, `monod_growth`, `holling_type2`, `holling_type3`, `emax_model`, `receptor_occupancy`, `scatchard_bound`, `hill_cooperativity_n2`, `lotka_volterra_pred`, `fick_membrane_flux`, `oral_absorption_pk`, `epidemic_growth`, `tumor_gompertz_growth`, `cell_cycle_doubling`, `light_attenuation`, `blood_flow_resistance`, `wall_shear_stress` |
| Hold | `exponential_growth`, `gompertz`, `logistic_solution`, `lotka_volterra_prey`, `beverton_holt`, `ricker_map`, `allee_growth`, `sir_incidence`, `q10_rate`, `heart_rate_scaling`, `metabolic_theory`, `von_bertalanffy`, `weight_length`, `nernst_potential`, `goldman_potential`, `murray_branching`, `laplace_wall_stress`, `hemoglobin_saturation`, `one_compartment_pk`, `iv_infusion_pk`, `hardy_weinberg_het`, `selection_allele_freq`, `heritability`, `lincoln_petersen`, `shannon_two`, `simpson_diversity`, `species_area`, `transpiration`, `photosynthesis_nonrect`, `cable_voltage_decay`, `bacterial_kill`, `stokes_sedimentation`, `gene_expression_ss`, `toggle_switch_steady`, `mrna_protein_ss`, `allometric_brain`, `bone_remodel` |

**Principal findings**

1. Competitive/noncompetitive/uncompetitive inhibition, substrate inhibition, Lineweaver–Burk, Monod, Holling II, Holling III, Emax, receptor occupancy and ligand-binding equations are related enzyme/saturation/binding families. The Core-15 Michaelis–Menten exclusion must be applied at family level, not evaded by changing application labels.
2. Exponential and epidemic early-phase growth overlap; tumor Gompertz is not a second Gompertz family. Logistic solution is a closed-form solution of the logistic growth ODE. Cell-cycle doubling time is derived from exponential growth.
3. Lotka–Volterra prey and predator expressions are components of one coupled ODE system; SIR incidence alone is not a complete SIR model; the toggle-switch expression is only one steady-state branch, not the coupled bistable system.
4. `clearance_auc` is mislabeled: (F D/CL) is AUC, not clearance. Oral absorption, IV bolus and infusion belong to related one-compartment PK families; the oral expression also needs a bioavailability convention.
5. Fick membrane flux shares a linear-gradient transport structure; blood-flow resistance and wall shear derive from the same Poiseuille family. Light attenuation also has a close structural relation to Beer–Lambert transmittance.
6. Shannon and Simpson candidates are restricted to two or three categories and require probabilities on a simplex. Hardy–Weinberg and selection models require allele-frequency and fitness constraints.
7. Heart-rate, brain-mass, species-area, weight-length, Q10 and metabolic-scaling coefficients are species/taxon/unit dependent. Source populations and calibration ranges are missing. Nernst/Goldman constants are temperature-specific approximations; the Goldman form here omits anions.

## Physics — 75 candidates

| First-pass disposition | Candidate IDs (suffix after `physics__`) |
|---|---|
| Reject as written | `driven_resonance_amp`, `elastic_collision_v1`, `string_wave_energy` |
| Family-blocked | `projectile_range`, `projectile_height`, `centripetal_accel`, `centripetal_force`, `displacement`, `final_speed`, `gravity_field`, `grav_potential_energy`, `rc_charge`, `rc_discharge`, `lc_frequency`, `radioactive_decay`, `decay_activity`, `pendulum_period`, `physical_pendulum` |
| Hold | `kepler_period`, `damped_oscillation`, `doppler`, `sound_level_db`, `parallel_resistors`, `rlc_impedance`, `ac_power`, `faraday_emf`, `lens_maker`, `fresnel_reflectance`, `brewster_angle`, `wien_law`, `stefan_boltzmann`, `rayleigh_jeans`, `photoelectric_ke`, `bohr_levels`, `bohr_radius_n`, `particle_in_box`, `relativistic_ke`, `mass_energy`, `thermal_expansion`, `heat_conduction`, `newton_cooling`, `adiabatic_pressure`, `isothermal_work`, `entropy_expansion`, `boltzmann_factor`, `drag_force`, `terminal_velocity`, `stokes_drag`, `hydrostatic_pressure`, `torricelli`, `standing_wave`, `inelastic_final_v`, `friction_work`, `incline_accel`, `beam_deflection`, `hall_voltage`, `skin_depth`, `wire_force`, `matter_wave_ke`, `malus_law`, `double_slit_intensity`, `single_slit_intensity`, `kinetic_pressure`, `gyro_precession`, `orbital_angular_momentum`, `rocket_equation`, `traveling_wave`, `beats`, `sound_intensity`, `magnetic_moment_energy`, `coax_capacitance`, `solenoid_energy`, `poynting_flux`, `tidal_acceleration`, `synchrotron_power` |

**Principal findings**

1. Projectile range/height, constant-acceleration displacement/final speed, centripetal acceleration/force, gravity field/potential, and simple/physical pendulum formulas require family clustering. Derived force/energy/observable forms do not automatically create independent equations.
2. `driven_resonance_amp` appears dimensionally incomplete: the force numerator needs division by mass unless the symbol denotes force per unit mass. `damped_oscillation` needs a clear damped-frequency definition and underdamped-regime constraint. RC charge/discharge are paired responses of one first-order circuit.
3. `elastic_collision_v1` omits the second body's initial-velocity term unless that body is initially at rest. `string_wave_energy` has units of power, not energy. `kinetic_pressure` requires `n` to mean number density, not particle count.
4. Heat conduction has its sign suppressed and shares the scalar linear-gradient structure flagged for Fick flux. Cooling, ideal-gas expansion, isothermal work, entropy change and Boltzmann factors need explicit assumptions and units.
5. Lens-maker radii need a stated sign convention. Fresnel reflectance is normal-incidence only. Rayleigh–Jeans is spectral radiance per wavelength, not spectral exitance. Single-slit variable `b` must be defined as the dimensionless phase argument.
6. Stokes drag/settling require low Reynolds number; quadratic drag applies in a different regime; terminal velocity omits buoyancy. Poiseuille, beam and elastic formulas depend on idealized geometry and boundary conditions.
7. Synchrotron coefficient and variables are not interpretable without particle type, energy units, magnetic-field units and pitch-angle convention. Fixed numerical constants throughout the pool need a versioned constants source and unit audit.

## Selected authoritative source checks

These checks support selected findings; they do not verify all 188 equations.

- OpenStax *Chemistry 2e*, integrated rate laws: first-order concentration-time equation and conditional nature of zero-order kinetics: https://openstax.org/books/chemistry-2e/pages/12-4-integrated-rate-laws
- IUPAC Gold Book, transition-state theory: Eyring prefactor (k_B T/h), activation Gibbs energy and transmission coefficient: https://goldbook.iupac.org/terms/view/T06470
- IUPAC Gold Book, Marcus equation: Eyring-prefactor formulation and Marcus activation barrier: https://goldbook.iupac.org/terms/view/M03702
- OpenStax *Concepts of Biology*, population growth and regulation: exponential/logistic models and simplifying assumptions: https://openstax.org/books/concepts-biology/pages/19-2-population-growth-and-regulation
- OpenStax *Biology 2e*, environmental limits to population growth: logistic differential equation and carrying-capacity interpretation: https://openstax.org/books/biology-2e/pages/45-3-environmental-limits-to-population-growth
- Patlak (1960), referencing Goldman (1943), on assumptions behind the Goldman diffusion-potential equation: https://www.nature.com/articles/188944b0
- OpenStax *University Physics Volume 2*, RLC series circuits: differential equation and underdamped solution: https://openstax.org/books/university-physics-volume-2/pages/14-6-rlc-series-circuits
- NIST CODATA 2022 recommended constants: current values/units for (G), (h), (hbar), (k_B) and related constants: https://www.physics.nist.gov/cuu/pdf/wall_2022.pdf

## Static checks performed and limitations

- Parsed the source using Python AST; did not import or execute `author_pool.py`.
- Confirmed 54 Chemistry, 59 Biology and 75 Physics rows.
- Compared expression identifier names with declared training-range keys: the only mismatch among these 188 rows is `chemistry__fick_flux` (`dx` in expression, `x` in declared ranges).
- This name-set check does not validate formula correctness, dimensions, units, constraints, source attribution or generator behavior.
- No candidate was promoted; no equation was imported; no source record was reclassified.
- No experiments, solvers, validators, workflows, paid compute or live protocol/API calls were run.

## Recommended next actions

1. Settle the catalogue-wide structural-equivalence rule, including cross-domain constitutive-law overlaps and whether different governing mechanisms may share the same algebraic form.
2. Apply Core-15 exclusions at mathematical-family level, especially Michaelis–Menten/Hill saturation and derived observables.
3. Correct defects only after source-level verification: `fick_flux`, `clearance_auc`, `driven_resonance_amp`, `elastic_collision_v1`, `string_wave_energy`, and `enzyme_free_energy`.
4. Pin source/equation location, scope, variables, units, assumptions, material/species identity, and defensible training/extrapolation ranges for every retained candidate.
5. Do not fill Chemistry's five-entry shortfall by promoting derived identities, cosmetic variants or untraceable empirical fits. Expand source discovery instead.
6. Preserve the 299-row file as a disclosed discovery artefact; do not describe it as a benchmark or validated equation set.

**Formal catalogue status remains unchanged:** 128 candidate source records, 19 proposed equation records, 0 accepted equation records; sampling frame unfrozen. The 295 target and 59-per-domain requirement remain unchanged.
