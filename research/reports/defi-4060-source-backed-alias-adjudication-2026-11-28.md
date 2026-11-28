# DeFi 40/60 source-backed symbolic adjudication

**Date:** 2026-11-28  
**Scope:** committed Random 40/60 and PCA 40/60 results; seeds 42, 99, 123, 777, 2024; 74 equation families per protocol.

## Executive result

The source-backed alias pass and conservative evaluator extensions were run against all 740 saved records. No experiment, training run, or LLM call was performed. Original result JSON, prompts, generated formula strings, and protocol ground-truth metadata were not changed.

| Protocol | Records | Exact symbolic matches | Not assessable | Not symbolically equivalent |
|---|---:|---:|---:|---:|
| Random 40/60 | 370 | 255 (68.92%) | 6 (1.62%) | 109 (29.46%) |
| PCA 40/60 | 370 | 255 (68.92%) | 6 (1.62%) | 109 (29.46%) |
| Combined | 740 | 510 (68.92%) | 12 (1.62%) | 218 (29.46%) |

The original strict pass, before source-backed aliases and safe parser extensions, found 170 exact, 530 not-assessable, and 40 non-equivalent records. The updated pass raises exact matches by 340 records and reduces not-assessable results by 518. The additional non-equivalent results are previously unassessable formula comparisons that can now be evaluated; they are not new changes to the saved formulas.

At equation-family level, each protocol has:
- 51 families equivalent across all five seeds;
- 21 families non-equivalent across all five seeds;
- 1 mixed family (Capital efficiency: four seeds non-equivalent, one not assessable);
- 1 family not assessable across all five seeds (Black-Scholes Put Price).

## Why the audit can now assess more records

