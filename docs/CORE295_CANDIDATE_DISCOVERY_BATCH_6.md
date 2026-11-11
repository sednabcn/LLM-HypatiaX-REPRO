# Core-295 candidate discovery batch 6: DeFi AMM primary invariant tracing

**Status:** protocol-source tracing only. No equation is accepted or counted toward the 59 DeFi AMM target. Protocol versions and source-family relationships remain review gates.

## Source map

| Mechanism | Primary/official source and equation location | Candidate mathematical object | Curation boundary |
|---|---|---|---|
| Weighted geometric AMM (Balancer) | Balancer official Weighted Math reference; linked Balancer whitepaper is the derivation source. [Weighted Math](https://docs.balancer.fi/reference/math/weighted-math.html) | Invariant/value function \(V=\prod_t B_t^{W_t}\), normalized weights \(\sum_t W_t=1\); pairwise spot price \(SP_i^o=(B_i/W_i)/(B_o/W_o)\); exact-input/output swap relations are derived from invariant preservation. | The invariant is a weighted, multi-asset generalization of constant product. Equal weights and two assets reduce to the Core-15 excluded constant-product form. A non-equal-weight or multi-asset instance may be structurally distinct, but the invariant, spot price, swap equations and fee-adjusted versions are one derivation family—not multiple candidates. Record normalized-weight and fixed-point conventions and the exact protocol version. |
| Concentrated liquidity (Uniswap v3) | Uniswap v3 Core whitepaper §6.2.1, equations (6.3)–(6.6). [Whitepaper PDF](https://app.uniswap.org/whitepaper-v3.pdf) | Within a tick interval, virtual reserves satisfy \(L=\sqrt{xy}\), \(\sqrt P=\sqrt{y/x}\), and \(x=L/\sqrt P,\ y=L\sqrt P\). Liquidity positions impose finite price bounds and piecewise active liquidity. | These virtual-reserve equations are a coordinate representation of the constant-product curve within a bounded range. Do not count them as a new independent invariant merely because liquidity is concentrated or expressed through \(L\) and \(\sqrt P\). The genuinely distinct object is the piecewise range/active-liquidity state machine, which is not automatically a scalar equation benchmark. |
| StableSwap (Curve, 2019) | Egorov, *StableSwap: Efficient Mechanism for Stablecoin Liquidity*, original paper, invariant on p. 5. [Original whitepaper](https://curve.fi/files/stableswap-paper.pdf); official overview [here](https://docs.curve.finance/developer/stableswap-exchange/stableswap/overview). | For \(n\) coins, the invariant is \(A n^n\sum_i x_i + D = A D n^n + D^{n+1}/(n^n\prod_i x_i)\), with \(D\) determined by the pool balances and held invariant through swaps. | This combines constant-sum-like behaviour near the peg with a constant-product-like tail. It is distinct from the excluded pure constant-product invariant, but its Newton solver, per-token balance solution, price derivative and algebraic rearrangements belong to the same StableSwap family. Define amplification convention, coin count, balance scaling and fixed-point precision. |
| CryptoSwap / dynamic peg (Curve, 2021) | Egorov, *Automatic market-making with dynamic peg*, June 9, 2021. [Primary whitepaper](https://docs.curve.fi/assets/pdf/whitepaper_cryptoswap.pdf) | Dynamic-peg invariant \(K D^{N-1}\sum_i x_i + \prod_i x_i = K D^N + (D/N)^N\), with \(K_0=N^N\prod_i x_i/D^N\) and state-dependent \(K=A K_0\gamma^2/(\gamma+1-K_0)^2\). | This is a separate candidate invariant from 2019 StableSwap: the coefficient depends on pool state and the model tracks an internal price scale/peg. Verify the paper's transformed-balance conventions and the versioned contract implementation. Newton iterations for \(D\) or an output balance are solvers, not separate economic equations. |

## Source-family and Core-15 overlap controls

- Core-15 explicitly excludes the Uniswap-style constant-product invariant. Uniswap v3 virtual reserves still satisfy a constant-product relation locally; do not count a variable substitution or bounded operating interval as an independent invariant.
- Balancer weighted math generalizes constant product. It is a candidate only where the non-equal weights or multi-asset structure are preserved as part of the model, not when a 50/50 two-token pool collapses to the excluded case.
- Balancer spot-price and swap-output expressions are consequences of its weighted invariant and should share a source-family ID.
- StableSwap and CryptoSwap have distinct invariant structures. Keep their equations separate as candidate mechanisms, but assign protocol-family clustering so they are not automatically treated as independent statistical units.
- Curve StableSwap Newton iterations and closed-form per-token rearrangements are numerical/derived representations of one invariant. Likewise, CryptoSwap's solver equations are not additional invariant families.
- A protocol whitepaper equation is not automatically a valid deterministic benchmark. The catalogue must specify admissible balances, positive domains, token count, fee convention, precision/rounding, parameter bounds and output variable.

## Primary references and version controls

- [Balancer Weighted Math official reference](https://docs.balancer.fi/reference/math/weighted-math.html); derivation pointer: [Balancer whitepaper](https://docs.balancer.fi/whitepaper.pdf).
- [Uniswap v3 Core whitepaper](https://app.uniswap.org/whitepaper-v3.pdf), §6.2.1, equations (6.3)–(6.6).
- [Curve StableSwap original paper](https://curve.fi/files/stableswap-paper.pdf), p. 5; [official technical overview](https://docs.curve.finance/developer/stableswap-exchange/stableswap/overview).
- [Curve CryptoSwap primary whitepaper](https://docs.curve.fi/assets/pdf/whitepaper_cryptoswap.pdf), June 9, 2021.

All are candidate source traces only. No DeFi AMM equation has been accepted, and no experiment or workflow has been run.
