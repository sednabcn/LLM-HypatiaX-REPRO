# Core-295 DeFi Risk protocol-model audit 1: Aave V3 and Compound Comet

**Date:** 2026-11-11  
**Scope:** Official protocol documentation and specification review; no on-chain calls, live API calls, contract execution, validator or experiment run.

## 1. Aave V3 health factor

The official Aave V3 Health Factor Preview documentation gives

[
HF=\frac{V_C\,\overline{LT}}{V_D},
]

where (V_C) is total collateral value, ̅LT is the weighted-average collateral factor/liquidation threshold, and (V_D) is total borrow value. A position with (HF<1) is eligible for liquidation. Aave's FAQ independently explains the same ratio and explicitly cautions that liquidation price is not a single scalar when several collateral and debt assets/oracle prices are present.

**Disposition:** This is the same health-factor family already registered under `RISK-AAVE-FAQ` and `RISK-AAVE-V3`. The new V3 developer page is complementary provenance, not a new equation entry. Do not count a liquidation-price rearrangement as another equation; for multi-asset positions it is generally a surface/curve in the vector of oracle prices, not one universal scalar price.

## 2. Compound Comet borrow and supply rates

The official Comet specification defines utilization as total present-value borrows divided by total present-value supply (zero when supply is zero). Borrow rate is piecewise linear around a utilization kink (u_k):

[
r_b(u)=
\begin{cases}
r_0+s_Lu,&u\leq u_k,\\
r_0+s_Lu_k+s_H(u-u_k),&u>u_k.
\end{cases}
]

The supply rate in the same specification multiplies the borrow rate by utilization and the retained share after the reserve rate. Interest indices accrue multiplicatively over elapsed time:

[
I_{t+\Delta t}=I_t(1+r\Delta t)
]

under the specification's per-second rate and elapsed-time convention.

**Disposition:** The kinked piecewise-linear form is a real protocol-specific model, but its normalized structure is shared with Compound V2 jump-rate models and Aave's two-slope utilization models. Under the current draft E3 rule, these are mechanism/protocol diversity leads, not separate structural equation counts solely because their parameters, clock units or naming differ. The prior generic quartic borrow-rate sketch remains unsupported and should not be treated as Compound III's rate law.

**Version caveat:** The specification page identifies itself as Comet v2.5. The source snapshot is now pinned below; it is not yet matched to a specific deployed market or proxy implementation.

## 3. Compound Comet liquidation is not Aave's liquidation mechanism

The Comet specification defines borrowing collateralization and liquidatability using signed account liquidity. For each collateral asset, value is multiplied by a borrow collateral factor or a liquidation collateral factor and accumulated against base-token debt value. The liquidation predicate is negative liquidity under liquidation factors. The `AbsorbInternal` transition transfers seized collateral to the protocol, accounts for liquidation penalties, applies the collateral value against the account balance, and adjusts supply/borrow principal; the protocol subsequently sells collateral to rebuild reserves.

This is structurally more than a scalar health-factor display: it is a protocol state transition with collateral seizure, debt absorption, penalty, reserve effects and subsequent collateral sale. Nevertheless, the threshold test is a weighted-collateral-versus-debt inequality closely related to Aave's HF < 1 test. Do not count the threshold inequality as a new structural family. The complete absorb-and-accounting state machine may be studied as a protocol-level system, but only with an explicit state/transition model and pinned code/spec version.

## 4. Candidate disposition

| Candidate | Structural screen | Next action |
|---|---|---|
| Aave V3 health factor | Existing family; duplicate documentation source | Keep one family; define multi-collateral weighted aggregation and oracle units |
| Aave liquidation price | Derived threshold locus, not a universal scalar equation | Exclude as separate row |
| Compound Comet borrow rate | E3 normalized kinked piecewise-linear utilization model | Keep as protocol lead, not independent count from equivalent kinked rate laws |
| Compound Comet supply rate | Derived from borrow rate × utilization × reserve share | Same rate family; not separate count |
| Compound Comet index accrual | Discrete multiplicative state update tied to rate and elapsed time | Model with principal/index state; do not count each balance rearrangement separately |
| Compound Comet liquidatability | Weighted collateral-debt threshold, related to Aave HF | Do not count scalar threshold separately |
| Compound Comet absorption | Multi-state collateral seizure, penalty, debt absorption and reserve accounting | Potential protocol-level model; full state transition and version pin required |


