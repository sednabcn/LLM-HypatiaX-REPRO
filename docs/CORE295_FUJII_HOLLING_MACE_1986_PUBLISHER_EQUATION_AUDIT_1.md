# Core-295 Fujii–Holling–Mace 1986 publisher-equation audit 1

**Candidate:** `BIO-FUJII-HOLLING-MACE-1986-GENERALIZED-ATTACK-001`  
**Disposition:** exact equation verified in primary publisher abstract image; full article derivation and structural-equivalence review remain open; proposed only.  
**Date:** 2026-11-12

## Primary source and access level

Koichi Fujii, C. S. Holling and P. M. Mace, “A Simple Generalized Model of Attack by Predators and Parasites,” *Ecological Research* 1(2) (August 1986), 141–156, DOI 10.1007/BF02347017.

The Wiley/Ecological Research publisher page provides the article metadata, abstract, and a linked image of the proposed equation. The equation image itself was opened and inspected. The accessible page does not expose the full 16-page article text; therefore this audit is a publisher-abstract/equation-image transcription, not a full-paper derivation audit. The equation is unnumbered in the abstract image.

Publisher page and equation image: https://esj-journals.onlinelibrary.wiley.com/doi/abs/10.1007/BF02347017  
DOI: https://doi.org/10.1007/BF02347017

## Exact equation and output semantics

The publisher's equation image displays

\[
A(N_0)=\frac{T_t}{t_h+\dfrac{1}{a'N_0\exp(cN_0)}}.
\]

The abstract defines:
- (A(N_0)): number of attacks per predator during exposure time (T_t).
- (N_0): prey density.
- (T_t): total time for which prey are exposed.
- (t_h): handling time per prey.
- (a'): rate of successful search.
- (c): facilitation coefficient.

The output is an attack count per predator over the stated exposure duration, not a rate per unit time. The abstract introduces the equation in the context of the effect of prey density on instantaneous attack rate, but the defined (A) includes the exposure time (T_t). Preserve this distinction in the catalogue and generator.

For dimensional consistency, (a'N_0) has units of inverse time, (t_h) has units of time, (cN_0) is dimensionless, and the denominator has units of time. (T_t) divided by that denominator yields a dimensionless attack count per predator.

## Parameter regimes

The publisher abstract explicitly identifies the following regimes of the same generalized equation:

- (c=0): Type II.
- (c>a't_h): Type III.
- (c<0): Type IV.
- (c=a't_h): pseudo Type I.

These are not separate equation candidates. The special case (c=0) reduces to the Holling Type II hyperbolic response. The abstract states that the model is primarily descriptive and reports comparison with a simulation model and available laboratory and field predation data. It does not supply a common parameter range or transferable sampling design.

## Structural-equivalence issue

The Core-15 exclusion registry includes Michaelis–Menten. At (c=0), the expression has the usual saturating hyperbolic structure associated with Holling Type II and Michaelis–Menten response forms. For (c\ne0), the effective encounter/search term is (N_0\exp(cN_0)), adding density-dependent facilitation or interference inside the saturating denominator.

That modification may yield a structurally distinct operator, but a mechanism label or nonzero parameter alone is not enough. The complete equation must be compared against the Core-15 Michaelis–Menten exclusion and other Holling/functional-response candidates under E0–E5. In particular, do not count the (c=0) Type II subcase separately, and do not count Type I–IV parameter regimes as distinct equations.

## Evidence limitations and parameter scope

The full article text and its detailed experimental/simulation sections were not available in the inspected publisher page. The abstract does not identify the individual datasets, fitted parameter estimates, prey/predator species, density intervals, exposure-time ranges, or a transferable training/extrapolation design. Do not infer numerical ranges from the abstract.

The source equation is directly visible in the publisher-hosted equation image, but its unnumbered abstract location is the only page-level equation location verified here. Keep (N_0,T_t,t_h,a',c) ranges unset and fixed values empty until the full paper or named source datasets are inspected.

## Catalogue disposition

The candidate remains `proposed`; generator status remains `pending_benchmark_contract`. No parameter values or input bounds are added. No equation is accepted, no generator is implemented, and no experiment, validator, or workflow is run by this audit.

## Sources

1. Fujii, Holling & Mace (1986), publisher abstract and linked equation image, *Ecological Research* 1(2), 141–156: https://esj-journals.onlinelibrary.wiley.com/doi/abs/10.1007/BF02347017
2. DOI record: https://doi.org/10.1007/BF02347017
