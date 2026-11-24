# Offline τ convergence evaluator

## Purpose and safety boundary

\`scripts/evaluate_tau_convergence.py\` evaluates already-produced, frozen LLM degradation records. It does not call an LLM provider, generate formulas, construct cohorts, change routing configuration, or write \`degradation_tau\`.

The evaluator follows the repository-approved calibration policy:

- Candidate thresholds are declared in advance and ordered strictest-to-laxest (ascending τ).
- Per category, accepted routes satisfy the frozen eligibility gate and \`delta_llm <= tau\`.
- The bad-route label is supplied by the frozen edge/ensemble evaluator. This script does not guess the ensemble relative-margin calculation.
- Candidate thresholds are tested in fixed sequence using an exact one-sided binomial test of \`H0: p_bad >= 0.05\` against \`p_bad < 0.05\` at \`delta = 0.05\`. Stop at the first candidate that is not certified.
- At least 59 distinct independent units are required in each declared category, even with zero bad accepted routes. More units may be needed when failures occur or accepted coverage is low.

The exact binomial test is the risk-certification procedure. Family bootstrap and local threshold perturbation are descriptive stability diagnostics; they are not substitutes for the approved risk test.

**Important limitation:** the repository has not yet declared numeric acceptance tolerances for bootstrap threshold variability, plateau width, or local decision-flip rate. Consequently, the tool deliberately reports \`convergence_status=not_established_missing_predeclared_stability_tolerances\`, even when the risk constraint is certified. It will not invent those tolerances or claim convergence from a risk test alone.

## Input schema

The input JSON has four top-level fields:

\`\`\`json
{
  "approved_protocol": {
    "edge_r2_floor": 0.99,
    "relative_margin": 0.0,
    "tolerated_bad_route_rate_epsilon": 0.05,
    "family_wise_error_delta": 0.05,
    "one_sided_confidence": 0.95,
    "minimum_n_if_zero_failures": 59
  },
  "candidate_tau_values": [0.05, 0.10, 0.15],
  "category_list": ["continuous_bivariate"],
  "records": [
    {
      "equation_id": "candidate-001",
      "independent_unit_id": "family-001",
      "category": "continuous_bivariate",
      "llm_eligible": true,
      "delta_llm": 0.07,
      "bad_route": false,
      "status": "scored"
    }
  ]
}
\`\`\`

Each record is one independently adjudicated equation-family unit. The \`independent_unit_id\` must be unique across the entire input, not just within a category. Repeated prompts, seeds, formula variants, sampled rows, and reruns do not create new independent units.

- \`llm_eligible\` must already encode the frozen formula/core-quality and structural eligibility gates. Invalid or failed formula records should be retained with \`llm_eligible: false\`; they remain in the assigned-unit and coverage denominator.
- \`delta_llm\` is \`R2_core - R2_edge\` for the same frozen LLM formula. It must be finite for eligible records.
- \`bad_route\` is a boolean computed by the approved evaluator using the ratified edge R² floor and ensemble comparison. It means the route would be bad **if accepted**. Do not derive this label from NN degradation or from a different predictor's score.
- \`status\` is retained as audit metadata; it does not override the explicit eligibility and bad-route fields.

Do not include held-out evaluation outcomes in this calibration input.

## Run

From the repository root:

\`\`\`bash
python scripts/evaluate_tau_convergence.py \\
  --input path/to/frozen_calibration_outcomes.json \\
  --output path/to/tau_convergence_report.json \\
  --bootstrap-replicates 2000 \\
  --seed 20261123 \\
  --tau-perturbation 0.01
\`\`\`

The bootstrap seed and replicate count make the diagnostic reproducible. The perturbation is expressed in τ units and should be chosen before inspecting the results. Use \`--bootstrap-replicates 0\` to disable bootstrap diagnostics; exact fixed-sequence testing still runs.

Exit code 0 means every declared category has a threshold certified by the exact calibration risk test and meets the 59-unit floor. Exit code 1 means at least one category is not certified or is underpowered. Exit code 2 means the input or invocation is invalid.

## Reading the report

Per category, the report includes:

- assigned independent units, eligible units, and eligibility coverage;
- exact candidate-by-candidate accepted counts, bad-route counts, rates, p-values, and pass/fail decisions;
- the selected threshold, if any;
- family-resampled selected-threshold frequencies and a conditional percentile interval;
- local route-flip fractions at \`tau - perturbation\` and \`tau + perturbation\`.

The bootstrap interval is conditional on replicates that selected a threshold; the report separately exposes the fraction of replicates that selected none. Interpret both. Small family counts and uncertain family adjudication limit bootstrap reliability.

A certified threshold is a calibration result, not a deployment authorization. Freeze the threshold, manifest, code, evaluator, and protocol before opening the untouched family-disjoint evaluation cohort. Evaluate the frozen rule once; never tune τ against that evaluation cohort. Calibration risk certification does not itself establish out-of-family generalization.

## Current project status

The manifest remains a draft with no eligible calibration family list or candidate threshold grid. The existing 74-case replay is historical and cannot be recycled as a fresh calibration cohort. No provider calls or experiment runs are authorized by this evaluator. Until the source/family, cohort, readiness, and user-authorization gates are met, do not create calibration outcomes or set a production τ.
