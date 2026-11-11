# Core-295 provisional source-family cluster map

**Status:** review aid only, not an accepted equation catalogue. Cluster labels below are provisional grouping identifiers for equivalence review and statistical sampling. They do not imply that every source in a cluster contributes a structurally distinct equation.

**Current discovery snapshot:** 128 candidate source records; 122 bibliography items; 38 discovery batches; 19 proposed equation records; zero accepted equation entries. Option 2 remains 295 accepted structurally distinct equations, 59 per domain. A source record, paper, protocol or formula variant is not itself an equation count.

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


## Source verification audit 12 (2026-11-11)

[Source Verification Audit 12](CORE295_SOURCE_VERIFICATION_AUDIT_12.md) distinguishes Gyro E-CLP's elliptic invariant from Gyro 2-CLP's translated constant-product invariant, and distinguishes Solidly V2's quartic stable-pool invariant (x^3y+xy^3) from both constant product and Curve StableSwap. E-CLP and Solidly stable remain held for implementation/version, units, decimals, fixed-point and rounding contracts. Gyro 2-CLP remains blocked by the Core-15 Constant Product exclusion; virtual offsets and quadratic solution are not independent equations.


## Source verification audit 13 (2026-11-11)

[Source Verification Audit 13](CORE295_SOURCE_VERIFICATION_AUDIT_13.md) confirms Euler EVK's capped health-dependent discount (d=min(1-h,m)), equivalently retained factor (f=max(h,1-m)), against a pinned implementation. Unlike Morpho's market-LLTV rational LIF, Euler's discount depends on individual position health. Keep both as distinct mechanisms in one liquidation-incentive source family; neither health ratio, discount complement nor collateral conversion is an extra equation. Euler remains held pending its full valuation and rounding contract.


## Source verification audit 14 (2026-11-11)

[Source Verification Audit 14](CORE295_SOURCE_VERIFICATION_AUDIT_14.md) distinguishes Sky LIQ2.0's linear auction-price decay from its exponential decay calculators. Stairstep exponential uses a floor-quantized elapsed-time exponent and becomes identical to continuous per-second exponential at step=1. Treat them as alternative price functions within one Clipper/Abacus liquidation-auction family; the auction architecture, resets, buffers and price-calculator helpers are not extra equation candidates. Hold pending immutable implementation pinning and exact RAY arithmetic/rounding contract.


## Source verification audit 15 (2026-11-11)

[Source Verification Audit 15](CORE295_SOURCE_VERIFICATION_AUDIT_15.md) records Liquity V1's coupled product-sum Stability Pool accounting: the cumulative depletion product P and collateral-gain sum S jointly determine compounded deposits and collateral gains from depositor snapshots. It is a possible system-level risk-sharing candidate only if the domain admits stateful protocol accounting and a deterministic system adapter. Do not split P, S, deposit/gain queries, scale handling or LQTY reward sum G into separate equations. Hold pending immutable implementation pin and domain/Recovery Mode contract.


## Source verification audit 16 (2026-11-11)

[Source Verification Audit 16](CORE295_SOURCE_VERIFICATION_AUDIT_16.md) confirms Aave V3's health factor expands to the collateral-value-weighted liquidation-threshold sum divided by total debt. This is the multi-collateral form of the same risk-adjusted collateral/debt health family as Euler EVK, while Morpho's market formula is its single-collateral case. Do not count protocol labels or the weighted-average-threshold identity as new equations; keep health-state measures separate from liquidation incentive functions.


## Source verification audit 17 (2026-11-11)

[Source Verification Audit 17](CORE295_SOURCE_VERIFICATION_AUDIT_17.md) separates Compound III's post-absorption storefront price discount from liquidation eligibility and liquidator incentives. The discount is a configured product of StoreFrontPriceFactor and one minus the asset's LiquidationFactor; its quote conversion is not an independent equation. Keep as collateral-sale pricing context in the broader liquidation family, not a new structurally rich candidate.


