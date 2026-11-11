# Core-295 proposed equation records — review pass 16

**Status:** one additional Chemistry record drafted as proposed. It is not accepted, scientifically reviewed, structurally reviewed or eligible for shard planning.

## CHEM-BEER-LAMBERT-001 — decadic spectral attenuation

IUPAC Gold Book B00626 gives the exact modern decadic relation for spectral radiant power:

\[
P_\lambda=P_\lambda^0\,10^{-\varepsilon c l}.
\]

Here \(P_\lambda^0\) is incident spectral radiant power, \(P_\lambda\) transmitted spectral radiant power, \(\varepsilon\) the molar decadic absorption coefficient, \(c\) absorber concentration, and \(l\) optical path length. With \(c\) in mol m\(^{-3}\) and \(l\) in m, \(\varepsilon\) is in m\(^2\) mol\(^{-1}\). The equivalent absorbance form \(A=\log_{10}(P_\lambda^0/P_\lambda)=\varepsilon c l\) is a linked representation, not a separate equation candidate.

**Primary historical source:** Beer (1852), “Bestimmung der Absorption des rothen Lichts in farbigen Flüssigkeiten,” *Annalen der Physik* 162(5), 78–88, DOI [10.1002/andp.18521620505](https://doi.org/10.1002/andp.18521620505). Wiley confirms the metadata but the full text is unavailable through its current endpoint. The exact modern equation is therefore sourced to [IUPAC Gold Book B00626](https://goldbook.iupac.org/terms/view/B00626), not claimed as a direct transcription of the original 1852 notation.

**Regime:** collimated monochromatic radiation in a homogeneous isotropic medium; the spectral bandwidth must be narrow relative to absorption linewidths. Scattering, reflection, chemical association, high-concentration interactions and wavelength-dependent departures from the ideal model require separate treatment.

**Family controls:** Lambert's natural-exponential path attenuation, Beer's concentration extension, decadic absorbance and transmitted-power expressions are one optical-absorption family. Do not count the linear absorbance relation and exponential transmission relation separately. Keep decadic coefficients separate from natural-log attenuation coefficients; the conversion includes \(\ln 10\).

**Benchmark blockers:** select a named absorber and wavelength, specify \(\varepsilon\), concentration and path-length domains, enforce the low-concentration/homogeneous-medium regime, and freeze a deterministic generator. Explicitly screen the exponential structure against Core-15 exclusions; physical interpretation alone does not establish structural distinctness.

## Proposed-record inventory

- Chemistry: CHEM-HENRY-001, CHEM-LANGMUIR-001, CHEM-MARCUS-001, CHEM-RAOULT-VAPOR-001, CHEM-FICK-FLUX-001, CHEM-BEER-LAMBERT-001.
- Biology: BIO-HILL-MUSCLE-001, BIO-FICK-CARDIAC-OUTPUT-001.
- Physics: PHYS-POISEUILLE-001, PHYS-PLANCK-SPECTRUM-001, PHYS-THIN-LENS-001.
- DeFi AMM: AMM-BALANCER-WEIGHTED-001, AMM-DODO-PMM-BASE-SHORTAGE-001.
- DeFi Risk: RISK-MORPHO-LIF-001, RISK-EULER-AUCTION-001, RISK-COMPOUND-BORROW-KINK-001, RISK-UNISWAP-V3-GEOMETRIC-TWAP-001, RISK-UNISWAP-V2-ARITHMETIC-TWAP-001.
- All eighteen records are proposed; none is accepted.
- Ranges and generator contracts remain pending.

No experiment, validator execution, live API call or GitHub Actions workflow was run.
