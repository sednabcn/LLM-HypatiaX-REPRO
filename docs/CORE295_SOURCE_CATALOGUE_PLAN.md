# Core-295 source catalogue: source selection and review plan

**Status:** source register drafted; no equation entries approved yet.  
**Design:** Option 2 — 295 structurally distinct equations, 59 per domain.

The first candidate discovery pass is recorded in [CORE295_CANDIDATE_DISCOVERY_BATCH_1.md](CORE295_CANDIDATE_DISCOVERY_BATCH_1.md). It is a review backlog only; none of its candidates count toward the 295 accepted records. The expanded source-universe pass is recorded in [CORE295_CANDIDATE_DISCOVERY_BATCH_2.md](CORE295_CANDIDATE_DISCOVERY_BATCH_2.md); it also contains discovery leads only, not accepted equations. A third verification pass is recorded in [CORE295_CANDIDATE_DISCOVERY_BATCH_3.md](CORE295_CANDIDATE_DISCOVERY_BATCH_3.md), with exact OpenStax physics equation locations and biology source leads; it likewise does not approve or count candidates. A fourth pass, [CORE295_CANDIDATE_DISCOVERY_BATCH_4.md](CORE295_CANDIDATE_DISCOVERY_BATCH_4.md), expands Chemistry coverage into equilibrium, acid–base, solubility/complexation, thermodynamics and ionic activity; it remains a discovery-only source map. A fifth pass, [CORE295_CANDIDATE_DISCOVERY_BATCH_5.md](CORE295_CANDIDATE_DISCOVERY_BATCH_5.md), begins primary-source equation tracing for Biology (Lotka, Kermack–McKendrick and Turing); it is also discovery-only. A sixth pass, [CORE295_CANDIDATE_DISCOVERY_BATCH_6.md](CORE295_CANDIDATE_DISCOVERY_BATCH_6.md), traces DeFi AMM primary invariants and implementation equations; it remains discovery-only. A seventh pass, [CORE295_CANDIDATE_DISCOVERY_BATCH_7.md](CORE295_CANDIDATE_DISCOVERY_BATCH_7.md), traces DeFi Risk lending, liquidation and auction mechanisms; it remains discovery-only. An eighth pass, [CORE295_CANDIDATE_DISCOVERY_BATCH_8.md](CORE295_CANDIDATE_DISCOVERY_BATCH_8.md), traces additional Physics equation families in electromagnetism, geometric/wave optics and quantum mechanics; it remains discovery-only. A ninth pass, [CORE295_CANDIDATE_DISCOVERY_BATCH_9.md](CORE295_CANDIDATE_DISCOVERY_BATCH_9.md), traces primary tumor-growth and PK/PD equations in Biology; it remains discovery-only. A tenth pass, [CORE295_CANDIDATE_DISCOVERY_BATCH_10.md](CORE295_CANDIDATE_DISCOVERY_BATCH_10.md), traces additional Physics fluid, thermal-transport and damped-oscillator relations; it remains discovery-only.

## Consolidated bibliography

The consolidated literature, textbook, standards and protocol reference list is maintained in [CORE295_REFERENCES.md](CORE295_REFERENCES.md). It covers all sources cited or proposed across discovery batches 1–10 and the catalogue source register. Use it as the bibliography index; each accepted equation must still carry its own exact source location and version in the catalogue record.

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

The offline adapter in `hypatiax/experiments/benchmarks/core295_catalogue.py` parses `canonical_expression` through a restricted Python-AST grammar and an explicit mathematical-function allow-list (no source-code evaluation), converts it to SymPy, and compiles it to NumPy, and maps the record to the Core-15 equation dictionary contract (`name`, `domain`, `vars`, `train_range`, `extrap_range`, `fn`, formula metadata). It requires each variable's train and extrapolation intervals. Its deterministic smoke check is a preflight only; it does not replace scientific validation, dimensional analysis, or range review.

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


## 7. Rejection and replacement procedure (required)

The 59-per-domain targets are targets for **accepted** equations, not quotas that justify retaining weak candidates. A proposed record is removed from the accepted count if any review gate fails.

Reject a candidate from the current catalogue when any of the following applies:

- its equation cannot be verified in an authoritative, versioned source at an exact location;
- its assumptions, variable definitions, units, valid regime, or deterministic input/output mapping cannot be stated;
- it duplicates a Core-15 equation or is only a variable rename, coefficient change, algebraic rearrangement, or cosmetic parameterization;
- it is a solver iteration or numerical implementation step for a mechanism already represented, rather than a distinct scientific relation;
- it is outside the supported scalar deterministic regression contract and no defensible mapping has been approved;
- its structural or derivation-family relationship makes it unsuitable as a distinct candidate under the frozen sampling design;
- the source provenance is inadequate or contradictory.

For each rejection, retain an audit record with the candidate ID, rejection reason, evidence, reviewer, and date. Rejected entries never count toward 59. Do not erase the audit trail or recycle a rejected ID for a different equation.

Replacement must follow this order:

1. Search the same predeclared domain/subdomain stratum for another candidate from the approved source universe.
2. Verify it against a primary or otherwise authoritative source and record exact location/version.
3. Complete scientific, dimensional, validity-range, structural-equivalence, source-family, and benchmark-interface review.
4. Assign a new stable ID and record the rejected candidate it replaces.
5. Re-run catalogue and structural checks; a replacement is accepted only after all gates pass.

A replacement is not automatically an independent statistical unit. Record its source-family/derivation cluster and independence eligibility separately. Multiple valid equations from one family may remain in the scientific catalogue if the sampling design permits clustered observations, but they must not be counted as independent Bernoulli units merely to reach 59. If the calibration design requires 59 independent units and a domain cannot provide them, report the shortfall and keep the calibration guarantee uncertified; do not substitute pseudo-replication.

If a stratum is exhausted, expand the source universe only through a documented, reviewed amendment made before selecting additional candidates. Preserve the original source frame and amendment history. Do not quietly broaden the domain definition, alter the 295 target, or fill the gap with synthetic variants.

## 8. Stage correspondence gate

The current `run_all.sh` sequence confirms `exp1_ablation`, its aggregate step, and `exp1_five` as the identifiable Core-15 stages. The separate `exp1b` stage is part of the DeFi route and is not a Core-15 equation-suite counterpart. No third Core-15 stage corresponding to the requested `exp295b` has yet been established from the current launcher. Therefore, do not map `exp295b` to `exp1b` by naming similarity. Before implementing the three Core-295 stage wrappers, define the intended scientific purpose and output contract for the third stage, or document that it is a new Core-295-specific stage rather than a counterpart.
