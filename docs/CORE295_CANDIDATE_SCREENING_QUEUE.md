# Core-295 candidate screening queue

**Status:** prioritized source-evidence queue, not an equation catalogue. Tier A means the equation or implementation formula is directly visible in an accessible primary/official source and can move to proposed-record drafting after a technical review. It does **not** mean scientifically accepted. Tier B means the formula is visible but exact primary-source mapping, assumptions, units or implementation details remain incomplete. Tier C means a source lead or domain-boundary issue remains.

**Current manifest (2026-11-11):** 173 candidate source-register records (Chemistry 36, Biology 35, Physics 43, DeFi AMM 26, DeFi Risk 33); 19 proposed equation records; zero accepted equation entries. Bibliography-item and discovery-batch totals are omitted until refreshed from their source files. See [proposed-record audit 1](CORE295_PROPOSED_RECORD_AUDIT_1.md) for primary-source attribution and formula-representation corrections, [audit 2](CORE295_PROPOSED_RECORD_AUDIT_2.md) for Marcus/Fick blockers, and [audit 3](CORE295_PROPOSED_RECORD_AUDIT_3.md) for Hill's primary-source verification, unit convention and Michaelis–Menten structural-overlap blockers; [audit 4](CORE295_PROPOSED_RECORD_AUDIT_4.md) distinguishes the modern Hagen–Poiseuille expression from Poiseuille's original empirical law and records its Navier–Stokes derivation-family question; [audit 5](CORE295_PROPOSED_RECORD_AUDIT_5.md) fixes the Planck spectral-exitance observable and its conversion from the 1901 spectral-energy-density equation. [audit 6](CORE295_PROPOSED_RECORD_AUDIT_6.md) adds De Buck's fixed-parameter, PK-input, empirical-scope and Michaelis–Menten subexpression policy blockers.

**Proposed-record review pass 1:** `CHEM-HENRY-001`, `CHEM-LANGMUIR-001`, and `CHEM-MARCUS-001`. Pass 2 adds `BIO-HILL-MUSCLE-001`; pass 3 adds `PHYS-POISEUILLE-001`; pass 4 adds `PHYS-PLANCK-SPECTRUM-001`; pass 5 adds `PHYS-THIN-LENS-001`; pass 6 adds `AMM-BALANCER-WEIGHTED-001`; pass 7 adds `RISK-MORPHO-LIF-001`; pass 8 adds `RISK-EULER-AUCTION-001`; pass 9 adds `RISK-COMPOUND-BORROW-KINK-001`; pass 10 adds `AMM-DODO-PMM-BASE-SHORTAGE-001`; pass 11 adds `CHEM-RAOULT-VAPOR-001`; pass 12 adds `BIO-FICK-CARDIAC-OUTPUT-001`; pass 13 adds `RISK-UNISWAP-V3-GEOMETRIC-TWAP-001`; pass 14 adds `RISK-UNISWAP-V2-ARITHMETIC-TWAP-001`; pass 15 adds `CHEM-FICK-FLUX-001`; pass 16 adds `CHEM-BEER-LAMBERT-001`; pass 17 adds `BIO-TUMOR-TURNOVER-001`. All have stable IDs, source-family IDs, normalized symbolic fingerprints and stated assumptions. Their train/extrapolation ranges and generator contracts remain deliberately unset; Marcus also requires explicit overlap review against Core-15 exclusions; its rate prefactor and LaTeX transcription were corrected in the manifest after primary-source review. See proposed-record reviews [1](CORE295_PROPOSED_RECORD_REVIEW_1.md), [2](CORE295_PROPOSED_RECORD_REVIEW_2.md), [3](CORE295_PROPOSED_RECORD_REVIEW_3.md), [4](CORE295_PROPOSED_RECORD_REVIEW_4.md), [5](CORE295_PROPOSED_RECORD_REVIEW_5.md), [6](CORE295_PROPOSED_RECORD_REVIEW_6.md), [7](CORE295_PROPOSED_RECORD_REVIEW_7.md) and [8](CORE295_PROPOSED_RECORD_REVIEW_8.md), [9](CORE295_PROPOSED_RECORD_REVIEW_9.md) and [10](CORE295_PROPOSED_RECORD_REVIEW_10.md), [11](CORE295_PROPOSED_RECORD_REVIEW_11.md), [12](CORE295_PROPOSED_RECORD_REVIEW_12.md), [13](CORE295_PROPOSED_RECORD_REVIEW_13.md), [14](CORE295_PROPOSED_RECORD_REVIEW_14.md) and [15](CORE295_PROPOSED_RECORD_REVIEW_15.md) and [16](CORE295_PROPOSED_RECORD_REVIEW_16.md) and [17](CORE295_PROPOSED_RECORD_REVIEW_17.md). The source counts are not equation counts.



**Author-pool audit 7:** the complete uploaded Chemistry (54 rows) and Biology (59 rows) blocks have now been statically screened in [CORE295_AUTHOR_POOL_CHEM_BIO_AUDIT_1.md](CORE295_AUTHOR_POOL_CHEM_BIO_AUDIT_1.md). This is a discovery-pool audit only: zero rows promoted. Key blockers include duplicate/rearranged kinetic summaries, hyperbolic saturation overlap across Monod/Holling-II/receptor/Emax, invalid Fick gradient variable metadata, unconstrained probability simplexes, PK and ecological systems sampled as independent scalars, and generic placeholder provenance. See also [author-pool DeFi audit 1](CORE295_AUTHOR_POOL_DEFI_AUDIT_1.md).

## Tier A — eligible for proposed-record drafting after technical review

| Domain | Source IDs | Candidate structure | Remaining checks before proposed record |
|---|---|---|---|
| Chemistry | CHEM-OPENSTAX-HENRY-11-3 | Henry gas-solubility relation | Fix Henry constant convention/units, dilute regime, temperature and gas/solvent assumptions. |
| Chemistry | CHEM-IUPAC-MARCUS; CHEM-MARCUS-1956 | Marcus outer-sphere electron-transfer barrier/rate | Confirm primary-paper equation and classical high-temperature/nonadiabatic regime; explicitly separate from Arrhenius exclusion. |
| Chemistry | CHEM-FICK-1855 | Fick one-dimensional diffusive flux law | Primary scan p. 66 gives the transfer law; the modern flux adapter is drafted. Structural overlap with Fourier heat-flux and Ohm current-density laws must be resolved before acceptance. |
| Chemistry | CHEM-IUPAC-BEER-LAMBERT; CHEM-BEER-1852 | Beer–Lambert decadic spectral attenuation | IUPAC gives the exact modern equation; original Beer 1852 full-text equation page remains unavailable. Fix monochromatic/homogeneous medium conditions, decadic coefficient units and concentration range. |
| Chemistry | CHEM-LANGMUIR-1918 | Langmuir single-site adsorption isotherm | Eq. 8/9 is located in the 1918 primary paper; exact adsorbate/surface context, site balance and benchmark ranges remain pending. |
| Biology | BIO-TUMOR-DBUCK-2014 | Concentration-modulated tumor turnover, primary Eq. 9 | Exact Eq. 9 is visible on printed p. 547; freeze the BYL719 PK input, tumor state, units and clinical range. Emax/IC50 term needs explicit Core-15 Michaelis–Menten overlap review. |
| Biology | BIO-HH-1952; BIO-HH-MODERN-2019 | Hodgkin–Huxley coupled membrane/gating ODE system | Freeze original/modern current sign convention, temperature scaling, gate-rate functions and full four-state system. The current catalogue expression schema is scalar-only; do not split the coupled ODEs into separate entries. Hold until a full-system schema or justified deterministic system adapter exists. |
| Biology | BIO-MICHAELIS-MENTEN-1913 | **Excluded** | Michaelis–Menten is explicitly in the Core-15 exclusion list; retain the bibliography lead for provenance only, never draft it as a Core-295 candidate. |
| Biology | BIO-MORRIS-LECAR-1981 | Two-variable conductance-based excitable-cell model | Confirm original equations 1–2, ionic-current conventions, quasi-steady activation and parameter units. Preserve the two-variable ODE system; current scalar schema cannot accept a flattened component as an independent equation. |
| Physics | PHYS-PLANCK-1901; PHYS-OPENSTAX-V3-PLANCK | Planck blackbody spectral distribution | OpenStax Eq. 6.11 is spectral exitance per unit wavelength (W m^-3); Planck 1901 Eq. 13 is spectral energy density and requires the isotropic c/4 conversion. Keep radiance distinct and cluster Stefan/Wien consequences; see audit 5. |
| Physics | PHYS-OPENSTAX-V3-THIN-LENS | Thin-lens equation | Confirm sign convention, refractive index assumptions and thin-lens regime. |
| Physics | PHYS-OPENSTAX-V3-SCHRODINGER | Time-dependent Schrödinger equation | Define one-dimensional or higher-dimensional state, potential, initial/boundary conditions and output observable. The PDE/eigenproblem requires a full-system adapter; do not substitute a scalar projection without predeclared scientific justification. |
| Physics | PHYS-OPENSTAX-V1-FLUID | Poiseuille laminar pipe-flow relation | Modern viscosity-explicit Hagen–Poiseuille form verified in OpenStax §14.7 Eq. 14.19. Do not attribute this exact form verbatim to Poiseuille's original empirical law; resolve the later Hagenbach derivation lineage and whether a special Navier–Stokes solution counts as a distinct equation. Freeze Newtonian, fully developed laminar, cylindrical, no-slip and pressure-drop conditions; see audit 4. |
| Physics | PHYS-OPENSTAX-V2-HEAT-TRANSFER | Fourier slab conduction and Stefan–Boltzmann radiation | Separate conduction and radiation families; freeze geometry, emissivity, absolute temperature and boundary conditions. |
| DeFi AMM | AMM-DODO-PMM-MATH | DODO PMM inventory-dependent marginal price and integrated trade | Pin pool type/version, guide price, equilibrium inventory, k parameter, regression mode, fee and fixed-point conventions. |
| DeFi AMM | AMM-CURVE-CRYPTOSWAP-WP | Curve CryptoSwap dynamic-peg invariant | Pin whitepaper revision, transformed balances, K/price-scale definitions and deployed contract version. |
| DeFi AMM | AMM-GYRO-ECLP-2022; AMM-GYRO-2CLP-CODE | Gyro elliptic and quadratic concentrated-liquidity invariants | Pin paper/code commit, alpha/beta or ellipse parameters, bounds, fixed-point precision and rounding. Keep E-CLP and 2-CLP distinct but cluster protocol lineage. |
| DeFi AMM | AMM-BALANCER-WEIGHTED-MATH | Weighted geometric pool invariant | Require non-equal weights or multi-asset structure; exclude equal-weight two-token constant-product special case. |
| DeFi AMM | AMM-SOLIDLY-STABLE-V2 | Solidly stable polynomial invariant | Pin fork/version, reserve scaling, pair correlation regime and contract implementation. Volatile xy=k remains excluded. |
| DeFi Risk | RISK-MORPHO-LIF | LLTV-dependent liquidation incentive factor | Pin Morpho code commit/constants, LLTV domain, oracle conversion and fixed-point rounding. |
| DeFi Risk | RISK-EULER-REVERSE-AUCTION | Health-dependent capped liquidation discount | Pin EVK commit, health calculation, max discount, rounding, cool-off and collateral quote. |
| DeFi Risk | RISK-UNISWAP-V2-TWAP; RISK-UNISWAP-V3-TWAP | Arithmetic v2 TWAP and geometric v3 tick TWAP | Fix observation interval, token direction, timestamp wrap, tick rounding, fixed-point scales and liquidity semantics. |
| DeFi Risk | RISK-COMPOUND-IR; RISK-COMPOUND-LIQUIDATION | Compound III utilization-kink rate and collateral discount | Pin Comet version, market parameters, utilization denominator, annualization, collateral factor and quote units. |

