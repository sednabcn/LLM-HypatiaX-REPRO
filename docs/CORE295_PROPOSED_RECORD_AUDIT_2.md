# Core-295 proposed-record audit 2: Marcus prefactor and transport-law equivalence

**Date:** 2026-11-11  
**Status:** review findings only. No equation is accepted by this audit.

## 1. CHEM-MARCUS-001 — separate the historical and modern rate formulations

The proposed entry currently gives

\[
\Delta G^\ddagger=\frac{(\lambda+\Delta G^0)^2}{4\lambda},
\qquad
k_{ET}=Z\exp\left(-\frac{\Delta G^\ddagger}{RT}\right).
\]

Its review note attributes the collision-frequency prefactor \(Z\) to Marcus (1956), while the barrier is explicitly a modern classical parabolic parameterization.

The primary paper is Marcus, R. A. (1956), “On the Theory of Oxidation-Reduction Reactions Involving Electron Transfer. I,” *J. Chem. Phys.* 24, 966–978, DOI [10.1063/1.1742723](https://doi.org/10.1063/1.1742723). The publisher's abstract is available at [AIP Publishing](https://pubs.aip.org/aip/jcp/article-abstract/24/5/966/74480/On-the-Theory-of-Oxidation-Reduction-Reactions?redirectedFrom=fulltext); its abstract describes the overall reaction rate as the solution collision number multiplied by the activated-state Boltzmann factor, \(\exp(-\Delta F^*/kT)\).

The authoritative current IUPAC Gold Book entry [“Marcus equation,” M03702](https://goldbook.iupac.org/terms/view/M03702) instead defines the rate constant within the encounter complex (or intramolecular transfer) using an Eyring prefactor:
\[
k_{ET}=\frac{\kappa_{ET} k_B T}{h}
\exp\left(-\frac{\Delta G^\ddagger}{RT}\right),
\qquad
\Delta G^\ddagger=\frac{(\lambda+\Delta G^0)^2}{4\lambda}.
\]
IUPAC cites the 2006 photochemistry glossary recommendation (published in *Pure and Applied Chemistry* 79, 293; DOI [10.1351/pac200779020293](https://doi.org/10.1351/pac200779020293)).

**Finding:** the current record should not describe \(Z\exp(-\Delta G^\ddagger/RT)\) as the uniquely authoritative “Marcus equation” without an explicit source-specific derivation. The original collision-number formulation and the modern IUPAC encounter-complex/intramolecular Eyring formulation have different prefactor definitions and kinetic scope. The energy convention must also be consistent: use \(k_B T\) for per-molecule energies or \(RT\) for molar energies.

**Required resolution before acceptance:**
1. Decide whether the benchmark record represents the 1956 solution collision-number model or the modern IUPAC Marcus equation.
2. Transcribe the selected rate expression and barrier from the corresponding exact source, keeping the kinetic scope and prefactor together.
3. Define solvent, encounter-complex/intramolecular context, electronic coupling/transmission assumptions, energy convention and units.
4. Continue explicit comparison with the Core-15 Arrhenius and generic Rate Law exclusions. A quadratic Marcus barrier alone does not establish that the full rate expression survives the exclusion.
5. Freeze physically meaningful train/extrapolation ranges and a deterministic generator only after the source formulation is fixed.

The current manifest formula is therefore retained as **proposed but source-formulation unresolved**; this audit does not silently replace it.

## 2. CHEM-FICK-FLUX-001 — cross-domain constitutive-form overlap

The candidate's scalar one-dimensional Fick relation is of the form
\[
J=-D\,\frac{dC}{dx}.
\]
The corresponding linear constitutive forms are Fourier heat flux
\[
q=-k\,\frac{dT}{dx}
\]
and Ohm current density
\[
i=-\sigma\,\frac{dV}{dx},
\]
with sign and geometry conventions chosen consistently.

The primary Fick source is Fick, A. (1855), “Ueber Diffusion,” *Annalen der Physik* 170, 59–86, DOI [10.1002/andp.18551700105](https://doi.org/10.1002/andp.18551700105). A scholarly historical analysis by Narasimhan (2004), [“Fick's Insights on Liquid Diffusion”](https://digital.library.unt.edu/ark:/67531/metadc784988/), explains that Fick explicitly drew on Fourier's heat-diffusion equation by analogy. A standard transport text excerpt likewise writes the three laws as the same gradient-driven transport structure; see [the cited transport textbook extract](https://citeseerx.ist.psu.edu/document?doi=b11a8a588240a24d67882d3660157e1dfc666395&repid=rep1&type=pdf).

**Finding:** after normalizing dependent flux, driving potential/concentration and transport coefficient, the simple scalar laws share the same first-order linear-gradient operator structure. This is a stronger overlap than merely sharing a broad “transport” topic. The different physical dimensions and domain interpretations are important scientifically, but do not by themselves prove structural distinctness under the catalogue's stated normalization policy.

**Required resolution before acceptance:** make an explicit policy decision on cross-domain equation-family equivalence. If mathematical operator form is the unit of structural distinctness, the simple Fick flux candidate should not be counted separately from Fourier/Ohm constitutive laws. If domain-specific physical laws are allowed as distinct units despite normalized operator equivalence, that exception must be justified and applied consistently across all five domains. The diffusion PDE is not a cosmetic variant of the scalar flux law, but it is a linked conservation/constitutive model and requires its own system-level inclusion rule and deterministic adapter.

The record remains **proposed and structurally unresolved**. Do not count it toward the 59 Chemistry target pending this decision.

## 3. Audit status

- No candidate accepted or rejected by manifest status.
- No formula was changed in the catalogue in this audit.
- No experiment, validator, paid compute, live API/protocol call or GitHub Actions workflow was run.
- Next review priority: resolve the two policy/source-formulation decisions above before drafting more records from the same structural families.
