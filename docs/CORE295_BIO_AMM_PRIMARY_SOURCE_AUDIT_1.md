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

## 1A. Pütter (1920): direct equation/page transcription

The Fisheries Research Board of Canada Translation Series No. 325 (1960) reproduces Pütter's 1920 German paper, *Studien über physiologische Ähnlichkeit VI. Wachstumsähnlichkeiten* (Pflügers Archiv 180, 298–340). The translation's printed pp. 299–300 (PDF pp. 2–3) explicitly states:
- theoretical linear dimension \(\lambda=\sqrt[3]{G}\), where \(G\) is body weight;
- anabolic construction rate proportional to \(\lambda^2\);
- catabolic destruction rate proportional to \(\lambda^3\);
- net increment \(d\lambda/dt=k_1\lambda^2-k_2\lambda^3\);
- limiting dimension \(L=k_1/k_2\), obtained by setting net increment to zero.

This is the directly transcribed governing relation. The familiar mass form with exponents \(2/3\) and \(1\) follows by the chain rule from \(G=\lambda^3\), with coefficient rescaling; it is not a second independent model. Pütter's integrated length expression on printed p. 300 is a solution of the same ODE, not another candidate. The translation's OCR corrupts some equation glyphs, so the explicit differential relation above is reconstructed from the surrounding verbal definition and the displayed powers; confirm the exact original typeset notation from the German scan before claiming a verbatim transcription.

Source: https://waves-vagues.dfo-mpo.gc.ca/Library/147555.pdf (translation pp. 299–300; PDF pp. 2–3). Original DOI: https://doi.org/10.1007/BF01755094.

**Disposition:** strong primary-lineage evidence for the surface/volume growth mechanism; keep the generalized arbitrary-exponent Pütter–Bertalanffy equation as a later family generalization, not a verbatim Pütter (1920) formula. Keep the cube-root length ODE, its mass-variable transform and its integrated solution in one source family; do not count them separately.

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

A Fisheries Research Board of Canada translation of Pütter's original 1920 article is available and has now been inspected. The paper defines a theoretical linear dimension \(\lambda\) as the cube root of weight. It assumes catabolic breakdown proportional to \(\lambda^3\) and anabolic construction proportional to \(\lambda^2\), so the net increment is proportional to \(k_1\lambda^2-k_2\lambda^3\). At the limiting size \(L\), the two terms balance, giving \(k_1L^2=k_2L^3\), hence \(L=k_1/k_2\). The paper then gives an integrated growth curve for the theoretical linear dimension (its equation (3)); the OCR available here does not make every symbol in that expression reliable enough for a verbatim transcription.

Primary source: Pütter (1920), *Studien über physiologische Ähnlichkeit VI. Wachstumsähnlichkeiten*, Pflügers Archiv 180, 298–340, DOI https://doi.org/10.1007/BF01755094; Fisheries Research Board of Canada Translation Series No. 325 (1960), especially the discussion on original pp. 299–301: https://waves-vagues.dfo-mpo.gc.ca/Library/147555.pdf. The translation explicitly identifies the original title, journal, volume, pages and 1920 date.

This verifies Pütter's particular surface-versus-volume mass-balance model. It does **not** establish that the arbitrary-exponent generalization \(dm/dt=p m^a-q m^b\) appears in the 1920 paper; that broader form is a later generalized family and must not be back-attributed without direct source evidence. The classical von Bertalanffy mass-growth form with exponents \(2/3\) and 1 is closely related to the surface/volume mechanism, but the 1938 article's exact equation number/page and notation still require direct inspection. The integrated length-at-age curve is a derived solution/observable under geometric and length–mass assumptions, not an independent governing equation.

**Disposition:** register Pütter 1920 as a primary source for the specific surface/volume balance and associated growth curve. Keep later arbitrary-exponent Pütter/Bertalanffy generalizations in a related lineage, but do not claim they are verbatim 1920 equations. Do not count the integrated curve separately from its governing model.

### 5.5 Holling 1959 evidence boundary

The original 1959 article's accessible abstract transcribes the saturating count relation as \(y=Ttax/(1+abx)\), with the paper's own notation and definitions for search period, disk density, discovery rate and handling time. It then reports an S-shaped rise in the small-mammal experiment and states that an additional component, apparently stimulation of searching by each prey found, was still being investigated. Thus the article supports the saturating functional-response mechanism but does not establish a fully specified Type III equation from this abstract. Keep the Holling S-curve observation as an unresolved mechanistic lead, not a candidate equation or distinct family.


## 6. Biology: primary and later functional-response/growth evidence

### 6.1 Holling Type II versus later Type III formulation

The 1959 Holling article's abstract transcribes the experimental saturating relation as \(y=Ttax/(1+abx)\), where \(x\) is disk density, \(Tt\) the search period, \(a\) the instantaneous discovery rate, and \(b\) handling time. Its separate small-mammal result is described as S-shaped, but the abstract says a search-stimulation component was still being investigated. That observation is not a complete Type III equation.

A later primary model paper, Real (1977), explicitly generalizes the organismal-interaction formulation to Type III and presents an equation intended to account for both Type II and Type III responses. It attributes the sigmoid transition to learning/encounter effects and includes maximal feeding rate, affinity/handling terms and an encounter-count parameter. This is a much better primary equation lead for Type III than assigning the 1959 observed S-curve a formula it did not yet specify.

Sources: Holling (1959), DOI https://doi.org/10.4039/Ent91385-7; Real (1977), *The Kinetics of Functional Response*, The American Naturalist 111(978), 289–300, DOI https://doi.org/10.1086/283161.

**Structural disposition:** Holling's saturating Type II response and Real's generalized Type II/III interaction model share a family lineage but may differ in the full organismal encounter-state contract. Under draft E3/E4, do not count them as distinct scalar equations merely by response label; inspect Real's full equation and mechanism before deciding whether the encounter-history state is irreducible at the chosen benchmark unit. The Type III family is now a traceable primary-source lead, not yet an accepted candidate.