## Tier B — formula visible; source/assumption work still required

The Hill muscle force–velocity relation is drafted as `BIO-HILL-MUSCLE-001`; the original 1938 characteristic equation is now verified at printed pp. 183–184 and 193. It remains proposed/Tier B because the force-versus-stress convention, velocity normalization, muscle/activation scope, and affine one-pole structural overlap with the Core-15-excluded Michaelis–Menten family remain unresolved. See [proposed-record audit 3](CORE295_PROPOSED_RECORD_AUDIT_3.md).

| Domain | Source IDs | Candidate structure | Main blocker |
|---|---|---|---|

| Chemistry | CHEM-ERDEY-GRUZ-VOLMER-1930; CHEM-BUTLER-1924 | Butler–Volmer electrode kinetics | Historical attribution and generalized modern form need primary-source synthesis; Tafel is an asymptote, Nernst is equilibrium. |
| Chemistry | CHEM-LH-WACHS-2024 | Langmuir–Hinshelwood surface-reaction kinetics | Formula visible in modern review; primary mechanistic equation/page and catalyst-specific rate-determining-step assumptions still require tracing. |
| Chemistry | CHEM-RAOULT-1887; CHEM-RAOULT-FREEZING-1882 | Ideal-solution vapor pressure and freezing-point depression | Modern formula forms are accessible, but exact original equation notation/concentration basis remains to verify. |

| Chemistry | CHEM-RIDEAL-1939; CHEM-ELEY-RIDEAL-1940; CHEM-ER-ENG-REACTION; CHEM-IUPAC-LANGMUIR-RIDEAL | Rideal–Eley / Langmuir–Rideal gas/adsorbed surface-reaction rate | Rideal's 1939 primary paper (DOI 10.1017/S030500410002082X) establishes the gas-phase/adsorbed-species mechanism; IUPAC defines the same mechanism class. The primary record does not yet supply a verified general scalar rate equation. Published engineering rate forms are model-specific and remain secondary leads; do not draft a generic equation until the kinetic assumptions and exact catalyst pathway are sourced. |
| Biology | BIO-SIMEONI-2004; BIO-TUMOR-ODE-COMPARISON-2020 | Exponential-to-linear tumor growth and transit-compartment TGI | Exact growth formula currently transcribed from secondary comparison; original primary equation/page remains outstanding. |
| Biology | BIO-HILL-1910; BIO-ADAIR-1925 | Hemoglobin oxygen-binding models | Hill/Adair formula transcription needs original-paper page verification; keep common hemoglobin source cluster. |
| Biology | BIO-HILL-MUSCLE-1938 | Hill muscle force–velocity relation | Primary characteristic equation verified in Hill (1938), printed pp. 183–184 and 193. Resolve force-versus-stress units, velocity normalization, muscle preparation and maintained tetanic/constant-load scope, plus affine one-pole structural overlap with the Core-15 Michaelis–Menten exclusion; see audit 3. The record is drafted but remains proposed pending primary-page verification. |
| Biology | BIO-FICK-1870; BIO-WINDKESSEL-FRANK-1899; BIO-WINDKESSEL-WESTERHOF-2009 | Fick cardiac output and Windkessel hemodynamics | Original notation, assumptions and modern model translation require exact page-level review. |
| Biology | BIO-FITZHUGH-1961 | FitzHugh/BVP reduction | Canonical dimensionless FHN form is a later parameterization; exact 1961 original equations need transcription. |
| Physics | PHYS-NAVIER-1822; PHYS-STOKES-1845 | Modern Navier–Stokes system | Modern compact form is a synthesis; exact historical equations and Newtonian constitutive assumptions need lineage mapping. |
| Physics | PHYS-EULER-ELASTICA-1744; PHYS-EULER-COLUMN-1759; PHYS-TIMOSHENKO-1921; PHYS-TIMOSHENKO-BEAM-EQUATIONS | Elastica, buckling and Timoshenko beam models | Exact original equation and end-condition mapping; distinguish Euler–Bernoulli limit from Timoshenko shear/rotary inertia. |
| DeFi AMM | AMM-LFJ-LIQUIDITY-BOOK | Discrete-bin fixed-price AMM | Per-bin accounting invariant and rounding need pinned contract verification. |
| DeFi AMM | AMM-SWAAP-V2-WP | RfQ market-making optimization and safeguards | Confirm DeFi AMM domain includes RfQ; stochastic objective needs deterministic benchmark contract. |
| DeFi Risk | RISK-AAVE-HEALTH; RISK-AAVE-RISK-V3-PARAMS | Aave health factor and collateral thresholds | Related collateral/debt ratio family; pin oracle/threshold/accrual conventions and avoid protocol-name duplication. |
| DeFi Risk | RISK-CHAINLINK-FEED-FRESHNESS | Chainlink heartbeat/deviation and consumer maxAge | Feed-specific parameters and consumer safety conditions need a versioned feed/network contract. |

## Tier C — source lead or domain decision pending

| Domain | Source IDs | Why held |
|---|---|---|
| Chemistry | CHEM-HINSHELWOOD-PRICHARD-1925 | Historical surface-catalysis paper located; exact mechanism-specific rate equation still needs primary transcription. |
| Biology | BIO-MONOD-1949 | **Not eligible as a distinct candidate**: the Monod hyperbolic saturation form is structurally equivalent to the explicitly excluded Core-15 Michaelis–Menten family; retain as a source lead only. |
| Biology | BIO-LOTKA-1920; BIO-KERMACK-MCKENDRICK-1927; BIO-TURING-1952 | Strong primary source families, but vector/integral/spatial model adapters and independence units need full review. |
| Physics | PHYS-OPENSTAX-V3-DIFFRACTION; PHYS-OPENSTAX-V3-QHO; PHYS-OPENSTAX-V1-DAMPED-OSCILLATOR | Equations are visible, but wave-optics and quantum-eigenproblem family overlaps plus model-specific ranges/benchmark adapters remain to be frozen. |
| DeFi AMM | AMM-BANCOR-2017-WP | Archived third-party whitepaper copy; official archive/contract release and domain inclusion for reserve-backed issuance need confirmation. |
| DeFi AMM | AMM-MAVERICK-DYNAMIC; AMM-CARBON-ADJUSTABLE-CURVES | Complete price/invariant/state-transition equations not yet recovered from pinned code. |
| DeFi Risk | RISK-SKY-COLLATERAL-LIQUIDATION; RISK-MAKER-MIP45-LIQ2; RISK-LIQUITY-STABILITY-POOL | Sky/Maker source versioning and Liquity's complete product/scale/epoch accounting remain incomplete; MIP45 is obsolete historical context. |

