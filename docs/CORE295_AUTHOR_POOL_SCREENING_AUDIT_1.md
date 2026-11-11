# Core-295 author_pool.py screening audit 1

**Status:** screening-only; no candidate accepted.  
**Input:** user-supplied `author_pool.py`, statically inspected on 2026-11-11. The script was not executed.  
**Scope of this audit:** complete declaration inventory and detailed first-pass review of all DeFi AMM and DeFi Risk rows. This is not a scientific validation, implementation test, or source-complete review.

## Provenance and interpretation

The file itself states that its equations were written by the assistant from standard textbook/protocol-math forms, were not taken from a peer-reviewed benchmark, and have not been human-verified. Its `source` field is a generated label, not a bibliography citation. This provenance must remain explicit. The pool must not be described as a human-verified or peer-reviewed benchmark.

The catalogue's structural-distinctness policy rejects cosmetic variants, requires algebraic-equivalence checks where feasible, human review, source-family tracking, and a sampling design before independence claims. A different name, output variable, inverse, rearrangement, observable, or derived metric does not by itself establish a distinct equation.

## Static inventory

AST inspection (without importing or executing the module) confirms 299 rows:

| Domain | Rows | Target | Difference |
|---|---:|---:|---:|
| Physics | 75 | 59 | +16 |
| Biology | 59 | 59 | 0 |
| DeFi Risk | 57 | 59 | -2 |
| Chemistry | 54 | 59 | -5 |
| DeFi AMM | 54 | 59 | -5 |
| **Total** | **299** | **295** | **+4** |

Only one expression/range-key mismatch was found by a simple AST name-set check: `chemistry__fick_flux` uses `dx` in its expression but declares `x`. The other 298 rows have matching expression names and range keys under this limited check. This does not verify units, physical validity, domain constraints, equation correctness, or extrapolation suitability.

The builder's stated finiteness screen is not a validity screen. A finite expression can still be outside its physical/protocol domain, dimensionally inconsistent, or inconsistent with a source implementation.

## DeFi AMM detailed screening

Disposition vocabulary:
- **Family overlap:** do not count separately from the named parent family or excluded Core-15 family.
- **Conditional source review:** potentially useful mathematical family, but requires primary source, pinned version, assumptions, units, bounds and deterministic generator.
- **Rewrite/reject as written:** formula is unsupported, materially incomplete, or appears incorrect; do not use as currently written.
- **Not AMM-specific / identity:** generic arithmetic or bookkeeping relation; insufficient as a distinct DeFi AMM equation without a defensible protocol context.

