# Core-295 proposed equation records — review pass 10

**Status:** one additional DeFi AMM record drafted as proposed. It is not accepted, scientifically reviewed, structurally reviewed or eligible for shard planning.

## AMM-DODO-PMM-BASE-SHORTAGE-001 — base-shortage marginal price

Official DODO PMM documentation defines the base-shortage branch as:

\[
P=i\left(1-k+k\left(\frac{B_0}{B}\right)^2\right),
\qquad 0<B<B_0.
\]

Here \(i\) is the guide price, \(k\) the slippage factor, \(B_0\) the equilibrium/regression target base inventory, and \(B\) the current base inventory. \(P\) is the marginal quote price per unit of base token.

**Pinned implementation:** DODOEX/contractV2 commit 2f1bcdac7ef1beee7599a756e2eed26732c2536d, contracts/lib/PMMPricing.sol. The getMidPrice ABOVE_ONE branch uses the squared inventory ratio \(B_0^2/B^2\), matching the documented base-shortage expression.

**Family controls:** the quote-shortage branch is the reciprocal counterpart in the same PMM family; the equilibrium branch gives \(P=i\). The integrated trade amount is the integral of the marginal price curve, and the regression-target update is a state transition. Do not count these as independent equations in this record. Pool types (DVM/DSP/DPP), guide-price source, state classification and regression policy must be frozen before acceptance.

**Benchmark blockers:** enforce \(i>0\), \(B_0>0\), \(0<B<B_0\), and \(0\leq k\leq1\); pin DecimalMath precision and rounding; freeze oracle/guide-price context, pool type and state/regression adapter; define deterministic ranges and generator.

## Proposed-record inventory

- Chemistry: CHEM-HENRY-001, CHEM-LANGMUIR-001, CHEM-MARCUS-001.
- Biology: BIO-HILL-MUSCLE-001.
- Physics: PHYS-POISEUILLE-001, PHYS-PLANCK-SPECTRUM-001, PHYS-THIN-LENS-001.
- DeFi AMM: AMM-BALANCER-WEIGHTED-001, AMM-DODO-PMM-BASE-SHORTAGE-001.
- DeFi Risk: RISK-MORPHO-LIF-001, RISK-EULER-AUCTION-001, RISK-COMPOUND-BORROW-KINK-001.
- All twelve records are proposed; none is accepted.
- Ranges and generator contracts remain pending.

No experiment, validator execution, live API call or GitHub Actions workflow was run.
