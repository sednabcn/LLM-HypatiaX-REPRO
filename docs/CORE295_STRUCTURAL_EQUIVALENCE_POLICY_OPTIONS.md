# Core-295 structural-equivalence policy: decision options and evidence map

**Date:** 2026-11-11  
**Status:** decision-support memo only. No policy option is selected by this document; no catalogue statuses or counts are changed.

## 1. Why a formal rule is required

Core-295 targets 295 structurally distinct equations, not 295 coefficient variants. Source verification has now exposed repeated cases where different scientific domains, protocols or historical names share the same normalized equation form. Without a predeclared rule, candidate inclusion can become inconsistent and the 59-per-domain target can be padded by relabeling.

The policy must define two related but different concepts:
1. **Structural equivalence:** whether two equations represent the same mathematical structure after allowed normalization.
2. **Statistical independence:** whether two sampled equation instances can be treated as independent observations for calibration/evaluation.

A different source, domain, protocol, variable name or unit does not by itself establish either structural distinction or statistical independence.

## 2. Normalization transformations to declare

The policy should explicitly say whether the following preserve equation identity:

- variable renaming and reordering;
- unit conversion and multiplication/division by fixed nonzero constants;
- algebraic rearrangement and solving for a different variable;
- dimensionless reparameterization and monotone change of output;
- replacing a parameter by a fixed value or taking a limiting case;
- derivative/integral/discrete-time representations of the same governing model;
- component equations, derived outputs, solver steps and numerical discretizations;
- vector/PDE systems reduced to scalar special cases.

A strict form rule normally treats all of the above as the same equation family unless the transformation changes the governing state structure or physical mechanism in a way the policy explicitly recognizes.

## 3. Three policy options

### Option A — strict normalized-form equivalence

Two equations belong to the same family if they reduce to the same normalized mathematical structure under variable/unit changes, algebraic rearrangement, fixed-parameter specialization or equivalent representation, regardless of scientific domain.

**Advantages**
- Strongest protection against formula padding.
- Simple to audit and apply consistently.
- Structural distinctness has a clear mathematical meaning.

**Costs**
- Different physical mechanisms with the same functional form cannot both count.
- The 59-per-domain requirement becomes harder and may require broader source universes or a revised design.
- Some scientifically meaningful cross-domain models are collapsed into one family.

### Option B — mechanism-aware structural equivalence

Equations with the same normalized scalar form may count separately if they arise from independently specified physical mechanisms, state variables, constitutive assumptions and source derivations. A different domain label alone is insufficient.

**Advantages**
- Recognizes genuine physical distinctions even when the observable formula is simple.
- Better reflects scientific domain diversity.

**Costs**
- The boundary between “different mechanism” and relabeling can be subjective.
- Correlated equations may be counted as distinct despite identical functional dependence.
- Statistical independence must still be clustered by shared form/derivation.

### Option C — hybrid form-and-system rule (recommended for decision)

Use strict normalized-form equivalence for scalar constitutive/algebraic equations, but treat a **complete coupled system** as a model unit when its state variables, coupling structure, dynamics and constraints differ materially from another system. A system may not be split into component equations to inflate the count. Domain labels and different parameter values never split a family.

This means:
- same scalar form with different units, parameter names or domain labels: same family;
- different scalar forms from one mechanism: may be distinct if not derivations, limits or rearrangements of one another;
- complete ODE/PDE/discrete/vector systems: compare the full system structure and state constraints, not individual components;
- scalar reductions, steady states, outputs and solver equations: remain attached to their parent system;
- statistical independence unit: source-family/model-system cluster, not each formula or protocol deployment.

**Advantages**
- Maintains a defensible mathematical criterion while allowing complete scientific systems that cannot be represented by scalar formula comparison.
- Fits the repository's existing distinction between equation-level and full-system candidates.
- Prevents component/variant padding.

**Costs**
- Requires a full-system adapter and explicit system-equivalence review.
- The 59 independent units per domain may still be difficult to obtain.

## 4. Evidence map: known collisions and distinctions

