# Fresh rerun readiness register

**Review baseline:** `master` at `cce7f8673eeb1c8f37bb64a1bef0db461fa2512b` (2026-11-15).  
**Scope:** focused static review of the fresh-run launcher, Protocol-30 execution metadata, merged CI work, and remaining campaign gates.  
**Validation policy:** no local tests or experiments were run for this update. CI on the proposed PR and user-side experiment runs remain separate acceptance gates.

## Current disposition

The repository has a fresh-run entry point and protocol on master:

- `ci_runner/run_fresh_experiments.sh`
- `config/fresh_rerun.yaml`

The launcher is a single-job campaign runner. Its declared stages were checked against `run_all.sh`; every declared stage has a corresponding stage definition. The separate five-shard aggregation stages are intentionally not in this launcher:

- `exp1_four_way_matched_aggregate` consumes downloaded Core-15 worker artifacts.
- `exp2_protocol30_random_8020_aggregate` and `exp2_protocol30_pca_4060_aggregate` validate and merge five Protocol-30 worker artifacts.

Do not append these aggregation stages to the single-job launcher without changing its execution model and artifact contract.

A remaining metadata gap was found: the Protocol-30 stages wrote `protocol30_shard_manifest.json` only when `TASK_IDS` was set. The normal full-run path does not set `TASK_IDS`, so it produced benchmark outputs without the registry-bound Protocol-30 execution manifest. The focused change proposed alongside this register writes a manifest for both modes:
- Full single-job execution: all 30 equation identities, `n_shards=1`, and `official_aggregate_eligible=false`.
- Five-shard worker execution: the explicit worker assignment and existing five-shard aggregation eligibility.
- Smoke execution: only the selected equation(s), marked as smoke and excluded from official aggregation.

## Merged and validated work

- **PR #111** is merged. It adds the LLM provenance and non-finite input gates. Pure-LLM routing remains disabled pending separate training-only calibration.
- **PR #113** is merged. It adds bounded PCA subprocess timeout cleanup, HybridDiscovery timeout regression tests, and explicit CI execution of those tests. The targeted timeout regressions and full pinned Python 3.12 CI jobs passed before merge.
- **PR #108** is closed and superseded by #113; do not reopen or merge it.

These CI results validate code contracts, not the scientific results of a new campaign.

## Remaining blockers and constraints

1. **Protocol-30 full-run manifest change:** review and pass CI for the focused change that emits manifests in both single-job and sharded modes. The five-shard aggregator must continue to reject single-job and smoke manifests as worker artifacts.
2. **Dry-run dispatch:** run `bash ci_runner/run_fresh_experiments.sh --dry-run` on a clean current-master checkout. This validates stage dispatch only; it does not prove that experiment dependencies or live providers work.
3. **One-equation smoke:** run a fresh Protocol-30 smoke task in a new external output directory. Confirm the result JSON, registry identity mapping, effective temperature, and smoke/non-aggregate flags. Keep smoke outputs out of official campaign aggregation.
4. **Runtime preflight:** confirm Python 3.12, the pinned Python package versions, Julia 1.11, PySR warm-up, and a live API preflight using the configured model and temperature.
5. **Full campaign:** launch only after the smoke and runtime preflights pass. Preserve the run manifest, stage logs, Python freeze, Julia version/status/manifests, and all result artifacts.
6. **Post-run audit:** verify output provenance and completeness separately from historical paper targets. Do not treat a successful process exit as proof that every method produced a valid candidate.

## Scientific/profile rules

- The fresh protocol uses `claude-sonnet-4-6` at effective LLM temperature `0.25`.
- Keep the canonical comparative profile distinct from diagnostic or Phase 3 profiles with different compute budgets.
- Do not collapse method timeout, PySR attempt timeout, and fit wall-clock timeout into one setting.
- Preserve all ablation implementations and label deferred arms explicitly.
- Routing remains ensemble-only while `routing_policy.degradation_tau` is null and marked as requiring separate training-only calibration. Do not claim that the calibrated pure-LLM route was evaluated.
- Core-295 remains gated on its accepted-record and generator/manifest contracts; discovery tooling is not itself a completed 295-equation benchmark.
- Pure-LLM Phase 2 and Phase 3 remain deferred pending fresh-input contracts and gates. Do not substitute historical `p2/` or `phase2_out/` data.

## Branch handling

- Do not merge `promotion/rerun-code-review` wholesale. Its comparison history is large and includes unrelated work; port useful changes selectively.
- Keep `fix/rerun-blockers` separate; it targets `audit-main`, not `master`.
- Keep experiment profiles and ablation variants distinct.
- Retain branches with unique, unported code until a containment review confirms that their useful changes are represented elsewhere.

## Acceptance checklist before a full rerun

- [ ] Protocol-30 full-run manifest change is merged with green CI.
- [ ] Current-master checkout is clean and the launcher points to the intended protocol file.
- [ ] `bash ci_runner/run_fresh_experiments.sh --dry-run` dispatches every declared stage successfully.
- [ ] Runtime dependency and provider preflights pass.
- [ ] A one-equation smoke run writes a complete registry-bound manifest and isolated output.
- [ ] Smoke artifacts are explicitly excluded from official aggregation.
- [ ] The full fresh campaign completes with all stage statuses recorded.
- [ ] Fresh outputs are reviewed separately; historical expected values are not used as run inputs.

## Suggested fresh-run command

After the above gates are satisfied:

```bash
RESULTS_DIR=/absolute/path/outside/repository/hypatiax-fresh-run-<unique-id> \
  bash ci_runner/run_fresh_experiments.sh
```

The output directory must be new/empty and outside the repository. Supply API credentials through the execution environment; never put secrets in the protocol, logs, or committed files.

## Review boundary

This register records static repository state and the proposed metadata repair. It does not certify that the proposed change has passed CI, that a fresh campaign has been run, that Core-295 is complete, that Phase 2/3 are ready, or that manuscript results have been reproduced.
