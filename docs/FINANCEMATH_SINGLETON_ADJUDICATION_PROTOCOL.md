# FinanceMath singleton review and adjudication protocol

**Status:** reviewer procedure only; no singleton records are adjudicated by this document.  
**Queue:** `data/external_candidates/financemath_singleton_review_queue.json`  
**Source:** `yale-nlp/FinanceMath` revision `bdc2b6b04252aa09630b66ec1e2a5c98e5a2794c`  
**Current policy:** no calibration/evaluation eligibility, cohort assignment, routing change, or numeric tau follows from this protocol.

## 1. Purpose and scope

This protocol specifies how reviewers should assess the 1,172 records in the literal-normalized singleton queue. "Singleton" means only that the source solution was not placed in one of the 13 existing literal-normalized code clusters. It does **not** mean a distinct equation, mathematical family, or independent unit.

The queue is a work-allocation artifact. It intentionally contains metadata rather than question text, source solutions, answers, or generated equations. Reviewers must retrieve candidate material from the pinned source revision and preserve the source question ID and split as provenance.

This protocol does not reopen or silently promote the separate 28-record provisional code-cluster review or the 34-record named-overlap triage. Those artifacts remain provisional and must be reconciled during any eventual global family review.

## 2. Required source and reference material

For each review, record the exact revision/blob identity actually inspected. At minimum:

- FinanceMath source revision and source split/question ID.
- The retained question, supplied Python solution, and any referenced table or source data.
- The candidate registry and singleton queue revision.
- The applicable Core-15 definitions from `hypatiax/experiments/benchmarks/exp1_ablation.py`.
- The pinned historical-74 formula evidence: stored result-artifact expressions plus the four source-reconstructed expressions, clearly distinguishing the two evidence bases.
- Any relevant existing FinanceMath duplicate, family, and overlap review records.

A missing question, missing solution, unavailable table, or unresolved source-version mismatch is a review blocker—not permission to infer a formula from the topic label.

## 3. Record-level review fields

Every reviewed source row should retain the following fields (or a lossless equivalent):

| Field | Required content |
|---|---|
| `source_question_id` | Exact source ID, e.g. `validation-123` |
| `source_split` | Original `validation` or `test` label; provenance only |
| `source_revision` | Full pinned FinanceMath revision |
| `source_question_hash` | Hash of exact retrieved question text |
| `source_solution_hash` | Hash of exact retrieved solution text |
| `table_provenance` | Table IDs/revision/hash, or explicit `not_applicable` / `unavailable` |
| `review_status` | One of the controlled statuses below |
| `normalized_equation` | Reviewer-derived expression(s), with variable definitions and assumptions |
| `mathematical_category` | Predeclared category; use `unclassified` until taxonomy review |
| `within_source_relation` | Relation to other FinanceMath records, with referenced IDs |
| `formula_equivalence_review` | Explicit equation-equivalence decision, evidence, and reviewer rationale |
| `core15_overlap` | Exact reference and relation, or `not_identified_after_review` |
| `historical74_overlap` | Exact reference and relation, or `not_identified_after_review` |
| `cross_registry_overlap` | Review against other candidate registries, with exact IDs/evidence or unresolved status |
| `independence_status` | `not_adjudicated` until a separate family-level independence review is complete |
| `canonical_equation_family_id` | Null until family grouping is reviewed and approved |
| `reviewer_id`, `reviewed_at` | Reviewer and timestamp |
| `rationale` | Short mathematical explanation, not keyword-only reasoning |
| `uncertainties` | Assumptions, missing evidence, and unresolved alternatives |
| `second_review` | Independent reviewer decision and rationale when required |

Do not overwrite source registry fields in place merely because an individual review is complete. Keep review evidence in a versioned companion artifact and preserve an auditable link to the source row.

## 4. Controlled review statuses

Use only these statuses, or an explicitly versioned extension:

- `not_reviewed`: no candidate-level assessment performed.
- `source_unavailable`: pinned question/solution/table could not be retrieved or verified.
- `needs_table_review`: calculation depends on a table or external values not yet retained and checked.
- `needs_math_review`: a normalized equation or family boundary cannot yet be determined.
- `reviewed_family_candidate`: equation and provisional within-source family relation documented; independence not decided.
- `reviewed_overlap_hold`: possible Core-15 or historical-74 overlap requiring resolution.
- `reviewed_related_not_same_equation`: related concept/component identified, with rationale; family-level review still required.
- `reviewed_false_positive`: apparent name/topic match rejected by inspecting the actual calculation.
- `reviewed_non_equation_or_procedure`: source solution does not define a suitable single equation under the predeclared scope.
- `second_review_required`: borderline or consequential decision awaiting independent review.
- `adjudicated_family_relation`: relation approved after required review; this still does not establish statistical independence or cohort eligibility.

Do not use a generic `independent`, `calibration_eligible`, or `evaluation_eligible` status as a shortcut for equation review. Those are separate later decisions requiring a complete family-level evidence package and the applicable validators.

## 5. Mathematical comparison rules

Review the implemented mathematical operation, not just the question wording, topic, variable names, or code syntax.

Classify the relation using separate dimensions:

1. **Exact duplicate:** same question/data/solution or same raw equation, as applicable.
2. **Algebraic equivalence:** same function after valid algebraic rearrangement, variable renaming, or parameter substitution under stated domains and assumptions.
3. **Same equation family / parameterized template:** same governing relation with changed inputs, units, horizon, or parameters. Explain why the variation does not create a new family.
4. **Shared component:** a common subexpression appears inside otherwise different target equations. Name the component and explain whether it is disqualifying under the predeclared exclusion policy.
5. **Related concept:** same domain or terminology but a different mathematical target or operation.
6. **No overlap identified:** only after explicit comparison against the applicable reference definitions; this is not a proof of global inequivalence.
7. **Unresolved:** insufficient evidence or disputed family boundary.

A code-text singleton may still be algebraically equivalent to another record. Conversely, a shared operator such as `sqrt`, `log`, multiplication, or a covariance term is not enough to establish the same equation family.

For multi-step solutions, identify each material equation and its role. Do not force a procedural solution into one equation merely to assign a family. Record domain restrictions, sign conventions, units, assumptions, and whether values are supplied constants or estimated quantities.

## 6. Table-dependent and data-dependent candidates

For any table-dependent candidate:

1. Identify the exact table and the values used by the solution.
2. Preserve the table's source/revision or a stable content hash.
3. Map each used value to its source row/column and unit.
4. Determine whether the solution implements a general equation, a lookup, a table-specific calculation, or a multi-step procedure.
5. If the table or provenance is unavailable, use `needs_table_review` or `source_unavailable`; do not reconstruct missing values from the answer.

A formula-looking code fragment is not sufficient evidence that the candidate is a standalone equation.

## 7. Core-15 and historical-74 overlap review

Compare the normalized equation and its assumptions to the actual canonical expression, not merely the equation name.

For every possible match, record:

- canonical equation ID and source path/revision;
- candidate expression and canonical expression;
- relation type from Section 5;
- variable mapping and parameter/domain assumptions;
- whether the match is direct, a shared family, a component, merely related, or unresolved;
- reviewer rationale and any required second review.

For historical-74 comparisons, distinguish expressions present in the pinned result artifact from the four expressions reconstructed from the pinned historical protocol source. An absent artifact formula is not evidence of no overlap.

The existing 34-record FinanceMath overlap triage is a lead list, not an exclusion oracle. Reconcile relevant candidates with it and the Core-15/historical-74 comparison documents; do not duplicate, erase, or silently reverse their provisional findings.

## 8. Family identity and second review

Assign a family ID only after comparing the candidate against the already reviewed pool, including both source splits and the existing 28-record review. Family IDs must be global across FinanceMath, stable, and supported by a written equation-level rationale. Record formula-equivalence review, Core-15 overlap, historical-74 overlap, cross-registry overlap, and independence status as separate fields; do not collapse them into one family decision. In particular, set `independence_status` to `not_adjudicated` until the separate independence protocol is completed.

Require an independent second reviewer for:

- disputed exact or algebraic equivalence;
- parameterized-template boundaries that could change the independent-unit count;
- Core-15 or historical-74 overlap decisions;
- component-overlap decisions that affect exclusion;
- table-dependent or multi-equation cases with ambiguous interpretation;
- any proposed decision that could make a family appear eligible for a future cohort.

The second reviewer must assess the source evidence independently before seeing the first reviewer's conclusion. Record both decisions. Resolve disagreement explicitly; otherwise retain an unresolved status. Repeated reviews of the same record do not create additional independent units.

## 9. Independence and cohort firewall

Equation-family adjudication is not statistical independence adjudication. After family identities are reviewed, a separate protocol must assess shared generators, templates, data construction, source provenance, category membership, and benchmark leakage before any independence claim.

- Never infer family independence from the validation/test split.
- Preserve split labels as provenance; do not use public test labels to tune formulas, prompts, thresholds, or tau.
- Do not split one family across calibration and evaluation.
- Do not count question variants, parameter changes, code rewrites, repeated prompts, model runs, or random seeds as independent families.
- Do not pool unlike mathematical strata to reach a sample-size target.
- Do not treat a no-overlap finding as proof of independence.
- Keep all cohort assignments null until the full family and independence review is complete and the manifest validators pass.

The current protocol's zero-failure minimum of 59 independent units per category applies to accepted independent units, not candidate rows. The present singleton queue does not establish that this minimum is attainable.

## 10. Completion and audit checks

Before marking a batch complete, verify:

- every queue ID in the batch has exactly one review record;
- no source ID is missing, duplicated, or silently changed;
- each review references the pinned source revision and evidence hashes;
- table-dependent cases are resolved or explicitly blocked;
- equation relations and canonical overlaps have written rationales;
- all required second reviews are recorded;
- family IDs are globally consistent across reviewed artifacts;
- unresolved cases remain unresolved rather than being forced into a category;
- no registry cohort, calibration, evaluation, routing, or tau field was changed by the review.

Batch completion is an administrative checkpoint only. It does not imply that the reviewed records form an independent cohort.

## 11. Non-claims and authorization boundary

This protocol makes no mathematical adjudication of any of the 1,172 queued records, assigns no family IDs, and establishes no independent units. It does not certify any category's sample size, populate calibration/evaluation manifests, select tau, authorize formula generation or provider calls, authorize experiments or seed sweeps, or change routing.

Keep `degradation_tau: null` and the existing fail-closed routing policy until the separately approved calibration and evaluation requirements are satisfied.
