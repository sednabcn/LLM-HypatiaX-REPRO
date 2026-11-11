# Core-295 provisional source-family cluster map

**Status:** review aid only, not an accepted equation catalogue. Cluster labels below are provisional grouping identifiers for equivalence review and statistical sampling. They do not imply that every source in a cluster contributes a structurally distinct equation.

**Current discovery snapshot:** 128 candidate source records; 122 bibliography items; 24 discovery batches; 19 proposed equation records; zero accepted equation entries. Option 2 remains 295 accepted structurally distinct equations, 59 per domain. A source record, paper, protocol or formula variant is not itself an equation count.

## How to use the clusters

1. Assign each proposed equation a provisional source-family identifier before considering it for acceptance.
2. Compare normalized mathematical structure, not names, variables, units, protocol branding or algebraic rearrangements.
3. Keep a derivation parent where a formula is a special case, solution, asymptote, integral, derivative or numerical solver for another equation.
4. Keep statistical-unit identifier separate from source-family identifier. Two equations can be structurally different yet share the same source, protocol, data generator or dependence mechanism.
5. Mark candidate, overlap, excluded or unresolved. Do not pad a domain to 59 by splitting one family into cosmetic variants.
6. For coupled systems, PDEs, integral equations and state machines, preserve the whole model or document a justified deterministic adapter; a single output projection does not make the underlying system a scalar equation.

## Chemistry

| Provisional family ID | Source leads / related structures | Initial screen |
|---|---|---|
| CHEM-MASS-ACTION | Guldberg–Waage; equilibrium constants; Ksp, Kf, Kd; complexation; polyprotic acid speciation | One broad mass-action lineage. Ksp, formation/dissociation constants and species-balance expressions must not be counted separately without structural proof. |
| CHEM-THERMO-EQUILIBRIUM | Gibbs free energy relations; van’t Hoff temperature dependence; equilibrium thermodynamics | Keep state-function identities and rearrangements together. Distinguish temperature dependence of equilibrium from excluded Arrhenius rate dependence. |
| CHEM-ELECTROCHEM-EQUILIBRIUM | Nernst relation; ΔG°/E°/K links | Equilibrium potential is distinct from electrode kinetics, but ΔG/E°/K conversions are one thermodynamic identity family. |
| CHEM-GAS-SOLUBILITY | Henry’s law | Gas partial pressure versus dissolved concentration; preserve dilute regime and Henry-constant convention. |
| CHEM-IDEAL-SOLUTION-VAPOR | Raoult’s law | Liquid mole fraction versus partial vapor pressure; distinct from Henry’s law but ideal-solution regime only. |
| CHEM-COLLIGATIVE | Freezing-point depression, boiling-point elevation, osmotic pressure | Related colligative consequences; do not count solvent-specific constants or rearrangements independently. Osmotic pressure requires an explicit overlap check against excluded Ideal Gas Law structure. |
| CHEM-ADSORPTION-SURFACE | Langmuir adsorption; Langmuir–Hinshelwood and Rideal–Eley surface reactions | Langmuir–Hinshelwood (two adsorbed reactants) and Rideal–Eley (one gas-phase plus one adsorbed reactant) are distinct mechanisms with different site-balance denominators; cluster within heterogeneous surface catalysis. Langmuir coverage and rate laws remain linked. |
| CHEM-DIFFUSION | Fick flux law and diffusion equation | Flux law and PDE are linked levels of one transport family unless a predeclared model split justifies otherwise. The scalar Fick flux form shares the same normalized first-order linear-gradient constitutive structure as Fourier heat flux and Ohm current density; treat CHEM-FICK-FLUX-001 as a high-priority cross-domain equivalence blocker, not an independently countable equation pending an explicit policy decision. See [proposed-record audit 2](CORE295_PROPOSED_RECORD_AUDIT_2.md). |
| CHEM-OPTICAL-ABSORPTION | Beer absorption / Beer–Lambert notation | Decadic absorbance, natural-log attenuation and transmittance forms are equivalent representations. |
| CHEM-ELECTRODE-KINETICS | Butler/Erdey-Grúz–Volmer; Butler–Volmer; Tafel asymptotes | Kinetic current–overpotential law is distinct from Nernst equilibrium. Tafel forms are asymptotic regimes, not independent families. |
| CHEM-ELECTRON-TRANSFER | Marcus outer-sphere electron-transfer rate and electrochemical extension | Quadratic reorganization-energy barrier is distinct from Butler–Volmer's transfer-coefficient current law and Nernst equilibrium, but Marcus rate forms and activation-barrier forms are linked. Explicitly screen against the Arrhenius exclusion. |

