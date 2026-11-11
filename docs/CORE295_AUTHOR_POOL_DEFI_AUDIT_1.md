# Core-295 author_pool.py DeFi screening audit 1

**Status:** static scientific/design review of the user-supplied discovery pool; not a benchmark, accepted equation catalogue, or experimental result.  
**Scope:** all 54 `defi_amm` and 57 `defi_risk` records in the supplied `author_pool.py`.  
**Method:** source-code text and literal records were inspected statically. The script was not executed; no data were generated; no validator, solver, workflow, protocol call or experiment was run.

## 1. Executive result

The supplied pool contains 54 DeFi AMM and 57 DeFi Risk rows, versus the Core-295 target of 59 accepted structurally distinct equations per domain. These raw row counts are not acceptance counts. A substantial fraction are derived views of a few shared mechanisms, generic finance identities, or formulas whose protocol/source, units, state variables, or validity domain are not specified.

**Recommendation: do not import either block into the formal catalogue and do not use these rows to fill the 59/domain quota.** Keep them as discovery leads pending source-specific reconstruction and the project's structural-family policy.

| Pool block | Raw rows | Target | Raw shortfall | Accepted from this audit |
|---|---:|---:|---:|---:|
| DeFi AMM | 54 | 59 | 5 | 0 |
| DeFi Risk | 57 | 59 | 2 | 0 |

The 0 means this audit did not promote any pool row to accepted status. It does not invalidate already-drafted formal catalogue records (which are separately reviewed and still proposed).

## 2. Cross-cutting defects in the supplied pool

1. **Provenance is not traceable.** `defi_amm_math:<name>` and `defi_risk_math:<name>` are category labels, not citations. Each candidate needs a named source, exact equation/section or implementation file, version/commit, and a transcription check.
2. **No operational definition of a data-generating process.** Most rows do not define state evolution, units, token denomination, oracle source, block/time convention, or parameter configuration. A finite expression is not a reproducible protocol model.
3. **Ranges are not validity proofs.** Extrapolation defaults to `[hi, 5*hi]` even for variables that are signed, bounded, correlated, dimensionless probabilities, weights, correlation coefficients, or prices constrained by ordering. A finite value can still be physically or economically impossible.
4. **The far-regime filter is insufficient.** Finiteness alone does not ensure denominators remain nonzero, square-root/log arguments remain valid, weights remain normalized, a pool trade stays inside its invariant's domain, or a protocol state is reachable.
5. **Structural distinctness is not demonstrated.** Algebraic rearrangements, derivative prices, inverse trade equations, fee variants, special cases and summary metrics are mixed with underlying invariants. The pool's claim that it excludes limiting cases/reparameterizations is not established by the records.
6. **Core-15 exclusions must be applied before counting.** DeFi AMM rows related to constant-product swaps, impermanent loss and price impact overlap explicitly excluded Core-15 families. DeFi Risk's VaR rows overlap the excluded Value at Risk family; liquidation-price rows overlap excluded Liquidation Price; portfolio variance/correlation rows need review against excluded Portfolio Std Dev.
7. **Cross-domain duplication is possible.** Generic compounding, exponentials, weighted averages, logarithms and quadratic risk forms cannot be counted as new DeFi equations merely by changing labels or input names.

## 3. DeFi AMM review

### 3.1 Constant-product family and Core-15 exclusions

The following records should be grouped for one source-family review, not counted as separate independent equations:

- `swap_out_with_fee`: fee-adjusted constant-product exact-input output.
- `spot_price`, `post_trade_price`, `effective_price`: spot/marginal, post-trade marginal and average execution-price views of the same two-reserve trade curve. The post-trade expression omits fee treatment and must state whether `dx` is gross or net input.
- `lp_tokens_initial`, `lp_tokens_subsequent`: initial geometric-mean minting and proportional subsequent minting are distinct protocol operations but share the constant-product LP accounting family; they require implementation-specific rounding/minimum-liquidity rules.
- `arb_trade_size`, `rebalance_trade`: reserve/invariant-derived arbitrage or rebalancing quantities; no explicit arbitrage objective, fee, external price convention, or optimality derivation is given.
- `impermanent_loss_usd`, `lp_hold_ratio_weighted`, `il_weighted_pool`, `concentrated_il`, `net_lp_return`: LP-versus-hold and fee-adjusted return measures, not independent swap invariants. The first overlaps the Core-15 Impermanent Loss exclusion; the weighted and concentrated variants need separate derivations and cannot inherit distinctness from a different name.
- `pool_depth_for_slippage`, `price_deviation`, `pool_utilization`, `stable_price_impact`, `oracle_manipulation_cost`, `dex_depth_risk` (the last is in the risk block): impact/depth summaries. They are not interchangeable exact AMM equations and must not be presented as generic invariant-derived formulas without derivation.

