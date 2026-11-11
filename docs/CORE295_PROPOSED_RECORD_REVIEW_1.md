# Core-295 proposed equation records — review pass 1

**Status:** three records drafted as `proposed`; none is accepted, scientifically reviewed, structurally reviewed or eligible for shard planning. This is a record-format and provenance pass, not a completed benchmark specification.

## Proposed records

| ID | Candidate | Primary/authoritative source | Outstanding blockers |
|---|---|---|---|
| CHEM-HENRY-001 | Henry gas-solubility relation | OpenStax Chemistry 2e §11.3 | Select a defensible gas/solvent/temperature context; freeze Henry coefficient convention, pressure and concentration units, train/extrapolation ranges and generator. |
| CHEM-LANGMUIR-001 | Single-site monolayer adsorption isotherm | Langmuir (1918), pp. 1369–1370, Eqs. (8)–(9) | Choose a physically defensible adsorbate/surface context; freeze pressure range, parameter treatment, units and generator. Confirm source transcription and site-count interpretation. |
| CHEM-MARCUS-001 | Outer-sphere electron-transfer rate with Marcus barrier | IUPAC Gold Book M03702; Marcus (1956) | Verify exact primary-paper equation/page; resolve consistent molecular vs molar energy units; freeze donor/acceptor/solvent context and ranges; conduct formal overlap review against Core-15 Arrhenius and Rate Law exclusions. |

## Exact candidate forms

### CHEM-HENRY-001

\[
C_g=k_H P_g.
\]

The chosen convention is dissolved concentration per gas partial pressure, e.g. mol L\(^{-1}\) kPa\(^{-1}\). OpenStax explicitly states the coefficient depends on gas, solvent and solution temperature. The section describes the proportionality for many gaseous solutes and ideal-solution treatment. Do not mix this with the reciprocal pressure-over-concentration Henry convention.

### CHEM-LANGMUIR-001

\[
\theta=\frac{u_1p}{1+u_1p}.
\]

Original notation \(u_1\) and the source's Eq. (8) are retained. Eq. (9) relates amount adsorbed to fractional coverage and the number of surface sites; it is not a second independent candidate. The original simple model assumes equivalent sites, one molecule per site, monolayer coverage and adsorption/desorption equilibrium.

### CHEM-MARCUS-001

\[
\Delta G^\ddagger=\frac{(\lambda+\Delta G^0)^2}{4\lambda},
\qquad
k_{ET}=\kappa_{ET}\frac{k_BT}{h}
\exp\left(-\frac{\Delta G^\ddagger}{RT}\right).
\]

This is the IUPAC modern form for outer-sphere electron transfer. IUPAC cautions that the classical expression is adequate in the normal region, while a more elaborate Franck–Condon treatment is generally needed in the inverted region. The rate-prefactor form must not be used to evade the Core-15 Arrhenius/Rate Law exclusions: the Marcus-specific reorganization-energy barrier is the claimed structural feature and needs explicit reviewer justification.

## Record hygiene and readiness

- All three records have stable IDs, source IDs, source-family IDs, explicit assumptions, variable meanings/units, and 64-character structural fingerprints computed from SymPy-normalized expressions.
- Input ranges are deliberately null and generator contracts explicitly pending. These are blocking omissions, not inferred values.
- `independence_unit_id`, reviewer and review dates are absent because no independence or scientific review has occurred.
- Status remains `proposed`; no record is marked `source_verified`, `scientifically_reviewed`, `structurally_reviewed` or `accepted`.
- The catalogue status remains `draft`; the 295 target and 59-per-domain target are unchanged.
- Proposed records are not loaded by the Core-295 equation loader, which only selects `accepted` entries.

## Source references

- OpenStax Chemistry 2e, [§11.3 Solubility](https://openstax.org/books/chemistry-2e/pages/11-3-solubility), Henry equation and example.
- Langmuir, I. (1918), [JACS 40(9), 1361–1403](https://doi.org/10.1021/ja02242a004), especially pp. 1369–1370, Eqs. (8)–(9).
- IUPAC, [Marcus equation, Gold Book M03702](https://goldbook.iupac.org/terms/view/M03702); Marcus, R. A. (1956), [J. Chem. Phys. 24, 966–978](https://doi.org/10.1063/1.1742723).

No experiment, live API call, validator execution or GitHub Actions workflow was run.