### 6.2 Pütter 1920 and von Bertalanffy 1938: equation lineage boundary

The Pütter 1920 translated primary text directly supports a surface/volume balance: define theoretical linear dimension \(\lambda=W^{1/3}\), assume construction proportional to \(\lambda^2\) and destruction proportional to \(\lambda^3\), then the net mass increment is proportional to \(k_1\lambda^2-k_2\lambda^3\). It derives the limiting dimension \(L=k_1/k_2\) and an integrated growth curve. The translation is Fisheries Research Board of Canada Translation Series No. 325 (1960), based on the 1920 German article, original pp. 298–340: https://waves-vagues.dfo-mpo.gc.ca/Library/147555.pdf.

Later literature writes a generalized Bertalanffy–Pütter family \(dm/dt=p m^a-qm^b\), but this generalized arbitrary-exponent form must not be attributed verbatim to Pütter 1920 solely from the specific surface/volume derivation. Likewise, the familiar weight law \(dW/dt=H_1W^{2/3}-H_2W\) and integrated cube-root length curve are linked by assumptions and solution; they are not independent candidates. A 2013 fisheries model review notes the Pütter 1920 lineage and the later von Bertalanffy rediscovery; a later meta-study formalizes the generalized exponent-pair family.

Sources: Pütter (1920), DOI https://doi.org/10.1007/BF01755094 and translation above; von Bertalanffy (1938), *Human Biology* 10(2), 181–213, https://www.jstor.org/stable/41447359; supporting lineage discussion: https://www.osti.gov/servlets/purl/6163660 and https://pmc.ncbi.nlm.nih.gov/articles/PMC7451746/.

**Disposition:** keep the original Pütter surface/volume balance, the von Bertalanffy mechanistic interpretation, generalized exponent-pair model and integrated length-at-age curve in a single related lineage for pairwise E0–E4 review. Do not accept multiple counts for the ODE, its parameterized special case, and its integrated curve. Exact 1938 equation/page transcription remains open because the primary article's full text was not available in the accessible sources.

## 7. DeFi Risk: Compound Comet specification/implementation version audit

### 7.1 Pinned source snapshot

A reproducible GitHub snapshot was fetched at commit f766f51583c23acc33b2a7824654ef2029a96804 (2026-06-23; development repository snapshot). At that commit:
- SPEC.md blob SHA: 0a9fb98d505b57494ce2d6ec437c21ae90360091
- contracts/CometWithExtendedAssetList.sol blob SHA: 3490e984d133789aa1afe2e8f7e37a11d2512396
- Commit: https://github.com/compound-finance/comet/commit/f766f51583c23acc33b2a7824654ef2029a96804
- Pinned spec: https://github.com/compound-finance/comet/blob/f766f51583c23acc33b2a7824654ef2029a96804/SPEC.md
- Pinned contract: https://github.com/compound-finance/comet/blob/f766f51583c23acc33b2a7824654ef2029a96804/contracts/CometWithExtendedAssetList.sol

### 7.2 AbsorbInternal reconstruction and specification/code discrepancy

The pinned SPEC describes the liquidation/absorption sequence as: require liquidatability; read signed account principal and present value; iterate the account's collateral assets; zero the user's collateral and credit seized collateral to the protocol account; add collateral value multiplied by a liquidation-penalty factor to the account balance; record reserve deficit/debt-repaid diagnostics; clamp the resulting balance at zero and convert it back to principal; update the account base balance; increase aggregate supply principal and decrease aggregate borrow principal. The external absorb wrapper accrues interest, loops over accounts and pays an absorber incentive.

The pinned Solidity implementation is not a line-for-line realization of those exact spec operations. Its absorbInternal:
1. checks isLiquidatable, reads signed principal and presentValue;
2. iterates the account's assetsIn bitset and obtains each asset's liquidationFactor;
3. zeros the user's collateral balance and decrements totalsCollateral[asset].totalSupplyAsset;
4. computes value = mulPrice(seizeAmount, getPrice(priceFeed), scale) and adds mulFactor(value, liquidationFactor) to deltaValue;
5. converts deltaValue into base units, adds it to the old signed base balance, and clamps a negative result to zero;
6. converts to new principal, updates the account, resets assetsIn/reserved flags, obtains repay/supply amounts through repayAndSupplyAmount, adjusts totalSupplyBase and totalBorrowBase, and emits debt/collateral events.

Notably, the SPEC's explicit credit of seized collateral to a protocol-owned collateral account and its LiquidationPenalty notation do not appear in that same form in this implementation; the contract uses a liquidationFactor, and its collateral accounting is implemented through token-balance/total-collateral bookkeeping. Do not assume liquidationFactor = 1 + liquidationPenalty or that the specification and this implementation are interchangeable without a precise version/configuration mapping. This is a substantive model/provenance mismatch, not cosmetic wording.

**Disposition:** the full absorption state transition is a strong DeFi Risk system-level candidate lead, but no scalar piece (liquidatability predicate, seize value, debt clamp, principal conversion, reserve update or absorber reward) is independently countable. Before any formal candidate, pin the exact deployed release/market configuration and reconcile the spec-to-contract accounting semantics. The 2026-06 development snapshot is a reproducible source snapshot, not proof of any specific production deployment. No chain/RPC/API query was made.

## 8. DeFi AMM: Solidly implementation gate

The official Solidly V2 documentation specifies volatile \(xy\geq k\) and stable \(x^3y+xy^3\geq k\). The stable polynomial is a plausible separate invariant family from constant product and Curve StableSwap, but the documentation page does not specify the complete implementation-level quote contract: decimal normalization, fee source/application, integer scaling, rounding and exact reserve variables. A generic third-party adapter description also notes that Solidly V2 swap quotes depend on the pool's stable flag, token decimals and factory fee read, and that storage layouts are fork-specific; it is not the protocol's primary implementation.

Sources: official formula documentation https://docs.solidly.com/dex-basics/swaps.html; adapter-level corroboration https://docs.rs/evm-amm-state/latest/evm_amm_state/adapters/solidly_v2/struct.SolidlyV2Adapter.html.

