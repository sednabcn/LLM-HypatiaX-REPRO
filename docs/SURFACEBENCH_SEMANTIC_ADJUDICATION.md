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


## Within-source repeated-template groups

The JSON now enumerates eight concrete repeated-subexpression/template groups with member IDs. These are reviewer queues, **not** equivalence classes or independent-family assignments:

| Shared construction | SurfaceBench IDs | Interpretation |
|---|---|---|
| `exp(-a*(x²+y²))` radial Gaussian envelope | NACS3, NACS10, MTAS3, NCS2, NCS6, EMTS1, EMTS7, LRDS1, LRDS2, LRDS3, LRDS4, LRDS8, PTM3, MOCS10, EBS3, TECS2 | Same parameterized envelope; coefficients and remaining factors differ |
| Radial square-root construction | NACS9, MTAS6, OCS6, OCS10, TECS1, MOCS5, MOCS8, NCS4, LRDS6 | Shared radial-root argument/factor; surrounding functions differ |
| `log(1+x²+y²)` | NACS5, TECS4, MOCS1, EBS7, PTM2 | Shared subexpression used as factor, standalone surface, or additive term |
| `sin(x*y)` | NACS4, NACS11, OCS3, OCS4, TECS3, CMRS7, EBS9 | Direct, nested, piecewise, and envelope-modulated appearances |
| Piecewise/discrete regimes | PDS1–PDS6, PDS8–PDS10, CMRS1–CMRS4, CMRS6–CMRS9, MOCS7, DIGS3, DIGS4, DIGS7, DIGS9, DIGS10 | Shared regime structure; predicates and branch expressions differ |
| `exp(-Abs(x-y))` | OCS8, EBS10 | Shared factor; one record multiplies it by an oscillatory term |
| `sin(x)*cos(y)` | EBS2, PTM5 | Shared subexpression; PTM5 adds a cross-coordinate term |
| `tanh(x*y)` | MTAS2, OCS10, PTM8 | Shared subexpression with different surrounding terms |

The group membership is deliberately conservative and explicit. A common subexpression, envelope, or branch mechanism is insufficient to merge two equations: each proposed family merge still needs a canonicalized formula and a mathematical rationale. The JSON preserves `canonical_equation_family_id=null` and `independence_status=not_adjudicated` for every record.

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


## Second-pass review of the eight repeated-template groups

A second symbolic-structure pass reviewed the eight groups member-by-member. It does **not** create additional canonical equation families:

| Group | Second-pass finding | Decision |
|---|---|---|
| Radial Gaussian envelope | Exact `exp(-(x²+y²))` factor occurs with different multipliers/addends; other members vary the damping coefficient. | Shared factor only; no whole-equation merge |
| Radial square-root | `OCS6` and `OCS10` share `cos(sqrt(x²+y²))`, but multiply it by different functions. Other members use distinct compositions. | Shared factor only |
| Radial logarithm | `EBS7` is the standalone logarithm; the other members combine it with different functions and operations. | Shared subexpression only |
| `sin(x*y)` | `EBS9` is standalone; the other records compose, modulate, divide, add, or branch on the term. | Shared subexpression only |
| Piecewise/discrete | Predicates and branch functions differ. Integer-grid floor/modulo records have a different input-domain stratum from continuous surfaces. | No merge; keep discrete stratum separate |
| `exp(-Abs(x-y))` | `EBS10` is the envelope alone; `OCS8` multiplies it by an oscillatory term. | Shared envelope only |
| `sin(x)*cos(y)` | `PTM5 = EBS2 + 0.1*x*y`. | Candidate parameterized extension; source provenance needed |
| `tanh(x*y)` | Same subexpression appears with distinct additive and multiplicative compositions. | Shared subexpression only |

### Pair requiring source-level review

`EBS2` and `PTM5` are not equivalent as written. They may be related by a parameterized generator in which the cross-coordinate coefficient is zero for one instance and nonzero for the other, but the catalog formulae alone do not establish that provenance. Keep them separate provisionally and do not count either as independent until the upstream generation metadata is checked.

### Second-pass decision and limits

- The only established whole-equation duplicate remains `NACS1 = TECS7`.
- No further whole-equation family merges are justified by these eight shared-template groups.
- The integer-grid `DIGS*` cases are a distinct input-domain stratum and should not be pooled with continuous `x,y` surfaces without an explicit protocol rationale.
- This is a targeted second pass over the eight pre-identified groups, not an exhaustive all-pairs equivalence proof or a proof of independent data generation.
- All canonical family IDs, independence statuses, and cohort assignments remain unresolved/null. No tau or routing change follows from this review.
