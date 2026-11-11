# Core-295 candidate discovery batch 15: Chemistry spectroscopy and surface/electrode kinetics

**Status:** primary-source tracing and modern derivation cross-check only. No equation is accepted or counted toward the 59 Chemistry target.

## 1. Beer absorption law (1852) and modern Beer–Lambert notation

**Primary source:** August Beer, “Bestimmung der Absorption des rothen Lichts in farbigen Flüssigkeiten,” *Annalen der Physik* 162(5) (1852), 78–88, DOI [10.1002/andp.18521620505](https://doi.org/10.1002/andp.18521620505).

The absorption relation is exponential in optical path and absorber concentration. In modern spectroscopic notation it is commonly written:

\[
A=\log_{10}\left(\frac{I_0}{I}\right)=\varepsilon c\ell,
\qquad
I=I_0,10^{-\varepsilon c\ell}.
\]

Here \(I_0\) and \(I\) are incident/transmitted intensities, \(c\) is concentration, \(\ell\) is path length and \(\varepsilon\) is the decadic molar absorption coefficient under the stated unit convention.

**Historical boundary:** Beer (1852) extended the earlier exponential absorption law; the modern combined name and molar-absorptivity notation should not be projected verbatim onto the 1852 paper. Bouguer's earlier work and Lambert's photometric treatment are part of the lineage. Verify the original paper's exact variables and logarithm convention before accepting a transcription.

**Overlap:** absorbance, transmittance, base-10 exponential attenuation and natural-log attenuation are equivalent representations of one optical attenuation family. Do not count them separately.

## 2. Erdey-Grúz–Volmer / Butler–Volmer electrode kinetics

**Primary sources and historical attribution:**
- Butler (1924), Part II, “The kinetic interpretation of the Nernst theory of electromotive force,” *Transactions of the Faraday Society* 19, 729–733, DOI [10.1039/TF9241900729](https://doi.org/10.1039/TF9241900729).
- Butler (1924), Part III, “A kinetic theory of reversible oxidation potentials at inert electrodes,” pp. 734–739, DOI [10.1039/TF9241900734](https://doi.org/10.1039/TF9241900734).
- Erdey-Grúz & Volmer (1930), “Zur Theorie der Wasserstoff Überspannung,” *Zeitschrift für Physikalische Chemie* 150A, 203–213, DOI [10.1515/zpch-1930-15020](https://doi.org/10.1515/zpch-1930-15020).

The generalized modern current-overpotential relation is commonly written:

\[
j=j_0\left[
\exp\left(\frac{\alpha_a nF\eta}{RT}\right)
-
\exp\left(-\frac{\alpha_c nF\eta}{RT}\right)
\right],
\]

where \(j\) is current density, \(j_0\) exchange current density, \(\eta\) overpotential, \(n\) electron number, \(F\) Faraday constant, \(R\) gas constant, \(T\) absolute temperature and \(\alpha_a,\alpha_c\) anodic/cathodic transfer coefficients. Some conventions impose \(\alpha_a+\alpha_c=1\); do not assume this without specifying the elementary mechanism and parameter convention.

**Historical boundary:** Butler's 1924 papers treated kinetic interpretations of the Nernst equilibrium but did not by themselves derive the complete generalized current-overpotential law. Erdey-Grúz and Volmer's 1930 work developed the reversible anodic/cathodic kinetic treatment for the hydrogen overpotential reaction. The generalized law is a historical synthesis; cite all relevant primary sources rather than attributing the full modern expression to Butler alone.

**Overlap:** the Tafel equation is an asymptotic one-direction/high-overpotential approximation of the exponential current relation. It is not an independent equation family. The Nernst equation describes equilibrium potential and remains distinct from the kinetic current-overpotential relation.

## 3. Langmuir–Hinshelwood surface-reaction rate expression

**Primary historical source trail:** Langmuir, “Heterogeneous reactions,” *Transactions of the Faraday Society* 17 (1922), 607–620, DOI [10.1039/TF9221700607](https://doi.org/10.1039/TF9221700607); Hinshelwood & Prichard, “The relation of homogeneous to catalysed reactions: The catalytic decomposition of hydrogen iodide on the surface of gold,” *J. Chem. Soc., Trans.* 127 (1925), 1552–1559, DOI [10.1039/CT9252701552).

A modern explicit competitive-adsorption derivation is given by Wachs (2024), [ACS Catalysis](https://doi.org/10.1021/acscatal.4c02813), Eq. 5. For two reactants \(R_1,R_2\) adsorbing competitively on single sites and reacting through a rate-limiting surface step:

\[
r=
\frac{
k_{rds}K_{R_1}K_{R_2}P_{R_1}P_{R_2}[\ast]_0^2
}{
(1+K_{R_1}P_{R_1}+K_{R_2}P_{R_2})^2
}.
\]

The denominator is the squared site-balance term; the numerator contains the product of adsorption factors and total site density. This expression assumes adsorption/desorption equilibria, equivalent independent sites, competitive adsorption, and a bimolecular reaction between adsorbed species as the rate-determining step.

**Boundary:** this is one specific Langmuir–Hinshelwood mechanism, not a universal surface-reaction law. Unimolecular surface reactions, Eley–Rideal reactions, dissociative adsorption, multisite ensembles, lateral interactions and diffusion limitations produce different rate expressions. The Langmuir adsorption isotherm and the resulting surface reaction law are linked; do not count adsorption coverage, site balance, rate expression and algebraic rearrangements as independent candidates.

## Cross-family and Core-15 controls

- Beer absorption is an optical attenuation law and is distinct from Henry/Raoult solubility, but its absorbance/transmittance/logarithm variants are one family.
- Butler–Volmer kinetics is distinct from the Nernst equilibrium-potential relation. Tafel slopes and limiting-current approximations are linked regimes, not independent equations.
- Historical attribution of Butler–Volmer requires care: Butler 1924, Erdey-Grúz–Volmer 1930 and Butler 1932 are distinct contributions; the full modern expression should not be assigned to a single paper without source-level verification.
- Langmuir–Hinshelwood rates depend on the Langmuir adsorption/site-balance assumptions. The rate-law variants are grouped by surface mechanism, not counted per substrate or catalyst.
- Arrhenius remains a Core-15 exclusion. Do not count temperature dependence of \(k_{rds}\) as a new equation family.
- The Chemistry mass-action and adsorption source clusters must be preserved; no linearization, unit conversion, logarithmic form or parameter substitution creates a new structural equation.

## Acceptance requirements

For Beer absorption, specify wavelength, optical path, solvent, concentration units and decadic/natural-log convention. For electrode kinetics, specify reaction, electron number, overpotential reference, transfer coefficients, exchange current density, temperature and mass-transfer limitations. For surface kinetics, specify adsorption mechanism, site balance, catalyst geometry, pressure/activity convention, rate-determining step and transport limitations. Exact original-source equation transcription and assumptions are required before acceptance.

All records remain candidates. No Chemistry entry is accepted; no experiment or workflow has been run.
