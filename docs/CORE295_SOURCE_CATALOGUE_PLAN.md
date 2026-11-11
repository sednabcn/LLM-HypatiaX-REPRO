# Core-295 source catalogue: source selection and review plan

**Status:** source register drafted; no equation entries approved yet.  
**Design:** Option 2 — 295 structurally distinct equations, 59 per domain.

## 1. Source policy

Use textbooks, peer-reviewed mathematical-biology literature, standards bodies, and primary protocol documentation. Secondary formula sheets may help discover candidate equations but cannot be the sole acceptance source. For each equation, cite an exact chapter/section/page or protocol version, not merely a general home page.

A candidate is not accepted because its name is familiar. Reviewers must verify the equation, assumptions, units, input domain, and whether it is a genuinely different functional structure. Distinct equations can still share a derivation family and therefore be statistically dependent.

## 2. Initial source register

| Domain | Reference | Intended coverage | Acceptance note |
|---|---|---|---|
| Chemistry | [OpenStax Chemistry 2e](https://openstax.org/details/books/chemistry-2e) | Kinetics, equilibrium, acid-base, thermodynamics, electrochemistry | Cite exact chapter/section for each formula |
| Chemistry | [SQA HN Chemistry Databook](https://www.sqa.org.uk/sqa/files_ccc/SQA%20Databook%20for%20HN%20Chemistry.pdf) | Kinetics, electrochemistry, thermodynamics | Formula reference; verify conventions and units |
| Chemistry | [Engineering LibreTexts reaction chemistry review](https://eng.libretexts.org/Bookshelves/Chemical_Engineering/Foundations_of_Chemical_and_Biological_Engineering_I_%28Verret_Qiao_Barghout%29/02%3A_Reaction_Chemistry/2.10%3A_Reaction_Chemistry_Chapter_Review) | Rate laws, integrated rate laws, equilibrium, Arrhenius | Candidate discovery; cross-check against textbook |
| Biology | [Oxford Mathematical Modelling and Scientific Computing handbook](https://www.cs.ox.ac.uk/files/1099/MMSC_Handbook_2008.pdf) | Population, predator-prey, competition, epidemics, enzyme kinetics, pattern formation | Course handbook identifies model families; exact sources still required |
| Biology | [University of Michigan SOCR: ODEs in Biological Systems](https://socr.umich.edu/BPAD1/BPAD1_notes/BPAD1_Chap01_MathFoundations.html) | Exponential kinetics, pharmacokinetics, tumour growth, epidemiology, enzyme kinetics | Exact model assumptions and parameter units required |
| Biology | [Daun, Equation-based models of dynamic biological systems](https://pmc.ncbi.nlm.nih.gov/articles/PMC6698907/) | Physiological and clinical differential-equation models | Peer-reviewed review; trace candidate models to primary references |
| Biology | [Mathematical and computational modeling in biology at multiple scales](https://pmc.ncbi.nlm.nih.gov/articles/PMC4396153/) | Epidemiology, cell physiology, cancer, genetics, cellular biology, biochemistry | Review for candidate model families |
| Physics | [OpenStax University Physics](https://openstax.org/details/books/university-physics-volume-1) | Mechanics, energy, momentum, oscillations, waves and thermodynamics | Use all relevant volumes and exact sections |
| Physics | [NIST CODATA constants](https://physics.nist.gov/cuu/Constants/) | Fundamental constants used by formula implementations | Constants source only; not an equation catalogue |
| Physics | [NIST Guide to the SI](https://www.nist.gov/pml/special-publication-811) | SI units and dimensional consistency | Units/standards source only |
| Physics | [OpenStax University Physics Volume 2: circuits](https://openstax.org/books/university-physics-volume-2/pages/9-key-equations) | Current, resistance, Ohm's law and power | Exact chapter-level equation reference |
| Physics | [OpenStax University Physics Volume 2: magnetic fields](https://openstax.org/books/university-physics-volume-2/pages/12-key-equations) | Biot–Savart, Ampère and magnetic-force relations | Exact chapter-level equation reference |
| Physics | [OpenStax University Physics Volume 2: Maxwell's equations](https://openstax.org/books/university-physics-volume-2/pages/16-1-maxwells-equations-and-electromagnetic-waves) | Electromagnetic field laws and waves | Exact section-level equation reference |
| Physics | [OpenStax University Physics Volume 3: optics](https://openstax.org/books/university-physics-volume-3/pages/1-key-equations) | Reflection, refraction, critical angle, polarization | Exact chapter-level equation reference |
| Physics | [OpenStax University Physics Volume 3: modern physics](https://openstax.org/books/university-physics-volume-3/pages/6-key-equations) | Photon relations, Compton shift, de Broglie and uncertainty | Exact chapter-level equation reference |
| DeFi AMM | [Uniswap developer concepts](https://developers.uniswap.org/docs/get-started/concepts/how-uniswap-works) | Constant-product invariant and concentrated liquidity | Primary protocol documentation; version-tag every formula |
| DeFi AMM | [Uniswap v2 pricing](https://developers.uniswap.org/docs/protocols/v2/concepts/pricing) | Reserve pricing, exact-input/output mechanics | Version-specific |
| DeFi AMM | [Uniswap fees](https://developers.uniswap.org/docs/get-started/concepts/fees) | Fee and protocol-fee mechanics | Version-specific |
| DeFi AMM | [Uniswap v3 whitepaper](https://app.uniswap.org/whitepaper-v3.pdf) | Concentrated liquidity and tick/range mechanics | Primary technical source |
| DeFi AMM | [AMM slippage survey](https://www.mdpi.com/2813-5288/4/3/8) | Constant product, weighted product, constant sum, Curve-style stable-swap families | Secondary discovery source; trace to protocol papers |
| DeFi AMM | [Curve mathematical derivations](https://docs.curve.finance/developer/resources/derivations/) | StableSwap invariant and Newton iteration | Primary protocol math documentation |
| DeFi AMM | [Curve StableSwap NG math contract](https://docs.curve.finance/developer/stableswap-exchange/stableswap-ng/utility_contracts/math) | Iterative invariant implementation | Version-specific contract math |
| DeFi AMM | [Balancer whitepaper](https://docs.balancer.fi/whitepaper.pdf) | Weighted invariant and weighted spot-price equations | Primary protocol whitepaper |
| DeFi Risk | [Aave V3 health factor](https://www.aave.com/docs/aave-v3/markets/health-factor) | Collateral-weighted health factor | Protocol/version-specific |
| DeFi Risk | [Aave FAQ](https://www.aave.com/faq) | Liquidation eligibility, close factor, bonus, liquidation-price concepts | Protocol/version-specific; verify current governance parameters |
| DeFi Risk | [Aave V3 overview](https://aave.dev/docs/aave-v3/overview) | Utilization-dependent interest rates and liquidation thresholds | Protocol/version-specific |
| DeFi Risk | [Aave V4 overview](https://aave.com/docs/aave-v4) | Risk premium and revised liquidation mechanics | V4-only; do not blend with V3 |
| DeFi Risk | [Compound III interest rates](https://docs.compound.finance/interest-rates/) | Utilization-kink supply and borrow rate functions | Primary protocol documentation |
| DeFi Risk | [An Empirical Study of DeFi Liquidations](https://discovery.ucl.ac.uk/id/eprint/10150722/) | Borrowing capacity, liquidation mechanisms and protocol risk | Peer-reviewed research; cite exact equations |
| DeFi Risk | [OECD DeFi Liquidations](https://www.oecd.org/content/dam/oecd/en/publications/reports/2023/07/defi-liquidations_89cba79d/0524faaf-en.pdf) | Collateral ratios and liquidation dynamics | Institutional research report |
| DeFi Risk | [Mitigating Decentralized Finance Liquidations](https://eprint.iacr.org/2023/254.pdf) | Collateralization, close factor, spread and liquidator-profit equations | Research preprint; verify version and assumptions |
| DeFi Risk | [BIS Working Paper 1171: DeFi leverage](https://www.bis.org/publications/working-paper-1171-defi-leverage) | Wallet leverage and proximity-to-liquidation risk | Central-bank research; cite exact model definitions |
| DeFi Risk | [A Risk Classification Framework for DeFi Protocols](https://www.soa.org/globalassets/assets/files/resources/research-report/2022/decentralized-finance-protocols.pdf) | Collateralization, liquidity and systemic-risk measures | Industry research report; validate each metric |

## 3. Domain coverage plan

The 59-per-domain quota should be met by a predeclared stratified source plan, not by collecting convenient equations until the quota is full.

Suggested strata (candidate areas, not yet approved quota allocations):

- **Chemistry:** reaction kinetics; chemical equilibrium; acid-base equilibria; electrochemistry; thermodynamics; transport and solution properties; spectroscopy/optics where the underlying formula is a chemistry model.
- **Biology:** population growth; predator-prey and competition; epidemiology; enzyme and receptor kinetics; pharmacokinetics; physiology; tumour/cell-growth models; ecological dynamics.
- **Physics:** mechanics and kinematics; oscillations and waves; gravitation; electromagnetism; circuits; thermodynamics/statistical mechanics; optics; quantum models.
- **DeFi AMM:** constant-product pools; weighted geometric-mean pools; stable-swap invariants; concentrated liquidity; swap quoting and fee mechanics; LP position valuation; fee growth and liquidity accounting. Formulae must represent distinct protocol mechanics, not algebraic rearrangements of one invariant.
- **DeFi Risk:** collateral and borrowing capacity; health factor and liquidation; liquidation bonus/close-factor rules; interest accrual and utilization curves; oracle/price stress; portfolio covariance and tail risk; exposure/concentration and solvency metrics.

Do not force all topics into a single smooth scalar regression task if their natural inputs/outputs are discontinuous, piecewise, stochastic, or vector-valued. Either define a mathematically appropriate deterministic benchmark mapping with transparent assumptions, or mark the candidate unsuitable for the current Core-15 runner and seek a reviewed design change.

## 4. Candidate acceptance record

Each entry must carry:

- stable equation ID, display name, domain and subdomain;
- human-readable formula plus a SymPy-parseable `canonical_expression` using only declared variable symbols;
- variable meanings, SI/financial units, parameter meanings and valid ranges;
- exact source citation and source version;
- assumptions, validity regime, singularities and boundary conditions;
- source-family/derivation cluster ID;
- canonicalization and equivalence-review result;
- independent-unit eligibility decision and rationale;
- per-variable `input_ranges` with explicit `train: [lower, upper]` and `extrapolation: [lower, upper]` bounds, plus input distribution and output transform if any;
- deterministic generator implementation/version and seed policy;
- human reviewer, review date, and acceptance state.

Candidate states: `proposed`, `source_verified`, `scientifically_reviewed`, `structurally_reviewed`, `accepted`, `rejected`. Only `accepted` entries count toward 59/domain.

The offline adapter in `hypatiax/experiments/benchmarks/core295_catalogue.py` parses `canonical_expression` with SymPy (never Python `eval`), compiles it to NumPy, and maps the record to the Core-15 equation dictionary contract (`name`, `domain`, `vars`, `train_range`, `extrap_range`, `fn`, formula metadata). It requires each variable's train and extrapolation intervals. Its deterministic smoke check is a preflight only; it does not replace scientific validation, dimensional analysis, or range review.

## 5. Independence is a separate decision

A structurally distinct formula can share a derivation, data-generating mechanism, or source family with another. Store `source_family_id` and `independence_unit_id` separately. Do not assign a unique independence unit by default. If several equations share a family, their inferential treatment must account for clustering or justify why their errors are independent under the declared sampling design.

The 59-per-domain zero-failure calibration sample-size calculation applies only if the 59 units are genuinely independent Bernoulli units sampled from the declared target population. Formula syntax alone cannot establish this.

## 6. Completion gates

- [ ] Exact source universe and inclusion/exclusion policy frozen per domain.
- [ ] Candidate strata and quota allocation frozen before selection.
- [ ] 59 source-verified and scientifically reviewed entries per domain.
- [ ] Structural equivalence and source-family reviews complete.
- [ ] Input ranges and deterministic data-generation suitability reviewed.
- [ ] Catalogue manifest hashes frozen.
- [ ] Separate independence assessment approved before calibration use.

Until these gates pass, the catalogue remains draft and the calibration manifest must remain not-ready.