**Disposition:** retain one stable-invariant family lead and one volatile constant-product exclusion. No Solidly equation accepted until the exact source repository/contract revision and the decimal/fee implementation are pinned. Do not use fork code or third-party adapter code as a substitute for the protocol's own source.


## 3A. Solidly-derived stable AMM: pinned implementation audit

A primary implementation is now pinned from the official Velodrome Finance V2 contracts repository:
- Repository: https://github.com/velodrome-finance/contracts
- Commit: https://github.com/velodrome-finance/contracts/commit/b3065d8b6702b14b094f9f6046b752cc9f78c43b (2025-12-18)
- File: https://github.com/velodrome-finance/contracts/blob/b3065d8b6702b14b094f9f6046b752cc9f78c43b/contracts/Pool.sol
- Blob SHA: `91412c378bba4d8076271cee52e1397b1520b709`

Implementation details from `Pool.sol`:
1. `initialize` stores token decimal scales as \(10^{decimals_i}\).
2. Stable `_k` normalizes raw reserves to 1e18 units, computes \(a=xy/10^{18}\), \(b=(x^2+y^2)/10^{18}\), and returns \(ab/10^{18}\). In real arithmetic this is the polynomial \(x^3y+xy^3\), scaled by \(10^{54}\); integer division introduces truncation at intermediate stages.
3. Stable `_getAmountOut` obtains the pre-swap invariant, normalizes reserves and input to 1e18 decimal-adjusted units, solves the output reserve with `_get_y`, then rescales output to raw token units.
4. `_get_y` uses a bounded Newton–Raphson iteration (maximum 255 iterations) over the stable polynomial and handles one-unit rounding cases explicitly.
5. `getAmountOut` deducts the factory-provided pool fee in basis points before calling the quote routine. The fee source is external factory state, not part of the invariant itself.
6. Volatile mode instead uses \(xy\) and the constant-product quote.

**Scope warning:** this is the official Velodrome V2 implementation, a partial rewrite/redesign of the Solidly architecture; it is not evidence that every Solidly fork or original Solidly deployment uses identical code, decimal scaling, fee configuration or rounding. The documentation's bare polynomial is not a complete benchmark contract. The pinned Pool.sol plus a pinned factory fee implementation is much closer to one, but market-specific factory/pool deployment configuration remains unpinned. Do not call this original Solidly implementation or count volatile mode separately from the Core-15 constant-product exclusion. Keep one stable polynomial family lead, subject to cross-family structural review and an explicit integer-arithmetic benchmark adapter.

No live chain calls, RPC, contract simulation or tests were performed.


### 3A.1 Factory fee source pinned

The paired factory implementation is pinned at the same repository commit:
- File: https://github.com/velodrome-finance/contracts/blob/b3065d8b6702b14b094f9f6046b752cc9f78c43b/contracts/factories/PoolFactory.sol
- Blob SHA: `6a415031333011c4bb1196eabeeaf3b5f8deb0b2`
- `PoolFactory.getFee(pool, stable)` returns a per-pool custom fee when configured, otherwise the stable/volatile default; sentinel `ZERO_FEE_INDICATOR=420` explicitly represents a zero-fee override.
- Constructor defaults are 5 basis points (0.05%) for stable pools and 30 basis points (0.30%) for volatile pools. `setFee` allows the fee manager to change nonzero defaults up to 300 basis points (3%); `setCustomFee` permits per-pool overrides and the zero-fee sentinel.

This resolves the source-code fee-selection rule, but not the runtime fee of any particular pool: that requires the actual factory and pool state at a specified block/deployment. No chain calls were made. Keep default constructor values distinct from market-specific deployed configuration.


## Real (1977) functional response: provenance boundary and equation lead

The publisher record for Real's article confirms its scope and abstract: an allosteric-enzyme-kinetics analogy generalizes Type II into learning/encounter-dependent Type III behaviour, with maximal feeding rate \(F\), affinity \(G\), and encounter number \(n\). A search result that appeared to be a full-text copy was a false positive: opening it shows Harvey J. Gold's 1978 *Biosystems Modeling* volume, which reproduces only Real's abstract on p. 120; it is not the 1977 article and contains no equation transcription. The publisher full text remains access-restricted.

An open 2013 Oecologia paper explicitly attributes the generalized density-response form
\[
F_{ij}=\frac{a_{ij}N_i^{q+1}}{1+a_{ij}h_{ij}N_i^{q+1}}
\]
to Holling (1959), Real (1977), Hassell (1978), Rall et al. (2008), and Vucic-Pestic et al. (2010b). In that paper, \(q=0\) gives the hyperbolic Type II form and \(q=1\) the sigmoid Type III form. This is useful equation-level secondary evidence for a generalized Holling/Real lineage, but it does not establish that this exact notation or parameterization is printed verbatim in Real (1977), nor does it transcribe Real's abstract's distinct \((F,G,n)\) allosteric-kinetics expression. Keep the generalized exponent family and Real's encounter-history mechanism linked but provenance-distinct until the primary paper is inspected.

**Catalogue disposition:** retain Real as a high-priority source lead, not equation-ready. Do not accept the generalized power-law expression as a direct Real transcription. Do not count Type II/III parameter limits or exponent choices as separate families without applying the structural-equivalence review to the complete governing model.


## von Bertalanffy (1938): full-text retrieval false positive and equation status

A search result labelled as a PDF of *A Quantitative Theory of Organic Growth* (1938) was opened and found to be an unrelated 1987 Russian fisheries proceedings volume; the Bertalanffy article appears only in its bibliography. The JSTOR stable-PDF URL redirects to the article record rather than exposing the paper text in this retrieval path. The bibliographic identity and abstract-level mechanism are corroborated by the article record and secondary records: growth is modelled as construction proportional to surface and destruction proportional to volume. This supports the Pütter-lineage interpretation, but it does not provide a direct transcription of von Bertalanffy's 1938 equation, numbered equation, or page.

