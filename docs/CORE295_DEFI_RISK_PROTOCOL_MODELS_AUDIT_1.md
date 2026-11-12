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


## 6. Aave V3 Origin: pinned health-factor and liquidation implementation audit

**Pinned source:** official Aave repository aave-v3-origin, commit 5c2eb37f39959dd491ba97fdc2af94bb4ee88f41 (2025-09-19). This is a reproducible source snapshot, not proof of the implementation deployed behind any particular market proxy.
- LiquidationLogic.sol, blob SHA 1f45295207de0309b9adf6ab16da19e47e235297
- GenericLogic.sol, blob SHA 4c923df4aab9eece6c68bfe0ffa4c05a30842733
- Repository commit: https://github.com/aave/aave-v3-origin/commit/5c2eb37f39959dd491ba97fdc2af94bb4ee88f41
- Liquidation implementation: https://github.com/aave/aave-v3-origin/blob/5c2eb37f39959dd491ba97fdc2af94bb4ee88f41/src/contracts/protocol/libraries/logic/LiquidationLogic.sol
- Account aggregation: https://github.com/aave/aave-v3-origin/blob/5c2eb37f39959dd491ba97fdc2af94bb4ee88f41/src/contracts/protocol/libraries/logic/GenericLogic.sol

### Health factor aggregation

GenericLogic iterates the user's enabled collateral and borrowed reserves, values normalized aToken/debt balances using reserve prices and decimal units, and accumulates collateral and debt in the oracle base currency. It computes the collateral-value-weighted average liquidation threshold and then:
\[
HF =
\begin{cases}
+\infty,&D=0,\\
\displaystyle\frac{C\cdot \overline{LT}}{D},&D>0,
\end{cases}
\]
where \(C\) is total collateral value, \(D\) is total debt value, and \(\overline{LT}\) is the collateral-value-weighted liquidation threshold. The implementation uses PercentageMath and WadRayMath fixed-point operations. In efficiency mode, reserve-specific category liquidation thresholds may replace ordinary reserve thresholds for eligible collateral. Thus HF is an aggregate state-dependent risk metric, not a standalone universal constant-parameter equation.

### Liquidation execution and close factor

LiquidationLogic recalculates the account HF and reserve-specific balances, validates the liquidation (including the price-oracle sentinel), selects the applicable liquidation bonus (efficiency-mode category or reserve config), and obtains both collateral and debt prices and decimal scales. In this pinned snapshot:
- default close factor is 50%;
- full liquidation is permitted when HF is at or below 0.95, or when the debt/collateral value is below the configured small-position threshold;
- for positions above the small-position threshold and with HF above 0.95, the maximum repay may be capped at 50% of total account debt, translated into the selected debt reserve's units;
- the implementation enforces a minimum residual debt and collateral value when neither side is fully cleared, to prevent dust positions.

These constants are code-snapshot values and must not be generalized to all Aave markets or future versions.

### Collateral conversion, protocol fee and bad debt

The helper _calculateAvailableCollateralToLiquidate first converts debt-to-cover into base collateral using the two oracle prices and token decimal units, then applies the liquidation bonus. If the borrower's collateral balance is insufficient, it caps collateral at the user's balance and inversely computes the debt amount needed. The protocol fee is taken from the bonus portion, not from the base collateral amount. The liquidation path then burns debt tokens, updates reserve accounting, transfers or burns collateral aTokens according to the receiveAToken flag, transfers the protocol fee to treasury, and transfers the repaid debt asset to the reserve. If collateral is exhausted while debt remains, the implementation records a reserve deficit and burns the remaining bad debt according to its bad-debt path.

**Structural disposition:** the weighted health-factor ratio, close-factor rule, collateral/debt price conversion, bonus, protocol-fee extraction, dust guard and bad-debt write-off form one coupled liquidation mechanism. Do not count HF, liquidation price, close-factor percentage, bonus conversion and fee formula as independent equation candidates. The scalar HF<1 eligibility boundary is structurally related to Compound Comet's weighted collateral/debt liquidation predicate; protocol-level state transitions differ, but neither deserves multiple rows from its subexpressions. Before a production claim or candidate benchmark, match chain, market proxy, implementation bytecode, reserve configuration, eMode category and oracle state at a specified block. No chain/RPC calls were made.


