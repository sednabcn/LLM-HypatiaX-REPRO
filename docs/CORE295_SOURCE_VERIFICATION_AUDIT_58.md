# Core-295 source verification audit 58: Euler liquidation-LTV time ramp

**Date:** 2026-11-11  
**Status:** extension of the existing Euler Vault Kit DeFi Risk source lead; no equation is added to the formal catalogue or counted toward 295.

## 1. Pinned source

Repository: euler-xyz/euler-vault-kit  
Commit: 93a1de491531e54cbbcf0e5c8cacfe558f924867  
File: src/EVault/shared/types/LTVConfig.sol  
Blob SHA: 48f3e19fbe4c8a3e1e4c2b7b83a6a2a1a9fbe0c1

The LTVConfig stores separate borrow LTV and liquidation LTV values, plus initial liquidation LTV, target timestamp and ramp duration. The source comment says liquidation LTV is ramped down when governance lowers it.

## 2. Piecewise time-ramped liquidation LTV

Let:
- \(L_0\) be initial liquidation LTV at the start of the ramp;
- \(L_1\) be the target liquidation LTV;
- \(t_*\) be the target timestamp;
- \(T_r\) be ramp duration;
- \(t\) be current block timestamp.

The implementation returns the target directly if \(t\ge t_*\) or \(L_1\ge L_0\). Otherwise:
\[
L_{liq}(t)=L_1+(L_0-L_1)\frac{t_*-t}{T_r}.
\]
This is a linear ramp from \(L_0\) at the ramp start to \(L_1\) at \(t_*\). The contract uses integer arithmetic and truncates the interpolated value to the ConfigAmount representation. Increases in liquidation LTV are applied immediately; only decreases are ramped.

The setLTV operation captures the currently effective liquidation LTV as \(L_0\), stores the new target \(L_1\), sets \(t_*=\text{block.timestamp}+T_r\), and stores \(T_r\). A subsequent update therefore starts from the currently effective value, not necessarily the prior target.

## 3. Risk-model interaction

Euler's liquidation calculation uses the current time-dependent liquidation LTV, not the borrow LTV. Its liquidation eligibility values collateral using oracle mid prices and current liquidation LTV; the ordinary account-liquidity check uses borrow LTV and bid/ask prices. Thus the LTV ramp changes liquidation eligibility over time without changing the LTV at which new borrowing is permitted.

The ramp is part of the same Euler liquidation-risk system as the health ratio, capped discount, collateral-yield conversion and repay calculation documented in Audit 46. It should not be counted as an independent sample merely because it is a separate piecewise equation. Different collateral LTVs, ramp durations or governance parameter updates are not separate equations.

## 4. Adapter requirements

Freeze:
- exact Euler Vault Kit commit and collateral LTVConfig;
- initial and target liquidation LTV, target timestamp and ramp duration;
- update timestamp and any mid-ramp subsequent configuration changes;
- ConfigAmount precision and integer truncation;
- borrow LTV separately from liquidation LTV;
- oracle price convention and the distinction between account-status bid/ask checks and liquidation mid-price checks.

## 5. Decision

**Disposition:** pinned source verifies a time-dependent, downward-only linear liquidation-LTV ramp. Add it to the Euler source-family description as a coupled parameter-state transition. Keep it grouped with Euler's health/discount/reverse-liquidation system; no additional source-register or equation-catalogue record is needed.

No formal catalogue status changed. The source register remains 129 records, with 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, validators, solvers, workflows, paid compute, API calls, on-chain reads or transactions were run. This is static-source review only.