**Catalogue disposition:** keep the 1938 article as a primary-source lead only. Do not backfill its equation from the 1957 generalization, from Pütter (1920), or from later fisheries parameterizations. The direct original equation/page remains unresolved; the Pütter 1920 equation already transcribed above is a separate historically earlier primary source within the same broad surface–volume growth lineage.


## 3B. Curve StableSwap NG: pinned implementation audit

**Pinned source:** official repository `curvefi/stableswap-ng`, commit `3332cd44656ec64b3c048885e1dd71955254b262`. The main pool source is `contracts/main/CurveStableSwapNG.vy` (blob `f192932a22958735acad4ca24c977cc4e058f1aa`); the associated math helper is `contracts/main/CurveStableSwapNGMath.vy` (blob `25acc73e8b5cf0a0652bf833d7a1d9cd22cf83c5`). The repository README describes permissionless plain/metapool deployment, up to eight coins in plain pools and two in metapools, and identifies the implementation contract and factory/blueprint deployment pattern.

### Invariant and numerical solution

The implementation's `get_D` comment states the N-coin StableSwap invariant in the form
\[
A\,n^n\sum_i x_i + D
=
A\,n^n D + \frac{D^{n+1}}{n^n\prod_i x_i},
\]
with the implementation's amplification integer scaled by `A_PRECISION = 100`. The state variables used in the invariant are not raw token balances: `_xp_mem` constructs normalized balances as \(x_i=\lfloor r_i b_i/10^{18}\rfloor\), where \(b_i\) is the pool balance net of admin balances and \(r_i\) is the stored rate. Rates can incorporate external rate oracles or ERC-4626 `convertToAssets` calls. The active amplification is linearly ramped between initial and future values according to timestamps.

The integer solver initializes \(D=\sum_i x_i\), iteratively computes the product term \(D_P\), and updates \(D\) using the source's rational recurrence. It allows up to 255 iterations and returns when successive integer values differ by at most one. The output-balance solver `get_y` solves the corresponding quadratic relation by Newton iteration, also with a 255-iteration cap and one-unit convergence threshold. These are implementation-specific integer algorithms for the same StableSwap invariant, not additional invariant families.

### Swap fee and state handling

The swap path:
1. reads stored balances and normalized rates;
2. applies the received input to normalized balance \(x_i\);
3. computes invariant \(D\) and solves the output reserve \(y_j\);
4. subtracts one unit as a rounding guard;
5. calculates the off-peg dynamic fee from the average pre/post normalized balances;
6. converts net output back using the output token's rate, with integer truncation;
7. accrues the admin share and updates the state-price and invariant EMAs.

For off-peg multiplier \(m>10^{10}\), the contract's dynamic fee is
\[
f_{dyn}=
\frac{m f_0}{
(m-10^{10})\,\frac{4x_i x_j}{(x_i+x_j)^2}+10^{10}},
\]
and it returns the base fee when \(m\leq10^{10}\). Fee denominator is \(10^{10}\); the admin share constant is 50% of the fee. The contract documentation explicitly warns that dynamic fee estimates can differ slightly from realized fees. Fee values, amplification, rates, and pool coin configuration are deployment state; the pinned source does not determine a universal deployed pool parameter set.

### Structural disposition and limitations

StableSwap NG is an implementation evolution of the 2019 StableSwap family, not a new invariant family merely because it adds normalized rate assets, dynamic fees, oracle state, rebasing-token handling, ERC-4626 support and revised integer arithmetic. Treat the invariant, fee policy, rate/oracle inputs and accounting as one protocol implementation contract when benchmarking executable pool behavior. Do not count the fee function, EMA, solver recurrence or one-coin withdrawal formula as independent equations. Do not assume every deployed pool uses this exact source revision: a candidate must bind a specific deployment, factory, pool configuration and block-state snapshot before any runtime fee or parameter claims. No chain/RPC calls or simulations were made.


## 3C. Curve Tricrypto NG: pinned CryptoSwap implementation audit

**Pinned source:** official `curvefi/tricrypto-ng` repository, commit `ecaa8161c240f21dd7c3712eefc5637e1dac742b`. Main pool `contracts/main/CurveTricryptoOptimizedWETH.vy`, blob `d1bf61fd3d6569d18acfc784bb6aeb34943de281`; math reference `contracts/reference/CurveCryptoMath3Reference.vy`, blob `55cca5446e6899b4b8e993c507b9e540422fc077`. The README describes a three-asset auto-rebalancing CryptoSwap implementation for unpegged assets and a factory/blueprint/math/views architecture. It identifies a deployed Ethereum Tricrypto pool as the lineage example, but this repository commit alone does not pin the bytecode/configuration of that or any other live deployment.

### Model state and numerical contract

The pool is explicitly three-coin. Its state includes balances, invariant \(D\), packed internal price scales, EMA price oracle, last prices, \(A\) and \(\gamma\) parameters (which can be ramped over time), fee parameters \((f_{mid},f_{out},fee_\gamma)\), rebalancing parameters and profit/virtual-price accounting. Balances are normalized by token precisions and the internal price scales before entering the math library. The pool delegates invariant and output-balance calculations to a separate math contract.

The reference math contract defines \(ANN=A N^N\) (with an implementation multiplier), \(\gamma\), normalized balances and \(D\) as the solver inputs. `newton_D` uses a three-coin geometric-mean-based initial estimate (or a prior \(K_0\) estimate), then a bounded Newton iteration with integer arithmetic and safety bounds on \(A,\gamma,D\), and normalized balances. `get_y` solves the output reserve; it uses a closed-form cubic-root path when numerically admissible and falls back to a bounded Newton method otherwise. The solver and its fallback are numerical implementations of the same CryptoSwap invariant, not separate model candidates.

### Dynamic fee and endogenous price-scale adjustment

