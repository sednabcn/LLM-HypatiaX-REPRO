# Core-295 Biology and DeFi AMM primary-source audit 1

**Date:** 2026-11-11  
**Status:** source reconstruction and structural-family screen; no candidate accepted.  
**Method:** static review of primary/official sources and an accessible mathematical biology textbook. No code, protocol calls, experiments, validators or workflows were run.

## 1. Biology: stock–recruitment and population growth

### 1.1 Stock–recruitment generalized-family lead

A published synthesis gives the generalized Deriso–Schnute stock–recruitment relation

\[
R_t=\alpha S_t(1-\gamma\beta S_t)^{1/\gamma},
\]

with the Ricker limit as \(\gamma\to0\) and Beverton–Holt form at \(\gamma=-1\). This is useful equation-level secondary evidence for an E2 family relationship. It does **not** yet establish that the generalized formula and exact parameter restrictions have been transcribed from the relevant Deriso and Schnute primary papers. Keep the parent and its named special cases grouped provisionally; do not count three equations or promote a candidate until primary equation/page evidence is complete.

Source: ICES Journal of Marine Science synthesis (2014), which explicitly attributes the general three-parameter stock–recruitment relation to Deriso (1980), further developed by Schnute (1985): https://academic.oup.com/icesjms/article/71/8/2307/2804451

### 1.2 Do not conflate different model types sharing surnames

Thieme's *Mathematics in Population Biology* (2003) separately treats:
- continuous-time Beverton–Holt and Smith growth equations (Chapter 5, §5.2);
- continuous-time Ricker growth equation (Chapter 5, §5.3);
- discrete-time Beverton–Holt difference equation and generalization (Chapter 9, §9.1);
- discrete-time Ricker difference equation (Chapter 9, §9.2).

This source organization is a material warning: continuous-time density-dependent population growth ODEs, discrete-time population maps, and fisheries stock–recruitment functions are not automatically the same model unit. The surname or curve shape is not enough to infer E0–E2 equivalence. Preserve time structure, state interpretation, and derivation lineage in each candidate.

The textbook is secondary context, not primary equation provenance:
https://api.pageplace.de/preview/DT0400.9780691187655_A33705070/preview-9780691187655_A33705070.pdf

### 1.3 Coupled population systems

A delay-difference or age-structured model must be treated as a complete state/observation system. Recruitment, survival, growth, age transitions, harvest and catch observations cannot be split into several independent equation counts simply because they appear as separate lines in a paper. A scalar recruitment function alone is not the complete population state transition.

**Disposition:** retain the generalized stock–recruitment family as a provisional cluster; keep continuous and discrete population-growth forms in separate clusters pending derivation review; no Biology candidate accepted.


### 1.4 Additional primary Biology source families

The source register now includes five additional primary/foundational lineages and one review:

- **Kermack–McKendrick epidemic model (1927):** the epidemic flow is a coupled compartment system. Infection incidence, removal and susceptible depletion are linked state transitions; do not split them into three independent equation counts. Primary scan: https://pdodds.w3.uvm.edu/files/papers/others/1927/kermack1927a.pdf
- **Leslie age-structured matrix (1945):** the age-class population vector advances through a fertility/survival matrix. Stable age distribution, growth eigenvalue and reproductive-value outputs are derived from the matrix model, not independent candidates. DOI: https://doi.org/10.1093/biomet/33.3.183
- **Michaelis–Menten invertase kinetics (1913):** the original article studies reaction progress for invertase. Do not silently replace the original mechanistic/reaction-progress treatment with a later steady-state hyperbolic rate-law transcription. Accessible English translation: https://www.chem.uwec.edu/Chem352_F18/pages/readings/media/Michaelis_%26_Menton_1913.pdf
- **Holling functional response (1959):** the accessible abstract for *Some Characteristics of Simple Types of Predation and Parasitism* gives a saturating search/handling response and reports an S-shaped small-mammal response, but explicitly says an additional search-stimulation component was still under investigation. This article alone does not provide a complete, separately specified Type III model. DOI: https://doi.org/10.4039/Ent91385-7
- **Volterra predator–prey dynamics (1926):** keep predator and prey equations as one coupled system. The 1927 correspondence explicitly acknowledges Lotka's prior publication of the two-species differential equations; the surname "Lotka–Volterra" should not obscure the shared model family. DOI: https://doi.org/10.1038/118558a0
- **Monod bacterial culture growth (1949):** a foundational review/synthesis of quantitative bacterial growth, not the original primary discovery paper. Use it for model lineage and assumptions, not as an unqualified primary-source attribution. DOI: https://doi.org/10.1146/annurev.mi.03.100149.002103


