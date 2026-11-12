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


## 11. Liquity V2: Stability Pool offset, collateral penalty and stake-weighted redistribution

**Pinned implementation snapshot.** Official repository `liquity/bold`, commit `d262669ef3c4d37bf0544df3bb2624c07b8a5ee0` (2026-09-26):
- `contracts/src/TroveManager.sol`, blob SHA `389586974a407e59bb31dcd588070927d0992452`
- `contracts/src/StabilityPool.sol`, blob SHA `db0a24a56921e84c12d95f53f1841eff60f410a6`
- `contracts/src/Dependencies/Constants.sol`, blob SHA `9e0231988039464b070dc5cd325f7e35d35f1e22`
- `contracts/src/Dependencies/LiquityMath.sol`, blob SHA `d6d2474f370c27a630d92732de430b910e458ac5`

Pinned commit: https://github.com/liquity/bold/commit/d262669ef3c4d37bf0544df3bb2624c07b8a5ee0. The repository describes Liquity V2's multi-branch system; the pinned commit is a source snapshot, not a deployment/branch configuration match.

### Eligibility and liquidation input

The Trove Manager obtains the branch price and computes the individual collateral ratio from the entire trove state, including accrued interest and pending redistribution gains:
\[
ICR=\left\lfloor\frac{coll\cdot price}{debt}\right\rfloor.
\]
The pinned batch liquidation path processes active or zombie troves only when (ICR<MCR). The MCR, critical collateral ratio and shutdown collateral ratio are branch-specific values loaded through the AddressesRegistry; source constants include 110%/150%/110% for WETH and 120%/160%/120% for staked-ETH branches. Do not treat those constants as proof of a current deployed branch's live parameters.

### Priority Stability Pool offset

The batch path reserves a minimum 1 BOLD in the Stability Pool when deposits are at least 1 BOLD, then uses the remaining available deposits for offsets. For a trove with entire debt (D), collateral (C), and available offset deposits (S):
\[
D_{off}=\min(D,S),
\qquad
C_{SP,portion}=\left\lfloor\frac{C\,D_{off}}{D}\right\rfloor.
\]
Collateral gas compensation is (min(\lfloor C_{SP,portion}/200\rfloor,2\;ETH)). After subtracting that compensation, the offset collateral is capped at debt value plus the configured Stability Pool liquidation penalty:
\[
C_{SP}=\min\!\left(
C_{SP,portion}-G_C,
\left\lfloor\frac{D_{off}(1+p_{SP})}{price}\right\rfloor
\right).
\]
Any excess is recorded as borrower collateral surplus. The Stability Pool burns the offset BOLD, reduces each depositor's deposit proportionally, and receives the corresponding collateral. Its product-sum accounting updates the deposit product (P) and collateral gain sum (S), with scale changes when (P) becomes small.

### Residual redistribution

Debt not covered by the Stability Pool is redistributed to active troves in the same collateral branch:
\[
D_{red}=D-D_{off},
\qquad
C_{red,portion}=C-C_{SP,portion}.
\]
The collateral amount retained for redistribution is capped by (D_{red}(1+p_{red})/price); any remaining collateral is accounted as surplus. The redistribution penalty is branch-configured and is higher than the Stability Pool penalty in the source constants (10% for WETH and 20% for staked-ETH branches, versus 5% for both SP paths).

The implementation distributes collateral and debt per unit of total stake, with carried-forward division errors:
\[
N_C=C_{red}\cdot 10^{18}+e_C,
\quad
r_C=\left\lfloor\frac{N_C}{totalStakes}\right\rfloor,
\quad
e_C'=N_C-r_C\cdot totalStakes,
\]
and analogously for debt. The cumulative (L_{coll}) and (L_{boldDebt}) reward-per-stake terms are incremented; trove reward snapshots determine each active trove's pending collateral and debt gains. DefaultPool holds the pending redistribution amounts until individual troves apply them.

The liquidation sequence closes the trove, accounts for batch interest/management fees where applicable, offsets Stability Pool debt, redistributes residual debt/collateral, sends collateral surplus to the CollSurplusPool, updates system snapshots and pays ETH plus collateral gas compensation. The source also supports batches of troves and leaves at least 1 BOLD in the SP when possible.