### 6.1 Later Aave V3 Origin 3.7 snapshot: arithmetic and rounding delta

A later official repository snapshot is available at aave-dao/aave-v3-origin commit 8305565ae342f1773c42cd2e4593f175fe5968a0 (2026-09-09):
- LiquidationLogic.sol blob SHA 581d451f0e24bc6853aece8afc2228226c50c510
- GenericLogic.sol blob SHA 7b9820133e7f76c2acf6e7b304c7143b2da3f126
- Commit: https://github.com/aave-dao/aave-v3-origin/commit/8305565ae342f1773c42cd2e4593f175fe5968a0

The later snapshot retains the same high-level 50% default close factor, 0.95 HF threshold, 2000e8 minimum base threshold and half-threshold minimum leftover. The collateral conversion helper now uses explicit directional rounding helpers: percentMulFloor for bonus-adjusted collateral, percentDivCeil when converting a collateral-limited position back into debt repayment, percentDivFloor for the base-collateral component of the bonus, and percentMulCeil for the protocol fee. The helper also no longer returns the prior snapshot's collateral-to-liquidate base-currency diagnostic value.

GenericLogic's health-factor numerator is accumulated directly as the sum of collateral base value times its liquidation-threshold percentage, then converted to WAD and divided by 10,000 and total debt. The prior snapshot first computed a collateral-value-weighted average threshold and then multiplied total collateral by that average threshold. These are algebraically equivalent in exact arithmetic, but not necessarily bit-for-bit identical under integer truncation and changed rounding rules. The later code comments explicitly document the intermediate decimal scales.

**Version rule:** retain the 2025 source snapshot above as a historical pinned implementation; do not silently treat it as current. For a current 3.7 implementation adapter, use the 2026-09-09 aave-dao snapshot and its rounding semantics. Both are source snapshots only; the deployed proxy implementation and reserve configuration must still be pinned separately. No live chain calls were made.


## 7. Compound Comet liquidation-factor semantics: specification versus Solidity

A closer cross-check of the pinned v2.5 specification and Solidity implementation resolves an important naming trap, but does not eliminate the version/release reconciliation requirement.

The specification distinguishes three asset-level risk parameters: (i) the borrow collateral factor, used to constrain new borrowing; (ii) the liquidation collateral factor, used in the liquidatability test; and (iii) the liquidation factor, described as the fraction of collateral value received in the base token when liquidated. The first two are threshold weights in the signed-liquidity calculation; the third is a collateral valuation/settlement parameter, not another threshold.

The Solidity `AssetInfo` struct likewise stores separate `borrowCollateralFactor`, `liquidateCollateralFactor`, and `liquidationFactor` fields. The implementation-level absorb path values seized collateral using `liquidationFactor`, while `isLiquidatable` uses `liquidateCollateralFactor`. The later `buyCollateral` path uses `storeFrontPriceFactor` together with the complement of `liquidationFactor` to determine the storefront discount. Thus the code's factor is not simply a percentage fee applied to the user's debt; it is part of the protocol's collateral acquisition/resale economics.

For interpretation, keep these operations separate within one coupled Comet state-transition model:

- **Eligibility:** signed base liquidity plus each collateral value weighted by its liquidation collateral factor; absorb is allowed when the resulting liquidity is negative.
- **Absorption settlement:** seized collateral is removed from the account, valued with oracle/scale conversions and the liquidation factor, and applied to the signed base balance; a negative residual is clamped to zero, with aggregate principal/supply/borrow accounting updated.
- **Reserve restoration:** protocol-held collateral can later be sold through `buyCollateral`, with the storefront discount derived from the storefront factor and the complement of the liquidation factor, subject to reserve and minimum-output constraints.