- **Verhulst logistic population growth (1838):** an original translated scan is registered. Keep the differential equation, integrated logistic solution, and discrete logistic map as related forms; the integrated solution is not a second governing equation. Original note: https://www.neo-classical-physics.info/uploads/3/4/3/6/34363841/verhulst_-_law_of_population.pdf
- **von Bertalanffy organic growth (1938):** the primary article derives growth from opposing construction/anabolism and destruction/catabolism terms with surface/volume scaling. Exact equation/page and observable transcription remain open. Bibliographic record: https://www.jstor.org/stable/41447359

**Cross-family screen:** Monod substrate-limited growth, Holling Type II consumption and Michaelis–Menten enzyme rates share a hyperbolic saturation structure after normalization, but represent different biological mechanisms. Under the current draft E3 rule, do not count them as three structurally distinct scalar formulas solely because their variables and interpretations differ. A full enzyme mechanism, consumer-handling model or microbial growth/state system may be a different model unit only when its complete state equations are supplied and the benchmark unit is declared accordingly. The S-shaped small-mammal response reported by Holling (1959) is not yet a complete Type III equation candidate: the paper describes an additional search-stimulation component as unresolved. Any later Type III formulation needs its own primary-source equation and mechanism audit.

## 2. DeFi AMM: primary invariant reconstruction

### 2.1 Uniswap constant-product and concentrated liquidity

The official Uniswap developer guide states the reserve invariant \(xy=k\), and explicitly says v3/v4 apply it within each LP's chosen price range. This is not evidence for a new independent invariant for every price, output, spot-price, or liquidity expression derived from it.

For one concentrated-liquidity position, an accessible academic appendix gives a virtual-reserve representation:

\[
\left(x+\frac{L}{\sqrt{p_{upper}}}\right)
\left(y+L\sqrt{p_{lower}}\right)=L^2,
\]

with a fixed active range \([p_{lower},p_{upper}]\). The same source gives per-range token balances and a piecewise trade relation; trades crossing ticks must be composed across successive active ranges. The virtual-reserve equation is an affine-coordinate representation of constant-product trading within the selected range, not automatically a separate structural family from the Core-15 constant-product exclusion.

Sources:
- Official Uniswap concepts: https://developers.uniswap.org/docs/get-started/concepts/how-uniswap-works
- Caparros, Chaudhary & Klein (2024 working paper), Appendix B/C: https://wrap.warwick.ac.uk/id/eprint/186143/1/WRAP-blockchain-scaling-liquidity-concentration-decentralized-exchanges-2024.pdf

**Screen:** keep the full concentrated-liquidity state/position model as a system-level lead only if the benchmark unit includes tick ranges, active liquidity, tick crossing and position accounting. Do not count token0 amount, token1 amount, liquidity inversion, virtual reserves, tick conversion, spot price and position value as separate equations.

### 2.2 Balancer weighted invariant

The official Balancer V2 reference defines the weighted value invariant

\[
V=\prod_i B_i^{w_i},\qquad \sum_i w_i=1,
\]

where \(B_i\) are pool balances and \(w_i\) normalized weights. Spot-price and exact-in/exact-out swap equations are derived from this invariant; they are not separate model families. The source explicitly says swap fees are applied to the input amount and that the invariant is generalized from constant product to arbitrary token counts and non-50/50 weights.

Source: https://docs-v2.balancer.fi/reference/math/weighted-math.html

**Screen:** cluster the invariant, spot price, outGivenIn and inGivenOut in one weighted-pool family. A two-token 50/50 pool reduces to the constant-product family after a monotone power transformation; generalized weights and multi-token topology are materially richer, but distinctness relative to Core-15 must be adjudicated under the draft E3/E4 policy, not assumed from a different protocol name.

### 2.3 Curve StableSwap: directly verified primary invariant

Egorov's 2019 Curve StableSwap whitepaper directly derives the N-coin invariant:

\[
A n^n\sum_i x_i+D
=
A D n^n+
\frac{D^{n+1}}{n^n\prod_i x_i},
\]

