# Core-295 generator taxonomy and current catalogue triage

**Status:** design control; not an acceptance policy or execution authorization.  
**Branch:** `promotion/rerun-code-review`

## Why this contract is needed

The initial shared adapter treats every key in `variables` as an independently sampled input. That is not generally valid: scientific records commonly mix measured inputs, fixed physical parameters, dependent variables, dynamic states, discrete protocol settings, and coupled constraints. A formula string alone cannot identify those roles.

The catalogue must describe the mathematical object and the data-generation contract explicitly. A record is not executable merely because it has a scalar expression and numeric ranges.

## Required variable-role declaration

Every candidate record must complete `model_definition` with:

- `model_class`: one of the classes below;
- `independent_variables`: externally varied explanatory/forcing variables;
- `dependent_variables`: quantities computed by the model;
- `state_variables`: dynamic state vector (empty only for non-dynamic models);
- `fixed_parameters`: named parameters held fixed within a generated dataset or run;
- `constraints`: machine-readable constraints plus a human-readable rationale;
- `operator_structure`: concise description of the governing operator/system.

These role lists must be mutually consistent with the source equation and the `variables` dictionary. Do not duplicate a symbol in incompatible roles. Constants and protocol settings are not independent inputs merely because they appear in a formula.

## Generator model classes

| Class | Mathematical object | Generator requirements | Initial adapter support |
|---|---|---|---|
| `explicit_scalar` | One explicit scalar output from independent inputs and fixed parameters | Explicit input/parameter roles, units, valid ranges, constraints, deterministic sampler | Narrow shared adapter only when all its exact assumptions hold |
| `implicit_scalar` | Implicit relation or root-defined output | Equation residual, admissible root interval, uniqueness/branch policy, solver and tolerance contract | Unsupported |
| `coupled_algebraic_system` | Coupled equations or vector-valued algebraic state | Full system, state ordering, constraints, solution existence/branch policy | Unsupported |
| `ode_ivp` | Initial-value dynamical system | State vector, RHS, initial-condition distribution, integration method/tolerances, event and stability policy | Unsupported |
| `difference_system` | Discrete-time state recurrence/system | State vector, transition operator, initial states, time horizon, constraints | Unsupported |
| `stochastic_process` | Random process or stochastic differential/difference model | Probability law, random stream policy, path/time discretization, reproducibility and estimand | Unsupported |
| `protocol_simulation` | Contract/protocol or event-driven state machine | Pinned implementation/version, state transitions, integer/fixed-point semantics, environment and transaction/input generation | Unsupported |
| `matrix_operator` | Matrix/vector projection or operator | Dimension policy, matrix construction, state/input roles, spectral/positivity constraints | Unsupported |

The current shared adapter is limited to `explicit_scalar` with the exact method `catalogue_expression_v1`, seed policy `sha256_run_equation_v1`, parameter sampling `independent_uniform_over_declared_ranges`, and sampling semantics `all_declared_variables_are_independent_inputs`. That last semantics is only appropriate when every declared symbol really is an independently sampled feature. It is not a generic default and must not be used for records with fixed parameters, constraints, coupled variables, or protocol semantics.

A future explicit-scalar contract should separate `input_variables` from `fixed_parameters` and specify whether parameters are fixed per equation, sampled once per dataset, or sampled per observation. This distinction must be encoded and reviewed before implementation; do not infer it from variable names.

## Triage of the current 24 proposed records

This is a preliminary implementation-class triage based on the catalogue expressions and descriptions, not a scientific acceptance or source-verification decision.

