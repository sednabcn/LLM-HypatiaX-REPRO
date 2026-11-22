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
