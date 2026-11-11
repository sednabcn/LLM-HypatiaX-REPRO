# Core-295 candidate discovery — batch 3: verified physics locations and biology source leads

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