**Structural disposition:** a strong candidate for one coupled liquidation-and-loss-allocation family: individual ICR threshold, priority Stability Pool debt cancellation with product-sum depositor accounting, branch-specific collateral penalties/surplus, stake-weighted redistribution with error feedback, pending reward snapshots and gas compensation. This is structurally distinct from Maker/Sky Dutch auctions, Morpho direct repay/seize, Compound Comet absorption and Euler's debt-transfer liquidation. Do not count ICR, SP offset, P/S reward accounting, redistribution and gas compensation as separate candidate equations.

**JIT terminology caveat.** Liquity's current user documentation describes a just-in-time (JIT) fallback when a Stability Pool is empty. The pinned TroveManager source path inspected here exposes the ordinary Stability Pool offset plus redistribution path; it does not expose a separately named `liquidateJIT` function. Treat JIT as an operational/composability mode to be mapped to the exact deployed transaction path before formalizing it as a distinct mechanism.

**Version and deployment caveats.** The current repository is multi-branch and the TroveManager constructor loads MCR, SCR, CCR and penalty ratios from an AddressesRegistry. This audit does not map a deployed branch, registry, price feed, trove manager, pool balance, parameter set or block. No RPC, deployment lookup, contract execution, tests, simulation or experiment was performed.


## 12. Silo V3: partial collateral liquidation and internal collateral-debt defaulting

**Pinned implementation snapshot.** Official repository `silo-finance/silo-contracts-v3`, commit `ed18f3a33be1a08e786279c50b914b1d6eaf04c7` (2026-10-07):
- `silo-core/contracts/hooks/liquidation/PartialLiquidation.sol`, blob SHA `d335836e347b7617e675e462f49a551b9666f301`
- `silo-core/contracts/hooks/liquidation/lib/PartialLiquidationLib.sol`, blob SHA `3b9755b8abaa7fdb8e3262b6c69dcc4b695a7cb4`
- `silo-core/contracts/hooks/liquidation/lib/PartialLiquidationExecLib.sol`, blob SHA `ecffe43e71cc74cee3f57309a169ee190712625a`
- `silo-core/contracts/hooks/defaulting/PartialLiquidationByDefaulting.sol`, blob SHA `72db29f8402348be3da485f106e76a0b6b8577b9`
- `silo-core/contracts/hooks/defaulting/DefaultingSiloLogic.sol`, blob SHA `581b46cbbe33dacc2d74e614299f2e6025b12e09`
- `silo-core/contracts/hooks/defaulting/DefaultingRepayLib.sol`, blob SHA `e0a011e985d977bd8751aa25168d2281b4379544`
- `silo-core/contracts/lib/SiloSolvencyLib.sol`, blob SHA `f4bc66a364110c4f711f6d5a47faea61ad4de8db`
- `silo-core/contracts/hooks/SiloHookV2.sol`, blob SHA `920075bee5a302f64e74fb31bebdce542dc64630`
- `silo-core/contracts/hooks/SiloHookV3.sol`, blob SHA `d2960743f7f4b5cf4db44e6a3980b657d96c1a4b`
- `silo-core/contracts/SiloConfig.sol`, blob SHA `dd68772bd7936d2ba8391b58a2872f0b146de231`

Pinned commit: https://github.com/silo-finance/silo-contracts-v3/commit/ed18f3a33be1a08e786279c50b914b1d6eaf04c7. Hook source reports versions `SiloHookV2 4.19.0` and `SiloHookV3 4.19.0`. V2 inherits both standard partial liquidation and defaulting; V3 inherits the defaulting implementation, overrides standard `liquidationCall` to revert, and sets the defaulting LT margin to zero. These hook versions must not be conflated.

### Solvency and standard collateral-sale liquidation

The solvency library converts protected and collateral shares into underlying assets, converts debt shares into debt assets with debt-side rounding, values collateral and debt through their configured solvency oracles, and computes
\[
LTV=\left\lceil\frac{D_v\cdot 10^{18}}{C_v}\right\rceil.
\]
A position is liquidatable when its LTV exceeds the configured collateral liquidation threshold `LT`. The collateral and debt may live in separate Silos; their SiloConfig binds the collateral Silo, debt Silo, share tokens, oracle routes, `LT`, target post-liquidation LTV and liquidation fee. Interest is accrued before execution.