| Candidate ID | First-pass disposition and reason |
|---|---|
| `defi_amm__swap_out_with_fee` | **Family overlap.** Constant-product exact-input swap equation with fee; overlaps the excluded Core-15 Constant Product family. Pin fee convention, integer rounding and token orientation if retained as a derived test, but it cannot fill a new structural slot under the current exclusion. |
| `defi_amm__spot_price` | **Family overlap.** Marginal price (y/x) is the derivative/price observable of the constant-product invariant; not independent of that family. |
| `defi_amm__post_trade_price` | **Family overlap + scope correction.** (yx/(x+dx)^2) is the post-trade marginal price for a fee-free constant-product reserve update. The pool's actual-input reserve update and fee accounting must be specified; it is a derived observable, not a new invariant. |
| `defi_amm__effective_price` | **Family overlap.** (y/(x+dx)) is the average execution price derived from the fee-free constant-product exact-input output divided by input. Not independent of the swap equation. |
| `defi_amm__lp_token_value` | **Conditional source review / family cluster.** (2sqrt{kP}) is a constant-product pool valuation under a specified quote-price convention. It is derived from the same invariant and price relation; not a new AMM invariant. |
| `defi_amm__lp_tokens_initial` | **Family overlap.** (sqrt{xy}) is proportional initial LP issuance under a constant-product pool, with protocol-specific minimum-liquidity and decimal rules omitted. |
| `defi_amm__lp_tokens_subsequent` | **Conditional source review / family cluster.** Proportional LP issuance (S,dx/x) is a join-accounting relation. It needs exact one-sided/proportional deposit semantics, total-supply and rounding rules; cluster with LP issuance/accounting, not the swap invariant. |
| `defi_amm__il_weighted_pool` | **Family overlap.** Weighted-pool impermanent-loss/hold-value comparison. It is an impermanent-loss family member and overlaps the excluded Core-15 Impermanent Loss family; define price-ratio and weight orientation if studied separately. |
| `defi_amm__balancer_out_given_in` | **Conditional source review.** The expression matches the ideal weighted-pool out-given-in formula before fee adjustment. It is a credible distinct weighted-invariant family, but needs pinned Balancer version, normalized weights, fee-on-input convention, token scaling, bounds and fixed-point rounding. |
| `defi_amm__balancer_spot_price` | **Family overlap.** Correct ideal weighted-pool marginal spot-price relation, but a derivative/observable of the same weighted invariant and not a separate equation slot from out-given-in. |
| `defi_amm__balancer_in_given_out` | **Family overlap.** Algebraic inverse of weighted-pool out-given-in; fees and rounding need explicit treatment. Cluster with the weighted invariant family, not a separate equation. |
| `defi_amm__v3_token0_amount` | **Conditional source review.** Resembles the Uniswap v3 token0 delta (L(1/sqrt{P_{low}}-1/sqrt{P_{high}})), but the present variables represent current and upper price only. State the in-range branch and use sqrt-price units consistently; outside-range behavior is piecewise. |
| `defi_amm__v3_token1_amount` | **Conditional source review / family overlap.** Resembles the corresponding token1 delta (L(sqrt{P_{high}}-sqrt{P_{low}})). It is the other side of the same concentrated-liquidity amount family, not an independent equation. |
| `defi_amm__v3_liquidity_from_x` | **Family overlap.** Algebraic inversion of the token0 amount formula to solve liquidity from token0; same concentrated-liquidity family. |
| `defi_amm__v3_capital_efficiency` | **Rewrite/reject as written.** No source or derivation establishes this expression as a general Uniswap v3 capital-efficiency relation. State the comparison baseline, current price, range symmetry and capital measure; derive before reconsideration. |
| `defi_amm__v3_position_value` | **Family overlap / conditional correction.** Combines token0 and token1 amounts into value for an in-range position under a quote-price convention. It is derived from the same v3 amount equations; piecewise outside-range behavior is absent. |
| `defi_amm__tick_to_price` | **Conditional source review.** Tick-to-raw-price relation (1.0001^{tick}) is protocol-specific and potentially distinct from liquidity deltas, but token ordering, sqrtPriceX96/tick semantics, decimal scaling, tick bounds and rounding must be pinned. |
| `defi_amm__sqrt_price` | **Not a distinct candidate.** Elementary square-root transformation of price; no AMM-specific structural content. |
| `defi_amm__lp_fee_share` | **Conditional source review.** Fee allocation by liquidity share is a generic accounting approximation. Requires protocol, fee-growth accounting, active liquidity, tick-range participation, fee token and collection/rounding semantics. |
| `defi_amm__arb_trade_size` | **Family overlap.** Constant-product reserve rebalance to an external price; derived from (xy=k). Requires price orientation and feasibility constraints but cannot be counted independently of constant-product mechanics. |
| `defi_amm__impermanent_loss_usd` | **Family overlap.** Dollar-scaled constant-product impermanent loss; also directly overlaps the excluded Core-15 Impermanent Loss family. |
| `defi_amm__net_lp_return` | **Rewrite / family overlap.** Adds a fee-return term to an impermanent-loss term. It is a composite performance model, not a single primitive equation; time units, fee accumulation, capital base and IL convention are unspecified. |
| `defi_amm__pool_depth_for_slippage` | **Family overlap / approximation.** Inverse slippage-depth expression, apparently based on a simplified constant-product impact relation. It overlaps excluded Price Impact/Constant Product and needs an exact derivation and impact definition. |
| `defi_amm__rebalance_trade` | **Rewrite/reject as written.** The expression (sqrt{k}(sqrt{P_2}-sqrt{P_1})) does not match the reserve change (x(P)=sqrt{k/P}) under the usual quote-price convention. Re-derive with token orientation and units before use. |
| `defi_amm__price_deviation` | **Not AMM-specific / identity.** Relative deviation from a reference price; generic arithmetic and not a protocol equation. |
| `defi_amm__pool_utilization` | **Not AMM-specific / identity.** Volume/TVL ratio is a generic metric; the time basis and meaning of volume are missing. |
| `defi_amm__bonding_linear_cost` | **Conditional source review.** Integral of a linear bonding-curve price from zero to supply (s). Requires an identified protocol/curve, initial supply convention and token units; not automatically an AMM equation. |
| `defi_amm__bonding_exponential_price` | **Conditional source review.** Generic exponential bonding-curve price. No protocol/source or parameter calibration is identified. |
| `defi_amm__bonding_exponential_cost` | **Family overlap.** Integral of the preceding exponential price curve; derived from the same arbitrary curve family, not a second independent equation. |
| `defi_amm__bonding_power_price` | **Conditional source review.** Generic cubic bonding-curve price, with no source, protocol or economic interpretation. |
| `defi_amm__bonding_log_price` | **Conditional source review.** Generic logarithmic bonding-curve price, with no source, protocol or economic interpretation. |
| `defi_amm__bancor_buy` | **Conditional source review.** Matches the Bancor continuous-token purchase-return form with connector weight (cw). Pin contract/version, ppm weight scale, integer fixed-point approximation and valid deposit domain. |
| `defi_amm__bancor_sell` | **Family overlap.** Matches the Bancor sale-return form, inverse transaction direction of the same constant-reserve-ratio bonding-curve family. |
| `defi_amm__bancor_spot` | **Family overlap / convention check.** Spot price from reserve, connector weight and supply is a derivative of the same Bancor CRR family; define price direction and token units. |
| `defi_amm__constant_sum_out` | **Rewrite / insufficient model.** (dx(1-f)) is a fee-adjusted 1:1 transfer with no finite-reserve slippage or invariant solution. Specify a constant-sum pool and boundary behavior; as written it is too generic. |
| `defi_amm__curve_amplified_depth` | **Reject as written.** ((A+1)sqrt{xy}) is not the Curve StableSwap invariant. StableSwap uses an amplification-dependent implicit invariant (D) over normalized balances and coin count, solved iteratively. |
| `defi_amm__stable_price_impact` | **Rewrite/reject pending derivation.** The approximation (dx^2/(2Ax)) is unsupported as a general Curve price-impact equation. Need the StableSwap invariant, coin count, balances, amplification scaling and local expansion derivation. |
| `defi_amm__twap_weighted` | **Conditional source review / likely generic.** Arithmetic weighted average of two prices and durations. It is not a sufficient representation of a specific on-chain oracle: specify cumulative-price construction, observation window, sampling and integer arithmetic. |
| `defi_amm__lvr_rate` | **Rewrite/reject pending derivation.** The (\sigma^2V/8) term resembles a constant-product LVR approximation under a stochastic-price model; multiplying by (1-f) is not established as a valid netting rule. Define volatility/time units, pool value and fee revenue separately. |
| `defi_amm__gas_adjusted_arb` | **Not AMM-specific / identity.** Generic arbitrage proceeds less gas and input cost; requires quote currency conversion and a specific trade/route model. |
| `defi_amm__sandwich_profit` | **Rewrite/reject as written.** Heuristic expression lacks front-run/back-run reserve transitions, victim trade, fee tiers, ordering and gas. No traceable protocol derivation. |
| `defi_amm__tvl_mining_apr` | **Rewrite / incomplete units.** Reward emissions must be a rate over a defined period; annualization, token price, denominator TVL snapshot/average and reward allocation are unspecified. |
| `defi_amm__ve_boost` | **Rewrite/reject as written.** Resembles Curve gauge working-balance boost but uses `TVL` where the veCRV formula uses total gauge working supply/total ve supply terms. Correct variables, units and gauge version are required. |
| `defi_amm__virtual_reserve` | **Rewrite/reject pending derivation.** No source establishes (x/(1-sqrt{P_a/P_b})) as a general virtual-reserve formula. Define pool model, price orientation and reserve being virtualized. |
| `defi_amm__range_order_fill` | **Family overlap.** Algebraically equivalent to the v3 token0 amount delta (L(1/sqrt{P_a}-1/sqrt{P_b})); same concentrated-liquidity amount family. |
| `defi_amm__jit_liquidity_profit` | **Conditional source review / heuristic.** Fee share less gas is a simplified profit identity; needs transaction timing, active-liquidity interval, fee-growth, price impact, gas denomination and protocol specifics. |
| `defi_amm__oracle_manipulation_cost` | **Rewrite/reject pending derivation.** Generic square-root expression lacks an oracle design, attack objective, invariant, manipulation duration, arbitrage response and cost definition. |
| `defi_amm__three_asset_invariant_price` | **Reject as written.** The extra third-token factor ((B_j/w_j)^{0.5}) is not the pairwise Balancer weighted-pool spot price and creates an unexplained dimension/scale dependence. |
| `defi_amm__lp_hold_ratio_weighted` | **Family overlap.** (r^w) is a component of the weighted-pool IL/hold-value comparison, not an independent equation. |
| `defi_amm__dutch_auction_price` | **Not AMM-specific / conditional reclassification.** Linear Dutch-auction price decay is a generic auction schedule, not an AMM equation. Needs a named protocol and exact time/price bounds if moved to DeFi Risk. |
| `defi_amm__batch_clearing` | **Not AMM-specific / identity.** Ratio of aggregate quantities; not a complete batch-auction clearing-price equation without limit orders, constraints and objective. |
| `defi_amm__concentrated_il` | **Rewrite / family overlap.** Composite of constant-product IL and an unverified concentration multiplier. Overlaps excluded IL and v3 range-liquidity families; no derivation. |
| `defi_amm__fee_tier_breakeven` | **Rewrite/reject pending derivation.** Formula is an unsupported heuristic; no fee revenue, LVR, volatility horizon, liquidity base or competing tier definition is stated. |
| `defi_amm__mev_priority_bid` | **Not AMM-specific / identity.** Fraction of transaction value; not a protocol-specific priority-fee or auction equilibrium formula. |

