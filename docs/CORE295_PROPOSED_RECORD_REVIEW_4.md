# Core-295 proposed equation records — review pass 4

**Status:** one additional Physics record drafted as proposed. It is not accepted, scientifically reviewed, structurally reviewed or eligible for shard planning.

## PHYS-PLANCK-SPECTRUM-001 — Planck blackbody spectral intensity

Chosen benchmark convention: spectral power intensity emitted per unit wavelength, as printed in OpenStax *University Physics Volume 3*, §6.1, Eq. 6.11:

\[
I(\lambda,T)=\frac{2\pi h c^2}{\lambda^5}
\frac{1}{\exp\left(\frac{hc}{\lambda k_B T}\right)-1}.
\]

This convention has units W m\(^{-3}\) (power per area per unit wavelength). It is not the same object as spectral energy density or spectral intensity per unit frequency; transformations between conventions require the appropriate wavelength/frequency Jacobian.

Planck's 1901 paper, “Ueber das Gesetz der Energieverteilung im Normalspectrum,” *Annalen der Physik* 309, 553–563, DOI [10.1002/andp.19013090310](https://doi.org/10.1002/andp.19013090310), is the primary historical source. Its original spectral-distribution convention must be transcribed separately before this record can be marked source-verified. OpenStax Eq. 6.11 is the exact modern equation chosen for this candidate.

**Overlap control:** Wien's displacement law is the location of the maximum of this spectrum; Stefan's law is obtained by integrating it over wavelength. They are derived consequences in the same blackbody-radiation family and are not counted as independent equation units here.

**Benchmark blockers:** keep \(h,c,k_B\) fixed at declared SI constants; sample only positive wavelength and temperature; choose defensible wavelength/temperature domains; specify the output scaling because spectral intensity spans many orders of magnitude; freeze a deterministic generator and extrapolation policy. A real surface with non-unit emissivity is outside the ideal-blackbody formula unless emissivity is explicitly modelled.

## Proposed-record inventory

- Chemistry: CHEM-HENRY-001, CHEM-LANGMUIR-001, CHEM-MARCUS-001.
- Biology: BIO-HILL-MUSCLE-001.
- Physics: PHYS-POISEUILLE-001, PHYS-PLANCK-SPECTRUM-001.
- All six records are proposed; none is accepted.
- Ranges and generator contracts remain pending.

No experiment, validator execution, live API call or GitHub Actions workflow was run.
