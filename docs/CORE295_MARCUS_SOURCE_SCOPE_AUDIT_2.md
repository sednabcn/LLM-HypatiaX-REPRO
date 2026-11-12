# Core-295 Marcus source-scope audit 2

Date: 2026-11-12

Candidate: `CHEM-MARCUS-001`

## Decision

**Do not benchmark or promote the current catalogue expression.** It is a hybrid of (a) the 1956 solution-bimolecular collision-number prefactor and (b) a later/generalized quadratic reorganization-barrier parameterization. The prefactor convention and barrier expression are not yet demonstrated as one source-matched equation for one fully specified kinetic model.

## What the 1956 primary source actually supports

Marcus, R. A. (1956), “On the Theory of Oxidation-Reduction Reactions Involving Electron Transfer. I,” *Journal of Chemical Physics* 24(5), 966–978, DOI 10.1063/1.1742723.

The publisher-hosted abstract and the Caltech repository's attached published paper identify the model as a slight-orbital-overlap electron-transfer mechanism in solution. The paper derives an electrostatic contribution to the intermediate-state formation free energy, \(\Delta F^*\), using nonequilibrium solvent polarization and a constrained variational calculation. It states that when conversion of the intermediate to products is more probable than return to reactants, the overall rate is the solution collision number multiplied by \(\exp(-\Delta F^*/kT)\).

The full-paper equation/page mapping already inspected in audit 1 is:
- Eq. (7), printed p. 969: overall bimolecular rate constant for the two-intermediate mechanism.
- Eq. (8), printed p. 969: conditional approximation \(k_{bi}\cong k_1\) in the stated parameter regime.
- Eq. (44), printed p. 975: intermediate-formation rate \(k_1=Z\exp(-\Delta F^*/kT)\), with \(Z\) the solution collision number.
- Eq. (47), printed p. 976: restates the conditional overall-rate approximation.

The paper explicitly says the more exact Eq. (7) is required if \(k_2\) is appreciably less than \(k_{-1}\). The collision-number expression is therefore not a universal Marcus prefactor or a general rate law for all electron-transfer regimes.

## Quadratic barrier and prefactor are a different convention

The IUPAC Gold Book Marcus equation entry gives an encounter-complex/intramolecular expression with an Eyring prefactor and electronic transmission coefficient, conventionally written

\[
k_{ET}=\kappa_{ET}\frac{k_BT}{h}
\exp\left(-\frac{\Delta G^\ddagger}{RT}\right),
\qquad
\Delta G^\ddagger=\frac{(\lambda+\Delta G^0_{ET})^2}{4\lambda}.
\]

This is not interchangeable with Marcus's 1956 solution collision-number prefactor \(Z\). Also, the 1956 primary-paper abstract describes \(\Delta F^*\) as the electrostatic contribution obtained from its nonequilibrium-polarization variational construction; the current catalogue does not yet document a line-by-line derivation identifying that exact \(\Delta F^*\) with the modern quadratic \(\Delta G^\ddagger\) in the proposed hybrid equation.

## Core-15 structural exclusion

Even a source-faithful activated-rate form \(k=Z\exp(-\Delta F^*/kT)\) has an exponential activation structure. The Core-15 exclusion registry explicitly includes Arrhenius and generic Rate Law. A Marcus mechanism label alone is not evidence of structural distinctness. The proposed candidate must undergo explicit E0-E5 comparison against those exclusions, and it must demonstrate that the full governing model is not merely an activated-rate special case already represented by Core-15.

## Required resolution before any promotion

1. Choose one kinetic scope: the 1956 solution-bimolecular slight-overlap model, or a specified encounter-complex/intramolecular model.
2. Transcribe the complete source-matched barrier expression and all symbol definitions from the selected primary derivation, not from an abstract or a later summary.
3. Match the prefactor and units to that kinetic scope; do not combine \(Z\) and \(\kappa_{ET}k_BT/h\).
4. Specify the reactant charge/radius/solvent/electrostatic inputs required by the chosen barrier model, including whether the candidate is self-exchange or a general redox reaction.
5. Resolve the Arrhenius/Rate Law E0-E5 overlap against the frozen Core-15 exclusion policy.
6. Only then define fixed parameters, independent inputs, physical validity conditions and source-supported sampling bounds.

## Catalogue disposition

Keep `CHEM-MARCUS-001` as proposed and generator-pending. Keep numeric ranges and fixed parameter values empty. Mark the current hybrid expression as source-scope unresolved and explicitly ineligible for benchmarking. This audit does not accept a new equation or change the accepted-equation count.

## Sources

- Marcus (1956), CaltechAUTHORS record with attached published paper and abstract: https://authors.library.caltech.edu/records/desqy-fmq55
- Marcus (1956), publisher bibliographic record and abstract: https://pubs.aip.org/aip/jcp/article-abstract/24/5/966/74480/On-the-Theory-of-Oxidation-Reduction-Reactions?redirectedFrom=fulltext
- Marcus (1956), DOI: https://doi.org/10.1063/1.1742723
- IUPAC Gold Book, Marcus equation M03702: https://goldbook.iupac.org/terms/view/M03702
- Earlier repository audit with the detailed equation/page mapping: docs/CORE295_CHEM_ADSORPTION_AND_MARCUS_AUDIT_1.md

No scripts, validators, tests, workflows, live experiments or scientific simulations were run.