Uniswap V2's canonical exact-input implementation uses integer arithmetic with fee multiplier 997/1000, reserve positivity checks, and integer division; the continuous expression in the pool is a real-valued approximation, not the complete contract calculation. The source code also rounds the exact-output input upward. See the [Uniswap V2 library implementation](https://github.com/Uniswap/swap-router-contracts/blob/main/contracts/libraries/UniswapV2Library.sol). This family is not eligible to evade the Core-15 Constant Product / Price Impact exclusions by adding a fee parameter or reporting a different price observable.

### 3.2 Balancer weighted invariant family

- `balancer_out_given_in` and `balancer_in_given_out` are inverse trade directions derived from the same weighted invariant, not two structurally independent equations.
- `balancer_spot_price` is the invariant's marginal price relation, again a derived observable in the same family.
- `three_asset_invariant_price` is not the documented general N-token weighted-pool spot-price formula: it multiplies a two-token normalized price ratio by an unrelated third-balance factor with exponent 0.5. It has no defensible source or derivation as written and should be rejected pending a complete reconstruction.
- The `wi`/`wo` intervals are sampled independently, but normalized pool weights must obey protocol constraints (including a sum-to-one condition over all assets and configured min/max weight bounds). The ranges do not encode that joint constraint.

Balancer documents the weighted invariant as a product of token balances raised to normalized weights and gives the outGivenIn, inGivenOut and spot-price equations as consequences of that invariant. The documented spot-price formula is `(Bi/wi)/(Bo/wo)`; the documented swap formula also applies the swap fee to the input amount. These should be clustered as one weighted-pool family, with exact implementation/version and rounding rules fixed before any adapter is considered. Source: [Balancer Weighted Math](https://github.com/balancer/docs-developers/blob/main/resources/pool-math/weighted-math.md).

### 3.3 Uniswap V3 concentrated-liquidity family

Group these as one concentrated-liquidity position/state family pending an explicit rule for whether different derived observables count separately:

- `v3_token0_amount`, `v3_token1_amount`: piecewise token amounts as a function of current price relative to range endpoints. The expressions are valid only in their specified price region; the supplied ranges do not guarantee the required orderings.
- `v3_liquidity_from_x`: inversion of the token0 amount relation.
- `v3_position_value`: valuation assembled from token amounts and price.
- `virtual_reserve`, `range_order_fill`: transformed/derived concentrated-liquidity representations; exact definitions and token/price orientation are absent.
- `v3_capital_efficiency`, `concentrated_il`: derived position metrics; neither is a stand-alone pool invariant.
- `tick_to_price`, `sqrt_price`: coordinate transforms of the same price representation, not independent economic laws.

The ranges allow invalid combinations such as current price outside the position range or reversed `Pa`/`Pb`. Tick-to-price also needs the protocol's tick bounds, token ordering, decimal scaling, fixed-point representation and rounding. A continuous real-valued `1.0001**tick` is not an exact reproduction of the on-chain sqrtPriceX96/tick arithmetic.

The Uniswap V3 oracle's geometric-mean tick is not the same construction as an arithmetic time-weighted price; these should be separated by source and observable rather than hidden under a generic TWAP label. Official documentation: [Uniswap V3 price oracles](https://developers.uniswap.org/docs/protocols/v3/concepts/price-oracles).

### 3.4 Curve StableSwap family

- `curve_amplified_depth = (A+1)*sqrt(x*y)` is not the Curve StableSwap invariant. It is an unsupported shortcut and should be rejected as a purported StableSwap equation.
- `stable_price_impact = dx**2/(2*A*x)` is not established as a general Curve StableSwap price-impact relation. It omits pool balances, coin count, invariant state, amplification convention, fee and numerical solution.
- A StableSwap trade requires solving the pool invariant for the updated balance; the Newton iteration is a numerical method for that invariant, not a separate equation family.
- The meaning/scaling of `A` differs across implementations and pool versions; do not substitute a bare amplification range.

Curve's developer derivations define the StableSwap invariant in terms of all coin balances, coin count, amplification and invariant (D), and explicitly derive a numerical Newton method. That is materially different from the two proposed shortcuts. Sources: [Curve StableSwap derivations](https://docs.curve.finance/developer/resources/derivations/) and [StableSwap overview](https://docs.curve.finance/protocol/pool/understanding-stableswap/).

### 3.5 Bancor and bonding curves

- `bancor_buy`, `bancor_sell`, `bancor_spot` belong to one connector-reserve / connector-weight family. Buy and sell are inverse operations; spot price is the marginal derivative. They cannot be counted as three unrelated equations.
- The pool must identify the Bancor protocol generation and exact connector-weight convention. The exponent `cw` and reserve/supply meanings must be pinned; implementation rounding and fee mechanics may differ by version.
- `bonding_linear_cost`, `bonding_exponential_price`, `bonding_exponential_cost`, `bonding_power_price`, `bonding_log_price` are arbitrary curve families as written. No protocol, token design, source, boundary condition or economic rationale is specified. Price and integrated cost must be treated as derivative/integral pairs within a selected curve family, not independent rows.
- `constant_sum_out` is only a linear no-slippage trade relation multiplied by a fee. It needs a named constant-sum pool and exact invariant/fee assumptions; it is not a general AMM law.
- `batch_clearing` is an average ratio without a clearing rule, objective, constraints or solver. It is not a defined batch-auction mechanism.

### 3.6 Oracle, MEV, fee and liquidity metrics

- `twap_weighted` is a generic two-observation arithmetic weighted mean. It does not encode either Uniswap V2 cumulative-price oracle semantics or Uniswap V3 mean-tick semantics; observation boundaries, cumulative accumulator wrap, interpolation and token orientation are absent.
- `lvr_rate = sigma**2*V/8*(1-f)` is not adequately sourced or dimensioned. The time horizon/volatility convention and the AMM model assumptions are absent; multiplying by `(1-f)` is not a demonstrated universal fee adjustment. Do not accept without deriving from a named LVR model and specifying annualization and liquidity value.
- `gas_adjusted_arb`, `sandwich_profit`, `jit_liquidity_profit`, `mev_priority_bid`, `flash_loan_profit` are strategy-specific profit sketches. They omit transaction ordering, gas denomination/conversion, pool state transition, fee tiers, competition, revert/failure costs, financing and block inclusion assumptions. They are not general protocol equations.
- `tvl_mining_apr`, `lp_fee_share`, `ve_boost`, `fee_tier_breakeven` are accounting/incentive metrics with incomplete protocol definitions. `ve_boost` embeds a hard-coded 0.4/0.6 split and needs the exact gauge/reward formula and caps. `tvl_mining_apr` needs reward token price, reward period and annualization convention.
- `price_deviation` has no definition of actual versus expected price or whether the output is signed/absolute; the denominator can approach zero only if the declared range changes, but the semantic issue remains.
- `pool_utilization` is a ratio whose numerator and denominator are undefined for a pool (volume/TVL? reserve usage? liquidity usage?). It should not be confused with lending utilization.

### 3.7 AMM disposition

| Disposition | Records / families |
|---|---|
| Hold as one family, not separate counts | Constant-product swap/price/LP/IL/depth; Balancer weighted invariant and derived trade/spot relations; Uniswap V3 concentrated-liquidity observables; Bancor connector buy/sell/spot; curve price/cost pairs |
| Reject as written pending reconstruction | `three_asset_invariant_price`; `curve_amplified_depth`; `stable_price_impact`; generic `batch_clearing`; unsupported arbitrary bonding curves |
| Source-specific protocol model required | TWAPs, fee/reward/gauge accounting, LVR, arbitrage/MEV/JIT/flash-loan profit, oracle manipulation |
| Core-15 overlap blocker | Constant-product, impermanent-loss, price-impact derivatives and their relabelled variants |

No AMM pool row is accepted by this audit.

## 4. DeFi Risk review

### 4.1 VaR family: direct Core-15 exclusion collision

The following all remain in the excluded Value at Risk family or are derivatives of it:

- `var_normal_horizon`
- `es_normal` (expected shortfall under a normal model; related tail-risk measure, but must not be counted as a new VaR equation by relabelling a quantile-density expression)
- `var_cornish_fisher`
- `var_two_asset`
- `marginal_var`
- `var_hurst_scaling`
- `var_delta_gamma`

`var_cornish_fisher` also has a range defect: training skewness (S\in[-1,1]), but extrapolation (S\in[1,5]) is one-sided and can invalidate the truncated approximation's interpretation. The two-asset, marginal-VaR and diversification records allow correlation extrapolation `rho: [0.8,4]`, which violates the correlation bound ([-1,1]) and can make covariance matrices non-positive-semidefinite. These are not valid extrapolation domains.

The normal ES expression must define confidence level, tail convention and standard-normal density/quantile consistently. The formula as written uses `exp(-z**2/2)/(2.5066*(1-c))`; it omits an explicit tail-loss sign/convention and does not identify whether `c` is confidence or tail probability.

### 4.2 Portfolio and covariance family

- `var_two_asset`, `marginal_var`, `risk_parity_weight`, `min_variance_weight`, `portfolio_beta`, `portfolio_return`, `diversification_ratio`, `correlation_from_cov` are portfolio construction/aggregation and covariance-family relations. Some are distinct objectives or statistics, but they share common portfolio inputs and cannot be counted without explicit family and statistical-unit rules.
- `correlation_from_cov` has independent ranges that do not enforce (|cov|\le s_1s_2); valid samples can yield (|rho|>1).
- `min_variance_weight` requires a positive, nonzero covariance-matrix determinant/denominator and valid (ho); no weight constraint or short-sale convention is stated.
- `risk_parity_weight` is a two-asset inverse-volatility weight, not a general risk-parity solution. It omits covariance and portfolio constraints.
- `portfolio_beta` and `portfolio_return` omit the requirement that weights sum to one; the current independent ranges can sum to values other than one.
- `diversification_ratio` requires a valid positive-semidefinite covariance matrix and a clear long-only/shorting and weight normalization convention.

### 4.3 Volatility models

- `ewma_volatility` is a one-step volatility update with fixed decay 0.94; the state definition, sampling frequency, initialization and return units are absent.
- `garch11_variance` is a one-step GARCH(1,1)-style variance recursion, but the inputs `r` and `s` need to be explicitly defined as innovation and prior conditional standard deviation/variance. The standard recursion uses a variance state and squared innovation; the current expression `w + al*r**2 + be*s**2` can be a conditional variance update only if `s` is prior conditional standard deviation and parameter restrictions are enforced. Require (omega>0,alpha\ge0,eta\ge0), and state stationarity/positivity constraints such as (alpha+eta<1) where claimed.
- EWMA and GARCH(1,1) are related volatility recursion families; fixed-parameter EWMA is closely related to an IGARCH-type recursion, so the family relationship must be recorded rather than counted by label alone.

### 4.4 Lending and liquidation

- `health_factor` is a legitimate protocol metric candidate when tied to a specific protocol's collateral valuation, weighted liquidation thresholds, debt valuation, oracle and rounding. Aave defines it as total collateral value times weighted-average liquidation threshold divided by total borrow value; below 1 is liquidation-eligible. The pool's `C*LT/D` is only the single-collateral/single-debt simplification, not the full multi-asset implementation. Source: [Aave Health Factor](https://aave.com/faq).
- `liq_collateral_price` is an algebraic rearrangement of the single-collateral health-factor boundary. Keep it in the same family; it also collides conceptually with the Core-15 Liquidation Price exclusion.
- `liquidation_price_long` and `liquidation_price_short` are simplified leverage/margin heuristics. They omit maintenance margin, collateral denomination, fees, funding, mark/index price, isolated/cross margin and liquidation rules. These are not generic protocol liquidation-price formulas and overlap the excluded Core-15 Liquidation Price family.
- `borrow_capacity_ltv`, `debt_ceiling_ratio`, `collateral_haircut_value` are collateral/credit-limit accounting relations; their price, LTV, debt and haircut conventions must be protocol-pinned.
- `liquidation_bonus_profit` is a simple share of collateral value, not a general liquidation bonus or profit calculation. It omits protocol close factor, debt repayment, bonus scaling, slippage, gas and eligibility.
- `time_to_liquidation` uses a log-price expression divided by `mu - sigma**2/2`; it is not a general first-passage hitting-time formula for geometric Brownian motion. It can change sign or diverge when the drift denominator crosses zero, and it omits the hitting-time distribution/quantile.
- `stability_fee_accrual` needs a specific protocol compounding convention, time unit and rate scale; Maker/Sky debt accrual is index/rate-state dependent, not automatically this generic expression.

### 4.5 Lending rates, utilization and compounding

- `utilization_rate` is a generic lending utilization ratio; it needs a named protocol definition of borrows, cash, reserves, accrued interest and rounding.
- `borrow_rate_curve = r0+s1*U+s2*U**4` is not the documented Compound III borrow-rate curve. Compound III uses a piecewise-linear model with low/high slopes around a governance-configured kink and accrues per second. Replace only with a version-pinned, correctly scaled piecewise implementation if that protocol is selected. Source: [Compound III interest rates](https://docs.compound.finance/interest-rates/).
- `supply_apy` is not a general supply-rate equation; it omits reserve factor conventions, protocol spread and compounding frequency. It cannot be inferred universally from borrow rate and utilization.
- `apr_to_apy`, `continuous_apy`, `compound_growth`, `lending_interest_index`, `stability_fee_accrual` are compounding/index-accrual family relations. Their time base and compounding convention differ or are unspecified; do not count simple algebraic reparameterizations as separate equations.
- `apr_to_apy` uses `n` as a frequency but its ranges mix 12 to 365 without defining whether periods/year, payment frequency or per-period rate. `continuous_apy` assumes continuously compounded annual rate. `compound_growth` uses discrete per-period rate and period count.
- Compound III explicitly documents piecewise per-second rates, with annualization by seconds/year; an annual APR shortcut must preserve the per-second scaling and selected market parameters.

### 4.6 Perpetuals, funding, staking and protocol economics

- `funding_rate = (F-S)/(8*S)` is not a universal funding-rate formula. It resembles a price-premium component divided by an 8-hour interval, but omits interest component, clamp, premium TWAP, exchange-specific conventions and whether the output is an 8-hour rate or annualized rate. No venue or contract is named.
- `perp_pnl_long` is a generic linear contract PnL identity; it requires contract multiplier, quote/base denomination, settlement currency and fees.
- `margin_ratio` is a simplified equity/notional ratio; its numerator can become negative and it omits maintenance margin/position mode.
- `staking_reward` and `insurance_premium` are generic accrual/actuarial sketches, not protocol equations without reward emission, slashing, coverage, claim and reserve assumptions.
- `net_apr_after_costs` is simple subtraction of rates with incompatible possible periods/compounding; `leverage_cost_carry` similarly needs synchronized annualization and funding conventions.
- `rebase_dilution` is a share-supply accounting ratio but assumes a single positive supply expansion and no burns, price/oracle effects or rebase timing.
- `bridge_risk_loss` and `governance_attack_cost` are scenario heuristics, not general risk equations. They need threat model, attacker objective, quorum/borrowable supply, market depth, recovery and loss definitions.
- `peg_deviation_bound`, `cascade_price_impact`, `oracle_lag_loss`, `slippage_budget`, `impact_cost_sqrt`, `flash_loan_profit` and `dex_depth_risk` are model sketches with no source, derivation or calibrated state model. They should not be treated as protocol equations.
- `parkinson_volatility` requires high/low prices over a defined sampling interval and log-price positivity; the ranges are plausible positive ratios but the sampling/annualization convention is missing.
- `prob_ruin_exp` is a Brownian-drift approximation whose boundary and process assumptions must be stated; the formula cannot be used as a generic protocol-risk law.
- `merton_distance` and `credit_spread_approx` are related structural-credit-model measures. The latter's (-\log(1-PD\cdot LGD)/T) is a reduced-form constant-hazard approximation, not a universal credit spread. Define asset value/debt units and Merton assumptions before treating either as a candidate.
- `kelly_fraction` is a betting/portfolio sizing relation, not intrinsically DeFi; it requires payoff odds definition and can be negative or exceed allowed leverage. Current ranges permit fractional Kelly values that need explicit clipping/position constraints.
- `expected_loss = PD*LGD*EAD` is a standard expected-credit-loss identity, but not distinct merely because applied to a DeFi protocol. Define horizon, default event, recovery and exposure-at-default measurement.

### 4.7 Risk disposition

| Disposition | Records / families |
|---|---|
| Core-15 exclusion blocker | All VaR variants; liquidation-price heuristics; portfolio variance/correlation structures where equivalent to excluded Portfolio Std Dev |
| Keep as one family pending definition | EWMA/GARCH volatility; portfolio/covariance measures; health factor and its rearrangements; utilization/rate/interest-index accrual; APR/APY/compounding; Merton/credit spread |
| Protocol/venue-specific reconstruction required | Aave health factor; Compound III rate; funding rate; staking rewards; stability fee; liquidation bonuses; oracle/bridge/governance/MEV risk |
| Reject as generic equations as written | Quartic borrow-rate curve attributed to no protocol; generic liquidation price formulae; unsupported time-to-liquidation shortcut; generic flash-loan/bridge/governance/cascade/peg/attack profit sketches |

No DeFi Risk pool row is accepted by this audit.

## 5. Concrete next actions before any formal import

1. Preserve the supplied file as an explicitly unverified discovery pool; do not merge it wholesale into `config/core295_catalogue.json`.
2. Add a source record only after an exact primary/official source and exact version/commit have been pinned.
3. Define the structural equivalence unit: invariant, protocol state transition, derived observable, estimator, or operational metric. Apply the same rule to every domain.
4. Apply Core-15 exclusion families before counting candidates.
5. For AMMs, define token ordering, token decimals, price denomination, fee convention, state variables, invariant, trade direction, valid price/range region, and integer rounding.
6. For risk, define return frequency, horizon, confidence level, covariance constraints, oracle/mark price, collateral valuation, debt units, compounding interval and protocol parameters.
7. Replace independent scalar ranges with constrained joint samplers. Include domain assertions for every sample and every extrapolation regime.
8. Keep source-family IDs separate from independent statistical-unit IDs. Multiple equations from one protocol/version or one synthetic generator do not automatically provide independent calibration units.
9. Only after source and structural screening should candidate expressions be adapted to the benchmark's deterministic generator contract.

## 6. Sources consulted for this pass

- Uniswap V2 exact-input/exact-output library implementation: https://github.com/Uniswap/swap-router-contracts/blob/main/contracts/libraries/UniswapV2Library.sol
- Balancer Weighted Math (invariant, spot price, outGivenIn, inGivenOut and fee handling): https://github.com/balancer/docs-developers/blob/main/resources/pool-math/weighted-math.md
- Uniswap V3 price-oracle semantics: https://developers.uniswap.org/docs/protocols/v3/concepts/price-oracles
- Curve StableSwap invariant and Newton derivation: https://docs.curve.finance/developer/resources/derivations/
- Curve StableSwap amplification context: https://docs.curve.finance/protocol/pool/understanding-stableswap/
- Aave health-factor definition and liquidation threshold: https://aave.com/faq
- Compound III piecewise per-second borrow/supply rate model: https://docs.compound.finance/interest-rates/

These sources establish selected protocol formulas and expose mismatches; they do not validate every row in the supplied pool. Uncited generic finance formulae remain unverified leads, not accepted records.