## Source verification audit 18 (2026-11-11)

[Source Verification Audit 18](CORE295_SOURCE_VERIFICATION_AUDIT_18.md) places Marcus outer-sphere transfer in the activated-rate family but records its distinctive quadratic driving-force barrier. It distinguishes the original collision-frequency prefactor from the IUPAC encounter-complex Eyring prefactor. Keep one Marcus family and hold until the benchmark selects one prefactor and resolves Core-15 Arrhenius/generic rate-law overlap; no barrier/prefactor/regime variants are independent entries.


## Source verification audit 19 (2026-11-11)

[Source Verification Audit 19](CORE295_SOURCE_VERIFICATION_AUDIT_19.md) verifies the BYL719 tumour-turnover ODE against De Buck et al. (2014), equation 9. It is a drug-specific PK/PD model with zero-order growth modulated by saturable Emax inhibition and first-order loss; its state is the sum of longest tumour diameters, and drug concentration is an external PK input. Keep it as one complete turnover model, not component equations, and hold pending clinical input/range and family-dependence contracts.


## Source verification audit 20 (2026-11-11)

[Source Verification Audit 20](CORE295_SOURCE_VERIFICATION_AUDIT_20.md) groups Henry and Raoult as different physical equilibria but flags their identical bare proportionality structure for the strict structural-distinctness policy. Beer–Lambert is one decadic exponential attenuation family; Lambert/Beer contributions, absorbance and transmission forms are not extra entries. Henry's modern textbook equation and Beer–Lambert's IUPAC expression are verified; primary historical equation-page checks and benchmark ranges remain outstanding.


## Source verification audit 21 (2026-11-11)

[Source Verification Audit 21](CORE295_SOURCE_VERIFICATION_AUDIT_21.md) verifies Hill's muscle force–velocity equation from the original 1938 paper and clarifies its first occurrence (printed p. 162) versus later mechanical verification (pp. 176–177). It is distinct from Hill ligand binding. Planck's 1901 equation (13) is spectral energy density per wavelength; the proposed exitance form follows from isotropic (c/4) conversion. Keep frequency/radiance forms and Wien/Stefan consequences in one Planck family; use an explicit spectral-exitance symbol.


## Source verification audit 22 (2026-11-11)

[Source Verification Audit 22](CORE295_SOURCE_VERIFICATION_AUDIT_22.md) confirms the thin-lens imaging relation (with signed real/virtual image conventions) and the viscosity-explicit Hagen–Poiseuille tube-flow relation. Keep thin-lens imaging with geometric-optics/lens-maker relations and Poiseuille flow with laminar viscous-fluid mechanics; do not count rearrangements, resistance identity or pressure-flow components as extra equations.


## Source verification audit 23 (2026-11-11)

[Source Verification Audit 23](CORE295_SOURCE_VERIFICATION_AUDIT_23.md) verifies the Fick cardiac-output mass balance directly against the original 1870 report. The source states the principle in prose rather than printing the modern equation; the transcription is oxygen uptake rate divided by the arterial–mixed-venous oxygen-content difference. It is a physiological conservation relation, not Fick diffusion flux. Keep CO2 cross-check and stroke-volume conversion as derived/validation steps, not separate equations.


## Source verification audit 24 (2026-11-11)

[Source Verification Audit 24](CORE295_SOURCE_VERIFICATION_AUDIT_24.md) verifies Balancer's weighted geometric invariant and its correspondence to the V2 WeightedMath implementation. Three-token form is one fixed-arity adapter to the general n-token weighted family; the equal two-token special case is constant product. Do not count spot prices, swap formulas or weight/token-count variants separately. Hold pending immutable implementation pin and numerical contract.


## Source verification audit 25 (2026-11-11)

