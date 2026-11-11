# Core-295 candidate discovery batch 5: Biology primary-source equation tracing

**Status:** primary-source tracing only. No equation is accepted or counted toward the 59 Biology target. The catalogue remains draft.

## Scope and findings

This pass follows three existing biological source leads to original papers and records what the original mathematical objects actually are. The purpose is to prevent familiar modern textbook labels from obscuring differences in the source equations.

| Candidate family | Primary source and exact location | What the original source contains | Curation boundary |
|---|---|---|---|
| Two-species plant–herbivore interaction (Lotka) | Lotka (1920), *PNAS* 6(7), 410–415, DOI [10.1073/pnas.6.7.410](https://doi.org/10.1073/pnas.6.7.410); original scan pp. 411–414, equations (5)–(10), transformed system (15), equilibrium/oscillation analysis (23)–(29) | Plant biomass and herbivore biomass, with growth, loss and feeding terms. The interaction terms are bilinear, but the coefficients are generally functions of both state variables; the paper then transforms variables and studies a local expansion near equilibrium. | Do not silently substitute the familiar constant-coefficient Lotka–Volterra equations for Lotka’s original variable-coefficient formulation. The 1925 *Elements of Physical Biology* expands the same lineage; treat 1920 and 1925 as one source/model family unless a genuinely distinct formulation is demonstrated. |
| Epidemic spread with infection-age structure (Kermack–McKendrick) | Kermack & McKendrick (1927), *Proceedings of the Royal Society A* 115(772), 700–721, DOI [10.1098/rspa.1927.0118](https://doi.org/10.1098/rspa.1927.0118); original scan pp. 702–705, equations (1)–(15), especially limiting integral equations (13)–(15) | A discrete infection-age cohort construction is taken to a continuous-time limit. The resulting system uses infectivity and removal kernels over infection age, with convolution-type integrals for new infections, removals and infectious prevalence. | This is not simply the later elementary SIR ODE system with constant per-capita removal. Preserve the age-dependent infectivity/removal functions and integral structure if using this source. Any finite-dimensional SIR reduction requires its own source, assumptions and derivation record. |
| Reaction–diffusion morphogenesis (Turing) | Turing (1952), *Philosophical Transactions of the Royal Society B* 237(641), 37–72; original scan §§3–4, §§6–10, especially cell-ring model equations in §6 and subsequent stability analysis | The paper formulates chemical reactions and diffusion in both discrete-cell and continuous-tissue descriptions. The detailed worked analysis focuses on a ring of cells, with morphogen transfer between neighbours and local reaction dynamics, followed by instability and pattern analysis. | Do not present a modern generic two-species reaction–diffusion PDE as a verbatim equation from Turing’s detailed ring model. Distinguish the general continuous description from the discrete ring equations actually analyzed. Define geometry, neighbour coupling, reaction kinetics, units and boundary conditions. |

## Source-level details

### Lotka (1920)

The paper first describes the broad system as differential equations for species masses. For the plant–herbivore case, the analytical forms are given in equations (5) and (9), with factored equivalents in (8) and (10). Lotka explicitly allows the coefficients to depend on both populations. Around a positive equilibrium, he shifts variables (13)–(14), obtains the transformed system (15), and analyzes oscillatory behaviour through the local expansion and characteristic roots. This is a primary biological interaction source, but it should not be conflated with the chemical autocatalytic examples discussed in the paper or counted separately from its later book treatment without a source-family rationale.

### Kermack–McKendrick (1927)

The paper explicitly models infectivity and removal as functions of time since infection. The discrete cohort relations are equations (1)–(10); the continuous-time limit gives the conservation relation and integral equations (11)–(15). The independent relations are identified by the authors as (12)–(15). This original structure is a strong candidate for a deterministic age-of-infection benchmark, provided the input/output interface handles kernels or a justified finite-dimensional parameterization. It is not interchangeable with a modern SIR ODE by naming convention.

### Turing (1952)

Section 3 states the diffusion and mass-action assumptions and explains why actual reaction steps—not merely net reaction equations—must be used. The detailed cell-ring construction appears in later sections and leads into stability/pattern analysis. The model is coupled and spatial/discrete; it is not a scalar algebraic law. Any benchmark representation must specify the state vector, cell count, topology, kinetic parameters, initial state and observable. The continuous-tissue description and discrete-cell model should be treated as related representations of the same Turing source family.

## Overlap and acceptance controls

- Core-15 exclusions still apply. Do not use the logistic growth model as a new candidate.
- Lotka’s 1920 paper and 1925 book are one historical model lineage for sampling purposes unless a structural distinction is demonstrated.
- The Kermack–McKendrick age-of-infection integral system is distinct from a standard SIR ODE formulation, but both belong to the epidemic transmission family; do not count alternative notations or reductions as independent units.
- Turing’s discrete ring and continuum descriptions are linked representations of one reaction–diffusion morphogenesis family.
- These systems are vector-valued, integral or spatial models. A scalar benchmark adapter must be justified and documented; projecting a system onto one output does not make its underlying equations independent scalar families.
- All records remain discovery candidates. Acceptance requires exact transcription, units, assumptions, validity regime, deterministic data interface, source-family ID, independence-unit decision and equivalence review.

## Primary-source access pointers

- [Lotka 1920 original paper DOI](https://doi.org/10.1073/pnas.6.7.410)
- [Kermack–McKendrick 1927 original paper DOI](https://doi.org/10.1098/rspa.1927.0118)
- [Turing 1952 original paper scan](https://www.damtp.cam.ac.uk/user/gold/pdfs/teaching/old_literature/Turing1952.pdf)
