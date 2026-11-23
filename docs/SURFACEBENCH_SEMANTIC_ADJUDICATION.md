# SurfaceBench explicit-surface semantic adjudication

**Status:** provisional formula/template screen; no independent-family IDs or cohort assignments approved.

## Scope and pinned evidence

- Candidate registry: `data/external_candidates/surfacebench_candidate_registry.json` (blob `05c6dc130afa8edf1203ccada4a749cde92760ef`).
- SurfaceBench source: `deep-symbolic-mathematics/surfacebench@619bcb0aa17cd80694798c5ca92283cd9a4e6ba4`.
- Catalog: `psaegert/symbolic-data@13b23672154e6dd6a463ad223d3f72829d21fe60`.
- Core-15 formula definitions: `hypatiax/experiments/benchmarks/exp1_ablation.py`, blob `05b28899120a077a5fb8edbd5f38b23b1bf7e2dc`.
- Historical cohort: 74-record artifact from workflow run `45038667467`, artifact `14760901742`, source commit `107fcd6da06fe15833ecdf37c6d2284da84256c8`, ZIP digest `sha256:ddfc8fdc28a12db6615005629d01141d369d1978c5fe685e69c750b20f2aa5db`.
- Historical protocol definitions: `hypatiax/protocols/experiment_protocol_defi.py` at the same source commit, blob `231c3c43f1c27b35280f48366185f1ee442f099b`.

## Findings

1. The 128 SurfaceBench explicit records contain **127 unique literal formula strings**. `NACS1` and `TECS7` are the sole exact-duplicate pair; they must count as one equation.
2. Formula-level review found **no direct equivalent or same named mathematical equation family** between the 127 unique SurfaceBench formulas and the 15 Core-15 formulas.
3. The historical artifact stores formulas for 70 of 74 cases. The other four artifact-missing expressions were recovered from the protocol source at the artifact's exact pinned source commit: `Capital efficiency` = `P_upper / (P_upper - P_lower)`; `Incremental VaR` = `sqrt(v1**2 + v2**2 + 2*rho*v1*v2) - v1`; `Options Delta` = `clip(0.5 + m/(2*vol*sqrt(T)), 0, 1)`; and `Theta of option` = `-(S*norm_pdf(d1)*sigma)/(2*sqrt(T)) - r*K*exp(-r*T)*norm_cdf(d2)`, with the source-defined Black–Scholes `d1` and `d2`. No direct SurfaceBench equivalent or same named equation family was identified across all 74 cases after this recovery. The recovered formulas are explicitly distinguished from formulas stored in the result artifact.
4. `Incremental VaR` shares the covariance-quadratic portfolio-risk core with Core-15 `Portfolio Std Dev` (it subtracts the old portfolio VaR after computing the combined portfolio risk). This is a historical/Core-15 family overlap, so the historical case remains excluded from any independent cohort. It is not a SurfaceBench overlap.
5. The candidate formulas share broad construction patterns: radial quadratic invariants, Gaussian/exponential envelopes, oscillatory trigonometric/hyperbolic components, piecewise regimes, coupled bivariate interactions, and free symbolic coefficients. These are **template annotations**, not equivalence classes. Different branch conditions, radial envelopes, coefficients, and base functions mean the tag alone cannot merge records into one equation family.
6. OOD renderings are not counted as separate equations; each is a view of its source equation.

## Adjudication policy

- Exact duplicates are one equation.
- Algebraic rearrangements, variable renamings, and parameter substitutions that preserve the governing equation should be merged into one family after explicit review.
- Similar operator vocabulary or a common envelope is insufficient by itself to declare equivalence.
- The per-record JSON records descriptive template tags, exact-duplicate status, cross-cohort screen result, and the unresolved independence status.
- No canonical family ID, calibration/evaluation assignment, or tau-manifest entry is created by this audit.

## Decision

The 127 literal-unique formulas are **not yet 127 certified independent units**. The screen identifies one exact duplicate, finds no direct SurfaceBench overlap with the Core-15 or the 74 historical cases after reconstructing the four artifact-missing formulas from their pinned source, and identifies one historical/Core-15 family overlap (`Incremental VaR` / `Portfolio Std Dev`). Full SurfaceBench family-level adjudication remains open—especially for parameterized templates and shared radial, oscillatory, and piecewise constructions. Do not use this result to populate calibration or evaluation cohorts, pool the 13 source categories, or change routing/tau.

## Next review required

A second reviewer should inspect the tagged candidate pairs/groups, especially parameterized/free-coefficient forms and the shared radial, damped-oscillatory, and piecewise templates. Any merged family must receive a documented canonical formula and rationale. The four historical expressions are now source-recovered, but their provenance must remain marked as protocol-derived rather than artifact-stored.
