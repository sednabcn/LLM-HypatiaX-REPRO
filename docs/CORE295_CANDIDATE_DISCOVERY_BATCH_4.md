# Core-295 candidate discovery batch 4: Chemistry source-map expansion

**Status:** discovery and provenance leads only. No equation is approved, accepted, or counted toward the 59 Chemistry target. The catalogue remains draft.

## Scope

This pass broadens the Chemistry source universe beyond the integrated rate-law examples in batch 1. It maps four underrepresented strata: chemical equilibrium; acid–base equilibria; solubility/complexation; and thermodynamics/electrochemistry. It also records solution non-ideality through ionic activities.

| Stratum | Source lead | Candidate coverage | Review boundary |
|---|---|---|---|
| Chemical equilibrium | Guldberg & Waage (1864), “Studies concerning affinity”; English translation in *J. Chem. Educ.* (1986), [DOI](https://doi.org/10.1021/ed063p1044) | Historical mass-action formulation and chemical affinity | Translation metadata is 1986, not the original 1864 publication. Trace exact original equation and assumptions; equilibrium-constant expressions sharing one stoichiometric mass-action law form one family. |
| Equilibrium conventions | IUPAC Gold Book, [equilibrium constant](https://doi.org/10.1351/goldbook.E02177) | Pressure-, fugacity-, concentration-, molality- and activity-based equilibrium constants | These are thermodynamic conventions/representations, not automatically distinct mechanisms. State standard state, activities and units explicitly. |
| Acid–base equilibria | OpenStax Chemistry 2e, Chapter 14: [Acid-Base Equilibria](https://chem.libretexts.org/Bookshelves/General_Chemistry/Chemistry_2e_%28OpenStax%29/14%3A_Acid-Base_Equilibria) | Weak-acid/base equilibria, salt hydrolysis, polyprotic systems, buffers and titration curves | Henderson–Hasselbalch is a Core-15 exclusion. Do not reintroduce it as buffer capacity, rearranged pH or a titration special case. Other acid/base equations need distinct derivation and exact source locations. |
| Solubility and complexation | OpenStax Chemistry 2e, Chapter 15: [Precipitation and Dissolution](https://openstax.org/books/chemistry-2e/pages/15-1-precipitation-and-dissolution) and [Chapter 15 summary](https://openstax.org/books/chemistry-2e/pages/15-summary) | Solubility products, precipitation thresholds, formation/dissociation constants, coupled dissolution and complex formation | Ksp, Qsp and formation constants are equilibrium expressions within related mass-action frameworks. Cluster by reaction stoichiometry/derivation; do not count simple rearrangements or reaction reversals as new independent units. |
| Ionic non-ideality | IUPAC Gold Book, [Debye–Hückel equation](https://doi.org/10.1351/goldbook.D01534) | Ionic activity coefficients as a function of charge and ionic strength | Distinct solution-property relation, but the Gold Book definition cites a later convention. Verify original Debye–Hückel derivation, limiting-law form, solvent/temperature constants and dilute-solution validity before considering acceptance. |
| Thermodynamics | OpenStax Chemistry 2e, Chapter 16: Thermodynamics | Entropy, spontaneity, Gibbs free energy and chemical-potential/equilibrium relationships | Related identities such as ΔG = ΔH − TΔS and ΔG° = −RT ln K are not automatically independent. Treat as a thermodynamic derivation family and specify standard/nonstandard state. |
| Electrochemistry | OpenStax Chemistry 2e, Chapter 17: Electrochemistry | Cell potential, free-energy/equilibrium links and electrochemical response | Nernst equation already appears in batch 1; do not count a rearrangement, concentration form or equivalent cell notation as a new family. Other electrochemical candidates require exact equation and standard-state provenance. |

## Source-universe additions

The consolidated bibliography now includes four additional Chemistry records (items 54–57): the Guldberg–Waage mass-action translation, IUPAC equilibrium-constant definition, IUPAC Debye–Hückel definition, and OpenStax Chemistry 2e Chapters 13–17. The JSON source register adds corresponding Chemistry records. All remain candidate references only.

## Core-15 overlap and family controls

- **Henderson–Hasselbalch:** explicitly excluded. Buffer equations that reduce to this relation do not evade the exclusion by changing notation or solving for a different variable.
- **Arrhenius:** explicitly excluded. Temperature dependence of equilibrium constants (van ’t Hoff relation) is conceptually distinct from Arrhenius rate dependence, but must be reviewed carefully for source lineage and not mislabelled as a rate-law variant.
- **Rate Law:** integrated zero-, first- and second-order forms from batch 1 remain grouped as one kinetics family; no quota inflation from order-specific algebraic forms.
- **Nernst:** already present in batch 1; electrochemical potential and free-energy forms linked by ΔG = −nFE must be clustered pending structural review.
- **Ideal Gas Law:** excluded. Gas-phase equilibrium expressions may use partial pressures/fugacities, but the ideal-gas equation itself is not a candidate.
- **Thermodynamic identities:** algebraic rearrangements, standard-state conversions and equivalent expressions for the same state function are not independent equations.

## Candidate families worth investigating next

1. **Mass-action equilibrium and reaction quotients:** one general stoichiometric family; specific chemical systems may be useful as examples but not independent units by default.
2. **Acid–base speciation:** polyprotic distribution fractions and charge-balance systems may provide distinct coupled nonlinear structures, but their equations and domain assumptions must be sourced and compared before inclusion.
3. **Solubility/complexation:** conditional solubility under common-ion, pH or ligand coupling is promising as a coupled-equilibrium family; avoid counting Ksp rearrangements separately.
4. **Ionic activity:** Debye–Hückel limiting/general forms and extensions are one solution non-ideality lineage unless a principled source-family split is justified.
5. **Thermodynamic equilibrium:** van ’t Hoff temperature dependence and Gibbs-energy/equilibrium relations are promising source leads, but require primary-source verification and careful separation from kinetics.


## Additional equation-level source tracing (not yet accepted)

| Candidate family | Source and evidence | What it adds | Required review |
|---|---|---|---|
| Polyprotic acid distribution fractions | King & Kester (1990), [DOI](https://doi.org/10.1021/ed067p932); Tissue (2013), [Chapter 6](https://doi.org/10.1002/9781118647042.ch6) | General speciation equations and alpha-fraction plots for multiple protonation states; cases include amphiprotic species | Derive the distribution fractions from sequential dissociation equilibria and mass balance. The family is a coupled mass-action/speciation system; buffer-capacity formulas that collapse to Henderson–Hasselbalch are excluded. Record pH/activity assumptions and limiting approximations. |
| Ionic activity coefficients | Debye & Hückel (1923), *Zur Theorie der Elektrolyte II*, [original issue scan](https://www.pdf-archive.com/2020/01/07/untitled-pdf-document-9/); publisher metadata for Debye’s 1923 electrolyte-osmotic-pressure paper [here](https://doi.org/10.1002/recl.19230420711) | Historical primary theoretical basis for ionic non-ideality; limiting-law family relates log activity coefficient to charge and square-root ionic strength | The accessible original scan is a third-party archive, so confirm volume/page metadata from a library or publisher source before formal citation. The limiting law and extended Debye–Hückel equations are one lineage, not multiple independent candidates. |
| Temperature dependence of equilibrium | van ’t Hoff (1885), *L’équilibre chimique dans les systèmes gazeux ou dissous à l’état dilué*; [contents/translation record](https://chg.kncv.nl/l/library/download/urn%3Auuid%3A756b7abc-d782-42ee-ae70-c038cdb2ff08/van--t-hoff---chemical-thermodynamics--contents-.pdf?ext=.pdf&format=save_to_disk) | Original chapter-level source for equilibrium at variable temperature in dilute systems; modern integrated van ’t Hoff form appears in later teaching derivations | Keep distinct from Arrhenius rate dependence, but do not count alternative integrated/differential forms separately. State constant reaction enthalpy and dilute-solution assumptions; inspect original pages before transcribing. |
| Conditional solubility under complexation | Christian, Dasgupta & Schug (2014), *Analytical Chemistry* (7th ed.), Chapter 11.3 | Conditional solubility product under ligand complexation, including silver bromide/ammonia as a worked coupled-equilibrium example | The conditional Ksp is a derived aggregate of Ksp and formation constants, not a new independent equilibrium law. Could be a useful coupled deterministic mapping if species balances and ligand conditions are explicitly specified. |

These leads strengthen the Chemistry source universe but are not equivalent to a verified formula catalogue. For example, the analytical-chemistry worked example supplies a coupled species balance and conditional-solubility mapping, while the polyprotic-acid sources identify alpha-fraction formulations; exact equation/page extraction remains outstanding.


## Additional exact equation lead: gas–liquid solubility

**Henry’s law (OpenStax Chemistry 2e, §11.3):** the source gives the proportional relation

\[C_g = k P_g\]

where dissolved-gas concentration is proportional to the gas partial pressure above the liquid; the proportionality constant depends on gas identity, solvent identity and temperature. The source's worked example uses (k=C_g/P_g), so this record must preserve that convention and units (e.g. mol L⁻¹ kPa⁻¹ or mol L⁻¹ atm⁻¹). [Exact section and equation](https://openstax.org/books/chemistry-2e/pages/11-3-solubility#fs-idm169453760).

**Core-15 and family screen:** Henry’s law is not the Ideal Gas Law: it maps gas partial pressure to dissolved concentration in a liquid. It is a plausible distinct chemistry relation, but its accepted domain must be restricted to conditions where the proportional law is valid. Reactive dissolution (e.g. ammonia reacting with water), non-dilute solutions and pressure/temperature-dependent constants require a different coupled-equilibrium or nonideal model. Henry-constant conventions vary between sources (some define the reciprocal), so the equation and units—not the name alone—must define the catalogue record.

**Related equilibrium equations:** OpenStax §15 summary gives (K_{sp}) as the activity/concentration product for a dissolution stoichiometry and identifies formation/dissociation constants and coupled equilibria. Those are useful source-backed mechanisms, but (K_{sp}), (K_f), and (K_d) are instances of the same general mass-action framework; count only genuinely different coupled-system structures after review, not every equilibrium constant as a separate independent equation. [Chapter 15 summary](https://openstax.org/books/chemistry-2e/pages/15-summary).

**Thermodynamic/electrochemical linkage:** OpenStax §16.4 states (G=H-TS), ΔG=ΔH-TΔS and ΔG°=−RT ln K; §17.4 links ΔG°=−nFE°cell. These identities are linked state-function/electrochemical relations, and the last is connected to the Nernst/electrochemical family already listed in batch 1. Do not count these as independent equations by rearrangement. Exact source sections: [§16.4](https://openstax.org/books/chemistry-2e/pages/16-4-free-energy) and [§17.4](https://openstax.org/books/chemistry-2e/pages/17-4-potential-free-energy-and-equilibrium).


## Additional Chemistry strata: adsorption and molecular transport

| Family | Primary source | Candidate relation and scope | Review boundary |
|---|---|---|---|
| Gas adsorption at a surface | Langmuir (1918), [JACS DOI](https://doi.org/10.1021/ja02242a004), *The adsorption of gases on plane surfaces of glass, mica and platinum* | Surface coverage as a saturating function of gas pressure; the paper is the primary source lineage for the Langmuir isotherm | Verify the original equation and page. State assumptions about equivalent independent sites, monolayer coverage and adsorption/desorption equilibrium. Do not treat linearized/rearranged Langmuir forms as separate candidates; distinguish later heterogeneous/multilayer isotherms by mechanism and source. |
| Molecular diffusion | Fick (1855), [Annalen der Physik DOI](https://doi.org/10.1002/andp.18551700105), *Ueber Diffusion* | Concentration-gradient-driven diffusive transport; the original work is the primary source lineage for Fickian diffusion | The constitutive flux law and its conservation-derived diffusion PDE are linked levels of one model family. Specify coordinate, geometry, diffusivity, concentration units, and boundary/initial conditions. Avoid treating 1-D/2-D/3-D or constant/variable diffusivity variants as automatically independent. |

These additions broaden Chemistry into interfacial phenomena and transport. They are not substitutes for exact formula transcription, dimensional checks, regime checks or source-family review.


## Additional exact equation lead: ideal-solution vapor pressure

**Raoult’s law (Raoult, 1887; OpenStax Chemistry 2e, §11.4):** for component \(A\) in an ideal liquid solution, the partial vapor pressure is \(P_A=X_A P_A^*\), where \(X_A\) is the liquid-phase mole fraction and \(P_A^*\) is the pure-component vapor pressure at the same temperature. For a multicomponent ideal solution, the total vapor pressure is the sum of component partial pressures.

**Primary-source trail:** Raoult, F.-M. (1887), “Loi générale des tensions de vapeur des dissolvants,” *Comptes Rendus* 104, 1430–1433. A bibliographic record confirms the original journal and page range; the accessible OpenStax section gives the explicit equation and ideal-solution condition. The original paper’s precise equation wording and empirical scope still require page-level verification before formal acceptance.

**Core-15 and family screen:** this is distinct from Henry’s law: Raoult relates a liquid component’s vapor pressure to its liquid mole fraction, whereas Henry relates dissolved-gas concentration to gas partial pressure in the applicable dilute regime. Keep Raoult’s law as one ideal-solution vapor-pressure family. Do not count each component, total-pressure summation, solvent-only special case, or algebraic rearrangement as a separate equation. Nonideal mixtures require activity/fugacity treatment; do not silently apply the ideal relation outside its validity regime.

## Acceptance boundary

No equation is promoted to entries. The candidate source map does not establish 59 structurally distinct Chemistry equations, nor 59 independent statistical units. Each eventual entry still requires an exact source location, formula transcription, assumptions, units, validity ranges, source-family ID, equivalence review, and a defensible deterministic benchmark mapping. If the Chemistry stratum cannot supply the required independent units, report the shortfall rather than pad the catalogue.