## Next screening order

1. Draft proposed records from Tier A only, preserving coupled systems as systems and marking every record proposed, never accepted.
2. For each proposed record, compute a normalized structural fingerprint and document derivation parent, source-family identifier and statistical-unit identifier.
3. Freeze units, validity domains, deterministic input/output adapter, train/extrapolation ranges and data-generator contract before adding it to the manifest.
4. Run the local catalogue validator only in a permitted offline repository environment; do not dispatch workflows or run scientific experiments as part of this source-screening pass.
5. Promote to accepted only after exact-source, scientific, equivalence, provenance and independence review.

**No equation is accepted by this queue.** Tier A is an order of work, not a quality guarantee.

## User-supplied author_pool.py DeFi screening audit

Static review of all 54 DeFi AMM and 57 DeFi Risk rows in the user-supplied `author_pool.py` is recorded in [author-pool DeFi audit 1](CORE295_AUTHOR_POOL_DEFI_AUDIT_1.md). The script was not executed and no benchmark/experiment was run. **No rows were promoted or accepted.**

Key blockers:
- DeFi AMM: constant-product swap/price/LP/impermanent-loss/depth rows collapse into shared families and collide with Core-15 exclusions; Balancer trade directions and spot price derive from one weighted invariant; Uniswap V3 amount/liquidity/position/tick metrics share a concentrated-liquidity family; the two supplied Curve shortcuts are not the documented StableSwap invariant; Bancor buy/sell/spot are one connector-weight family; TWAP, LVR, MEV, bonding-curve and reward sketches need exact source/model contracts.
- DeFi Risk: all VaR variants collide with the Core-15 Value at Risk exclusion; liquidation-price rows collide with the Liquidation Price exclusion; correlation extrapolation to 4 is invalid; portfolio weights/covariances lack joint constraints; the quartic borrow-rate expression is not Compound III's documented piecewise-linear kink model; generic APR/APY, volatility, funding, credit and liquidation sketches need source-specific definitions.
- Raw counts are 54 AMM and 57 Risk, but accepted counts remain zero. Do not fill the 59/domain target by counting algebraic rearrangements, derived observables or unsupported generic formulas.


## Additional author-pool screen (2026-11-11)

The second static screen covers all 54 Chemistry, 59 Biology and 75 Physics rows (188 candidates). See [Author Pool Screening Audit 2](CORE295_AUTHOR_POOL_SCREENING_AUDIT_2.md). The review identifies cross-family overlaps, formula/definition defects and missing source/range provenance. No candidates were accepted or imported; the formal catalogue count is unchanged.


## Selected source-verification leads (2026-11-11)

See [Source Verification Audit 3](CORE295_SOURCE_VERIFICATION_AUDIT_3.md). Five existing source-register leads were checked at equation/model level: Langmuir–Hinshelwood and Eley–Rideal surface kinetics; Adair's four-step hemoglobin binding polynomial; the age-structured Kermack–McKendrick epidemic model; Turing's coupled reaction–diffusion system; and Euler column stability. These remain held, not accepted. The audit distinguishes different mechanisms/structures from shared source families and requires system-level adapters for coupled models.


## Source verification audit 4 (2026-11-11)

[Source Verification Audit 4](CORE295_SOURCE_VERIFICATION_AUDIT_4.md) checks Frank's original Windkessel lineage and the canonical two-element RC equation, and transcribes FitzHugh's original 1961 two-state BVP system and parameter constraints. The diastolic exponential and impedance are derived forms of the Windkessel model; the BVP equations are a coupled system, not separate scalar entries. Both remain held pending exact model contracts, ranges and independence review. No candidates were accepted.


## Source verification audit 5 (2026-11-11)

[Source Verification Audit 5](CORE295_SOURCE_VERIFICATION_AUDIT_5.md) reviews Fick's 1870 cardiac-output mass-balance principle and Timoshenko's 1921 shear-correction source. Fick remains held pending original-page transcription and a decision on whether measurement equations are in scope; Timoshenko remains a source lead only because the primary equation text was not accessible and the Bresse–Timoshenko lineage needs precise mapping. No candidates were accepted.


## Source verification audit 6 (2026-11-11)

[Source Verification Audit 6](CORE295_SOURCE_VERIFICATION_AUDIT_6.md) checks the JOE v2.1 Liquidity Book whitepaper against a pinned joe-v2 implementation commit. The model's per-bin constant-sum accounting, geometric bin-price grid and traversal across nonempty bins form one discrete multi-bin AMM system; bin equations, swap directions and fee/volatility components are not separate independent candidates. The lead remains held pending a frozen model/implementation contract. No candidate was accepted.


## Source verification audit 7 (2026-11-11)

[Source Verification Audit 7](CORE295_SOURCE_VERIFICATION_AUDIT_7.md) classifies the Chainlink feed-freshness lead. Official documentation separates feed-specific heartbeat/deviation update triggers from consumer-defined updatedAt/maxAge checks. These are operational safety rules, not a universal portable equation; retain as risk/provenance context and do not count toward the equation target unless the domain contract explicitly includes version-pinned safety predicates.


## Source verification audit 8 (2026-11-11)

[Source Verification Audit 8](CORE295_SOURCE_VERIFICATION_AUDIT_8.md) verifies the DODO PMM's piecewise inventory-dependent marginal price, integrated finite-trade equation and quadratic inversion against official mathematical documentation and the pinned contractV2 implementation commit 2f1bcdac7ef1beee7599a756e2eed26732c2536d. The branches, trade directions, integral, inversion and R-state changes are components of one PMM state-transition family, not separate independent entries. Strong lead; held pending exact pool/version, unit/range and statistical-unit contracts. No candidate accepted.


## Source verification audit 9 (2026-11-11)

[Source Verification Audit 9](CORE295_SOURCE_VERIFICATION_AUDIT_9.md) transcribes Carbon whitepaper v1.2's adjustable hyperbolic invariant, swap equation and marginal-price equation. The paper explicitly identifies the intermediate curves as translated/scaled constant-product hyperbolas, financially equivalent to virtual-token models, with constant-price as the endpoint. The one-direction orders and linked strategy are protocol-state innovations, not additional independent equations under the current equation-only policy. Do not count this lead as a structurally distinct equation; retain as architecture context.


## Source verification audit 10 (2026-11-11)

[Source Verification Audit 10](CORE295_SOURCE_VERIFICATION_AUDIT_10.md) compares the registered Uniswap v2 and v3 oracle implementations. V2 computes an arithmetic time-weighted mean of reserve-ratio spot prices from cumulative-price deltas; v3 averages ticks and converts the arithmetic mean tick to a geometric mean price, with negative-floor rounding. These are distinct estimands, but they share a broad oracle family and market dependencies. Hold both pending the catalogue's family/independence policy; do not count helper accumulators, token inverses, time windows or v3 harmonic-mean liquidity as extra price equations.


## Source verification audit 11 (2026-11-11)

[Source Verification Audit 11](CORE295_SOURCE_VERIFICATION_AUDIT_11.md) verifies the Curve CryptoSwap dynamic-peg invariant against Egorov's 2021 primary whitepaper; Morpho Blue's capped LLTV-dependent liquidation incentive factor against official documentation and the pinned Morpho implementation; and Compound III's piecewise-affine utilization-kink borrow rate against official documentation and the pinned Comet implementation. CryptoSwap remains held pending a pinned deployed implementation and numerical contract; Morpho LIF and Compound borrow kink remain held pending family-level comparisons and frozen unit/parameter/rounding contracts. The audit rejects counting helper definitions, supply-rate conversions, annualization, oracle/price-scale updates or liquidation bookkeeping as additional independent equations. No candidates were accepted and the formal catalogue is unchanged.


## Source verification audit 12 (2026-11-11)

[Source Verification Audit 12](CORE295_SOURCE_VERIFICATION_AUDIT_12.md) verifies the Gyroscope E-CLP's shifted/stretched/rotated ellipse invariant against its November 2022 technical specification; screens the registered Gyro 2-CLP math snapshot and identifies its virtual-reserve invariant as constant product after translation; and verifies Solidly V2's stable quartic invariant (x^3y+xy^3) against official documentation. E-CLP and Solidly stable remain held pending pinned deployed implementations and numerical contracts. Gyro 2-CLP is not a new structurally distinct equation under the current Core-15 Constant Product exclusion. No candidates were accepted.


## Source verification audit 13 (2026-11-11)

[Source Verification Audit 13](CORE295_SOURCE_VERIFICATION_AUDIT_13.md) verifies Euler EVK's health-dependent capped liquidation discount against official documentation and the pinned `Liquidation.sol` commit. The implementation uses health (h=) risk-adjusted collateral/liability, retained discount factor (f=max(h,1-m)), equivalent discount (d=min(1-h,m)), and collateral yield value (R/f) before availability and conversion constraints. This is not a time-elapsed auction schedule. It is structurally distinct from Morpho's LLTV-dependent capped rational LIF, but both remain in the liquidation-incentive family and held pending complete valuation/unit/rounding contracts. No candidates were accepted.


