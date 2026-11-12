# Core-295 Raoult source and scope audit 1

Date: 2026-11-12

Candidate: `CHEM-RAOULT-VAPOR-001`

## Decision

The generalized component equation is directly and explicitly stated in OpenStax Chemistry 2e §11.4:

\[
P_A=X_A P_A^*.
\]

Here \(P_A\) is the equilibrium vapor partial pressure of component A, \(X_A\) is its liquid-phase mole fraction, and \(P_A^*\) is the pure-component saturation vapor pressure at the same temperature. OpenStax states this relation for any component of an ideal solution, and separately gives the solvent-only reduction when the other solutes are nonvolatile.

The original Raoult paper is bibliographically verified as F.-M. Raoult (1887), “Loi générale des tensions de vapeur des dissolvants,” *Comptes Rendus* 104, 1430–1433. In this pass, the original four-page paper was not retrieved for direct page-level equation transcription. Do not claim the modern generalized component notation is a verbatim equation from the 1887 paper.

## Concrete source-grounded worked case

OpenStax Example 11.6 specifies an ideal glycerin/ethanol solution at 40 °C. Glycerin is treated as essentially nonvolatile; ethanol is the volatile solvent. The source gives the pure ethanol vapor pressure at 40 °C as 0.178 atm and computes a liquid ethanol mole fraction of 0.800, yielding a solution vapor pressure of 0.142 atm.

For a narrowly scoped candidate, use:
- Component A: ethanol.
- Other component: glycerin (glycerol), treated as nonvolatile in the cited example.
- Temperature: 40 °C.
- Fixed pure-component vapor pressure: \(P_A^*=0.178\) atm.
- Independent input: \(X_A\), dimensionless, constrained by mole-fraction definition to \(0\le X_A\le1\).
- Output: \(P_A\), atm.
- The cited worked point is \(X_A=0.800\), \(P_A=0.142\) atm (rounded by the source).

The worked point is a textbook illustration, not a measured validation dataset, a statistical sampling frame, or evidence that every ethanol-glycerol composition is experimentally ideal. The physical input domain \([0,1]\) follows from mole-fraction definition; it is not a claim that the ideal-solution approximation is validated over the full interval for this actual pair.

## Limitations and family review

- The source explicitly describes ideal-solution behavior. Nonideal mixtures require activity coefficients and cannot be generated with this scalar ideal relation without a separate model.
- Keep temperature fixed because \(P_A^*\) is temperature-specific.
- The total vapor pressure \(P_{solution}=\sum_i X_iP_i^*\) is the multicomponent sum plus Dalton's law; do not count it as an independent equation candidate from the component relation.
- The solvent-only equation is a specialization when other solutes are nonvolatile; do not count it separately.
- Henry's law describes the dilute-solute limiting regime, whereas Raoult's law describes ideal-solution component behavior. Their shared liquid-gas equilibrium setting and linear component-pressure form require explicit E0-E5/source-family review before both are counted as structurally distinct calibration units. This audit does not resolve that pairwise decision.
- The 1887 original paper equation/page transcription remains open. The accessible exact modern equation source is OpenStax §11.4, lines 147–157 and worked Example 11.6, lines 162–172.

## Catalogue disposition

Narrow the candidate to ethanol in the ideal ethanol-glycerin worked example at 40 °C, fix \(P_A^*=0.178\) atm, and use \(X_A\in[0,1]\) only as the mathematical mole-fraction domain. Keep train/extrapolation splits unset pending benchmark design. Candidate remains proposed and generator pending. Do not claim primary-source transcription, empirical validation, full-domain physical validity, or structural distinctness from Henry's law.

## Sources

- OpenStax Chemistry 2e §11.4, exact component law, assumptions and Example 11.6: https://openstax.org/books/chemistry-2e/pages/11-4-colligative-properties
- Raoult (1887), bibliographic record: *Comptes Rendus* 104, 1430–1433; DOI not identified. Bibliographic cross-check: https://pmc.ncbi.nlm.nih.gov/articles/PMC6682120/
- Le Moyne historical chemistry notes cite the original 1887 paper and state the solvent vapor-pressure relation, but are secondary teaching notes: https://web.lemoyne.edu/giunta/classicalcs/raoultvapnote.html

No scripts, validators, tests, workflows, live experiments or scientific simulations were run.