## Biology

| Provisional family ID | Source leads / related structures | Initial screen |
|---|---|---|
| BIO-POPULATION-INTERACTION | Lotka 1920 plant–herbivore system; Lotka 1925 book | Preserve original variable-coefficient and transformed forms. The 1920 paper and 1925 book are one lineage unless a distinct structure is proven. Core-15 Logistic Growth remains excluded. |
| BIO-EPIDEMIC-AGE | Kermack–McKendrick 1927 infection-age integral system; later SIR reductions | Original age-structured integral model is not interchangeable with a constant-rate SIR ODE. Reductions and alternate notation share a source lineage. |
| BIO-MORPHOGENESIS | Turing 1952 discrete cell-ring and continuous-tissue reaction–diffusion descriptions | Discrete and continuum representations are related forms of one source family; specify geometry and boundary conditions. |
| BIO-TUMOR-PKPD | De Buck 2014 exact Eq. 9 concentration-modulated tumor turnover; Simeoni 2004 exponential-to-linear growth and transit compartments; Gompertz and other tumor curves | De Buck's Emax*C/(C+IC50) term embeds a hyperbolic saturation structure and must be reviewed against the Core-15 Michaelis–Menten exclusion. Distinguish state variable (diameter, volume, mass), PK input and transit dynamics. Logistic remains excluded. Alternative parameterizations and compartments are not automatically separate equations. |
| BIO-SATURATION-KINETICS | Michaelis–Menten; Monod | Same hyperbolic saturation structure; different context and units do not create structural novelty. |
| BIO-HEME-LIGAND-BINDING | Hill 1910 oxygen-binding curve; Adair 1925 four-step binding polynomial | Hill empirical curve and Adair binding polynomial have distinct structures but share the hemoglobin oxygen-binding source cluster. |
| BIO-CARDIAC-OUTPUT | Fick principle | Oxygen mass-balance measurement; distinguish oxygen content from partial pressure and preserve steady-state assumptions. |
| BIO-ARTERIAL-HEMODYNAMICS | Frank two-element Windkessel; later three-element extensions | RC pressure decay and lumped ODE are one model. Characteristic impedance extension is a related model extension. |
| BIO-MUSCLE-MECHANICS | Hill 1938 force–velocity relation | Hyperbolic force–velocity, power curve and linearized forms are linked. Distinguish from Hill ligand-binding equation. |
| BIO-EXCITABLE-CELL | Hodgkin–Huxley; FitzHugh BVP/FHN reduction; Morris–Lecar | Distinct state dimensions/mechanisms but one broad excitable-cell source cluster. HH current and gate equations are coupled parts of one system. |

## Physics

| Provisional family ID | Source leads / related structures | Initial screen |
|---|---|---|
| PHYS-MAXWELL-FIELD | Gauss electric/magnetic, Faraday, Ampère–Maxwell laws | Four laws form one coupled field system. Source-free wave equation and Poynting relations are derived consequences. |
| PHYS-GEOMETRIC-OPTICS | Snell; thin lens; lens-maker | Thin-lens and lens-maker equations share a derivation lineage. Air special cases and sign-convention changes are not new families. |
| PHYS-WAVE-OPTICS | Double-slit interference; diffraction grating; single-slit envelope | Double-slit and grating maxima share a path-difference condition; finite aperture envelope is coupled to the interference pattern. |
| PHYS-QUANTUM-SCATTERING | Photon energy/momentum; Compton shift | Compton shift is one collision derivation using conservation laws and photon relations; do not count each conservation identity again. |
| PHYS-SCHRODINGER-EIGENPROBLEM | Time-dependent Schrödinger PDE; time-independent separation; free particle; quantum harmonic oscillator | PDE, eigenvalue problem, solutions and spectra are linked levels of one operator framework. |
| PHYS-FLUID-MECHANICS | Continuity; Bernoulli; Poiseuille; Navier–Stokes | Poiseuille is a special Navier–Stokes solution; Bernoulli is an inviscid energy integral. Keep assumptions and parent derivations explicit. |
| PHYS-THERMAL-TRANSPORT | Fourier conduction; Stefan–Boltzmann law; Planck spectrum; Wien displacement | Planck spectrum yields Wien and Stefan relations; slab conduction is a geometry reduction of Fourier flux law. |
| PHYS-OSCILLATORY-DYNAMICS | Damped harmonic oscillator ODE and solutions | ODE, under/critical/overdamped solutions and frequencies are one source family. |
| PHYS-STRUCTURAL-ELASTICITY | Euler elastica; Euler column buckling; Timoshenko beam dynamics | Buckling is a stability/eigenvalue result from elastic-column mechanics; Timoshenko adds shear deformation and rotary inertia to slender-beam theory. Cluster the models but preserve their different kinematics and validity regimes. |