[Source Verification Audit 25](CORE295_SOURCE_VERIFICATION_AUDIT_25.md) verifies Langmuir's 1918 single-site monolayer coverage equation. Its rational saturation form is mathematically shared with Michaelis–Menten/Hill-one occupancy despite the different surface-adsorption mechanism. This is a cross-domain structural-equivalence gate against Core-15's MM exclusion; source/domain labels alone do not make it a distinct equation. Keep coverage, adsorbed amount and LH adsorption substeps together.


## Source verification audit 26 (2026-11-11)

[Source Verification Audit 26](CORE295_SOURCE_VERIFICATION_AUDIT_26.md) verifies Fick's 1855 original local flux relation and explicitly records Fick's own Fourier/Ohm transport-law analogy. The normalized constitutive form is linear flux proportional to a driving-field gradient. Fick first law and the derived diffusion PDE are one family; cross-domain structural policy must determine whether Fourier/Ohm analogues can count independently.


## Proposed-record source verification matrix (2026-11-11)

[Core-295 Proposed-Record Source Verification Matrix](CORE295_PROPOSED_RECORD_SOURCE_VERIFICATION_MATRIX.md) maps all 19 proposed records to their source-verification audit and records the remaining acceptance gates, including cross-domain structural equivalence, source/version pinning, valid ranges and independent-unit definitions. No candidate is accepted by this matrix.


## Discovery batch 25 (2026-11-11)

[Candidate Discovery Batch 25](CORE295_CANDIDATE_DISCOVERY_BATCH_25.md) adds source leads for Nernst electrochemical equilibrium and Debye–Hückel ionic activity, with Clausius–Clapeyron/van't Hoff family-overlap review and an osmotic-pressure/Ideal Gas Law exclusion warning. No equation is accepted or added to the formal catalogue.


## Discovery batch 26 (2026-11-11)

[Candidate Discovery Batch 26](CORE295_CANDIDATE_DISCOVERY_BATCH_26.md) adds Biology leads for Nicholson–Bailey host–parasitoid dynamics, Leslie age-structured matrix projection and Taylor–Jonker replicator dynamics. These are complete discrete/vector systems and require a full-system adapter. Beverton–Holt stock–recruitment is flagged as a rational saturation structure related to Langmuir/MM, not an automatic new equation.


## Discovery batch 27 (2026-11-11)

[Candidate Discovery Batch 27](CORE295_CANDIDATE_DISCOVERY_BATCH_27.md) adds Physics leads for Kepler orbital period, Lorentz force and Bragg diffraction. Keep Kepler linked to Newtonian central-force dynamics, Lorentz as a vector matter–field coupling distinct from Maxwell's field equations, and Bragg in the same path-difference interference family as double-slit/grating relations.


## Discovery batch 28 (2026-11-11)

[Candidate Discovery Batch 28](CORE295_CANDIDATE_DISCOVERY_BATCH_28.md) adds financial-risk leads for Parkinson range variance, GARCH(1,1), normal expected shortfall and Merton structural credit risk. EWMA is grouped with GARCH as an IGARCH boundary case; Merton distance-to-default is a derived statistic of the structural credit model. Confirm that general market/credit risk fits the DeFi Risk domain before formal registration.


## Source verification audit 27 (2026-11-11)

[Source Verification Audit 27](CORE295_SOURCE_VERIFICATION_AUDIT_27.md) confirms the modern Nernst reaction-quotient equation and the original 1889 historical context, and clarifies Debye–Hückel's limiting law for mean ionic activity coefficients. Keep original Nernst electrode notation distinct from modern whole-cell form; distinguish mean, single-ion and osmotic coefficients. No formal catalogue record is added.


## Source verification audit 28 (2026-11-11)

[Source Verification Audit 28](CORE295_SOURCE_VERIFICATION_AUDIT_28.md) confirms Leslie's age-structured linear projection matrix and Taylor–Jonker's nonlinear simplex-constrained replicator dynamics from their original papers. Treat each as one complete vector system; no age/strategy component, eigenvalue or equilibrium condition is a separate equation. Nicholson–Bailey remains a source lead only until its original equation page is verified.


