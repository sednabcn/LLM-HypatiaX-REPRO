# Core-295 Biology stock–recruitment family source audit 1

**Date:** 2026-11-11  
**Status:** source-lineage and structural-family screen; no equation accepted.

## 1. New source records

Four Biology references were added:

- Beverton & Holt (1957), *On the Dynamics of Exploited Fish Populations*, primary monograph.
- Ricker (1954), “Stock and Recruitment,” primary article.
- Deriso (1980), “Harvesting Strategies and Parameter Estimation for an Age-Structured Model,” primary article.
- Schnute (1985), “A General Theory for Analysis of Catch and Effort Data,” primary article.

The catalogue source register now has 163 records: Chemistry 32, Biology 34, Physics 43, DeFi AMM 23, DeFi Risk 31. These are source records, not equation entries.

## 2. Structural finding: do not count Beverton–Holt and Ricker as independent equations

The stock–recruitment pool contains a family-level dependency that must be made explicit. A published synthesis reports the generalized Deriso–Schnute form

[
R_t=\alpha S_t(1-\gamma\beta S_t)^{1/\gamma}
]

and gives the Ricker form as the (\gamma\to0) limit and the Beverton–Holt form at (\gamma=-1). A separate stock-assessment reference likewise describes the classical Ricker and Beverton–Holt relations as special cases of a generalized three-parameter recruitment model. This is a strong E2 family relationship under the current *draft* policy: the two named models must not be counted as independent from the generalized parent solely because they use different parameterizations or limits. See the secondary equation-level cross-checks at [ICES Journal of Marine Science (2014)](https://academic.oup.com/icesjms/article/71/8/2307/2804451) and [FAO stock–recruitment chapter](https://www.fao.org/4/x9026e/x9026e0b.htm).

**Important provenance qualification:** the new Deriso (1980) and Schnute (1985) records establish the primary model lineage, but this pass has not yet verified the exact generalized recruitment equation and its page directly in both primary papers. The equation above is therefore a secondary-source transcription for discovery and family screening, not a primary-source-verified candidate record.

## 3. Scope and model-unit cautions

- A stock–recruitment function (R=f(S)) is a one-generation recruitment relation, not by itself a full population-dynamics recurrence or an age-structured assessment system.
- A delay-difference or age-structured population model has state, survival, growth, recruitment timing and observation components. It must be represented as a complete model/system, not split into a recruitment function plus arbitrary output equations and counted several times.
- The Ricker and Beverton–Holt formulas are both empirical/mechanistic stock–recruitment relationships with different density-dependent response shapes. Their different curve shapes do not override their reported generalized-family relationship under E2.
- The 1957 Beverton–Holt monograph is catalogued through a bibliographic record; the exact original equation page has not yet been transcribed from a scanned primary copy.
- The current 59-per-domain target must not motivate counting the two special cases separately.

## 4. Provisional disposition

| Candidate/model | Source status | Structural screen | Next action |
|---|---|---|---|
| Beverton–Holt stock–recruitment | Primary monograph registered; page not yet transcribed | E2 special case of generalized Deriso–Schnute form | Inspect primary monograph's recruitment chapter and equation page |
| Ricker stock–recruitment | Primary article registered | E2 limit of generalized Deriso–Schnute form | Transcribe original equation/context and density-dependent assumptions |
| Deriso–Schnute generalized recruitment relation | Primary lineage papers registered; equation transcription not yet confirmed directly | Potential parent family; not yet a catalogue entry | Verify exact equation, parameter restrictions and biological derivation in Deriso/Schnute primary texts |
| Full age-structured/delay-difference population system | Primary Deriso/Schnute sources registered | Separate complete model class from scalar recruitment function, but must preserve full state and observation structure | Reconstruct one complete system with explicit state, timing, survival, growth and observation equations |

No formal catalogue entry was added or promoted. No generator, range, independent statistical unit or accepted status is claimed.

## 5. Sources

- Beverton & Holt (1957): https://books.google.com/books/about/On_the_Dynamics_of_Exploited_Fish_Popula.html?id=1JntoCImKC8C
- Ricker (1954): https://doi.org/10.1139/f54-039
- Deriso (1980): https://doi.org/10.1139/F80-034
- Schnute (1985): https://doi.org/10.1139/f85-057
- Secondary equation/family cross-check: https://academic.oup.com/icesjms/article/71/8/2307/2804451
- FAO stock–recruitment family summary: https://www.fao.org/4/x9026e/x9026e0b.htm
