# Core-295 candidate discovery batch 25: chemical equilibrium, electrochemistry and solution thermodynamics

**Date:** 2026-11-11  
**Status:** discovery-only source leads. None of the relations below is added to the formal catalogue or counted toward the 295 target.  
**Domain focus:** Chemistry. The aim is to expand the source universe beyond the six current proposed records without creating variants of excluded or already-covered families.

## 1. Nernst electrochemical potential relation

**Source:** OpenStax Chemistry 2e §17.4, *Potential, Free Energy, and Equilibrium*; OpenStax Ch. 17 key equations.

[
E_{cell}=E_{cell}^{\circ}-\frac{RT}{nF}\ln Q.
]

**Distinctive role:** equilibrium cell potential under nonstandard composition. (Q) is the reaction quotient built from activities; (n) is electrons transferred; (F) is Faraday's constant.

**Boundary and risks:** distinguish cell potential from standard potential, electrode potential, and reaction free energy. Activities are dimensionless relative to standard states; replacing them with raw concentrations is an ideal-solution approximation. (T) is absolute temperature. The standard-state relation (E^circ=(RT/nF)\ln K), the base-10 form at 298.15 K, and the Gibbs relation ΔG=-nFE are linked thermodynamic conversions, not separate candidates.

**Initial disposition:** high-value source lead for electrochemical equilibrium; verify exact reaction quotient construction and compare the full equation with existing electrochemical source families before drafting.

## 2. Debye–Hückel limiting law for ionic activity coefficients

**Sources:** Debye and Hückel (1923), *Zur Theorie der Elektrolyte I*; IUPAC Gold Book, *Debye–Hückel equation* (D01534), with mean-activity/limiting-law convention clarified in Audit 27.

The mean molal activity-coefficient limiting form is:
\[
\log_{10}\gamma_{\pm}=-A\,|z_+z_-|\sqrt{I},
\]
where \(\gamma_{\pm}\) is the mean ionic activity coefficient, \(z_+\) and \(z_-\) are cation and anion charge numbers, \(I=\tfrac12\sum_i m_i z_i^2\) is molal ionic strength, and \(A\) is solvent- and temperature-dependent. A single-ion coefficient form is convention-dependent and is not independently measurable thermodynamically.

**Boundary and risks:** the limiting law applies only at sufficiently low ionic strength, where finite-ion-size corrections are negligible (a common aqueous rule of thumb is about 0.01 mol kg−1 for uni-univalent electrolytes). Do not conflate the mean activity coefficient with the osmotic coefficient or a single-ion convention, and do not conflate the limiting law with the extended Debye–Hückel equation, Davies equation or Bates–Guggenheim convention. Those are related corrections/approximations in one electrolyte-activity family, not automatically independent equations. Individual-ion activity coefficients are convention-dependent and cannot be independently measured thermodynamically.

**Initial disposition:** high-value candidate lead, but freeze solvent, temperature, ionic-strength units, charge and activity convention; compare against existing ionic-activity source records before drafting.

## 3. Clausius–Clapeyron vapor-pressure temperature relation

**Source:** OpenStax Chemistry 2e §10.3, *Phase Transitions*.

The integrated constant-enthalpy form is:
[
\ln\left(\frac{P_2}{P_1}\right)
=\frac{\Delta H_{vap}}{R}
\left(\frac{1}{T_1}-\frac{1}{T_2}\right).
]

**Boundary and risks:** this is an integrated approximation for vapor-pressure change over a temperature interval, assuming approximately constant enthalpy of vaporization and the standard Clausius–Clapeyron approximations (ideal vapor and negligible liquid molar volume). The differential relation and integrated relation are one family; do not count the linearized plot or rearranged forms separately.

**Initial disposition:** high-value phase-equilibrium lead. It is related in functional form to van't Hoff temperature dependence of equilibrium constants, and both have reciprocal-temperature exponential/log-linear forms. A strict structural policy may cluster them even though the equilibrium quantities and physical systems differ.

## 4. van't Hoff temperature dependence of equilibrium constants

**Sources:** OpenStax Chemistry 2e thermodynamics/equilibrium material; Atkins, *Physical Chemistry*, chemical equilibrium chapter; modern peer-reviewed phase-equilibrium review.

Differential form:
[
\frac{d\ln K}{dT}=\frac{\Delta_r H^\circ}{RT^2}.
]
For approximately constant (Delta_r H^\circ), the two-temperature integrated form is:
[
\ln\left(\frac{K_2}{K_1}\right)
=-\frac{\Delta_r H^\circ}{R}
\left(\frac{1}{T_2}-\frac{1}{T_1}\right).
]

**Boundary and risks:** the integrated form assumes reaction enthalpy is effectively constant across the temperature interval; heat-capacity changes may require a more complete treatment. Do not count differential, integrated and rearranged forms as separate equations. Clausius–Clapeyron is a phase-equilibrium specialization/analogue of the broader temperature-dependence structure. Both require a family-level equivalence ruling.

**Initial disposition:** sourceable thermodynamic relation, but do not count independently of Clausius–Clapeyron without an explicit structural/physical-family decision.

## 5. Osmotic pressure: explicit Core-15 overlap warning

OpenStax Chemistry 2e §11.4 gives the dilute-solution van't Hoff osmotic-pressure relation:
[
\Pi=MRT.
]
This is mathematically the ideal-gas equation with pressure interpreted as osmotic pressure and molar concentration replacing (n/V). Because Core-15 excludes the Ideal Gas Law, this is not an eligible Core-295 candidate under the current exclusion policy unless a future, explicit physical-mechanism policy permits the same algebraic structure in a different domain. Retain it as a source lead and exclusion/equivalence example only; do not draft it as a new candidate now.

## 6. Batch-level structural findings

| Lead | Functional structure | Relation to existing families | Initial decision |
|---|---|---|---|
| Nernst | Additive standard potential minus (RT/(nF)) times log reaction quotient | Electrochemical equilibrium; distinct from electrode kinetic current laws | Verify and consider |
| Debye–Hückel limiting | Log activity coefficient proportional to charge squared and square root ionic strength | One family with extended DH/Davies corrections | Verify and consider |
| Clausius–Clapeyron | Log vapor-pressure ratio linear in reciprocal temperature | Related to van't Hoff and activated reciprocal-temperature forms | Hold for family policy |
| van't Hoff | Log equilibrium-constant ratio linear in reciprocal temperature | Related to Clausius–Clapeyron; differential/integrated forms are one family | Hold for family policy |
| Osmotic pressure | (Pi=MRT) | Algebraically identical to excluded Ideal Gas Law | Exclude under current policy |

The batch supplies five source leads, not five independent equations. The strongest candidates for further source verification are Nernst and Debye–Hückel. Clausius–Clapeyron and van't Hoff require explicit family handling; osmotic pressure is blocked by the Core-15 Ideal Gas Law exclusion.

## 7. Catalogue status and work not performed

No source-register or equation-catalogue record was changed. The formal manifest remains 128 source records, 19 proposed equation records, zero accepted equations, and an unfrozen sampling frame.

No experiments, validators, solvers, workflows, paid compute, API calls or chemical measurements were run. This is source discovery only.
