# LLM tau calibration cohort feasibility audit

**Date:** 2026-11-22  
**Scope:** Offline source-registry inventory and sample-size feasibility only. No formula generation, model/API calls, benchmark execution, or routing changes.

## Decision

**The current repository does not contain a defensible, unused, provenance-pinned equation registry large enough to start the approved calibration. Keep the calibration manifest in draft and `degradation_tau: null`.**

The existing candidate sources are useful starting points, but none individually supplies the required 59 independent equation/family units in a predeclared calibration category plus a distinct evaluation cohort. Pooling them naively would duplicate equation families, mix benchmark populations, or reuse previously calibrated observations.

## Repository inventory

| Source | Verified scope | Why it is not currently an eligible cohort |
|---|---:|---|
| Core-15 (`hypatiax/experiments/benchmarks/exp1_ablation.py`) | 15 equations | Explicitly excluded by `config/tau_calibration_manifest.json`; must not be reintroduced. |
| Manuscript Protocol-30 (`hypatiax/protocols/experiment_protocol_benchmark_v2.py`) | 30 equations across 11 domains | Source comments state it is not a strict subset of the AI Feynman benchmark and includes custom crossover equations. It is not enough for the 59-unit calibration minimum, and overlap/family independence against Core-15 and other registries must be resolved. |
| Experiment Protocol ALL-30 (`hypatiax/protocols/experiment_protocol_all_30.py`) | 30 equations | Separate registry with shared canonical equation families (e.g. kinetic energy, ideal gas, Arrhenius, Michaelis-Menten, logistic growth). It cannot be added to Protocol-30 by raw row count. |
| Nguyen-12 (`hypatiax/protocols/experiment_protocol_nguyen12.py`) | 12 equations in 3 categories | Too small; repeated seeds/runs are not independent equations. Cross-registry equation-family overlap still needs canonical identity resolution. |
| Existing LLM edge calibration artifact | 74 equations: 44 calibration / 30 evaluation | Already consumed by the historical calibration/replay. It is not a fresh, untouched cohort; its results were poor/undefined in substantial numbers. It cannot be silently recycled as a new preregistered study. |
| Feynman-labelled definitions in Protocol-30 source | Curated definitions, including Feynman-derived and custom crossover entries | The source itself warns that the manuscript registry is not a strict AI Feynman subset. The repository inventory does not establish a larger immutable external dataset snapshot with source IDs, family IDs, licensing/provenance, and pinned hashes. |

The source files and their comments were inspected on `master`. Counts above are registry counts, not counts of statistically independent equation families.

## Sample-size implications

The approved manifest fixes:

- Bad-route probability target: `epsilon = 0.05`.
- One-sided family-wise error: `delta = 0.05`.
- Exact zero-failure minimum: `ceil(log(0.05) / log(1 - 0.05)) = 59`.

Therefore:

1. Each declared calibration category needs at least 59 distinct independent equation/family units even if it observes zero bad routes.
2. The independent evaluation cohort must be disjoint. To demonstrate the same 5% risk bound with zero bad accepted routes, it also needs at least 59 **accepted/evaluable independent units per category**. The number of assigned evaluation equations must be larger if the policy abstains, formulas fail, or scoring is undefined.
3. If there are bad accepted routes, the required sample size is greater than 59; compute the exact bound from the observed count and freeze the precision plan before evaluation.
4. Multiple seeds, prompt variants, noise settings, rows, or repeated executions of the same equation/family do not increase the independent-unit count.

The validator enforces the calibration-side minimum. Evaluation-side accepted-route precision must be enforced in the evaluation analysis/validator before a go decision; do not infer readiness from the calibration manifest alone.

## Required registry construction

Build a new, versioned registry from a named public benchmark release or other auditable source. Before any model calls:

