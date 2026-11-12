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

The primary Marcus 1956 paper describes a slight-orbital-overlap outer-sphere electron-transfer mechanism and a quantitative solution-rate theory. Direct inspection of the paper PDF now verifies the numbered equations and their conditional scope. The steady-state two-intermediate mechanism gives the overall bimolecular rate constant (Eq. 7, printed p. 969) as \(k_{bi}=k_1/[1+(1+k_{-2}/k_3)k_{-1}/k_2]\). For the stated parameter regime, Marcus reduces this to \(k_{bi}\cong k_1\) (Eq. 8, printed p. 969; neglecting a factor of about two). The intermediate-formation constant is explicitly \(k_1=Z\exp(-\Delta F^*/kT)\) (Eq. 44, printed p. 975), where the paper identifies \(Z\) as the collision number in solution; the resulting approximation is restated as \(k_{bi}\cong k_1=Z\exp(-\Delta F^*/kT)\) (Eq. 47, printed p. 976). The approximation is not universal: Marcus says the more exact Eq. 7 must be used if \(k_2\) is appreciably less than \(k_{-1}\). The paper itself emphasizes that its final formula is not applicable to electron-transfer reactions with a large-overlap activated complex. Thus the source-specific prefactor and rate expression are now directly transcribed, but only for this small-overlap solution mechanism and its stated kinetic regime. IUPAC's current Marcus equation entry gives an encounter-complex/intramolecular form with an Eyring prefactor and electronic transmission coefficient:

[
k_{ET}=\kappa_{ET}\frac{k_BT}{h}\exp\left(-\frac{\Delta G^{\ddagger}}{RT}\right),
\qquad
\Delta G^{\ddagger}=\frac{(\lambda+\Delta G^0_{ET})^2}{4\lambda}.
]

The transmission factor distinguishes adiabatic and diabatic transfer; the inverted region requires additional Franck–Condon/vibrational treatment.

**Pool disposition:** Do not label either prefactor universally correct without fixing the model scope. The 1956 solution-reaction treatment is associated with a solution collision-number prefactor (Z), whereas the IUPAC encounter-complex/intramolecular form uses κ_ET k_BT/h. These are not interchangeable metadata choices: the equation must declare bimolecular solution encounter versus encounter-complex/intramolecular kinetics, and define the prefactor and units accordingly. The uploaded candidate's generic (Z) is therefore not automatically wrong, but it is underspecified as a general Marcus rate law. Do not silently identify the 1956 ΔF* with the later/generalized quadratic expression ΔG‡=(λ+ΔG°ET)²/(4λ): the 1956 abstract describes an electrostatic variational construction, and its exact equation/parameter mapping still needs line-by-line PDF verification. The collision-number statement and numbered equations are now source-confirmed from the full PDF: Eq. 7–8 on printed p. 969, Eq. 44 on p. 975, and Eq. 47 on p. 976. The collision-number convention is the solution collision number \(Z\), not an Eyring prefactor. The source's small-overlap and rate-regime restrictions remain part of the model contract.

## 4. Butler–Volmer lineage: correct primary attribution

The full modern two-exponential current–overpotential relation should not be attributed to Butler's 1924 paper alone. Butler's 1924 Part II/III papers developed a kinetic/dynamic-equilibrium interpretation of the Nernst reversible potential. Erdey-Grúz and Volmer's 1930 *Zur Theorie der Wasserstoffüberspannung* is a key primary source for slow-discharge hydrogen overpotential kinetics and the transfer coefficient; the historical record also includes Erdey-Grúz and Volmer's 1931 treatment and Butler's 1932 paper on overvoltage. A recent detailed historical review explicitly cautions that Butler's 1924 works did not set out a complete theory of heterogeneous electron-transfer rates, while the 1930 Erdey-Grúz–Volmer contribution is often omitted from the familiar equation name.

