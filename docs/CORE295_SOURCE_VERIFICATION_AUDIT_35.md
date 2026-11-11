# Core-295 source verification audit 35: Bancor constant-reserve-ratio bonding curve

**Date:** 2026-11-11  
**Status:** source-family verification of an existing source-register lead; no equation is added to the formal catalogue or counted toward 295.  
**Scope:** AMM-BANCOR-CRR source lead previously screened in Audit 1.

## 1. Official formula and implementation reference

The Inverter documentation page BancorFormula.sol documents the Bancor purchase and sale return functions and links to a pinned implementation source:
- Git source: InverterNetwork/inverter-contracts at commit 649b450f02fc8b735c128ff0821467e71966c666, src/modules/fundingManager/bondingCurve/formulas/BancorFormula.sol.
- The documentation identifies its implementation lineage as the AragonBlack fundraising BancorFormula.sol contract.
- Connector weight is represented in parts per million, with the documented domain 1–1,000,000.

Let \(S\) be smart-token supply, \(R\) reserve balance, \(w\in(0,1]\) the constant reserve ratio (CRR), \(E\) reserve-token deposit and \(T\) smart tokens minted.

Purchase return:
\[
T=S\left[\left(1+\frac{E}{R}\right)^w-1\right].
\]

Sale return, for \(T\) smart tokens burned:
\[
E=R\left[1-\left(1-\frac{T}{S}\right)^{1/w}\right].
\]
The source documentation states this sale formula explicitly. It is not the algebraic inverse of the purchase formula in the variable \(T\) at fixed \(S,R\); it is derived from the same CRR invariant with the post-sale supply \(S-T\) and reserve \(R-E\).

## 2. Invariant derivation and source-version discrepancy

The purchase equation implies:
\[
S'=S+T=S\left(1+\frac{E}{R}\right)^w
\]
after a deposit \(E\), with \(R'=R+E\). Thus:
\[
\frac{S'}{S}=\left(\frac{R'}{R}\right)^w,
\qquad
\frac{S}{R^w}=\mathrm{constant}
\]
for a fixed CRR and no fees. The sale equation follows by reversing the state change:
\[
\frac{S-T}{S}=\left(\frac{R-E}{R}\right)^w.
\]

A publicly accessible earlier whitepaper draft (v0.77, 28 April 2017) prints a sale-return expression of the form
\[
E=R\left[\left(1+\frac{T}{S}\right)^{1/w}-1\right],
\]
which is not consistent with a reserve outflow for tokens burned and does not satisfy the CRR invariant above. It has the sign/branch structure of an inverse purchase expression. The registered source record cites a later v0.99 whitepaper; its exact page-level equation has not yet been checked against the original version. Do not silently copy the v0.77 sale expression into a candidate or claim that all whitepaper versions agree.

The implementation documentation's sale-return formula is the invariant-consistent form with \(1-(1-T/S)^{1/w}\). The implementation uses fixed-point exponentiation and rounding; the real-valued equations are not an exact reproduction of integer contract behavior.

## 3. Structural and domain classification

The CRR curve is a reserve-backed single-connector bonding curve with a minted/burned smart-token supply. It is not a two-sided constant-product swap pool:
- the reserve balance and smart-token supply jointly move along a power-law invariant;
- the CRR \(w\) controls the curve's price elasticity;
- the purchase and sale functions are two directions of the same state transition;
- cross-connector conversion and spot-price calculations are derived from the same reserve-ratio model.

This is mathematically distinct from the two-token constant-product invariant \(xy=k\), Balancer's positive-weight multi-asset geometric invariant, and the finite-amplification StableSwap family. However, the domain contract must explicitly decide whether reserve-backed bonding curves count as DeFi AMMs or as a separate token-issuance/funding-mechanism category.

Do not count purchase return, sale return, spot price, cross-connector conversion, or parameterized CRR values as independent equations. They are operations or derived quantities in one CRR family.

## 4. Adapter and acceptance requirements

Before any formal candidate can be considered, freeze:
- whether the domain includes bonding-curve token issuance as AMM;
- exact whitepaper version and page-level source transcription (especially sale return);
- immutable implementation commit and source path;
- reserve and smart-token units, decimals and supply semantics;
- CRR ppm representation and allowed range;
- purchase/sale fees, if any, and the real-valued vs fixed-point rounding contract;
- valid trade sizes, including \(0\leq T<S\) for sales and positive reserve/supply.

## 5. Decision

**Disposition:** CRR purchase/sale mathematics and the implementation-documentation sale formula are source-supported. The earlier v0.77 whitepaper contains a conflicting sale expression, while the registered v0.99 page-level transcription remains outstanding. Retain as a potentially distinct DeFi bonding-curve lead, held pending source-version reconciliation and the AMM-domain boundary. Do not add a proposed equation record or accept the lead yet.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, pool reads or transactions were run. This is documentation and source-family review only.