where \(x_i\) are coin balances, \(n\) is the number of coins, \(A\) is the amplification parameter under the paper's convention, and \(D\) is the invariant-like pool quantity solved from the balances. The paper describes the construction as interpolating between constant-sum behavior near balance and constant-product behavior as the pool becomes imbalanced. It explicitly states that solving for \(D\) or a new output balance is iterative.

Primary source: Egorov (2019), *StableSwap — efficient mechanism for Stablecoin liquidity*, original PDF pp. 3–4:
https://docs.curve.finance/assets/files/whitepaper_stableswap-fc0bb370db9fe3a91afdde8662e78206.pdf

The current official Curve overview distinguishes StableSwap for near-parity assets from CryptoSwap for volatile pairs and notes that current NG contracts and legacy implementations differ:
https://docs.curve.finance/developer/amm/curve-amm-overview/

**Screen:** StableSwap is a strong distinct invariant-family lead relative to constant product: its defining equation combines a sum term, product term and amplification-dependent interpolation. It is not the unsupported shortcut \((A+1)\sqrt{xy}\). Do not count the Newton iteration, derivative price, output-balance root, fee-adjusted output and LP share accounting as separate invariant families. The whitepaper's algebra is real-valued; any code candidate must separately pin contract revision, amplification scaling, integer precision, rounding and iteration bounds.

### 2.4 Curve CryptoSwap and other AMMs

Egorov's 2021 CryptoSwap whitepaper directly gives a dynamic invariant system. It transforms balances by an internal price-scale vector, defines a dynamic coefficient from amplification A, gamma and a normalized product term K0, then uses that coefficient in a StableSwap-like sum/product invariant. It defines an internal N-dimensional exponential-moving-average price oracle and a repegging rule constrained by a tracked profit/loss condition. The paper states Newton iteration is used to solve for D and the output balance and explicitly warns that the solve function is not monotonic, making initial values and applicability ranges important (original PDF pp. 1–4). This is substantially more than a fee or parameter variant of StableSwap: the complete system includes dynamic price-scale/oracle state and repegging. Under draft E4 it is a plausible separate full-system family, but must be reviewed against the exact benchmark unit and version-pinned NG implementation before acceptance.

Primary source: Egorov (2021), *Automatic market-making with dynamic peg*: https://docs.curve.finance/assets/files/whitepaper_cryptoswap-de196d8f95aae3164a1226234d6d96ca.pdf

The official Curve overview also identifies CryptoSwap for volatile pairs and current Twocrypto-NG/Tricrypto-NG implementations. The whitepaper is not a substitute for matching one current contract revision and its integer implementation.

Balancer weighted pools, Curve StableSwap, Curve CryptoSwap, DODO PMM, Solidly stable/volatile pools, Gyro E-CLP, YieldSpace and liquidity-book designs should each be reconstructed from their own primary whitepapers or pinned code. Similar use of reserves, weights, amplification, exponentials or derivatives does not by itself establish equivalence or distinctness.


### 2.5 DODO Proactive Market Maker

Official DODO documentation defines a guide-price-centered, inventory-dependent marginal price. For base inventory \(B\) below its equilibrium \(B_0\), the relative price factor is \(R=1-k+k(B_0/B)^2\), so \(P=iR\). The documentation integrates this marginal price to obtain a finite-trade quote and then derives a quadratic inversion for the post-trade inventory. It also defines a long-regression rule that resets the equilibrium inventory using the guide price. These are not four independent equations: they are one PMM pricing/inventory-regression mechanism. Its use of an external guide price and inventory re-centering is structurally different from a static reserve-only constant-product invariant; the full guide-price and regression state contract must be part of any candidate.

Source: https://docs-next.dodoex.io/en/product/pmm-algorithm/the-mathematical-principle-of-pmm

### 2.6 YieldSpace constant-power-sum invariant

The 2020 YieldSpace working paper gives

\[
x^{1-t}+y^{1-t}=k,
\]

where \(t\) is normalized time to maturity with \(0\leq t<1\). At \(t=0\) it becomes constant sum; as \(t\to1\) it approaches constant product. The paper's intended observable is fixed-yield-token interest rate rather than a conventional spot price, and it derives the reserve-ratio rate relation \(r=y/x-1\). Time-to-maturity is an explicit state/parameter in the invariant, not merely a different numerical fee.

