# Core-295 candidate screening queue

**Status:** prioritized source-evidence queue, not an equation catalogue. Tier A means the equation or implementation formula is directly visible in an accessible primary/official source and can move to proposed-record drafting after a technical review. It does **not** mean scientifically accepted. Tier B means the formula is visible but exact primary-source mapping, assumptions, units or implementation details remain incomplete. Tier C means a source lead or domain-boundary issue remains.

**Current manifest:** 128 candidate source records; 122 bibliography items; 24 discovery batches; 19 proposed equation records; zero accepted equation entries. See [proposed-record audit 1](CORE295_PROPOSED_RECORD_AUDIT_1.md) for primary-source attribution and formula-representation corrections, [audit 2](CORE295_PROPOSED_RECORD_AUDIT_2.md) for Marcus/Fick blockers, and [audit 3](CORE295_PROPOSED_RECORD_AUDIT_3.md) for Hill's primary-source verification, unit convention and Michaelis–Menten structural-overlap blockers; [audit 4](CORE295_PROPOSED_RECORD_AUDIT_4.md) distinguishes the modern Hagen–Poiseuille expression from Poiseuille's original empirical law and records its Navier–Stokes derivation-family question; [audit 5](CORE295_PROPOSED_RECORD_AUDIT_5.md) fixes the Planck spectral-exitance observable and its conversion from the 1901 spectral-energy-density equation.

**Proposed-record review pass 1:** `CHEM-HENRY-001`, `CHEM-LANGMUIR-001`, and `CHEM-MARCUS-001`. Pass 2 adds `BIO-HILL-MUSCLE-001`; pass 3 adds `PHYS-POISEUILLE-001`; pass 4 adds `PHYS-PLANCK-SPECTRUM-001`; pass 5 adds `PHYS-THIN-LENS-001`; pass 6 adds `AMM-BALANCER-WEIGHTED-001`; pass 7 adds `RISK-MORPHO-LIF-001`; pass 8 adds `RISK-EULER-AUCTION-001`; pass 9 adds `RISK-COMPOUND-BORROW-KINK-001`; pass 10 adds `AMM-DODO-PMM-BASE-SHORTAGE-001`; pass 11 adds `CHEM-RAOULT-VAPOR-001`; pass 12 adds `BIO-FICK-CARDIAC-OUTPUT-001`; pass 13 adds `RISK-UNISWAP-V3-GEOMETRIC-TWAP-001`; pass 14 adds `RISK-UNISWAP-V2-ARITHMETIC-TWAP-001`; pass 15 adds `CHEM-FICK-FLUX-001`; pass 16 adds `CHEM-BEER-LAMBERT-001`; pass 17 adds `BIO-TUMOR-TURNOVER-001`. All have stable IDs, source-family IDs, normalized symbolic fingerprints and stated assumptions. Their train/extrapolation ranges and generator contracts remain deliberately unset; Marcus also requires explicit overlap review against Core-15 exclusions; its rate prefactor and LaTeX transcription were corrected in the manifest after primary-source review. See proposed-record reviews [1](CORE295_PROPOSED_RECORD_REVIEW_1.md), [2](CORE295_PROPOSED_RECORD_REVIEW_2.md), [3](CORE295_PROPOSED_RECORD_REVIEW_3.md), [4](CORE295_PROPOSED_RECORD_REVIEW_4.md), [5](CORE295_PROPOSED_RECORD_REVIEW_5.md), [6](CORE295_PROPOSED_RECORD_REVIEW_6.md), [7](CORE295_PROPOSED_RECORD_REVIEW_7.md) and [8](CORE295_PROPOSED_RECORD_REVIEW_8.md), [9](CORE295_PROPOSED_RECORD_REVIEW_9.md) and [10](CORE295_PROPOSED_RECORD_REVIEW_10.md), [11](CORE295_PROPOSED_RECORD_REVIEW_11.md), [12](CORE295_PROPOSED_RECORD_REVIEW_12.md), [13](CORE295_PROPOSED_RECORD_REVIEW_13.md), [14](CORE295_PROPOSED_RECORD_REVIEW_14.md) and [15](CORE295_PROPOSED_RECORD_REVIEW_15.md) and [16](CORE295_PROPOSED_RECORD_REVIEW_16.md) and [17](CORE295_PROPOSED_RECORD_REVIEW_17.md). The source counts are not equation counts.

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