| Candidate pair/group | Evidence from audits | Option A result | Option B result | Option C result |
|---|---|---|---|---|
| Henry vs Raoult | Both linear proportionality laws, different gas/solution equilibrium assumptions (Audit 20) | Same scalar form family | Potentially distinct mechanisms | Same scalar family unless full constitutive systems differ |
| Langmuir vs Michaelis–Menten / Hill-one | Same rational saturation form (Audit 25) | Same family | Could split only with a strong mechanism rule | Same scalar family |
| Fick vs Fourier vs Ohm | Same linear-gradient flux structure; Fick explicitly gives analogy (Audit 26) | Same family | Could split by physical mechanism | Same scalar family; coupled transport PDEs may differ as systems |
| Clausius–Clapeyron vs van't Hoff | Same reciprocal-temperature log-linear dependence, different equilibrium quantities (Batch 25) | Likely same form family | Could split by phase vs reaction equilibrium | Scalar forms grouped unless full state systems differ |
| EWMA vs GARCH(1,1) | EWMA is the IGARCH boundary case (Audit 34) | Same family | Same family | Same conditional-variance family |
| Bragg vs double-slit/grating maxima | Same path-difference constructive-interference form (Audit 33) | Same family | Could split by crystal vs slit mechanism | Same scalar path-difference family |
| Uniswap v2 vs v3 TWAP | Arithmetic vs geometric averaging estimands (Audit 10) | Distinct formulas | Distinct estimands | Distinct scalar estimands but one oracle/market-data source family for independence |
| Gyro 2-CLP / Uniswap v3 / Maverick / LLAMMA per-band | Constant product in virtual reserves (Audits 32, 38, 39 and Batch 32) | Same invariant family | Same mechanism family or closely related implementations | Same invariant family; LLAMMA full lending/liquidation state machine may be a distinct system unit |
| Gyro E-CLP vs Gyro 2-CLP | Affine-transformed ellipse vs virtual constant product (Audit 38/39) | Distinct | Distinct | Distinct |
| StableSwap vs CryptoSwap | Fixed amplification vs dynamic \(K(K_0,A,\gamma)\) invariant (Audit 37) | Distinct formulas within amplified-invariant family | Distinct model mechanisms | Distinct invariant structures but one related family for source/parameter clustering |
| Fick cardiac output vs Fick diffusion | Oxygen mass balance vs concentration-gradient flux (Audit 23/26) | Distinct | Distinct | Distinct structures and mechanisms |
| Hill muscle vs Hill ligand-binding | Same surname, different source, variables and mechanism (Audit 21/25) | Distinct formulas | Distinct | Distinct |
| Fisher–KPP vs scalar logistic growth | Spatial diffusion plus logistic reaction (Audit 29) | Different PDE vs ODE structure, but shares reaction family | Different spatial mechanism | One spatial reaction–diffusion system; logistic reaction not a separate equation |
| Leslie vs replicator vs Nicholson–Bailey | Different vector/discrete population systems (Audit 28) | Distinct system structures | Distinct | Distinct complete systems; no component splitting |
| Heston vs Merton jump diffusion | Coupled stochastic variance vs compound-Poisson jumps (Audits 30/32) | Distinct stochastic structures | Distinct | Distinct systems; shared market data may still induce statistical dependence |

## 5. Recommended operational rule (Option C)

If adopted, use the following test for every candidate:

1. Normalize variables, units and fixed constants; identify the exact mathematical form.
2. Identify the governing physical/protocol mechanism and the source derivation.
3. Identify parent models, limiting cases, algebraic rearrangements, equivalent representations and derived outputs.
4. For systems, write the complete state vector, all coupled equations, constraints, boundary/initial conditions and discrete/continuous time structure.
5. Assign one family ID to all forms and variants that are not independent under the adopted rule.
6. Assign the statistical independent-unit ID at the family/system level; multiple source documents or deployments of one family do not create independent units.
7. If a domain cannot supply 59 defensible independent units, expand the source universe or revise the design explicitly; do not relax the equivalence rule after seeing the count.

This recommendation is not adopted until the user explicitly chooses a policy. Until then, all unresolved cross-domain candidates remain held and the sampling frame stays unfrozen.

## 6. Catalogue status and work not performed

This memo does not modify the formal catalogue. The manifest remains 128 source records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls or statistical independence tests were run. This is policy design and evidence synthesis only.