**Structural screen:** this is a strong distinct AMM invariant lead because the exponent depends on time to maturity and the target property is a constant interest rate for a fixed reserve ratio. The t=0 and t→1 limits are not separate equations. The invariant, rate observable, time convention, fee function and maturity behavior should be one coherent model contract.

Primary source: Niemerg, Robinson & Livnev (2020), *YieldSpace*, working draft: https://yieldprotocol.com/YieldSpace.pdf

### 2.7 Solidly V2 stable and volatile pools

Solidly's official V2 documentation specifies:
- volatile pool: \(xy\geq k\), which remains in the constant-product family;
- stable pool: \(x^3y+y^3x\geq k\), a polynomial invariant intended for correlated assets.

The stable polynomial is not the Curve StableSwap invariant and should not be represented by the unsupported Curve shortcut \((A+1)\sqrt{xy}\). However, reserve units, decimal normalization, fee treatment, invariant inequality and exact deployed implementation revision need verification. Do not infer the full contract math from the short documentation page alone.

Source: https://docs.solidly.com/dex-basics/swaps.html

## 3. Cross-family and Core-15 exclusion gates

1. Uniswap V2 swap output, reserve ratio, spot price, execution price, price impact and LP share formulas remain tied to the constant-product family and must not evade Core-15 exclusions by changing observable or fee convention.
2. Uniswap V3's per-range virtual-reserve curve is a coordinate transform of constant-product trading in an active range; count a full tick/position state system only if its complete state transition is the benchmark unit.
3. Balancer's weighted invariant is a generalized product-power family. Its relationship to constant product requires explicit E3/E4 adjudication.
4. Curve StableSwap is a separate nonlinear sum/product invariant candidate; its scalar solver and derived swap/price outputs are not independent equations.
5. Curve CryptoSwap is provisionally separate from StableSwap according to its primary dynamic-invariant/oracle formulation.
6. YieldSpace's time-dependent constant-power-sum invariant is a distinct yield-space candidate; its constant-sum and constant-product limits are not additional equations.
7. DODO PMM is a guide-price/inventory-regression system; do not count its marginal price, integrated quote and quadratic inverse separately.
8. Solidly stable polynomial invariant is distinct from Curve StableSwap in form, but its implementation-level scaling/normalization remains unverified; Solidly volatile remains constant-product.
6. Structural distinctness does not imply statistical independence. Pool versions, forks, and parameterized deployments from one invariant family should be clustered for sampling.

## 4. Current disposition

| Domain/family | Evidence state | Disposition |
|---|---|---|
| Biology: Deriso–Schnute stock–recruitment | Secondary equation transcription; primary mapping incomplete | Provisional E2 family cluster only |
| Biology: continuous vs discrete population growth | Textbook separates model types/time structures | Keep separate pending equation-level review |
| DeFi AMM: Uniswap v2/v3 | Official concepts + academic equation transcription | Constant-product exclusion / full concentrated-liquidity system lead |
| DeFi AMM: Balancer weighted | Official invariant and derived formulas | One weighted-invariant family; E3/E4 review |
| DeFi AMM: Curve StableSwap | Primary whitepaper equation verified | Strong distinct invariant lead; not accepted |
| DeFi AMM: Curve CryptoSwap | Primary 2021 whitepaper equations and dynamic oracle/repeg system verified | Plausible E4 full-system family; pin NG implementation and audit parameter/state contract |

No formal catalogue entry was added or accepted. Source records are not equation counts. No experiments, validators, solvers, workflows, paid compute or live protocol/API calls were run.


## 5. Chemistry: primary-source transcription checks

### 5.1 Marcus solution electron-transfer rate (1956)

The original Marcus Part I paper describes an intermediate state \(X^*\) with nonequilibrium solvent polarization. Under the paper's stated mechanism, when electronic transfer from \(X^*\) to product is more probable than return to reactants, the overall rate is the rate of formation of \(X^*\): the solution collision number multiplied by \(\exp(-\Delta F^*/kT)\). This is a conditional result tied to the paper's encounter/intermediate-state mechanism and its solution-phase collision-number convention. It must not be silently rewritten with a universal Eyring \(k_BT/h\) prefactor. Nor should the Part I electrostatic free-energy expression be conflated with later inner-sphere, nonadiabatic, electrochemical or intramolecular Marcus formulations.