For a healthy-but-liquidatable position, the maximum debt value to repay is derived from the target post-liquidation LTV `T`, total debt value `D_v`, collateral value `C_v`, and liquidation fee `f`. The source documents the rearrangement
\[
\frac{D_v-x}{C_v-(x+xf)}=T,
\qquad
x=\frac{D_v-TC_v}{1-T-Tf}.
\]
The implementation uses 18-decimal integer arithmetic, explicit early exits and rounding. If debt value is at least collateral value, or target LTV is zero, it forces full liquidation. A partial repay that would exceed 90% of total debt is also promoted to full liquidation to avoid dust. Bad debt (LTV at least 100%) bypasses the target-LTV restriction and allows the caller's requested repay up to the debt balance.

Collateral value seized is capped at
\[
C_{seize}=\min\bigl(x(1+f),C_v\bigr).
\]
The amount is converted back to collateral assets and then to collateral shares with the implementation's specified rounding; the 2-wei underestimation guard addresses the assets-to-shares-to-assets conversion path. Protected collateral is consumed before ordinary collateral. The standard liquidation hook takes the debt asset from the liquidator, approves and repays the debt Silo, transfers collateral/protected shares from the borrower, and either returns shares or redeems the underlying to the liquidator. If the calculated liquidation requires more debt repayment than the caller's maximum, it reverts rather than silently exceeding that cap.

### Internal collateral-debt swap / defaulting mode

The defaulting hook reuses the partial-liquidation sizing logic but changes settlement. In V2, the defaulting threshold adds a 1 percentage-point margin to the collateral `LT`; V3 overrides that margin to zero. The defaulting initializer validates a one-way market (one side has `LT = 0`), requires zero liquidation fee on the non-collateral side, and requires `LT + margin + fee <= 1e18`.

The hook calculates the maximum permitted liquidation amounts (which may still be partial under the target-LTV rule), converts the seized collateral and protected collateral to shares, and splits each share amount between keeper and lenders. `KEEPER_FEE = 0.2e18` (20%) is the keeper's fraction of the liquidation-fee component; the keeper share calculation is rounded down and the remaining seized shares are assigned to lenders. Lender shares are transferred to the configured incentives controller for immediate distribution; keeper shares go directly to the liquidator.

Instead of transferring debt tokens into the debt Silo, the defaulting logic reduces the collateral Silo's recorded collateral assets by the defaulted debt amount (using DAO/deployer revenue as a secondary accounting buffer if collateral assets are insufficient), and burns the borrower's debt shares while reducing the debt Silo's total debt assets. This is an internal loss-allocation mechanism: lenders receive collateral shares, the borrower debt is erased, and the keeper receives a fee share. It is materially different from the standard sale path, which requires the liquidator to provide debt assets and repays the debt Silo.

**Structural disposition:** this pinned source contains two related but structurally distinct settlement modes: (a) partial collateral-sale liquidation that transfers borrower collateral to a liquidator in exchange for debt repayment, and (b) internal collateral-debt defaulting that writes off borrower debt and distributes collateral shares to lenders. The latter is a strong distinct DeFi Risk lead because it allocates losses directly to lender collateral accounting instead of relying on a market sale. Both modes share the target-LTV partial-liquidation sizing operator; do not count the sizing formula, share conversions, fee split, and accounting branches as separate equations. Pairwise E0–E5 review should decide whether the two settlement modes qualify as separate structural candidates or one multi-mode family.

**Version and deployment caveats.** The source repo includes multiple hook versions and immutable per-Silo configurations. This audit does not map a particular deployed hook, SiloConfig, Silo pair, oracle, collateral LT, liquidation target LTV, fee, incentive controller or block. The source uses mixed license headers across core and library files; preserve file-level license provenance. No RPC, deployment lookup, contract execution, tests, simulation or experiment was performed.


## 13. Fraxlend: clean/dirty liquidation fee and lender-claim write-off

