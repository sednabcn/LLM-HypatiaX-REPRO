# Core-295 candidate screening queue

**Status:** prioritized source-evidence queue, not an equation catalogue. Tier A means the equation or implementation formula is directly visible in an accessible primary/official source and can move to proposed-record drafting after a technical review. It does **not** mean scientifically accepted. Tier B means the formula is visible but exact primary-source mapping, assumptions, units or implementation details remain incomplete. Tier C means a source lead or domain-boundary issue remains.

**Current manifest:** 127 candidate source records; 121 bibliography items; 23 discovery batches; 13 proposed equation records; zero accepted equation entries.

**Proposed-record review pass 1:** `CHEM-HENRY-001`, `CHEM-LANGMUIR-001`, and `CHEM-MARCUS-001`. Pass 2 adds `BIO-HILL-MUSCLE-001`; pass 3 adds `PHYS-POISEUILLE-001`; pass 4 adds `PHYS-PLANCK-SPECTRUM-001`; pass 5 adds `PHYS-THIN-LENS-001`; pass 6 adds `AMM-BALANCER-WEIGHTED-001`; pass 7 adds `RISK-MORPHO-LIF-001`; pass 8 adds `RISK-EULER-AUCTION-001`; pass 9 adds `RISK-COMPOUND-BORROW-KINK-001`; pass 10 adds `AMM-DODO-PMM-BASE-SHORTAGE-001`; pass 11 adds `CHEM-RAOULT-VAPOR-001`. All have stable IDs, source-family IDs, normalized symbolic fingerprints and stated assumptions. Their train/extrapolation ranges and generator contracts remain deliberately unset; Marcus also requires explicit overlap review against Core-15 exclusions. See proposed-record reviews [1](CORE295_PROPOSED_RECORD_REVIEW_1.md), [2](CORE295_PROPOSED_RECORD_REVIEW_2.md), [3](CORE295_PROPOSED_RECORD_REVIEW_3.md), [4](CORE295_PROPOSED_RECORD_REVIEW_4.md), [5](CORE295_PROPOSED_RECORD_REVIEW_5.md), [6](CORE295_PROPOSED_RECORD_REVIEW_6.md), [7](CORE295_PROPOSED_RECORD_REVIEW_7.md) and [8](CORE295_PROPOSED_RECORD_REVIEW_8.md), [9](CORE295_PROPOSED_RECORD_REVIEW_9.md) and [10](CORE295_PROPOSED_RECORD_REVIEW_10.md). The source counts are not equation counts.

## Tier A — eligible for proposed-record drafting after technical review

| Domain | Source IDs | Candidate structure | Remaining checks before proposed record |
|---|---|---|---|
| Chemistry | CHEM-OPENSTAX-HENRY-11-3 | Henry gas-solubility relation | Fix Henry constant convention/units, dilute regime, temperature and gas/solvent assumptions. |
| Chemistry | CHEM-IUPAC-MARCUS; CHEM-MARCUS-1956 | Marcus outer-sphere electron-transfer barrier/rate | Confirm primary-paper equation and classical high-temperature/nonadiabatic regime; explicitly separate from Arrhenius exclusion. |
| Chemistry | CHEM-LH-WACHS-2024; CHEM-LANGMUIR-1918 | Competitive-adsorption Langmuir–Hinshelwood rate | Confirm surface-site balance, rate-determining step, adsorption equilibria and primary historical lineage. |
| Biology | BIO-TUMOR-DBUCK-2014 | Concentration-modulated tumor turnover, primary Eq. 9 | Freeze tumor state as sum of longest diameters, concentration input, units and valid clinical range. |
| Biology | BIO-HH-1952; BIO-HH-MODERN-2019 | Hodgkin–Huxley coupled membrane/gating ODE system | Freeze original/modern current sign convention, temperature scaling, gate-rate functions and full four-state system. |
| Biology | BIO-MICHAELIS-MENTEN-1913 | **Excluded** | Michaelis–Menten is explicitly in the Core-15 exclusion list; retain the bibliography lead for provenance only, never draft it as a Core-295 candidate. |

| Biology | BIO-MORRIS-LECAR-1981 | Two-variable conductance-based excitable-cell model | Confirm original equations 1–2, ionic-current conventions, quasi-steady activation and parameter units. |
| Physics | PHYS-PLANCK-1901; PHYS-OPENSTAX-V3-PLANCK | Planck blackbody spectral distribution | Freeze spectral energy density versus exitance/radiance convention and SI conversion; cluster Stefan/Wien consequences. |
| Physics | PHYS-OPENSTAX-V3-THIN-LENS | Thin-lens equation | Confirm sign convention, refractive index assumptions and thin-lens regime. |
| Physics | PHYS-OPENSTAX-V3-SCHRODINGER | Time-dependent Schrödinger equation | Define one-dimensional or higher-dimensional state, potential, initial/boundary conditions and output observable. |
| Physics | PHYS-OPENSTAX-V1-FLUID | Poiseuille laminar pipe-flow relation | Specify Newtonian fluid, fully developed laminar flow, cylindrical geometry, no-slip and pressure-drop convention. |
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

The Hill muscle force–velocity relation is drafted as `BIO-HILL-MUSCLE-001` but remains in Tier B until the original 1938 equation page and notation are checked; its benchmark ranges and muscle context are also pending.

| Domain | Source IDs | Candidate structure | Main blocker |
|---|---|---|---|
| Chemistry | CHEM-BEER-1852 | Beer absorption / modern Beer–Lambert relation | Original Beer notation and modern decadic molar-absorptivity convention need exact mapping. |
| Chemistry | CHEM-ERDEY-GRUZ-VOLMER-1930; CHEM-BUTLER-1924 | Butler–Volmer electrode kinetics | Historical attribution and generalized modern form need primary-source synthesis; Tafel is an asymptote, Nernst is equilibrium. |
| Chemistry | CHEM-RAOULT-1887; CHEM-RAOULT-FREEZING-1882 | Ideal-solution vapor pressure and freezing-point depression | Modern formula forms are accessible, but exact original equation notation/concentration basis remains to verify. |
| Chemistry | CHEM-FICK-1855; CHEM-LANGMUIR-1918 | Diffusion and adsorption | Fick original equation and diffusion-PDE assumptions still need page-level transcription; Langmuir Eq. 8/9 is now located in the 1918 primary paper. |
| Chemistry | CHEM-RIDEAL-1939; CHEM-ELEY-RIDEAL-1940; CHEM-ER-ENG-REACTION; CHEM-IUPAC-LANGMUIR-RIDEAL | Rideal–Eley gas/adsorbed surface-reaction rate | Mechanism is primary-sourced; explicit engineering rate form is secondary. Verify the rate-law assumptions and catalyst-specific pathway before proposed-record drafting. |
| Biology | BIO-SIMEONI-2004; BIO-TUMOR-ODE-COMPARISON-2020 | Exponential-to-linear tumor growth and transit-compartment TGI | Exact growth formula currently transcribed from secondary comparison; original primary equation/page remains outstanding. |
| Biology | BIO-HILL-1910; BIO-ADAIR-1925 | Hemoglobin oxygen-binding models | Hill/Adair formula transcription needs original-paper page verification; keep common hemoglobin source cluster. |
| Biology | BIO-HILL-MUSCLE-1938 | Hill muscle force–velocity relation | Confirm exact equation page and original notation; specify muscle preparation, steady isotonic/tetanic conditions, sign convention, and valid force–velocity range. The record is drafted but remains proposed pending primary-page verification. |
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
