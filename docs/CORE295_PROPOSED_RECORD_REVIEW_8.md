# Core-295 proposed equation records — review pass 8

**Status:** one additional DeFi Risk record drafted as proposed. It is not accepted, scientifically reviewed, structurally reviewed or eligible for shard planning.

## RISK-EULER-AUCTION-001 — Euler EVK reverse-auction discount factor

Pinned source: euler-xyz/euler-vault-kit commit 93a1de491531e54cbbcf0e5c8cacfe558f924867, src/EVault/modules/Liquidation.sol, calculateMaxLiquidation.

The source computes the health score as risk-adjusted collateral value divided by liability value. It then floors the discount factor at one minus the vault's configured maximum discount:

\[
F_{discount}=\max\left(\frac{C_{adj}}{L},1-D_{max}\right),
\qquad D=1-F_{discount}.
\]

Here \(C_{adj}\) is liquidation-LTV-adjusted collateral value, \(L\) is liability value, and \(D_{max}\) is the configured maximum discount. For an unhealthy position, \(C_{adj}/L\leq1\); the discount is zero at the threshold and increases linearly with the health shortfall until the cap is reached.

This is the EVK reverse Dutch auction mechanism, not Euler V1's older boosted discount model. The scalar formula is only the discount-factor subcomponent: actual seizure and repayment amounts additionally depend on collateral selection, oracle midpoint prices, liquidation LTVs, collateral balances and fixed-point arithmetic.

**Benchmark blockers:** freeze the collateral set, risk-adjusted aggregation, liability value, oracle convention, CONFIG_SCALE and integer rounding; enforce positive liability and unhealthy-position constraints; freeze a deterministic generator. The discount cap is a per-vault parameter and must not be sampled outside the configured domain.

## Proposed-record inventory

- Chemistry: CHEM-HENRY-001, CHEM-LANGMUIR-001, CHEM-MARCUS-001.
- Biology: BIO-HILL-MUSCLE-001.
- Physics: PHYS-POISEUILLE-001, PHYS-PLANCK-SPECTRUM-001, PHYS-THIN-LENS-001.
- DeFi AMM: AMM-BALANCER-WEIGHTED-001.
- DeFi Risk: RISK-MORPHO-LIF-001, RISK-EULER-AUCTION-001.
- All ten records are proposed; none is accepted.
- Ranges and generator contracts remain pending.

No experiment, validator execution, live API call or GitHub Actions workflow was run.