## Discovery batch 29 (2026-11-11)

[Candidate Discovery Batch 29](CORE295_CANDIDATE_DISCOVERY_BATCH_29.md) adds Balancer Linear Pool's rate-normalized constant-sum invariant with piecewise nominal main-balance fees. It is distinct from CP, weighted geometric, finite-amplification StableSwap, PMM and E-CLP structures, but should be grouped with constant-sum/linear-pool families and reviewed against the StableSwap high-amplification limit.


## Discovery batch 30 (2026-11-11)

[Candidate Discovery Batch 30](CORE295_CANDIDATE_DISCOVERY_BATCH_30.md) adds two distinct electrochemical mechanisms: Butler–Volmer charge-transfer kinetics at the electrode interface and Nernst–Planck ionic bulk transport. Keep Nernst equilibrium, Butler–Volmer current response and Tafel asymptotes in one related electrode-kinetics family; keep Nernst–Planck's diffusion/migration/convection terms and Poisson/electroneutrality closures in one electrodiffusion system.


## Discovery batch 31 (2026-11-11)

[Candidate Discovery Batch 31](CORE295_CANDIDATE_DISCOVERY_BATCH_31.md) adds Bernoulli, Stokes drag and Young–Laplace pressure. Keep Bernoulli with inviscid Euler-flow energy integrals; Stokes drag with creeping-flow/Poiseuille/Navier–Stokes special solutions; Young–Laplace as a distinct curvature-dependent interfacial pressure family.


## Discovery batch 32 (2026-11-11)

[Candidate Discovery Batch 32](CORE295_CANDIDATE_DISCOVERY_BATCH_32.md) identifies Maverick V2's tick invariant as constant product in virtual reserves, structurally related to Gyro 2-CLP. Bin movement, merging and the recursive tick-domain log-price TWAP are protocol-state features; they are not independent invariant equations.


## Discovery batch 33 (2026-11-11)

[Candidate Discovery Batch 33](CORE295_CANDIDATE_DISCOVERY_BATCH_33.md) adds four stochastic-risk families: OU (constant-volatility mean reversion), CIR (square-root mean reversion), Hawkes (self-exciting event clusters) and Merton jump diffusion. Keep OU/CIR in the broader mean-reverting diffusion family; keep Hawkes as point-process risk; keep Merton jump and its no-jump GBM limit in one jump-diffusion family. Applicability depends on the DeFi Risk domain boundary.


## Discovery batch 34 (2026-11-11)

[Candidate Discovery Batch 34](CORE295_CANDIDATE_DISCOVERY_BATCH_34.md) adds Fisher–KPP, Gierer–Meinhardt and chemostat–Monod. Fisher–KPP extends logistic growth spatially; Gierer–Meinhardt is a nonlinear activator–inhibitor member of the broader Turing/morphogenesis PDE family; chemostat–Monod couples biomass and substrate states but contains the MM/Monod saturation structure.


## Source verification audit 29 (2026-11-11)

[Source Verification Audit 29](CORE295_SOURCE_VERIFICATION_AUDIT_29.md) transcribes Fisher 1937's scalar reaction–diffusion equation and Gierer–Meinhardt 1972 Eq. (15a,b). Keep Fisher in the spatial logistic-reaction family; keep Gierer–Meinhardt as a coupled activator–inhibitor model within the broader Turing/morphogenesis PDE family. The source's explicit source-density fields and multiple mechanism variants must not be collapsed into one generic formula without a declared model choice.


## Discovery batch 35 (2026-11-11)

[Candidate Discovery Batch 35](CORE295_CANDIDATE_DISCOVERY_BATCH_35.md) adds Schrödinger wave mechanics, Compton photon–electron scattering and de Broglie matter waves. Keep stationary/time-dependent Schrödinger forms in one family; keep Compton wavelength shift distinct from Planck spectral distribution; keep de Broglie phase/group-wave representations in one matter-wave family.


