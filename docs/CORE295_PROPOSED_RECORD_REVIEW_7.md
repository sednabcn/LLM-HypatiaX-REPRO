# Core-295 proposed equation records — review pass 7

**Status:** one additional DeFi Risk record drafted as proposed. It is not accepted, scientifically reviewed, structurally reviewed or eligible for shard planning.

## RISK-MORPHO-LIF-001 — Morpho Blue liquidation incentive factor

The pinned Morpho Blue implementation computes the liquidation incentive factor as:

\[
LIF=\min\left(1.15,\frac{1}{1-0.3(1-LLTV)}\right).
\]

**Pinned source:** morpho-org/morpho-blue commit 430bd61d8ab9238c1bde327eec2bfcd3f494fe9d, src/Morpho.sol liquidation branch and src/libraries/ConstantsLib.sol. The constants file sets the liquidation cursor to 0.3e18 and maximum incentive factor to 1.15e18. The implementation uses WAD fixed-point multiplication/division and a downward-rounded reciprocal.

This is a liquidation incentive factor, not a health factor, LTV definition or liquidation-price equation. The input LLTV is a dimensionless fraction. The source is version-specific; do not substitute the newer Morpho Midnight per-collateral cursor and post-maturity ramp mechanism.

**Benchmark blockers:** freeze the exact allowed LLTV set for the pinned release; preserve WAD scaling and rounding; define a deterministic adapter and test domain; do not sample arbitrary continuous LLTVs if the protocol only permits governance-approved values. The cursor and cap are constants for this record, not additional free input variables.

## Proposed-record inventory

- Chemistry: CHEM-HENRY-001, CHEM-LANGMUIR-001, CHEM-MARCUS-001.
- Biology: BIO-HILL-MUSCLE-001.
- Physics: PHYS-POISEUILLE-001, PHYS-PLANCK-SPECTRUM-001, PHYS-THIN-LENS-001.
- DeFi AMM: AMM-BALANCER-WEIGHTED-001.
- DeFi Risk: RISK-MORPHO-LIF-001.
- All nine records are proposed; none is accepted.
- Ranges and generator contracts remain pending.

No experiment, validator execution, live API call or GitHub Actions workflow was run.