### DeFi Risk detailed screening

| Candidate ID | First-pass disposition and reason |
|---|---|
| `defi_risk__var_normal_horizon` | **Core-15 exclusion overlap.** Normal VaR with fixed 1.645 quantile and square-root-of-time scaling. VaR is an explicitly excluded Core-15 family; no separate slot. Confidence level and return horizon assumptions also need pinning. |
| `defi_risk__es_normal` | **Conditional source review / same risk family.** Normal expected shortfall formula is plausible, but (z) must be the standard-normal quantile associated with confidence (c); the ranges sample them independently. State tail convention, units and horizon. |
| `defi_risk__var_cornish_fisher` | **Core-15 exclusion overlap.** Cornish–Fisher adjusted VaR remains a VaR family member. Skewness extrapolation range is not intrinsically invalid, but the formula is truncated and requires distribution assumptions. |
| `defi_risk__var_two_asset` | **Core-15 exclusion + range failure.** VaR over a two-asset covariance model overlaps VaR and portfolio standard deviation. Extrapolated (hoin[0.8,4]) violates correlation bounds; weights are not constrained to a valid portfolio. |
| `defi_risk__marginal_var` | **Family overlap / incomplete definition.** Marginal VaR derived from portfolio covariance and portfolio volatility; specify (sp), weights, covariance and whether this is derivative or component contribution. Extrapolated correlation range exceeds 1. |
| `defi_risk__ewma_volatility` | **Conditional source review.** One-step RiskMetrics-style EWMA volatility update is plausible. State whether (s) is prior variance/volatility, (r) is the new return, lambda=0.94 is fixed or estimated, and time/return units. |
| `defi_risk__garch11_variance` | **Conditional source review / range failure.** Standard GARCH(1,1) variance recursion, but (alpha+eta) can reach 1.05 under the declared training ranges, violating the usual covariance-stationarity condition. Define (omega) units, initialization and return scaling. |
| `defi_risk__sharpe_ratio` | **Not DeFi-specific / generic metric.** Standard excess-return-to-volatility ratio. Requires matching annualization and return-period conventions; not a DeFi protocol equation. |
| `defi_risk__sortino_ratio` | **Not DeFi-specific / incomplete metric.** Standard downside-risk ratio, but `dd` must be a downside deviation with a defined target/period; not a protocol equation. |
| `defi_risk__liquidation_price_long` | **Rewrite/reject as written.** Simplified leveraged long liquidation price; lacks entry price, maintenance margin, fee/funding, collateral mode and exchange-specific contract convention. The variable `p0` is not explicitly defined as entry price. |
| `defi_risk__liquidation_price_short` | **Rewrite/reject as written.** Same issue as long side; not a general protocol formula and must not be treated as an exact liquidation rule without exchange/market contract specification. |
| `defi_risk__health_factor` | **Conditional source review.** Matches a generic lending health-factor structure (collateral value × liquidation threshold / debt value). For Aave, aggregate collateral valuation and weighted-average liquidation threshold must be explicit; pin version, oracle units and rounding. |
| `defi_risk__liq_collateral_price` | **Family overlap.** Rearrangement of the health-factor threshold (HF=1) for a single collateral asset; not distinct from the health-factor/liquidation-threshold family. |
| `defi_risk__utilization_rate` | **Conditional source review / generic lending state.** Standard borrow/(borrow+cash) utilization, but protocol definitions may account for reserves, bad debt or cash adjustments. Pin market/version. |
| `defi_risk__borrow_rate_curve` | **Reject as a generic protocol claim.** (r_0+s_1U+s_2U^4) is an unsupported polynomial. It is not Compound III's documented piecewise-linear kinked borrow-rate model. Needs named protocol and source or replacement with the actual protocol function. |
| `defi_risk__supply_apy` | **Rewrite / mislabelled.** (Br,U(1-rf)) resembles a supply APR/rate approximation, not APY absent compounding. It assumes a single reserve factor and no protocol-specific supply-rate implementation. |
| `defi_risk__apr_to_apy` | **Family overlap / generic transform.** Standard periodic-compounding conversion. Related to continuous APY and compound-growth rows; not DeFi-specific. |
| `defi_risk__continuous_apy` | **Family overlap / generic transform.** Continuous-compounding conversion (e^r-1), same compounding family as APR-to-APY. |
| `defi_risk__compound_growth` | **Family overlap / generic growth.** Discrete compound-growth equation; cluster with APR/APY transformations, not an independent protocol-risk equation. |
| `defi_risk__staking_reward` | **Conditional source review.** Simple reward accrual approximation. Requires protocol, reward-rate period, compounding/reinvestment, commission and stake/validator eligibility assumptions. |
| `defi_risk__funding_rate` | **Rewrite/reject as written.** ((F-S)/(8S)) has an unexplained divisor 8 and no funding interval, mark/index definition, interest component or exchange-specific premium formula. |
| `defi_risk__perp_pnl_long` | **Not DeFi-specific / generic identity.** Linear-contract long mark-to-market PnL. Requires contract multiplier, settlement currency, fees and funding; not a distinctive risk equation. |
| `defi_risk__margin_ratio` | **Conditional source review.** Equity/notional ratio for a simplified linear long position. Define initial equity, contract multiplier, direction, funding, fees and maintenance margin; pin venue. |
| `defi_risk__kelly_fraction` | **Not DeFi-specific / generic sizing rule.** Binary-outcome Kelly fraction; requires a well-defined net odds and probability model. |
| `defi_risk__var_hurst_scaling` | **Rewrite/reject pending assumptions.** (T^H) scaling is not a general VaR horizon rule; needs a specified self-similar process, Hurst estimator and dependence assumptions. Also remains a VaR-family variant. |
| `defi_risk__insurance_premium` | **Family overlap / conditional source review.** Expected loss plus proportional loading; overlaps expected-loss actuarial family. Define event probability, insured loss, coverage period and loading basis. |
| `defi_risk__parkinson_volatility` | **Conditional source review.** Parkinson high-low volatility estimator is plausible, but H/L must be same-period high and low prices, H≥L>0; define sampling frequency and annualization. |
| `defi_risk__impact_cost_sqrt` | **Conditional source review.** Square-root market-impact approximation; requires source, market/asset class, volatility and volume horizon, impact coefficient calibration and cost units. Not automatically a DeFi protocol formula. |
| `defi_risk__prob_ruin_exp` | **Conditional source review.** Brownian drift/diffusion hitting-probability form under specific continuous-time assumptions. Define drift, barrier distance, volatility convention and boundary event; not a generic DeFi risk law. |
| `defi_risk__collateral_haircut_value` | **Not DeFi-specific / valuation identity.** Haircut-adjusted collateral value; requires price units and haircut policy but is an accounting transformation, not a distinct equation. |
| `defi_risk__net_apr_after_costs` | **Not DeFi-specific / composite identity.** Net APR subtracting fee and IL terms. IL is not generally an APR flow; define period and annualization. Composite performance bookkeeping, not a primitive risk equation. |
| `defi_risk__time_to_liquidation` | **Rewrite/reject as written.** Under GBM, log-price drift is (mu-sigma^2/2). For downward drift, the current denominator makes the stated positive time negative; hitting-time expectation also needs conditions and may not be finite. Re-derive and define drift convention. |
| `defi_risk__risk_parity_weight` | **Conditional source review / generic portfolio allocation.** Two-asset inverse-volatility normalized weight; not DeFi-specific and assumes a particular risk-parity setup. |
| `defi_risk__min_variance_weight` | **Conditional source review / family overlap.** Standard two-asset minimum-variance weight. Requires covariance matrix positive semidefinite, (|\rho|\le1), and a decision on shorting/weight constraints. Extrapolated (ho) exceeds 1. |
| `defi_risk__portfolio_beta` | **Not DeFi-specific / generic identity.** Weighted portfolio beta; weights need a valid normalization and a defined benchmark. |
| `defi_risk__portfolio_return` | **Not DeFi-specific / generic identity.** Two-asset weighted return; trivial portfolio accounting and not a distinct DeFi risk equation. |
| `defi_risk__diversification_ratio` | **Conditional source review / family overlap.** Portfolio weighted average volatility divided by portfolio volatility. Define normalized/nonnegative weights and covariance matrix; extrapolated (ho) exceeds 1. |
| `defi_risk__correlation_from_cov` | **Rewrite range constraints.** Identity (ho=Cov/(s_1s_2)), but the independent ranges permit (|\rho|>1). Constrain covariance consistently with standard deviations and positive semidefiniteness. |
| `defi_risk__leverage_cost_carry` | **Not DeFi-specific / generic carry.** Borrow-minus-supply rate times leverage and time; requires financing convention, rate compounding and collateral/position definition. |
| `defi_risk__debt_ceiling_ratio` | **Conditional source review / generic risk ratio.** Debt divided by collateral value times LTV. Requires currency-consistent values, collateral valuation and protocol LTV policy; overlaps borrow-capacity arithmetic. |
| `defi_risk__peg_deviation_bound` | **Rewrite/reject pending derivation.** Unsupported square-root-time heuristic with arbitrary (k) and discount term; no stochastic process, confidence level or peg mechanism specified. |
| `defi_risk__cascade_price_impact` | **Rewrite/reject pending derivation.** Unsupported square-root depth ratio; cascade mechanism, liquidation flow and market-depth model are undefined. |
| `defi_risk__stability_fee_accrual` | **Conditional source review.** Discrete compounding of a stability fee is plausible but must pin Maker/Sky version, annualized fee convention, time step, debt accumulator and fixed-point rounding. |
| `defi_risk__liquidation_bonus_profit` | **Rewrite/reject pending derivation.** Formula does not define debt repaid versus collateral seized and appears to conflate bonus fraction with profit. Derive from a named protocol's liquidation accounting and bonus convention. |
| `defi_risk__oracle_lag_loss` | **Rewrite/reject pending derivation.** Arbitrary factor 0.8 and square-root-time volatility heuristic; oracle sampling/latency, asset process and loss event are unspecified. |
| `defi_risk__borrow_capacity_ltv` | **Not DeFi-specific / accounting identity.** Collateral value × LTV minus debt; generic capacity arithmetic and closely related to debt-ceiling ratio. |
| `defi_risk__expected_loss` | **Conditional source review / generic credit-risk family.** (PD\times LGD\times EAD) is standard expected loss, but not DeFi-specific without a lending/bridge exposure model and clear horizon/default event. |
| `defi_risk__merton_distance` | **Conditional source review.** Merton structural distance-to-default expression is a recognized model, but asset value, debt face value, asset drift/volatility and horizon assumptions must be specified. |
| `defi_risk__credit_spread_approx` | **Conditional source review / family overlap.** (-\log(1-PD\,LGD)/T) is a flat-hazard spread approximation under recovery/default assumptions. Define horizon, risk-neutral vs physical PD and spread convention. |
| `defi_risk__var_delta_gamma` | **Core-15 exclusion overlap / conditional formula review.** Delta-gamma VaR approximation remains a VaR family member. Specify normal shock assumptions, mean correction, gamma convention and quantile; as written it is a variance-based approximation. |
| `defi_risk__slippage_budget` | **Rewrite/reject pending derivation.** No definition for (c), (eta), horizon or impact model supports this expression; dimensional consistency is not established. |
| `defi_risk__dex_depth_risk` | **Rewrite/reject pending derivation.** Quadratic depth-risk expression is unsupported; define the event, pool invariant, order size and empirical/theoretical derivation. |
| `defi_risk__rebase_dilution` | **Conditional source review.** Share-of-supply after rebase/dilution identity is plausible, but clarify whether (dS) is newly minted supply, who receives it and whether the numerator also rebases. |
| `defi_risk__flash_loan_profit` | **Rewrite/reject as written.** Profit expression mixes (dy\,P) with (fee\,A); the fee term's units are ambiguous unless (A) is a loan amount in the same denomination or converted. Specify borrowed asset, fee schedule, route and gas. |
| `defi_risk__lending_interest_index` | **Conditional source review / protocol mismatch.** Linear simple-interest index update is only an approximation. Pin protocol index convention, per-second rate, time step, compounding, fixed-point scale and rounding; do not present as a generic exact lending index. |
| `defi_risk__bridge_risk_loss` | **Family overlap.** (p\times TVL\times(1-rec)) is expected-loss arithmetic with PD, exposure and LGD; cluster with `expected_loss`, not a separate equation. |
| `defi_risk__governance_attack_cost` | **Rewrite/reject pending model.** (TPq/(1-q)) is not a general governance attack cost. Requires token supply/float, voting threshold, liquidity/market impact, borrowability, lockups and protocol-specific governance rules. |