## Discovery batch 36 (2026-11-11)

[Candidate Discovery Batch 36](CORE295_CANDIDATE_DISCOVERY_BATCH_36.md) adds GHK multi-ion membrane potential and revised Starling filtration. Keep GHK voltage/current and original Goldman/Hodgkin–Katz formulations in one constant-field family; keep classical/revised Starling in one capillary-filtration lineage, with the glycocalyx subcompartment defining the revised oncotic term.


## Source verification audit 30 (2026-11-11)

[Source Verification Audit 30](CORE295_SOURCE_VERIFICATION_AUDIT_30.md) confirms Hawkes self-exciting event intensity and Merton's Brownian-plus-Poisson jump process from the original papers. OU and CIR remain related mean-reverting diffusion families with incomplete original-page transcription; Hawkes and Merton are distinct process classes. No stochastic process has been added to the formal catalogue.


## Source verification audit 31 (2026-11-11)

[Source Verification Audit 31](CORE295_SOURCE_VERIFICATION_AUDIT_31.md) confirms the GHK constant-field diffusion-potential lineage and the revised Starling glycocalyx model. GHK is a multi-ion zero-current steady state, not a Nernst thermodynamic equilibrium. The revised Starling Πg force balance is not a closed steady-state law; the full Levick–Michel Eq. (3) is implicit through its Péclet number. Keep all expressions in one model lineage.


## Discovery batch 37 (2026-11-11)

[Candidate Discovery Batch 37](CORE295_CANDIDATE_DISCOVERY_BATCH_37.md) adds Heston stochastic volatility and Cramér–Lundberg reserve ruin. Heston is a coupled price/variance SDE with CIR-like variance and correlated Brownian shocks; Cramér–Lundberg is a compound-Poisson reserve process with a first-passage ruin functional. Keep components and derived pricing/ruin outputs in one complete-system family.


## Source verification audit 32 (2026-11-11)

[Source Verification Audit 32](CORE295_SOURCE_VERIFICATION_AUDIT_32.md) verifies Heston's coupled stochastic-volatility system from the original 1993 paper and records the physical vs risk-neutral process distinction. It also records the Cramér–Lundberg reserve/compound-Poisson process and its exponential-claim ruin functional. Keep Heston price and variance equations together; keep reserve process and ruin probability together. Applicability to DeFi depends on token-market/insurance-fund assumptions.


## Source verification audit 33 (2026-11-11)

[Source Verification Audit 33](CORE295_SOURCE_VERIFICATION_AUDIT_33.md) confirms Kepler, Lorentz and Bragg equations and their family boundaries. Keep Kepler linked to Newtonian orbital dynamics; Lorentz as a vector force law coupled to but distinct from Maxwell's field equations; Bragg in the constructive-interference path-difference family.


## Source verification audit 34 (2026-11-11)

[Source Verification Audit 34](CORE295_SOURCE_VERIFICATION_AUDIT_34.md) verifies Parkinson range variance, GARCH conditional variance and normal expected shortfall. Group EWMA with GARCH as its IGARCH boundary case; keep Parkinson as a range estimator, GARCH as a conditional-variance recursion, and ES as a tail-mean functional distinct from the VaR quantile but subject to the Core-15 VaR-family exclusion policy.


## Source verification audit 35 (2026-11-11)

[Source Verification Audit 35](CORE295_SOURCE_VERIFICATION_AUDIT_35.md) records Bancor CRR's purchase/sale return functions and a versioned source discrepancy in an earlier whitepaper draft. The invariant is a reserve-backed power-law bonding curve, distinct from two-sided CP and weighted pools but potentially a separate token-issuance domain. Keep purchase, sale, spot-price and cross-connector calculations in one CRR family.


## Source verification audit 36 (2026-11-11)

