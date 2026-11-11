# Core-295 author_pool.py audit 7 — Chemistry and Biology

**Status:** static source-code and scientific-structure screen of the uploaded `author_pool(1).py`; no code execution, data generation, solver run, validator run, or experiment. Every row remains a discovery candidate only. The uploaded file itself declares that its formulas were assistant-authored from textbook/protocol forms, are not taken from a peer-reviewed benchmark, and have not been human-verified.

## Scope and count

This review covers the complete Chemistry and Biology blocks in the uploaded file: 54 Chemistry rows and 59 Biology rows. It does not modify the formal catalogue's accepted count or imply that any row qualifies toward the 59-per-domain target.

## Chemistry findings

### 1. Reaction kinetics and derived summaries

Rows: `first_order_conc`, `second_order_conc`, `zero_order_conc`, `half_life_first`, `half_life_second`, `half_life_zero`, `consecutive_rxn_B`, `temp_jump_relax`.

- The three concentration-time laws and three half-life expressions are paired integrated-rate/derived-summary families, not six structurally independent equations. Half-lives are algebraic consequences of the corresponding kinetic laws.
- The zero-order concentration law becomes negative when (t>A_0/k); the far extrapolation default does not encode depletion or stop the trajectory at exhaustion.
- The second-order expression assumes a particular single-reactant second-order rate law and concentration units consistent with (k). The reaction stoichiometry and kinetic order must be explicit.
- The consecutive-reaction intermediate formula is valid only with the correct reaction scheme and (k_1\ne k_2); the expression is numerically ill-conditioned near equality and requires the limiting form there.
- `temp_jump_relax` is not source-identified and lacks a state/forcing definition. It cannot be accepted as a generic relaxation law without a physical derivation and units.

### 2. Activated rates and temperature dependence

Rows: `eyring_rate`, `vant_hoff_K`, `clausius_clapeyron`, `collision_theory_rate`, `arrhenius_two_point`, `catalytic_rate_ratio`, `viscosity_Andrade`.

- `eyring_rate` uses a fixed numerical prefactor (2.084\times10^{10}T), which is approximately (k_B T/h) in s⁻¹ K⁻¹ units, but the equation omits transmission coefficient and standard-state/activation-free-energy conventions. Its `dG` must be molar activation Gibbs energy in J/mol, not an unspecified free energy.
- `arrhenius_two_point` is an algebraic rearrangement of the Arrhenius law; do not count it separately from an Arrhenius rate equation.
- `collision_theory_rate` has no source or molecular collision model defining its prefactor (A), collision cross-section, orientation/steric factor or units.
- `catalytic_rate_ratio` is a ratio derived from Arrhenius-type exponential rates under equal prefactor assumptions; it is not a distinct kinetic mechanism without those assumptions.
- van ’t Hoff equilibrium-constant and Clausius–Clapeyron vapour-pressure equations share the same reciprocal-temperature exponential form. They describe different observables and assumptions, but the normalized functional form is closely related; the structural distinctness policy must decide whether this counts as one family.
- Andrade viscosity is empirical and substance/range-specific; no material, unit convention or fit provenance is supplied.

### 3. Equilibrium, acid–base, solution and electrochemistry

Rows: `gas_density`, `osmotic_pressure`, `raoult_pressure`, `boiling_elevation`, `pH_from_H`, `weak_acid_H`, `weak_acid_exact`, `ionic_strength`, `debye_huckel`, `gibbs_energy`, `gibbs_from_K`, `K_from_dG`, `faraday_electrolysis`, `combined_gas`, `mole_fraction`, `dilution`, `transmittance`, `activity_coeff_davies`, `buffer_capacity`, `solubility_cuberoot`.

