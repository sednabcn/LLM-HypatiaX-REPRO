# Core-295 source verification audit 60: Maker/Sky Jug per-second stability-fee accumulation

**Date:** 2026-11-11  
**Status:** verification of the author-pool stability-fee candidate; no equation is added to the formal catalogue or counted toward 295.

## 1. Pinned implementation

Repository: sky-ecosystem/dss  
Commit: d5326367a9e1a6bfc4cb74673f934834e06d9da5  
File: src/jug.sol  
Blob SHA: c72aa2f62039362d381d893636766524788fdcb1

The contract defines:
- global base per-second stability-fee contribution \(base\), in RAY;
- collateral-specific per-second contribution \(duty_{ilk}\), in RAY;
- last accrual timestamp \(\rho_{ilk}\);
- the prior accumulated collateral rate \(rate_{ilk,prev}\), stored in Vat.

The initial collateral duty is set to \(RAY=10^{27}\), i.e. a unit multiplier before any fee contribution.

## 2. Exact rate accumulation

On drip(ilk), the contract computes:
\[
rate_{ilk,new}=
rmul\left(
rpow(base+duty_{ilk},\,t-\rho_{ilk},\,RAY),
rate_{ilk,prev}
\right),
\]
where \(t\) is the current block timestamp.

The RAY multiplication is:
\[
rmul(a,b)=\left\lfloor\frac{ab}{RAY}\right\rfloor
\]
in the source's checked integer arithmetic. The rpow implementation uses exponentiation by squaring with half-up rounding at each RAY multiplication and overflow checks. The resulting rate delta is passed to Vat.fold, and the collateral's last-accrual timestamp is set to \(t\).

This is a discrete-time implementation of per-second exponential compounding with a global base contribution and a collateral-specific duty contribution. It is not a simple annual APR multiplier. The exact result depends on elapsed seconds, the prior accumulated rate, the RAY exponentiation/rounding algorithm and the update sequence.

## 3. Parameter-update semantics

The collateral duty may be changed only when the last accrual timestamp equals the current timestamp. Thus the old rate must be accrued before changing the collateral-specific duty. The global base parameter is separately updated through governance authorization. The source's rate is therefore piecewise compounded across parameter-update intervals.

The formula can be written as a product over intervals:
\[
rate_n=rate_0\prod_{j=1}^{n}
\left(base_j+duty_{ilk,j}\right)^{\Delta t_j},
\]
with each interval evaluated using the contract's RAY rpow/rmul rounding. This product representation is explanatory; the implementation stores the cumulative rate and applies one interval at each drip.

## 4. Structural classification

The Jug rate is a protocol-specific parameterization of the generic exponential-compounding family:
- the global base plus per-collateral duty is a sum of per-second rate contributions;
- exponentiation over elapsed seconds is ordinary compounding;
- drip, Vat.fold, and rate-index updates are the state transition and accounting application.

Do not count separately:
- global base and collateral duty;
- the per-second factor, rpow and rmul;
- the accumulated rate, rate delta and Vat.fold debt update;
- APR/annualized APY conversions or alternative parameter values.

The formula is sourceable and version-pinned, but under strict scalar-form equivalence it belongs with generic continuous/per-period compounding and lending-interest-index accrual rather than creating a new independent DeFi Risk family. The old Jug implementation must not be conflated with later Sky/Savings Rate or other protocol interest modules.

## 5. Decision

**Disposition:** exact Maker/Sky Jug per-second stability-fee formula and implementation semantics verified. Retain as a source-backed example of the generic exponential-compounding family; do not count it as a distinct equation alongside APR-to-APY, compound growth or other per-second interest-index formulas. A protocol-specific full-system unit would require the exact deployment generation, Vat accounting and governance parameter timeline.

No formal source-register or equation-catalogue record was changed. The source register remains 129 records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, validators, solvers, workflows, paid compute, API calls, on-chain reads or transactions were run. This is static-source review only.
