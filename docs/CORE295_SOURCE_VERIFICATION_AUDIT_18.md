# Core-295 source verification audit 18: Marcus outer-sphere electron-transfer barrier and rate prefactor

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** proposed record CHEM-MARCUS-001 and its registered primary Marcus 1956 and IUPAC Gold Book sources.

## 1. Source roles and what each source establishes

Marcus (1956), *On the Theory of Oxidation-Reduction Reactions Involving Electron Transfer. I*, J. Chem. Phys. 24, 966–978, DOI 10.1063/1.1742723, presents a solution-phase outer-sphere electron-transfer mechanism with slight orbital overlap. Its abstract states that the rate is the solution collision number multiplied by an activated exponential involving the free-energy cost of forming the intermediate state.

The IUPAC Gold Book entry M03702 provides the modern classical outer-sphere Marcus barrier:
[
Delta G^{\ddagger}
=\frac{(\lambda+\Delta G^0_{ET})^2}{4\lambda},
]
and describes an encounter-complex/intramolecular transfer rate using an Eyring prefactor:
[
k_{ET}=\frac{\kappa_{ET}k_BT}{h}
\exp\left(-\frac{\Delta G^{\ddagger}}{RT}\right).
]
IUPAC also notes that the classical Marcus equation is adequate in the normal region, while the inverted region generally requires a more elaborate Franck-Condon treatment.

These are related but not identical source statements. The primary paper's collision-number prefactor and the IUPAC encounter-complex Eyring prefactor must not be silently substituted for one another.

## 2. Proposed record transcription

The current proposed record uses:
[
\Delta G^{\ddagger}
=\frac{(\lambda+\Delta G^0)^2}{4\lambda},
\qquad
k_{ET}=Z\exp\left(-\frac{\Delta G^{\ddagger}}{RT}\right),
]
where (Z) is the solution collision frequency (s\(^{-1}\)), (T) is absolute temperature, and (lambda,\Delta G^0) are molar energies. The units must be internally consistent: (lambda) and (Delta G^0) in J mol\(^{-1}\), (R) in J mol\(^{-1}\) K\(^{-1}\), and the exponential dimensionless.

This is a classical Marcus barrier paired with the collision-frequency prefactor described in the 1956 primary-paper abstract. It is not the same prefactor expression as the modern IUPAC Eyring form. If the intended benchmark instead models transfer within an encounter complex, the record must use (kappa_{ET}k_BT/h) and define the transmission factor and encounter-complex regime explicitly.

## 3. Structural distinction and exclusion risk

The Marcus barrier is quadratic in the reaction free-energy change:
[
\Delta G^{\ddagger}(\Delta G^0)
=\frac{(\lambda+\Delta G^0)^2}{4\lambda}.
]
This makes the activation barrier depend on driving force and produces normal, activationless and inverted regimes in the classical model. It is not merely a constant activation energy inserted into an Arrhenius expression.

Nevertheless, the rate still has an activated exponential form. The Core-15 exclusions include Arrhenius/generic rate-law structures. The mechanism label alone does not settle whether this candidate is structurally distinct under the benchmark's equation-family policy. The decision must compare the complete barrier-plus-rate expression, not only the Marcus name or the exponential operator.

The candidate must not be counted as:
- separate equations for the parabolic barrier and the activated rate;
- a separate candidate for an alternate prefactor;
- independent entries for normal, activationless and inverted regions;
- independent entries for solvent and inner-sphere contributions to total reorganization energy.

## 4. Required benchmark contract

Before acceptance, freeze:
- whether the target is the barrier (Delta G^{\ddagger}) or the full rate constant (k_{ET});
- which prefactor model is used: original collision frequency (Z) or IUPAC encounter-complex Eyring prefactor;
- outer-sphere, classical parabolic free-energy-surface assumptions;
- energy convention, temperature range, solvent and reorganization-energy definition;
- normal-region-only or full classical inverted-region scope;
- a documented structural-equivalence ruling against Core-15 Arrhenius and generic Rate Law exclusions.

Input ranges and a deterministic generator remain unspecified. A generator must enforce (lambda>0), consistent molar-energy units, and a physically justified (Delta G^0) domain; arbitrary extrapolation through an inverted region is not justified by the classical expression alone.

## 5. Decision

**Disposition:** source roles and the classical Marcus barrier are verified; the current proposed record is a plausible mechanistic rate model but remains held. The prefactor convention and Core-15 structural-overlap policy are unresolved. Do not accept the record or split it into barrier/rate/prefactor variants.

No catalogue record or status was changed. The formal catalogue remains at 128 source records, 19 proposed records and zero accepted records; the sampling frame remains unfrozen.

No experiments, solvers, validators, workflows, paid compute, live API calls or chemical measurements were run. This is source review only.
