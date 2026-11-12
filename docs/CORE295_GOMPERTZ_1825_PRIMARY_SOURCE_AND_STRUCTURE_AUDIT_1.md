# Core-295 Gompertz 1825 primary-source and structure audit 1

**Candidate:** `BIO-GOMPERTZ-1825-MORTALITY-001`  
**Disposition:** source transcription verified; remains proposed; structural-equivalence and generator reviews open.  
**Date:** 2026-11-12

## Primary source and exact location

Benjamin Gompertz, “On the Nature of the Function Expressive of the Law of Human Mortality, and on a New Mode of Determining the Value of Life Contingencies,” *Philosophical Transactions of the Royal Society of London* 115 (1825), 513–583, read 16 June 1825.

The full article scan was inspected. The relevant passage is Article I, Arts. 4–5, printed pp. 517–518; the subsequent empirical interpolation and table fits are in Arts. 6–10, printed pp. 518–525. Article 5 is printed p. 518. The Royal Society/JSTOR volume record independently identifies the article and pagination.

Primary full scan: https://jhanley.biostat.mcgill.ca/c609/material/Gompertz-1825.pdf  
JSTOR article record: https://www.jstor.org/stable/107756  
Volume 115 issue record: https://www.jstor.org/stable/i206980

## What the original source says

Article 4 (printed pp. 517–518) distinguishes two generally co-existing causes of death: an age-independent “chance” component and age-related deterioration. Article 5 then isolates the deterioration mechanism. In Gompertz's words, the age-dependent “intensity of mortality” at age (x) is denoted (a q^x), with (a) and (q) constant. He relates the fluxion of deaths in a living cohort to the negative derivative of the number living, and gives the corresponding survivor-count relation

\[
\mu(x)=a q^x, \qquad L_x=d\,g^{q^x}.
\]

The scan OCR around the fluxion notation and integration is imperfect, but the prose and the explicit survivor-count expression are legible. Gompertz explicitly clarifies that (g^{q^x}) means (g) raised to the power (q^x), not ((g^q)^x). The candidate's primary transcribed equation is therefore the age-dependent hazard/intensity, not the survivor expression.

The correct modern interpretation of the relative cohort decrement is

\[
\mu(x)=-\frac{d}{dx}\log L_x,
\]

with the understanding that Gompertz's (x) is age and the derivative is on the declared age/time scale. Thus the instantaneous hazard is conditional on being alive at age (x); it is not the unconditional death density. The cohort death density, where a continuous survival distribution is defined, is (f(x)=\mu(x)S(x)), not simply (\mu(x)).

The survivor-count expression is the integrated consequence of the hazard under the model assumptions. It must not be entered as another independent equation row.

## Empirical scope and parameter interpretation

Article 2 notes that geometric progression in survivor counts is an approximation over portions of mortality tables. Articles 7–10 fit the relation to named historical tables and age spans, including Northampton, Deparcieux and Carlisle. The fitted (q) values differ between tables and age intervals; for example, the source reports different fitted age-multiplication factors for Northampton and Deparcieux data. These are historical table-specific fits, not universal human mortality constants and not a common parameter range.

The original notation (q^x) presumes a declared age unit. For an implementation with continuous age, make the age scale explicit. An equivalent parameterization is (q^x=\exp(\beta x)), where (eta=\log q) is per unit age. Do not pass a dimensionful age directly into a dimensionless exponent without that convention.

No universal (a,q) values, common cohort, or rectangular input interval is justified by the original paper. Leave fixed parameter values and train/extrapolation ranges unset until a named cohort, period, age convention, and source dataset are selected.

## Model boundaries

- **Candidate model:** age-dependent Gompertz mortality intensity/hazard.
- **Not included:** an age-independent chance term. Gompertz discusses it separately in Article 4; a combined model would be a distinct specification requiring its own provenance and review.
- **Not a second candidate:** (L_x=d g^{q^x}), which is the associated survivor-count relation.
- **Not the same by name:** Gompertz growth curves used for tumor or organism growth are not this human-mortality model.
- **Not interchangeable:** hazard, survival function, and death density are different quantities.

## Structural-equivalence review

The hazard's surface form is exponential in age. That creates a broad mathematical resemblance to other exponential operators in the Core-15 and Core-295 pool. A domain label or different scientific interpretation is not enough to establish structural distinctness. The review must compare the complete governing model and its output semantics, including the integrated survivor relation, against the Core-15 exclusion registry and the E0–E5 policy. This audit does not assign a final E-class or declare the candidate countable.

The 1825 paper and its historical mortality-table fits form one source family. The several table fits in the paper are not independent statistical units. A future calibration/evaluation sampling design must specify cohort-level independent units and avoid treating fitted age bands from one life table as independent equations.

## Catalogue disposition

The candidate remains `proposed`; generator status remains `pending_benchmark_contract`. No numerical fixed parameter values or input bounds are added. No equation is accepted, no generator is implemented, and no experiment or validator is run by this audit.

## Sources

1. Gompertz, B. (1825), original article scan, especially Article I, Arts. 4–10, printed pp. 517–525: https://jhanley.biostat.mcgill.ca/c609/material/Gompertz-1825.pdf
2. JSTOR primary article record, volume 115, pp. 513–583: https://www.jstor.org/stable/107756
3. JSTOR volume 115 table of contents: https://www.jstor.org/stable/i206980
4. Hanley et al. (2015), “Deciphering death: a commentary on Gompertz (1825),” for modern historical context and the distinction between the Gompertz component and the later Makeham age-independent addition: https://pmc.ncbi.nlm.nih.gov/articles/PMC4360127/