## DeFi AMM

| Provisional family ID | Source leads / related structures | Initial screen |
|---|---|---|
| AMM-CONSTANT-PRODUCT | Uniswap v2; Uniswap v3 virtual reserves; volatile Solidly pools | Core-15 constant-product exclusion applies. Uniswap v3 local virtual reserves and range restrictions do not create a new invariant. |
| AMM-WEIGHTED-GEOMETRIC | Balancer weighted pools | Non-equal weights or multi-asset structure may be structurally distinct. Spot prices, swap formulas and equal-weight two-token special cases remain linked to the invariant. |
| AMM-CURVE-STABLE | Curve StableSwap; Solidly stable polynomial | Distinct invariant structures: amplified sum/product blend versus polynomial stable curve. Related stable-asset AMM source cluster, but do not merge mathematically distinct invariants. |
| AMM-CURVE-CRYPTOSWAP | Curve CryptoSwap dynamic-peg invariant | Separate invariant from StableSwap; cluster protocol lineage and state-dependent coefficient/price-scale mechanism. |
| AMM-DODO-PMM | DODO Proactive Market Maker | Inventory-deviation marginal price, integrated trade amount, average price and quadratic solve are one PMM curve family. |
| AMM-DISCRETE-BINS | LFJ Liquidity Book; Maverick dynamic distribution; Carbon adjustable orders | Fixed-price bins, geometric bin progression and dynamic bin movement are related discrete-liquidity mechanisms. Carbon curve formula and Maverick state transitions still require code-level tracing. |
| AMM-GYRO-CONCENTRATED | Gyro 2-CLP quadratic invariant; Gyro E-CLP ellipse | Distinct quadratic and elliptic invariants, but shared Gyroscope/Balancer lineage; do not assume independent samples. |
| AMM-CRR-BONDING | Bancor constant-reserve-ratio bonding curve | Purchase, sale and marginal-price expressions are one curve. Include only if the DeFi AMM domain explicitly includes reserve-backed continuous-token issuance. |
| AMM-RFQ-MARKET-MAKING | Swaap v2 | Stochastic markup optimization and on-chain settlement safeguards form one RfQ architecture, not a conventional invariant pool. Include only if the domain definition includes off-chain RfQ systems. |


**Additional screening from the supplied `author_pool.py`:** the pool's 54 AMM rows are discovery leads only; none is accepted. Cluster `swap_out_with_fee`, `spot_price`, `post_trade_price`, `effective_price`, LP minting, arbitrage/rebalance, impermanent-loss and depth metrics under the constant-product family, subject to the frozen Core-15 exclusions. Cluster Balancer `outGivenIn`, `inGivenOut` and spot price as derived relations of one weighted invariant. Cluster Uniswap V3 token amounts, liquidity inversion, position value, virtual reserves, range-order fill, capital efficiency and tick/price transforms as one concentrated-liquidity family. The supplied `three_asset_invariant_price` is not the documented general weighted-pool spot-price equation; `curve_amplified_depth` and `stable_price_impact` are not the documented StableSwap invariant/derivation. Bancor buy/sell/spot are one connector-weight curve. Generic TWAP, LVR, MEV, bonding-curve, fee and reward sketches require exact source/model contracts. See [author-pool DeFi audit 1](CORE295_AUTHOR_POOL_DEFI_AUDIT_1.md).

## DeFi Risk

