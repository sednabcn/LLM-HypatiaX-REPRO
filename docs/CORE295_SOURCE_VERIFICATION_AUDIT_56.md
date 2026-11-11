# Core-295 source verification audit 56: Aave V4 collateral-risk premium and health-dependent liquidation

**Date:** 2026-11-11  
**Status:** verification of existing source-register leads RISK-AAVE-V4 and RISK-AAVE-V4-POSITIONS; no equation is added to the formal catalogue or counted toward 295.

## 1. Pinned upstream implementation

Repository: aave/aave-v4  
Commit: 8be3e0d59efc23cd1d4664a88743340533dd5a0c

Files:
- src/spoke/Spoke.sol, blob SHA 4b1115696076b02241a97bb68a74f7da4eee1d57
- src/spoke/libraries/LiquidationLogic.sol, blob SHA 2b2443915688ab0f0354fe2ba20660e6cc97141d
- src/spoke/libraries/UserPositionUtils.sol, blob SHA a16f5531a26c13629d8cd355319b3e8cf22ef9ec
- src/hub/libraries/Premium.sol, blob SHA af11b7d49555eb3430fcd679f4479b343c546897

The repository is an evolving Aave V4 codebase under a source license. This audit pins a code snapshot; it does not claim that the exact commit is deployed on a live market.

## 2. Multi-asset health factor

For each collateral reserve \(i\), the implementation values supplied shares at the reserve oracle price and applies that user's configured collateral factor \(CF_i\). Let \(V_i\) be the value of the supplied collateral and \(D\) the total debt value, including drawn debt and premium debt. The account's weighted collateral capacity is:
\[
W_C=\sum_i V_i CF_i.
\]
The health factor is:
\[
HF=\frac{W_C}{D}.
\]
The source uses BPS-to-WAD and RAY scaling, rounds collateral against the user, and calculates debt with full precision. If there is no debt, it returns the maximum uint value for health factor. Liquidation eligibility is \(HF<1\).

This aggregate is structurally related to Aave V3 and other weighted-collateral health factors. It is not a new equation merely because V4 stores debt as drawn shares plus premium debt or supports multiple Hubs/Spokes.

## 3. Collateral-risk premium aggregation

Aave V4 additionally computes a user-specific risk premium from collateral risk scores. The implementation:
1. collects the value of each eligible collateral position and its reserve-level collateral-risk score \(\rho_i\);
2. sorts collateral entries by risk score ascending, then collateral value descending;
3. allocates debt coverage against collateral in that order, stopping once the debt value is covered;
4. calculates the value-weighted average risk score of the collateral consumed by that allocation.

Let \(V_i\) be collateral values sorted by ascending \(\rho_i\), \(D\) total debt value, and define:
\[
w_i=\min\left(V_i,\left[D-\sum_{j<i}w_j\right]_+\right).
\]
Then the user risk premium is:
\[
RP_u=\frac{\sum_i w_i\rho_i}{\sum_i w_i},
\]
when the denominator is nonzero; otherwise the implementation leaves it at zero. The weights sum to \(\min(D,\sum_iV_i)\). This is not the same as the health-factor collateral-factor average: it is a distinct debt-coverage-weighted aggregation of collateral-risk scores.

The Spoke then applies the resulting user risk premium to the user's borrowed reserves through premium-share/index accounting. The Premium library computes premium debt from premium shares, a premium offset and the drawn index:
\[
PremiumDebt_{ray}=PremiumShares\cdot DrawnIndex-PremiumOffset_{ray}.
\]
The risk aggregation and premium debt accounting form one coupled user-risk-pricing system; do not count each collateral score, sorting step, average and debt accumulator separately.

## 4. Health-dependent liquidation bonus

The V4 LiquidationLogic exposes a health-dependent liquidation bonus. Let:
- \(H_f\) be the health factor at which the maximum bonus applies;
- \(F_b\) be the configured liquidation-bonus factor;
- \(B_{\max}\) be the reserve's maximum liquidation bonus;
- \(H\) be the current health factor;
- \(P=10{,}000\) the percentage scale and \(W=10^{18}\) the WAD health-factor scale.

