# Core-295 candidate discovery — batch 3: verified physics locations and biology source leads

**Consolidated bibliography:** [CORE295_REFERENCES.md](CORE295_REFERENCES.md). This reference list collects the literature and source links used across all Core-295 discovery batches and the catalogue plan.

**Status:** discovery and source verification only. No equation in this document is accepted, counted toward 295, or certified as an independent statistical unit.

This batch records exact OpenStax equation locations for additional physics mechanisms and a more specific biology source map. It deliberately distinguishes a verified chapter-level source from verification of a candidate's full scientific assumptions and benchmark suitability.

## Physics: exact equation locations verified

Primary source: Ling, Moebs and Sanny, *University Physics Volume 2*, OpenStax (2016). The following chapter key-equation pages expose the equations directly.

| Discovery lead | Relation as printed/defined by source | Exact source location | Review required before acceptance |
|---|---|---|---|
| Motional emf | `epsilon = B*l*v` | [Chapter 13, Key Equations](https://openstax.org/books/university-physics-volume-2/pages/13-key-equations) | Uniform field, conductor length perpendicular to velocity/field as specified by geometry; scalar magnitude only. Distinguish from Faraday flux law, which is the broader mechanism. |
| Rotating-generator emf | `epsilon(t) = N*B*A*omega*sin(omega*t)` | [Chapter 13, Key Equations](https://openstax.org/books/university-physics-volume-2/pages/13-key-equations) | Fixed uniform field and rotating coil geometry; phase convention and units. Related to electromagnetic induction/Faraday family. |
| Mutual-inductance response | `epsilon_1 = -M*d(I_2)/dt` | [Chapter 14, Key Equations](https://openstax.org/books/university-physics-volume-2/pages/14-key-equations) | Coupled-circuit assumptions, sign/orientation convention and fixed mutual inductance. Same inductive-coupling family as other Chapter 14 entries. |
| Inductor energy | `U = (1/2)*L*I^2` | [Chapter 14, Key Equations](https://openstax.org/books/university-physics-volume-2/pages/14-key-equations) | Linear inductor and energy reference; distinguish energy relation from dynamic circuit response. |
| RL step response | `I(t) = (epsilon/R)*(1 - exp(-t/tau_L))`, `tau_L = L/R` | [Chapter 14, Key Equations](https://openstax.org/books/university-physics-volume-2/pages/14-key-equations) | Initial condition, constant source and ideal lumped circuit. Treat the response and its time constant as one derivation family, not two independent units. |
| Damped RLC charge response | `q(t) = q0*exp(-R*t/(2*L))*cos(omega_prime*t + phi)` | [Chapter 14, Key Equations](https://openstax.org/books/university-physics-volume-2/pages/14-key-equations) | Underdamped regime only; verify `omega_prime` real and positive. Distinct damped-oscillator structure, but shares the RLC circuit family with its frequency relation. |
| RLC impedance | `Z = sqrt(R^2 + (X_L - X_C)^2)` | [Chapter 15, Key Equations](https://openstax.org/books/university-physics-volume-2/pages/15-key-equations) | Series RLC steady-state sinusoidal regime; define angular frequency and component idealizations. |
| RLC phase angle | `phi = atan((X_L - X_C)/R)` | [Chapter 15, Key Equations](https://openstax.org/books/university-physics-volume-2/pages/15-key-equations) | Same series RLC steady-state family as impedance; phase branch and sign convention must be explicit. |
| Resonant angular frequency | `omega_0 = sqrt(1/(L*C))` | [Chapter 15, Key Equations](https://openstax.org/books/university-physics-volume-2/pages/15-key-equations) | Ideal series RLC resonance; do not count alternate quality-factor/resonance restatements as separate independent units. |
| Transformer voltage ratio | `V_S/V_P = N_S/N_P` | [Chapter 15, Key Equations](https://openstax.org/books/university-physics-volume-2/pages/15-key-equations) | Ideal transformer assumptions and turns/voltage convention; distinguish ideal ratio from loss-inclusive models. |

### Physics curation decision

These are source-verified discovery leads, not ten independent observations. In particular:

- Chapter 13 entries share electromagnetic-induction foundations.
- Chapter 14 entries share inductance/circuit dynamics; the RL response and time constant form one model family, and the RLC response and damped frequency form another.
- Chapter 15 impedance, phase and resonance are all series-AC-circuit relations and must be source-family clustered.
- Formula appearance on a key-equations page does not itself establish structural novelty relative to the existing catalogue or suitability for the scalar Core-15 interface.
- The catalogue review must decide whether the benchmark target is a scalar response under a fixed, physically justified geometry/circuit configuration. Do not silently convert vector, integral, or system equations into scalar formulas by arbitrary assumptions.

## Biology: improved source map, exact equations still to retrieve

| Source lead | Specific source location/scope verified | Candidate model families to inspect | Current status |
|---|---|---|---|
| Mazumdar, *An Introduction to Mathematical Physiology and Biology*, Cambridge University Press (1999; online chapter pages 2012) | [Book contents](https://www.cambridge.org/core/books/abs/an-introduction-to-mathematical-physiology-and-biology/contents/967A19A933CCD802DD1A278C7FD16ECA): Chapters 2–10 cover diffusion, population biology, biogeography, pharmacokinetics, epidemiology, biological fluid mechanics, left-ventricular mechanics and heart-valve vibration. | Diffusion transport; population and spatial ecology; compartment pharmacokinetics; epidemic dynamics; flow and cardiac mechanics. | Chapter scope verified; individual equations, page numbers, assumptions and exact source equations remain unverified. |
| Mazumdar, Chapter 2 | [The Mathematics of Diffusion](https://www.cambridge.org/core/books/abs/an-introduction-to-mathematical-physiology-and-biology/mathematics-of-diffusion/F33AA5B77FEF96EEE9F89139A8589484) | Diffusion equations and defensible one-dimensional/steady-state reductions, if explicitly given by the source. | Chapter-level source only; PDE/scalar mapping requires review. |
| Daun et al., “Equation-based models of dynamic biological systems” (2008) | [Peer-reviewed review, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6698907/); its abstract defines coupled ODE systems `dx_i/dt = F(x_1,...,x_n,lambda_1,...,lambda_p,t)` and explains the well-mixed/continuous-state assumptions. | Physiological and clinical dynamic systems; inspect cited primary models and their equations. | Review source verified; the generic ODE template is not a distinct biological candidate. Trace every proposed model to primary literature before acceptance. |

### Biology curation decision

Do not create candidate records from chapter titles or from the generic ODE template. For each selected biological model, retrieve the actual equation and exact page/section, define state variables and units, state the biological assumptions and parameter regime, and trace review-derived models to the original paper or authoritative primary source. Coupled ODE/PDE systems must not be forced into a scalar regression benchmark without a predeclared and scientifically justified output mapping.

## Next review actions

1. Retrieve exact equations and primary-source citations from Mazumdar's diffusion, pharmacokinetics, population-biology and cardiovascular chapters.
2. Extract candidate models from Daun's review only as leads, then trace each to its cited primary paper.
3. For physics, assign provisional source-family IDs before symbolic equivalence review; do not count equations from the same circuit derivation as independent units.
4. Compare all leads against Core-15 and earlier Core-295 batches for duplicate mechanisms and algebraic restatements.
5. Populate the catalogue only after exact formula, units, assumptions, valid ranges, deterministic mapping, reviewer and provenance are complete.

**No equations in this document count toward the 295 target. No scientific experiments, paid compute, live API calls, or workflow dispatches were performed.**

## Biology: equation-level leads from a peer-reviewed tumor-dynamics review

A further accessible review provides an equation table with explicit model equations and cross-references to primary studies: [A Review of Mathematical Models for Tumor Dynamics and Treatment Resistance Evolution of Solid Tumors](https://pmc.ncbi.nlm.nih.gov/articles/PMC6813171/), Table 1, equations 1–8.

| Discovery lead | Equation reported in review | Review location | Curation status |
|---|---|---|---|
| Linear growth with first-order shrinkage | `dT/dt = k_g - d*T` | Table 1, Eq. 2 | Exact review-level equation found; trace cited primary study [21], verify biological interpretation, units and admissible T range. |
| Gompertz tumor growth | `dT/dt = k_g*T*ln(T_max/T)` | Table 1, Eq. 6 | Exact review-level equation found; trace primary studies [27, 29], verify parameterization and positive T regime. Do not count the alternate log-derivative Eq. 7 as a second unit without equivalence review. |
| Combined exponential-to-linear growth | `dT/dt = lambda_0*T / (1 + (lambda_0/lambda_1*T)^20)^(1/20)` | Table 1, Eq. 8 | Exact review-level equation found; trace primary study [31], verify the transition exponent and parameter units. Potentially distinct saturating growth mechanism, subject to symbolic comparison and source-family review. |

**Explicit exclusion:** Logistic tumor growth in Table 1, Eq. 5 is not a new Core-295 candidate because Core-15 already includes Logistic Growth. Generic exponential growth and the net-growth restatement in Eq. 4 also require careful comparison with other exponential-growth and first-order kinetic families; do not count them by default.

These three are still discovery leads, not accepted entries: the review's table gives equations and cites primary studies, but the primary references, assumptions, source-family IDs, and scalar benchmark mappings must be checked before catalogue entry. The tumor models are likely correlated by shared application/data-generating context; structural distinctness and independence must be reviewed separately.

### Additional scalar tumor-burden response leads from the same review

The same review's Table 1 also reports algebraic time-course models that are naturally scalar in their stated output (tumor burden (T(t))). These are promising for a deterministic benchmark interface, subject to primary-source tracing and a decision about whether time-course models are admissible in the frozen Core-295 domain strata.

| Discovery lead | Equation reported in review | Exact review location | Review status |
|---|---|---|---|
| Two-phase growth/regression | `T(t) = BASE*(exp(-k_d*t) + exp(k_g*t) - 1)` | Table 1, Eq. 26; cited studies 50, 51, 55 | Exact equation found; source family is the two-phase tumor growth/regression model. |
| Delayed regrowth | `T(t) = BASE*(exp(-k_d*t) + exp(k_g*(t-tau)) - 1)` | Table 1, Eq. 27; cited study 50 | Modification of Eq. 26; do not count as an independent unit without a substantive structural review. |
| Sensitive-fraction two-phase model | `T(t) = BASE*(phi*exp(-k_d*t) + (exp(k_g*t)-phi))` | Table 1, Eq. 28; cited study 55 | Modification of Eq. 26; same family pending source-level and structural review. |
| Exponential shrinkage plus linear growth | `T(t) = BASE*exp(-A*t) + B*t` | Table 1, Eq. 29; cited studies 52, 56 | Exact scalar algebraic form; trace Wang et al. and check validity/time range. |
| Quadratic extension | `T(t) = BASE*exp(-A*t) + B*t + C*t^2` | Table 1, Eq. 30; cited study 53 | Extension of Eq. 29; same source/derivation family, not a separate independent unit by default. |
| Simplified treatment-growth-inhibition model | `T(t) = BASE*exp(k_g*t - (k_d/lambda)*(1-exp(-lambda*t)))` | Table 1, Eq. 32; cited studies 54, 57–60 | Exact scalar algebraic form; trace original model paper(s), confirm exposure assumptions and parameter units. |

These candidates share a clinical tumor-growth/treatment-response application and some are explicitly extensions of one another. They may be retained as structurally different scientific models if the review approves them, but the family must be clustered for sampling and must not be treated as six independent calibration units. The review notes that model selection depends on cancer type, treatment and available longitudinal measurements; those conditions must be reflected in any validity regime and deterministic generator.

**Not promoted:** Table 1 Eq. 25 is a saturating exposure-effect relation and may overlap Michaelis–Menten-type saturation; Table 1 Eq. 33 is a reaction-diffusion PDE and requires a non-arbitrary spatial/scalar output contract. Neither is counted here as a candidate accepted into the catalogue.

## Biology: primary-source tracing for selected tumor-growth leads

The tumor-dynamics review's Table 1 maps selected equation structures to original clinical or preclinical studies. The following source links have now been added to the consolidated bibliography and catalogue source register. These are **primary-source leads**, not accepted catalogue records.

| Review equation | Candidate structure | Primary-source lead | Curation interpretation |
|---|---|---|---|
| Table 1, Eq. 2 | Linear tumor growth with first-order shrinkage, `dT/dt = k_g - d*T` | De Buck et al. (2014), *British Journal of Clinical Pharmacology*, 78(3), 543–555, DOI [10.1111/bcp.12378](https://doi.org/10.1111/bcp.12378); primary model Eq. 9 | The source is a clinical PK/PD turnover model. Verify the exact exposure-linked term and whether the simplified review form is an appropriate deterministic benchmark equation before acceptance. |
| Table 1, Eq. 6 | Gompertz tumor growth, `dT/dt = k_g*T*ln(T_max/T)` | Belfatto et al. (2016), DOI [10.1109/JBHI.2015.2453437](https://doi.org/10.1109/JBHI.2015.2453437); Bethge et al. (2015), DOI [10.1016/j.jbi.2015.07.011](https://doi.org/10.1016/j.jbi.2015.07.011) | These are application/simulation sources cited by the review, not necessarily the origin of the Gompertz law. Treat the two papers as a shared Gompertz derivation family unless the sampling design supports a different unit. |
| Table 1, Eq. 8 | Combined exponential-to-linear tumor growth | Simeoni et al. (2004), DOI [10.1158/0008-5472.CAN-03-2524]; Ouerdani et al. (2016), DOI [10.1007/s00280-016-3046-2] | Simeoni et al. describe the preclinical model in which untreated growth transitions from exponential to linear; Ouerdani et al. provide a clinical application. These are related source-family evidence, not two independent equations. |

The review explicitly distinguishes natural-growth equations, treatment-effect terms, heterogeneous-cell ODE systems, and algebraic tumor-time-course models. Do not flatten these into one undifferentiated candidate pool. In particular, a simplified equation transcribed from a review must be checked against the primary model's full terms, state definitions, units and assumptions. The new references are recorded as `candidate_reference`; no equation has been promoted to `source_verified` or `accepted`.

## Biology: primary-source expansion beyond tumor dynamics

The source universe has been extended with primary works covering population interactions, epidemic dynamics, reaction–diffusion morphogenesis and physiological transport. They are source leads only; no equations have been accepted.

| Model family | Primary source | What is supported | Core-295 curation decision |
|---|---|---|---|
| Predator–prey / host–parasite population dynamics | Lotka (1910, 1925), *Contribution to the theory of periodic reactions* and *Elements of Physical Biology*; [1925 book notice](https://www.nature.com/articles/116461b0) | Lotka's 1910 work is a chemical periodic-reaction precursor; the 1925 book develops population interactions. The later historical literature records Volterra's independent development and Lotka's priority clarification. | One Lotka–Volterra model family, not multiple independent equations for each author, species interpretation or algebraic arrangement. Define prey/predator state order and positive-state domain. |
| Epidemic dynamics | Kermack & McKendrick (1927), [*A contribution to the mathematical theory of epidemics*](https://doi.org/10.1098/rspa.1927.0118), *Proceedings of the Royal Society A*, 115(772), 700–721 | Foundational homogeneous-population epidemic theory. | Do not equate every modern SIR/SEIR compartment extension with an independent source family. Verify the original model assumptions and decide whether the benchmark target is an integral final-size relation, a trajectory, or a reduced ODE output. |
| Reaction–diffusion morphogenesis | Turing (1952), [*The chemical basis of morphogenesis*](https://doi.org/10.1098/rstb.1952.0012), *Philosophical Transactions B*, 237(641), 37–72 | Primary source for coupled morphogen reaction–diffusion and instability-driven pattern formation. | The governing model is spatial and coupled. Do not squeeze the PDE into a scalar pointwise regression equation without a declared geometry, boundary conditions, initial conditions and output functional. |
| Whole-body fluid/solute transport | Gyenge, Bowen, Reed & Bert (1999), [*Transport of fluid and solutes in the body I*](https://doi.org/10.1152/ajpheart.1999.277.3.H1215), *American Journal of Physiology*, 277(3), H1215–H1227 | Primary four-compartment model for vascular/interstitial and embedded cellular compartments. | Potentially useful physiological system, but requires a state/flux table, units, parameter source and a deterministic scalar or vector output contract. |

**Source-lineage caution:** Lotka's chemical oscillator work and later predator–prey models are historically related but not identical applications. The Lotka–Volterra ecological equations should remain one family; the 1910 chemical oscillator must not be counted as a second ecological model simply by relabeling variables. Likewise, a Kermack–McKendrick final-size relation and the associated epidemic trajectory equations belong to the same foundational model family unless the catalogue's structural unit is explicitly defined otherwise.

The Cambridge contents for Mazumdar's textbook independently confirm the relevant topic strata—diffusion, population biology, pharmacokinetics, epidemiology, biofluid mechanics and left-ventricular mechanics—but contents metadata alone does not verify any particular equation. Exact chapter equations and primary derivations remain required.