| Provisional family ID | Source leads / related structures | Initial screen |
|---|---|---|
| RISK-COLLATERAL-HEALTH | Aave HF; Morpho LLTV; Euler health ratio; Liquity ICR; Compound collateral factors | Related collateral-capacity/debt ratios. Do not count protocol naming, weighted-average thresholds or rearrangements separately. |
| RISK-UTILIZATION-RATES | Compound III kink; Aave V3 two-slope rate model | Piecewise-affine utilization curves are structurally related across protocols; borrow/supply rates are linked outputs. |
| RISK-LIQUIDATION-INCENTIVES | Compound discount; Morpho LIF; Euler health-dependent discount | Distinct incentive mechanisms, but one liquidation-incentive source cluster. Pin exact implementation and parameter conventions. |
| RISK-LIQUIDATION-AUCTIONS | Maker/Sky Abacus linear/exponential decay; Liquity liquidation branches | Price-time schedules and debt/collateral redistribution are distinct mechanisms within liquidation risk. Historical MIP45 is obsolete. |
| RISK-LOSS-ABSORPTION | Liquity Stability Pool | Stateful debt offset, collateral gain and product/scale/epoch accounting. A scalar pro-rata summary is not the full model. |
| RISK-ORACLE-TWAP | Uniswap v2 arithmetic cumulative-price TWAP; Uniswap v3 geometric tick TWAP and harmonic mean liquidity | Distinct averaging constructions, but all belong to the oracle manipulation-resistance cluster. Spot price, cumulative accumulator and derived mean are not independent equations. |
| RISK-ORACLE-FRESHNESS | Chainlink heartbeat/deviation update triggers; consumer updatedAt/maxAge checks | Provider update policy and consumer freshness guard are separate layers. Feed-specific parameters are not universal constants. |


**Additional screening from the supplied `author_pool.py`:** the pool's 57 Risk rows are discovery leads only; none is accepted. All supplied VaR variants remain in the Core-15 Value at Risk exclusion family; liquidation-price heuristics remain in the Core-15 Liquidation Price family. Correlation extrapolation to 4 is invalid, covariance/portfolio-weight constraints are missing, and the quartic borrow-rate expression is not Compound III's documented piecewise-linear kink model. Group EWMA/GARCH, portfolio/covariance measures, health-factor rearrangements, utilization/rate/index accrual, APR/APY compounding and Merton/credit-spread measures by their underlying models. Generic funding, liquidation, bridge, oracle, MEV and governance-risk sketches require protocol/venue-specific reconstruction. See [author-pool DeFi audit 1](CORE295_AUTHOR_POOL_DEFI_AUDIT_1.md).

## Open structural questions before acceptance

1. **Domain boundary:** decide whether the DeFi AMM domain includes reserve-backed continuous-token bonding curves (Bancor), RfQ market making (Swaap), and algorithmic order curves (Carbon/Maverick). If excluded, retain as source-universe context but do not count them toward 59.
2. **Vector/PDE/system adapters:** decide whether the benchmark accepts coupled ODEs, integral equations, PDEs, vector fields and state machines directly, or only after a deterministic scalar-output adapter. Do not flatten without preserving the model.
3. **Source-family versus independent unit:** predeclare the sampling unit (equation structure, primary source, model family, protocol family or benchmark generator). Structural distinction alone does not prove statistical independence.
4. **Core-15 exclusions:** maintain an explicit exclusion registry for logistic growth, kinetic energy, gravitational force, ideal gas, Henderson–Hasselbalch, Arrhenius, constant product and any other frozen Core-15 equations.
5. **Equivalence review:** normalize symbols/units, compare algebraic forms, identify special cases, and trace derivative/integral/solution relationships before assigning unique equation fingerprints.

**No entries are accepted by this map.** It is a curation aid for the next candidate-screening stage; all final acceptance remains subject to the catalogue validator, exact source transcription, domain review, provenance and independence metadata.


## Author-pool screening audit 2 (2026-11-11)

The Chemistry, Biology and Physics portions of the assistant-authored 299-row discovery pool have been screened (188 rows). The detailed candidate disposition register and cross-domain family blockers are in [Author Pool Screening Audit 2](CORE295_AUTHOR_POOL_SCREENING_AUDIT_2.md). In particular, the review flags Michaelis–Menten/Hill saturation and population-growth families in Biology, kinematic/mechanical and circuit response families in Physics, and linear-gradient transport overlap across Chemistry/Physics/Biology. This map remains provisional; no candidate is accepted by the audit.


## Source verification audit 3 (2026-11-11)

[Source Verification Audit 3](CORE295_SOURCE_VERIFICATION_AUDIT_3.md) records equation-level source checks for L–H versus E–R surface kinetics, Adair versus Hill hemoglobin binding, Kermack–McKendrick age-structured epidemic dynamics versus its SIR reduction, Turing reaction–diffusion systems, and Euler column stability. These findings reinforce that source-family membership and structural equivalence are separate decisions. Coupled ODE/PDE/integral models must be treated as whole systems; alternate representations, components and special-case reductions are not extra entries. No candidates were accepted.