## Source verification audit 14 (2026-11-11)

[Source Verification Audit 14](CORE295_SOURCE_VERIFICATION_AUDIT_14.md) checks the current Sky LIQ2.0 documentation and the registered Abacus implementation source. It transcribes the linear decrease (P_0(1-t/\tau)) until zero, the stairstep exponential (P_0c^{\lfloor t/s\rfloor}), and the continuous per-second exponential (P_0c^t). The implementation explicitly identifies the stairstep and continuous forms as equivalent when (s=1). These are configurable price calculators in one Dutch-auction architecture, not separate liquidation systems. Keep the linear and exponential structures distinct but cluster them; do not count parameter variants, (s=1), auction reset, initial-price buffer or partial-take logic as extra equations. Hold pending immutable source commit and fixed-point adapter. No candidates were accepted.


## Source verification audit 15 (2026-11-11)

[Source Verification Audit 15](CORE295_SOURCE_VERIFICATION_AUDIT_15.md) checks Liquity V1's product-sum Stability Pool derivation against Pardoe's December 2020 paper, V1 documentation and a fetched Solidity source snapshot. The core coupled state is (P_n=\prod_i(1-Q_i/D_{i-1})), (S_n=\sum_k(E_k/D_{k-1})P_{k-1}), with depositor outputs (d_n=d_tP_n/P_t) and (e_n=d_t(S_n-S_t)/P_t). Treat it as one stateful accounting/system candidate, not separate formulas for P, S, deposit, gain, scale or LQTY rewards. Hold pending immutable code pin, Recovery Mode/domain boundary and deterministic stateful adapter. No candidates were accepted.


## Source verification audit 16 (2026-11-11)

[Source Verification Audit 16](CORE295_SOURCE_VERIFICATION_AUDIT_16.md) verifies Aave V3's multi-collateral health factor as Σ(collateral value × asset liquidation threshold) / total debt. This is the portfolio-weighted form of the same risk-adjusted collateral/debt health family already represented by Euler EVK; Morpho's single-collateral health ratio is the corresponding one-collateral case. Retain Aave as multi-collateral source/adapter context, not an additional independent equation. Keep health metrics distinct from liquidation incentive functions. No new proposed record or accepted equation was added.


## Source verification audit 17 (2026-11-11)

[Source Verification Audit 17](CORE295_SOURCE_VERIFICATION_AUDIT_17.md) verifies Compound III's post-absorption collateral storefront discount against official docs and the pinned Comet implementation: (d_{store}=StoreFrontPriceFactor(1-LiquidationFactor_a)), followed by discounted collateral price and a decimal-aware base-to-collateral quote. This is distinct in role from health-based liquidation eligibility, Morpho/Euler liquidation incentives and Sky time-decay auctions, but it is a configured proportional sale-price adjustment rather than a strong new structural equation. Retain as source-family context; do not add a proposed record or count the quote conversion as another equation.


## Source verification audit 18 (2026-11-11)

[Source Verification Audit 18](CORE295_SOURCE_VERIFICATION_AUDIT_18.md) verifies the classical outer-sphere Marcus barrier against IUPAC and distinguishes the 1956 paper's solution collision-number prefactor from IUPAC's encounter-complex Eyring prefactor. The proposed formula pairs the classical quadratic driving-force barrier with the collision-frequency prefactor; it remains held because the prefactor convention and overlap with Core-15 Arrhenius/generic Rate Law exclusions require an explicit ruling. Do not count barrier, rate, prefactor or reaction-region variants separately.


## Source verification audit 19 (2026-11-11)

[Source Verification Audit 19](CORE295_SOURCE_VERIFICATION_AUDIT_19.md) verifies De Buck et al. (2014) equation 9 (printed p. 547) for the BYL719 tumour-growth turnover model: zero-order growth inhibited by a saturable Emax concentration response, minus first-order tumour loss. The state is the one-dimensional sum of longest lesion diameters; concentration is an external PK input from the study's t_lag model. Treat the complete ODE as one drug-specific PK/PD turnover system, not separate Emax/growth/degradation/PK equations. Hold pending input trajectory, units/ranges, clinical scope and turnover-family dependence policy. No candidates were accepted.


## Source verification audit 20 (2026-11-11)

[Source Verification Audit 20](CORE295_SOURCE_VERIFICATION_AUDIT_20.md) verifies Henry's gas-solubility proportionality and Raoult's ideal-solution component vapor-pressure equation from OpenStax, and the decadic Beer–Lambert attenuation expression from IUPAC. Henry and Raoult describe different physical regimes but share the same bare linear-proportionality structure; do not automatically count both as structurally distinct. Raoult's original 1887 page-level transcription and Beer (1852) original equation-page transcription remain outstanding. Beer/Lambert/absorbance/transmission forms are one family. All remain held.


## Source verification audit 21 (2026-11-11)

[Source Verification Audit 21](CORE295_SOURCE_VERIFICATION_AUDIT_21.md) verifies Hill's muscle force–velocity characteristic equation against the 1938 original PDF: equation (2) first appears on printed p. 162; pp. 176–177 contain later mechanical verification. It is not Hill ligand-binding. It also verifies Planck's original 1901 equation (13) as spectral energy density per wavelength and derives the proposed modern spectral exitance by the isotropic (c/4) conversion. Rename the candidate output symbol from ambiguous (I_\lambda) to (M_\lambda); keep frequency/radiance forms and Wien/Stefan consequences in the same Planck family. Both candidates remain held for ranges/output conventions.


## Source verification audit 22 (2026-11-11)

[Source Verification Audit 22](CORE295_SOURCE_VERIFICATION_AUDIT_22.md) verifies the thin-lens equation and signed image/focal-length conventions against OpenStax Eq. 2.19, and Hagen–Poiseuille flow against OpenStax Eq. 14.19 with its Eq. 14.18 resistance derivation. The thin-lens rearrangement and Poiseuille resistance/pressure-flow components are not separate entries. Both candidates remain held pending signed optical ranges and a physically constrained laminar Reynolds-number/geometry generator.


## Source verification audit 23 (2026-11-11)

[Source Verification Audit 23](CORE295_SOURCE_VERIFICATION_AUDIT_23.md) closes the original-source gap for the Fick cardiac-output relation: the 1870 scanned report gives the measurement principle in prose, not a displayed algebraic equation. The modern faithful mass-balance transcription is ẏVO2 = Q(CaO2−CvO2), hence Q = ẏVO2/(CaO2−CvO2), with oxygen content units and steady-state/system-boundary assumptions explicit. The CO2 cross-check and stroke-volume conversion are not separate equations. This is distinct from Fick's diffusion law despite the shared surname. Candidate remains held pending physiological ranges.


## Source verification audit 24 (2026-11-11)

[Source Verification Audit 24](CORE295_SOURCE_VERIFICATION_AUDIT_24.md) verifies Balancer's weighted geometric invariant (V=\prod_i B_i^{w_i}), Σw_i=1, against official documentation and the fetched V2 WeightedMath implementation. The proposed three-token expression is a fixed-arity adapter to the general n-token invariant; equal two-token weights reduce to excluded constant product. Keep spot-price and swap-output equations in the same family. Hold pending immutable implementation commit, token scaling, weight-sampling and fixed-point rounding contracts.


## Source verification audit 25 (2026-11-11)

[Source Verification Audit 25](CORE295_SOURCE_VERIFICATION_AUDIT_25.md) verifies Langmuir's 1918 primary single-site coverage equation, Eq. (8), and its amount-adsorbed Eq. (9). The source's one-site, one-molecule, monolayer and adsorption/desorption equilibrium assumptions are explicit. The formula is the same rational saturation form as Michaelis–Menten/Hill-one occupancy, so the Core-15 cross-domain exclusion and structural-unit policy must be resolved before acceptance. Keep Eq. (8), Eq. (9), LH adsorption substeps and linearized forms in one family.


## Source verification audit 26 (2026-11-11)

[Source Verification Audit 26](CORE295_SOURCE_VERIFICATION_AUDIT_26.md) verifies Fick's original 1855 p. 66 local transfer relation (dM=-Qk(dy/dx)dt) and its modern 1D flux form (J=-D,dC/dx). Fick explicitly analogizes the constitutive law to Fourier heat conduction and Ohm electrical conduction, so the same linear-gradient transport structure crosses domain boundaries. Hold pending the declared physical-mechanism versus strict structural-equivalence policy; do not count the derived diffusion PDE, geometry specializations or Fourier/Ohm analogues as separate equations under a strict form rule.


## Proposed-record source verification matrix (2026-11-11)

[Core-295 Proposed-Record Source Verification Matrix](CORE295_PROPOSED_RECORD_SOURCE_VERIFICATION_MATRIX.md) consolidates audit coverage for all 19 currently proposed records, their source evidence, hold reasons and cross-domain structural-equivalence blockers. It does not change any record status: 19 proposed, zero accepted, sampling frame unfrozen.