This cross-check supports the prior warning that the specification's prose and Solidity's accounting should not be mixed as if they were one line-for-line algorithm. It does **not** establish that the pinned development snapshot matches any deployed market. The exact source release, deployed implementation bytecode, immutable configuration and market-specific asset factors remain necessary for a production reconstruction. No RPC, explorer API, contract execution or live protocol call was made.

**Structural disposition:** retain one candidate coupled protocol-level absorption/settlement state machine. Do not count the liquidation-factor formula, liquidatability inequality, collateral offset, storefront quote and principal update as independent equation rows. The threshold component remains structurally related to Aave's weighted collateral/debt health-factor eligibility test.


## 8. Morpho Blue: pinned direct-liquidation and bad-debt accounting audit

**Pinned source:** official `morpho-org/morpho-blue` repository, commit `430bd61d8ab9238c1bde327eec2bfcd3f494fe9d` (2026-11-09).
- Core implementation: `src/Morpho.sol`, blob SHA `ab064b646bf161b1510e2575a99412cdc2a43ebb`.
- Constants: `src/libraries/ConstantsLib.sol`, blob SHA `1046e6a03462fb68b78dbdcee26339c983dc00de`.
- Fixed-point arithmetic: `src/libraries/MathLib.sol`, blob SHA `3c0afc991c3bfa9314498b43047a0675be4a9410`.
- Share/asset conversion: `src/libraries/SharesMathLib.sol`, blob SHA `c63d937e81d5470e2d073383f45dd66c46f36a6b`.
- Commit: https://github.com/morpho-org/morpho-blue/commit/430bd61d8ab9238c1bde327eec2bfcd3f494fe9d
- Core implementation: https://github.com/morpho-org/morpho-blue/blob/430bd61d8ab9238c1bde327eec2bfcd3f494fe9d/src/Morpho.sol

This is a pinned repository snapshot, not a mapping to a particular deployed contract address, chain, market or oracle state. Morpho Blue markets are isolated one-loan-token/one-collateral-token markets with an oracle and immutable market LLTV. The source snapshot must not be mistaken for the market's runtime values or for optional periphery liquidation products.

### Eligibility

For a borrower position in one market, the implementation converts borrow shares to debt assets with upward rounding and computes collateral borrowing capacity with downward rounding:
\[
D=\operatorname{toAssetsUp}(s_D;B_D,S_D),
\qquad
C_{\max}=\operatorname{wMulDown}\!\left(
\operatorname{mulDivDown}(c\,P,10^{36}),\,LLTV
\right).
\]
The position is healthy iff \(C_{\max}\ge D\); it is liquidatable when this predicate is false. The oracle price uses the source's \(10^{36}\) scale and the market's fixed LLTV. This is a single-market collateral/debt threshold, not a weighted multi-collateral aggregation.

### Liquidation incentive and direct exchange

The implementation defines:
\[
LIF=\min\!\left(
1.15,\,
\frac{1}{1-0.3(1-LLTV)}
\right),
\]
with WAD-scaled fixed-point operations, downward rounding in the division and the constants \(LIQUIDATION\_CURSOR=0.3\), \(MAX\_LIQUIDATION\_INCENTIVE\_FACTOR=1.15\). The incentive decreases as LLTV rises, subject to the 1.15 cap. This is a direct repay-for-collateral transaction, not an auction. The core contract permits the caller to specify exactly one of collateral assets seized or debt shares repaid; it derives the other amount using the oracle, LIF and share/asset conversion routines. The two directions intentionally use different rounding:
- specified seized collateral: quote collateral with upward rounding, divide by LIF with upward rounding, then convert repayment assets into shares with upward rounding;
- specified repayment shares: convert shares to debt assets with downward rounding, multiply by LIF with downward rounding, then convert quote value to collateral assets with downward rounding.
The final repaid asset amount is converted from shares with upward rounding.

### Bad debt and market accounting

