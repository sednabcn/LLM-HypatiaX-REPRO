# Core-295 source verification audit 21: Hill muscle force–velocity relation and Planck spectral exitance

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** proposed records BIO-HILL-MUSCLE-001 and PHYS-PLANCK-SPECTRUM-001.

## 1. Hill 1938 muscle force–velocity characteristic equation

### Primary transcription

A. V. Hill, *The heat of shortening and the dynamic constants of muscle*, Proceedings of the Royal Society B 126 (1938), 136–195, DOI 10.1098/rspb.1938.0050. The original paper's Part II, section (b), prints:
[
(P+a)v=b(P_0-P) 	ag{1}
]
and rewrites it as
[
(P+a)(v+b)=(P_0+a)b=mathrm{constant}. 	ag{2}
]
The original PDF confirms this at printed page 162 (equations 1–2). It later states that the force-velocity relation can be verified mechanically without thermal measurements and gives experimental fits on printed pages 176–177. Thus the proposed record's pp. 174–177 reference points to the later verification, not the first printed occurrence of equation (2).

The original paper defines (P) as load, (v) as shortening velocity, (P_0) as isometric tension, (a) as a force/load dimension, and (b) as a velocity. For isotonic shortening, (P<P_0) and (v>0). The paper's equation is grounded in the measured relationship between excess energy liberation rate and load, not simply a generic hyperbola fit.

### Scope and family boundary

The relation is a steady force-velocity characteristic for active striated muscle under the paper's experimental conditions (tetanic activation, constant load during shortening, controlled muscle preparation and temperature). The source discusses extension to lengthening, but the proposed record should keep its stated concentric-shortening regime unless a separate lengthening contract is specified.

This is not the Hill ligand-binding/saturation equation. Shared author surname and hyperbolic algebra do not make muscle mechanics and ligand binding the same scientific model family. Conversely, do not count the energy-rate relation ((P+a)v=b(P_0-P)), the rearranged characteristic equation, its normalized form, or a fitted parameter rescaling as separate candidates: they are equivalent representations of one force-velocity relation.

**Disposition:** original equation and experimental context verified. Correct the source-location metadata to cite equation (2) at printed p. 162 and its later mechanical verification at pp. 176–177. Retain as a credible Biology candidate, held pending muscle-preparation, temperature, force/velocity convention and valid-range contract.

## 2. Planck 1901 spectral distribution and modern spectral exitance

### Primary equation and conversion

Max Planck, *Ueber das Gesetz der Energieverteilung im Normalspectrum*, Annalen der Physik 309 (1901), 553–563, DOI 10.1002/andp.19013090310. The accessible original German text prints equation (13), for wavelength-resolved spatial energy density:
[
E_\lambda
=\frac{8\pi c h}{\lambda^5}
\frac{1}{\exp\left(\frac{ch}{k\lambda\vartheta}\right)-1}.
]
The same paper gives the frequency-domain spatial energy density in equation (12). The source convention is energy density per unit wavelength, not surface radiance or spectral exitance.

For isotropic equilibrium radiation, the outward hemispherical spectral flux/exitance is (c/4) times the spectral energy density. Applying that conversion gives:
[
M_\lambda
=\frac{c}{4}E_\lambda
=\frac{2\pi h c^2}{\lambda^5}
\frac{1}{\exp\left(\frac{hc}{\lambda k_B T}\right)-1}.
]
This matches the proposed formula's coefficient and wavelength dependence. The proposed symbol (I(\lambda,T)) should be replaced by (M_\lambda) (or another explicitly defined exitance symbol) to avoid confusing exitance with radiance. (M_\lambda) has units W m\(^{-3}\), power per area per unit wavelength.

### Structural and scope boundary

The candidate is the blackbody spectral exitance per unit wavelength. The original Planck paper's energy-density equation, the frequency-domain form, the (c/4) exitance conversion, and spectral radiance are different representations/observables of the same Planck distribution family; do not count them as independent candidates. Wien's displacement law is obtained from the spectral maximum and Stefan–Boltzmann total power from integration; both remain in the Planck source family and must not be added as independent equations by simple derivation.

The benchmark must fix:
- wavelength-domain output (M_\lambda), not frequency-domain density or radiance;
- vacuum wavelength and absolute temperature (T>0);
- ideal blackbody equilibrium;
- fixed SI values of (h,c,k_B), not sampled constants;
- positive wavelength and a finite physically justified wavelength/temperature domain.

Real-material emissivity, spectral bandwidth, non-equilibrium radiation and non-blackbody surfaces are outside this equation unless explicitly incorporated.

**Disposition:** original Planck equation (13), the spectral convention and the modern (c/4) conversion are source-verified. Retain as a credible Physics candidate, held pending a frozen output convention and wavelength/temperature ranges.

## 3. Catalogue and experiment status

No catalogue record, source status, proposed count or accepted count was changed. The formal catalogue remains at 128 source records, 19 proposed records and zero accepted records; the sampling frame remains unfrozen.

No experiments, solvers, validators, workflows, paid compute, API calls, muscle measurements or thermal-radiation measurements were run. This is source review only.
