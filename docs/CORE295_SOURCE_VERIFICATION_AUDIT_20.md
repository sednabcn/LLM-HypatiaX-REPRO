# Core-295 source verification audit 20: Henry, Raoult and Beer–Lambert chemistry relations

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** proposed records CHEM-HENRY-001, CHEM-RAOULT-VAPOR-001 and CHEM-BEER-LAMBERT-001.

## 1. Henry gas-solubility relation

OpenStax Chemistry 2e §11.3 gives the relation:
[
C_g=k_H P_g.
]
The proportionality constant depends on gas identity, solvent identity and solution temperature. The text explicitly presents the law as applying to many gaseous solutes and gives an example with (k_H) in mol L(^{-1}) kPa(^{-1}).

The proposed record's units are consistent with the OpenStax example if (C_g) is mol L(^{-1}) and (P_g) is kPa. The coefficient convention must be fixed: other Henry constant conventions invert the ratio or use mole fraction instead of concentration.

**Boundary:** gas-liquid equilibrium at fixed temperature and fixed gas/solvent pair, in the dilute/ideal proportionality regime. Reactive dissolution, strong nonideality, changing temperature or a different Henry-constant convention requires a different adapter.

**Disposition:** exact modern equation and unit example verified. Retain as a credible candidate pending named gas/solvent pair, temperature and train/extrapolation ranges.

## 2. Raoult ideal-solution component vapor-pressure relation

OpenStax Chemistry 2e §11.4 gives:
[
P_A=X_A P_A^*,
]
where (P_A) is the component partial pressure, (X_A) its liquid-phase mole fraction, and (P_A^*) the pure-component saturation vapor pressure at the same temperature. The source explicitly restricts the relation to an ideal solution. For a multicomponent mixture, total pressure is obtained by summing component partial pressures under Dalton's law; that sum is not another independent Raoult equation.

The registered historical source is Raoult (1887), Comptes Rendus 104, 1430–1433, but original page-level equation transcription remains outstanding. The current exact formula is therefore supported by OpenStax as a modern textbook expression, not yet by direct transcription of the original 1887 paper.

**Structural boundary:** Henry and Raoult describe different physical limits and thermodynamic systems—dilute gas solubility versus ideal liquid-vapor component equilibrium—but their proposed scalar equations both have the same bare proportionality structure (y=kx). If Core-295 requires structural rather than merely physical-mechanism distinctness, these two cannot automatically be counted as separate units. The catalogue's distinct source-family IDs do not settle this policy question.

**Disposition:** formula and ideal-solution regime verified from OpenStax; hold pending primary historical transcription and a formal decision on whether distinct physical regimes with the same linear proportionality form count as structurally distinct.

## 3. Beer–Lambert decadic spectral attenuation

The registered IUPAC Gold Book B00626 source gives the modern decadic spectral-power expression:
[
P_\lambda=P_\lambda^0 10^{-\varepsilon c l}.
]
The proposed record writes the same relation using (I) and (I_0):
[
I=I_0 10^{-\varepsilon c l}.
]
This is a notation change only. (arepsilon) is the decadic molar absorption coefficient, (c) the absorber concentration and (l) the optical path length. Units must satisfy dimensional consistency, e.g. (arepsilon) in m\(^2\) mol\(^{-1}\), (c) in mol m\(^{-3}\), and (l) in m.

The registered Beer (1852) primary paper metadata is known, but the full original paper equation page was not available in this source check. The exact modern decadic expression is supported by IUPAC; do not claim that the notation above is a verbatim transcription from Beer (1852). Lambert's path attenuation and Beer’s concentration dependence are contributions to one Beer–Lambert family. Decadic absorbance (A=\varepsilon c l), transmitted-power form and natural-exponential form are linked representations, not separate candidates.

**Boundary:** homogeneous isotropic absorbing medium, monochromatic or sufficiently narrow-band radiation, negligible scattering/reflection, and a concentration/path-length regime where the molar absorption coefficient remains constant. Do not mix decadic and natural-log coefficients without the (ln 10) conversion.

**Disposition:** modern equation and IUPAC provenance verified; hold pending primary Beer source-page transcription, named absorbing species/wavelength and valid parameter ranges.

## 4. Cross-candidate decision

| Candidate | Source result | Structural issue | Disposition |
|---|---|---|---|
| Henry | Exact OpenStax equation and coefficient units verified | Linear proportionality family | Hold pending named system/ranges |
| Raoult | Exact OpenStax ideal-solution equation verified | Same bare linear proportionality form as Henry despite different physical regime | Hold; primary-source transcription and distinctness policy unresolved |
| Beer–Lambert | Exact modern IUPAC decadic expression verified | One exponential attenuation family; Beer/Lambert/absorbance variants are linked | Hold pending original Beer source and material/wavelength/ranges |

No equation is accepted by this audit. Do not count component sums, alternate coefficient conventions, absorbance/transmission representations, or source notation variants as additional equations.

## 5. Catalogue and experiment status

No catalogue record, source status, proposed count or accepted count was changed. The formal catalogue remains at 128 source records, 19 proposed records and zero accepted records; the sampling frame remains unfrozen.

No experiments, solvers, validators, workflows, paid compute, API calls or chemical measurements were run. This is source review only.