**Pinned implementation snapshot.** Official repository `FraxFinance/fraxlend`, commit `2bed49d4dcc6702d92dede825c3424893517d841` (2025-11-12):
- `src/contracts/FraxlendPairCore.sol`, blob SHA `ad3be86d383ffa3dde691f8960c82d4101760fbb`
- `src/contracts/FraxlendPair.sol`, blob SHA `5133f41c73f49a3b1dcca94f91ac28a66d858340`
- `src/contracts/libraries/VaultAccount.sol`, blob SHA `3a7ad956c83d4e32f811d5751acef9b88cb1b0c8`

Pinned commit: https://github.com/FraxFinance/fraxlend/commit/2bed49d4dcc6702d92dede825c3424893517d841. This is a versioned pair implementation snapshot, not a mapping to a particular deployed pair's immutable parameters or current state.

### Solvency and oracle selection

The pair accrues interest before liquidation and updates its dual-oracle exchange rate. The exchange rate represents collateral units per `10^18` asset units; liquidation uses the lower returned exchange rate. The borrower debt amount is obtained from borrow shares using upward rounding. With collateral balance `C`, debt amount `B`, exchange rate `E`, and configured maximum LTV `L_max`,  the code computes
\[
LTV=\left\lfloor
\frac{\left\lfloor B E/E_{prec}\right\rfloor L_{prec}}{C}
\right\rfloor,
\qquad
\text{solvent iff }LTV\le L_{max}.
\]
A liquidation reverts if the borrower is solvent. The low exchange rate is used for this liquidation test and collateral quote; the high exchange rate is used by the post-operation solvency modifier for borrower-initiated actions.

### Clean versus dirty liquidation

The liquidator chooses the number of borrow shares to repay. The pair converts those shares to a debt amount rounded down for the collateral quote, multiplies by the selected exchange rate, then calculates an optimistic collateral amount using the clean fee:
\[
C_{clean}=\left\lfloor
\frac{B_{repay}^{down}E}{E_{prec}}
\cdot\frac{L_{prec}+f_{clean}}{L_{prec}}
\right\rfloor.
\]
It compares the borrower's collateral balance `C_b` with this amount. If `C_b - C_clean <= 0`,  the liquidation is treated as a clean/full collateral liquidation and the liquidator receives all borrower collateral. Otherwise, the collateral reward uses the dirty fee:
\[
C_{liq}=\left\lfloor
\frac{B_{repay}^{down}E}{E_{prec}}
\cdot\frac{L_{prec}+f_{dirty}}{L_{prec}}
\right\rfloor.
\]
The constructor sets `f_dirty = 0.9 * f_clean`. A separate protocol fee is then taken as a fraction of `C_liq` and retained as protocol collateral in the pair. The amount actually transferred by the liquidator is calculated from the selected borrow shares using upward rounding, so it is not identical to the down-rounded collateral-quote amount.

### Residual bad-debt restructuring

If the clean-fee calculation consumes all collateral, the code computes the borrow shares remaining after the liquidator's selected shares. Any remaining shares are marked for adjustment; their corresponding debt amount is converted down and removed from both `totalBorrow.amount` and `totalAsset.amount`. The subsequent repayment burns both the liquidator-repaid shares and adjusted shares, but the liquidator only transfers the asset amount corresponding to the shares they selected. Thus the uncollateralized residual is written off against the pair's total lender asset claim rather than being left as a borrower debt balance. The fToken supply is not reduced by this amount, so the loss is reflected in the value backing lender shares.

**Structural disposition:** one coupled Fraxlend pair liquidation/state-transition family: dual-oracle low-rate eligibility, share-based debt repayment, clean-versus-dirty collateral incentive selection, protocol fee extraction and residual bad-debt write-off against lender asset claims. The clean/dirty fee branch is one integrated collateral-exhaustion rule, not two independent equation candidates. The lender-claim write-off is related to Compound, Liquity, Silo and Euler loss-allocation motifs, but the exact mechanism here couples partial share repayment with pair-level asset-claim reduction. Retain for pairwise structural review.

**Version and parameter caveats.** The constructor configures max LTV, clean liquidation fee and protocol fee per pair; dirty fee is derived as 90% of clean fee in this source snapshot. Oracle contract, max deviation, pair parameters, fToken share price and block state remain deployment-specific. No deployed pair was mapped. No RPC, contract execution, tests, simulation or experiment was performed.


