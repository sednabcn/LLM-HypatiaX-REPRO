# Core-295 Chemistry adsorption and electron-transfer audit 1

**Date:** 2026-11-11  
**Scope:** Static source and equation-family reconstruction. No candidate accepted; no code, fitting, solver, experiment or validator run.

## 1. Frumkin adsorption versus Langmuir

The source register includes Langmuir's 1918 primary paper and Frumkin's 1920 *On the theory of electrocapillarity: II* (Philosophical Magazine, Series 6, 40(237), 375–385). **Attribution correction:** the 1920 paper is a relevant electrocapillarity source, but it should not be cited as the established original derivation of the modern Frumkin coverage isotherm. The Moscow State University Department of Electrochemistry bibliography separately lists Frumkin's 1926 *The Influence of the Electric Field on the Adsorption of Neutral Molecules* (Zeitschrift für Physik 35, 792–802); a later technical account attributes the isotherm derivation to 1926. That 1926 paper is now registered as the higher-priority primary equation source, but its exact equation/page is not yet transcribed.

The equation-level form commonly given in modern literature is

[
bc=\frac{\theta}{1-\theta}\exp(-2a\theta),
]

where θ is surface coverage, (b) an adsorption coefficient/activity convention, and (a) an adsorbate-interaction parameter. A later technical treatment gives the corresponding surface equation of state, γ = −RTΓ∞ ln(1−θ) + aθ², and reports that combining it with Gibbs adsorption yields this coverage isotherm. This is secondary equation-level evidence, not yet direct transcription from the 1926 primary paper.

**Structural screen:** At (a=0), the Frumkin equation reduces to the Langmuir isotherm. Thus Langmuir is a parameter-limit/special case of this Frumkin expression, not an independent count if the generalized Frumkin family is the model unit (E2 under the draft policy). For nonzero (a), the exponential coverage-interaction factor changes the constitutive relation and represents nonideal lateral adsorbate interactions. This is a potentially distinct model family from ideal Langmuir adsorption, but it must be reconstructed with a source-verified parameter/sign convention and a physical coverage domain (0\leq\theta<1).

**Provenance caution:** Frumkin's 1920 paper is registered as the primary historical lead, but the exact modern form above is not claimed to have been directly transcribed from a numbered equation in that paper. The equation-level cross-check is secondary/modern literature. Do not accept or import it until the original source or a definitive authoritative derivation is checked.

## 2. Electrocapillary adsorption is not a generic Langmuir row

Frumkin's electrocapillarity work concerns the dependence of interfacial adsorption on electrode potential/electric field. A 1926 Nature note by Frumkin and Obrutsheva explicitly reports that adsorption of ions and neutral molecules depends on the direction and strength of the interfacial electric field. This is a mechanistic clue, not itself a complete equation record. If an electrosorption candidate is pursued, its model contract must specify electrode potential/reference, electrolyte composition, surface charge, adsorbate valence, competitive site balance and standard states.

## 3. Marcus electron transfer: distinguish the rate prefactor by kinetic scope

The primary Marcus 1956 paper describes a slight-orbital-overlap outer-sphere electron-transfer mechanism and a quantitative solution-rate theory. Its publisher abstract explicitly states that, when conversion from the activated intermediate to products is more probable than return to reactants, the overall solution reaction rate is the intermediate-formation rate: the solution collision number multiplied by exp(-ΔF*/kBT). Thus the source-specific expression is k = Z exp(-ΔF*/kBT), with Z denoting the solution collision number and ΔF* the electrostatic free-energy contribution to forming the intermediate. This is direct primary-source abstract evidence, not yet a transcription of the complete numbered equation from the paper PDF. IUPAC's current Marcus equation entry gives an encounter-complex/intramolecular form with an Eyring prefactor and electronic transmission coefficient:

[
k_{ET}=\kappa_{ET}\frac{k_BT}{h}\exp\left(-\frac{\Delta G^{\ddagger}}{RT}\right),
\qquad
\Delta G^{\ddagger}=\frac{(\lambda+\Delta G^0_{ET})^2}{4\lambda}.
]

The transmission factor distinguishes adiabatic and diabatic transfer; the inverted region requires additional Franck–Condon/vibrational treatment.

**Pool disposition:** Do not label either prefactor universally correct without fixing the model scope. The 1956 solution-reaction treatment is associated with a solution collision-number prefactor (Z), whereas the IUPAC encounter-complex/intramolecular form uses κ_ET k_BT/h. These are not interchangeable metadata choices: the equation must declare bimolecular solution encounter versus encounter-complex/intramolecular kinetics, and define the prefactor and units accordingly. The uploaded candidate's generic (Z) is therefore not automatically wrong, but it is underspecified as a general Marcus rate law. Do not silently identify the 1956 ΔF* with the later/generalized quadratic expression ΔG‡=(λ+ΔG°ET)²/(4λ): the 1956 abstract describes an electrostatic variational construction, and its exact equation/parameter mapping still needs line-by-line PDF verification. The collision-number statement is now source-confirmed at abstract level; the full equation transcription and model contract remain open.