| Candidate | Preliminary class | Main issue before generator design |
|---|---|---|
| CHEM-HENRY-001 | explicit_scalar | (P_g) is the varying input; (k_H) is ordinarily a gas/solvent/temperature-specific coefficient |
| CHEM-LANGMUIR-001 | explicit_scalar | (p) is input; (u_1) is an adsorption parameter; enforce positive denominator and physical coverage |
| CHEM-MARCUS-001 | explicit_scalar | Resolve collision-prefactor/source convention; (R) is a physical constant, while (Z,lambda) are parameters and (T,Delta G) are conditions |
| BIO-HILL-MUSCLE-001 | explicit_scalar | (P) is load input; (P_0,a,b) are preparation-specific parameters; enforce physical force domain |
| PHYS-POISEUILLE-001 | explicit_scalar | Pressure difference is input; geometry and viscosity are normally fixed parameters; enforce (p_2>p_1), positivity and laminar regime |
| PHYS-PLANCK-SPECTRUM-001 | explicit_scalar | (lambda,T) are inputs; (h,c,k_B) are constants, not sampled features |
| PHYS-THIN-LENS-001 | explicit_scalar | Object distance is input; focal length is a lens parameter; exclude singular/invalid geometry |
| AMM-BALANCER-WEIGHTED-001 | explicit_scalar / protocol_simulation boundary | Balances may vary; weights are pool configuration, constrained positive and normalized; actual invariant is protocol-defined |
| RISK-MORPHO-LIF-001 | protocol_simulation | LLTV is a discrete market configuration; validate against pinned market configuration rather than arbitrary continuous sampling |
| RISK-EULER-AUCTION-001 | explicit_scalar / protocol_simulation boundary | (C_{adj},L) are state/valuation inputs; (D_{max}) is a configured parameter; preserve protocol branch semantics |
| RISK-COMPOUND-BORROW-KINK-001 | explicit_scalar / protocol_simulation boundary | Utilization is input; kink and rate slopes are market parameters; enforce utilization and parameter bounds |
| AMM-DODO-PMM-BASE-SHORTAGE-001 | explicit_scalar / protocol_simulation boundary | Balance is state/input; (i,k,B_0) are pool parameters; enforce shortage branch and invariant constraints |
| CHEM-RAOULT-VAPOR-001 | explicit_scalar | (X_A) is input; (P_A^*) is a component/temperature-specific parameter |
| BIO-FICK-CARDIAC-OUTPUT-001 | explicit_scalar | Oxygen consumption and arterial/venous contents are measured inputs; enforce positive content difference |
| RISK-UNISWAP-V3-GEOMETRIC-TWAP-001 | protocol_simulation | Mean tick is integer protocol state; observation window, token direction, and fixed-point semantics matter |
| RISK-UNISWAP-V2-ARITHMETIC-TWAP-001 | protocol_simulation | Cumulative prices are paired observations; interval, token ordering and modular arithmetic must be represented |
| CHEM-FICK-FLUX-001 | explicit_scalar | Diffusion coefficient and concentration gradient have different roles; sign convention and geometry must be fixed |
| CHEM-BEER-LAMBERT-001 | explicit_scalar | Incident intensity, concentration and path length roles must be separated from fixed absorptivity; enforce nonnegative optical depth |
| BIO-TUMOR-TURNOVER-001 | ode_ivp | Expression is a state derivative, not a static scalar response; requires initial tumour state and integration contract |
| BIO-GOMPERTZ-1825-MORTALITY-001 | explicit_scalar | (mu) is the dependent output; (x) is age input and (a,q) are parameters; current expression/variable declaration needs reconciliation |
| BIO-VOLTERRA-1926-N-SPECIES-CONSERVATIVE-001 | coupled_algebraic_system / ode_ivp | Full coupled state system and antisymmetric interaction matrix; cannot flatten to one scalar equation |
| BIO-LESLIE-1945-AGE-STRUCTURED-MATRIX-001 | matrix_operator / difference_system | Vector recurrence with structured matrix; age classes and matrix dimensions must be explicit |
| BIO-FUJII-HOLLING-MACE-1986-GENERALIZED-ATTACK-001 | explicit_scalar | (N_0) is input, parameters fixed; source equation and attack-time/handling-time constraints need verification |
| CHEM-FRUMKIN-1967-INTERACTION-001 | implicit_scalar | Coverage is implicitly defined by the isotherm; requires branch/root policy and admissible coverage interval |

A slash indicates a boundary requiring source/model review, not permission to select whichever class is easiest to implement. In particular, protocol-derived equations should be classified according to whether the benchmark is evaluating a closed-form relation or the deployed protocol behavior.

## Readiness and acceptance rules

1. Preserve the original source model and complete governing system; do not reduce a dynamic or coupled model to a convenient scalar output without a documented derivation and review.
2. Separate inputs, fixed parameters, dependent variables, states, constants, and protocol configuration.
3. Declare constraints in the generator contract and enforce them during deterministic sample generation.
4. Declare parameter sampling scope: fixed per equation, sampled per dataset, or sampled per observation. State the distribution and seed derivation.
5. For dynamic systems, declare initial-condition and solver contracts; for protocol models, pin code/version/configuration and preserve integer/fixed-point behavior.
6. Unsupported classes remain pending and cannot pass the task planner by filling arbitrary strings or ranges.
7. Human source-page/code review, structural-equivalence review, source-family grouping and independent statistical-unit decisions remain separate acceptance gates.

## Catalogue annotation pass

The 24 current draft records have now been annotated with preliminary `model_definition` role partitions and matching `generator.model_class` labels. Current counts are 14 `explicit_scalar`, 6 `protocol_simulation`, 2 `ode_ivp`, 1 `matrix_operator`, and 1 `implicit_scalar`. These are triage labels, not completed generator implementations or scientific approvals. The annotations should be checked against primary sources and model definitions during candidate review.

The shared scalar adapter was tightened to reject any record that declares fixed parameters, physical constants, dependent variables, or states. It accepts only records where every declared symbol is explicitly an independent input and every such input has a range. Consequently, the 14 records labelled `explicit_scalar` are not automatically compatible with that adapter; most separate inputs from fixed parameters and need a more expressive generator contract. The current adapter must not be used as a shortcut to sample those parameters independently.

## Current status

The catalogue remains draft with 24 proposed records and a non-frozen sampling frame. No generator is marked ready, no equation is accepted, and the new role annotations do not verify equations, assign acceptance, or make any record executable. No tests, validators, scripts, generators, experiments, workflows, or live services were run to produce this document.


## Fixed-parameter scalar adapter extension

The restricted scalar conversion path now separates independent inputs from fixed parameters and physical constants. The catalogue carries exact numeric bindings in `fixed_parameter_values` and `physical_constant_values`; only independent inputs receive train/extrapolation feature ranges. The converter substitutes the bindings into the symbolic expression and lambdifies only the independent inputs. This supports fixed-per-equation values, not a parameter distribution.

The shared adapter requires all input ranges to remain within explicit `input_validity_bounds` across the Core-15 training, medium, near and far generation regimes. Its only current constraint policy is `rectangular_input_bounds_v1`. Cross-variable inequalities, coupled domains, state-dependent constraints and protocol semantics remain unsupported and require specialized generation. A reviewer-provided `constraint_evidence` string is not an automatic proof.

The existing 24 records have not been assigned numeric parameter values or validity intervals by this implementation pass. Those values must be grounded in primary-source/model review. Consequently, no candidate was promoted to generator-ready.