After repayment and collateral seizure, if the borrower's collateral balance reaches zero while debt shares remain, the implementation writes off the remaining borrower debt shares. It computes the residual debt assets, bounded by aggregate borrow assets, then reduces aggregate `totalBorrowAssets`, `totalSupplyAssets` and `totalBorrowShares`, and clears the borrower's borrow shares. This is a lender-side loss realization through the market's supply accounting, not Aave's reserve-deficit path or Comet's absorption/reserve model.

Interest is accrued before liquidation. The core accrual uses the configured IRM's borrow rate and a three-nonzero-term Taylor approximation to continuous compounding, then adds interest to both total borrow and supply assets; any market fee is converted to fee-recipient supply shares. These accrual and share-conversion operations are integral to the state transition and should not be split into extra liquidation equation rows.

**Structural disposition:** Morpho Blue is a strong candidate for one protocol-level direct-liquidation/state-transition family: single-market LLTV eligibility, LLTV-dependent incentive, caller-selected partial/full repay/seize sizing, fixed-point rounding and collateral-exhaustion bad-debt write-off. The threshold inequality alone remains related to Aave and Comet collateral/debt eligibility and is not a separate structural equation. Do not split LIF, the two quote directions, share conversions and bad-debt accounting into independent candidate rows. Optional pre-liquidation periphery contracts are a separate extension and are not part of this core `Morpho.sol` snapshot. No RPC, deployment lookup, contract execution, tests or simulation were performed.


## 9. Maker/Sky Liquidation 2.0: Dog, Clipper and Abaci

**Pinned implementation snapshot.** The official repository is now maintained as `sky-ecosystem/dss`. The source snapshot used here is commit `c8d4c806691dacb903ff281b81f316bea974e4c7` (2021-04-02, the upstream “Liq 2.0” integration commit):
- `src/dog.sol`, blob SHA `7ded73181503e85e79b0d2e58f668426b60ff03d`
- `src/clip.sol`, blob SHA `96a085848cb26cc5d3232004adcd6782e43253a2`
- `src/abaci.sol`, blob SHA `8aa7fb96cfc5c630512751096d62a3bf551fd917`

Pinned commit: https://github.com/sky-ecosystem/dss/commit/c8d4c806691dacb903ff281b81f316bea974e4c7. This is an implementation snapshot, not evidence that a particular present-day Sky deployment uses these exact bytecodes or parameters. MIP45 itself is marked obsolete by MIP102c2-SP1; it remains useful as historical design context, not as the current governance specification.

### Liquidation eligibility and debt/collateral extraction

For collateral type (i), the source checks the unsafe-vault predicate
\[
ink\cdot spot < art\cdot rate,
\]
where (ink) is collateral, (art) is normalized debt, and (spot)/(rate) are the Vat collateral safety price and accumulated debt rate. The liquidation capacity is constrained by both global and collateral-specific auction headroom:
\[
room=\min(Hole-Dirt,\;hole_i-dirt_i),
\qquad
dart=\min\!\left(art,\left\lfloor\frac{room\cdot WAD}{rate\cdot chop_i}\right\rfloor\right).
\]
If the residual debt after a partial liquidation would be below the collateral's dust threshold, the implementation liquidates the full remaining debt instead; otherwise it rejects a partial auction whose debt is itself below dust. Collateral removed is proportional and rounded down:
\[
dink=\left\lfloor\frac{ink\cdot dart}{art}\right\rfloor.
\]
The debt engine confiscates (dink,dart), the Vow records due debt (due=dart\cdot rate), and the auction target is
\[
tab=\left\lfloor\frac{due\cdot chop_i}{WAD}\right\rfloor.
\]
Global and per-collateral `Dirt` accumulators are increased by (tab), then `Clipper.kick` is called. The exact code order, integer divisions and dusty-vault exception matter; these expressions are not interchangeable with a continuous-arithmetic simplification.

### Dutch auction start and time-dependent price

