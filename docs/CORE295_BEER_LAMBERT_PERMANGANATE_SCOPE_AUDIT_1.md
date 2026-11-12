# Core-295 Beer-Lambert permanganate scope audit 1

Date: 2026-11-12

Candidate: `CHEM-BEER-LAMBERT-001`

## Decision and scoped system

Keep the decadic transmitted-intensity form

\[
I=I_0 10^{-\varepsilon c l}
\]

and specialize the material/wavelength coefficient to direct spectrophotometric measurement of aqueous permanganate, \(\mathrm{MnO_4^-}\), at 525 nm in neutral-pH aqueous phosphate buffer (pH 7.1, 0.1 M), using the direct method of McBeath, Wilkinson and Graham (2020).

The paper reports a molar absorption coefficient of 3340 M\(^{-1}\) cm\(^{-1}\) at 525 nm for the direct method, with standards prepared from 0 to 63 μM. It reports an LOQ of 1.51 μM and LOD of 0.45 μM for that direct method. It also reports measurable instability during the first 60 minutes after preparation, so sample handling/time must be controlled; this is not a timeless fixed-composition calibration.

For the catalogue's SI convention, convert the decadic coefficient:
\[
3340\;\mathrm{L\,mol^{-1}\,cm^{-1}}
=334\;\mathrm{m^2\,mol^{-1}}.
\]
Use concentration in mol m\(^{-3}\) and optical path length in m, so \(\varepsilon c l\) is dimensionless. Do not mix this decadic coefficient with a natural-log attenuation coefficient.

## Evidence limits

- The reported 0–63 μM is the range of prepared direct-method standards, not a proof that every concentration is quantitatively reliable. The reported LOQ is 1.51 μM; the LOD is 0.45 μM. Preserve these distinctions.
- The coefficient is specific to aqueous permanganate at 525 nm and the reported neutral-pH matrix; do not reuse it for other wavelengths, species, pH or buffer matrices.
- The paper abstract and accessible sections do not establish a transferable optical path length for the calibration coefficient in the accessible text. Keep path length as an explicit input with range unset; do not assume 1 cm.
- The paper reports instability over the first 60 minutes; define immediate/controlled measurement timing in any future dataset protocol. Do not use the time-drift observation to alter the Beer-Lambert coefficient without source-supported kinetic modelling.
- The original Beer (1852) paper is bibliographically verified, but this audit still relies on the IUPAC Gold Book for the exact modern decadic spectral attenuation equation, not a direct transcription from Beer.
- Lambert's natural-exponential path relation, decadic absorbance A=εcl, and transmitted-intensity expression are linked forms of the same optical attenuation family, not separate equation candidates.

## Catalogue model contract correction

The existing catalogue record had no dependent variable, even though the formula predicts transmitted intensity I. Correct the role assignment to independent variables \(I_0,c,l\), dependent variable \(I\), and fixed coefficient \(\varepsilon\). Wavelength, species, and matrix are fixed scope metadata. The coefficient is fixed at 334 m² mol\(^{-1}\) only for the declared 525 nm permanganate system. Do not set numeric I0 or l values or ranges without source evidence.

## Structural review

The exponential attenuation map is not the same normalized first-gradient flux operator as Fick/Fourier/Ohm. However, compare it against Core-15 exponential/attenuation and generic response exclusions before acceptance; physical application labels alone do not prove structural uniqueness.

## Disposition

Candidate remains proposed and generator pending. The corrected output role and scoped coefficient improve the model contract but do not establish benchmark readiness, independent statistical units, or full source-page transcription. Keep train/extrapolation bounds unset pending a specific instrument/path and data design.

## Sources

- McBeath, Wilkinson & Graham (2020), “Analytical quantification of aqueous permanganate: Direct and indirect spectrophotometric determination for water treatment processes,” *Chemosphere* 251, 126626, DOI 10.1016/j.chemosphere.2020.126626: https://doi.org/10.1016/j.chemosphere.2020.126626
- PubMed record and abstract, including direct-method coefficient, 0.03–63 μM method range, LOD/LOQ and time instability: https://pubmed.ncbi.nlm.nih.gov/32443247/
- IUPAC Gold Book, Beer-Lambert law B00626, exact decadic spectral-power attenuation expression: https://goldbook.iupac.org/terms/view/B00626
- Beer (1852), historical primary source metadata: https://doi.org/10.1002/andp.18521620505

No scripts, validators, tests, workflows, live experiments or scientific simulations were run.
