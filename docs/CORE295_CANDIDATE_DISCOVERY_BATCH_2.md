# Core-295 source-universe expansion — discovery batch 2

**Consolidated bibliography:** [CORE295_REFERENCES.md](CORE295_REFERENCES.md). This reference list collects the literature and source links used across all Core-295 discovery batches and the catalogue plan.

**Status:** source-universe discovery only. This is not an equation catalogue, does not approve any candidate, and does not establish 59 independent units in any domain.

This batch expands the source universe using chapter-level open textbooks, publisher-level mathematical biology references, and protocol-owned technical documentation. Each future equation still requires exact section/page/equation provenance, domain review, dimensional analysis, structural comparison, source-family clustering, and a defensible scalar benchmark mapping.

## Chemistry

| Source | Useful coverage | How to use it |
|---|---|---|
| [University of Minnesota, General Chemistry: Principles, Patterns, and Applications](https://open.umn.edu/opentextbooks/textbooks/69) | Chapters 14–19: kinetics, equilibrium, acid-base, solubility/complexation, thermodynamics, electrochemistry | Strong additional open-textbook source beyond the existing OpenStax/LibreTexts set. Record exact chapter and equation location. |
| [University of Calgary Chemistry Open Textbook v2](https://chem-textbook.ucalgary.ca/) | Chapters 6–12: gases, kinetics, equilibrium, acid-base, solubility, thermodynamics, electrochemistry | Additional structured coverage; use exact chapter pages and cross-check assumptions. |

The two sources overlap heavily in introductory chemistry. They expand discoverability but should not be treated as independent source families merely because they are separate textbooks.

## Biology

| Source | Useful coverage | How to use it |
|---|---|---|
| [Murray, Mathematical Biology, SIAM](https://epubs.siam.org/doi/10.1137/1.9780898719147) | Population biology, molecular/cellular models, PDE models, development and pattern formation | Major mathematical-biology source. Many models are coupled ODE/PDE systems; do not force them into a scalar task without an explicit reviewed output mapping. |
| [Mazumdar, An Introduction to Mathematical Physiology and Biology, Cambridge University Press](https://www.cambridge.org/core/books/an-introduction-to-mathematical-physiology-and-biology/08FE1C4CE05359988B68BCE69C8E2F04) | Diffusion, population biology, pharmacokinetics, epidemiology, biofluid mechanics, cardiac mechanics | Useful additional source families beyond generic growth/kinetics. The publisher contents identify chapter scope; retrieve exact chapter equations before proposing entries. |
| [Daun, Equation-based models of dynamic biological systems](https://pmc.ncbi.nlm.nih.gov/articles/PMC6698907/) | Physiological and clinical differential-equation models | Discovery/review source. Trace each selected model to its cited primary literature before acceptance. |

The biology domain is likely to need the broadest source expansion. Distinct physiological mechanisms may offer stronger diversity than counting many variants of logistic growth, SIR, or enzyme kinetics. This is a curation hypothesis, not a claim that the 59-entry quota is already achievable.

## Physics

| Source | Useful coverage | How to use it |
|---|---|---|
| [OpenStax University Physics Volume 1 contents](https://openstax.org/books/university-physics-volume-1/pages/preface) | Mechanics, gravitation, fluid mechanics, oscillations, waves and acoustics | Chapter structure provides broad subdomain coverage. Retrieve each relevant chapter's key equations and conditions. |
| [OpenStax University Physics Volume 2, Chapter 9 key equations](https://openstax.org/books/university-physics-volume-2/pages/9-key-equations) | Current, resistivity, Ohm's law, resistance and power | Exact chapter-level equation source. Avoid counting equivalent definitions or rearrangements as separate structures. |
| [OpenStax University Physics Volume 2, Chapter 11 key equations](https://openstax.org/books/university-physics-volume-2/pages/11-key-equations) | Magnetic forces, particle motion, magnetic dipoles and Hall effect | Potentially distinct mechanisms; vector relations need a clearly specified scalar component or magnitude task. |
| [OpenStax University Physics Volume 2, Chapters 13, 14, 15 and 16](https://openstax.org/books/university-physics-volume-2/pages/13-key-equations) | Induction, inductance, AC circuits, electromagnetic waves and Maxwell relations | Strong equation-level sources. Check overlap between integral laws, special geometries and derived circuit responses. |
| [OpenStax University Physics Volume 3, Chapters 1 and 2](https://openstax.org/books/university-physics-volume-3/pages/1-key-equations) | Reflection, refraction, polarization, lenses and optical systems | Potentially useful distinct optical relations; document paraxial/geometry assumptions. |

## DeFi AMM

| Source | Useful coverage | How to use it |
|---|---|---|
| [Uniswap v3 Core whitepaper](https://app.uniswap.org/whitepaper-v3.pdf) | Concentrated liquidity, virtual reserves, square-root price and tick representation | Primary technical source. Distinguish actual economic relations from implementation transformations and tick-index approximations. |
| [Uniswap developer documentation: concentrated liquidity](https://developers.uniswap.org/docs/get-started/concepts/liquidity-providers/concentrated-liquidity) | Position-specific price ranges and active liquidity | Current developer explanation; use the whitepaper/contract specification for exact equations. |
| [Balancer weighted math](https://docs.balancer.fi/whitepaper.pdf) and [developer math reference](https://docs.balancer.fi/reference/math/weighted-math.html) | Weighted invariant, spot price, exact-in/exact-out swap relations | Several equations derive from one weighted invariant and must be grouped under one source/derivation family unless a review establishes otherwise. |
| [Curve mathematical derivations](https://docs.curve.finance/developer/resources/derivations/) | StableSwap and CryptoSwap invariants and Newton methods | Primary protocol math. StableSwap invariant and its Newton solver are one mechanism/solver family, not independent economic equations. |
| [Curve AMM overview](https://docs.curve.finance/developer/curve-amm-overview) | StableSwap, CryptoSwap, Twocrypto-NG, Tricrypto-NG and FXSwap families | Useful to broaden beyond StableSwap; version and pool-family identity must be explicit. |

The Uniswap v2 constant-product invariant remains excluded because Core-15 already includes it. A concentrated-liquidity formula may be a candidate only if its functional structure is not merely a parameterized/re-expressed constant-product relation and the equivalence review supports that distinction.

## DeFi Risk

| Source | Useful coverage | How to use it |
|---|---|---|
| [Aave V3 health factor documentation](https://www.aave.org/docs/aave-v3/markets/health-factor) | Collateral-weighted health factor | Protocol-versioned metric; source-family related to collateralization and liquidation eligibility. |
| [Aave V3 overview](https://aave.dev/docs/aave-v3/overview) | Utilization-dependent interest rates, liquidation thresholds and debt accrual | Distinguish rate curves from health-factor calculations; pin V3 parameters and accrual conventions. |
| [Aave V4 positions documentation](https://aave.dev/docs/aave-v4/positions) | V4 health factor and user risk premium | Keep V4 separate from V3. Similar health-factor algebra is not a new independent mechanism just because protocol version changes. |
| [Compound III interest-rate documentation](https://docs.compound.finance/interest-rates/) | Utilization, kinked borrow/supply rate curves and per-second accrual | Strong primary source for piecewise functions. Preserve fixed-point scaling and rate-time conventions in a deterministic benchmark mapping. |
| [Aave risk-v3 parameter documentation](https://github.com/aave/risk-v3/blob/main/asset-risk/risk-parameters.md) | Liquidation thresholds, health factor and reserve factor | Protocol parameter source; avoid counting governance parameters or weighted-sum restatements as distinct equations. |

## Candidate-family and independence cautions

1. Multiple equations derived from one invariant or model are normally one source/derivation cluster. Examples include StableSwap plus its Newton solver, Balancer invariant plus spot-price/swap formulas, and multiple Aave health-factor restatements.
2. Protocol-version differences can be scientifically meaningful, but they do not automatically create independent statistical units. Version-specific parameterizations should be clustered unless the model mechanism materially changes.
3. Equations from different textbooks may share the same canonical derivation. Source bibliography count is not independence count.
4. Vector and integral laws, PDEs, coupled ODEs, discontinuous liquidation rules, and piecewise interest curves require explicit review against the Core-15 scalar regression interface.
5. A source can be approved for discovery while individual formulas from it remain rejected or unreviewed.

## Immediate review priorities

- Biology: retrieve exact equation candidates from Murray and Mazumdar and trace selected models to primary sources; this is the most promising source expansion beyond the current small candidate list.
- Physics: inspect OpenStax key-equation chapters systematically, deduplicate definitions/rearrangements, and exclude vector/integral forms that cannot be reduced without arbitrary assumptions.
- DeFi AMM: assess CryptoSwap/Twocrypto/Tricrypto families as potentially distinct mechanisms; do not count solver iterations as independent equations.
- DeFi Risk: enumerate exact protocol-defined piecewise functions and liquidation mechanics, but keep each protocol/version/source family explicit.
- Chemistry: expand beyond integrated rate laws by covering equilibrium, acid-base, solubility, thermodynamics and electrochemistry; avoid overcounting textbook restatements of the same law.

**No equations in this document count toward the 295 target. No experiment, API call, or paid compute was run.**