`Clipper.kick` reads the OSM feed, converts it against `par`, and sets
\[
feedPrice=\operatorname{rdiv}(val\cdot 10^9,par),
\qquad
top=\operatorname{rmul}(feedPrice,buf).
\]
The configured Abacus implementation then maps initial price and elapsed seconds to the current auction price. The pinned `abaci.sol` contains three alternatives:
- Linear: (P(t)=top\,(tau-t)/tau) for (t<tau), and zero thereafter.
- Stairstep exponential: (P(t)=top\cdot cut^{\lfloor t/step\rfloor}).
- Continuous exponential: (P(t)=top\cdot cut^t).

The exponential forms use RAY fixed-point exponentiation-by-squaring with half-up intermediate rounding in `rpow`; the stairstep form quantizes elapsed time by integer division. These are configurable alternative implementations of one price-calculator interface, not three independent liquidation-system candidates. The source also allows governance to change calculator and parameters, so a running auction's quote need not be monotone if governance changes its configuration or calls `redo`.

### Purchase, auction reset and accounting

`Clipper.take` enforces the buyer's maximum price, caps the collateral slice by the caller's requested amount and remaining lot, and caps DAI owed by the auction's remaining `tab`. The implementation applies a `chost` floor to partial purchases to avoid leaving a small residual target; `chost` is refreshed from Vat dust and Dog liquidation penalty. It transfers collateral, optionally invokes the composable callee, moves DAI to the Vow, and calls `Dog.digs` to release the corresponding global/per-collateral auction capacity. Completion either removes the auction or returns excess collateral when the debt target is reached.

An auction needs reset when elapsed time exceeds `tail` or current price divided by starting price falls below `cusp`. `redo` resets the timestamp and recomputes `top` from the current OSM price and `buf`; eligible keeper incentives use the flat `tip` plus a `chip`-scaled amount. Circuit-breaker levels separately disable new kicks, resets, and takes.

**Structural disposition:** this is a strong lead for one coupled protocol-level Dutch-auction liquidation/state-transition family: unsafe-vault test, global/per-collateral capacity constraints, partial/dust-aware confiscation, oracle-buffered starting price, time-decaying price, partial purchase/settlement and accumulator updates. It is structurally different from Morpho Blue's direct repay-for-collateral liquidation, while the collateral/debt eligibility inequality remains a related risk-threshold motif shared with Aave and Comet. Do not count `Dog.bark`, the three Abacus alternatives, `Clipper.take`, reset logic or keeper incentives as separate equations.

**Version and evidence caveats.** MIP45 is explicitly marked obsolete by MIP102c2-SP1. Sky's current developer documentation still describes Liquidation 2.0's Dutch-auction mechanics, but this audit does not map a current deployment, chain, Dog/Clipper/Abacus addresses, bytecode, collateral ilk, OSM state or governance parameters. The source snapshot and historical MIP must therefore remain provenance evidence, not a claim about live market configuration. No RPC, deployment lookup, contract execution, tests, simulation or experiment was performed.


## 10. Euler V2 / Euler Vault Kit: reverse-Dutch discount and debt-transfer liquidation

**Pinned implementation snapshot.** Official repository `euler-xyz/euler-vault-kit`, commit `93a1de491531e54cbbcf0e5c8cacfe558f924867` (2026-10-29):
- `src/EVault/modules/Liquidation.sol`, blob SHA `8ce05719f1200e543b1b81ad5c749780e4cf7df4`
- `src/EVault/shared/LiquidityUtils.sol`, blob SHA `e6b68e28284c404b72608bd9213721ab9b54ad0c`
- `src/EVault/shared/BorrowUtils.sol`, blob SHA `e60faf14e1d1d9fcc607f793455c96d7e0188688`
- `src/EVault/modules/RiskManager.sol`, blob SHA `4f78db4dab2ba07ad0e6dc9c9f41822109a55140`
- `src/EVault/modules/Governance.sol`, blob SHA `08c5c96f0a356381ca14d02d48defe1b570c6120`

Pinned commit: https://github.com/euler-xyz/euler-vault-kit/commit/93a1de491531e54cbbcf0e5c8cacfe558f924867. This is a versioned source snapshot, not a deployment/proxy or live vault-configuration match.