## Discovery batch 25 (2026-11-11)

[Candidate Discovery Batch 25](CORE295_CANDIDATE_DISCOVERY_BATCH_25.md) expands Chemistry source discovery to Nernst electrochemical equilibrium, Debye–Hückel ionic activity, Clausius–Clapeyron vapor-pressure dependence and van't Hoff equilibrium-temperature dependence. It flags their structural-family relationships and the osmotic-pressure/Ideal Gas Law exclusion. Discovery-only; no source-register or equation-catalogue entries were added.


## Discovery batch 26 (2026-11-11)

[Candidate Discovery Batch 26](CORE295_CANDIDATE_DISCOVERY_BATCH_26.md) expands Biology discovery to Nicholson–Bailey's discrete host–parasitoid system, Leslie's age-structured population projection matrix, Taylor–Jonker replicator dynamics and Beverton–Holt stock–recruitment. The first three are complete vector/discrete systems requiring a system adapter; Beverton–Holt is flagged as a rational saturation-form overlap with Langmuir/MM. Discovery-only; no catalogue entries were added.


## Discovery batch 27 (2026-11-11)

[Candidate Discovery Batch 27](CORE295_CANDIDATE_DISCOVERY_BATCH_27.md) adds Physics leads for Kepler's third-law orbital relation, the Lorentz force law and Bragg crystal diffraction. Kepler is a derived orbital relation with Newtonian-force lineage; Lorentz requires a full-vector adapter and must be distinguished from Maxwell's field system; Bragg shares the normalized path-difference interference form with slit/grating maxima. Discovery-only; no catalogue entries were added.


## Discovery batch 28 (2026-11-11)

[Candidate Discovery Batch 28](CORE295_CANDIDATE_DISCOVERY_BATCH_28.md) expands DeFi Risk discovery to Parkinson high-low range variance, GARCH(1,1), normal expected shortfall and Merton structural credit risk. EWMA is identified as the IGARCH boundary special case of GARCH(1,1), not an independent structure. General financial-risk applicability to DeFi remains a domain-scope decision. Discovery-only; no catalogue entries were added.


## Source verification audit 27 (2026-11-11)

[Source Verification Audit 27](CORE295_SOURCE_VERIFICATION_AUDIT_27.md) verifies the modern Nernst equation against IUPAC and Nernst's 1889 electrode-potential theory, while distinguishing the original dissolution-pressure/osmotic-pressure form from the later whole-cell reaction-quotient expression. It also clarifies Debye–Hückel's low-ionic-strength square-root law for the mean ionic activity coefficient; single-ion activity is convention-dependent and not separately measurable. Discovery batch 25 was corrected accordingly. These leads remain discovery-only.


## Source verification audit 28 (2026-11-11)

[Source Verification Audit 28](CORE295_SOURCE_VERIFICATION_AUDIT_28.md) verifies Leslie's age-structured matrix recurrence directly against the 1945 original (printed pp. 183–184) and Taylor–Jonker's continuous replicator system directly against the 1978 original Eq. (2). Both are complete vector systems requiring constrained adapters; do not count component equations or derived stability outputs separately. Nicholson–Bailey's 1935 primary paper is bibliographically confirmed, but the equation-level transcription remains secondary and unverified.


## Discovery batch 29 (2026-11-11)

[Candidate Discovery Batch 29](CORE295_CANDIDATE_DISCOVERY_BATCH_29.md) adds Balancer V2 Linear Pool as a candidate lead: a rate-normalized constant-sum invariant with a piecewise nominal main-balance fee transform. Keep the invariant, nominal-balance mapping, BPT conversion and swap directions in one family. Hold pending immutable implementation commit and the constant-sum/StableSwap family decision; no catalogue entry was added.


## Discovery batch 30 (2026-11-11)

[Candidate Discovery Batch 30](CORE295_CANDIDATE_DISCOVERY_BATCH_30.md) adds Butler–Volmer interfacial current–overpotential kinetics and Nernst–Planck ionic flux/transport. Butler–Volmer is distinct from Nernst equilibrium and Tafel asymptotes; Nernst–Planck includes Fick diffusion plus electric migration and convection, requiring a coupled PDE/system adapter. Discovery-only; no catalogue entries were added.


## Discovery batch 31 (2026-11-11)

[Candidate Discovery Batch 31](CORE295_CANDIDATE_DISCOVERY_BATCH_31.md) adds Bernoulli's streamline mechanical-energy relation, Stokes drag for a sphere in creeping flow, and the Young–Laplace curvature pressure jump. It groups constant-height Bernoulli, terminal settling, and spherical/soap-bubble capillary forms as specializations, not extra equations. Discovery-only; no catalogue entries were added.


## Discovery batch 32 (2026-11-11)

[Candidate Discovery Batch 32](CORE295_CANDIDATE_DISCOVERY_BATCH_32.md) screens Maverick V2's dynamic-distribution AMM. Its tick invariant (L^2=(B+L/\sqrt{p_u})(A+L\sqrt{p_l})) is constant product in virtual reserves, so it is related to Gyro 2-CLP rather than a new invariant structure. Dynamic bin movement and log-price TWAP remain protocol architecture/state features, not separate equations.


## Discovery batch 33 (2026-11-11)

[Candidate Discovery Batch 33](CORE295_CANDIDATE_DISCOVERY_BATCH_33.md) adds stochastic DeFi Risk leads: OU log-depeg/basis diffusion, CIR nonnegative short-rate diffusion, Hawkes self-exciting liquidation-event intensity and Merton jump-diffusion returns. These are complete stochastic processes requiring a declared measure, state/event definition, calibration and simulator; discovery-only.


## Discovery batch 34 (2026-11-11)

[Candidate Discovery Batch 34](CORE295_CANDIDATE_DISCOVERY_BATCH_34.md) adds Fisher's spatial reaction–diffusion wave, Gierer–Meinhardt activator–inhibitor morphogenesis and a chemostat–Monod system. Fisher's logistic reaction is linked to the Core-15 logistic exclusion; Gierer–Meinhardt is a nonlinear kinetics member of the Turing/morphogenesis family and needs primary equation transcription; chemostat–Monod must be treated as a coupled system, not a separate MM saturation formula.


## Source verification audit 29 (2026-11-11)

