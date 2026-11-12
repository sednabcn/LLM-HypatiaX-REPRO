# Core-295 Frumkin branch and parameter audit 2

Date: 2026-11-12

Candidate: `CHEM-FRUMKIN-1967-INTERACTION-001`

## Scope retained

The source-verified Eq. (4) in Frumkin and Damaskin (1967), printed p.268, is

\[
Bc=\frac{\theta}{1-\theta}\exp(-2a\theta),
\qquad 0<\theta<1.
\]

The paper treats adsorption of organic substances at the free water surface and water-mercury interface. The catalogue candidate is scoped to the mercury-electrolyte interface. Here \(\theta\) is fractional coverage, \(c\) is bulk concentration, \(B\) is the adsorption coefficient in the paper's convention, and \(a\) is the dimensionless lateral interaction parameter. The product \(Bc\) must be dimensionless. Eq. (5) in the same paper makes \(B\) potential-dependent; Eq. (4) alone is not a statement that B is constant across electrode potential.

## Root topology and solver implications

Define the right-hand side as

\[
q_a(\theta)=\frac{\theta}{1-\theta}e^{-2a\theta}.
\]

Its logarithmic derivative is

\[
\frac{d}{d\theta}\ln q_a(\theta)
=\frac{1}{\theta(1-\theta)}-2a.
\]

Since \(1/[\theta(1-\theta)]\ge4\) for \(0<\theta<1\):

- If \(a\le2\), \(q_a\) is monotone increasing on \((0,1)\). For every positive \(Bc\), exactly one physical coverage root exists.
- If \(a>2\), two stationary points occur at
  \[
  \theta_\pm=\frac{1\pm\sqrt{1-2/a}}{2}.
  \]
  The isotherm can then have three roots for an interval of positive \(Bc\), separated by turning-point values. A numerical solver must not silently choose whichever root its initial guess happens to find.
- At \(a=0\), the relation reduces algebraically to the Langmuir isotherm. This limiting case is not a distinct candidate.
- This branch analysis is mathematical analysis of the catalogue equation, not a claim that every mathematical branch is thermodynamically stable or experimentally realized.

Therefore a specialized generator must define a branch-selection/stability policy and test root existence, residual accuracy, and uniqueness or explicitly preserve multiple admissible roots. A generic unconstrained root finder is insufficient.

## Parameter and source evidence

The accessible 1967 paper provides the governing relation and connects B to electrode potential in Eq. (5), but the present audit does not establish a transferable numerical interval for B, a, c, temperature, or electrode potential. Values are system- and condition-specific. Do not borrow the 2017 review's illustrative surfactant coefficient ranges as Frumkin model parameter bounds: those are material-specific and not universal.

A 2017 drop-profile tensiometry paper independently prints the Frumkin surface-layer equation of state and adsorption isotherm, defines the symbols and explains that a can be adjusted for attraction, repulsion, or reorientation effects. It is a useful modern corroborating source, not a substitute for the 1967 primary transcription or a universal parameter dataset.

The 1967 paper cites Frumkin's 1925 and 1926 work. The 1925 paper is the historical source associated with the interacting adsorption isotherm, but the earlier audit did not retrieve a sufficiently inspectable original scan to independently transcribe the exact non-ideal equation. First-publication priority remains distinct from the 1967 paper's accessible equation evidence.

## Structural and sampling disposition

- Compare the nonzero-interaction model with Langmuir under the E0-E5 policy. The a=0 case is a limiting case, not another equation.
- Keep the coupled potential-dependent B relation and capacitance equations (5)-(9) in the same source/model family unless a future review establishes an independently complete operator.
- Source-family independence is not established merely because the same isotherm appears in later papers.
- No numerical train/extrapolation bounds or fixed parameter values are justified by the sources inspected here.
- Keep status proposed and generator pending_specialized_generator. A specialized implicit solver needs an explicit branch policy before a generator can be considered ready.

## Catalogue disposition

Record the derivative/branch condition as an implementation blocker. Do not mark the candidate accepted, statistically independent, or benchmark-ready. No change to accepted-equation counts.

## Sources

- Frumkin and Damaskin (1967), “Adsorption of Organic Substances on the Free Water Surface and at the Water-Mercury Interface,” *Pure and Applied Chemistry* 15(2), 263–281, Eq. (4), printed p.268, and Eqs. (5)-(9): https://publications.iupac.org/pac/pdf/1967/pdf/1502x0263.pdf
- M. A. Kovalchuk et al. (2017), “Surface Tension and Adsorption Studies by Drop Profile Analysis Tensiometry,” *Journal of Surfactants and Detergents* 20, 1225–1241: https://pmc.ncbi.nlm.nih.gov/articles/PMC5686271/ and https://doi.org/10.1007/s11743-017-2016-y
- Frumkin (1925), “Die Kapillarkurve der höheren Fettsäuren und die Zustandsgleichung der Oberflächenschicht,” *Zeitschrift für Physikalische Chemie* 116, 466–484, DOI: https://doi.org/10.1515/zpch-1925-11629

No scripts, validators, tests, workflows, live experiments or scientific simulations were run.
