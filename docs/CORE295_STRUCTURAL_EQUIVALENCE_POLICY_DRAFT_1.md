# Core-295 structural-equivalence policy — draft 1

**Status:** proposed curation policy for review; not yet frozen into the catalogue or used to accept/reject any formal entry. This draft responds to overlap found in the five author-pool screens. It does not alter the target of 295 (59 per domain).

## 1. What is being counted

The counting unit should be a **complete governing mathematical model**, not an arbitrary formula string or an isolated output chosen from a larger model.

Each candidate must declare one model class:

- scalar algebraic constitutive/response relation;
- scalar ODE or recurrence;
- coupled ODE/recurrence system;
- PDE or coupled PDE system;
- integral/delay equation;
- constrained protocol state-transition or accounting system.

The model class, state dimension, independent/dependent variables, operator structure, and boundary/initial conditions are part of its identity. A component equation extracted from a coupled system is not an independent candidate unless the source itself defines it as a closed model and its statistical unit is defensibly independent.

## 2. Equivalence levels

Every pairwise comparison receives one of these labels:

| Level | Definition | Counting treatment |
|---|---|---|
| E0 — exact duplicate | Same expression/model after whitespace, symbol-name and metadata normalization | One candidate only |
| E1 — algebraically equivalent | Rearrangement, inverse, solved-for-different-variable form, unit conversion, or equivalent parameterization | Same structural family; do not count separately |
| E2 — derived/limiting form | Derivative, integral, linearization, asymptote, limiting case, closed-form solution or special solution of the same governing model | Same family unless a predeclared model-level rule justifies a separate governing model |
| E3 — same operator/topology, distinct mechanism | Same normalized scalar functional form or operator but a different physical/protocol mechanism and independent source lineage | **Do not count as structurally distinct under the strict primary rule.** Retain as a mechanism-diversity lead; a different benchmark objective would be needed to count it |
| E4 — related but structurally distinct model | Shared parent theory or broad motif, but different irreducible operator, state topology, nonlinear structure, constraint, or governing mechanism | May count separately after scientific review; preserve common source-family/dependence labels |
| E5 — unresolved | Insufficient source detail, ambiguous units/variables, incomplete system or uncertain equivalence | Hold; no count |

The strict E3 rule is deliberate. For example, a first-order RC exponential response and a radioactive-decay exponential can have the same normalized scalar function. Their mechanisms differ, but that alone does not make their equation structures distinct. Both may remain in the discovery bank, but the 295 structural count should not be inflated by relabelling the same functional structure across domains.

## 3. Canonical comparison

For each candidate, record:

1. Exact source expression and a faithful transcription.
2. Dimensionless/canonical form where scientifically valid; do not erase dimensional constants or constraints merely to force a match.
3. Symbol-renaming-invariant expression-tree or operator signature.
4. Variable-dependency graph and state dimension.
5. Differential order, integral/delay structure, recurrence order, constraints and boundary/initial conditions.
6. Derivation parent(s), special-case relations and source-family identifier.
7. Domain mechanism and source/protocol lineage.
8. Statistical-unit identifier, which is separate from the source-family identifier.

Symbolic fingerprints are a first-pass duplicate detector only. They do not prove inequivalence. Human review must check transformations, units, assumptions and parent models.

## 4. Rules for common cases

- **Rearrangements/inverses:** one family, not separate candidates.
- **Outputs from one model:** period, amplitude, peak, activity, force, energy or price derived from one governing model are not automatically independent equations.
- **Solutions vs governing equations:** an ODE and its closed-form solution belong to one family unless the benchmark explicitly defines the solution form as the counting unit for every domain.
- **Approximations/limits:** retain provenance but group with the parent (e.g. Rayleigh–Jeans with Planck; small-angle pendulum with nonlinear pendulum).
- **Special solutions:** Poiseuille flow is a special solution of viscous-fluid momentum equations; Torricelli efflux is a Bernoulli consequence. A special solution is not automatically a separate structural family.
- **Coupled systems:** preserve the full system as one model unit. Do not count prey and predator equations, HH gate equations, or multiple accounting stages as independent rows.
- **Same broad mechanism, different structures:** distinct invariant or governing equations can qualify even within one protocol family, provided their irreducible structures differ and they have separate source/model definitions.
- **Cross-domain analogues:** compare after variable and unit normalization. Domain labels cannot make identical operator structures distinct.
- **Empirical fits:** require a named dataset/material/population, fitted parameter meaning, validity domain and source. A generic power/exponential curve is not a sourced physical law.

## 5. Domain-specific illustrations from the static audits

- Chemistry: integrated kinetics and half-lives; Langmuir one-/two-site variants; Fick flux and its transport-operator analogues.
- Biology: Monod/Holling-II/receptor occupancy/Emax hyperbolic saturation; Lotka–Volterra as one coupled system; PK input/clearance outputs.
- Physics: projectile range/height; centripetal force/acceleration; Planck/Wien/Stefan/Rayleigh–Jeans; decay/activity; drag/terminal balance; Bohr energy/radius.
- DeFi AMM: swap directions, spot price and LP outputs from one invariant; concentrated-liquidity position/amount formulas; curve-specific invariant families.
- DeFi Risk: VaR variants under frozen Core-15 exclusions; health-factor/liquidation transformations; protocol rate and liquidation subsystems.

## 6. Statistical independence is a separate test

Structural distinctness does not establish independent observations. Every entry must have both:

- `source_family_id`: primary source lineage, shared theory/model family, or protocol implementation lineage;
- `statistical_unit_id`: unit actually sampled for calibration/evaluation.

A set of 59 structurally distinct equations from one source, generator, protocol family or shared dataset may still have dependent outcomes. The sampling frame must identify the source universe, cluster design, sampling method and independence assumptions before any binomial confidence guarantee is claimed.

## 7. Acceptance workflow

1. Source verified at exact page/equation/section/commit.
2. Formula/system transcribed and dimensional/physical/protocol assumptions reviewed.
3. Pairwise family comparison completed against existing accepted and proposed entries, including cross-domain entries and Core-15 exclusions.
4. E0–E5 decision and derivation parent recorded with rationale.
5. Deterministic generator and defensible training/extrapolation domain specified.
6. Source-family and statistical-unit identifiers assigned.
7. Independent human review completed.
8. Only then may the entry be marked accepted.

## 8. Consequence for the 295 target

The 295 target remains fixed for planning, but acceptance is not quota-driven. If a domain cannot reach 59 under this strict structural rule, expand the source universe. Do not relax E3 or split a model into derived outputs to meet the quota. Any later change from structural diversity to mechanism diversity requires an explicit design decision and revised manuscript description.

## 9. Open decisions before freezing

- Confirm strict E3 exclusion across domains, including RC vs radioactive exponential responses.
- Confirm that coupled systems/PDEs can count as one model unit, or define a uniform scalar adapter that preserves the full model.
- Freeze the Core-15 exclusion list and determine whether related governing families or only exact listed equations are excluded.
- Specify whether empirical constitutive equations count alongside first-principles governing equations.
- Define minimum source diversity per domain and maximum number of accepted entries from one source/protocol lineage.
