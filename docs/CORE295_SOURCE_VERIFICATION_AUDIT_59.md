# Core-295 source verification audit 59: Aave V4 Babylon cap-bounded liquidation sizing

**Date:** 2026-11-11  
**Status:** verification of the Babylon liquidation path in the existing Aave V4 source lead; no equation is added to the formal catalogue or counted toward 295.

## 1. Pinned source

Repository: aave/aave-v4  
Commit: 8be3e0d59efc23cd1d4664a88743340533dd5a0c  
File: src/spoke/libraries/BabylonLiquidationLogic.sol  
Blob SHA: 8343dbfc3d48eb23391decb42a5f40875763f367

The source's library notice describes Babylon liquidation as being sized by a collateral cap instead of a target health factor and without dust validation. It reuses the standard V4 LiquidationLogic validation, health-dependent liquidation bonus, collateral pricing and debt/collateral transfer helpers.

## 2. Collateral cap

The caller supplies:
- debt repayment cap \(D_{cover}\);
- maximum collateral amount to remove \(C_{max}\).

The implementation converts \(C_{max}\) into reserve shares with previewAddByAssets, rounds the share cap down, and takes the minimum with the borrower's supplied shares:
\[
S_{max}=\min\left(S_{supplied},
\operatorname{previewAddByAssets}(C_{max})\right).
\]
This is the maximum collateral share amount that can be removed by the liquidation call.

## 3. Initial debt and collateral sizing

Premium debt is liquidated first, up to \(D_{cover}\). Only after premium debt is fully covered does the remaining repayment cover drawn debt shares:
\[
P_{liq}=\min(P_{debt},D_{cover}),
\]
\[
S_{drawn}=
\min\left(S_{drawn,total},
\left\lfloor
\frac{(D_{cover}-P_{liq})RAY}{I_{drawn}}
\right\rfloor\right),
\]
when all premium debt has been covered. The debt-to-collateral conversion then uses the canonical V4 liquidation bonus pricing function.

If the priced collateral shares exceed \(S_{max}\), the code caps collateral shares at \(S_{max}\) and inversely solves the maximum repay amount consistent with that cap:
\[
D_{cap,ray}=
\left\lceil
\frac{
V_C(S_{max})\,P_C\,U_D\,PCT\,RAY
}{
P_D\,U_C\,B(H)
}
\right\rceil.
\]
Here \(V_C(S_{max})\) is the collateral asset amount represented by the capped shares, \(P_C,P_D\) are collateral/debt oracle prices, \(U_C,U_D\) are token-unit scales, \(PCT=10{,}000\), and \(B(H)\) is the same health-dependent liquidation bonus used by standard V4. The result is split between premium debt first and drawn shares second, using the drawn index and the code's directed rounding.

The collateral cap is thus binding: repayment is reduced to match the maximum collateral that may be seized. This is the inverse of the standard debt-to-collateral pricing relation, not a new independent bonus formula.

## 4. Differences from standard V4 liquidation

The Babylon path:
- uses the same health-factor eligibility validation and health-dependent liquidation bonus as standard V4;
- uses a caller-specified maximum collateral amount rather than calculating repayment to restore a target health factor;
- does not apply the standard V4 dust-validation/target-health-factor logic;
- charges no separate liquidation fee: the liquidator receives the full collateral removed;
- still prioritizes premium debt before drawn debt and uses the same debt-share/index accounting helpers.

The standard and Babylon paths are alternative liquidation sizing policies within the Aave V4 family. The health factor, dynamic bonus, collateral price conversion, premium debt repayment and share conversion should not be counted again for the Babylon path.

## 5. Adapter requirements

Freeze:
- exact Aave V4 commit and whether the standard or Babylon Spoke path is used;
- user health factor and reserve-specific dynamic configuration;
- debtToCover and maxCollateralToRemove;
- collateral/debt reserve IDs, decimals, prices and Hub share conversion;
- liquidation bonus inputs and healthFactorForMaxBonus;
- premium debt, drawn shares and drawn index;
- directed rounding, max removable share conversion and full-collateral-to-liquidator rule.

## 6. Decision

**Disposition:** pinned source verifies a distinct cap-bounded liquidation sizing policy. Retain it as a version-specific Aave V4 system variant, not as a new independent equation family beside standard V4. The main structural distinction is the externally imposed collateral cap and inverse repayment resizing; the health factor, bonus and debt/collateral conversion remain shared. Hold pending a frozen adapter and the still-unselected system-unit policy.

No formal source-register or equation-catalogue record was changed. The source register remains 129 records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, validators, solvers, workflows, paid compute, API calls, on-chain reads or transactions were run. This is static-source review only.