For \(H\le H_f\), the implementation returns \(B_{\max}\). Otherwise it computes:
\[
B_{\min}=P+(B_{\max}-P)F_b/P,
\]
and linearly interpolates:
\[
B(H)=B_{\min}+
(B_{\max}-B_{\min})\frac{W-H}{W-H_f}.
\]
The function therefore increases the bonus as health approaches the liquidation boundary from above, reaching the configured maximum at \(H_f\), and uses the maximum for still less healthy positions. Fixed-point integer rounding is downward.

This differs from a constant liquidation spread, Morpho's capped reciprocal LIF and Euler's capped health-shortfall discount. The bonus is one function within Aave V4's broader liquidation system, not an independent equation for every reserve.

## 5. Debt amount required to restore target health

The liquidation logic can size debt repayment to a target health factor \(H_T\). It first defines the liquidation penalty:
\[
\Pi_L= B(H)\cdot CF,
\]
with the bonus converted to WAD and collateral factor applied. It then calculates the debt amount required to reach the target:
\[
D_{repay,ray}=
\frac{D_{total,ray}\,U_D(H_T-H)}
{(H_T-\Pi_L)\,P_D},
\]
where \(U_D\) is the debt-asset unit scale and \(P_D\) is the debt-asset price converted to WAD under the contract's RAY/WAD conventions. The code implements this as a full-precision mulDiv with upward rounding and explicit unit scaling. It then converts the amount into premium debt and drawn shares, applies the caller's debtToCover cap, and handles dust exceptions.

The target-health repayment formula, debt-share conversion, collateral seizure and dust handling are one liquidation sizing procedure. They are not separate candidate equations. The exact adapter must reproduce the code's scaling, share/index conversions and exceptional branches rather than use the simplified real-number expression alone.

## 6. Structural classification

Aave V4 has three relevant layers:
- the health-factor ratio, which remains in the existing weighted-collateral family;
- the collateral-risk score aggregation and user-specific borrowing premium, which is a distinctive multi-collateral risk-pricing rule;
- the health-dependent liquidation bonus and target-health repayment sizing, which form a protocol-specific liquidation mechanism.

Do not count V4's HF separately from Aave V3, or count reserve-specific parameter sets as independent equations. The risk-premium aggregation may be a distinct scalar/system candidate; the dynamic bonus and target-health sizing are a distinct liquidation-policy system relative to fixed-spread, Morpho LIF and Euler reverse-auction designs. The complete V4 position-risk system must be treated as one family if the catalogue permits complete protocol systems.

## 7. Adapter requirements

Freeze:
- exact Aave V4 code commit and market/deployment version;
- reserve list, decimals, oracle prices, collateral factors and collateral-risk scores;
- per-user dynamic-config key and whether config is refreshed before calculation;
- supplied shares, drawn shares, drawn index, premium shares and premium offset;
- risk-score sort ordering and debt-coverage allocation;
- liquidation bonus factor, healthFactorForMaxBonus, maximum bonus and target health factor;
- debtToCover, collateral reserve conversion, share rounding and dust threshold;
- whether the sampled unit is the scalar risk-premium aggregator or the complete position-risk/liquidation system.

## 8. Decision

**Disposition:** pinned Aave V4 source confirms a new user-specific collateral-risk premium aggregation and health-dependent liquidation bonus/target-health sizing. Retain as a strong DeFi Risk lead, held pending exact deployment/adapter and the structural-equivalence policy. Keep the V3/V4 health factor in one weighted-collateral family; do not split the V4 premium, liquidation bonus, target repayment and share-conversion components into multiple independent equation records.

No formal equation-catalogue record was added or accepted. The source register remains 129 records, with 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, validators, solvers, workflows, paid compute, API calls, on-chain reads or transactions were run. This is static-source review only.