In the accessible ESTIR scan of the original 1930 paper (8-page scan), the authors explicitly construct two opposing electron-transfer rates, state the equilibrium condition where they are equal, and write the net current density as their difference. The key primary locations are Eqs. (7)–(8) on printed pp. 209–210, Eq. (13) and equilibrium Eq. (14) on printed p. 211, and the overpotential expression Eq. (15) and Tafel limit Eq. (17) on printed p. 212. The authors estimate the transfer coefficient parameter near 0.5 for their stated hydrogen-evolution conditions (printed p. 210). This is a source-verified mechanism-specific kinetic derivation, not proof that every modern multi-reaction Butler–Volmer parameterization is literally present in this 1930 paper.

A common generalized charge-transfer-controlled form is

[
j=j_0\left[\exp\left(\frac{\alpha_a nF\eta}{RT}\right)-\exp\left(-\frac{\alpha_c nF\eta}{RT}\right)\right],
]

with sign convention, electron number, transfer coefficients and surface concentrations declared. Some simplified forms impose a relation between anodic and cathodic transfer coefficients; that relation is not a universal identity for every mechanism. If surface concentrations differ from bulk because of mass transport, concentration ratios must be retained and the scalar form above is not the complete mixed-control model.

**Structural screen:** This is an electrochemical interfacial charge-transfer kinetic law with two directional exponential contributions. It is not the Frumkin adsorption isotherm and not the Marcus outer-sphere solution electron-transfer barrier model. The shared presence of exponentials is not enough to equate mechanisms. Keep the full current law as a family lead, but do not count its anodic and cathodic terms, Tafel limits, or linear small-overpotential approximation as separate equations. The 1930 primary equation/page locations are now verified from the scan, but a formal catalogue transcription still needs a consistent symbol/sign convention and a precise hydrogen-evolution surface-concentration contract before promotion.

## 4A. Frumkin chronology and primary-source correction

The earlier shorthand that treated Frumkin (1920) as the primary source for the modern interacting-coverage isotherm was too broad. The 1920 *On the Theory of Electrocapillarity* papers are electrocapillarity antecedents. The History of Electrochemistry bibliography explicitly dates the Frumkin isotherm to 1925 and separately lists (i) *Die Kapillarkurve der höheren Fettsäuren und die Zustandsgleichung der Oberflächenschicht* (Z. Phys. Chem. 116, 466–484), (ii) *Einige Bemerkungen zur Theorie der Adsorption und Verteilung* (pp. 501–503), and (iii) the 1926 neutral-molecule electric-field adsorption paper. The latter must not be conflated with the 1925 isotherm source. The accessible 1925 scan has been inspected at printed pp. 466–470: it defines \(\Gamma\), surface coverage and the dilute Gibbs/Langmuir baseline, but the exact non-ideal interaction equation still needs transcription from the relevant 1925 paper/pages. Retain the modern equation as a provisional family lead, not a verified verbatim primary transcription.

Historical source indexes: https://elchi.eu/frumkin-school/frumkins-publications/ and https://www.elch.chem.msu.ru/wp3/index.php/ru/articles/frumkinarticles/.

## 5. Candidate-family disposition

| Family | Structural relationship | Current action |
|---|---|---|
| Langmuir ideal monolayer | Frumkin (a=0) limit | Group under Frumkin parent if the generalized model is selected; do not count both |
| Frumkin interacting adsorption | Coverage-dependent exponential interaction term | High-priority distinct-family lead; exact primary transcription pending |
| Potential-dependent electrosorption | Adds electrode potential, charge and electrochemical standard-state dependence | Research lead; requires a complete electrochemical model contract |
| Marcus outer-sphere electron transfer | Quadratic reorganization-energy barrier; prefactor depends on solution-bimolecular versus encounter-complex/intramolecular scope | Specify source-matched (Z) or κ_ET(k_BT/h) convention and verify primary equation before promotion |
| Butler–Volmer / Erdey-Grúz–Volmer electrode kinetics | Two directional exponential charge-transfer contributions under declared surface-concentration and transfer-coefficient assumptions | Keep as a distinct electrochemical interfacial kinetic lead; do not attribute the complete modern law to Butler 1924 alone; verify 1930 primary equation |

## 5. Source evidence

