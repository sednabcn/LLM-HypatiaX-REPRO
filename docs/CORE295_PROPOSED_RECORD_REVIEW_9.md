# Core-295 proposed equation records — review pass 9

**Status:** one additional DeFi Risk record drafted as proposed. It is not accepted, scientifically reviewed, structurally reviewed or eligible for shard planning.

## RISK-COMPOUND-BORROW-KINK-001 — Compound III borrow utilization-kink function

Pinned source: compound-finance/comet commit f766f51583c23acc33b2a7824654ef2029a96804, contracts/CometWithExtendedAssetList.sol, getBorrowRate.

The source defines two continuous linear branches:

\[
r_b(U)=
\begin{cases}
r_{base}+s_{low}U,&U\leq U_k,\\
r_{base}+s_{low}U_k+s_{high}(U-U_k),&U>U_k.
\end{cases}
\]

Equivalent compact form:

\[
r_b=r_{base}+s_{low}\min(U,U_k)+s_{high}\max(U-U_k,0).
\]

Here \(U\) is base-asset utilization, \(U_k\) is the configured borrow kink, and the rate is returned per second in the Comet factor convention. The source implementation uses FACTOR_SCALE fixed-point multiplication and bounds the result to uint64.

This record is the borrow-rate function only. The supply-rate function additionally multiplies by utilization and the reserve-factor complement; it is not counted separately here. Aave's related two-slope utilization curve remains in the same source family and must not be counted as an independent equation merely because its parameter values differ.

**Benchmark blockers:** pin the exact market configuration, utilization and kink domains, base/slope parameters, FACTOR_SCALE conversion and integer rounding. Preserve continuity at the kink and the per-second rate convention. Freeze a deterministic generator before acceptance.

## Proposed-record inventory

- Chemistry: CHEM-HENRY-001, CHEM-LANGMUIR-001, CHEM-MARCUS-001.
- Biology: BIO-HILL-MUSCLE-001.
- Physics: PHYS-POISEUILLE-001, PHYS-PLANCK-SPECTRUM-001, PHYS-THIN-LENS-001.
- DeFi AMM: AMM-BALANCER-WEIGHTED-001.
- DeFi Risk: RISK-MORPHO-LIF-001, RISK-EULER-AUCTION-001, RISK-COMPOUND-BORROW-KINK-001.
- All eleven records are proposed; none is accepted.
- Ranges and generator contracts remain pending.

No experiment, validator execution, live API call or GitHub Actions workflow was run.