The protocol generator is the authoritative source for the variable schema and answer-key shorthand: [experiment_protocol_defi.py](https://github.com/sednabcn/LLM-HypatiaX-REPRO/blob/master/hypatiax/protocols/experiment_protocol_defi.py).

The new manifest uses 53 equation-specific alias maps. Examples include:
- x/y → reserve_x/reserve_y for AMM output;
- volatility → daily_volatility for VaR;
- loan → loan_amount for LTV;
- r → price_ratio for impermanent loss, but r → risk_free_rate for derivative pricing;
- ES1/ES2 → position1_es/position2_es for correlated portfolio ES.

Mappings are never generalized across equations. Every canonical target must exist in the saved variable_names or numeric constants for that record. The four liquidation-price families receive no aliases because their mismatches are formula differences, not naming differences.

The evaluator was extended conservatively and covered by regression tests:
- scalar np.dot and np.where with a single comparison;
- literal conditional expressions and final same-name function redefinitions (the final Python binding is the effective function);
- reassigning a declared constant only when the assigned value is symbolically identical;
- NumPy infinity;
- source-defined Black-Scholes d1/d2 expansion and the Theta constants K=100, r=0.04.

The Theta constants are read from the protocol generator because that generator defines them locally but omits them from the saved metadata. This source-backed addition is applied only in the post-hoc audit.

## Non-equivalent generated formulas

These are strict symbolic mismatches against the protocol's stored target. They are not inferred from R².

| Equation family | Protocol target | Saved generated expression differs by |
|---|---|---|
| Capital efficiency | price_upper / (price_upper - price_lower) | Uses a different square-root/current-price efficiency expression. Four seeds are non-equivalent; one remains not assessable due to a conservative constant-shadow guard. |
| Component ES | weight × individual_es × (1 + correlation) | Uses a covariance-style dot-product aggregation instead. |
| Compounding Staking Returns | principal × (1 + apr / n)^n | Subtracts principal, returning interest earned rather than the benchmark's compounded value. |
| Concentrated liquidity position width | price_upper / price_lower | Returns sqrt(price_upper) - sqrt(price_lower), which is the separately defined v2 width variant. |
| Convexity Adjustment | spot × (1 + 0.5 × trade_size / pool_depth) | Adds an additional squared trade-size term. |
| Effective Leverage | L / (1 + L × delta_p) | Divides delta_p by 100 even though the protocol supplies it as a decimal fraction. |
| Impermanent loss percentage | (2√r / (1 + r) - 1) × 100 | Omits the percentage multiplier. |
| LP share percentage | deposit / pool_total × 100 | Omits the percentage multiplier. |
| Liquidation Price Long | entry × (1 - 1 / (leverage × 0.8)) | Omits the 0.8 maintenance-margin factor. |
| Liquidation Price Short | entry × (1 + 1 / (leverage × 0.8)) | Omits the 0.8 maintenance-margin factor. |
| Liquidation price for leveraged long | entry × (1 - 1 / (leverage × 0.8)) | Uses the wrong coefficient for the leverage adjustment. |
| Liquidation price for leveraged short | entry × (1 + 1 / (leverage × 0.8)) | Uses the wrong sign and coefficient for the leverage adjustment. |
| Maximum safe leverage | 1 / (acceptable_loss_pct × 0.8) | Uses 1 - 0.8 (0.2) instead of 0.8 in the denominator. |
| Optimal LP Position (Kelly) | min(mu / (2 × sigma²), 1) | Uses an extra factor of 2 in the denominator. |
| Options Delta | clip(0.5 + m / (2 × vol × √T), 0, 1) | Implements a different Black-Scholes-style CDF expression using log(moneyness). |
| Portfolio Expected Shortfall for correlated | ES1 + ES2 + rho × √(ES1 × ES2) | Uses a covariance-norm aggregation instead of the protocol's simplified ES expression. |
| Position margin ratio | (collateral + upnl) / notional | Uses abs(notional). The saved protocol's notional values are positive, so this difference does not change values on the benchmark's declared data domain. |
| Price slippage percentage | 100 × dx / (2 × x + dx) | Uses x + dx in the denominator, omitting the factor of 2 on x. |
| Slashing penalty | staked × slash_pct | Divides slash_pct by 100 even though the source supplies it as a fraction. |
| Theta of option | Full source-defined Black-Scholes theta expression | Uses an ATM approximation per day and omits the rate/discount term. |
| Uniswap V3 virtual | amount / (√P_upper - √P_lower) | Multiplies by √P_lower × √P_upper in the numerator. |
| Utilization rate of DeFi | borrowed / supplied | Adds a zero-supply guard. The source generator always creates positive supplied values, so this is a strict global difference but equivalent on the saved benchmark domain. |

The two domain-limited differences (Position margin ratio and Utilization rate) should not be described as observed errors on the saved data range. They remain non-equivalent under the evaluator's unrestricted formal identity test.

## Remaining not-assessable cases

- **Black-Scholes Put Price (all five seeds per protocol):** the saved generated Python contains syntax errors (unterminated string / invalid syntax). No formula comparison is attempted.
- **Capital efficiency (one seed per protocol):** the generated formula assigns to a name already present in the declared constant environment. The evaluator retains its conservative rejection; no override was made.

## Confirmed liquidation-price source check

The protocol generator explicitly sets maintenance_margin = 0.8 and computes:
- long: entry_price × (1 - 1 / (leverage × maintenance_margin));
- short: entry_price × (1 + 1 / (leverage × maintenance_margin)).

This confirms the stored ground-truth expressions. The four generated-formula mismatches are genuine deviations from the source definitions, repeated across all five seeds and both protocols.

## Reproducibility and safeguards

- Read-only input: the canonical committed Random/PCA JSON result files.
- Seeds: 42, 99, 123, 777, 2024.
- No experiment reruns, model training, or LLM/provider calls.
- No changes to historical result JSON, prompts, generated formulas, or benchmark answer-key metadata.
- Alias manifest and source-backed constants are used only in the adjudication script.
- Unsupported or malformed expressions remain not assessable; no forced equivalence is assigned.

## Workflow and implementation

- Source-backed adjudication workflow: [run 46137673314](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/46137673314) — successful.
- Retrospective audit workflow: [run 46137673343](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/46137673343) — successful.
- Offline smoke workflow: [run 46137673330](https://github.com/sednabcn/LLM-HypatiaX-REPRO/actions/runs/46137673330) — successful.
- Focused regression suite: 12 tests passed.
- Machine-readable and Markdown case-level outputs are uploaded as the workflow artifact named defi-4060-source-backed-aliases (30-day retention).

This report distinguishes exact symbolic identity, non-equivalence, and not-assessable cases. It does not treat predictive R² or routing decisions as evidence of formula correctness.
