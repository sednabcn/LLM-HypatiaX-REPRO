# Core-295 proposed equation records — review pass 6

**Status:** one additional DeFi AMM record drafted as proposed. It is not accepted, scientifically reviewed, structurally reviewed or eligible for shard planning.

## AMM-BALANCER-WEIGHTED-001 — three-token weighted geometric invariant

Balancer's official Weighted Math documentation defines the invariant as \(V=\prod_t B_t^{W_t}\), with normalized weights summing to one. The V2 implementation computes this as the product of each balance raised to its normalized weight.

For a fixed three-token adapter:

\[
V=B_1^{w_1}B_2^{w_2}B_3^{w_3},
\qquad w_1+w_2+w_3=1.
\]

The adapter is deliberately three-token: the two-token equal-weight special case reduces to the Core-15 excluded constant-product family. Balances must be expressed in consistent normalized/upscaled units. The invariant is a mathematical pool state function; spot-price and swap-output equations derived from it are not separate independent candidates in this pass.

**Outstanding before source verification or acceptance:** pin the exact Balancer V2 repository commit and pool implementation; define token decimal scaling; define positive weight constraints and a constrained sampler; specify invariant normalization and fixed-point rounding; choose balance and weight ranges; freeze a deterministic benchmark generator. Do not sample \(w_1,w_2,w_3\) independently without enforcing positivity and unit sum.

## Proposed-record inventory

- Chemistry: CHEM-HENRY-001, CHEM-LANGMUIR-001, CHEM-MARCUS-001.
- Biology: BIO-HILL-MUSCLE-001.
- Physics: PHYS-POISEUILLE-001, PHYS-PLANCK-SPECTRUM-001, PHYS-THIN-LENS-001.
- DeFi AMM: AMM-BALANCER-WEIGHTED-001.
- All eight records are proposed; none is accepted.
- Ranges and generator contracts remain pending.

No experiment, validator execution, live API call or GitHub Actions workflow was run.
