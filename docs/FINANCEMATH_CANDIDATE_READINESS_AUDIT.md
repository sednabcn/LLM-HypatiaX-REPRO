# FinanceMath candidate split and readiness audit

**Review baseline:** `master` at `ca3e671714c0743c6b47a37b699ca8059bae5dba` (2026-11-24).  
**Pinned source:** `yale-nlp/FinanceMath` revision `bdc2b6b04252aa09630b66ec1e2a5c98e5a2794c`.  
**Scope:** offline review of the existing candidate registry, code-cluster screen, provisional family review, and overlap screen. No source records were modified; no cohort assignments, formula generation, model/API calls, experiments, or routing changes were made.

## Decision

**FinanceMath remains a candidate source pool, not a calibration or independent-evaluation cohort.** The source has enough raw candidate records to justify further review, but the current evidence does not establish 59 independent equation families in any declared category, nor a family-disjoint calibration/evaluation split. Keep `config/tau_calibration_manifest.json` in draft with no calibration equations and no numeric tau.

## Registry counts

The pinned 1,200-record registry has the following deterministic screening counts:

| Source split | Text formula candidates | Table-dependent formula candidates | Other classes | Total |
|---|---:|---:|---:|---:|
| Validation (200 records) | 104 | 71 | 25 | 200 |
| Test (1,000 records) | 506 | 368 | 126 | 1,000 |
| **Total** | **610** | **439** | **151** | **1,200** |

These are screening labels, not counts of equations or independent families. A Python solution containing arithmetic can still encode a lookup, accounting convention, multi-step procedure, or several related formulae. Table-dependent candidates additionally require a retained, source-pinned table and a stable interpretation of its values.

Every entry in `financemath_candidate_registry.json` remains `review_status=unreviewed`, `canonical_equation_family_id=null`, `core15_overlap_status=not_checked`, `historical_74_overlap_status=not_checked`, `independence_status=not_adjudicated`, and `cohort_assignment=null`. The separate provisional family-review file does not promote or mutate those registry records.

## Duplicate and family evidence

The source-solution screen reports:

- 1,200 source solutions found; none missing.
- Six exact code-duplicate groups covering 12 records.
- Thirteen literal-normalized code clusters covering 28 records.
- The manual review of those 28 records proposes 12 mathematical families; it does not review the remaining 1,172 literal-normalized singletons.

Two exact duplicate groups cross the source's validation/test boundary:

- `validation-25` and `test-828`.
- `validation-179` and `test-761`.

The other four exact-duplicate groups are within the test split. These cross-split duplicates are direct evidence that the dataset's question-level validation/test partition is not, by itself, a family-disjoint calibration/evaluation partition. They must be assigned one shared family identity and kept on only one side of any future split.

The 12 provisional family labels are reviewer leads only. They do not establish that the remaining candidates are distinct, that each family belongs to a predeclared mathematical category, or that any record is eligible for calibration/evaluation.

## Core-15 and historical-74 overlap screen

The keyword/context screen flags 34 records: seven validation and 27 test. Its provisional assessments are:

| Assessment | Records | Required handling |
|---|---:|---|
| Likely same broad VaR family | 16 | Hold out pending exact canonical formula comparison |
| Likely same formula family | 4 | Hold out pending exact Core-15 or historical-74 formula comparison |
| Component formula overlap | 1 | Human review of whether the shared component disqualifies the family |
| Related risk calculation, not the same VaR equation | 10 | Do not auto-exclude; review the family boundary |
| Related concept, not the same equation | 1 | Do not auto-exclude |
| False positive | 2 | Do not exclude on this keyword match |

The overlap screen itself states that exact formula references are required before final exclusion. A shared phrase such as “VaR”, “Sharpe”, or “Kelly” is not enough to establish mathematical equivalence; conversely, a different problem description does not prove that the underlying equation family is distinct.

The Core-15 comparison must use the canonical formula definitions in `hypatiax/experiments/benchmarks/exp1_ablation.py`, not only equation names. Historical comparisons must use the pinned historical formula evidence, including source-recovered expressions where the retained result artifact omitted a formula; those recovered expressions must remain explicitly distinguished from artifact-stored formulas.

## Split and sample-size implications

1. Do not use the source's validation/test labels as proof of independent equation families. The two cross-split exact duplicates already disprove that shortcut.
2. Preserve each source split and original question ID as provenance. Any future family-level partition must be frozen after adjudication, with every family assigned wholly to calibration or evaluation—not divided by question row.
3. The protocol's zero-failure minimum is 59 independent units per category for calibration. The independent evaluation cohort also needs at least 59 accepted/evaluable independent units per category to support the same zero-failure bound. Candidate rows, duplicate questions, repeated seeds, and multiple prompt runs do not increase that count.
4. The 175 validation candidate rows are only a pre-review upper bound for possible calibration material; they are not 175 equations. The 874 test candidate rows are only a pre-review upper bound for possible evaluation material; they are not 874 independent families.
5. The public release of test annotations means the test split must not be described as a blind or untouched benchmark. It may be considered for a predeclared evaluation only if the exact family allocation and non-use in calibration/formula selection are documented. Any evidence that test answers informed formula generation or threshold choice disqualifies the affected family from confirmatory evaluation.

## Safe next steps

1. Resolve all 34 overlap leads against exact canonical Core-15 and historical-74 formula definitions; preserve the distinction between same family, related calculation, component overlap, and false positive.
2. Complete a systematic family review beyond the existing 28-record queue. Review table-dependent records against retained source tables and solution provenance; do not infer formulas from question keywords alone.
3. Assign global family IDs across all 1,200 records, including cross-split duplicates and algebraic/reparameterized equivalents. Keep the provisional 12 labels provisional until independently reviewed.
4. Define mathematical categories before counting units. Do not pool unlike strata simply to reach 59.
5. Only after the review, design a family-disjoint calibration/evaluation allocation and update manifests through their validators. Keep the current calibration manifest unchanged until the full evidence package is ready.

## Non-claims

This audit does not establish any FinanceMath record as an independent equation, certify 59 units in any category, approve the test split as confirmatory evaluation, or prove that the keyword overlap screen is complete. It does not populate calibration/evaluation manifests, select tau, or authorize an experiment. The fail-closed `degradation_tau: null` policy remains unchanged.