The pool's `_fee` computes a state-dependent convex combination of mid-fee and out-fee using the math library's `reduction_coefficient(xp, fee_gamma)`. The pinned math code defines \(K=\prod_i(3x_i/\sum_jx_j)\) with 1e18 fixed-point normalization, then \(f=fee_\gamma/(fee_\gamma+1-K)\); the pool fee is \(f_{mid}f+f_{out}(1-f)\). Thus the fee moves between mid-fee and out-fee according to normalized pool balance composition. Swap execution normalizes the balances using precision and price-scale factors, solves the output reserve, deducts the dynamic fee, updates token balances, and calls \`tweak_price\`.

`tweak_price` updates the exponential moving-average price oracle from last trade prices, with a cap on the spot price admitted to the EMA. It computes the vector distance between the oracle and current price scale; only when the distance exceeds the configured adjustment step and the profit conditions are met does it move price scale toward the oracle, recompute \(D\), and update virtual price. This is an endogenous re-pegging/rebalancing state transition, not merely a static invariant with an unrelated oracle. Admin fees are accounted through the pool's profit/virtual-price mechanism; the source hardcodes a 50% admin-fee share.

### Structural disposition

CryptoSwap/Tricrypto NG is the implementation lineage for the 2021 CryptoSwap dynamic-peg model, distinct from the StableSwap near-parity invariant. Treat the coupled invariant, \(A,\gamma\), price-scale/oracle state, dynamic fee and re-pegging/profit logic as one governing protocol model. Do not split Newton solvers, fee reduction coefficient, EMA, virtual-price or rebalancing equations into separate equation counts. This is a three-coin optimized implementation snapshot; it must not be generalized automatically to two-coin CryptoSwap, older Tricrypto deployments, or every factory blueprint. Runtime values require a specific pool, factory/blueprint, chain and block-state pin. No chain/RPC calls, simulations or tests were performed.


## Frumkin (1925): primary-source archive cross-check and access boundary

The Moscow State University Electrochemistry Department's selected-papers archive lists the two relevant German-language records separately: Frumkin, *Die Kapillarkurve der höheren Fettsäuren und die Zustandsgleichung der Oberflächenschicht*, Z. Phys. Chem. 116 (1925), 466–484; and *Einige Bemerkungen zur Theorie der Adsorption und Verteilung*, Z. Phys. Chem. 116 (1925), 501–503 (the English-language archive labels the latter *On the Theory of Adsorption and Distribution*, 501–504). The archive exposes distinct PDF links for both records, but opening the higher-fatty-acid paper's PDF route returns an authorization-required login page rather than the scan.

The same department's 1914–1930 bibliography separately lists Frumkin's Russian collected-work version, *К вопросу о строении поверхностного слоя. Ч. III. Капиллярные кривые высших жирных кислот и управление состояния поверхностного слоя*, in *Сборник работ по чистой и прикладной химии* (1925), pp. 56–74. This is a plausible parallel primary-text retrieval route, but the bibliographic listing alone does not establish that its text is currently accessible or that it contains the exact same equation layout as the German article.

**Equation status unchanged:** the commonly reproduced Frumkin isotherm form remains secondary equation-level evidence. Neither the MSU bibliographic index nor the access-denied PDF route verifies the exact non-ideal interaction equation, notation, or printed page in the 1925 primary paper. Do not mark the candidate as directly transcribed or equation-ready until a readable original scan/translation is inspected. This cross-check strengthens the source identity and retrieval trail only.

Archive records:
- MSU selected Frumkin papers (entries for both 1925 articles): https://www.elch.chem.msu.ru/wp3/index.php/ru/articles/frumkinarticles/
- MSU 1914–1930 bibliography (Russian collected-work entry): https://www.elch.chem.msu.ru/wp3/index.php/ru/1914-1930/
- Direct MSU PDF route for the 466–484 article (currently authorization-gated): https://www.elch.chem.msu.ru/cgi-bin/getpdf.cgi?pdf=zpc1925.pdf


## 3D. DODO PMM: pinned Solidity pricing and numerical audit

**Pinned source:** official DODOEX/contractV2 repository at commit 2f1bcdac7ef1beee7599a756e2eed26732c2536d (latest repository commit available in the connector at review time; 2025-11-12). Relevant files:
- contracts/lib/PMMPricing.sol, blob SHA 257332467f7973b74f2ebae441a894c93d54a579
- contracts/lib/DODOMath.sol, blob SHA 8e4e6a1254afeab8bfe70ee552a1ebde2117423a
- contracts/lib/DecimalMath.sol, blob SHA 5a11899a9adf8b5f9cb90f9b46f9c06121f1d88e

Pinned source URLs:
- https://github.com/DODOEX/contractV2/blob/2f1bcdac7ef1beee7599a756e2eed26732c2536d/contracts/lib/PMMPricing.sol
- https://github.com/DODOEX/contractV2/blob/2f1bcdac7ef1beee7599a756e2eed26732c2536d/contracts/lib/DODOMath.sol
- https://github.com/DODOEX/contractV2/blob/2f1bcdac7ef1beee7599a756e2eed26732c2536d/contracts/lib/DecimalMath.sol

### Pricing law and piecewise trade integration

The implementation's PMM state is (i,K,B,Q,B0,Q0,R): guide price i, slippage curvature K, current base/quote inventories B,Q, target inventories B0,Q0, and discrete regime R in {ONE, ABOVE_ONE, BELOW_ONE}. The library does not implement one globally smooth quote expression. sellBaseToken and sellQuoteToken select among the R=1, R>1, and R<1 regions, split trades that cross the R=1 target boundary, and update the regime. The source caps certain computed outputs at the amount available to reach the target to guard against fixed-point precision error.

The DODOMath source documents the continuous marginal-price integral for a reserve variable V, moving from V1 to V2 relative to target V0:
\[
\mathrm{res}
=i(V_1-V_2)\left(1-K+K\frac{V_0^2}{V_1V_2}\right),
\]
for the stated ordering V0 >= V1 >= V2 > 0. The code evaluates this with 18-decimal fixed-point arithmetic and explicit K=0 handling. This is the integrated PMM curve, not an independent candidate beside its marginal-price law.

For a finite trade, _SolveQuadraticFunctionForTrade solves the corresponding quadratic reserve equation, handles K=0 and K=1 separately, selects the nonnegative root, and uses ceiling division in the final reserve calculation before returning the reserve difference. _SolveQuadraticFunctionForTarget inversely solves an equilibrium target update. These are inverse/implementation operators for the same PMM curve and state contract, not separate equation counts.

### State and implementation limits

adjustedTarget updates Q0 or B0 when the state is below or above target. getMidPrice uses the corresponding target/current reserve ratio and K to calculate a state-dependent marginal price. DecimalMath uses 1e18 fixed-point multiplication/division and floor/ceiling variants. The pinned library therefore adds concrete integer precision, rounding and regime-transition behavior beyond the documentation's real-valued presentation.

**Structural disposition:** this supports DODO PMM as one guide-price-anchored, inventory-sensitive, piecewise-integrated pricing/state model. Do not count marginal price, integrated quote, quadratic inverse, mid-price, target adjustment and the three R regimes as separate equations. It is not a static reserve-only constant-product invariant. However, the library snapshot alone does not establish which DODO pool type/version wraps it, nor any deployed pool's current i,K,B,Q,B0,Q0, fee or oracle configuration. Bind the intended DVM/DPP/DSP contract family and a versioned pool adapter before formal candidate acceptance. No chain/RPC calls or simulations were made.


## 4. Biology primary-source retrieval checkpoint: von Bertalanffy (1938) and Real (1977)

### von Bertalanffy, “A Quantitative Theory of Organic Growth” (1938)

The JSTOR issue contents now independently confirm the article's identity, title, author and pagination: *Human Biology* 10(2), May 1938, pp. 181–213. The publisher's issue page links directly to stable record 41447359. A separate bibliographic abstract describes the proposed mechanism as construction proportional to a surface function and destruction proportional to a volume function, and says growth equations are derived from those assumptions.

This is useful corroboration of the model's conceptual mechanism, but it is not a transcription of the primary differential equation. The apparent alternative PDFs already tested in the retrieval log were false positives (a 1987 proceedings volume containing only a bibliography entry). The JSTOR article record remains access-controlled in this review. Do not substitute the later 1957 synthesis, Pütter 1920, or later fisheries parameterizations for the 1938 equation. Keep the source as a high-priority primary lead; exact equation, notation and page remain unverified.

### Real, “The Kinetics of Functional Response” (1977)

The University of Chicago Press article record and issue contents confirm *The American Naturalist* 111(978), 1 March 1977, pp. 289–300. The publisher abstract says Real generalizes the organismal-interaction formulations underlying Holling Type II into a learning/encounter-dependent Type III model using an allosteric-enzyme analogy, with maximum feeding rate F, affinity G and encounter count n. The publisher page currently presents “Get Access”; the retrieved PDF endpoint resolves to that access page, not readable article pages.

An openly accessible later synthesis by Rosenbaum and Rall (2018) gives the generalized functional-response form and explicitly attributes the enzyme-kinetics formulation to Real (1977):
\[
F(N)=\frac{F_{\max}N^{1+q}}{N_{1/2}^{1+q}+N^{1+q}},
\]
with q controlling the Type-II-to-Type-III shape transition. The equivalent attack-rate parametrization is \(a=bN^q\), \(F(N)=bN^{1+q}/(1+bhN^{1+q})\). This is secondary equation-level corroboration and a useful retrieval clue, not proof that this notation or parameterization is verbatim from Real's original paper. Do not transcribe it as a direct Real quotation or accept the candidate until the original article's equation and page are inspected.

**Disposition:** both works remain primary-source leads rather than equation-ready entries. Their mechanisms are sufficiently supported to guide retrieval, but the original equation/page evidence gate remains open. No catalogue candidate was promoted, no source-count target was adjusted, and no experiment was run.

Retrieval and corroboration links:
- JSTOR 1938 issue contents and article record: https://www.jstor.org/stable/i40070616 and https://www.jstor.org/stable/41447359
- 1938 bibliographic abstract: https://eurekamag.com/research/029/761/029761670.php
- Real (1977) publisher article record/PDF endpoint: https://www.journals.uchicago.edu/doi/10.1086/283161
- Real (1977) publisher issue contents: https://www.journals.uchicago.edu/toc/an/1977/111/978
- Rosenbaum et al. open secondary equation-level discussion: https://pure.knaw.nl/portal/files/6764896/6543_Rosenbaum_AM.pdf


### 5.2.1 Russian parallel publication identified; equation transcription still open

A second primary-publication route is now identified: Frumkin's Russian-language paper “К вопросу о строении поверхностного слоя. Ч. III. Капиллярные кривые высших жирных кислот и управление состояния поверхностного слоя,” listed in *Сборник работ по чистой и прикладной химии*, Chemical Institute of L. Ya. Karpov, issue 4 (1925), pp. 56–74. The Russian Academy of Sciences / State Public Scientific-Technical Library catalogue identifies the complete 1925 volume as 233 pages and provides a PDF resolver URL. The MSU electrochemistry bibliography independently gives the title and page range. This is a potentially more accessible contemporaneous Russian publication of the same research programme, but its identity as a word-for-word parallel of the German journal article has not been established.

A second catalogue mirror has now been located through the Sverdlovsk Scientific Information Centre's GPNTB consolidated-catalogue interface. Its record describes issue 4 as dated 1 September 1925 and gives an extent of 231, [4] pages; it exposes a mirror filename `Resource-6567_Version-6678_application-pdf_0.pdf`. The mirror metadata page and direct download route also timed out or proved inaccessible to the retrieval service. This is not yet an additional scan. Its 231+[4]-page extent differs from the 233-page total in the earlier GPNTB catalogue record, so both descriptions are retained pending inspection of the physical/digital volume. Catalogue mirror: https://lib.dm-centre.ru/lib/gpntb/.

The MSU selected-papers page lists the German article (Z. Phys. Chem. 116, 466–484) but its PDF link currently resolves to a login/reprint-request screen. The De Gruyter DOI record confirms the German article's bibliographic identity and pagination but does not expose its text in the retrieved record. The GPNTB PDF endpoint was identified but could not be opened by the web retrieval service in this pass. No equation, sign convention or page-level definition has therefore been transcribed from the Russian volume yet.

**Disposition:** retain the Russian volume as a high-priority primary-source retrieval lead. Inspect printed pp. 56–74 (not PDF page indices) and compare its symbols, derivation and sign convention against the German pp. 466–484 before using it to resolve the Frumkin equation. Do not yet promote the familiar modern form (bc=\theta/(1-\theta)\exp(-2a\theta)) as an exact primary transcription.


## 4.1 Biology primary equations newly recovered: Verhulst (1838) and Gompertz (1825)

### Verhulst, “Notice sur la loi que la population suit dans son accroissement” (1838)

A scan-based English translation of Verhulst's original 1838 notice is now accessible. In the section introducing the population law, the text defines population \(p\), infinitesimal time \(dt\), and the increase \(dp\), first writing the Malthusian term and then the retarding function:

\[
\frac{dp}{dt}=mp-\phi(p),\qquad \phi(p)=np^2.
\]

The source gives the integrated relation

\[
t=\frac{1}{m}\left[\log p-\log(m-np)\right]+C,
\]

and states the limiting population \(P=m/n\). Crucially, Verhulst also discusses alternatives \(\phi(p)=np^\alpha\) and \(\phi(p)=n\log p\), and reports testing several forms. The logistic choice is the familiar quadratic-retardation case, not the whole set of hypotheses. The translation is scan-based and identifies the original notice as *Correspondance mathématique et physique* 10 (1838), pp. 113–121. A separate original French 1845 memoir is available through Persée as a page-image scan, but the 1838 translation is the source used for the directly readable transcription here.

**Disposition:** add the 1838 source to the Biology source register as provenance and Core-15 exclusion evidence. Logistic growth is already an explicit Core-15 exclusion, so do not add it as a new Core-295 equation or count the alternative retardation functions as independent models without separate primary-source and structural review.

### Gompertz, “On the nature of the function expressive of the law of human mortality” (1825)

An original scan of Gompertz's *Philosophical Transactions of the Royal Society of London* paper, volume 115, pp. 513–583, is now readable. In Article I, section 5, printed p. 518, Gompertz describes the age-dependent “intensity of mortality” as proportional to an exponential function of age, with historical notation transcribed as

\[
\mu(x)=a q^x,
\]

where \(a\) and \(q\) are constants. In the same passage he gives the corresponding number living at age \(x\) as \(L_x=d g^{q^x}\), and explicitly cautions that \(g\) is raised to the power \(q^x\), not merely to \(q\) and then to \(x\). The survivor-count expression is the integrated consequence of the mortality-intensity law in the model, not a second candidate. The common modern form \(\mu(x)=\alpha e^{\beta x}\) is a reparameterization, not the original printed notation. The OCR around the displayed survivor formula is noisy; the prose-defined intensity law is the primary transcribed expression.

**Disposition:** add one proposed demographic-survival equation record, with source-family tracking and no claim of acceptance. Its placement in Biology is provisional because the source is human demography/actuarial mortality; cross-domain structural review and scope review remain required. Do not conflate this mortality law with Gompertz growth curves. No experiment or validator was run.

Primary-source links:
- Verhulst 1838 scan-based translation: https://neo-classical-physics.info/uploads/3/4/3/6/34363841/verhulst_-_law_of_population.pdf
- Verhulst 1845 French memoir scan record: https://www.persee.fr/doc/marb_0770-8157_1845_num_18_1_3438
- Gompertz 1825 original scan: https://fileserver-az.core.ac.uk/download/pdf/14511273.pdf


## 4.2 Holling (1959b): original functional-response derivation and Watt comparison

The original scan of C. S. Holling, “Some Characteristics of Simple Types of Predation and Parasitism,” *The Canadian Entomologist* 91(7) (July 1959), pp. 385–398, is now accessible. On printed pp. 386–390, Holling derives the disc-search response from a constant instantaneous discovery rate \(a\), prey density \(x\), total time \(T_t\), and handling time \(b\):

\[
y=axT_s,\qquad T_s=T_t-by,
\]

so

\[
y=\frac{T_t a x}{1+abx} \tag{Holling 1959, Eq. 4}
\]

The paper then introduces an identification-time term \(c\), obtaining \(y=T_t a x/[1+(b+c)x]\) (Eq. 7) and \(a=a'/(1+a'cx)\) (Eq. 9). These are extensions/parameter decompositions of the same handling-time response, not separate candidates. The rational saturation form is algebraically the same normalized hyperbola as the Core-15 Michaelis–Menten family; retain this source as mechanism/provenance evidence and an explicit exclusion check.

The same paper is particularly useful for distinguishing Type II from Type III. Holling says the S-shaped responses observed for small mammals cannot be described by Eq. (4), because that equation has a continuously decreasing slope; he reports that an additional prey-stimulated searching component may be involved, but that experiments were then still underway. Therefore this 1959b article does **not** supply the later allosteric/encounter Type III equation attributed to Real (1977).

Holling also reproduces Watt's distinct exponential response as Eq. (11),

\[
N_a=PK\left(1-e^{-aN_0P^{1-b}}\right),
\]

and, for fixed predator density, reduces it to Eq. (12),

\[
y=K'\left(1-e^{-a'x}\right),
\]

which is equivalent to the differential relation \(dy/dx=a'(K'-y)\) printed in the same comparison. Holling attributes this model to K. E. F. Watt (1959) and notes its connection to Gause (1934). This exponential saturation has a different normalized functional form from the rational Holling Eq. (4), but the original Watt paper (pp. 129–144) remains access-gated in the publisher record. Keep Watt as a primary-source retrieval lead, not a directly transcribed or accepted candidate until its own article is inspected.

**Disposition:** add the Holling scan and Watt retrieval lead to the source register. No Holling Type II candidate is added because of the Core-15 Michaelis–Menten structural exclusion; no Watt candidate is added until its original source is checked. Do not count Holling's Eq. (7), Eq. (9), or fixed-predator-density specializations as additional independent equations. No experiments or validators were run.

Primary and retrieval links:
- Holling 1959b original scan: https://hahana.soest.hawaii.edu/cmoreserver/summercourse/2010/documents/Holling_1959b.pdf
- Holling 1959b publisher record: https://doi.org/10.4039/Ent91385-7
- Watt 1959 original publisher record: https://doi.org/10.4039/Ent91129-3


## 4.3 Lotka (1920): original coupled plant–herbivore system

The publisher-hosted full text of A. J. Lotka, “Analytical Note on Certain Rhythmic Relations in Organic Systems,” *Proceedings of the National Academy of Sciences* 6(7) (15 July 1920), pp. 410–415, is now accessible. Lotka starts with a plant species \(S_1\) drawing nourishment from an effectively constant source and a herbivore species \(S_2\) feeding on \(S_1\). The original equations (5)–(10), printed in the article, reduce to the coupled system

\[
\frac{dX_1}{dt}=X_1\left(A_1-B_1X_2\right),\qquad
\frac{dX_2}{dt}=X_2\left(A_2X_1-B_2\right),
\]

where Lotka explicitly states that \(A_1,A_2,B_1,B_2\) are, in general, functions of both \(X_1\) and \(X_2\). The components are mechanistically distinguished: plant formation, plant rejection/waste, plant loss through herbivory, conversion of consumed plant matter into herbivore growth, and herbivore loss. The original paper gives the equilibrium \(X_1=B_2/A_2\), \(X_2=A_1/B_1\), and analyzes the oscillatory behavior around it. The constant-coefficient textbook Lotka–Volterra system follows when these coefficient functions are fixed constants; that restriction must not be counted as a second equation.

**Disposition:** record as a primary-source lead and direct equation transcription. Do not yet create a proposed catalogue equation entry: the original leaves four constitutive coefficients as general state-dependent functions, so a benchmarkable instance would require a separately sourced and explicitly specified constitutive closure. Do not replace the source's general system with a later textbook constant-coefficient form and call that the verbatim 1920 model. The publisher HTML provides the article text and equation numbers; the PDF endpoint exists, but this transcription uses the publisher's readable full-text HTML. No experiment or validator was run.

Primary source: https://www.pnas.org/doi/10.1073/pnas.6.7.410


## 4.4 Volterra (1926): n-species conservative interaction system

An author-expanded reprint of Vito Volterra's 1926 Lincei memoir is now accessible as a scan-based PDF. Its opening editorial note states that Parts I–III rearrange and add to the work previously published in *Memorie della R. Accademia Nazionale dei Lincei*, series VI, vol. II (1926), pp. 31–113; Part IV reprints separate 1927 notes. The reprint therefore provides a direct authorial primary-source route to the 1926 model, while the 1927 reprint date and its expanded status must remain explicit.

In Part II, §2, printed pp. 38–39, Volterra derives the general n-species system (equation B):

\[
\beta_r\frac{dN_r}{dt}=\left(\varepsilon_r\beta_r+\sum_{s=1}^{n}a_{sr}N_s\right)N_r,
\qquad r=1,\ldots,n,
\]

with

\[
a_{rs}=-a_{sr},\qquad a_{rr}=0,\qquad \beta_r>0.
\]

The coefficients encode reciprocal encounter effects. Volterra describes the conservative association in terms of a weighted value assigned to individuals: the antisymmetric interaction contribution cancels in the derivative of the aggregate weighted value, although the intrinsic \(\varepsilon_r\) growth/depletion terms need not vanish. The source explicitly identifies the two-species feeding system in Part I, §2 as a special case of this general n-species form. It also treats chains of species feeding on one another, conservative and dissipative associations, forced environmental fluctuations, and adding a new species to an existing association.

**Disposition:** add one proposed n-species conservative-interaction candidate. Do not separately count the two-species Volterra feeding equations or the constant-coefficient Lotka–Volterra special case. This family is related to Lotka's independently published 1920 two-species plant–herbivore system, but its arbitrary n-dimensional antisymmetric interaction matrix and weighted-conservation constraint warrant a separate structural review. Acceptance remains pending; no benchmark ranges or generator are defined. No experiment or validator was run.

Primary scan: https://francesco-ferraro.com/lotka-volterra/volterra1927variazioni.pdf
Bibliographic corroboration for the original 1926 Lincei memoir: https://ndlsearch.ndl.go.jp/books/R100000136-I1574231874580495104


## 4.5 Nicholson–Bailey (1935): discrete-generation host–parasitoid source lead

The primary publisher record for A. J. Nicholson and V. A. Bailey, “The Balance of Animal Populations.—Part I,” *Proceedings of the Zoological Society of London* 105(3) (September 1935), pp. 551–598, is confirmed. Its abstract describes random searching, host–parasitoid interactions, steady-state analysis, discontinuous interactions, and multiple parasite/host configurations. The Wiley/Zoological Society PDF and ePDF endpoints were not accessible in this retrieval pass; no equation or page-level transcription from the original article has been completed.

The commonly reproduced discrete-generation system is

\[
H_{t+1}=\lambda H_t e^{-aP_t},\qquad
P_{t+1}=H_t\left(1-e^{-aP_t}\right),
\]

but this formula is retained here only as a retrieval target, not as a primary transcription. The original paper must be inspected for exact variable definitions, whether parasitoid progeny yield is normalized to one or separately parameterized, timing convention, and the derivation from the Poisson zero-attack probability. Later versions add density dependence, aggregation, handling/egg limitation or stage structure and must not be conflated with the original.

**Disposition:** add the publisher record as a primary-source retrieval lead only. Do not add an equation candidate or count later textbook notation as the 1935 original until the source PDF or a faithful scan is obtained. This is a discrete-generation host–parasitoid model and is structurally different from the continuous-time Lotka/Volterra predator–prey systems, subject to formal review. No experiment or validator was run.

Primary publisher record: https://doi.org/10.1111/j.1096-3642.1935.tb01680.x
