# Core-295 Henry CO2 source and parameter audit 1

Date: 2026-11-12

Candidate: `CHEM-HENRY-001`

## Decision

Keep the candidate proposed and narrow its model definition to physical dissolution of molecular carbon dioxide in pure water at a fixed reference temperature of 298.15 K. Use the solubility-form Henry coefficient convention

\[
c_{\mathrm{CO_2(aq)}} = H_s^{cp}\,p_{\mathrm{CO_2}},
\]

where \(c_{\mathrm{CO_2(aq)}}\) is molar concentration in mol m\(^{-3}\), partial pressure is Pa, and \(H_s^{cp}\) is mol m\(^{-3}\) Pa\(^{-1}\). This is not the reciprocal pressure-over-concentration convention.

The 2023 Sander compilation's CO2-in-water record gives \(H_s^{cp}=3.4\times10^{-4}\) mol m\(^{-3}\) Pa\(^{-1}\) at 298.15 K for the Burkholder et al. (2019) literature-evaluation entry; it also lists a distinct lower value (2.8e-4) with a different temperature-dependence parameter. The catalogue adopts the 3.4e-4 entry as a fixed reference coefficient, not as a universal value or a fitted benchmark range. The database also lists Carroll, Slupsky & Mather (1991), *The solubility of carbon dioxide in water at low pressure*, as a literature-review entry with 3.4e-4 at the same reference temperature. These are review/compilation sources, not a claim that the coefficient was newly measured in this audit.

## Source inspection

1. Rolf Sander (2023), “Compilation of Henry's law constants (version 5.0.0) for water as solvent,” *Atmospheric Chemistry and Physics* 23, 10901–12440, DOI: 10.5194/acp-23-10901-2023. The paper describes a normalized compilation of 46,434 values for 10,173 species from 995 references. The CO2 record states the \(H_s^{cp}\) convention and lists values at 298.15 K with temperature-dependence parameters and source types.
2. The corresponding CO2 database page identifies \(H_s^{cp}\) units as mol m\(^{-3}\) Pa\(^{-1}\), the first column as the value at 298.15 K, and lists 3.4e-4 with 2300 K from Burkholder et al. (2019), type L. It also lists Carroll et al. (1991) at 3.4e-4. The database reference list identifies Carroll et al. as *J. Phys. Chem. Ref. Data* 20, 1201–1209, DOI 10.1063/1.555900.
3. NIST Chemistry WebBook's CO2 page independently displays the solubility-form Henry coefficient at 298.15 K in mol kg\(^{-1}\) bar\(^{-1}\), illustrating why coefficient convention and units must be explicit. Its displayed multiple entries include review, QSPR, citation-only and other data classes; they must not be averaged indiscriminately.
4. The IUPAC-NIST Solubility Database records a CO2-water experiment by Shedlovsky & MacInnes (1935) at 298.15 K and 101.325 kPa. It reports a separate tabulated Henry-constant convention and documents the experimental procedure. That value is not copied into this candidate because the database's listed units/convention differ from \(H_s^{cp}\).

## Scope and limitations

- Gas: CO2; solvent: pure water; reference temperature: 298.15 K.
- The dependent concentration denotes physically dissolved molecular CO2(aq), not total dissolved inorganic carbon (which includes hydrated/carbonate species and requires coupled aqueous acid-base equilibria).
- Treat the gas phase through CO2 partial pressure, not total mixture pressure.
- The linear relation is restricted to dilute/low-pressure Henry-law behavior. The inspected accessible evidence does not establish a numeric upper pressure bound or a rectangular pressure sampling interval. Leave all train/extrapolation pressure ranges and input-validity bounds unset.
- Do not vary temperature while holding the coefficient fixed. A temperature-dependent model would be a distinct expanded model with an explicit van 't Hoff parameterization and its own evidence/range review.
- Do not convert the coefficient to mol L\(^{-1}\) kPa\(^{-1}\) without an explicitly documented solvent-density and unit conversion.
- This is a gas-liquid partition relation, not the Ideal Gas Law. Structural distinctness and source-family independence remain subject to the catalogue's E0-E5 review and frozen sampling-frame rules.

## Catalogue treatment

The catalogue record is narrowed to \(c_{CO2}=H_s^{cp}p_{CO2}\), fixes \(H_s^{cp}=3.4\times10^{-4}\) mol m\(^{-3}\) Pa\(^{-1}\) at 298.15 K, and records the two source references. The independent pressure range remains null. Generator remains pending; candidate status remains proposed. No scientific acceptance or benchmark readiness is claimed.

## Sources

- Sander (2023), article: https://doi.org/10.5194/acp-23-10901-2023
- CO2 Henry-constant record: https://henrys-law.org/henry/casrn/124-38-9
- NIST Chemistry WebBook, CO2 Henry data: https://webbook.nist.gov/cgi/cbook.cgi?ID=C124389&Mask=181F
- IUPAC-NIST Solubility Database, CO2 + water, Shedlovsky & MacInnes (1935): https://srdata.nist.gov/solubility/sol_detail.aspx?sysID=62_26
- Carroll, Slupsky & Mather (1991): https://doi.org/10.1063/1.555900

No scripts, validators, tests, workflows, live experiments or scientific simulations were run.
