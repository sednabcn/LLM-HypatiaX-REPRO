# Core-295 Chemistry adsorption and electron-transfer audit 1

**Date:** 2026-11-11  
**Scope:** Static source and equation-family reconstruction. No candidate accepted; no code, fitting, solver, experiment or validator run.

## 1. Frumkin adsorption versus Langmuir

The source register already includes Langmuir's 1918 primary paper. This pass adds Frumkin's 1920 *On the theory of electrocapillarity: II* as a primary historical source lead (Philosophical Magazine, Series 6, 40(237), 375–385). The source record is not yet a verified equation/page transcription.

The equation-level form commonly given in modern literature is

[
bc=\frac{\theta}{1-\theta}\exp(-2a\theta),
]

where θ is surface coverage, (b) an adsorption coefficient/activity convention, and (a) an adsorbate-interaction parameter. A recent accessible primary-research treatment gives this form and the corresponding surface equation of state; a review table lists Langmuir, Volmer, Frumkin, Temkin and other isotherms as distinct coverage relations derived from different assumptions.

**Structural screen:** At (a=0), the Frumkin equation reduces to the Langmuir isotherm. Thus Langmuir is a parameter-limit/special case of this Frumkin expression, not an independent count if the generalized Frumkin family is the model unit (E2 under the draft policy). For nonzero (a), the exponential coverage-interaction factor changes the constitutive relation and represents nonideal lateral adsorbate interactions. This is a potentially distinct model family from ideal Langmuir adsorption, but it must be reconstructed with a source-verified parameter/sign convention and a physical coverage domain (0\leq\theta<1).

**Provenance caution:** Frumkin's 1920 paper is registered as the primary historical lead, but the exact modern form above is not claimed to have been directly transcribed from a numbered equation in that paper. The equation-level cross-check is secondary/modern literature. Do not accept or import it until the original source or a definitive authoritative derivation is checked.

## 2. Electrocapillary adsorption is not a generic Langmuir row

Frumkin's electrocapillarity work concerns the dependence of interfacial adsorption on electrode potential/electric field. A 1926 Nature note by Frumkin and Obrutsheva explicitly reports that adsorption of ions and neutral molecules depends on the direction and strength of the interfacial electric field. This is a mechanistic clue, not itself a complete equation record. If an electrosorption candidate is pursued, its model contract must specify electrode potential/reference, electrolyte composition, surface charge, adsorbate valence, competitive site balance and standard states.

## 3. Marcus electron transfer: distinguish the rate prefactor by kinetic scope

The primary Marcus 1956 paper describes a slight-orbital-overlap outer-sphere electron-transfer mechanism and a quantitative solution-rate theory. The rate prefactor must be tied to the kinetic scope. IUPAC's current Marcus equation entry gives the encounter-complex/intramolecular form with an Eyring prefactor and electronic transmission coefficient:

[
k_{ET}=\kappa_{ET}\frac{k_BT}{h}\exp\left(-\frac{\Delta G^{\ddagger}}{RT}\right),
\qquad
\Delta G^{\ddagger}=\frac{(\lambda+\Delta G^0_{ET})^2}{4\lambda}.
]

The transmission factor distinguishes adiabatic and diabatic transfer; the inverted region requires additional Franck–Condon/vibrational treatment.

**Pool disposition:** Do not label either prefactor universally correct without fixing the model scope. The 1956 solution-reaction treatment is associated with a solution collision-number prefactor (Z), whereas the IUPAC encounter-complex/intramolecular form uses κ_ET k_BT/h. These are not interchangeable metadata choices: the equation must declare bimolecular solution encounter versus encounter-complex/intramolecular kinetics, and define the prefactor and units accordingly. The uploaded candidate's generic (Z) is therefore not automatically wrong, but it is underspecified as a general Marcus rate law. The quadratic free-energy barrier is the defining structural feature; the exact 1956 primary equation and parameter convention still require line-by-line verification before promotion.

## 4. Candidate-family disposition

| Family | Structural relationship | Current action |
|---|---|---|
| Langmuir ideal monolayer | Frumkin (a=0) limit | Group under Frumkin parent if the generalized model is selected; do not count both |
| Frumkin interacting adsorption | Coverage-dependent exponential interaction term | High-priority distinct-family lead; exact primary transcription pending |
| Potential-dependent electrosorption | Adds electrode potential, charge and electrochemical standard-state dependence | Research lead; requires a complete electrochemical model contract |
| Marcus outer-sphere electron transfer | Quadratic reorganization-energy barrier; prefactor depends on solution-bimolecular versus encounter-complex/intramolecular scope | Specify source-matched (Z) or κ_ET(k_BT/h) convention and verify primary equation before promotion |
| Butler–Volmer electrode kinetics | Exponential anodic/cathodic overpotential contributions | Keep separate from Marcus outer-sphere rate unless a derivation establishes equivalence; do not attribute the full modern equation to Butler 1924 alone |

## 5. Source evidence

- Frumkin (1920), primary historical source: https://doi.org/10.1080/14786440908636137
- Frumkin & Obrutsheva (1926), electric-field dependence of adsorption: https://doi.org/10.1038/117790a0
- Langmuir (1918), primary ideal adsorption source: https://doi.org/10.1021/ja02242a004
- Marcus (1956), primary electron-transfer theory: https://doi.org/10.1063/1.1742723
- IUPAC Marcus equation, prefactor and barrier definition: https://goldbook.iupac.org/terms/view/M03702
- Equation-level Frumkin isotherm and surface equation of state: https://pmc.ncbi.nlm.nih.gov/articles/PMC5686271/
- Interfacial adsorption isotherm comparison: https://pure.rug.nl/ws/portalfiles/portal/3086148/c3.pdf

No formal catalogue equation entry was added or accepted by this audit.
