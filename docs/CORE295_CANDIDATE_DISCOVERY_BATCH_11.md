# Core-295 candidate discovery batch 11: DeFi AMM inventory curves and discrete bins

**Status:** protocol-source tracing only. No equation is accepted or counted toward the 59 DeFi AMM target.

## 1. DODO Proactive Market Maker (PMM)

**Official source:** [DODO — The Math Behind](https://docs-next.dodoex.io/en/product/pmm-algorithm/the-mathematical-principle-of-pmm), with integration context in [DODO V1/V2 Integration Guide](https://docs-next.dodoex.io/en/developer/contracts/dodo-v1-v2/dodo-v1-v2-integration-guide).

The PMM marginal price is expressed as \(P=iR\), where \(i\) is the guide/oracle price and \(k\) is a slippage factor. Its piecewise inventory response is:

\[
R=
\begin{cases}
1-k+k\left(\frac{B_0}{B}\right)^2,&B<B_0,\\
\left(1-k+k\left(\frac{Q_0}{Q}\right)^2\right)^{-1},&Q<Q_0,\\
1,&\text{otherwise.}
\end{cases}
\]

Here \(B,Q\) are current base/quote inventories and \(B_0,Q_0\) are equilibrium targets. The documentation also derives the integrated trade amount for a base-shortage case:

\[
\Delta Q=i(B_2-B_1)\left(1-k+k\frac{B_0^2}{B_1B_2}\right),
\]

and the resulting average price \(\Delta Q/(B_2-B_1)\). It derives a quadratic solve for the post-trade inventory when only the quote amount is supplied.

**Curation boundary:** the marginal price, integral trade amount, average execution price, quadratic solve and equilibrium-regression target are all linked expressions from one PMM curve. They are not separate equation families. The source documents PMM V1/V2/V3 contexts; record the exact pool type (DVM, DSP, DPP or V3), parameter meanings, oracle/guide-price update rule and regression mode. The special cases \(k=0\) and \(k=1\) should be screened for overlap with constant-price and constant-product-like behaviour; do not count them separately.

## 2. LFJ / Trader Joe Liquidity Book

**Official source:** [LFJ Developer Docs — Concentrated Liquidity](https://developers.lfj.gg/concepts/concentrated-liquidity). The documentation describes liquidity divided into discrete bins, each with a fixed price; price moves to the next bin when the current bin's inventory is depleted. Consecutive bin prices form a geometric sequence controlled by bin step (for example, a step of 0.0001 gives successive prices proportional to \(1.0001^n\)).

The official docs contrast Liquidity Book with Uniswap v3: Uniswap v3 uses a continuous constant-product curve between ticks, while Liquidity Book uses fixed-price constant-sum behaviour within discrete bins. A secondary code-oriented source describes the per-bin value relation as \(L=P_iX+Y\); treat this as a code-trace lead and verify the exact accounting invariant and rounding in the pinned V2/V2.1 contracts before transcription.

**Curation boundary:** fixed-price bin accounting, geometric bin-price progression and bin-crossing transitions describe one discrete-bin AMM mechanism. Do not count each bin, bin-step setting, one-sided inventory state or swap-direction branch as a new equation. The state transition at bin exhaustion is piecewise/discrete and may require a deterministic algorithm benchmark rather than a single scalar equation.

## 3. Cross-family overlap and acceptance controls

- DODO PMM is distinct from the constant-product invariant: its marginal price is a piecewise function of inventory deviation from equilibrium and integrates to a protocol-specific trade amount. Still, its k=1 boundary and other special cases require algebraic-equivalence review.
- DODO price, integral trade, average price, quadratic inventory solution and regression-target update share one PMM source family.
- Liquidity Book's fixed-price bins differ from Uniswap v3's continuous constant-product intervals. Its bin-price progression is geometric, but that sequence is a discrete indexing rule, not a separate AMM invariant.
- Liquidity Book's per-bin constant-sum accounting must be verified against the exact protocol code and precision conventions; the current documentation is a source lead, not a complete primary mathematical specification.
- Do not count a different protocol name, bin width, fee setting or parameter choice as a structurally distinct equation.
- Source-family clustering and independence-unit decisions must reflect shared AMM design lineage and implementation reuse.

## Benchmarkability requirements

For PMM, specify guide price, equilibrium inventory, current inventory, slippage factor, pool version, regression mode, swap direction, fee convention and admissible positive domain. For Liquidity Book, specify bin step, bin index convention, initial price, token decimals, active-bin state, bin balances, rounding and boundary transitions. All formula records remain candidates pending code-level equivalence and exact version checks.

No experiment, live protocol call or workflow has been run.