- `weak_acid_H` is a small-dissociation approximation; `weak_acid_exact` is the corresponding quadratic solution. They are not independent acid-equilibrium families. The approximation needs a declared validity criterion, and the exact form needs the assumptions of a monoprotic weak acid with negligible water autoionization and appropriate concentration/activity convention.
- `gibbs_from_K` and `K_from_dG` are inverse rearrangements of \(\Delta G^\circ=-RT\ln K\), not separate equations. `gibbs_energy` is the state-function identity \(G=H-TS\), with state/standard-state and unit consistency required.
- `debye_huckel` gives a limiting-law activity coefficient expression only when interpreted as \(\log_{10}\gamma=-A z^2\sqrt I\); the file's expression is missing the solvent/temperature-dependent Debye–Hückel constant and does not state the log base. `activity_coeff_davies` is a distinct extended empirical approximation but shares the same activity-coefficient family and needs an ionic-strength validity limit.
- `buffer_capacity` is the monoprotic ideal-solution buffer-capacity expression only with consistent total concentration, acid dissociation constant and hydrogen-ion activity/concentration; the independent ranges are not a complete buffer preparation model.
- `solubility_cuberoot` assumes a 1:1 salt of type AB with (K_{sp}=s^2) would require a square root, whereas a 1:1:1 stoichiometry is not represented by this cube-root formula. The stated expression ((K_{sp}/4)^{1/3}) corresponds to a specific 1:2 salt stoichiometry (e.g. AB₂) only under ideal concentration assumptions; name and stoichiometry must be explicit.
- `raoult_pressure` is the partial pressure of one volatile component in an ideal solution, not total vapour pressure; mixture composition and ideality must be specified.
- `boiling_elevation` requires solvent-specific (K_b), molality units and a dilute-solution approximation; (i) is not a free continuous factor.
- `pH_from_H` requires positive hydrogen-ion activity (not simply arbitrary concentration) and the log base is encoded indirectly by division by \(\ln 10\).
- `gas_density` is ideal-gas mass density only if (M) is molar mass in kg/mol and pressure, volume and temperature are SI.
- `osmotic_pressure` is van ’t Hoff's dilute-solution limit, not a general concentrated-electrolyte equation.
- `faraday_electrolysis` needs the electrode reaction, electron stoichiometry and molar-mass convention; (M) is molar mass and (n) is electron number, not arbitrary dimensionless parameters.
- `combined_gas` is a combined gas-law rearrangement, while `mole_fraction` and `dilution` are elementary accounting identities. These are weak candidates for a structurally rich equation population and require an explicit policy on identities/rearrangements.
- `transmittance` is decadic Beer–Lambert only when `eps` is molar decadic absorptivity and (l,c) use compatible units. The candidate does not encode wavelength, species or solution conditions.
- `ionic_strength` is the standard concentration-weighted charge-square sum, but requires a complete ionic composition, consistent molarity and electroneutrality.
- `percent_composition` and `polymer_Mn` are accounting definitions; polymer number-average molecular weight expression needs a defined number distribution and species indexing.
- `calorimetry_mix` assumes adiabatic mixing, no phase change/reaction and constant heat capacities; temperature units and heat-capacity units must agree.
- `hess_sum` is a sign-sensitive stoichiometric cycle identity; three enthalpies cannot be sampled independently without a reaction-cycle definition.

### 4. Adsorption, transport, fluids and material properties

Rows: `langmuir_coverage`, `langmuir_two_site`, `freundlich_uptake`, `fick_flux`, `stokes_einstein`, `diffusion_time`, `kohlrausch`, `antoine_vapor`, `vdw_pressure`, `compressibility`, `virial_Z`, `chain_length_kinetic`, `heat_of_mixing_regular`, `enzyme_free_energy`, `band_gap_temp`.

- `langmuir_coverage` and `langmuir_two_site` are one-site and summed two-site forms of the same adsorption-family mechanism. The two-site sum can exceed unity as written; it must represent separate site capacities or a properly normalized total coverage.
- `freundlich_uptake` is an empirical power-law isotherm; it has no saturation capacity and needs fitted material-specific parameters and concentration units.
- `fick_flux` has a concrete code defect: expression uses `dC/dx), but declared variables include `x), not `dx`. More importantly, the expression treats a gradient as a scalar variable rather than a field derivative; a generator must define a spatial profile or use a finite-difference stencil. It also shares a normalized linear-gradient constitutive operator with Fourier heat flux and Ohm current density; see Audit 2's cross-domain distinctness blocker.
- `diffusion_time` is a characteristic scaling (x^2/(2D)), not a general diffusion solution. Geometry and boundary conditions determine the coefficient.
- `stokes_einstein` requires hydrodynamic radius, dynamic viscosity and temperature, and is limited by continuum/hydrodynamic assumptions; molecular-scale or non-Newtonian cases need caution.
- `kohlrausch` is an empirical limiting law for strong-electrolyte molar conductivity, not generic conductivity at arbitrary concentration. Units and electrolyte valence/type are absent.
- `antoine_vapor` needs substance-specific coefficients and temperature/pressure unit conventions; its extrapolation cannot use generic coefficients or unrestricted temperature ranges.
- `vdw_pressure` has hard-coded (a=0.37), (b=0.04), and assumes a particular gas and unit system; the generic name is misleading. Its denominator must remain positive and the parameters must match a declared substance.
- `compressibility` is the definition of compressibility factor (Z) using the ideal-gas denominator; it is not an independent equation of state unless (P,V,n,T) come from a specified thermodynamic system.
- `virial_Z` is truncated at the second virial coefficient and its (B) units must be volume/mol; the far-range values can produce physically implausible (Z) without a declared gas and convergence range.
- `chain_length_kinetic` resembles a steady-state free-radical polymerization rate expression, but lacks the reaction scheme, rate-constant units and assumptions (termination mode, initiator efficiency, steady-state radical balance). The square-root initiator dependence is mechanism-specific.
- `heat_of_mixing_regular` is a regular-solution enthalpy-of-mixing term, not a complete free energy or phase-stability equation; (W), composition basis and sign convention require definition.
- `enzyme_free_energy` is not a well-defined standard free energy from (K_d) unless the dimensionless standard-state ratio (K_d/c^\circ) and sign convention are used. As written, logarithm of dimensional (K_d) is invalid.
- `band_gap_temp` resembles a Varshni relation, but source, material-specific coefficients, temperature range and energy units are absent.

