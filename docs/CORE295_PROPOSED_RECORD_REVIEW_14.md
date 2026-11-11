# Core-295 proposed equation records — review pass 14

**Status:** one additional DeFi Risk record drafted as proposed. It is not accepted, scientifically reviewed, structurally reviewed or eligible for shard planning.

## RISK-UNISWAP-V2-ARITHMETIC-TWAP-001 — arithmetic cumulative-price TWAP

The Uniswap v2 example oracle computes the arithmetic time-weighted mean price as:

\[
P_{TWAP}=\frac{C(t_2)-C(t_1)}{t_2-t_1},
\]

where \(C(t)\) is the cumulative integral of the pair's instantaneous UQ112x112 price. The cumulative-price difference has price-seconds units; division by elapsed seconds returns the arithmetic mean price in UQ112x112 representation.

**Pinned source:** Uniswap/v2-periphery commit ed24991304291297c3b4a52818d02f46a17aa9a2, contracts/examples/ExampleOracleSimple.sol and contracts/libraries/UniswapV2OracleLibrary.sol. The example requires a minimum observation period of 24 hours; this is an example parameter, not a universal protocol constant.

**Overlap control:** Uniswap v2 arithmetic TWAP and Uniswap v3 geometric TWAP are distinct averaging constructions but belong to the same oracle-manipulation family. Do not count token-direction reciprocals or decimal conversions independently.

**Benchmark blockers:** freeze observation schedule, token ordering, UQ112x112 scaling, timestamp wrap, cumulative uint256 arithmetic and the security assumptions for observation spacing. Require a positive interval and paired observations from the same pair/direction.

## Proposed-record inventory

- Chemistry: CHEM-HENRY-001, CHEM-LANGMUIR-001, CHEM-MARCUS-001, CHEM-RAOULT-VAPOR-001.
- Biology: BIO-HILL-MUSCLE-001, BIO-FICK-CARDIAC-OUTPUT-001.
- Physics: PHYS-POISEUILLE-001, PHYS-PLANCK-SPECTRUM-001, PHYS-THIN-LENS-001.
- DeFi AMM: AMM-BALANCER-WEIGHTED-001, AMM-DODO-PMM-BASE-SHORTAGE-001.
- DeFi Risk: RISK-MORPHO-LIF-001, RISK-EULER-AUCTION-001, RISK-COMPOUND-BORROW-KINK-001, RISK-UNISWAP-V3-GEOMETRIC-TWAP-001, RISK-UNISWAP-V2-ARITHMETIC-TWAP-001.
- All sixteen records are proposed; none is accepted.
- Ranges and generator contracts remain pending.

No experiment, validator execution, live API call or GitHub Actions workflow was run.
