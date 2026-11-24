# Independent tau evaluation validator

**Status:** offline validator; it does not authorize an evaluation run or alter routing.

The script scripts/validate_tau_independent_evaluation.py validates a frozen evaluation-outcome JSON file. It never generates formulas, calls a provider, chooses a threshold, or retunes tau. It applies the already-frozen per-category threshold and checks whether the observed accepted routes meet the repository's exact one-sided binomial risk criterion.

## Required input

The JSON document must contain:

- schema_version 1 and status evaluation_complete.
- The exact approved_protocol constants from the calibration protocol.
- SHA-256 values for the frozen evaluation manifest, calibration manifest, and historical-74 exclusion registry.
- Calibration/evaluation code commit identifiers and the exact supported evaluator version (`tau-independent-evaluation-validator-v1`). Unknown or stale evaluator versions are rejected.
- calibration_family_ids and historical_74_family_ids, each a unique list of canonical family IDs.
- core15_exclusion_ids, exactly matching the current Core-15 catalogue.
- A predeclared category_list and selected_tau_by_category mapping. The selected values must be the frozen calibration outputs; this validator does not select them.
- One record per independently adjudicated evaluation family, including equation/family IDs, source/formula/training-row hashes, human review evidence, llm_eligible, and delta_llm for eligible rows. Accepted rows also require the frozen evaluator's boolean bad_route label.

The validator requires each record's independent_unit_id to equal its canonical_equation_family_id, and requires family review, formula-equivalence review, Core-15 overlap, historical-74 overlap, cross-registry overlap, and independence statuses to be complete/clear. Evidence references are required but their substantive correctness remains a human-review responsibility.

## Checks and interpretation

1. Reject duplicate evaluation equation IDs, canonical family IDs, and byte-identical formula hashes. Formula-hash uniqueness catches exact serialized duplicates; it does not establish algebraic equivalence, which still requires the documented human adjudication.
2. Reject any family ID shared with calibration or the historical-74 exclusion list.
3. Reject equation/family IDs matching Core-15.
4. Require the same predeclared categories and frozen tau values.
5. Count an accepted route only when llm_eligible is true and delta_llm <= selected_tau.
6. Count bad routes only from the frozen evaluator's bad_route labels for accepted rows.
7. Apply the exact lower-tail binomial test of H0: p_bad >= 0.05 against p_bad < 0.05 at one-sided delta = 0.05, independently within each category.

With zero bad routes, 59 accepted independent families are required. With one or more bad routes, the exact test requires more accepted routes; the validator computes the p-value from the observed accepted and bad counts rather than treating 59 as a universal minimum. Assigned but ineligible, abstained, invalid, or otherwise unaccepted records remain visible in assigned_independent_families but do not increase the accepted-route denominator.

The result risk_certified_on_independent_evaluation is a per-category statement under the frozen protocol. It is not a simultaneous all-category guarantee, does not permit tau retuning, and does not prove transportability beyond the declared evaluation population. A nonzero exit code means the file is invalid or at least one category did not meet the risk criterion.

## Invocation

~~~bash
python scripts/validate_tau_independent_evaluation.py \
  --input path/to/frozen_evaluation_outcomes.json \
  --output path/to/evaluation_risk_report.json
~~~

The default Core-15 source is hypatiax/experiments/benchmarks/exp1_ablation.py; override it with --core15-source only when validating against the exact approved source snapshot.

## Important provenance limitation

The validator checks the supplied family-ID exclusion lists and their declared hashes; it does not independently reconstruct the historical-74 registry from raw historical artifacts. The person preparing the evaluation file must ensure that the hashed exclusion registry is the reviewed, complete registry. Likewise, hashes and evidence-reference strings establish traceability fields, not mathematical truth. Independent human adjudication remains mandatory.

This validator is a post-evaluation audit tool. It does not make an incomplete cohort ready, authorize paid formula generation, or change the current degradation_tau: null fail-closed policy.


Malformed top-level JSON values are rejected as validation errors rather than
causing uncaught attribute errors; the validator requires the payload to be an
object before reading protocol or cohort fields.
