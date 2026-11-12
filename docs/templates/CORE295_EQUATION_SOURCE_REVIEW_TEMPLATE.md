# Core-295 source verification and equation transcription review

> **Working template — not an acceptance form.** Completing this record does not by itself verify scientific correctness, structural distinctness, or statistical independence. Do not change a catalogue entry to `accepted` until all independent review gates are satisfied.

## A. Candidate identity and disposition

| Field | Record |
|---|---|
| Candidate/equation ID | `[DOMAIN-SOURCE-MODEL-NNN]` |
| Candidate name | |
| Domain / subdomain | |
| Current review status | `proposed` / `source_verified` / `scientifically_reviewed` / `structurally_reviewed` / `rejected` |
| Review date (UTC) | |
| Primary reviewer | |
| Independent second reviewer | |
| Source-family ID | |
| Statistical-unit ID (provisional until sampling design is frozen) | |
| Related Core-15 exclusion(s) | |
| Related catalogue candidates | |

## B. Primary-source identity and provenance

Record the source actually inspected, not only a search result, abstract, citation aggregator, or secondary reproduction.

| Field | Evidence |
|---|---|
| Full citation (authors, title, venue, volume/issue, pages, year) | |
| DOI / ISBN / standard number / protocol version | |
| Publisher, archive, standards body, or official repository | |
| Stable landing-page URL | |
| Exact PDF / source-code URL | |
| Source type | Original research / standard / textbook / official protocol specification / pinned implementation / other |
| Primary-source rationale | |
| Version inspected | Version of record / accepted manuscript / preprint / edition / commit |
| Publication or release date | |
| Access and licence evidence | |
| Retrieval date (UTC) | |
| Local artifact path (if retained) | |
| Artifact SHA-256 | |
| Git commit and blob SHA (for code/protocol sources) | |

**Source identity checks**

- [ ] Title, authors/maintainers and venue match the primary landing page.
- [ ] DOI, ISBN, standard number, version or commit resolves to this exact work.
- [ ] Inspected artifact belongs to the cited work and version.
- [ ] It is not merely an abstract, review, tutorial, citation record or secondary equation reproduction.
- [ ] Any erratum, corrigendum, revision or superseding version has been checked.
- [ ] Licence/access conditions were checked at the source; metadata alone was not treated as legal permission.

**Primary-source evidence and unresolved issues**

- Direct evidence observed (describe exact page, section, theorem, table, code symbol or commit):
- What is not accessible or not yet verified:
- Why this source is adequate to support the proposed model:

## C. Exact location and equation evidence

| Field | Record |
|---|---|
| Printed page number(s) | |
| PDF page index (if different) | |
| Equation / theorem / section / figure / code location | |
| Equation label as printed | |
| Nearby heading / subsection | |
| Exact source notation retained? | Yes / No — explain |
| Screenshot or page-image reference (if retained) | |

**Transcription rule:** preserve the source's notation first. Do not silently modernize symbols, change sign conventions, omit terms, substitute a familiar textbook form, or infer a missing equation from an abstract.

### Verbatim mathematical transcription

```text
[Transcribe the complete equation or complete coupled system exactly as printed.]
```

### Faithful typeset transcription

```text
[LaTeX or unambiguous plain-text transcription; retain source notation.]
```

### Transcription cross-check

- [ ] Every term, exponent, subscript, superscript, derivative, integral and summation limit checked against the page image.
- [ ] Brackets, signs, fractions and parentheses checked.
- [ ] All coupled equations and constraints needed to define the model are included.
- [ ] Equation label and printed page independently checked.
- [ ] Transcription checked by a second reader or a documented independent pass.
- [ ] OCR/extracted text was compared with the rendered source page; OCR was not treated as authoritative.

**Ambiguous or damaged source notation:**  
**Differences between OCR/text extraction and page image:**  
**Second-pass reviewer and date:**

## D. Mathematical model definition

### Model class

Choose one and explain if hybrid:

- [ ] Scalar algebraic constitutive / response relation
- [ ] Scalar ODE or recurrence
- [ ] Coupled ODE / recurrence system
- [ ] PDE or coupled PDE system
- [ ] Integral or delay equation
- [ ] Constrained protocol state-transition / accounting system
- [ ] Other:

### Governing structure

| Field | Record |
|---|---|
| State variables | |
| Independent variables | |
| Dependent variables / outputs | |
| State dimension | |
| Differential / recurrence order | |
| Operator / nonlinear structure | |
| Initial and boundary conditions | |
| Algebraic constraints / conservation laws | |
| Complete system boundary (what is included/excluded) | |
| Source's derivation or model lineage | |

### Symbols, units and dimensions

| Symbol (source notation) | Meaning | SI / canonical unit | Dimension | Parameter/state/input | Source location defining it |
|---|---|---|---|---|---|
| | | | | | |

### Assumptions and validity

- Physical, biological, chemical, economic or protocol assumptions:
- Equilibrium / steady-state / continuity / ideality assumptions:
- Boundary and initial conditions:
- Parameter restrictions and sign constraints:
- Calibration or empirical fitting assumptions:
- Validity regime:
- Known failure modes and limitations:
- Conditions under which the model must not be used:

