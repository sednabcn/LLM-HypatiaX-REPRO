# Core-295 source verification audit 47: Liquity V1 Stability Pool product-sum accounting

**Date:** 2026-11-11  
**Status:** verification of existing source-register lead RISK-LIQUITY-STABILITY-POOL; no equation is added to the formal catalogue or counted toward 295.

## 1. Pinned implementation and scope

Repository: liquity/dev  
Commit: 3e64ee1b52c50d51587c64c1cf75e0ba82934979  
File: packages/contracts/contracts/StabilityPool.sol  
Blob SHA: 160433359c03930109b749584cad42b30a53de13

The Stability Pool receives LUSD deposits and absorbs eligible liquidated Trove debt in exchange for the liquidated collateral. The contract's offset operation is called by TroveManager liquidation paths. It calculates per-unit depositor collateral gain and deposit loss, updates cumulative product/sum state, burns offset LUSD and transfers collateral into the pool.

## 2. Per-unit loss and collateral gain

Let \(D\) be the debt offset, \(C\) the collateral added and \(T\) the total pool deposits before offset. In ideal real arithmetic:
\[
\ell=\frac{D}{T},\qquad
g=\frac{C}{T}.
\]
The contract scales by \(10^{18}\), carries forward prior division errors, and deliberately adds one unit to the rounded loss-per-unit quotient so that the loss slightly favors the pool:
\[
\widehat\ell=
\left\lfloor\frac{D\cdot10^{18}-e_{\ell,\mathrm{old}}}{T}\right\rfloor+1,
\qquad
\widehat g=
\left\lfloor\frac{C\cdot10^{18}+e_{g,\mathrm{old}}}{T}\right\rfloor.
\]
The new error residuals are stored for the next offset. The loss branch guards against subtraction underflow when the prior loss residual exceeds the current scaled debt offset.

## 3. Product-sum state

The contract tracks:
- \(P\): cumulative product representing the surviving fraction of a depositor's initial stake;
- \(S\): cumulative collateral gain per unit of initial deposit, in the current scale;
- a scale index to preserve precision as \(P\) becomes small.

Ignoring fixed-point rounding and scale transitions:
\[
P_{n+1}=P_n(1-\ell_n),
\qquad
S_{n+1}=S_n+P_n g_n.
\]
The update order matters: \(S\) is incremented using the pre-update \(P_n\), because the collateral gain from a liquidation is allocated against deposits immediately before that liquidation loss.

For an initial deposit \(d_0\) with snapshots \(P_0,S_0\), the contract's idealized claims are:
\[
d_n=d_0\frac{P_n}{P_0},
\qquad
G_C=d_0\frac{S_n-S_0}{P_0}.
\]
The implementation accounts for one scale transition by dividing the compounded deposit by SCALE_FACTOR; if two or more scale transitions occur, it returns zero for the residual compounded stake. Snapshot/scale indexing and fixed-point rounding are part of the model, not independent formulas.

## 4. Structural classification

The product-sum accumulator is a coupled path-dependent accounting system. It is not a generic one-step liquidation-bonus equation or a lending health factor. It represents sequential pro-rata deposit depletion and collateral-gain allocation across liquidation events.

The following belong to one Stability Pool system family:
- per-unit collateral gain and debt loss;
- error-feedback residual updates;
- cumulative \(P\) and \(S\) recurrences;
- scale transitions;
- depositor compounded-deposit and collateral-gain snapshot formulas;
- liquidation offset and token/collateral transfers.

Do not count any of those components, the individual liquidations or different scale/decimal parameters as separate equation units. A complete Liquity liquidation waterfall (Stability Pool offset followed by redistribution and Recovery Mode rules) is broader than the accumulator and must not be silently substituted for it.

## 5. Adapter and validity requirements

A deterministic adapter must freeze:
- exact Liquity V1 contract generation and commit;
- stablecoin and collateral asset units/decimals;
- initial pool deposits, sequence of debt offsets and collateral additions;
- eligible liquidation ordering and maximum debt offset;
- fixed-point precision, error-feedback residuals, quotient rounding and scale factor;
- depositor snapshot timing and scale-difference handling;
- whether the sampled unit is only the accumulator or the full TroveManager liquidation waterfall.

The current source tree's contract names and documentation must be checked against the exact V1 deployment/version before any benchmark adapter is authored; do not conflate Liquity V1 with Liquity V2/BOLD or later forks.

## 6. Decision

**Disposition:** pinned source confirms a nontrivial product-sum accumulator for pro-rata liquidation loss and collateral gain. Retain as a potentially distinctive DeFi Risk complete-system lead, held pending exact deployment/version confirmation and the benchmark's system-unit policy. The per-unit ratios, P/S recurrences, snapshot claims and scale mechanics are one coupled family, not a source of multiple equation counts.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, on-chain reads or transactions were run. This is static-source review only.