[Source Verification Audit 36](CORE295_SOURCE_VERIFICATION_AUDIT_36.md) records the Butler–Volmer history and transfer-coefficient convention and the Nernst–Planck mobility/diffusivity distinction. Keep Butler–Volmer as one empirical two-way electrode-kinetics family, with Tafel and linear-response limits derived; keep Nernst–Planck's diffusion/migration/convection and balance/field closure as one coupled electrodiffusion system.


## Source verification audit 37 (2026-11-11)

[Source Verification Audit 37](CORE295_SOURCE_VERIFICATION_AUDIT_37.md) verifies Curve CryptoSwap's A–gamma dynamic invariant and pinned Tricrypto implementation. It is distinct from fixed StableSwap but related within the amplified-invariant family; the dynamic price_scale/repeg state is part of the complete pool model. Keep the invariant, K0/K definitions, Newton D/y solvers, swap formulas and repegging machinery together as one family.


## Discovery batch 38 (2026-11-11)

[Candidate Discovery Batch 38](CORE295_CANDIDATE_DISCOVERY_BATCH_38.md) identifies Curve LLAMMA's per-band invariant as virtual constant product, structurally related to Gyro/Maverick/Uniswap v3. Its complete soft-liquidation/de-liquidation mechanism is a potentially distinct protocol-risk system, not a new per-band invariant; it requires oracle, band, fee, interest and hard-liquidation state in one adapter.


## Source verification audit 38 (2026-11-11)

[Source Verification Audit 38](CORE295_SOURCE_VERIFICATION_AUDIT_38.md) verifies Gyro E-CLP as a distinct ellipse invariant with finite price bounds, asymmetric concentration, stretch and rotation. Keep it separate from Gyro 2-CLP's virtual-constant-product curve; keep reserve solves, price derivatives, swaps, liquidity updates and parameter precomputation in one E-CLP family.


## Source verification audit 39 (2026-11-11)

[Source Verification Audit 39](CORE295_SOURCE_VERIFICATION_AUDIT_39.md) confirms Gyro 2-CLP belongs to the virtual-reserve constant-product family. Its bounded price range and protocol architecture differ, but the invariant form is shared with Uniswap v3, Maverick and LLAMMA. Gyro E-CLP remains distinct as an affine-transformed ellipse.


## Structural-equivalence policy decision pending (2026-11-11)

[Structural Equivalence Policy Options](CORE295_STRUCTURAL_EQUIVALENCE_POLICY_OPTIONS.md) consolidates the cross-domain collisions and system-level distinctions. The recommended hybrid rule (strict scalar-form comparison plus complete coupled-system units) is a proposal only; no rule has been adopted and unresolved families remain held.


## Source verification audit 40 (2026-11-11)

[Source Verification Audit 40](CORE295_SOURCE_VERIFICATION_AUDIT_40.md) verifies Balancer Linear Pool's rate-normalized constant-sum invariant and piecewise nominal-balance fee transform at a pinned V2 commit. The moving-branch source concern is closed; keep invariant, nominal transform, inverse, BPT conversion and swap directions in one family. Resolve whether the constant-sum mechanism is structurally separate from StableSwap's high-amplification limit.


## Source verification audit 41 (2026-11-11)

[Source Verification Audit 41](CORE295_SOURCE_VERIFICATION_AUDIT_41.md) confirms the LLAMMA per-band invariant is virtual constant product and groups it with Gyro 2-CLP, Uniswap v3 and Maverick. The full lending/liquidation mechanism couples bands, oracle, interest multiplier, fees, controller and hard-liquidation boundary; consider only as one complete DeFi Risk system if system-level units are permitted.


## Source verification audit 42 (2026-11-11)

[Source Verification Audit 42](CORE295_SOURCE_VERIFICATION_AUDIT_42.md) confirms the normalized Solidly stable invariant (XY(X^2+Y^2)=k), a symmetric quartic curve with no StableSwap amplification parameter. Keep Solidly-derived stable forks in one family; the volatile (xy=k) branch, decimal-normalization transforms, solver and swap directions are not additional equation candidates.