## 4. Version-pinned Comet absorption transition

A reproducible repository snapshot is now pinned:

- Repository: https://github.com/compound-finance/comet
- Commit: `f766f51583c23acc33b2a7824654ef2029a96804` (2026-06-23)
- Specification: https://github.com/compound-finance/comet/blob/f766f51583c23acc33b2a7824654ef2029a96804/SPEC.md
- Implementation: https://github.com/compound-finance/comet/blob/f766f51583c23acc33b2a7824654ef2029a96804/contracts/CometWithExtendedAssetList.sol
- Math helpers: https://github.com/compound-finance/comet/blob/f766f51583c23acc33b2a7824654ef2029a96804/contracts/CometMath.sol

The pinned `SPEC.md` metadata labels the specification `v2.5`. This pins a source snapshot, **not** a deployed market/proxy implementation. A market-specific record still needs the chain, market/proxy, implementation address and implementation bytecode/source match. No live RPC, explorer API or on-chain call was made.

### Implementation-level transition in `absorbInternal`

The implementation does the following:

1. Requires `isLiquidatable(account)`; snapshots the borrower's signed principal and present-value base balance.
2. Iterates the borrower's asset-membership bitmap. For each included collateral asset, reads the collateral balance, zeroes the borrower's balance, decrements `totalsCollateral[asset].totalSupplyAsset`, values the seized amount using asset price and scale, and adds `value × liquidationFactor` to `deltaValue`.
3. Converts the collateral offset into base units using the base-token price and base scale: `deltaBalance = divPrice(deltaValue, basePrice, baseScale)`.
4. Adds this offset to the old signed base balance. If the result is negative, clamps it to zero; the residual shortfall is borne through protocol reserves rather than leaving a negative borrower balance.
5. Converts the nonnegative balance to new principal and calls `updateBasePrincipal`; clears the borrower's `assetsIn` and reserved bitmap.
6. Computes `repayAmount` and `supplyAmount` from old and new principal; increases `totalSupplyBase` by the supply amount and decreases `totalBorrowBase` by the repay amount.
7. Emits `AbsorbDebt` using `basePaidOut = newBalance - oldBalance`, alongside collateral/debt events.

Important implementation distinctions:
- This snapshot uses `liquidationFactor` in the collateral-offset calculation; do not substitute a generic `liquidationPenalty` parameter.
- It updates borrower principal and aggregate principal accounting, not merely a market-value debt scalar.
- The `absorb` wrapper accrues interest before processing accounts and records liquidator-point statistics. The pinned implementation does not establish a universal cash incentive transfer to the absorber; do not import older specification wording as if it were identical implementation behavior.
- `buyCollateral` is a separate subsequent mechanism. It accepts base-token payment, prices collateral with a store-front discount derived from `storeFrontPriceFactor` and `liquidationFactor`, and transfers protocol-held collateral subject to minimum amount and available-reserve checks.

This is a coupled protocol state transition involving multiple storage variables, price feeds, index/principal conversions and event outputs. It is a candidate system-level family only if the benchmark unit is explicitly the full absorption/accounting transition. Do not count intermediate scalar formulas as independent equation rows.

## 5. Sources

- Compound Comet specification: https://github.com/compound-finance/comet/blob/main/SPEC.md
- Compound III interest-rate docs: https://docs.compound.finance/interest-rates/
- Aave V3 health factor preview: https://www.aave.com/docs/aave-v3/markets/health-factor
- Aave FAQ / liquidation semantics: https://www.aave.com/faq
- Aave V3 pool contract liquidation interface: https://aave.com/docs/aave-v3/smart-contracts/pool?language=en

No formal catalogue equation entry was added or accepted by this audit.
