# Fresh rerun readiness register

**Review baseline:** `master` at `34f574de8ab12222a8371325529ff952f28f302e` (2026-11-15).  
**Scope:** focused rerun-readiness review; this is not a full line-by-line repository audit.  
**Validation policy:** no tests or experiments were run during this review. Static review findings are not test passes.

## Current disposition

The repository is **not yet ready for the full fresh experiment rerun**. The merged master contains the consolidated config defaults and reproducibility contract checks, but it does not yet contain the fresh-run launcher and protocol files that exist on `promotion/rerun-code-review`.

## Blocking items

1. **Fresh-run entry point is absent from master.**  
   `ci_runner/run_fresh_experiments.sh` and `config/fresh_rerun.yaml` return 404 on master. The promotion branch contains them, but its PR (#100) is a 325-file, 1,722-commit comparison, is currently not mergeable, and must not be merged wholesale. Port the minimum dependency-complete set onto a clean branch based on current master.

2. **LLM temperature/provenance is not uniform across every experiment path.**  
   The promotion shared wrapper `hypatiax/core/llm_call.py` hard-codes 0.25 and fails closed if the provider rejects it. However, `hypatiax/experiments/benchmarks/hypatia.py` makes a direct Anthropic request and documents temperature as a no-op. It must not claim that a 0.25 request was sent. The `llm_sens_adapter.py` path also currently sets `llm_called=True` before establishing that a live call returned candidates. Define and record distinct states for live API success, cache replay, missing credentials, provider failure, and empty/invalid candidates.

3. **Routing is ensemble-only until tau is calibrated.**  
   The promotion fresh protocol has `routing_policy.degradation_tau: null` with status `requires_separate_training_only_calibration`. This intentionally fails closed to the ensemble. A rerun using this config must be described as ensemble-only; do not claim the calibrated pure-LLM route was exercised. If that route is required, complete and version the training-only tau calibration first.

4. **Protocol-30 execution is wired but not yet validated as part of a fresh campaign.**  
   The promotion protocol labels Protocol-30 `wired_not_executed`. Verify method/task/shard filtering, result isolation, aggregation, and provenance on a fresh smoke run before including its results in manuscript claims.

5. **Core-295 is not a runnable 295-equation benchmark yet.**  
   The catalogue currently has 0 accepted entries out of 295 target entries. Keep its discovery/review tooling, but do not count it as an executable experiment until the manifest and generator contracts are complete.

6. **Phase 2 and Phase 3 remain deferred.**  
   The promotion fresh protocol explicitly defers Pure-LLM Phase 2 and Phase 3 pending fresh-input contracts and gates. Preserve their code and ablation work, but do not silently include historical outputs or report these phases as freshly reproduced.

7. **Timeout repair is a separate focused change awaiting branch-head validation.**  
   PR #108 contains six focused commits affecting the PCA and Random subprocess launchers and HybridDiscovery retry behavior, plus regression tests. The PR description explicitly says its head has not been targeted-validated and remains draft. Run the targeted tests on the PR head, then merge only after reviewing their results.

## Config/profile rules

- Keep the canonical comparative profile distinct from any Phase 3 or diagnostic profile with different compute budgets.
- Current master defaults include LLM model `claude-sonnet-4-6`, LLM temperature `0.25`, PySR populations `30`, population size `33`, PySR attempt timeout `1100s`, fit wall timeout `1200s`, and method timeout `900s`.
- Do not collapse method timeout and PySR timeout into one value.
- Keep ablation code and label deferred arms explicitly rather than deleting them.

## Branch handling

- Retain `promotion/rerun-code-review`, `fix/rerun-blockers`, and `fix/hybriddiscovery-timeout-repair` until their unique useful changes are ported or explicitly rejected.
- Do not merge the promotion or rerun-blockers branches wholesale; their comparison histories are very large and include unrelated documentation/results.
- Delete no branch containing unported unique code. The stale/fully merged branch candidates can be removed after a complete ref/PR inventory and a final containment check.

## Acceptance checklist before a full rerun

- [ ] A clean, current-master-based PR adds a dependency-complete fresh launcher, fresh protocol, and manual workflow.
- [ ] Every experiment stage named by the launcher exists in `run_all.sh`, and the launcher does not invoke a deferred stage.
- [ ] A dry-run smoke check validates all stage dispatches without executing experiments.
- [ ] Targeted tests cover live LLM provenance, unsupported temperature behavior, cache exclusion, checkpoint isolation, and result metadata.
- [ ] Timeout repair tests pass on the exact candidate merge head.
- [ ] A fresh one-equation/one-task smoke run writes only to a new external output directory and produces a complete manifest.
- [ ] The full fresh run is launched only after the smoke run and dependency/runtime checks pass.
- [ ] Fresh outputs are reviewed separately; historical expected values are not used as inputs to the run.

## Suggested fresh-run command

Once the launcher and its complete dependency set have been merged and validated:

```bash
RESULTS_DIR=/absolute/path/outside/repository/hypatiax-fresh-run-<unique-id> \
  bash ci_runner/run_fresh_experiments.sh
```

The output directory must be new/empty and outside the repository. Supply the API credential through the execution environment; never put it in the protocol, logs, or committed files.

## Review boundary

This register records static findings and known branch state. It does not certify test success, scientific reproducibility, complete Core-295 readiness, Phase 2/3 readiness, or a completed fresh rerun.
