# Core-295 Leslie 1945 primary-source and matrix-operator audit 1

**Candidate:** `BIO-LESLIE-1945-AGE-STRUCTURED-MATRIX-001`  
**Disposition:** primary matrix transcription verified; remains proposed; structural-equivalence and generator reviews open.  
**Date:** 2026-11-12

## Primary source

P. H. Leslie, “On the Use of Matrices in Certain Population Mathematics,” *Biometrika* 33(3) (November 1945), 183–212, DOI 10.1093/biomet/33.3.183.

The complete article scan was inspected. The core transition is derived in sections 1–2, printed pp. 183–185. The matrix equation is printed p. 184; the definitions and approximations for its elements continue onto p. 185.

Full article scan: https://web.math.ku.dk/~moller/e04/bio/leslie-biometrika33.pdf  
Oxford Academic primary record: https://academic.oup.com/biomet/article-abstract/33/3/183/215959  
JSTOR issue contents: https://www.jstor.org/stable/i315400

## Model and exact source definitions

Leslie considers a female population divided into consecutive age classes, with the age-class width equal to the time step. If (n_{xt}) is the number of females alive in age class (x) to (x+1) at time (t), he defines:

- (P_x): probability that a female in age class (x) to (x+1) at time (t) survives into age class (x+1) to (x+2) at time (t+1).
- (F_x): number of daughters born during the interval (t) to (t+1), per female initially in age class (x) to (x+1), who themselves survive into age class 0–1 at time (t+1).

The one-step equations on printed p. 183–184 yield

\[
\mathbf n_{t+1}=M\mathbf n_t,
\]

where (M) has the age-specific fertility coefficients in its first row, survival probabilities (P_x) on the subdiagonal, and zeros elsewhere. Leslie explicitly gives (0<P_x<1) and (F_x\geq0); some fertility entries may be zero depending on reproductive biology and the terminal age class.

This is one discrete age-structured projection operator. The candidate should not be split into separate fertility, survival, stable-vector, eigenvalue, or matrix-power entries.

## Important fertility-coefficient approximation

The source emphasizes that the (F_x) coefficients are more difficult to derive than (P_x). On printed pp. 184–185, Leslie constructs them from maternal-frequency values and a life table by:

1. Representing the females initially in an age class as concentrated at its midpoint.
2. Approximating deaths as occurring around the midpoint of the time interval.
3. Applying maternal-frequency values over the first and second half-intervals.
4. Applying daughter-survival factors so that the counted daughters are alive in age class 0–1 at the next census.

Thus (F_x) is not merely a raw birth rate or a number of births during the interval. It is a composite transition coefficient that includes survival of daughters to the next census. The derivation is approximate and depends on the within-age-class distribution and the interpolation of the maternal-frequency curve.

For (P_x), Leslie relates the coefficient to the life-table ratio (L_{x+1}/L_x), while noting the assumption needed for exactness: the distribution within each age class must match the life-table distribution.

## Validity and example scope

The model assumes:

- Female population only, as in the original paper.
- Consecutive age classes of equal width.
- Time step equal to age-class width.
- Age-specific fertility and mortality schedules held constant over the projection period.
- A declared terminal age class and a dimensionally consistent fertility/survival matrix.

Leslie's numerical example is an imaginary brown-rat population with a constructed life table and fertility table, using 30-day units. The example's gross/net reproduction and growth values are specific to that constructed example, not universal demographic parameter ranges. The source warns that the age/time unit should not be too coarse relative to the species' life span and discusses cumulative error from repeated matrix projection.

No common empirical parameter range or transferable sampling distribution follows from the example. Keep catalogue input ranges unset.

## Structural-equivalence review

This is a discrete-time, finite-dimensional, age-structured matrix transition with fertility recruitment into the first age class and survival flow along the subdiagonal. It is not interchangeable with a scalar exponential or logistic growth equation, nor with a continuous-time Lotka renewal equation merely because all describe population change. The complete matrix topology and census/age-class semantics must be compared with other population matrix and renewal models under E0–E5. This audit does not assign a final E-class or declare the candidate accepted.

The paper's canonical matrix transformation, eigenvalue analysis, stable age distribution, stable vectors, powers (M^t), and special cases are analyses of the same operator, not separate catalogue candidates.

## Generator implications

A faithful generator requires a declared number of age classes, a consistent age/time step, a nonnegative initial age vector, (0<P_x<1), and (F_x\geq0), with the final age class convention explicit. The fertility coefficients must retain their meaning as surviving daughters at the next census; independently sampling (F_x) as generic birth rates would change the model. The current `matrix_operator` class is appropriate, but a specialized matrix generator and sampling contract remain necessary.

## Catalogue disposition

The candidate remains `proposed`; generator status remains `pending_specialized_generator`. No numerical parameter ranges are added. No equation is accepted, no generator is implemented, and no experiment, validator, or workflow is run by this audit.

## Sources

1. Leslie (1945), original article scan, sections 1–2, printed pp. 183–185: https://web.math.ku.dk/~moller/e04/bio/leslie-biometrika33.pdf
2. Oxford Academic primary record, *Biometrika* 33(3), 183–212: https://academic.oup.com/biomet/article-abstract/33/3/183/215959
3. JSTOR issue contents, November 1945: https://www.jstor.org/stable/i315400
