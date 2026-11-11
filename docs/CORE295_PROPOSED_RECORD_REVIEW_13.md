# Core-295 proposed equation records — review pass 13

**Status:** one additional DeFi Risk record drafted as proposed. It is not accepted, scientifically reviewed, structurally reviewed or eligible for shard planning.

## RISK-UNISWAP-V3-GEOMETRIC-TWAP-001 — geometric price TWAP from mean tick

The Uniswap v3 tick convention maps a tick to the raw token1/token0 price ratio:

\[
P_{TWAP}=1.0001^{\overline{tick}}.
\]

The mean tick is computed over a nonzero observation interval from the difference of cumulative ticks divided by elapsed seconds. The pinned OracleLibrary implementation rounds negative nonintegral quotients toward negative infinity, rather than truncating toward zero. Taking the exponential of the arithmetic mean tick produces a geometric time-average price in the raw token ratio.

**Pinned source:** Uniswap/v3-periphery commit 24ccf014fe7f81d74a14c1689d6fdf123f280e45, contracts/libraries/OracleLibrary.sol, consult and getQuoteAtTick. The source returns both arithmeticMeanTick and harmonicMeanLiquidity; this record covers only the price ratio.

**Benchmark blockers:** freeze the observation interval, token0/token1 ordering, decimal normalization, TickMath bounds and the exact rounding path; define a deterministic adapter for cumulative tick observations. The Uniswap v2 arithmetic cumulative-price TWAP is a distinct averaging construction but remains in the same oracle-manipulation source family. Do not count reciprocal prices or token-order conversions separately.

## Proposed-record inventory

- Chemistry: CHEM-HENRY-001, CHEM-LANGMUIR-001, CHEM-MARCUS-001, CHEM-RAOULT-VAPOR-001.
- Biology: BIO-HILL-MUSCLE-001, BIO-FICK-CARDIAC-OUTPUT-001.
- Physics: PHYS-POISEUILLE-001, PHYS-PLANCK-SPECTRUM-001, PHYS-THIN-LENS-001.
- DeFi AMM: AMM-BALANCER-WEIGHTED-001, AMM-DODO-PMM-BASE-SHORTAGE-001.
- DeFi Risk: RISK-MORPHO-LIF-001, RISK-EULER-AUCTION-001, RISK-COMPOUND-BORROW-KINK-001, RISK-UNISWAP-V3-GEOMETRIC-TWAP-001.
- All fifteen records are proposed; none is accepted.
- Ranges and generator contracts remain pending.

No experiment, validator execution, live API call or GitHub Actions workflow was run.
