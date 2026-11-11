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

**Version caveat:** The specification page currently identifies itself as Comet v2.5. Its GitHub URL points to the moving `main` branch. Before formal candidate use, pin the exact specification commit and the matching deployed contract revision; do not infer deployment-specific parameters from the generic specification.

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

## 5. Sources

- Compound Comet specification: https://github.com/compound-finance/comet/blob/main/SPEC.md
- Compound III interest-rate docs: https://docs.compound.finance/interest-rates/
- Aave V3 health factor preview: https://www.aave.com/docs/aave-v3/markets/health-factor
- Aave FAQ / liquidation semantics: https://www.aave.com/faq
- Aave V3 pool contract liquidation interface: https://aave.com/docs/aave-v3/smart-contracts/pool?language=en

No formal catalogue equation entry was added or accepted by this audit.
