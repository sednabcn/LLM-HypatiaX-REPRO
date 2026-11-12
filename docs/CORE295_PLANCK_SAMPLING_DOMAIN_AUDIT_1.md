# Core-295 Planck candidate: sampling-domain audit 1

**Candidate:** `PHYS-PLANCK-SPECTRUM-001`  
**Status:** evidence review only; no range or generator promotion  
**Date:** 2026-11-12

## Scope

The candidate represents Planck spectral exitance per unit wavelength:

\[
M_\lambda(T)=\frac{2\pi h c^2}{\lambda^5\left(\exp\left(\frac{hc}{\lambda k_B T}\right)-1\right)}.
\]

The selected output convention is power per area per unit wavelength (W m\(^{-3}\)), as stated by OpenStax University Physics Volume 3, §6.1, Eq. 6.11. It is not spectral radiance per unit solid angle.

## Evidence inspected

1. OpenStax §6.1 explicitly defines the wavelength-dependent power emitted per unit area and wavelength and prints Eq. 6.11. Its text and figures discuss blackbody examples at 300 K and 5000–6000 K, and curves at 2000, 3000, 4000 and 5000 K. These are teaching examples, not a prescribed joint sampling design.
2. NBS Special Publication 250-1 (Walker, Saunders & Hattenburg, 1987) describes a spectral-radiance calibration service over 225–2400 nm. It reports a variable-temperature comparison blackbody operable up to about 2700 K and a gold-point blackbody at 1337.58 K. It also gives Planck's law for spectral radiance in Eq. (2), with wavelength in air and refractive-index terms.
3. The NBS quantity is spectral radiance per solid angle, whereas this candidate is spectral exitance per area. The quantities are related for an ideal Lambertian blackbody, but the NBS calibration specification is not a direct statement of the candidate's exact output convention. Its calibration wavelengths and temperatures are also instrument/source operating conditions, not universal limits of Planck's law.

## Range decision

**Do not populate `input_ranges` or `input_validity_bounds` from these examples.** The inspected evidence does not define:
- a joint rectangular domain in wavelength and temperature;
- a training versus extrapolation split;
- a distribution over the independent variables; or
- universal finite physical validity bounds beyond \(\lambda>0\) and \(T>0\).

In particular, pairing the minimum and maximum values independently would manufacture a Cartesian sampling frame that the source does not report. Treating the NBS calibration envelope as the law's validity envelope would also confuse a specific radiometric service with the mathematical model's domain.

## What is still required

A benchmark owner must predeclare a numerical coverage design for \(\lambda\) and \(T\), with units and training/medium/near/far regions, and justify numerical conditioning and the intended blackbody regime. That design must be labelled as a benchmark sampling choice, not a source-reported physical limit. If it is intended to represent a specific calibration or physical application, the corresponding source dataset and output convention must be matched exactly.

The exact SI defining values already recorded for \(h\), \(c\), and \(k_B\) remain fixed constants. They do not determine input ranges.

## Disposition

- Candidate remains `proposed`.
- Source verification and structural review remain open.
- Generator remains `pending_benchmark_contract`.
- No input ranges or validity bounds were invented.
- No tests, validators, scripts, data generation, or experiments were run.

## Sources

- OpenStax, *University Physics Volume 3*, §6.1: https://openstax.org/books/university-physics-volume-3/pages/6-1-blackbody-radiation
- Walker, Saunders & Hattenburg, *NBS Measurement Services: Spectral Radiance Calibrations*, NBS SP 250-1 (1987): https://www.nist.gov/system/files/documents/pml/div685/pub/sp250-1.pdf
- BIPM, SI defining constants: https://www.bipm.org/en/measurement-units/si-defining-constants