## Source verification audit 43 (2026-11-11)

[Source Verification Audit 43](CORE295_SOURCE_VERIFICATION_AUDIT_43.md) records Swaap V2 as RFQ market-making infrastructure. The Balancer-derived vault does not make its off-chain quote-generation mechanism a new AMM invariant; the drawdown/last-look/imbalance checks are protocol-specific safeguards, not independent equation candidates.


## Source verification audit 44 (2026-11-11)

[Source Verification Audit 44](CORE295_SOURCE_VERIFICATION_AUDIT_44.md) adds Aave health factor as a multi-asset weighted collateral/debt ratio and Compound/Aave kinked borrowing rates as one piecewise-linear utilization-rate family. Keep the health-factor aggregate and liquidation predicate together; do not split reserve contributions or weighted-threshold components. Group Aave and Compound rate curves despite protocol-specific parameters.


## Source verification audit 45 (2026-11-11)

[Source Verification Audit 45](CORE295_SOURCE_VERIFICATION_AUDIT_45.md) confirms Morpho LIF as a capped reciprocal affine function of LLTV and liquidation cursor. Keep the Morpho Blue/Midnight naming and version distinctions explicit; do not count parameter values or collateral-seizure operations separately.


## Source verification audit 46 (2026-11-11)

[Source Verification Audit 46](CORE295_SOURCE_VERIFICATION_AUDIT_46.md) confirms Euler's capped linear health-shortfall discount and distinguishes it from Morpho's reciprocal liquidation incentive factor. Both belong to the broader liquidation-incentive family but have different scalar functional forms; protocol version, health calculation, discount cap and settlement semantics must be frozen.


## Source verification audit 46 (2026-11-11)

[Source Verification Audit 46](CORE295_SOURCE_VERIFICATION_AUDIT_46.md) distinguishes Euler's capped linear health-shortfall discount from Morpho Blue's reciprocal LIF. Both are liquidation-incentive rules within a broader risk family; neither health, discount, yield conversion nor repay calculations should be split into separate samples.


## Source verification audit 47 (2026-11-11)

[Source Verification Audit 47](CORE295_SOURCE_VERIFICATION_AUDIT_47.md) classifies Liquity Stability Pool as a coupled path-dependent product-sum accounting system. Per-unit loss/gain, P/S accumulators, snapshot claims, error correction and scale transitions are one family, not separate equation candidates. Do not conflate the reviewed source snapshot with Liquity V2/BOLD.


## Source verification audit 48 (2026-11-11)

[Source Verification Audit 48](CORE295_SOURCE_VERIFICATION_AUDIT_48.md) classifies Sky/Maker Liquidations 2.0 as a configurable Dutch-auction system. Linear and exponential time-price laws differ as scalar functions; stair-step exponential with one-second steps is equivalent to continuous exponential. Do not count calculator choices, reset logic, auction caps and incentives as separate system samples.


## Source verification audit 49 (2026-11-11)

[Source Verification Audit 49](CORE295_SOURCE_VERIFICATION_AUDIT_49.md) classifies Compound III's liquidation path as a weighted collateral eligibility check plus reserve absorption and storefront sale. The eligibility form is related to Aave/Euler health metrics; the reserve-funded absorption and storefront mechanism are protocol-specific. Treat all stages as one system unit if system-level candidates are allowed.


## Source verification audit 50 (2026-11-11)

[Source Verification Audit 50](CORE295_SOURCE_VERIFICATION_AUDIT_50.md) classifies the OECD liquidation-volatility study as empirical context. Realized volatility, OLS/2SLS specifications and alternative window lengths are not independent DeFi protocol equations; the reported relation is sample- and dataset-specific.


## Source verification audit 51 (2026-11-11)

