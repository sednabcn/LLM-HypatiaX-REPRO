# Core-295 Volterra n-species primary-source and structure audit 1

**Candidate:** `BIO-VOLTERRA-1926-N-SPECIES-CONSERVATIVE-001`  
**Disposition:** equation and source location verified; remains proposed; structural-equivalence and generator reviews open.  
**Date:** 2026-11-12

## Primary-source chain

Vito Volterra, *Variazioni e fluttuazioni del numero d'individui in specie animali conviventi* (1926), *Memorie della R. Accademia Nazionale dei Lincei*, series VI, vol. II, fasc. III, pp. 31–113.

The accessible equation-bearing text inspected here is Volterra's 1927 author-expanded reprint, *Variazioni e fluttuazioni del numero d'individui in specie animali conviventi*, *Memorie del R. Comitato talassografico italiano*, Mem. CXXXI. Its prefatory note states that Parts I–III rearrange and add to the 1926 Lincei memoir. The candidate's equation is in Part II, §2, printed pp. 38–39, Eq. (B).

Full reprint scan/OCR: https://francesco-ferraro.com/lotka-volterra/volterra1927variazioni.pdf  
1926 original bibliographic record: https://books.google.com/books?id=ugtJWtbokQ0C  
1926 article catalogue record: https://ndlsearch.ndl.go.jp/books/R100000136-I1574231874580495104

## Equation and source definitions

For (n) interacting species, Volterra derives

\[
\beta_r\frac{dN_r}{dt}
=\left(\varepsilon_r\beta_r+\sum_{s=1}^{n}a_{sr}N_s\right)N_r,
\quad r=1,\ldots,n,
\]

subject to

\[
a_{rs}=-a_{sr},\qquad a_{rr}=0,\qquad \beta_r>0.
\]

This is Eq. (B), Part II, §2, printed p. 39. The immediately preceding derivation on printed pp. 38–39 is important to interpretation:

- Volterra assumes pairwise encounter frequency proportional to (N_rN_s).
- An encounter transfers population-equivalent weight between species: the loss from one species and gain to the other are related by their individual weights.
- He defines (1/\beta_r) as the equivalence assigned to an individual of species (r). Thus (\beta_r) is not merely an arbitrary numerical scale; it encodes the source's species-equivalence convention.
- The intrinsic coefficient (\varepsilon_r) is the growth coefficient of species (r) when considered alone.

The reprint's Part II, §2 also makes clear that this is a continuous deterministic approximation: species counts are treated as positive real-valued quantities, births and deaths occur continuously, and individuals within a species are treated as homogeneous for the model.

## What is and is not conserved

Multiplying each species equation by its weight and summing cancels the pairwise interaction terms because the interaction matrix is antisymmetric:

\[
\frac{d}{dt}\sum_{r=1}^{n}\beta_rN_r
=\sum_{r=1}^{n}\varepsilon_r\beta_rN_r.
\]

Therefore the interaction contribution conserves the weighted association value, but the full weighted total is not generally constant when intrinsic growth/depletion terms are nonzero. It is constant in the special case (\varepsilon_r=0) for all species, or where the right-hand weighted intrinsic contribution is zero along the trajectory. The candidate must not be described as an unconditional conservation law for arbitrary (\varepsilon_r).

The source itself discusses the cases where all intrinsic coefficients are negative or positive and shows weighted population depletion or growth, respectively. This confirms that the nonzero intrinsic terms are substantive, not ignorable notation.

## Relationship to the two-species model and Lotka

Volterra treats the two-species predator-prey case earlier in Part I and identifies it as a special case within the broader theory. Do not count that two-species case as a second candidate.

The 1927 preface explicitly notes that, after the 1926 memoir, Volterra learned of Lotka's 1925 *Elements of Physical Biology* treatment of the two-species case, acknowledging Lotka's priority for the two-species differential equations, integral, diagram and small-oscillation period. Volterra distinguishes the broader n-species conservative/dissipative association theory as new in his treatment. This is relevant provenance, not proof that every n-species parameterization is structurally inequivalent to generalized Lotka–Volterra systems.

The 1926 Nature summary also describes the general conservative-association class as admitting species-equivalence weights and a system of differential quadratic equations associated with a skew-symmetric determinant:
https://www.nature.com/articles/118558a0

## Structural-equivalence review

The right-hand side is a coupled generalized Lotka–Volterra operator with a restricted antisymmetric interaction structure and source-defined species-equivalence weights. The candidate is not merely the classical two-species predator-prey special case. Nevertheless, its relation to the broader Lotka–Volterra family is a material structural question. Compare the full n-state operator, antisymmetry constraint, weighting convention, and intrinsic terms against the Core-15 exclusions and other catalogue ODE/matrix families under E0–E5. This audit does not assign a final E-class or certify countability.

The source's different sections, parity cases, stationary-state calculations, first integrals, stability results, and two-species special cases are not automatically separate equation entries; they are consequences or subcases of the governing system unless a distinct irreducible operator is demonstrated.

## Parameter and generator implications

No universal numerical values or rectangular input ranges for (N_r,\varepsilon_r,\beta_r,a_{sr}) are established by the source. A usable generator would require a declared (n), a full antisymmetric interaction matrix, positive species weights, initial positive population vector, and explicit handling of nonnegative/positive state constraints. The generator must preserve the antisymmetry and species-equivalence structure; independently sampling all coefficients would violate the model.

The current `ode_ivp` classification is directionally appropriate, but the catalogue's `pending_specialized_generator` status must remain until a constrained multi-species generator and its sampling semantics are specified. Do not treat a generic scalar adapter as sufficient.

## Catalogue disposition

The candidate remains `proposed`; generator status remains `pending_specialized_generator`. No parameter values or input bounds are added. No equation is accepted, no generator is implemented, and no experiment, validator, or workflow is run by this audit.

## Sources

1. Volterra (1927 author-expanded reprint), Part II, §2, printed pp. 38–39, Eq. (B), and prefatory note on relation to 1926 Lincei memoir: https://francesco-ferraro.com/lotka-volterra/volterra1927variazioni.pdf
2. Volterra (1926), *Memorie della R. Accademia Nazionale dei Lincei*, series VI, vol. II, fasc. III, pp. 31–113, bibliographic record: https://ndlsearch.ndl.go.jp/books/R100000136-I1574231874580495104
3. Volterra (1926), “Fluctuations in the Abundance of a Species considered Mathematically,” *Nature* 118, 558–560: https://www.nature.com/articles/118558a0
4. Volterra (1927), “Fluctuations in the Abundance of a Species considered Mathematically,” *Nature* 119, 12–13, reply acknowledging Lotka's priority for the two-species case: https://www.nature.com/articles/119012b0