## Biology findings

### 1. Enzyme kinetics, saturation, receptor binding and inhibition

Rows: `hill_cooperativity_n2`, `competitive_inhibition`, `noncompetitive_inhibition`, `uncompetitive_inhibition`, `substrate_inhibition`, `lineweaver_burk`, `monod_growth`, `holling_type2`, `holling_type3`, `emax_model`, `receptor_occupancy`, `scatchard_bound`, `hemoglobin_saturation`.

- `lineweaver_burk` is the reciprocal linearization of Michaelis–Menten kinetics, not a distinct nonlinear law. It is especially unsuitable for unweighted regression because reciprocal transformation magnifies low-substrate measurement error.
- `monod_growth`, `holling_type2`, `receptor_occupancy`, and the one-site `emax_model` share hyperbolic saturation forms after variable/parameter relabeling. They must be treated as a single structural family unless the policy explicitly recognizes distinct governing mechanisms despite algebraic equivalence.
- `hill_cooperativity_n2` is a Hill equation with fixed Hill coefficient 2; it belongs to the same Hill-family and should not be counted as a separate independent equation merely because the exponent is fixed.
- Competitive, noncompetitive, uncompetitive and substrate inhibition are distinct kinetic mechanisms, but their parameter definitions must follow the corresponding enzyme-binding mechanism; these expressions should be checked against the original steady-state derivations and not treated as generic response curves.
- `holling_type3` has the same general saturating rational family as Holling II but with a quadratic numerator/denominator; ecological interpretation and low-density facilitation assumptions must be explicit.
- `scatchard_bound` is a linear nonspecific-binding plus saturable-specific-binding decomposition, closely tied to receptor binding and Scatchard analysis; it is not an independent saturation family from the receptor occupancy component.
- `hemoglobin_saturation` is a Hill empirical approximation, with exponent 2.8 fixed; oxygen saturation depends on pH, CO₂, temperature and 2,3-BPG, so a fixed-(P_{50}) curve has a restricted context.

### 2. Population growth and ecological dynamics

Rows: `exponential_growth`, `gompertz`, `logistic_solution`, `lotka_volterra_prey`, `lotka_volterra_pred`, `beverton_holt`, `ricker_map`, `allee_growth`, `sir_incidence`, `epidemic_growth`, `species_area`.

- `exponential_growth` is the unconstrained early-growth solution and the low-density limit of multiple bounded-growth models; its scope must be explicit.
- `gompertz` and `logistic_solution` are different bounded-growth families, but are closed-form solutions of corresponding ODEs. Their parameterization, initial condition and time origin need consistent definitions.
- The two Lotka–Volterra rows are the two components of one coupled predator–prey ODE system, not two independent equations. Both must be generated jointly with shared state variables and parameters.
- `beverton_holt` and `ricker_map` are discrete-time population maps, not continuous-time growth-rate laws. Time step, density dependence, and population-generation convention must be stated.
- `allee_growth` is a continuous-time per-capita growth model with a threshold; the sampled (N) range must be checked relative to (A) and (K), and the equation's sign changes are part of its biology, not invalid numerical noise.
- `sir_incidence` is only the incidence term (eta SI/N), not a complete SIR system. The susceptible and infectious compartments must be dynamically coherent and the total population convention specified.
- `epidemic_growth` is the early exponential approximation to an epidemic compartment model with rate (eta-gamma); it is not independent from early-phase epidemic dynamics without a separate model contract.
- `species_area` is a fitted ecological scaling law with exponent fixed at 0.25; source, habitat/area units and calibration domain are missing.

### 3. Physiology, bioelectricity and biophysics

