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

## Acceptance boundary

No equation is promoted to entries. The candidate source map does not establish 59 structurally distinct Chemistry equations, nor 59 independent statistical units. Each eventual entry still requires an exact source location, formula transcription, assumptions, units, validity ranges, source-family ID, equivalence review, and a defensible deterministic benchmark mapping. If the Chemistry stratum cannot supply the required independent units, report the shortfall rather than pad the catalogue.