### Canonical form (review aid only)

- Source-faithful expression:
- Proposed canonical expression:
- Nondimensionalization, if valid:
- Transformations applied:
- Dimensional consistency check:
- What information canonicalization might erase (and how it is preserved):

## E. Candidate-level source and model checks

- [ ] Formula is explicitly present in the inspected primary source.
- [ ] Complete governing model is transcribed, not a derived output or isolated component.
- [ ] Variables and units are defined by the source or a clearly cited authoritative companion source.
- [ ] Assumptions and validity regime are documented.
- [ ] Source lineage and any parent/derived model are recorded.
- [ ] Candidate is not a cosmetic parameter, unit, symbol or algebraic variant.
- [ ] Candidate does not split a coupled system into multiple entries.
- [ ] Core-15 exclusion overlap has been examined.
- [ ] Cross-domain analogues have been searched.
- [ ] Existing proposed and accepted catalogue candidates have been compared.

## F. Structural-equivalence review (E0–E5)

Compare the complete governing model, not just a displayed output formula. Record each meaningful comparison, including cross-domain candidates.

| Compared candidate / family | Shared source or parent? | Operator / topology comparison | Transformations tested | E0–E5 | Rationale and evidence |
|---|---|---|---|---|---|
| | | | | | |

**Provisional classification**

- [ ] E0 — exact duplicate
- [ ] E1 — algebraically equivalent / rearrangement / inverse / unit conversion
- [ ] E2 — derived, limiting, linearized or special-solution form
- [ ] E3 — same normalized operator/topology, different mechanism (not countable under strict draft rule)
- [ ] E4 — related but irreducibly structurally distinct
- [ ] E5 — unresolved (hold; do not count)

- Derivation parent(s):
- Shared model/source family:
- Symbol-renaming-invariant signature:
- State/dependency graph:
- Differential, integral, delay or recurrence structure:
- Constraints and boundary/initial conditions:
- Why this is (or is not) structurally distinct:
- Remaining uncertainty:

**Important:** a hash or symbolic fingerprint is only a retrieval aid. It does not prove inequivalence. E4 requires a reasoned human comparison. Under the current strict draft, E3 does not count toward the 295 structural target.

## G. Source-family and statistical-unit assessment

These identifiers answer different questions and must not be conflated.

| Field | Record |
|---|---|
| Source-family ID | |
| Why these sources/models belong to this family | |
| Statistical-unit ID | |
| What was actually independently sampled | |
| Shared authors / source / dataset / generator / protocol / parameters | |
| Potential dependence or clustering | |
| Independence rationale | |
| Sampling-frame rule that admits this unit | |
| Is this unit eligible for calibration/evaluation? | Yes / No / Not yet determined |

Do not infer statistical independence from distinct equations, DOIs, papers, authors, protocols, or domains. If the sampling frame is not frozen, mark independence as unresolved and do not use this candidate to claim a binomial confidence guarantee.

## H. Benchmarkability and generator contract

| Field | Record |
|---|---|
| Deterministic generator method | |
| Seed policy | |
| Parameter sampling distribution / bounds | |
| Input variables and units | |
| Training ranges | |
| Extrapolation ranges | |
| Number of samples / noise model | |
| Ground-truth evaluator | |
| Numerical stability / singularities | |
| Constraints enforced by generator | |
| Reproducibility notes | |

- [ ] Generator samples the complete model, not a special case that changes its identity.
- [ ] Training and extrapolation regions are disjoint and documented.
- [ ] Parameter and input ranges are scientifically defensible.
- [ ] The model can be evaluated deterministically under the benchmark contract.
- [ ] Numerical edge cases and failure behaviour are specified.

## I. Review decisions and sign-off

| Gate | Reviewer | Date | Decision | Evidence / rationale |
|---|---|---|---|---|
| Primary-source identity | | | Pass / Hold / Fail | |
| Exact equation transcription | | | Pass / Hold / Fail | |
| Variables, units and assumptions | | | Pass / Hold / Fail | |
| Complete model boundary | | | Pass / Hold / Fail | |
| Core-15 overlap | | | Pass / Hold / Fail | |
| Structural equivalence | | | E0–E5 / Hold | |
| Source-family assignment | | | Pass / Hold / Fail | |
| Statistical-unit / sampling eligibility | | | Pass / Hold / Fail | |
| Generator and benchmark contract | | | Pass / Hold / Fail | |
| Independent second review | | | Pass / Hold / Fail | |

**Final disposition:** Proposed / Source verified / Scientifically reviewed / Structurally reviewed / Rejected / Accepted

**Acceptance is permitted only if:** every required gate passes; the complete governing model is source-verified; the structural decision is E4 under the strict draft policy; Core-15 overlap is resolved; source-family and statistical-unit decisions are documented; generator and input ranges are complete; and an independent reviewer signs off. Catalogue acceptance must still follow the repository's formal review process and current validator requirements.

## J. Change log

| Date (UTC) | Field changed | Previous value | New value | Reviewer | Reason / source evidence |
|---|---|---|---|---|---|
| | | | | | |
