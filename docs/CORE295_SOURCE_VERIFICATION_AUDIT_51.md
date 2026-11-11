# Core-295 source verification audit 51: Fixed-spread liquidation optimization and two-call close-factor strategy

**Date:** 2026-11-11  
**Status:** verification of existing source-register lead RISK-UCL-LIQUIDATIONS; no equation is added to the formal catalogue or counted toward 295.

## 1. Primary research source

Kaihua Qin, Liyi Zhou, Pablo Gamito, Philipp Jovanovic and Arthur Gervais, “An Empirical Study of DeFi Liquidations: Incentives, Risks, and Instabilities,” ACM Internet Measurement Conference (IMC '21), 2021, pp. 336–350, DOI 10.1145/3487552.3487811; arXiv:2106.06389v2.

The paper compares the liquidation designs of Aave, Compound, MakerDAO and dYdX. It distinguishes MakerDAO's auction-based liquidation from the fixed-spread atomic liquidation mechanisms studied for Aave, Compound and dYdX at the time.

## 2. Generic collateralization and fixed-spread definitions

For collateral value \(C\), debt value \(D\), liquidation threshold \(LT\), liquidation spread \(LS\) and close factor \(CF\), the paper defines:
\[
CR=\frac{C}{D},\qquad
BC= C\cdot LT,\qquad
HF=\frac{BC}{D}.
\]
For a fixed-spread liquidation that repays debt value \(r\), the liquidator claims collateral worth:
\[
V_{\mathrm{claim}}=r(1+LS).
\]
Under the paper's single-asset/scalar simplification, the remaining position after the liquidation is:
\[
(C',D')=(C-r(1+LS),\,D-r).
\]

These are generic abstractions of fixed-spread lending liquidation, not new protocol-specific equations. The multi-asset health factor is the same collateral-weighted borrowing-capacity ratio family already covered in Audit 44.

## 3. Two-successive-liquidation optimization

The paper's Algorithm 2 chooses the first repayment as large as possible while keeping the post-liquidation position eligible for liquidation:
\[
r_1=
\arg\max_r
\frac{LT\,[C-r(1+LS)]}{D-r}
\quad\text{subject to}\quad
\frac{LT\,[C-r(1+LS)]}{D-r}<1.
\]
For an initially liquidatable position (\(D-LT\,C>0\)) and the paper's reasonable-configuration condition \(1-LT(1+LS)>0\), its closed-form result is:
\[
r_1=\frac{D-LT\,C}{1-LT(1+LS)}.
\]
The second repayment is then the close-factor limit applied to the residual debt:
\[
r_2=CF(D-r_1).
\]
The paper derives total liquidator profit:
\[
\Pi_o=LS(r_1+r_2)
=LS\cdot CF\cdot D+
LS(1-CF)\frac{D-LT\,C}{1-LT(1+LS)}.
\]
For the up-to-close-factor strategy, the profit is:
\[
\Pi_c=LS\cdot CF\cdot D.
\]
The relative profit increase is:
\[
\Delta R_{\Pi}=
\frac{\Pi_o-\Pi_c}{\Pi_c}
=
\frac{CF}{1-CF}\,
\frac{1-LT\cdot CR}{1-LT(1+LS)}.
\]
These equations are tied to the paper's idealized two-call strategy. They assume fixed prices, a constant liquidation spread and threshold, no intervening interest/market movement, and that the first liquidation leaves the position liquidatable. They do not model all current protocol close-factor rules or auction systems.

## 4. Structural and provenance classification

The two-call optimizer is a genuine analytical result in the paper, not merely an observed regression coefficient. However, it is derived from the same fixed-spread liquidation transition and collateralization constraint; its argmax, closed form, second repayment and profit expressions are one optimization family.

It is not a new universal lending health-factor equation. It is also not directly interchangeable with the newer protocol-specific mechanics in Morpho Blue, Euler EVK, Compound III or Sky Liquidations 2.0. Its protocol descriptions and close-factor assumptions reflect the 2019–2021 implementations studied in the paper.

A deterministic adapter would have to specify the scalar position abstraction, values \(C,D\), LT, LS, CF, admissible first-repayment interval, strict/weak liquidation inequality, denominator condition, and whether the benchmark includes only the optimizer or the entire two-call strategy.

## 5. Decision

**Disposition:** retain the two-call fixed-spread optimizer as a credible DeFi Risk analytical-system lead. It is mathematically distinct from a simple health-factor ratio and from protocol liquidation-incentive schedules, but it remains a derived optimization within one fixed-spread liquidation family. Hold pending the system-unit policy and a source-faithful adapter. Do not count \(r_1\), \(r_2\), profit and relative-profit equations as independent samples.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No experiments, blockchain replay, regressions, validators, solvers, workflows, paid compute, API calls, on-chain reads or transactions were run. This is paper-level mathematical and source review only.
