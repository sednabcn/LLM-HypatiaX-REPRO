# Core-295 source verification audit 11: Curve CryptoSwap, Morpho liquidation incentive, and Compound III borrow-rate kink

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** three existing DeFi source-register leads. Primary whitepaper, official protocol documentation and the exact implementation commits already recorded in the source register were checked. No on-chain queries or protocol calls were made.

## 1. Curve CryptoSwap dynamic-peg invariant

### 1.1 Primary source and model

Michael Egorov, *Automatic market-making with dynamic peg*, Curve Finance, 9 June 2021. The paper explicitly positions CryptoSwap for assets that are not necessarily pegged to each other, and describes concentration around an internal oracle price that is adjusted subject to a profit/loss constraint.

Let (b_i) be the on-chain balances and (p_i) the internal price-scale coefficients. The paper transforms balances into the invariant's price-normalized coordinates:
[
x_i = b_i/p_i.
]
It defines the invariant level (D) so that at the equilibrium point (x_{m eq}), (D=Nx_{m eq}), where (N) is the number of coins.

### 1.2 Invariant transcription

The paper's CurveCrypto invariant is:
[
K D^{N-1}sum_{i=1}^{N}x_i+prod_{i=1}^{N}x_i
=K D^N+left(rac{D}{N}ight)^N,
]
with
[
K_0=rac{N^Nprod_{i=1}^{N}x_i}{D^N},
qquad
K=A K_0rac{gamma^2}{(gamma+1-K_0)^2}.
]
Here (A) is the amplification coefficient and (gamma>0) controls the distance between the constant-product-like and StableSwap-like curve shapes. The paper describes the invariant approximately as a superposition of constant-product and StableSwap invariants.

For numerical solution, the paper writes the invariant as (F(x,D)=0), solves for (D) and then solves for the output balance using Newton iterations. Initial values and explicit applicability bounds are discussed in the paper; these are not optional implementation trivia because the function is not monotonic over all inputs.

### 1.3 Dynamic-peg mechanism and family boundary

The internal price scale is not a static unit conversion: it is state updated from an internal exponential moving-average oracle, with price adjustments made in log space and constrained by the paper's repegging profit/loss rule. The invariant, transformed balances, dynamic coefficient (K), oracle price scale, and repegging state therefore form one protocol-level AMM model.

Do not count as additional equations:
- the transformed-balance definition and equilibrium normalization;
- the (K_0) and (K) helper definitions separately from the invariant;
- Newton iteration/update equations as independent scientific models;
- the internal EMA, repegging threshold, or alternative swap directions as extra invariant candidates;
- the constant-product or StableSwap limiting/approximation behavior as separate CryptoSwap entries.

The source distinguishes CryptoSwap from StableSwap, but both belong to Curve's broader invariant-AMM lineage and should share a source-family cluster. The source-register entry does not pin a deployed CryptoSwap implementation commit or a specific pool implementation/version. The whitepaper alone is insufficient to freeze integer precision, rounding, pool-specific parameterization, coin count, fee handling and exact production solver behavior.

**Disposition:** credible structurally distinct AMM invariant lead; held pending a version-pinned implementation contract and complete numerical adapter. Do not count a second candidate for the price-scale or repegging subcomponents.

## 2. Morpho Blue liquidation incentive factor

### 2.1 Official model and pinned implementation

The source register pins `morpho-org/morpho-blue` commit `430bd61d8ab9238c1bde327eec2bfcd3f494fe9d`, `src/Morpho.sol`, and records the matching constants/library source. The liquidation implementation computes:
[
mathrm{LIF}
=minleft(M,rac{1}{1-c(1-mathrm{LLTV})}ight),
]
where the registered implementation constants are (M=1.15) and (c=0.3). The implementation uses WAD fixed-point arithmetic and downward rounding for the factor calculation.

The official Morpho liquidation documentation separately defines:
[
mathrm{LTV}=rac{	ext{borrowed amount}}{	ext{collateral value}},
qquad
mathrm{HF}=rac{	ext{collateral value}	imesmathrm{LLTV}}{	ext{borrowed amount}}.
]
The health factor is the liquidation eligibility metric; the LIF determines the collateral incentive applied when converting debt repaid into collateral seized. These are different outputs and must not be conflated.

### 2.2 Structural and implementation review

