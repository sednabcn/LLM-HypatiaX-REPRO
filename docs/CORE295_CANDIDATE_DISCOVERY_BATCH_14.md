# Core-295 candidate discovery batch 14: Biology saturation kinetics and ligand binding

**Status:** primary-source equation tracing only. No equation is accepted or counted toward the 59 Biology target.

## 1. Michaelis–Menten enzyme kinetics (1913)

**Primary source:** Michaelis & Menten, “Die Kinetik der Invertinwirkung,” *Biochemische Zeitschrift* 49 (1913), 333–369. A complete modern translation and historical analysis is available in [Johnson & Goody (2011)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3381512/).

The initial-rate relation in the translation is:

\[
v=C\Phi\frac{[S]}{[S]+K_S}
=V_{max}\frac{[S]}{[S]+K_S},
\]

where \(C\Phi=V_{max}\), \(\Phi\) is total enzyme concentration and \(K_S\) is the substrate dissociation constant in the original rapid-equilibrium model. The original paper explicitly models \(E+S\rightleftarrows ES\rightarrow E+P\), assumes the enzyme-substrate complex is at equilibrium with substrate, and takes the reaction rate proportional to \([ES]\).

The full original time-course analysis also accounts for competitive product inhibition by glucose and fructose:

\[
v=\frac{C[S]}{[S]+K_S(1+[F]/K_F+[G]/K_G)}.
\]

**Important historical distinction:** the 1913 paper's \(K_S\) is an equilibrium dissociation constant under the authors' rapid-equilibrium assumption. The later Briggs–Haldane steady-state derivation yields the modern Michaelis constant \(K_m=(k_{-1}+k_{cat})/k_1\). These are not generally identical. Do not silently retrofit the later assumption onto the original paper.

## 2. Hill cooperative oxygen binding (1910)

**Primary source:** A. V. Hill, “The possible effects of the aggregation of the molecules of haemoglobin on its dissociation curves,” *The Journal of Physiology* 40 (1910), iv–vii, DOI [10.1113/jphysiol.1910.sp001386](https://doi.org/10.1113/jphysiol.1910.sp001386).

The original empirical relation is commonly transcribed as:

\[
y=100\frac{Kx^n}{1+Kx^n},
\]

where \(y\) is percent hemoglobin saturation, \(x\) is oxygen partial pressure, \(K\) is an apparent association parameter and \(n\) is the Hill coefficient. Hill introduced \(n\) as an average apparent aggregation/cooperativity descriptor. It is not generally a literal reaction stoichiometry or a direct count of binding sites.

**Boundary:** the equation is phenomenological and assumes a fixed cooperativity exponent. It is not a mechanistic sequential-binding model. Keep percentage and fractional-saturation conventions distinct but do not count them separately.

## 3. Adair four-step oxygen-binding polynomial (1925)

**Primary source:** G. S. Adair, “The hemoglobin system: VI. The oxygen dissociation curve of hemoglobin,” *Journal of Biological Chemistry* 63(2) (1925), 529–545, DOI [10.1016/S0021-9258(18)85018-9](https://doi.org/10.1016/S0021-9258(18)85018-9).

The four-step binding-polynomial form, as transcribed in a modern centenary review, is:

\[
Y=
\frac{\tfrac14K_1x+\tfrac12K_2x^2+\tfrac34K_3x^3+K_4x^4}
{1+K_1x+K_2x^2+K_3x^3+K_4x^4},
\]

where \(x\) is oxygen partial pressure and \(K_1,\ldots,K_4\) are apparent macroscopic equilibrium constants for sequential occupancy. The coefficients \(1/4,1/2,3/4,1\) represent fractional site occupancy across the four bound states.

**Provenance boundary:** the displayed formula is cross-checked against the 2025 centenary review of Adair's equation; its exact page/equation number in the 1925 primary paper remains to be verified. Adair's four-step binding polynomial is structurally richer than Hill's two-parameter empirical curve, but both are in the hemoglobin oxygen-binding source cluster and are not automatically independent statistical units.

## 4. Monod substrate-limited bacterial growth (1949)

**Primary source:** Jacques Monod, “The growth of bacterial cultures,” *Annual Review of Microbiology* 3 (1949), 371–394, DOI [10.1146/annurev.mi.03.100149.002103](https://doi.org/10.1146/annurev.mi.03.100149.002103).

The familiar substrate-limited specific-growth relation is:

\[
\mu(S)=\mu_{max}\frac{S}{K_S+S},
\]

with specific growth rate \(\mu\), limiting-substrate concentration \(S\), maximum specific growth rate \(\mu_{max}\) and half-saturation constant \(K_S\). Later microbial-kinetics reviews print this form and cite Monod (1949); the original article's exact equation/page mapping is still outstanding in this pass.

**Overlap:** this is algebraically the same hyperbolic saturation form as Michaelis–Menten, with different biological interpretation and units. Do not count Monod and Michaelis–Menten as two structurally distinct equations merely because one describes population growth and the other enzyme velocity. A chemostat adds dilution, biomass and substrate mass-balance ODEs; that coupled system is a separate model structure and needs its own primary-source tracing.

## 5. Source-family and Core-15 overlap controls

- Michaelis–Menten initial-rate, competitive product-inhibition and integrated progress-curve equations are linked by the same enzyme-substrate model; do not count the reciprocal Lineweaver–Burk plot or variable rearrangements separately.
- The MM and Monod hyperbolic functions have the same mathematical form. Treat them as one saturation-kinetics family for structural uniqueness, even though the biological contexts differ.
- Hill and Adair describe hemoglobin oxygen binding. Hill is a phenomenological two-parameter cooperativity curve; Adair is a four-step binding polynomial. Keep their mathematical structures distinct but cluster the common protein/ligand source lineage.
- Hill coefficient values, oxygen-pressure units, fractional versus percentage saturation and algebraic linearizations are not separate equations.
- Enzyme inhibition variants (competitive, uncompetitive, noncompetitive, product inhibition) are linked kinetic mechanisms; they need a mechanistic family review before any split.
- Logistic population growth remains a Core-15 exclusion. Monod substrate limitation is not logistic growth, but its hyperbolic rate form overlaps Michaelis–Menten and must not be counted as an independent structural family.

## Acceptance requirements

For enzyme kinetics, record enzyme/substrate/product definitions, initial-rate or progress-curve regime, pH, temperature, inhibition assumptions and concentration units. For microbial growth, specify the limiting substrate, biomass state, dilution/chemostat conditions, yield and maintenance terms. For oxygen binding, specify pO2, temperature, pH, 2,3-DPG and saturation convention. Verify every exact equation against the primary source before promotion.

All records remain candidates. No Biology entry is accepted; no experiment or workflow has been run.
