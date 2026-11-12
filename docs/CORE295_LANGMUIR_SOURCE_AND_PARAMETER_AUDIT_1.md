# Core-295 Langmuir candidate: primary-source and parameter audit 1

**Candidate:** `CHEM-LANGMUIR-001`  
**Date:** 2026-11-12  
**Disposition:** source mapping correction required; no parameter values or ranges populated

## Primary source inspected

Irving Langmuir, “The Adsorption of Gases on Plane Surfaces of Glass, Mica and Platinum,” *Journal of the American Chemical Society* 40(9), 1361–1403 (1918), DOI 10.1021/ja02242a004. A complete 43-page scan was inspected at the Colorado State University-hosted PDF.

Relevant printed pages and PDF pages:
- Printed p. 1368 (PDF page index 7): scope and limiting-case assumptions; simple adsorption is defined for a plane surface with one kind of elementary space, each holding one molecule.
- Printed p. 1369 (PDF page index 8): kinetic derivation. The molecular impingement rate is proportional to gas pressure (Eq. 3); equilibrium balances adsorption on vacant sites and evaporation from occupied sites (Eq. 4); the fractional coverage is then expressed in terms of the impingement-rate variable (Eq. 7).
- Printed p. 1370 (PDF page index 9): conversion from fractional coverage to amount adsorbed per unit area and the limiting low-/high-pressure interpretations.
- Printed pp. 1371–1375 (PDF page indices 10–14): distinct extensions for multiple site types, amorphous surfaces, multiple molecules per site, atomic adsorption and multilayer adsorption. These are not interchangeable with the single-site formula.
- Printed pp. 1376 onward (PDF page indices 15 onward): experimental methods and results. The experimental systems are specific gas/surface/temperature combinations, not a universal adsorption dataset.

## Formula and notation correction

The catalogue's expression
\[
\theta=\frac{u_1 p}{1+u_1p}
\]
is a pressure-parameterized form. In the original derivation, the symbol entering the coverage equation is the molecular impingement-rate variable, which Langmuir explicitly relates to gas pressure through kinetic theory in Eq. (3). Langmuir defines the corresponding coefficient from the adsorption fraction and the saturated-surface evaporation rate immediately before Eq. (7).

Consequently, the pressure-based coefficient in the catalogue is an effective coefficient that absorbs the pressure-to-impingement conversion (and the selected temperature/gas convention). It should not be described as simply the original kinetic ratio without documenting that conversion. Its units are inverse pressure only after this reparameterization.

**Required record correction before source verification:** distinguish (a) Langmuir's original impingement-rate variable and kinetic coefficient from (b) the effective pressure-form coefficient used in the modern isotherm. Record the chosen pressure units, gas identity, temperature convention and coefficient definition consistently. The original source's Eq. (7), not Eqs. (8)–(9), is the direct fractional-coverage expression; Eq. (9) concerns amount adsorbed.

## Parameter and range decision

No universal numerical value for the pressure-form coefficient follows from the equation or the source's derivation. It depends on the gas/surface pair and temperature. The paper reports experimental systems and temperature conditions, but the inspected evidence does not establish a single fitted coefficient and a clean, common rectangular pressure interval suitable for this benchmark record.

Do not populate `fixed_parameter_values`, `input_ranges`, or `input_validity_bounds` from arbitrary textbook examples or by inventing a generic positive coefficient. A defensible benchmark instance would need one explicitly selected gas/surface/temperature dataset, a source-grounded fitted coefficient (or source-reported kinetic parameters transformed with units), and a predeclared train/extrapolation split. The source's low-pressure and saturation asymptotes are qualitative regimes, not numeric cutoffs.

## Structural and scope cautions

The original paper explicitly treats several different adsorption mechanisms and surface structures. The present candidate is only the single-site, one-molecule-per-site, homogeneous-site limiting case. The paper itself warns against expecting one equation to describe all adsorption phenomena. Any future candidates from its multiple-site, amorphous, atomic, or multilayer cases need full model-level and source-family review; they must not be counted as cosmetic parameter variants.

## Disposition

- Keep candidate status `proposed`.
- Keep generator `pending_benchmark_contract`.
- Keep fixed parameter values and input ranges unset.
- Correct source location to the direct coverage expression, Eq. (7), printed p. 1369; distinguish it from the amount-adsorbed equation.
- No tests, validators, scripts, data generation, or experiments were run.

## Source

- Langmuir (1918), complete scan: https://diverdi.colostate.edu/C431/experiments/surface_area_of_solids/references/j_acs_1918_v40_p1361.pdf
- ACS publisher record: https://doi.org/10.1021/ja02242a004
- Zenodo deposited article record: https://zenodo.org/records/1429050