[Source Verification Audit 51](CORE295_SOURCE_VERIFICATION_AUDIT_51.md) classifies the fixed-spread two-call optimizer as a single derived strategy family. Its health-factor constraint overlaps the collateral-weighted lending-risk ratio; its first/second repayments and profit expressions are linked outputs. Keep separate from auction liquidation and modern protocol-specific incentive curves, but hold pending the system-unit policy.


## Source verification audit 52 (2026-11-11)

[Source Verification Audit 52](CORE295_SOURCE_VERIFICATION_AUDIT_52.md) adds Miqado as a potentially distinct reversible-option support system. Its baseline health factor/FSL equations overlap existing lending-risk families; the distinctive structure is the reversible option with early seller termination, borrower rescue and supporter maturity takeover/default. Keep all components in one system unit.


## Source verification audit 53 (2026-11-11)

[Source Verification Audit 53](CORE295_SOURCE_VERIFICATION_AUDIT_53.md) groups BIS actual wallet leverage and LTV-implied leverage as standard balance-sheet metrics. The study's “VaR” label means share of loans near liquidation, not conventional quantile VaR. Wallet addresses are not proven independent economic participants; preserve the reported sample-count discrepancy.


## Source verification audit 54 (2026-11-11)

[Source Verification Audit 54](CORE295_SOURCE_VERIFICATION_AUDIT_54.md) records the SOA report as taxonomy context only. It contributes no governing equation, quantitative risk function or independent equation family; use its categories for domain boundaries, not for padding the 295 count.


## Source verification audit 55 (2026-11-11)

[Source Verification Audit 55](CORE295_SOURCE_VERIFICATION_AUDIT_55.md) adds a peer-reviewed under-collateralized leverage model. Group its debt ratio, leverage, liquidation threshold, liquidation loss and maximum-leverage bound as one DeFi Risk analytical family; CP IL/arbitrage components remain attached to existing AMM families. Source RISK-WANG-SPECULATIVE-MULTIPLIERS is candidate_reference only.


## Source verification audit 56 (2026-11-11)

[Source Verification Audit 56](CORE295_SOURCE_VERIFICATION_AUDIT_56.md) adds Aave V4's debt-coverage-weighted collateral-risk premium: collateral is sorted by risk score and only the collateral value needed to cover debt contributes to the average. The health-dependent bonus interpolates between a minimum and maximum, and liquidation sizing targets a configurable health factor. Keep all in one Aave V4 position-risk/liquidation system; do not count components separately.


## Source verification audit 57 (2026-11-11)

[Source Verification Audit 57](CORE295_SOURCE_VERIFICATION_AUDIT_57.md) records MIP45's obsolete governance status and historical-design role. Keep MIP45, the Dog/Clipper/Abacus implementation, three price calculators, Hole/Dirt invariants, reset logic and circuit breaker in one historical liquidation-auction family; pin current deployed version before adapter work.


## Source verification audit 58 (2026-11-11)

[Source Verification Audit 58](CORE295_SOURCE_VERIFICATION_AUDIT_58.md) adds Euler's linear liquidation-LTV ramp to the same liquidation-risk family as its collateral-adjusted health ratio and capped discount. Only LTV decreases ramp; increases apply immediately. The current liquidation LTV, not borrow LTV, is used for liquidation valuation.


## Source verification audit 59 (2026-11-11)

[Source Verification Audit 59](CORE295_SOURCE_VERIFICATION_AUDIT_59.md) distinguishes Aave V4 Babylon cap-bounded sizing from standard V4 target-health sizing. Both share the same health factor, dynamic liquidation bonus and debt/collateral conversion family; Babylon adds maxCollateralToRemove and inverse repayment resizing, with no separate liquidation fee or dust validation.


## Source verification audit 60 (2026-11-11)

[Source Verification Audit 60](CORE295_SOURCE_VERIFICATION_AUDIT_60.md) groups Maker/Sky Jug's per-second stability fee with the generic exponential-compounding family. Global base, collateral duty, rpow/rmul, rate delta and Vat.fold are one accounting transition; do not count these components separately.