[Source Verification Audit 29](CORE295_SOURCE_VERIFICATION_AUDIT_29.md) verifies Fisher's original 1937 reaction–diffusion Eq. (1) and Gierer–Meinhardt's original 1972 different-source activator–inhibitor system Eq. (15a,b). Fisher's local reaction is the Core-15-excluded logistic term; Gierer–Meinhardt's original model has explicit source-density fields (Q(x),Q'(x)) and is not identical to the commonly quoted simplified form. Both are complete PDE systems and remain discovery-only pending family policy and PDE adapters.


## Discovery batch 35 (2026-11-11)

[Candidate Discovery Batch 35](CORE295_CANDIDATE_DISCOVERY_BATCH_35.md) adds quantum-physics leads for the Schrödinger stationary eigenvalue PDE, Compton wavelength shift and de Broglie matter wavelength–momentum relation. The Schrödinger model needs a complex PDE/eigenvalue adapter; Compton is a scattering kinematic relation; de Broglie's compact λ=h/p formula needs careful primary-source/provenance convention. Discovery-only.


## Discovery batch 36 (2026-11-11)

[Candidate Discovery Batch 36](CORE295_CANDIDATE_DISCOVERY_BATCH_36.md) adds Goldman–Hodgkin–Katz multi-ion membrane potential and revised Starling capillary filtration. GHK is a constant-field zero-current relation distinct from the single-ion Nernst equation; classical/revised Starling forms belong to one lineage, with the revised form using subglycocalyx oncotic pressure.


## Source verification audit 30 (2026-11-11)

[Source Verification Audit 30](CORE295_SOURCE_VERIFICATION_AUDIT_30.md) verifies Hawkes's original 1971 self-exciting intensity definition, exponential kernel and stationarity condition, and Merton's original 1976 jump-diffusion stock-return Eq. (2) and compound-Poisson distribution. OU and CIR are confirmed as primary model lineages, but their common modern SDE forms still need direct original equation-page transcription. All remain discovery-only; no catalogue entries were added.


## Source verification audit 31 (2026-11-11)

[Source Verification Audit 31](CORE295_SOURCE_VERIFICATION_AUDIT_31.md) clarifies that GHK is a steady-state zero-current diffusion potential under a constant-field assumption, not a thermodynamic Nernst equilibrium potential; the three-ion expression is the Hodgkin–Katz extension of Goldman's original constant-field treatment. It also distinguishes the revised Starling Πg force-balance component from the full implicit steady-state Eq. (3), where Jv appears inside the Péclet number. Discovery batch 36 was corrected accordingly; both leads remain discovery-only.


## Discovery batch 37 (2026-11-11)

[Candidate Discovery Batch 37](CORE295_CANDIDATE_DISCOVERY_BATCH_37.md) adds Heston's coupled stochastic-volatility price/variance system and the Cramér–Lundberg reserve/compound-Poisson ruin model. Heston's CIR variance component and Merton no-jump limits are not extra equations; Cramér–Lundberg's ruin probability is a first-passage output of one reserve system. DeFi applicability requires a token-market or protocol insurance-reserve domain contract.


## Source verification audit 32 (2026-11-11)

[Source Verification Audit 32](CORE295_SOURCE_VERIFICATION_AUDIT_32.md) verifies Heston's original price and square-root variance equations (1993 Eqs. 1 and 4) and distinguishes physical-measure drift from the risk-neutralized variance process (Eq. 27). It also checks the Cramér–Lundberg reserve process and the exact infinite-horizon ruin formula for exponential claim sizes. Heston's CIR variance component and pricing PDE are not separate candidates; Cramér–Lundberg's ruin time and distribution-specific ruin probability are outputs of one reserve system. Both remain discovery-only pending DeFi domain and adapter decisions.


## Source verification audit 33 (2026-11-11)

[Source Verification Audit 33](CORE295_SOURCE_VERIFICATION_AUDIT_33.md) verifies Kepler's third-law orbital period equation, the vector Lorentz force law, and Bragg's crystal-plane diffraction condition against OpenStax. Kepler is a derived consequence of Newtonian inverse-square dynamics; Lorentz is a distinct vector matter–field force law; Bragg shares the normalized path-difference interference structure with slit/grating maxima. Only Lorentz currently clears the immediate structural-form concern, and it remains discovery-only pending a vector adapter.


## Source verification audit 34 (2026-11-11)

[Source Verification Audit 34](CORE295_SOURCE_VERIFICATION_AUDIT_34.md) verifies Parkinson's 1980 original range-variance estimator (0.361/n\sum_i\ln(H_i/L_i)^2), Bollerslev's GARCH(p,q) conditional-variance family and its GARCH(1,1) specialization, and the normal-loss expected-shortfall formula by truncated-normal integration. EWMA is exactly an IGARCH boundary case (ω=0, α=1-λ, β=λ), not a separate structure. ES remains held pending the VaR-family exclusion ruling.


## Source verification audit 35 (2026-11-11)

[Source Verification Audit 35](CORE295_SOURCE_VERIFICATION_AUDIT_35.md) verifies Bancor CRR purchase/sale returns against Inverter's implementation documentation and identifies a version conflict: an accessible 2017 v0.77 whitepaper draft prints a sale expression inconsistent with the CRR reserve-outflow invariant, while the implementation docs give the invariant-consistent formula. The registered v0.99 paper page remains to be checked. Keep the bonding curve as one power-law reserve-backed issuance family; hold pending source-version reconciliation and whether bonding curves belong in DeFi AMM.


## Source verification audit 36 (2026-11-11)

[Source Verification Audit 36](CORE295_SOURCE_VERIFICATION_AUDIT_36.md) corrects the Butler–Volmer historical attribution and coefficient convention: Butler's 1924 work is conceptual lineage, while Erdey–Grúz/Volmer and later work developed the rate relation; under the modern engineer's form, transfer coefficients are not multiplied by total electron number n. It also distinguishes Nernst–Planck mobility form from the diffusivity form, which assumes the Nernst–Einstein relation. Discovery batch 30 was corrected; both remain discovery-only.


## Source verification audit 37 (2026-11-11)

[Source Verification Audit 37](CORE295_SOURCE_VERIFICATION_AUDIT_37.md) verifies Curve CryptoSwap's dynamic-peg invariant against the 2021 whitepaper and a pinned Tricrypto implementation commit. Its state-dependent (K(K_0,A,\gamma)) modifies StableSwap's implicit invariant and concentrates liquidity around an adaptive price scale. Treat it as a distinct invariant within the broader amplified/stable-swap family; do not count K0, K, D, Newton solvers, spot prices, swap functions, price_scale EMA or repegging as separate equations. Hold pending static-vs-dynamic adapter scope.


## Discovery batch 38 (2026-11-11)

[Candidate Discovery Batch 38](CORE295_CANDIDATE_DISCOVERY_BATCH_38.md) adds Curve LLAMMA's multi-band soft-liquidation/de-liquidation mechanism as a protocol-risk lead. Its per-band invariant is virtual constant product and therefore related to Gyro/Maverick/Uniswap v3; the potentially distinct unit is the complete oracle-driven lending/liquidation state machine, only if DeFi Risk admits system-level models.


## Source verification audit 38 (2026-11-11)

[Source Verification Audit 38](CORE295_SOURCE_VERIFICATION_AUDIT_38.md) verifies the E-CLP ellipse invariant from the November 2022 mathematical specification and a pinned Gyro implementation commit. The invariant is an affine-shifted, stretched and rotated ellipse, structurally distinct from Gyro 2-CLP virtual constant product, weighted geometric, StableSwap/CryptoSwap, PMM and linear/bin pools. Hold pending a two-token parameter/range generator and static-invariant vs full-pool adapter choice.


## Source verification audit 39 (2026-11-11)

[Source Verification Audit 39](CORE295_SOURCE_VERIFICATION_AUDIT_39.md) verifies Gyro 2-CLP's quadratic invariant against a pinned balancer-maths commit and shows it is constant product in virtual reserves. Group it with Uniswap v3, Maverick tick and LLAMMA per-band virtual-CP structures, not as a new equation; retain Gyro E-CLP as the distinct ellipse invariant.


## Structural-equivalence policy decision pending (2026-11-11)

[Structural Equivalence Policy Options](CORE295_STRUCTURAL_EQUIVALENCE_POLICY_OPTIONS.md) compares strict normalized-form, mechanism-aware and hybrid form-and-system rules, with a collision/distinction evidence map across all reviewed candidates. Option C is recommended for consideration but not adopted. No formal catalogue status changes until the rule is selected.


## Source verification audit 40 (2026-11-11)

[Source Verification Audit 40](CORE295_SOURCE_VERIFICATION_AUDIT_40.md) closes Balancer Linear Pool's implementation-version gap by pinning balancer-v2-monorepo commit e91a2b643a49856f51a648d175667c1b48cf3377. It verifies the invariant (I=N_m+B_w^{(m)}), piecewise nominal main-balance fee transform and wrapped-token upscaling in LinearPool.getRate. Remaining blockers are the constant-sum/StableSwap family ruling and frozen target/rate/fee adapter.


## Source verification audit 41 (2026-11-11)

[Source Verification Audit 41](CORE295_SOURCE_VERIFICATION_AUDIT_41.md) verifies LLAMMA whitepaper Eq. (6) and its correspondence to a pinned LlamaLend V2 AMM.vy implementation. The per-band invariant is virtual constant product and stays grouped with Gyro 2-CLP/Uniswap v3/Maverick. The potentially distinct candidate is the full multi-band oracle-driven soft-liquidation/de-liquidation state machine, pending a system-level DeFi Risk policy and adapter.


## Source verification audit 42 (2026-11-11)

[Source Verification Audit 42](CORE295_SOURCE_VERIFICATION_AUDIT_42.md) verifies Solidly's stable-pool quartic invariant (k=XY(X^2+Y^2)=X^3Y+XY^3) against its protocol specification and a pinned Velodrome/Solidly implementation. The implementation normalizes reserves by token decimals before applying the invariant. This is structurally distinct from CP, weighted geometric, StableSwap/CryptoSwap, PMM, E-CLP and linear-sum pools; all Solidly-derived forks remain one family.


## Source verification audit 43 (2026-11-11)

[Source Verification Audit 43](CORE295_SOURCE_VERIFICATION_AUDIT_43.md) classifies Swaap V2 as non-custodial RFQ market-making with off-chain quote optimization and on-chain settlement safeguards, not a new on-chain CFMM invariant. Its max-drawdown, last-look and max-imbalance rules are protocol-specific predicates; consider them only as one version-pinned settlement-policy system if DeFi Risk admits executable safeguards.


## Source verification audit 44 (2026-11-11)

[Source Verification Audit 44](CORE295_SOURCE_VERIFICATION_AUDIT_44.md) verifies Aave V3's weighted collateral/debt health factor against official docs and pinned GenericLogic.sol, including eMode, eligible collateral and debt accrual. It also verifies Compound III's utilization-based piecewise-linear borrow-rate function. Aave/Compound two-slope rate curves are one family; health factor is a distinct collateralization-risk metric, not a liquidation-price equation.


## Source verification audit 45 (2026-11-11)

[Source Verification Audit 45](CORE295_SOURCE_VERIFICATION_AUDIT_45.md) verifies Morpho Blue's capped liquidation incentive factor (LIF=\min(M,1/[1-\gamma(1-LLTV)])) against official docs and a pinned Morpho Blue implementation commit. The factor is one protocol-specific liquidation-incentive function; collateral seizure, debt-share conversion, health factor and bad-debt handling belong to the same liquidation system, not separate equation units.


## Source verification audit 46 (2026-11-11)

[Source Verification Audit 46](CORE295_SOURCE_VERIFICATION_AUDIT_46.md) verifies Euler EVK's capped linear liquidation discount (d(h)=\min(1-h,d_{max})) from the account health ratio and a pinned Liquidation.sol commit. It is a health-shortfall function, not a time-based Dutch auction; it differs structurally from Morpho's reciprocal LLTV/cursor LIF. Keep health, discount, collateral-yield conversion and max-repay logic in one liquidation transition.


## Source verification audit 46 (2026-11-11)

[Source Verification Audit 46](CORE295_SOURCE_VERIFICATION_AUDIT_46.md) verifies Euler EVK's capped linear health-shortfall liquidation discount against official documentation and a pinned implementation commit. The discount is (d(h)=\min(1-h,d_{max})) for (0\le h<1), unlike Morpho Blue's capped reciprocal LIF. Treat health, discount, collateral-yield conversion and repay limits as one liquidation transition.


## Source verification audit 47 (2026-11-11)

[Source Verification Audit 47](CORE295_SOURCE_VERIFICATION_AUDIT_47.md) verifies Liquity's Stability Pool product-sum accounting against a pinned contract snapshot. The coupled P/S recurrences allocate pro-rata collateral gains and debt losses over sequential liquidations, with error feedback and scale transitions. Keep the accumulator as one path-dependent system; confirm the exact Liquity V1 deployment/version before any adapter.


## Source verification audit 48 (2026-11-11)

[Source Verification Audit 48](CORE295_SOURCE_VERIFICATION_AUDIT_48.md) verifies Sky/Maker Liquidations 2.0 against official docs and pinned Dog/Clipper/Abacus sources. The auction supports linear, stair-step exponential and continuous exponential price decay; the stair-step case with step=1 is equivalent to continuous exponential. Treat the price calculator, resets, partial takes, Hole/Dirt capacity and keeper incentives as one versioned Dutch-auction liquidation system.


## Source verification audit 49 (2026-11-11)

[Source Verification Audit 49](CORE295_SOURCE_VERIFICATION_AUDIT_49.md) verifies Compound III's liquidation eligibility inequality, distinct collateral valuation factor used in reserve absorption, and storefront discount/quote function against a pinned Comet implementation. Keep the complete absorb-and-buy lifecycle as one possible protocol system; do not count its eligibility, discount, quote and reserve-update components separately.


## Source verification audit 50 (2026-11-11)

[Source Verification Audit 50](CORE295_SOURCE_VERIFICATION_AUDIT_50.md) screens the OECD 2023 DeFi liquidation/DEX volatility study. It verifies a two-hour realized-volatility measure and log-linear OLS/2SLS specifications, but classifies them as conventional empirical estimators tied to a particular 2020–2022 sample and token pair, not universal protocol equations. Retain as systemic-risk context, not a new equation count.


## Source verification audit 51 (2026-11-11)

[Source Verification Audit 51](CORE295_SOURCE_VERIFICATION_AUDIT_51.md) verifies Qin et al.'s two-successive fixed-spread liquidation optimizer. The closed-form first repayment (r_1=(D-LT\,C)/[1-LT(1+LS)]), second repayment (r_2=CF(D-r_1)), and profit equations form one constrained strategy under fixed-price/fixed-spread assumptions. Retain as an analytical system lead, not as several independent equation entries.


## Source verification audit 52 (2026-11-11)

[Source Verification Audit 52](CORE295_SOURCE_VERIFICATION_AUDIT_52.md) verifies Miqado's reversible-call-option liquidation-mitigation system from IACR ePrint 2023/254 / arXiv:2303.15162v2. The supporter collateral top-up, seller's early termination/reimbursement right, borrower rescue payment and maturity takeover/default form one distinct system lead. The paper's Black–Scholes premium is explicitly an approximation that omits early-termination value.


## Source verification audit 53 (2026-11-11)

[Source Verification Audit 53](CORE295_SOURCE_VERIFICATION_AUDIT_53.md) screens BIS Working Paper 1171. Actual wallet asset-to-equity leverage and LTV-implied maximum leverage are standard balance-sheet identities, not new DeFi equations. The study is empirical context only; it also contains a sample-count inconsistency between the prose and Table 3 and an address-level independence limitation.


## Source verification audit 54 (2026-11-11)

[Source Verification Audit 54](CORE295_SOURCE_VERIFICATION_AUDIT_54.md) classifies the SOA 2022 report as an insurer-oriented DeFi risk taxonomy and incident review, not a mathematical model. Its four principal risk categories and additional social/financial/societal categories inform scope and labels only; incident counts are not equation counts or independent statistical units.


## Source verification audit 55 (2026-11-11)

[Source Verification Audit 55](CORE295_SOURCE_VERIFICATION_AUDIT_55.md) verifies the peer-reviewed FC 2022 paper *Speculative Multipliers on DeFi*. Its most distinctive result is the liquidation-constrained maximum leverage bound (m_{max}=1+1/[\max(LS,Credit(B,C))q_{max}]). The source is registered as RISK-WANG-SPECULATIVE-MULTIPLIERS (candidate_reference); equations remain held, with no proposed/accepted record added.


## Source verification audit 56 (2026-11-11)

[Source Verification Audit 56](CORE295_SOURCE_VERIFICATION_AUDIT_56.md) verifies Aave V4's collateral-risk-sorted debt coverage premium, health-dependent liquidation bonus and target-health repayment sizing against a pinned upstream commit. Keep V3/V4 health factors in one weighted-collateral family; the V4 risk-premium aggregation and dynamic liquidation policy are potentially distinct leads, but all linked calculations remain held as one system pending deployment-specific adapter.


## Source verification audit 57 (2026-11-11)

[Source Verification Audit 57](CORE295_SOURCE_VERIFICATION_AUDIT_57.md) confirms MIP45 is now marked obsolete following MIP102c2-SP1, while remaining the historical primary design spec for the Dog/Clipper/Abacus Dutch-auction architecture. Its intended Hole/Dirt/lot accounting invariants are not formally proven. Audit 48 is cross-linked and clarified: its pinned liq-2.0 source commit does not establish current deployment.


## Source verification audit 58 (2026-11-11)

[Source Verification Audit 58](CORE295_SOURCE_VERIFICATION_AUDIT_58.md) verifies Euler's downward-only, time-ramped liquidation LTV against the pinned LTVConfig implementation. The ramp changes liquidation eligibility over time while borrow LTV remains separate; group it with Euler's health/discount/liquidation system, not as an independent equation sample.


## Source verification audit 59 (2026-11-11)

[Source Verification Audit 59](CORE295_SOURCE_VERIFICATION_AUDIT_59.md) verifies Aave V4's Babylon liquidation path: a caller-supplied maximum collateral amount caps removable shares, and repayment is inversely resized to match that cap. It shares standard V4's health-factor validation, dynamic bonus and debt/share accounting; treat it as a version-specific liquidation sizing variant, not a separate set of equations.


## Source verification audit 60 (2026-11-11)

[Source Verification Audit 60](CORE295_SOURCE_VERIFICATION_AUDIT_60.md) verifies Maker/Sky Jug's per-second stability-fee accumulation from a pinned source commit. The global base plus collateral-specific duty is exponentiated over elapsed seconds with RAY fixed-point rounding. It is a versioned instance of generic exponential compounding, not a distinct equation beside APY conversion or lending-index accrual.


## Source verification audit 61 (2026-11-11)

[Source Verification Audit 61](CORE295_SOURCE_VERIFICATION_AUDIT_61.md) verifies Parkinson's 1980 high–low range variance estimator from the original paper. It is a distinct range-based volatility estimator under driftless continuous Brownian assumptions. Source RISK-PARKINSON-1980 is registered as candidate_reference; the equation remains held pending the DeFi OHLC sampling contract and structural-equivalence policy.


## Source verification audit 62 (2026-11-11)

[Source Verification Audit 62](CORE295_SOURCE_VERIFICATION_AUDIT_62.md) verifies Merton's 1974 structural credit model: levered equity as a call on firm assets, risky debt as the residual claim, and a measure-specific default probability. Source RISK-MERTON-1974 is registered as candidate_reference; the DeFi balance-sheet mapping and physical-vs-risk-neutral probability convention remain unresolved.


## Source verification audit 63 (2026-11-11)

[Source Verification Audit 63](CORE295_SOURCE_VERIFICATION_AUDIT_63.md) verifies Black–Cox's first-passage structural default model with a time-dependent covenant barrier. Source RISK-BLACK-COX-1976 is registered as candidate_reference. Group it with Merton for source-family independence, but preserve the structural distinction between terminal-only default and barrier crossing at any time.


## Source verification audit 64 (2026-11-11)

[Source Verification Audit 64](CORE295_SOURCE_VERIFICATION_AUDIT_64.md) verifies Acerbi–Tasche's coherent expected-shortfall definition and the normal-distribution closed form. Source RISK-ACERBI-TASCHE-2002 is candidate_reference. ES is distinct from VaR, but the Core-15 exclusion's scope must be decided; continuous-loss conditional expectation and quantile-integral definitions are one ES family.


## Source verification audit 65 (2026-11-11)

[Source Verification Audit 65](CORE295_SOURCE_VERIFICATION_AUDIT_65.md) verifies Basel CRE35's (EL=PD\times LGD\) and (EL_{amount}=EL\times EAD). Source RISK-BASEL-CRE35-EL is candidate_reference. This is a standard credit-risk accounting decomposition, not a distinct structural equation; PD, LGD and EAD need their own model/source contracts.


## Source verification audit 66 (2026-11-11)

[Source Verification Audit 66](CORE295_SOURCE_VERIFICATION_AUDIT_66.md) rejects the author-pool ((F-S)/(8S)) expression as a universal funding-rate law. Deribit and Binance use different premium/index definitions, averaging, dampers, caps and interval/payment rules. Retain only as an underspecified basis proxy pending a named protocol and exact version.


## Source verification audit 32 source-register update (2026-11-11)

[Source Verification Audit 32](CORE295_SOURCE_VERIFICATION_AUDIT_32.md) contains Heston's coupled stochastic price/variance process and the Cramér–Lundberg reserve process with exponential-claim ruin probability. Sources RISK-HESTON-1993 and RISK-ASMUSSEN-ALBRECHER-2010 are now registered as candidate_reference; the complete Heston system and the reserve/ruin process each remain one family.


## Source verification audit 34 source-register update (2026-11-11)

[Source Verification Audit 34](CORE295_SOURCE_VERIFICATION_AUDIT_34.md) now has source-register entries for Parkinson (RISK-PARKINSON-1980), Bollerslev GARCH (RISK-BOLLERSLEV-1986) and RiskMetrics EWMA (RISK-RISKMETRICS-1996). GARCH(1,1) and EWMA remain one conditional-variance family because EWMA is the IGARCH boundary case.


## Source verification audit 67 (2026-11-11)

[Source Verification Audit 67](CORE295_SOURCE_VERIFICATION_AUDIT_67.md) confirms Maverick V2's whitepaper tick invariant is virtual constant product, shared with Gyro 2-CLP. The security review identifies a pinned supplemental commit but excludes core pool swap/liquidity files; the repository is not retrievable through the current GitHub access path. Keep the dynamic-bin/TWAP system held pending core implementation verification.


## Source verification audit 68 (2026-11-11)

[Source Verification Audit 68](CORE295_SOURCE_VERIFICATION_AUDIT_68.md) verifies Rogers–Satchell's drift-independent OHLC variance estimator against the 1991 primary paper. It is structurally distinct from Parkinson's zero-drift high–low estimator, but both belong to one range-volatility source family and share price-path/data dependencies. Retain as candidate_reference only; hold pending the discrete-extrema correction, DeFi OHLC sampling contract and statistical-unit policy. No proposed or accepted equation is added.



## Author-pool Physics audit 1 (2026-11-11)

The complete 75-row Physics block from the uploaded `author_pool.py` has now been statically screened in [CORE295_AUTHOR_POOL_PHYSICS_AUDIT_1.md](CORE295_AUTHOR_POOL_PHYSICS_AUDIT_1.md). This is a discovery-pool review only: zero rows promoted. Major clusters include Newtonian gravity/orbits; constant-acceleration/projectile kinematics; circular motion; linear oscillator/circuit responses; Planck/Wien/Stefan/Rayleigh–Jeans; quantum/atomic relations; radioactive decay/activity; fluid drag/terminal balance/Bernoulli special cases; wave optics/acoustics; electromagnetic device relations; and process-specific thermodynamics. Several rows are derived outputs, special cases or limiting forms. All 75 remain unaccepted pending exact-source reconstruction, unit/assumption/range review and global structural-equivalence policy. The uploaded script was not executed.


## Physics source expansion 1 (2026-11-11)

The Physics source register has been expanded from 25 to 43 candidate-reference records (+18), with matching bibliography entries 123–140. The new OpenStax section-level leads cover collisions, rocket propulsion, Kepler orbits, pendulums, forced oscillations, standing waves, Doppler shift, sound intensity, capacitance, RC circuits, Faraday induction, AC resonance, photoelectric effect, Compton scattering, Bohr hydrogen, de Broglie waves, the infinite well and Young double-slit interference. These are traceable discovery references, not 18 new equations and not accepted entries. Exact equation/page review and family screening remain required. Several section URLs were corrected after checking the official OpenStax pages.


## Cross-domain equivalence policy draft (2026-11-11)

[Structural Equivalence Policy Draft 1](CORE295_STRUCTURAL_EQUIVALENCE_POLICY_DRAFT_1.md) proposes a strict E0–E5 review scale. Exact duplicates, algebraic rearrangements, derived/limiting forms and identical normalized structures across different domains do not count as distinct structural equations. Different irreducible governing structures may qualify while retaining shared source-family/dependence labels. The policy is a draft only; no formal catalogue policy has been frozen and no entry has been accepted under it.

## DeFi AMM source expansion 1 (2026-11-11)

[DeFi AMM Source Expansion Audit 1](CORE295_AMM_SOURCE_EXPANSION_AUDIT_1.md) adds three traceable protocol/math references: Trader Joe JOE v2.1 Liquidity Book, YieldSpace, and Invariant concentrated liquidity. The Liquidity Book per-bin equation is a fixed-price constant-sum relation, while its aggregate bin state machine needs a full transition contract before it can be considered. YieldSpace's time-to-maturity-dependent constant power-sum invariant is a stronger candidate family; its constant-sum/product limits are not separate equations. Invariant's range formulas derive from translated constant-product geometry and remain grouped with Uniswap v3. The source register rises from 156 to 159 (DeFi AMM 20 to 23); this is source coverage only, not equation growth or acceptance. The manifest remains draft with 19 proposed and zero accepted.

## Consolidated author-pool audit matrix 1 (2026-11-11)

[CORE295_CONSOLIDATED_AUTHOR_POOL_AUDIT_MATRIX_1.md](CORE295_CONSOLIDATED_AUTHOR_POOL_AUDIT_MATRIX_1.md) consolidates the five static domain screens: 299 raw rows (54 Chemistry, 59 Biology, 75 Physics, 54 DeFi AMM, 57 DeFi Risk), zero accepted from the discovery pool, and 169 source-register records at the latest branch refresh (Chemistry 36, Biology 34, Physics 43, DeFi AMM 23, DeFi Risk 33). It distinguishes source coverage, proposed formal catalogue entries and accepted equations; records cross-domain overlaps, coupled-system/derived-output blockers, Core-15 exclusions and required acceptance gates. The matrix is an index and synthesis, not a new validation pass; no code or experiments were run.

## Biology stock–recruitment family source audit 1 (2026-11-11)

[Biology Stock–Recruitment Family Audit 1](CORE295_BIO_STOCK_RECRUITMENT_FAMILY_AUDIT_1.md) adds primary lineage records for Beverton–Holt (1957), Ricker (1954), Deriso (1980) and Schnute (1985). Secondary equation-level literature reports Ricker as the \(\gamma\to0\) limit and Beverton–Holt at \(\gamma=-1\) of the generalized Deriso–Schnute form. Count these as one E2 family under the draft policy; the exact generalized equation/page still requires direct primary-paper transcription. The full delay-difference/age-structured model is a separate complete-system unit and must not be split into components. Biology sources rise from 30 to 34; no equation is proposed or accepted by this source audit.

## Chemistry and DeFi Risk protocol/source audits (2026-11-11)

- [Chemistry Adsorption and Marcus Audit 1](CORE295_CHEM_ADSORPTION_AND_MARCUS_AUDIT_1.md): Frumkin adsorption is a nonideal-interaction lead; Langmuir is its (a=0) limit and must not be counted separately under E2. Marcus rate reconstruction requires the quadratic reorganization-energy barrier and a scope-matched prefactor: solution collision-number convention in the 1956 solution-rate treatment versus IUPAC's Eyring/transmission form for encounter-complex/intramolecular kinetics. The pool's generic Z is underspecified, not automatically invalid.
- [DeFi Risk Protocol Models Audit 1](CORE295_DEFI_RISK_PROTOCOL_MODELS_AUDIT_1.md): Aave V3 health factor and Compound Comet negative-liquidity threshold are related weighted-collateral/debt eligibility tests, not separate scalar families. Comet borrow/supply rates are kinked piecewise-linear/utilization-derived; same normalized structure as other lending kink-rate models. The absorb state machine may be a protocol-level model only after exact version pin and full state-transition reconstruction.
- Source register adds three references (Frumkin 1920, Compound Comet specification, Aave V3 health-factor developer documentation); total 166. No formal equation entry was added or accepted.



## Biology source-family additions (2026-11-11)

The source register now includes Kermack–McKendrick (1927) epidemic flow, Leslie (1945) age-structured matrix, Michaelis–Menten (1913) invertase kinetics, Holling (1959) functional response, Volterra (1926) predator–prey and Monod (1949) bacterial culture growth review. These are source leads, not accepted equations. Preserve complete coupled-system units for epidemic, predator–prey and Leslie matrix models. Do not count Monod, Holling Type II and Michaelis–Menten scalar saturation laws separately solely by naming/mechanism; the draft E3 rule blocks normalized-structure variants. Holling Type III remains a distinctness lead pending exact primary transcription. See [Biology and DeFi AMM primary-source audit 1](CORE295_BIO_AMM_PRIMARY_SOURCE_AUDIT_1.md).
