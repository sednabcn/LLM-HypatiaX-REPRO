# Core-295 proposed-record audit 5: Planck spectrum observable and primary-source conversion

**Date:** 2026-11-11  
**Status:** source-convention audit only. No equation is accepted by this audit.

## 1. PHYS-PLANCK-SPECTRUM-001 — exact observable in the current record

The proposed expression is
\[
I(\lambda,T)=\frac{2\pi h c^2}{\lambda^5}\,
\frac{1}{\exp\!\left(\frac{hc}{\lambda k_B T}\right)-1}.
\]

OpenStax *University Physics, Volume 3*, §6.1, Eq. 6.11 explicitly defines \(I(\lambda,T)\) as the power radiated per unit area of the cavity hole per unit wavelength. Therefore its SI output unit is \(\mathrm{W\,m^{-3}}\). In radiometric terminology, this observable is spectral radiant exitance (spectral emissive power), not spectral radiance per unit solid angle. The OpenStax formula and its definition are available at [§6.1 Blackbody Radiation](https://openstax.org/books/university-physics-volume-3/pages/6-1-blackbody-radiation).

**Required terminology correction:** rename the candidate **Planck spectral exitance per unit wavelength** (or explicitly retain the OpenStax term “power intensity per unit wavelength” and define it as exitance). Do not let “spectral intensity” be interpreted as radiance; radiance has a different angular normalization and a factor-of-\(\pi\) difference for an ideal Lambertian blackbody.

## 2. Relation to Planck's 1901 primary equation

Planck's 1901 paper, “On the Law of Distribution of Energy in the Normal Spectrum,” *Annalen der Physik* 309, 553–563, DOI [10.1002/andp.19013090310](https://doi.org/10.1002/andp.19013090310), gives the wavelength-domain spectral **energy density** in Eq. (13):
\[
E_\lambda=\frac{8\pi c h}{\lambda^5}\,
\frac{1}{\exp\!\left(\frac{hc}{\lambda k_B T}\right)-1}.
\]
The original text identifies \(E\,d\lambda\) as the volume density of blackbody radiation in the wavelength interval (printed p. 557; Eq. 13). It is not the same observable as the OpenStax per-area emitted power.

For isotropic equilibrium radiation, the outward flux through a surface is \(c/4\) times the energy density. Applying that conversion gives
\[
M_\lambda=\frac{c}{4}E_\lambda
=\frac{2\pi h c^2}{\lambda^5}\,
\frac{1}{\exp\!\left(\frac{hc}{\lambda k_B T}\right)-1},
\]
which is the candidate's OpenStax expression. Thus the modern formula is consistent with the Planck spectrum, but the conversion from Planck's original spectral energy density to surface spectral exitance must be stated. The primary paper is available as [a scan/translation](https://www.astro.puc.cl/~rparra/tools/PAPERS/planck1901.pdf); the original wavelength-domain Eq. (13) appears in the scan at lines corresponding to printed p. 557.

## 3. Family and derivation treatment

The candidate correctly records Wien's displacement relation and Stefan's integrated power as consequences of the same spectral family, not automatically separate independent equations. Preserve the spectral-exitance observable and its wavelength measure; changing to frequency density requires the Jacobian \(|d\lambda/df|=c/f^2\), not a simple substitution.

The constants \(h,c,k_B\) should remain fixed SI constants in the benchmark generator. Only \(\lambda\) and \(T\) are independent sampled inputs. The input ranges and deterministic generator are still unset.

## 4. Required resolution before acceptance

1. Rename the candidate to **Planck spectral exitance per unit wavelength** and explicitly define the observable and units.
2. Retain OpenStax §6.1 Eq. 6.11 as the direct modern source.
3. Record Planck 1901 Eq. (13) as the original wavelength spectral-energy-density equation and document the isotropic \(c/4\) conversion; do not imply the two observables are identical.
4. Freeze physically supported wavelength and temperature domains, fixed-constant policy, output units and deterministic generator.
5. Keep Wien and Stefan consequences in the same derivation family unless a predeclared structural rule justifies otherwise.

The manifest entry remains **proposed**. This audit does not change its status, count it toward Physics's 59, or authorize shard planning.

## 5. Audit boundary

No catalogue validator, experiment, paid compute, live API/protocol call or GitHub Actions workflow was run. No experiment results are implied by this source review.
