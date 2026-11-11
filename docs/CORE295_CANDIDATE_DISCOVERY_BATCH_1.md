# Core-295 candidate discovery backlog — batch 1

**Consolidated bibliography:** [CORE295_REFERENCES.md](CORE295_REFERENCES.md). This reference list collects the literature and source links used across all Core-295 discovery batches and the catalogue plan.

**Status:** discovery candidates only; none of these records is accepted into the 295-entry catalogue.  
**Review rule:** exact source section/page, units, assumptions, canonicalization, source-family clustering, and input-domain review are still required.

This first batch records a limited set of traceable candidate equation families from the initial source register. It is intentionally not represented as a complete or balanced 295-equation catalogue.

## Chemistry

| Candidate | Canonical relation (illustrative notation) | Source | Review note |
|---|---|---|---|
| Zero-order integrated kinetics | `[A](t) = [A]0 - k t` | [Engineering LibreTexts reaction chemistry](https://eng.libretexts.org/Bookshelves/Chemical_Engineering/Foundations_of_Chemical_and_Biological_Engineering_I_%28Verret_Qiao_Barghout%29/02%3A_Reaction_Chemistry/2.10%3A_Reaction_Chemistry_Chapter_Review) | Constrain domain to non-negative concentration; related to first/second-order kinetic family |
| First-order integrated kinetics | `[A](t) = [A]0 exp(-k t)` | [Engineering LibreTexts reaction chemistry](https://eng.libretexts.org/Bookshelves/Chemical_Engineering/Foundations_of_Chemical_and_Biological_Engineering_I_%28Verret_Qiao_Barghout%29/02%3A_Reaction_Chemistry/2.10%3A_Reaction_Chemistry_Chapter_Review) | Distinct functional structure; cluster with other integrated rate laws |
| Second-order integrated kinetics | `1/[A](t) = 1/[A]0 + k t` | [Engineering LibreTexts reaction chemistry](https://eng.libretexts.org/Bookshelves/Chemical_Engineering/Foundations_of_Chemical_and_Biological_Engineering_I_%28Verret_Qiao_Barghout%29/02%3A_Reaction_Chemistry/2.10%3A_Reaction_Chemistry_Chapter_Review) | Distinct reciprocal form; check concentration units and valid interval |
| Nernst equation | `E = E0 - (R T / (n F)) ln(Q)` | [SQA HN Chemistry Databook](https://www.sqa.org.uk/sqa/files_ccc/SQA%20Databook%20for%20HN%20Chemistry.pdf) | Specify reaction quotient convention, activities, temperature and standard state |
| Clausius–Clapeyron relation | `ln(P2/P1) = -(DeltaHvap/R) (1/T2 - 1/T1)` | [SQA HN Chemistry Databook](https://www.sqa.org.uk/sqa/files_ccc/SQA%20Databook%20for%20HN%20Chemistry.pdf) | Approximation assumes constant enthalpy over interval; use positive absolute temperatures |

## Biology

| Candidate family | Candidate model | Source | Review note |
|---|---|---|---|
| Exponential decay/growth | `N(t) = N0 exp(-k t)` (decay) | [University of Michigan SOCR biological ODE notes](https://socr.umich.edu/BPAD1/BPAD1_notes/BPAD1_Chap01_MathFoundations.html) | Generic kinetic form; assess overlap with chemistry family and biological interpretation |
| Predator–prey dynamics | Lotka–Volterra coupled ODE system | [Oxford Mathematical Modelling handbook](https://www.cs.ox.ac.uk/files/1099/MMSC_Handbook_2008.pdf) | Candidate family named in handbook; retrieve primary model source and specify deterministic output target |
| Epidemic compartment model | SIR/SEIR compartment ODE system | [Oxford Mathematical Modelling handbook](https://www.cs.ox.ac.uk/files/1099/MMSC_Handbook_2008.pdf) | Multiple model variants are related; do not count parameterizations as distinct |
| Enzyme kinetics | Michaelis–Menten family | [Oxford Mathematical Modelling handbook](https://www.cs.ox.ac.uk/files/1099/MMSC_Handbook_2008.pdf) | Core-15 already contains Michaelis–Menten; exclude that exact model and cosmetic variants from Core-295 |
| Reaction–diffusion pattern formation | Turing reaction–diffusion system | [Oxford Mathematical Modelling handbook](https://www.cs.ox.ac.uk/files/1099/MMSC_Handbook_2008.pdf) | Candidate family only; retrieve exact model equations and define scalar/vector regression interface |

## Physics

| Candidate | Canonical relation (illustrative notation) | Source | Review note |
|---|---|---|---|
| Ohm's law | `V = I R` | [OpenStax University Physics V2, key equations](https://openstax.org/books/university-physics-volume-2/pages/9-key-equations) | Linear constitutive relation; specify ohmic regime |
| Biot–Savart law | `dB = (mu0/(4 pi)) I (dl cross rhat) / r^2` | [OpenStax University Physics V2, key equations](https://openstax.org/books/university-physics-volume-2/pages/12-key-equations) | Vector/integral relation; may need geometry-specific deterministic reduction |
| Faraday's law | `emf = -N d(Phi_B)/dt` | [OpenStax University Physics V2, key equations](https://openstax.org/books/university-physics-volume-2/pages/13-key-equations) | Define coil orientation and flux geometry |
| Snell's law | `n1 sin(theta1) = n2 sin(theta2)` | [OpenStax University Physics V3, key equations](https://openstax.org/books/university-physics-volume-3/pages/1-key-equations) | Restrict to refraction at a planar interface and define angle convention |
| Photon energy | `E = h f = h c / lambda` | [OpenStax University Physics V3, modern physics key equations](https://openstax.org/books/university-physics-volume-3/pages/6-key-equations) | Distinct inverse-wavelength relation; use consistent SI units |

## DeFi AMM

| Candidate | Canonical relation (illustrative notation) | Source | Review note |
|---|---|---|---|
| Weighted geometric invariant | `prod_i(B_i ** W_i) = k` | [Balancer whitepaper](https://docs.balancer.fi/whitepaper.pdf) | Primary protocol family; normalize weight convention and protocol version |
| Weighted-pool spot price | `SP(i->o) = (B_i/W_i)/(B_o/W_o)` | [Balancer whitepaper](https://docs.balancer.fi/whitepaper.pdf) | Related to weighted invariant; likely same source family, not automatically an independent unit |
| StableSwap invariant | `A*n**n*sum(x_i) + D = A*D*n**n + D**(n+1)/(n**n*prod(x_i))` | [Curve mathematical derivations](https://docs.curve.finance/developer/resources/derivations/) | Primary protocol family; document amplification convention and coin count |
| StableSwap Newton iteration | `D_next = (A*n**n*S - D**(n+1)/(n**n*prod(x_i)))/(A*n**n - 1)` | [Curve StableSwap NG math](https://docs.curve.finance/developer/stableswap-exchange/stableswap-ng/utility_contracts/math) | Numerical solver for the invariant, not an independent economic mechanism; group with StableSwap family |
| Constant-sum invariant | `sum(x_i) = k` | [AMM slippage survey](https://www.mdpi.com/2813-5288/4/3/8) | Candidate discovery from survey; trace to primary protocol/whitepaper and define fee/price boundaries |

**Explicit exclusion:** Uniswap v2's `x*y=k` constant-product invariant is not a Core-295 novelty candidate because Core-15 already contains Constant Product. The same exclusion applies to algebraic restatements of that formula.

## DeFi Risk

| Candidate | Canonical relation (illustrative notation) | Source | Review note |
|---|---|---|---|
| Aave health factor | `HF = collateral_value * weighted_liquidation_threshold / debt_value` | [Aave V3 health factor](https://www.aave.com/docs/aave-v3/markets/health-factor) | Version-specific; define oracle prices, weighted threshold and debt accrual |
| Compound utilization-kink borrow rate | Piecewise affine borrow-rate function of utilization around the kink | [Compound III interest rates](https://docs.compound.finance/interest-rates/) | Need exact base/slope/kink conventions and per-second units |
| Borrowing capacity | `BC = sum_i(collateral_value_i * liquidation_threshold_i)` | [UCL empirical study of DeFi liquidations](https://discovery.ucl.ac.uk/id/eprint/10150722/) | Aggregate multi-collateral formula; source-family relation to health factor |
| Fixed-spread liquidation claim | `Q = debt * close_factor * (1 + spread)` | [Mitigating Decentralized Finance Liquidations](https://eprint.iacr.org/2023/254.pdf) | Assumptions exclude gas and slippage; protocol-specific mechanism |
| Collateralization ratio | `CR = collateral_value / debt_value` | [OECD DeFi Liquidations](https://www.oecd.org/content/dam/oecd/en/publications/reports/2023/07/defi-liquidations_89cba79d/0524faaf-en.pdf) | Related to health factor; likely same risk family, not a separate independent unit |

## Interpretation and next curation work

- This batch is a **candidate discovery aid**, not an accepted catalogue. It includes model families that overlap Core-15 or share source families; those are explicitly flagged rather than silently counted.
- The candidate list is not yet sufficient for the 59-per-domain quota. In particular, DeFi AMM needs more primary protocol families than simple transformations of constant-product/weighted/stable-swap invariants; DeFi Risk needs more distinct risk mechanisms and not just re-expressions of health factor or collateralization ratio.
- Expand each domain through predeclared subdomain strata, retrieve exact source sections, record source-family IDs, and perform symbolic equivalence review before adding any row to `config/core295_catalogue.json`.
- The calibration independence decision remains separate. Multiple equations derived from the same invariant, source paper, or protocol family may need to share a cluster/independence-unit ID.
