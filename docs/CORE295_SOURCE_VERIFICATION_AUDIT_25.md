# Core-295 source verification audit 25: Langmuir 1918 single-site adsorption isotherm

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** proposed record CHEM-LANGMUIR-001 and registered primary source CHEM-LANGMUIR-1918.

## 1. Primary source and equation transcription

Irving Langmuir, *The adsorption of gases on plane surfaces of glass, mica and platinum*, Journal of the American Chemical Society 40(9) (1918), 1361–1403, DOI 10.1021/ja02242a004.

In Case I, “Simple Adsorption,” Langmuir assumes one kind of elementary site and one adsorbed molecule per site. At equilibrium, the adsorption rate on bare surface equals the evaporation rate from occupied surface:
[
\alpha p\theta_0=\nu_1\theta_1,
\qquad \theta_0+\theta_1=1.
]
With (u_1=\alpha/\nu_1), the paper's Eq. (8) is the coverage fraction:
[
\theta_1=\frac{u_1p}{1+u_1p}.
]
The paper then relates the amount adsorbed per unit area to the occupied-site fraction in Eq. (9). The proposed record is the exact Eq. (8) coverage relation, not a later empirical fit. The primary PDF pages 1369–1370 support the source location.

## 2. Assumptions and validity

The source's “simple adsorption” derivation requires:
- one class of equivalent elementary sites;
- one molecule per site;
- monolayer coverage, with adsorption on an occupied site treated as effectively reflected/rapidly evaporated;
- equilibrium between adsorption and desorption;
- the single-site kinetic coefficients represented by (alpha) and (
u_1).

The same 1918 paper explicitly warns that real surfaces can have several kinds of elementary sites, different adsorption strengths, steric hindrance, multiple occupancy, and other complex adsorption behavior. It develops a separate multiple-site treatment later in the paper. Those variants must not be silently folded into the simple Eq. (8) record.

(u_1) has inverse-pressure units, and (u_1p) is dimensionless. (0leq\theta_1<1) for finite positive pressure and positive (u_1). The benchmark must use a named adsorbate/surface/temperature and ranges where the one-site monolayer assumptions are defensible.

## 3. Structural-family and Core-15 exclusion review

The equation is a rational saturation curve:
[
\theta=\frac{p}{K+p},\qquad K=1/u_1.
]
This has the same mathematical saturation form as the Michaelis–Menten occupancy/rate relation and the simple Hill-one binding curve, even though the physical interpretation is gas adsorption coverage rather than enzyme turnover or ligand occupancy.

Therefore:
- within Chemistry, the adsorption coverage equation, its amount-adsorbed Eq. (9), and Langmuir–Hinshelwood adsorption substeps are one linked surface-adsorption family;
- do not count the pressure/affinity reparameterization, amount-adsorbed conversion, reciprocal linearization or multi-site variants as extra instances of the same simple model;
- the cross-domain structural policy must explicitly decide whether a Langmuir isotherm can count independently of Core-15's excluded Michaelis–Menten family and Biology's Hill/ligand-occupancy saturation family.

Different physical systems alone do not establish structural distinctness under an equation-form criterion. Conversely, if the benchmark's intended unit is a complete physical mechanism rather than a symbolic function class, that mechanism-level criterion must be declared consistently across all five domains.

## 4. Decision

**Disposition:** primary equation and original source location verified. Retain as a scientifically credible simple-adsorption candidate, but hold pending the cross-domain saturation-family/ Core-15 exclusion ruling and a named surface/adsorbate/temperature range contract. Do not accept the equation solely because it has a distinct domain label or source ID.

No catalogue record or status was changed. The formal catalogue remains at 128 source records, 19 proposed records and zero accepted records; the sampling frame remains unfrozen.

No experiments, solvers, validators, workflows, paid compute, API calls or adsorption measurements were run. This is source review only.