Rows: `q10_rate`, `heart_rate_scaling`, `metabolic_theory`, `von_bertalanffy`, `weight_length`, `nernst_potential`, `goldman_potential`, `fick_membrane_flux`, `murray_branching`, `laplace_wall_stress`, `photosynthesis_nonrect`, `cable_voltage_decay`, `light_attenuation`, `transpiration`, `stokes_sedimentation`, `blood_flow_resistance`, `wall_shear_stress`.

- `q10_rate`, `heart_rate_scaling`, `metabolic_theory`, `von_bertalanffy`, `weight_length`, `species_area) are empirical/allometric relationships; they need original study/source, taxon, organism size and units. They are not universal biological constants.
- `metabolic_theory` uses (k_B) in eV/K and activation energy in eV, but the numerical coefficient (B_0) and mass scaling require unit and taxonomic conventions.
- `nernst_potential` uses a fixed 0.0267 V coefficient, approximating (RT/F) near room temperature; it omits temperature dependence and uses (ln(C_o/C_i)) only for a specified ion valence and sign convention. Its concentrations should be activities.
- `goldman_potential` is a cation-only GHK-like zero-current potential approximation, omitting anion terms and temperature dependence; permeability and concentration units must be consistent. It is not a generic membrane potential equation.
- `fick_membrane_flux` is a permeability-times-concentration-difference relation; it is a membrane permeability model, distinct in parameterization from the bulk Fick gradient law but closely related by a membrane-thickness reduction. Need units for (P), concentration, flux and membrane thickness convention.
- `murray_branching` assumes an idealized minimum-work branching rule and equal exponent 3; branch radii and geometry must be correctly assigned.
- `laplace_wall_stress` is a thin-wall cylindrical relation (circumferential stress) only; the generic name “wall stress” obscures geometry and stress vs tension units.
- `photosynthesis_nonrect` is a non-rectangular hyperbola for light-response, with discriminant constraints and fitted parameters; source and output units absent. The discriminant must remain nonnegative.
- `cable_voltage_decay` is a steady/passive exponential spatial decay with length constant; it is not a full cable equation solution for arbitrary boundary conditions.
- `light_attenuation` is Beer–Lambert-like exponential attenuation, structurally overlapping the Chemistry transmittance/absorbance family.
- `transpiration` is a simplified conductance-times-vapour-pressure-deficit relation; units, stomatal conductance basis, leaf area and boundary-layer assumptions are absent.
- `stokes_sedimentation` requires low Reynolds number, spherical particles, Newtonian fluid and density contrast. The given radius/density/viscosity ranges need unit checks and a source.
- `blood_flow_resistance` is Poiseuille resistance, a special case of the same laminar tube-flow family as the Physics Hagen–Poiseuille candidate. `wall_shear_stress` is a derived quantity from the same velocity profile and flow law; do not count both as structurally independent without a declared rule.
- `weight_length` is a cubic special case of a general allometric power law, not a universal fish/organism relationship.

### 4. Pharmacokinetics, gene regulation and molecular processes

Rows: `one_compartment_pk`, `oral_absorption_pk`, `iv_infusion_pk`, `clearance_auc`, `bacterial_kill`, `tumor_gompertz_growth`, `gene_expression_ss`, `toggle_switch_steady`, `mrna_protein_ss`, `cell_cycle_doubling`, `allometric_brain`, `hardy_weinberg_het`, `selection_allele_freq`, `heritability`, `lincoln_petersen`, `shannon_two`, `simpson_diversity`, `bone_remodel`.

- The one-compartment IV bolus, oral first-order absorption and constant-rate infusion are related PK model solutions but represent different administration/input models. Require shared units, initial conditions, bioavailability, elimination/absorption assumptions and time basis.
- `clearance_auc` is a mass-balance identity under linear PK, not a separate dynamic PK equation.
- `bacterial_kill` is a concentration-dependent log-linear kill model with Hill/Emax-like concentration term; (C_{MIC}) is not automatically the effect-site concentration, and the parameter (k) units depend on exponent (n) and time.
- `tumor_gompertz_growth` is a Gompertz solution, closely related to the Gompertz population-growth row; it is not a new structural family by relabeling state as tumour volume.
- `gene_expression_ss`, `toggle_switch_steady` and `mrna_protein_ss` are steady-state reductions of gene-regulatory ODE systems. They omit network topology, degradation/transcription/translation assumptions and stability conditions; the toggle-switch row is not a full toggle-switch model.
- `cell_cycle_doubling` is a derived time scale from exponential growth, not independent of `exponential_growth`.
- `allometric_brain` is an empirical allometry with an exponential correction, lacking source, taxon, mass units and calibration range.
- `hardy_weinberg_het` is a derived genotype-frequency identity under random mating and biallelic assumptions. `selection_allele_freq` is a one-generation selection update; genotype fitness mapping and normalization must be explicit.
- `heritability` is narrow-sense variance ratio only if (V_A) and (V_E) refer to the appropriate additive genetic and residual/environmental components in a defined population. It is not a universal deterministic biological law.
- `lincoln_petersen` is the basic capture–recapture estimator; it is biased for small samples and assumes closed population, equal catchability and independent marks/recaptures. The Chapman correction is often preferable.
- `shannon_two` and `simpson_diversity` sample component probabilities independently in [0.1,0.5], so their sums can exceed 1. Inputs must be a simplex vector, not independent uniforms. The two-category Shannon expression is a restricted case of the general Shannon index; Simpson's index requires all species proportions and a declared convention (D, 1-D, or reciprocal).
- `bone_remodel` is not source-identified and has no clear state equation/observable definition; as written it is an exponentially decaying response to a fixed stimulus difference, not a general bone-remodelling model.

## Cross-domain structural families requiring explicit treatment

1. First-/second-/zero-order integrated concentration laws and their half-life summaries.
2. Arrhenius/Eyring/collision-theory rate families and derived two-point/ratio forms.
3. van ’t Hoff and Clausius–Clapeyron reciprocal-temperature exponential relations.
4. Acid dissociation exact/approximate solutions; equilibrium constant/free-energy inverse forms.
5. Langmuir/Hill–Langmuir/receptor occupancy/Monod/Holling-II/Emax hyperbolic saturation.
6. Fick bulk flux, membrane permeability flux and the related Fourier/Ohm constitutive-gradient operator.
7. Beer–Lambert transmittance and biological light attenuation.
8. Poiseuille tube resistance/flow and derived wall shear stress.
9. Exponential/Gompertz growth and their PK/tumour/allometric variants.
10. Hill-form oxygen saturation, enzyme cooperativity and other fixed-exponent saturation curves.
11. Coupled system components (Lotka–Volterra, SIR, PK/PD and gene-regulatory systems) must be treated as systems, not independently sampled scalar equations.

## Source and generator blockers common to both blocks

- Every row's `source` value is a generic placeholder such as `textbook:<name>`; this is not bibliographic provenance. The pool-level disclaimer confirms the equations were assistant-authored. Each candidate needs an exact source, edition/page/equation or versioned protocol locator, and a note distinguishing original formula from modern textbook rearrangement.
- The default extrapolation rule `(hi, 5*hi)` is not a scientific validity rule. It can violate positivity, bounded fractions, simplex constraints, phase domains, asymptotic assumptions, model discriminants, or denominator constraints.
- Scalar independent-uniform sampling is inappropriate for coupled dynamical systems, probability vectors, compositions, reaction stoichiometry, concentration-time curves and correlated physiological variables.
- Several formula parameters are dimensioned constants but are sampled without units; some expressions contain implicit hard-coded constants that only work under a particular unit system.
- Static finiteness checks do not establish scientific validity, physical admissibility, or statistical independence.
- The claim in the source file that no limiting cases/reparameterizations are included is contradicted by the derived half-life rows, reciprocal Arrhenius form, inverse Gibbs/equilibrium relations, Lineweaver–Burk transform, PK-derived summaries, tumour Gompertz vs Gompertz growth, and other family overlaps listed above.

## Disposition

**Do not import Chemistry or Biology rows wholesale. Accept none on the basis of this audit.** The file is a useful brainstorming inventory, but its raw row count substantially overstates the number of structurally independent, source-grounded, generator-ready equations. Candidate selection should proceed by mathematical family and source, with coupled systems represented by a declared independent unit. Preserve the formal catalogue's current acceptance state until each record passes its own primary-source, units, domain, generator and structural-equivalence review.

## Selected references for follow-up verification

- Receptor occupancy and Hill–Langmuir history: https://pmc.ncbi.nlm.nih.gov/articles/PMC7060363/
- Lotka–Volterra system history and structure: https://www.frontiersin.org/journals/microbiology/articles/10.3389/fmicb.2022.1037407/full
- Monod bacterial growth: https://doi.org/10.1002/jbmte.390010403
- Nernst and Goldman/constant-field derivation: https://rupress.org/jgp/article/149/10/911/43579/The-enduring-legacy-of-the-constant-field-equation
- Nernst equation history: https://doi.org/10.1021/bk-1989-0390.ch008
- De Buck et al. tumour PK/PD audit: https://doi.org/10.1111/bcp.12378
- Simeoni et al. tumour growth inhibition model: https://doi.org/10.1158/0008-5472.CAN-03-2524