## Primary-source checks completed

These sources confirm selected formula families; they do not validate the entire candidate pool:

- Uniswap v2 exact-input swap implementation: https://github.com/Uniswap/v2-periphery/blob/master/contracts/libraries/UniswapV2Library.sol — implementation uses integer fee scaling (997/1000), reserve checks and integer division/rounding.
- Balancer weighted math: https://docs-v2.balancer.fi/reference/math/weighted-math.html and https://github.com/balancer/docs-developers/blob/main/resources/pool-math/weighted-math.md — documents the weighted invariant, pairwise spot price, out-given-in and in-given-out; fee is applied to input. The candidate's idealized expressions omit these implementation details.
- Uniswap v3 liquidity amount implementation: https://github.com/Uniswap/v3-periphery/blob/main/contracts/libraries/LiquidityAmounts.sol and https://github.com/Uniswap/v3-core/blob/main/contracts/libraries/SqrtPriceMath.sol — amount0/amount1 deltas are piecewise by current price relative to lower/upper bounds and use Q64.96 sqrt-price fixed-point arithmetic with explicit rounding.
- Curve StableSwap derivation: https://knowledge.curve.finance/developer/references/derivations — invariant is an amplification-dependent implicit equation in balances and coin count, solved iteratively; this contradicts the pool's `(A+1)*sqrt(x*y)` shortcut.
- Bancor purchase/sale return functions: https://docs.inverter.network/contracts/technical-reference/modules/funding-manager/bonding-curve/formulas/bancorformula.sol — confirms CRR purchase and sale return family; implementation uses connector weight in ppm and bounded fixed-point exponentiation.
- Compound III interest rates: https://docs.compound.finance/interest-rates/ — borrow/supply rates are per-second, piecewise linear around a utilization kink; this contradicts the candidate's generic (r_0+s_1U+s_2U^4) as a Compound III formula.
- Aave health factor: https://www.aave.com/docs/aave-v3/markets/health-factor — aggregate collateral value multiplied by weighted-average collateral factor divided by borrow value; candidate must encode aggregation/weighting if claiming Aave V3.

