# Core-295 candidate discovery batch 24: Beer–Lambert optical attenuation

**Status:** primary historical metadata plus authoritative modern equation tracing. One record has been drafted as proposed; no equation is accepted or counted toward the 59 Chemistry target.

## Beer–Lambert decadic spectral attenuation

**Primary historical source:** Beer (1852), “Bestimmung der Absorption des rothen Lichts in farbigen Flüssigkeiten,” *Annalen der Physik* 162(5), 78–88, DOI [10.1002/andp.18521620505](https://doi.org/10.1002/andp.18521620505). Wiley confirms bibliographic metadata, but the full text is currently unavailable through the publisher endpoint; the exact original equation page has not been transcribed.

**Authoritative modern equation:** [IUPAC Gold Book, Beer–Lambert law B00626](https://goldbook.iupac.org/terms/view/B00626) gives the decadic spectral-power relation:

\[
P_\lambda=P_\lambda^0\,10^{-\varepsilon c l},
\]

equivalently \(A=\log_{10}(P_\lambda^0/P_\lambda)=\varepsilon c l\).

Here \(P_\lambda^0\) and \(P_\lambda\) are incident and transmitted spectral radiant powers, \(c\) is absorber concentration, \(l\) is optical path length, and \(\varepsilon\) is the molar decadic absorption coefficient. For SI \(c\) in mol m\(^{-3}\) and \(l\) in m, \(\varepsilon\) has units m\(^2\) mol\(^{-1}\).

IUPAC limits the law to collimated monochromatic radiation in a homogeneous isotropic medium; spectral bandwidth must be narrow relative to absorption linewidths. Reflection, scattering, chemical association and high-concentration deviations must be controlled or modelled separately.

## Family and overlap controls

- Lambert's natural-exponential path attenuation, Beer's concentration dependence and the modern Beer–Lambert absorbance/transmittance forms belong to one optical-absorption family.
- Do not count \(A=\varepsilon c l\), \(P=P_0 10^{-\varepsilon c l}\), or the natural-exponential conversion as separate equation units.
- Decadic \(\varepsilon\) must not be mixed with a natural-log absorption coefficient; the conversion includes \(\ln 10\).
- The exponential attenuation structure is physically distinct from Arrhenius kinetics, but the Core-15 exclusion overlap still requires explicit review.
- The simple product \(A=\varepsilon c l\) may resemble other multiplicative scaling laws when parameters are grouped; compare full variable dependence and units rather than equation names.

## Proposed-record status

The draft entry CHEM-BEER-LAMBERT-001 uses the exact IUPAC decadic transmitted-power expression and cites Beer (1852) for historical lineage. It remains proposed because the original Beer equation page is not available, and the wavelength/material/concentration/path-length benchmark contract is not frozen.

No experiment, validator execution, live API call or GitHub Actions workflow was run.