1. Record canonical equation ID, source benchmark ID, domain/category, difficulty, independent family ID, source citation/version, formula source, variable/domain constraints, and licensing/provenance.
2. Normalize equations and manually adjudicate equivalent/reparameterized forms across sources. Assign one global independent-family ID per genuinely distinct mathematical family. Never use seeds or near-duplicate transformations as separate units.
3. Exclude all Core-15 equations/families and every equation/family used in the historical 74-case LLM calibration.
4. Allocate disjoint calibration and evaluation family IDs before generating any formulas. Each calibration category must contain at least 59 units; evaluation must be sized to attain the same risk-bound precision after expected abstention/invalid-score loss.
5. Generate deterministic training-only datasets and hash the source, canonical formula, and training rows. Edge rows/labels must be generated separately and withheld from formula-generation prompts.
6. Populate `config/tau_calibration_manifest.json` only after independent family review, then run `python scripts/validate_tau_calibration_manifest.py --require-ready`.
7. Add an evaluation manifest validator that rejects overlap with calibration, Core-15, and the historical 74-case cohort, and enforces accepted-route precision.

## What was deliberately not done

- No equations were invented, synthetically relabelled, or counted repeatedly to meet the threshold.
- No Core-15, historical calibration, or held-out evaluation records were moved into a new calibration cohort.
- No manifest was marked ready.
- No LLM/provider requests or paid API calls were made.
- No workflow was dispatched.
- No routing configuration or baseline artifact was changed.

## Outcome

The next valid step is to source and adjudicate a sufficiently large external equation-family registry, then freeze disjoint calibration/evaluation manifests. Until that exists and both validators pass, a paid calibration run would violate the approved protocol.


## External source landscape reviewed (2026-11-22)

A targeted source search identified several credible public research assets. They are **candidate source pools for expert extraction/adjudication**, not ready-made calibration cohorts. No source was imported or counted as independent equation units in this audit.

