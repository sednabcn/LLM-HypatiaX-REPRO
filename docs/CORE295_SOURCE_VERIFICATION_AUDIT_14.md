# Core-295 source verification audit 14: Sky/Maker Liquidations 2.0 Abacus price-decay functions

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** existing DeFi Risk leads RISK-SKY-COLLATERAL-LIQUIDATION and RISK-MAKER-MIP45-LIQ2. Current Sky Protocol documentation and the sky-ecosystem/dss liq-2.0 branch implementation of src/abaci.sol were checked. No auction, oracle or chain state was queried.

## 1. Current source lineage and auction architecture

Current Sky documentation describes Liquidation 2.0 as a Dutch auction: a collateral auction starts at an initial price and the price calculator returns a price as a function of elapsed time. The calculator is a configurable Abacus module. The auction's initial price is based on the Oracle Security Module price multiplied by a governance buffer; auction resets can restart the clock and establish a new starting price.

The 2020 MIP45 proposal is useful historical design context, not a sufficient current implementation reference by itself. The current Sky docs retain the LIQ2.0 architecture and describe the configurable price calculators.

The registered sky-ecosystem/dss branch liq-2.0 file src/abaci.sol was fetched; file blob SHA is 8aa7fb96cfc5c630512751096d62a3bf551fd917. The source register does not yet pin an immutable commit for this branch, so this audit does not treat the branch name as a reproducible version pin.

## 2. Price-decay functions transcribed from implementation

Let (P_0=\texttt{top}) be the initial auction price, (t=\texttt{dur}) elapsed seconds, (	au) the linear-decrease horizon, (s) the stairstep interval, and (c) the fixed-point multiplicative cut factor (RAY-scaled).

### 2.1 Linear decrease

The implementation returns:
\[
P_{\mathrm{lin}}(t)=
\begin{cases}
P_0\left(1-\frac{t}{\tau}\right),&0\leq t<\tau,\\
0,&t\geq\tau.
\end{cases}
\]
This is a genuinely linear time-decay function with a finite zero-price horizon. The contract computes it with RAY fixed-point arithmetic and returns zero at or after \(\tau\).

### 2.2 Stairstep exponential decrease

The implementation returns:
\[
P_{\mathrm{step}}(t)=P_0\,c^{\lfloor t/s\rfloor}.
\]
The exponent is integer division of elapsed seconds by the configured step. Price therefore remains constant between step boundaries and drops multiplicatively at each boundary.

### 2.3 Continuous per-second exponential decrease

The implementation returns:
\[
P_{\mathrm{exp}}(t)=P_0\,c^t.
\]
The exponent is elapsed seconds. The source code explicitly comments that this is mathematically equivalent to the stairstep implementation when \(s=1\), with a separate implementation retained for gas efficiency.

### 2.4 Fixed-point implementation

The Solidity implementation uses RAY = 10^27, rmul and exponentiation-by-squaring rpow. The mathematical formulas above describe the idealized real-valued curves; a deterministic benchmark must reproduce integer exponent behavior, fixed-point rounding, overflow guards, valid cut range, and parameter initialization. In particular:
- linear decrease requires \(\tau>0\);
- exponential cut is constrained to \(c\leq1\) and must be initialized to a valid nonzero value if positive prices are intended;
- stairstep decrease requires \(s>0\);
- continuous exponential is a per-second decay, not an exponential with a continuous real-valued time exponent in the implementation.

## 3. Structural and source-family classification

The linear schedule and exponential schedules are structurally distinct functions of elapsed time. The stairstep and continuous exponential schedules are related: the stairstep schedule reduces exactly to the continuous schedule at \(s=1\), and more generally is an exponential with a floor-quantized time argument.

These are not separate liquidation mechanisms. They are interchangeable price-calculator modules in the same Clipper/Abacus Dutch-auction architecture, share the same auction start price and elapsed-time input, and may be replaced by governance. For Core-295:
- retain the linear schedule as one possible time-decay structure;
- treat continuous and stairstep exponential as related subfamilies; do not count the \(s=1\) case or alternate \(c\)/\(s\) parameters as new structures;
- do not count initial-price buffering, auction reset, price cap, tail, cusp, keeper rewards, or partial-take accounting as additional price equations;
- decide whether alternative price-calculator functions inside one protocol auction family may be sampled as separate equation structures or must share one statistical unit.

The linear/exponential functions are not the same as Euler EVK's health-dependent liquidation discount or Morpho's LLTV-dependent LIF. Those are collateral incentive functions of position/market risk state; Abacus functions are auction prices of time since auction start.

## 4. Decision

**Disposition:** source-confirmed alternative liquidation price-decay functions; hold as DeFi Risk candidates pending immutable implementation commit, exact RAY arithmetic/rounding adapter, parameter-domain contract and the predeclared policy for multiple calculators within one auction family. Do not add one entry per parameterization, per auction stage, or per equivalent exponential implementation.

The current source record should be treated as strengthened by current Sky docs and the retrieved implementation file, but the formal source register is not modified in this audit.

## 5. Catalogue and experiment status

No catalogue record, source status, proposed count or accepted count was changed. The formal catalogue remains at 128 source records, 19 proposed records and zero accepted records; the sampling frame remains unfrozen.

No experiments, solvers, validators, workflows, paid compute, live API calls, oracle queries, on-chain reads or transactions were run. This is source and static implementation review only.