## Consequences for the Core-295 catalogue

1. Do not import the pool wholesale. The row count is not a qualified sampling frame.
2. Do not accept candidates merely to fill the 59-per-domain quota. Structural duplicates and invalid formulas must remain excluded.
3. Treat DeFi AMM's 54 and DeFi Risk's 57 as raw discovery counts, not a shortfall of valid equations that can be repaired by minor formula variants.
4. The Core-15 exclusions explicitly include Constant Product, Impermanent Loss, Price Impact, Value at Risk, Liquidation Price and Portfolio Std Dev. Candidates in those families cannot be reintroduced under new names or parameterizations without an explicit, justified change to the exclusion policy.
5. For DeFi AMM, the most defensible distinct leads in this pool are the Balancer weighted-invariant family, Uniswap v3 concentrated-liquidity family, and Bancor CRR bonding-curve family. Each still needs a single canonical equation per family and exact source/version/units/ranges. Other bonding-curve forms need named primary sources.
6. For DeFi Risk, plausible sourceable leads include normal expected shortfall, EWMA/GARCH volatility, Parkinson volatility, Brownian ruin probability, Merton distance-to-default, flat-hazard credit spread, and protocol-specific health/utilization/stability-fee/index mechanics. They require a domain-boundary policy because several are general finance/statistics rather than DeFi-specific. Excluded VaR and liquidation-price families remain excluded.
7. The formal catalogue remains separate. This audit does not add records, accept equations, freeze the source universe, or alter the target of 295 (59 per domain).

## Review limitations

This pass is a static and literature-backed first screen. It did not execute the script, run the catalogue validator, generate samples, test numerical stability, run experiments, or establish algebraic independence statistically. Several conditional candidates need more exact source and domain review before any acceptance decision.