## 14. Fluid Vault (shared T2/T3/T4 engine): tick/branch liquidation and absorb buffer

**Pinned implementation snapshot.** Official repository `Instadapp/fluid-contracts-public`, commit `404d73f91e6806f881f8dabeb30494f93f9e99b7` (2026-11-05):
- `contracts/protocols/vault/vaultTypesCommon/coreModule/main.sol`, blob SHA `5ede8aace90cc92709a3d4cc63191abf53f5ac51`
- `contracts/protocols/vault/vaultTypesCommon/coreModule/main2.sol`, blob SHA `2a70187234a4b8b02a68ef09fdfae0b9c2134cca`
- `contracts/protocols/vault/vaultTypesCommon/coreModule/helpersLiquidate.sol`, blob SHA `ddd46dd80ffc35e0a43fd2e0588f1a13eb50672b`
- `contracts/protocols/vault/vaultTypesCommon/common/variables.sol`, blob SHA `ab4f4e083cc9e16721751d7f7055efae2d5a7f69`
- `contracts/protocols/vault/vaultTypesCommon/coreModule/structs.sol`, blob SHA `53c4ec9d69eac5e80088565d0d8b6d009dd3c61b`
- `contracts/libraries/tickMath.sol`, blob SHA `a939a15df5251ed124af54b82a212a7e3b9956c4`
- `contracts/protocols/vault/vaultTypesCommon/SPEC.md`, blob SHA `65f1299c8956c49882ac43a4e89b08cb91d2d3f3`

Pinned commit: https://github.com/Instadapp/fluid-contracts-public/commit/404d73f91e6806f881f8dabeb30494f93f9e99b7. This audit covers the shared tick/branch engine used by Fluid Vault T2/T3/T4; T1 has a standalone mirrored implementation and type-specific execution paths. Do not assume the same exact source path, oracle implementation or DEX settlement for every vault type.

### Tick geometry and liquidation thresholds

Each position is assigned to a discrete tick using the debt-to-collateral ratio
\[
r(t)=1.0015^t\cdot 2^{96}.
\]
Ticks are indexed by integer (t), with a packed bitmap locating ticks that still contain debt. Positions in a tick share a ratio bucket; partially liquidated ticks are represented by a branch containing a partial-tick fraction, branch debt and a debt factor. This compresses many position updates into tick/branch state rather than iterating every NFT.

The shared liquidation engine updates supply and borrow exchange prices, reads the configured liquidation oracle rate, converts it through the vault exchange prices, and derives:
- a liquidation threshold tick from the configured liquidation threshold;
- a higher maximum-limit tick from the configured liquidation max limit;
- a collateral-per-debt liquidation quote including the configured penalty.

The source rounds debt-per-collateral upward before taking its reciprocal, so collateral-per-debt rounds down; the liquidator's collateral quote is therefore not inflated by reciprocal-rounding error. The configured liquidation penalty is stored in 4-decimal precision; source comments cap it at 10.23%, and the admin spec constrains liquidation max limit plus penalty below 99.7%.

### Absorb above the maximum-limit tick

Before the ordinary tick walk, if the current top tick is above the maximum-limit tick, the core calls the secondary module's `absorb` path. It walks populated ticks above the maximum limit, marks their debt as 100% liquidated, closes or merges affected branches, and accumulates the corresponding debt and collateral into `absorbedLiquidity`. This is an accounting buffer: the absorbed position amounts are subsequently available to a liquidator through the `absorb_` settlement option; the absorb step itself is not a market sale.

When `absorb_` is enabled, the liquidation call consumes the absorbed debt/collateral buffer first, proportionally if the caller's requested debt amount is smaller than the buffer. Any remaining requested liquidation then walks the ordinary tick/branch structure.

### Partial tick/branch liquidation

The engine walks from the current top tick toward the liquidation-threshold tick. At each step it selects the next reference point from the next populated perfect tick, the current branch's minima tick, or the liquidation threshold. For current aggregate debt (D), current ratio (R_s), reference ratio (R_e), and collateral-per-debt quote (q), the debt required to move the aggregate position to the reference ratio is calculated as
\[
x=
\frac{
\left(D-\frac{R_eD}{R_s}\right)10^{27}
}{
10^{27}-\frac{qR_e}{2^{96}}
},
\qquad
C_x=\frac{xq}{10^{27}}.
\]
The code adjusts a one-unit debt dust edge before calculating collateral. If the requested liquidation amount ends inside a tick, it solves the new terminal ratio, maps it back to a tick and partial fraction, and stores the new branch state. When a branch reaches its minima, the engine merges it into the base branch using a connection factor derived from the ratio of branch debt factors. A per-branch debt factor scales remaining debt after each liquidation; tick bitmaps and branch minima avoid scanning every position.