| Source | Publicly documented scope | Disposition for this protocol |
|---|---|---|
| [FinanceMath](https://financemath-acl2024.github.io/) (ACL 2024) | 1,200 finance reasoning examples across multiple subareas; each has expert-annotated Python-formatted solutions. The project site says test annotations/answers were released in July 2026. | Best near-term candidate for finance-domain extraction. It is a reasoning QA benchmark, not a deduplicated equation-family registry; tabular problems and repeated underlying formula families must be filtered. Extract only examples whose mathematical model is explicit and whose solution can be independently verified. Preserve original IDs, split, license, and solution provenance. |
| [formal-mathfin](https://github.com/formal-applied-math/formal-mathfin) | A Lean 4 mathematical-finance library; README reports 870 literature results, including stochastic calculus, pricing, fixed income, portfolio theory, and risk measures. | Strong formal-verification source for theorem/formula families, but the corpus is a theorem library rather than a tabular input/output benchmark. A separate, reviewed numeric problem specification and deterministic evaluator would be needed. Do not count theorem lemmas or variants as independent units without family-level adjudication. |
| [IL_Measurement](https://github.com/ThanosDrossos/IL_Measurement) | MIT-licensed Uniswap v3 study with 30,058 closed-position observations across nine pools, plus extraction/analysis code. | Relevant DeFi domain source, but 30,058 are position observations, not 30,058 independent equations. The nine pools and repeated position/burn events are clustered; the README also notes its legacy tick-math appendix is superseded and does not run as-is. Use only as empirical validation/context for a small number of explicitly sourced DeFi formulas, not as an independent-unit count. |
| [FinanceMath dataset card](https://huggingface.co/datasets/yale-nlp/FinanceMath) | Public validation/test dataset with Python solutions and ground-truth annotations. | Distribution and license details must be checked from the pinned dataset revision before use. Do not assume all 1,200 examples are unique equation families or eligible for formula-generation training. |

### Recommended next extraction path

1. Pin a specific FinanceMath dataset revision and license metadata; download only through a reproducible, offline-capable acquisition step and record revision/file hashes.
2. Extract candidate examples whose solution is a deterministic equation or model, excluding table-retrieval-only questions, multi-step accounting lookups, and examples with hidden external facts.
3. Independently map each candidate to a canonical equation-family ID; deduplicate algebraic rearrangements, parameter changes, and same-model question variants.
4. Use formal-mathfin declarations as independent references for theorem/model identity and correctness where applicable, not as extra observations when they express the same family.
5. Keep DeFi-specific formula families as a separately declared stratum if the target claim is DeFi. The IL_Measurement observations cannot be inflated into independent equation cases.
6. Have a reviewer not involved in formula generation adjudicate source correctness, formula equivalence, category assignment, and independence. Only then consider allocating disjoint calibration and evaluation cohorts.

### Feasibility conclusion

FinanceMath may provide a large enough *raw candidate pool* for broad finance categories, but the public project description does not establish 59 independent, eligible formula families in any one category. formal-mathfin may expand the verified reference library but requires task construction. IL_Measurement adds DeFi empirical context, not equation-family count. Therefore the approved manifest remains draft and empty; no external records are currently eligible for counting toward the 59-unit minimum.


## FinanceMath candidate extraction completed (offline, 2026-11-22)

The public source repository was inspected at immutable commit `bdc2b6b04252aa09630b66ec1e2a5c98e5a2794c`. Its source data blobs are pinned as:

- `data/validation.json`: Git blob `2c6027405c2fb3009d5d43ba14cc3eb45952fc61` (200 records).
- `data/test.json`: Git blob `75638f09072637df164a5602035da1c77e58b089` (1,000 records).

An offline metadata/code-shape screen produced a reviewer queue of all 1,200 source IDs in [financemath_candidate_registry.json](../data/external_candidates/financemath_candidate_registry.json). It records source split, source ID, topic, table count, solution-presence/length, screening class, and explicit blank adjudication fields. It deliberately does not redistribute full question text or solution code.

| Screening class | Records |
|---|---:|
| Text-only formula-shaped candidate | 610 |
| Table-dependent formula-shaped candidate | 439 |
| Procedural/library-shaped solution | 134 |
| Non-formula/lookup-shaped solution | 17 |
| **Total** | **1,200** |

The heuristic marks a record as formula-shaped when its Python solution contains arithmetic operators and no obvious loop/import/library tokens; table presence separates table-dependent from text-only candidates. This is intentionally a high-recall queue, not semantic equation extraction. It does not prove that a problem has a single closed-form model, that its formula is eligible for the restricted evaluator, or that two problems are different mathematical families.

All 1,200 entries remain `unreviewed`; family IDs are null; Core-15 and historical-74 overlap checks are unperformed; independence is not adjudicated; and cohort assignments are null. The 200/1,000 source split is preserved as provenance only. In particular, the test split must not be treated as an evaluation cohort until overlap, leakage, and protocol compatibility are independently established.

The FinanceMath GitHub repository has no declared repository license in its GitHub metadata, although its Hugging Face dataset card identifies MIT. This registry therefore stores only IDs and derived screening metadata, cites the source, and avoids redistributing the question/solution payload. The Hugging Face file access route separately requires acceptance of contact-information conditions; the extraction used the public GitHub source blobs at the pinned revision.

**Result:** a reproducible reviewer queue now exists, but the number of independent, eligible equation families is still **not established**. No entries were counted toward the 59-unit minimum; the calibration manifest remains draft and empty.


## FinanceMath provisional code-fingerprint clustering (2026-11-22)

A deterministic offline candidate-generation pass compared all 1,200 pinned FinanceMath Python solutions using a lightweight line-aware token scanner. It did **not** parse Python ASTs or assess mathematical equivalence. The scanner preserves identifiers, operators, literal values, and indentation transitions; comments and whitespace are ignored. A second fingerprint replaces numeric and string literals with placeholders while retaining identifiers and operators.

Results:
- 6 exact token-stream duplicate groups containing 12 records (1,188 exact-fingerprint singletons).
- 13 literal-normalized token-shape groups containing 28 records (1,172 literal-normalized singletons).
- All 1,200 source solutions were found.
- The exact and literal-normalized groups overlap; do not add their counts together.

These are **review leads only**, not equation families. Literal-normalized matches can represent different financial quantities or coincidental code shapes. Conversely, equivalent formulas can differ in variable names, algebraic form, or control flow and will be missed. The scanner is heuristic, and fingerprints use a non-cryptographic 64-bit FNV-1a code-point hash solely as deterministic grouping keys.

No candidate was adjudicated for formula correctness, canonical equation-family identity, overlap with Core-15 or the historical 74, statistical independence, or calibration/evaluation cohort eligibility. The candidate registry remains unchanged: all review states remain unreviewed, all family IDs remain null, and no cohort assignments were made. No LLM/provider calls were made.

Machine-readable output: `data/external_candidates/financemath_provisional_code_clusters.json`.