### Health and liquidation discount

The liability vault evaluates all enabled collateral assets using the liquidation LTVs and oracle mid-point quotes. For each collateral (j), the collateral contribution is the mid-point oracle value multiplied by its configured liquidation LTV and divided by `CONFIG_SCALE`; contributions are summed. Liability value is the current accrued debt, rounded up to assets, valued at the mid-point oracle quote (or directly in the unit of account). Let the aggregate adjusted collateral and liability values be (C_L) and (D). Liquidation is eligible when
\[
C_L\le D,\qquad D>0.
\]
The liquidation health ratio is
\[
h=\frac{C_L}{D}.
\]
The code clamps the discount factor from below using the configured maximum liquidation discount. Governance rejects a maximum discount equal to `CONFIG_SCALE`, because that would make the liquidation division by zero (d_{max}):
\[
q=\max\!\left(h,1-d_{max}\right).
\]
Thus the effective collateral discount is (1-q): it is zero at the threshold, grows with the health shortfall, and is capped by (d_{max}). This is health-dependent pricing, not an elapsed-time Dutch auction. Euler documentation calls the mechanism a reverse Dutch auction; do not infer a time-decay state variable from that label.

### Debt transfer and collateral yield

For the selected collateral, the implementation values the violator's available collateral at the mid-point oracle price. Before collateral caps, it sets maximum repay value to the full liability value and maximum collateral yield value to
\[
V_{repay}^{max}=D,
\qquad
V_{yield}^{max}=\frac{D}{q}.
\]
If the selected collateral is insufficient to deliver that yield, the source caps yield to the available collateral value (V_c) and reduces repay value:
\[
V_{yield}^{max}=V_c,
\qquad
V_{repay}^{max}=V_c q.
\]
These values are converted proportionally into the actual debt asset amount and collateral-token balance using the accrued liability amount and collateral balance. A caller may request a smaller repay; the corresponding collateral yield is scaled pro rata using integer division. The implementation rejects self-liquidation, unrecognized or disabled collateral, a violator with deferred EVC account checks, and liquidation inside the configured cool-off interval. The liquidator must satisfy the EVC/controller and collateral constraints.

Unlike Aave- or Morpho-style repay-and-seize flows, the liquidator takes over the violator's selected liability through an internal debt transfer and receives collateral in the same operation; the liquidator does not simply send an external repayment asset to extinguish the debt. The transfer uses the vault's accrued debt accounting and includes dust-aware exact-owed handling.

### Residual debt socialization

After the debt and collateral transfer, remaining debt may be socialized only if all code gates pass: the pre-liquidation liability value is at least (10^6) units of the unit of account; the vault has not disabled debt socialization; the violator still has liability exceeding the transferred repay; and no recognized collateral balance remains. The remaining owed amount is then removed from the violator's borrow balance and reflected in vault accounting. This is conditional loss allocation, not an unconditional consequence of every liquidation.

**Structural disposition:** a strong candidate for one coupled Euler V2 liquidation/state-transition family: multi-collateral liquidation-LTV health aggregation, health-shortfall-dependent capped discount, collateral-limited repay/yield sizing, internal debt transfer to the liquidator, EVC/cool-off safeguards and conditional residual-debt socialization. The weighted collateral/debt eligibility test is related to Aave and Compound risk aggregation, but the reverse-discount function and debt-transfer settlement are a distinct mechanism. Do not count the health ratio, discount cap, collateral cap, debt transfer and socialization branches as independent equations.

**Version and deployment caveats.** Euler V2 uses modular EVault deployments and per-vault integrations/configuration. This snapshot does not identify a deployed EVault proxy, module set, collateral-vault list, oracle route, unit of account, LTV schedule, max discount, cool-off value, configuration flags or block state. The source's `BUSL-1.1` liquidation module and GPL-2.0-or-later shared utility files are also distinct license headers; preserve these provenance details. No RPC, deployment lookup, contract execution, tests, simulation or experiment was performed.