The caller supplies a minimum collateral-per-debt value as a slippage floor. Final debt charged to the liquidator rounds up through the borrow exchange price, while collateral paid out rounds down through the supply exchange price. The engine caps actual debt by the caller's debt amount, rejects dust-only outcomes, and reverts if the realized collateral/debt ratio falls below the caller's minimum.

### State settlement and scope

For non-smart-debt vault types, the liquidated debt is paid back into Fluid Liquidity; for non-smart-collateral types, collateral is withdrawn from Liquidity to the recipient. T2/T3/T4 add type-specific DEX callbacks and smart collateral/debt share settlement around the shared engine. The engine updates aggregate vault supply and borrow amounts and emits the liquidation event. The secondary module also supports dust-debt absorption for already liquidated positions.

**Structural disposition:** a strong candidate for one coupled tick/branch liquidation-and-absorb family: geometric debt/collateral tick quantization, bitmap traversal, partially liquidated branch topology, branch debt-factor scaling/merging, automatic absorb above a maximum-limit tick, optional absorbed-buffer-first settlement, and slippage-constrained debt/collateral transfer. This is structurally distinct from scalar per-position liquidation formulas and from the other auction/repay/redistribution mechanisms audited above. Do not count TickMath, the tick-walk equation, branch debt-factor update, absorb buffer or per-token rounding as independent equations.

**Version and deployment caveats.** The shared base commit uses the older Oracle V1 interface for this engine, while T1's standalone path imports Oracle V2; T2/T3/T4 additionally differ in smart collateral/debt DEX interactions. This audit does not map a specific vault address, vault type, oracle nonce, liquidation threshold, max limit, penalty, token exchange price, branch/tick storage state or block. No RPC, deployment lookup, contract execution, tests, simulation or experiment was performed.


## 15. Notional V3: multi-route portfolio liquidation by haircut removal and maturity-aware asset unwind

**Pinned implementation snapshot.** Official repository `notional-finance/contracts-v3`, commit `ae20d99ebfb0b14cf7b08421722b85849fb11edf` (2025-02-03):
- `contracts/internal/liquidation/LiquidationHelpers.sol`, blob SHA `f2e433ccd75561a0e9853edb0b0e8a0c43433484`
- `contracts/internal/liquidation/LiquidateCurrency.sol`, blob SHA `e15e99fb541b7a4a3e6d89962ba834f856ba0458`
- `contracts/internal/liquidation/LiquidatefCash.sol`, blob SHA `b6ac53c9cbafe36264ba0625f3bf6c025bad2ab9`
- `contracts/external/actions/LiquidateCurrencyAction.sol`, blob SHA `fa65e90b262c3f740e2dca2985e0d8465ec75704`
- `contracts/external/actions/LiquidatefCashAction.sol`, blob SHA `e065e306113dfc9ca35168e35673bd2c588be596`

Pinned commit: https://github.com/notional-finance/contracts-v3/commit/ae20d99ebfb0b14cf7b08421722b85849fb11edf. This is a reproducible source snapshot; the commit is not a deployment/proxy implementation match or evidence of current liquidation enablement.

### Portfolio preparation and eligibility

Before liquidation, the helper obtains the account's liquidation factors and portfolio, updates account context, and constructs a portfolio state. The Notional liquidation design first settles matured portfolio assets and evaluates the resulting free-collateral state. The relevant quantities distinguish:
- local-currency available value, which may be positive or negative;
- collateral-currency available value;
- aggregate negative free collateral in ETH;
- currency-specific exchange-rate haircuts and debt buffers;
- asset-type haircuts and liquidation discounts for cash, nTokens, liquidity tokens and fCash.

This means the system is not simply a scalar LTV threshold followed by a fixed bonus. It unwinds risky claims into cash while ensuring that the account's free-collateral position improves.

