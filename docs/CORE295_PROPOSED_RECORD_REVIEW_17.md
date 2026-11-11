# Core-295 proposed equation records — review pass 17

**Status:** one additional Biology record drafted as proposed. It is not accepted, scientifically reviewed, structurally reviewed or eligible for shard planning.

## BIO-TUMOR-TURNOVER-001 — De Buck concentration-modulated tumor turnover

De Buck et al. (2014), *British Journal of Clinical Pharmacology* 78(3), 543–555, DOI [10.1111/bcp.12378](https://doi.org/10.1111/bcp.12378), give the final tumor-growth turnover model as Eq. 9 on printed page 547:

\[
\frac{dT}{dt}
=K_{growth}\left(1-\frac{E_{max}C}{C+IC_{50}}\right)
-K_{deg}T.
\]

The primary paper defines \(T\) as the one-dimensional sum of the longest diameters of measurable lesions. \(C\) is the individual predicted BYL719 plasma concentration supplied by the PK model. \(K_{growth}\) is the zero-order tumor growth rate, \(K_{deg}\) the first-order tumor death/turnover rate, \(E_{max}\) the maximum PD effect, and \(IC_{50}\) the concentration at half-maximal inhibition. The paper constrains \(K_{growth}\) and \(K_{deg}\) to be positive.

This is not the simplified \(dT/dt=k_g-dT\) expression quoted in a secondary tumor-model comparison table; that is only the no-drug/simplified turnover structure. The exact primary equation contains an exposure-dependent inhibition term.

**Critical exclusion overlap:** \(E_{max}C/(C+IC_{50})\) is a hyperbolic saturation function structurally related to Michaelis–Menten. Because Michaelis–Menten is explicitly excluded from Core-15, this full ODE must undergo explicit structural/equivalence review before it can be accepted. A different biological interpretation does not automatically make the embedded saturation structure independent. The complete ODE may or may not survive the project's structural distinctness rule; it remains proposed.

**Benchmark blockers:** preserve the tumor state as sum of longest diameters, specify a BYL719 concentration-time input function and its PK provenance, freeze units (cm, ng/mL, weeks), choose clinically defensible parameter ranges, and define deterministic initialization and extrapolation. Do not treat the PK model's transit compartments as extra independent records in this pass.

## Proposed-record inventory

- Chemistry: CHEM-HENRY-001, CHEM-LANGMUIR-001, CHEM-MARCUS-001, CHEM-RAOULT-VAPOR-001, CHEM-FICK-FLUX-001, CHEM-BEER-LAMBERT-001.
- Biology: BIO-HILL-MUSCLE-001, BIO-FICK-CARDIAC-OUTPUT-001, BIO-TUMOR-TURNOVER-001.
- Physics: PHYS-POISEUILLE-001, PHYS-PLANCK-SPECTRUM-001, PHYS-THIN-LENS-001.
- DeFi AMM: AMM-BALANCER-WEIGHTED-001, AMM-DODO-PMM-BASE-SHORTAGE-001.
- DeFi Risk: RISK-MORPHO-LIF-001, RISK-EULER-AUCTION-001, RISK-COMPOUND-BORROW-KINK-001, RISK-UNISWAP-V3-GEOMETRIC-TWAP-001, RISK-UNISWAP-V2-ARITHMETIC-TWAP-001.
- All nineteen records are proposed; none is accepted.
- Ranges and generator contracts remain pending.

No experiment, validator execution, live API call or GitHub Actions workflow was run.