The LIF is a capped rational function of the market's LLTV parameter. It is not merely a renamed health-factor or liquidation-price expression, and it is distinct from a generic fixed liquidation bonus. However, it belongs to the existing liquidation-incentive family alongside Euler's health-dependent discount and Compound's collateral-discount mechanisms. Protocol-specific constants do not by themselves establish independent statistical units.

The source-level contract also determines how this factor is used:
- debt/collateral conversion uses the market oracle price and the protocol's (10^{36}) oracle-price scale;
- share/asset conversion uses protocol share math;
- collateral seizure and debt repayment use different rounding directions;
- bad-debt handling is a separate liquidation-state transition, not another LIF equation.

The candidate benchmark must freeze LLTV as a WAD fraction below 1, (M), (c), oracle price orientation/scale, collateral and loan token decimals, share conversion state, and integer rounding. The factor formula alone does not reproduce the full liquidation operation.

**Disposition:** formula and implementation lineage verified against the pinned source; retain as a credible DeFi Risk candidate, but hold pending family-level comparison with Euler and Compound liquidation incentives and a frozen unit/rounding adapter. Do not add separate entries for health factor, collateral quote, share conversion or seizure arithmetic.

## 3. Compound III utilization-kink borrow rate

### 3.1 Official documentation and pinned implementation

The source register pins `compound-finance/comet` commit `f766f51583c23acc33b2a7824654ef2029a96804`, `contracts/CometWithExtendedAssetList.sol`. The official Compound III documentation and implementation define utilization as:
[
u=egin{cases}
0,&S=0,\
B/S,&S>0,
end{cases}
]
where (B) and (S) are the protocol's present-value total borrows and total supply of the base asset.

The per-second borrow rate is piecewise affine:
[
r_b(u)=
egin{cases}
r_0+m_Lu,&uleq u_k,\
r_0+m_Lu_k+m_H(u-u_k),&u>u_k,
end{cases}
]
where (u_k) is the borrow kink, (r_0) the per-second base rate, and (m_L,m_H) the low/high per-second slopes. The pinned implementation's `getBorrowRate` follows these two branches and returns the rate in the protocol's fixed-point factor scale.

The supply-rate output is not the same function: the protocol multiplies the utilization-dependent borrow-rate curve by utilization and the retained-supply factor ((1-	ext{reserveRate})). It should not be counted as a second independent rate curve.

### 3.2 Structural and family review

This confirms the author-pool quartic expression is not the Compound III borrow-rate model. The correct model is continuous and piecewise linear with a slope change at the kink. Its piecewise-affine structure is shared with other utilization-based lending-rate models, including Aave's multi-slope utilization curves. Different parameter values or protocol labels do not create independent structures.

For a benchmark adapter, freeze:
- the exact Comet implementation/version and market configuration;
- utilization denominator and present-value balance convention;
- (u_k), (r_0), (m_L), (m_H), factor scale and per-second time unit;
- the (S=0) branch and admissible utilization range;
- whether the target is per-second borrow rate or an annualized display conversion.

Do not count the utilization identity, supply-rate conversion, annualization, or a second parameterization as separate equations.

**Disposition:** exact piecewise borrow-rate equation verified against the registered implementation commit and official specification. Retain as a protocol-specific member of the utilization-kink rate family, but hold pending cross-protocol family policy and exact market parameter contract.

## 4. Cross-candidate conclusions

| Lead | Mathematical distinction | Main blocker | Disposition |
|---|---|---|---|
| Curve CryptoSwap | Dynamic-coefficient invariant distinct from StableSwap and constant product | No pinned deployed implementation/version or complete fixed-point/rounding contract in the source register | Hold |
| Morpho LIF | Capped rational LLTV-dependent incentive factor | Family-level comparison with Euler/Compound incentives; full unit and rounding adapter | Hold |
| Compound III borrow kink | Continuous piecewise-affine utilization-rate curve | Shared structure with Aave/other kink-rate models; exact market configuration | Hold |

These three leads are not interchangeable with one another. That does not establish three independent statistical units: CryptoSwap belongs to the Curve invariant-AMM lineage; Morpho LIF belongs to the liquidation-incentive family; Compound belongs to the utilization-rate family. The source-family and independent-unit policy must be applied before any final count.

## 5. Catalogue and experiment status

No catalogue record, source status, proposed count or accepted count was changed by this audit. The formal catalogue remains at 128 source records, 19 proposed records and zero accepted records; the sampling frame remains unfrozen.

No experiments, solvers, validators, workflows, paid compute, live API calls, oracle queries, on-chain reads or protocol transactions were run. This is source and static implementation review only.
