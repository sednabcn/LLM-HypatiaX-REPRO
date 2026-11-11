# Core-295 proposed equation records — review pass 11

**Status:** one additional Chemistry record drafted as proposed. It is not accepted, scientifically reviewed, structurally reviewed or eligible for shard planning.

## CHEM-RAOULT-VAPOR-001 — ideal-solution component vapor pressure

OpenStax Chemistry 2e §11.4 states the component form of Raoult's law:

\[
P_A=X_A P_A^*.
\]

Here \(P_A\) is the equilibrium vapor partial pressure of component A, \(X_A\) its liquid-phase mole fraction, and \(P_A^*\) the saturation vapor pressure of pure A at the same temperature. The selected record is the component relation, not the total-pressure sum across all volatile components.

**Historical source:** François-Marie Raoult, “Loi générale des tensions de vapeur des dissolvants,” *Comptes Rendus Hebdomadaires des Séances de l'Académie des Sciences*, 104 (1887), 1430–1433. The original empirical paper is registered, but its exact equation/page notation still requires direct transcription; OpenStax is the explicit modern equation source for this candidate.

**Regime and overlap controls:** ideal liquid-solution activity behavior at fixed temperature. Nonideal mixtures require activity coefficients. Henry's law is a distinct dilute-solute limiting regime, not an algebraic rearrangement of Raoult's ideal-solvent relation. The total vapor-pressure sum is linked via Dalton's law and is not counted separately. This relation is not the excluded Ideal Gas Law.

**Benchmark blockers:** select a defensible ideal binary/ternary mixture, specify temperature, pure-component vapor-pressure data or model, mole-fraction range, and deterministic generator. Verify the original 1887 paper's exact formula and notation before source verification.

## Proposed-record inventory

- Chemistry: CHEM-HENRY-001, CHEM-LANGMUIR-001, CHEM-MARCUS-001, CHEM-RAOULT-VAPOR-001.
- Biology: BIO-HILL-MUSCLE-001.
- Physics: PHYS-POISEUILLE-001, PHYS-PLANCK-SPECTRUM-001, PHYS-THIN-LENS-001.
- DeFi AMM: AMM-BALANCER-WEIGHTED-001, AMM-DODO-PMM-BASE-SHORTAGE-001.
- DeFi Risk: RISK-MORPHO-LIF-001, RISK-EULER-AUCTION-001, RISK-COMPOUND-BORROW-KINK-001.
- All thirteen records are proposed; none is accepted.
- Ranges and generator contracts remain pending.

No experiment, validator execution, live API call or GitHub Actions workflow was run.