- Frumkin (1920), *On the Theory of Electrocapillarity*, Philosophical Magazine 40, 363–385: electrocapillarity antecedent, not the original Frumkin interacting-adsorption isotherm: https://doi.org/10.1080/14786440908636137
- Frumkin (1925), *Die Kapillarkurve der höheren Fettsäuren und die Zustandsgleichung der Oberflächenschicht*, Z. Phys. Chem. 116, 466–484, DOI https://doi.org/10.1515/zpch-1925-11629. Original scan: https://elchi.eu/pdf/frumkin/2-article/1914-1930/2-1-1925-29-zpc-Frumkin.pdf. Printed pp. 467–468 define surface coverage and derive the dilute Gibbs/Langmuir baseline; the exact non-ideal interaction equation still needs transcription.
- Frumkin (1925), *Einige Bemerkungen zur Theorie der Adsorption und Verteilung*, Z. Phys. Chem. 116, 501–503, DOI https://doi.org/10.1515/ZPCH-1925-11632; bibliographic confirmation: https://www.elch.chem.msu.ru/wp3/index.php/ru/articles/frumkinarticles/.
- Frumkin (1926), *The Influence of the Electric Field on the Adsorption of Neutral Molecules*, Z. Phys. 35, 792–802; a distinct field-dependent adsorption paper, not the original 1925 isotherm source: https://www.nature.com/articles/117790a0
- Later technical treatment of Frumkin equation of state and isotherm derivation: https://studylib.net/doc/26249563/yuliy-d.-gamburg--giovanni-zangari--auth.----theory-and-p...
- Frumkin & Obrutsheva (1926), electric-field dependence of adsorption: https://doi.org/10.1038/117790a0
- Langmuir (1918), primary ideal adsorption source: https://doi.org/10.1021/ja02242a004
- Marcus (1956), primary electron-transfer theory; full PDF directly verifies Eq. 7–8 (printed p. 969), Eq. 44 (p. 975), and Eq. 47 (p. 976): the conditional solution-rate approximation is \(k_{bi}\cong k_1=Z\exp(-\Delta F^*/kT)\), with \(Z\) the solution collision number. https://doi.org/10.1063/1.1742723; accessible full-text PDF: https://www.researchgate.net/profile/Rudolph-Marcus/publication/234932363_On_the_Theory_of_Oxidation-Reduction_Reactions_Involving_Electron_Transfer_I/links/56a232e808ae24f62705e226/On-the-Theory-of-Oxidation-Reduction-Reactions-Involving-Electron-Transfer-I.pdf
- Caltech repository record and attached original paper PDF: https://authors.library.caltech.edu/records/desqy-fmq55
- IUPAC Marcus equation, prefactor and barrier definition: https://goldbook.iupac.org/terms/view/M03702
- Butler (1924), *Studies in heterogeneous equilibria, Part III*: https://doi.org/10.1039/TF9241900734
- Erdey-Grúz & Volmer (1930), *Zur Theorie der Wasserstoffüberspannung*, original 8-page scan (Eqs. 7–8, 13–17; printed pp. 209–212): https://knowledge.electrochem.org/estir/hist/hist-34-Volmer-1.pdf
- DOI record: https://doi.org/10.1515/zpch-1930-15020
- Dickinson & Wain, historical and equation-form review of Butler–Volmer: https://www.sciencedirect.com/science/article/pii/S1572665720303283
- Equation-level Frumkin isotherm and surface equation of state: https://pmc.ncbi.nlm.nih.gov/articles/PMC5686271/
- Interfacial adsorption isotherm comparison: https://pure.rug.nl/ws/portalfiles/portal/3086148/c3.pdf

No formal catalogue equation entry was added or accepted by this audit.

## 4B. Real (1977) functional-response full-text retrieval check

A search hit previously surfaced as a possible full-text copy of Real's *The Kinetics of Functional Response*. Opening it revealed that the PDF is actually Harvey J. Gold's 1978 *Biosystems Modeling* proceedings/mimeograph volume; its page 120 reproduces only the Real article abstract. It is not the 1977 article and contains no equation transcription. Do not cite that PDF as the Real primary text. The publisher's article record confirms pages 289–300 and the abstract's three-parameter encounter-history description (maximum feeding rate \(F\), affinity \(G\), encounter number \(n\)), but the full equation and page remain unverified. Retain Real as a high-priority source lead, not an equation-ready candidate, until the original article text is obtained.
