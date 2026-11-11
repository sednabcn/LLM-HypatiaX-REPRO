# Core-295 proposed-record audit 6 — De Buck tumour-turnover model

**Status:** primary-source and model-contract review; candidate remains proposed. No equation was accepted, no generator was run, and no experiment or validator was executed.

## Candidate

- ID: `BIO-TUMOR-TURNOVER-001`
- Source: De Buck et al. (2014), *British Journal of Clinical Pharmacology* 78(3), Eq. 9, printed p. 547.
- DOI: https://doi.org/10.1111/bcp.12378
- Primary article: https://bpspubs.onlinelibrary.wiley.com/doi/10.1111/bcp.12378

The paper's final tumour-growth turnover model is defined on the one-dimensional **sum of longest diameters** of measurable lesions, not tumour volume or mass. Its concentration input is the individual predicted BYL719 plasma concentration from the associated PK model. The model has a zero-order tumour-growth term inhibited by a saturating Emax/IC50 function and a first-order tumour-death/turnover term:

`dT/dt = Kgrowth * (1 - Emax*C/(C+IC50)) - Kdeg*T`

## Primary-source findings

1. The article identifies the measured tumour quantity as the sum of longest tumour diameters. The state unit is therefore cm; this candidate must not be silently converted to a volume-growth model.
2. The final model fixed `Kgrowth = 0.581 cm/week` and `Emax = 1`; `Kdeg` and `IC50` were estimated. A source-faithful generator must not independently sample the fixed parameters as if they were freely estimated.
3. `C(t)` is an individual PK-derived concentration-time input. A deterministic adapter must specify dose schedule, PK/transit model, concentration units, time grid and initialization. Sampling unrelated concentration values row by row does not reproduce the model.
4. The authors characterize the implementation as empirical and caution against generalization beyond the baseline tumour-size range represented in the study (2–20 cm). This is a study-specific evidence boundary, not a universal physical validity interval.
5. The paper reports no serial tumour measurements before treatment; the authors note possible confounding between turnover parameters and drug effect. This limitation should travel with any benchmark use.

## Structural-distinctness decision still required

The embedded inhibition fraction `Emax*C/(C+IC50)` has a hyperbolic saturation form related to the Core-15-excluded Michaelis–Menten family. However, the **complete** candidate is a non-autonomous tumour-state ODE with a zero-order inhibited growth term, first-order state-dependent turnover, and an external time-varying PK input. Similarity of one subexpression is not by itself proof that the full ODE is algebraically equivalent to the excluded scalar Michaelis–Menten rate equation.

The catalogue policy must decide explicitly whether an excluded structure disqualifies a full model containing that structure as a subexpression, or whether exclusion requires equivalence of the complete canonical model. Apply the chosen rule consistently to other embedded saturation models (e.g. Monod/Emax, receptor occupancy and tumor PK/PD models). Do not accept this entry until that policy decision is recorded.

## Benchmark contract still required

- A time-dependent PK input contract for `C(t)`, with reproducible dosing and PK parameterization.
- Explicit units and time basis for every state and parameter.
- A declared observation/time grid and initial tumour diameter.
- Clinically defensible parameter and concentration ranges, with the 2–20 cm baseline-size evidence boundary represented honestly.
- A decision on fixed versus estimated parameters matching the source.
- A deterministic generator, seed policy and data split contract.
- Structural-family and Core-15 exclusion ruling as described above.

## Disposition

**Remain proposed; do not accept or count toward 59 Biology equations.** This audit strengthens provenance and benchmark-contract notes but does not certify the model as structurally distinct or statistically independent.

## References

- De Buck et al. (2014), primary article and Eq. 9: https://doi.org/10.1111/bcp.12378
- Simeoni et al. (2004), distinct xenograft PK/PD ODE and transit-compartment model: https://doi.org/10.1158/0008-5472.CAN-03-2524
- Later comparison documenting alternative tumour-growth models and non-uniqueness: https://pmc.ncbi.nlm.nih.gov/articles/PMC7076937/