### Local-currency and collateral-currency routes

The local-currency route sells or converts same-currency nTokens and liquidity-token claims into cash. It can increase free collateral by removing the haircut on a risky asset even when it does not directly repay debt in another currency. The amount required is derived by converting the negative ETH free-collateral value back into local currency and dividing by the relevant local haircut (when local available is positive) or debt buffer (when it is negative):
\[
A_{local,req}
=
\frac{\operatorname{convertETHToLocal}(-FC_{ETH})\;P}
{m_{local}},
\]
where (P) is the percentage scale and (m_{local}) selects the applicable haircut or buffer. The implementation rejects a zero multiplier because liquidation of a zero-haircut asset cannot improve free collateral.

For cross-currency liquidation, let (FC_c) be the negative free-collateral shortfall expressed in collateral currency, (b_l) the local-currency debt buffer, (h_c) the collateral haircut, (d) the liquidation discount and (X_{l\to c}) the local-to-collateral exchange rate. The liquidator supplies local cash and purchases collateral. The source's relationship is:
\[
A_{local}=
\frac{C_{sell}}{X_{l\to c}\,d},
\qquad
FC_c=A_{local}b_lX_{l\to c}-C_{sell}h_c.
\]
Solving for the collateral sale:
\[
C_{sell}
=
\frac{FC_c}{b_l/d-h_c}.
\]
The liquidation discount is the greater of the local- and collateral-currency discounts. The code caps local cash supplied so that the account's local available balance is not pushed above zero, and caps collateral sold so that collateral available is not pushed below zero. The liquidator can also specify a maximum purchase. A default liquidation portion permits at least 40% of the available asset amount where required, subject to available-balance and user-specified caps.

### Maturity-aware fCash routes

The fCash liquidation engine has local-currency and cross-currency paths. For local fCash, the amount required to restore free collateral is divided by the difference between the liquidation discount factor and risk-adjusted discount factor:
\[
fCash_{sell}
=
\frac{Benefit_{required}}
{|d_{liq}(maturity,t)-d_{risk}(maturity,t)|}.
\]
The discount factors depend on the fCash maturity, time to maturity and whether the fCash notional is positive or negative. Maturities must be supplied in descending order, causing the longest-dated (more exposed) positions to be processed first. Negative fCash positions may also be liquidated through the local route, with the associated cash transfer effectively allowing the liquidator to borrow at the liquidation discount.

The cross-currency fCash route combines the fCash haircut-removal benefit with the cross-currency collateral benefit. The code's benefit divisor contains both the difference between liquidation and risk-adjusted fCash discount factors and the collateral-side term:
\[
d_{liq}-d_{risk}
+
d_{liq}\left(\frac{b_l}{d}-h_c\right).
\]
This is a maturity-sensitive portfolio unwind, not a single collateral token seizure. The engine limits purchases to preserve nonnegative local/collateral available constraints and to ensure the account's free collateral does not deteriorate.

### Structural disposition

A strong candidate for one coupled multi-route portfolio liquidation/state-transition family: pre-liquidation settlement, free-collateral restoration, currency-specific haircuts/buffers, local and cross-currency cash conversion, nToken/liquidity-token redemption, maturity-dependent fCash discounting, negative-fCash handling, ordered asset liquidation and balance-sign constraints. Its key structural distinction is that liquidation benefit arises partly from removing risk haircuts and converting portfolio claims into cash, rather than only transferring debt and seizing collateral at a discount.

Do not count local-currency liquidation, collateral-currency liquidation, local fCash, cross-currency fCash, haircut removal and maturity discounting as independent equations. They are coupled routes within the same portfolio liquidation framework. Pairwise E0–E5 review should compare this with the other multi-asset risk systems before any separate candidate rows are admitted.

**Version and deployment caveats.** This repository snapshot is dated 2025-02-03. Notional's router can enable/disable liquidation routes; this audit does not map the current mainnet proxy implementation, enabled liquidation bitmap, currency configuration, cash-group/market parameters, oracle state, account portfolio or block. The user-facing documentation and the pinned source explain the design, but neither is a live deployment check. No RPC, contract execution, tests, simulation or experiment was performed.