## 4. Butler–Volmer lineage: correct primary attribution

The full modern two-exponential current–overpotential relation should not be attributed to Butler's 1924 paper alone. Butler's 1924 Part II/III papers developed a kinetic/dynamic-equilibrium interpretation of the Nernst reversible potential. Erdey-Grúz and Volmer's 1930 *Zur Theorie der Wasserstoffüberspannung* is a key primary source for slow-discharge hydrogen overpotential kinetics and the transfer coefficient; the historical record also includes Erdey-Grúz and Volmer's 1931 treatment and Butler's 1932 paper on overvoltage. A recent detailed historical review explicitly cautions that Butler's 1924 works did not set out a complete theory of heterogeneous electron-transfer rates, while the 1930 Erdey-Grúz–Volmer contribution is often omitted from the familiar equation name.

The commonly used charge-transfer-controlled form is

[
j=j_0\left[\exp\left(\frac{\alpha_a nF\eta}{RT}\right)-\exp\left(-\frac{\alpha_c nF\eta}{RT}\right)\right],
]

with sign convention, electron number, transfer coefficients and surface concentrations declared. Some simplified forms impose a relation between anodic and cathodic transfer coefficients; that relation is not a universal identity for every mechanism. If surface concentrations differ from bulk because of mass transport, concentration ratios must be retained and the scalar form above is not the complete mixed-control model.

**Structural screen:** This is an electrochemical interfacial charge-transfer kinetic law with two directional exponential contributions. It is not the Frumkin adsorption isotherm and not the Marcus outer-sphere solution electron-transfer barrier model. The shared presence of exponentials is not enough to equate mechanisms. Keep the full current law as a family lead, but do not count its anodic and cathodic terms, Tafel limits, or linear small-overpotential approximation as separate equations. Exact primary equation/page transcription and scope conditions remain required before promotion.

## 5. Candidate-family disposition

| Family | Structural relationship | Current action |
|---|---|---|
| Langmuir ideal monolayer | Frumkin (a=0) limit | Group under Frumkin parent if the generalized model is selected; do not count both |
| Frumkin interacting adsorption | Coverage-dependent exponential interaction term | High-priority distinct-family lead; exact primary transcription pending |
| Potential-dependent electrosorption | Adds electrode potential, charge and electrochemical standard-state dependence | Research lead; requires a complete electrochemical model contract |
| Marcus outer-sphere electron transfer | Quadratic reorganization-energy barrier; prefactor depends on solution-bimolecular versus encounter-complex/intramolecular scope | Specify source-matched (Z) or κ_ET(k_BT/h) convention and verify primary equation before promotion |
| Butler–Volmer / Erdey-Grúz–Volmer electrode kinetics | Two directional exponential charge-transfer contributions under declared surface-concentration and transfer-coefficient assumptions | Keep as a distinct electrochemical interfacial kinetic lead; do not attribute the complete modern law to Butler 1924 alone; verify 1930 primary equation |

## 5. Source evidence

- Frumkin (1920), primary electrocapillarity source: https://doi.org/10.1080/14786440908636137
- Frumkin (1926), *The Influence of the Electric Field on the Adsorption of Neutral Molecules*, Z. Phys. 35, 792–802; bibliographic listing: https://www.elch.chem.msu.ru/article/index.htm
- Later technical treatment of Frumkin equation of state and isotherm derivation: https://studylib.net/doc/26249563/yuliy-d.-gamburg--giovanni-zangari--auth.----theory-and-p...
- Frumkin & Obrutsheva (1926), electric-field dependence of adsorption: https://doi.org/10.1038/117790a0
- Langmuir (1918), primary ideal adsorption source: https://doi.org/10.1021/ja02242a004
- Marcus (1956), primary electron-transfer theory; publisher abstract explicitly identifies solution collision number × exp(-ΔF*/kBT): https://doi.org/10.1063/1.1742723
- Caltech repository record and attached original paper PDF: https://authors.library.caltech.edu/records/desqy-fmq55
- IUPAC Marcus equation, prefactor and barrier definition: https://goldbook.iupac.org/terms/view/M03702
- Butler (1924), *Studies in heterogeneous equilibria, Part III*: https://doi.org/10.1039/TF9241900734
- Erdey-Grúz & Volmer (1930), *Zur Theorie der Wasserstoffüberspannung*: https://doi.org/10.1515/zpch-1930-15020
- Dickinson & Wain, historical and equation-form review of Butler–Volmer: https://www.sciencedirect.com/science/article/pii/S1572665720303283
- Equation-level Frumkin isotherm and surface equation of state: https://pmc.ncbi.nlm.nih.gov/articles/PMC5686271/
- Interfacial adsorption isotherm comparison: https://pure.rug.nl/ws/portalfiles/portal/3086148/c3.pdf

No formal catalogue equation entry was added or accepted by this audit.