## Source verification audit 4 (2026-11-11)

[Source Verification Audit 4](CORE295_SOURCE_VERIFICATION_AUDIT_4.md) adds equation-level checks for Frank's Windkessel model and FitzHugh's 1961 BVP system. Keep the Windkessel two-element RC equation, its zero-inflow decay and frequency-domain impedance in one derivation family; keep FitzHugh's two coupled ODEs as one system-level unit and distinguish the original BVP form from later FHN parameterizations. Both are held, not accepted; source-family membership does not establish independent statistical units.


## Source verification audit 5 (2026-11-11)

[Source Verification Audit 5](CORE295_SOURCE_VERIFICATION_AUDIT_5.md) records Fick's oxygen mass-balance cardiac-output relation as a measurement equation, with primary-page transcription and domain-scope questions still open. It also records the Timoshenko 1921 shear-correction source as metadata-verified but not equation-transcribed; Bresse antecedents and later Timoshenko formulations must not be conflated. Neither lead is accepted.


## Source verification audit 6 (2026-11-11)

[Source Verification Audit 6](CORE295_SOURCE_VERIFICATION_AUDIT_6.md) verifies LFJ Liquidity Book's per-bin constant-sum relation, geometric bin-price grid and multi-bin swap traversal against the whitepaper and a pinned implementation snapshot. Treat the complete multi-bin state-transition model as one family, not a separate equation per bin, direction, fee or accumulator. It is structurally distinct from the Core-15 constant-product exclusion but remains held pending model-scope and implementation-contract decisions.


## Source verification audit 7 (2026-11-11)

[Source Verification Audit 7](CORE295_SOURCE_VERIFICATION_AUDIT_7.md) separates Chainlink's feed-specific heartbeat/deviation update triggers from consumer-defined updatedAt/maxAge freshness guards. Treat these as protocol operations and application safety predicates, not distinct universal equations. Keep the source as context; defer equation eligibility until the DeFi Risk domain contract explicitly includes version-pinned safety predicates.


## Source verification audit 8 (2026-11-11)

[Source Verification Audit 8](CORE295_SOURCE_VERIFICATION_AUDIT_8.md) adds DODO PMM as a strong, structurally distinct inventory-dependent AMM family: a piecewise guide-price-centered marginal curve, its integrated finite-trade amount and the R-state transition. Keep the whole piecewise state-transition model as one candidate family. It is distinct from constant-product, weighted-product, discrete-bin constant-sum and Uniswap v3 position models, but statistical independence is not established. Lead remains held.


## Source verification audit 9 (2026-11-11)

[Source Verification Audit 9](CORE295_SOURCE_VERIFICATION_AUDIT_9.md) clarifies Carbon's structural relationship: its invariant is a translated/scaled constant-product hyperbola (including a constant-price limiting case), and the whitepaper says it is financially equivalent to a virtual-token model. Carbon's genuinely distinctive element is its asymmetric one-direction order and linked-strategy state architecture. Keep as protocol architecture context, not a new structural equation family under the current equation-only catalogue policy.


## Source verification audit 10 (2026-11-11)

[Source Verification Audit 10](CORE295_SOURCE_VERIFICATION_AUDIT_10.md) distinguishes Uniswap v2's arithmetic mean of price from Uniswap v3's geometric mean price obtained through an arithmetic mean tick. The estimands are mathematically different, although they remain in one broad on-chain oracle family with shared market dependence. Preserve this distinction and avoid counting accumulators, inverse orientation, window lengths or harmonic-mean liquidity as separate price equations.


## Source verification audit 11 (2026-11-11)

[Source Verification Audit 11](CORE295_SOURCE_VERIFICATION_AUDIT_11.md) sharpens three DeFi family boundaries. Curve CryptoSwap is a distinct dynamic-peg invariant within the Curve invariant-AMM lineage; Morpho's LLTV-dependent capped rational LIF is a liquidation-incentive model, not another health-factor equation; and Compound III's per-second borrow rate is a piecewise-affine utilization-kink function, structurally related to Aave-style kink curves. Keep each complete mechanism in one family and do not count helper identities, supply-rate conversions, annualization, price-scale/repegging updates or liquidation bookkeeping as extra equations. All three remain held, not accepted.