Primary source: Marcus, R. A. (1956), *On the Theory of Oxidation-Reduction Reactions Involving Electron Transfer. I*, Journal of Chemical Physics 24(5), 966–978, DOI: https://doi.org/10.1063/1.1742723. Publisher abstract and Caltech-hosted original PDF record: https://authors.library.caltech.edu/records/desqy-fmq55.

**Disposition:** source-level rate statement verified; exact equation number/page, collision-number definition and all model-specific prefactors still require direct PDF transcription before candidate acceptance. Keep distinct from Eyring/transition-state theory unless a full mechanism and benchmark contract establish the relationship.

### 5.2 Frumkin electrocapillarity and adsorption attribution

The registered Frumkin (1920) paper is *On the Theory of Electrocapillarity: II*, Philosophical Magazine 40(237), 375–385, DOI: https://doi.org/10.1080/14786440908636137. The search evidence available for this audit did not expose its original equation text or establish that the modern adsorption isotherm \(bc=\u005cfrac{\theta}{1-\theta}\u005cmathrm{exp}(-2a\theta)\) is a verbatim equation from that 1920 article. A later historical source attributes a Frumkin modification to 1925, while Frumkin and Obrutsheva's 1926 Nature letter specifically discusses field dependence of neutral-molecule adsorption. These are related historical sources, not interchangeable proof of one exact equation's date or convention.

**Disposition:** retain the Frumkin 1920, 1925 and 1926 references as a provenance cluster; do not claim exact 1920 equation transcription or promote the modern isotherm until the original pages and sign/parameter definitions are checked. In particular, do not infer the sign meaning of the interaction parameter from modern conventions alone.

### 5.3 Von Bertalanffy organic growth (1938): evidence boundary

The accessible bibliographic record for *A Quantitative Theory of Organic Growth* supports the premise that construction/anabolism is treated as a surface function and destruction/catabolism as a volume function, with growth equations derived from those assumptions. The record does not expose the equation text, equation numbering or page-level definitions. The common later shorthand \(dW/dt=aW^{2/3}-bW\) must therefore not be represented as a verified transcription of the 1938 paper on this evidence alone.

**Disposition:** source lead only. Directly inspect the primary article to identify the original size/mass variable, geometric assumptions, coefficients and equation/page before considering a candidate.

No new equation was accepted. These checks refine provenance and prevent later textbook conventions from being back-attributed to the original papers.


### 5.4 Pütter–von Bertalanffy growth lineage: attribution and model unit

A primary-source lead for the generalized growth law predates von Bertalanffy's 1938 paper: Pütter (1920), *Studien über physiologische Ähnlichkeit VI. Wachstumsähnlichkeiten*, Pflügers Archiv 180, 298–340, DOI https://doi.org/10.1007/BF01755094. Later reviews transcribe the generalized mass-growth equation as

\[
\frac{dm}{dt}=p m^a-q m^b,
\]

and attribute this general two-power form to Pütter. Von Bertalanffy's contribution is more specifically associated with a mechanistic anabolism/catabolism interpretation and the choice of surface-like and mass-like scaling exponents (classically \(2/3\) and 1), yielding a special case of the generalized Pütter form. The integrated length-at-age curve is a derived solution/observable under additional geometric and length–mass assumptions, not an independent governing equation.

The available evidence here is still secondary for the exact Pütter 1920 equation transcription and page. It is sufficient to correct the source lineage and prevent treating the generalized Pütter law and the classical von Bertalanffy special case as unrelated equation families. The 1938 primary article's own equation number/page and definitions remain to be checked directly.

**Disposition:** group the generalized Pütter growth law and the classical \(a=2/3,b=1\) von Bertalanffy mass-growth specialization as one provisional lineage (E2/specialization pending primary transcription); keep other exponent pairs as parameterized members of that general family unless the complete mechanism/state contract establishes a different model unit. Do not count the integrated length-at-age curve separately.

### 5.5 Holling 1959 evidence boundary

The original 1959 article's accessible abstract transcribes the saturating count relation as \(y=Ttax/(1+abx)\), with the paper's own notation and definitions for search period, disk density, discovery rate and handling time. It then reports an S-shaped rise in the small-mammal experiment and states that an additional component, apparently stimulation of searching by each prey found, was still being investigated. Thus the article supports the saturating functional-response mechanism but does not establish a fully specified Type III equation from this abstract. Keep the Holling S-curve observation as an unresolved mechanistic lead, not a candidate equation or distinct family.
