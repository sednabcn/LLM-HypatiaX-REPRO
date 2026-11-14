# Code reconciliation registry (working inventory)

Updated: 2026-11-14

## Purpose and safety boundary

This is a source/commit registry for the requested first-pass scope:
- `hypatiax/core/`
- `hypatiax/experiments/benchmarks/`
- `hypatiax/tools/`
- the directly coupled ablation/configuration/CI files needed to preserve ablation continuity and configuration parity.

The registry records source branches and commits so that later consolidation can be traced to its origin. It is not a test report and it does not imply that unreviewed code is approved. `PASS — INCLUDE` means static review only, not test success. `INSPECT — HOLD` means do not consolidate until the competing implementation or parameter contract is resolved.

**Safety:** `master` is the reference and remains untouched. This document is being recorded on `integration/consolidated-work` only. No source code is merged by this registry commit. Do not delete source branches or stashes.

## Branch tips recorded

| Branch | Tip commit |
|---|---|
| `master` | `c80da69c6fe7987db1bd3a46da7ac17a035d3008` |
| `promotion/rerun-code-review` | `7852a256c8d5708949463dc856f4e53044ebc85c` |
| `fix/rerun-blockers` | `df09b77a2eba6e883b6a4b523d465320e5587c34` |
| `fix/hybriddiscovery-timeout-repair` | `9d1bce1acb27aac6a1afb911daedae2df6803ad3` |
| `rerun/integration` | `d38aa940c5fcafcb4c8e8edf6cd73ef1a273def6` |
| `audit-main` | `3f04eeba7f62f16ba08c5d75c18efce435877ce0` |
| `sync/hypatiax-package-to-master` | `f232865c3ed08310aa5fa11ef1ab04d82b323b6e` |
| `integration/ci-workflow-fixes` | `f009b9ac9ebae98013e6d00b5cde4f21ce4c3b51` |
| `ci/update-smoke` | `a13a8cb9bf67feac4f494592b700c3de4219a917` |
| `enable-fresh-rerun-dispatch` | `681624196fecc58bc06befe30776417e1680275a` |

## Registry: reviewed code families and source commits

### Core LLM, routing, metadata and JSON

| File/family | Source branch | Source commit(s) / blob | Status and notes |
|---|---|---|---|
| Shared fixed-temperature LLM wrapper | `promotion/rerun-code-review` | `1d6511c28b0802d077e8732e1aad4bcdd3c827ba`; fail-closed follow-up `d2e9ff8401c0838dafbf62c8e4f30c259b665138) | INSPECT — HOLD. Promotion pins 0.25 and fails closed; fix branch has env-driven temperature and retry behavior. Resolve one protocol. |
| LLM call-local provenance | `promotion/rerun-code-review` | `c7604c25ddf36b459d0325e9346eb5581a03ba18`; additional provenance changes `001d9a87f544fe22735c2b34847b652b8b477520`, `1292027c1db04286c6922ac1e2fa1650b3be60cf) | INSPECT — HOLD. Review together with wrapper and engine callsites. |
| Routing diagnostics / OOD weighting | `promotion/rerun-code-review` | `0f8f7248a91920319abe6db7be4359b06e2129b0` and later validation `c38b81b5f346a5e534f38b5b0bb52c2139d07540) | INSPECT — HOLD. Promotion adds `hypatiax/core/routing.py`; fix branch does not carry an equivalent module at the compared tip. |
| Core-15 NN/probe primitives | `promotion/rerun-code-review` | `9aa8d82ea52f8f88fc1c94dc04fe0a3c8e666975` | INSPECT — HOLD. Later commits explicitly describe these helpers as prototype/not integrated; do not treat as production path without call-graph verification. |
| Strict JSON serialization | `promotion/rerun-code-review` / `fix/rerun-blockers` | promotion blob `cb18bd9717a054c2d316982f0a0629193b1bb6a9`; fix introduced by `5f2719885bcaeedf9cfdc45c5b41a3775dd7a14b) | PASS — INCLUDE, provisional static review. Promotion protects caller JSON keys from non-finite marker collisions. |
| LLM metadata numeric validation | `promotion/rerun-code-review` | reviewed blob `llm_meta.py` (branch comparison) | PASS — INCLUDE, provisional static review. Promotion rejects booleans as numeric metadata; verify exact blob again when staging. |

### Benchmark and symbolic tools

| File/family | Source branch | Source commit(s) | Status and notes |
|---|---|---|---|
| Comparative benchmark v2 worker timeout | `promotion/rerun-code-review` | `0f8bfea08e3c4b26d6dd99173bdb5b29554f9c98`; timeout-budget alignment `1142ceda1b20b8d6120d74684a223639f727b04c`; worker comment follow-up `b89ebd3204464bdef4135a94604588af604d8581` | INSPECT — HOLD until per-attempt environment and timeout budget parity are verified. |
| Comparative benchmark PCA worker timeout | `promotion/rerun-code-review` | `33059532849974f4c6699bdbd864b8e3d495d754`; process-group cleanup `1a9fad2fc420dc63eb5fc4a767d9926e4488a312) | INSPECT — HOLD. |
| PCA timeout cleanup hardening | `fix/hybriddiscovery-timeout-repair` | `22c340b2a9a16864c3db38d91193dfda36d17964`; signal import `40a6d97bc16a80d7ef79a96381e9484a1da36e62`; bounded cleanup `b519f6f71067e49a29f78c6dbbd3b2a7bc2e4776` | Candidate to preserve. The bounded post-kill `communicate(timeout=10)` is a meaningful difference from promotion's unbounded cleanup wait. Review together as one dependency chain. |
| Random worker per-attempt timeout | `fix/hybriddiscovery-timeout-repair` | `07904977fb1ab9651f06f8304e3b2f768179d907` | Compare with promotion's `0f8bfea08e3c4b26d6dd99173bdb5b29554f9c98`; do not duplicate without checking exact behavior. |
| Hybrid symbolic retry stop on hard timeout | promotion and timeout repair | promotion `ae3b302da62faca612c5e2669b4b95457cc1a07c`; timeout repair `746670b68326470d2032f510df03e6d65620ebcf` | PASS — INCLUDE, provisional. Core behavior already exists in promotion; retain regression coverage from repair branch. |
| Symbolic input validation / non-finite handling | `promotion/rerun-code-review` | `a86ec15b303940ad5039f6544de7fc45526d3ad0`, `58ef91001661999d0bb877c15b63dfe22c66f276), `ada9d74e8c8837edd0a6d305871ef729017034b2), `851888e93f6e921c39f69ee711529a2c02d97d59` | INSPECT — HOLD. Review full validation path, error propagation, and tests. |
| DeFi benchmark result adapter / shape validation | `promotion/rerun-code-review` | `e840f26faaee200a8a3e1e6b464d8a6fb4947fab`, `2a59886ccbed04627d29a0c922793aa9e0daa30a`, `33946e4c3340fe28a51649c8961f970f00696520), `6c0c86f82e0bc3e864c2da986a73400731f25991` | INSPECT — HOLD. Review as a coherent adapter/result-shape chain. |
| PCA split and resampling diagnostics | `fix/hybriddiscovery-timeout-repair` | `42c308e514f4190fc44d55f126ad65a66d200909`, `910b58695d0ae6d91dd564305c2dd0bea0d6f280`, `47075302bee6d2e9ab608e6b64a2beec02c407e1` | INSPECT — HOLD. Preserve diagnostic metadata and auditability; compare tests and downstream readers. |

### Ablation, configuration and CI continuity

| File/family | Source branch | Source commit(s) / blob | Status and notes |
|---|---|---|---|
| `exp1_ablation.py` promotion variant | `promotion/rerun-code-review` | blob `4017d9edf5caf88e8992d59a07416bd77971356a); temperature/provenance commits `c5ac9810f9a03d24c69934b4d33722bad0455897`, `20ec5aa099c8f06f8db5415434360650055657e3) | INSPECT — HOLD. Uses fixed 0.25; includes extra wall-clock limit argument; PySR call has population_size=50 versus config 33. |
| `exp1_ablation.py` fix variant | `fix/rerun-blockers` | blob `feb1071a07fd91e6f56111ab444ca1a3128a6e98); sanitizer/config audit `47d07813fc29df8741791100dc38fd14e9b13724); R² and provenance follow-ups `fea104de8c5e8cb8b8dc1ef7c32e37885e93d040`, `72748a72e637e6eed96a2676a7240d5d38d317d5) | INSPECT — HOLD. Defaults temperature from environment (0.3); must be reconciled with config 0.25. |
| `config/repro.yaml` | promotion / fix | promotion blob `8df4fcb78efc517c526647a60d871ebd8c7c506e`; fix blob `0739eb47c3d6432d732e9c327807cb9eced7115d); config contract commit `e05e9597cc7efb4801ea98b7966901b76f9232e0) | INSPECT — HOLD. Shared keys align in places, but CI environment values and runner-level overrides differ. |
| Phase 3 workflow | `fix/rerun-blockers` | initial `25fa2a33eda1373e4129cdc45d06a7628149db3e`; replay/smoke `e0dd8f17e60b9332e5b5c07f2aeabece42987900); dirty-check fix `d1425c26ca1e200d15782f00779560b40db62ec3) | PRESERVE. Promotion removes this workflow relative to master; deletion is a blocking continuity regression. |
| Phase 3 runner / closure | `fix/rerun-blockers` | base switches/adapter/runner/closer `9a2490287d7e5386cf1fe1eea8fee543bb36ecf6); default/STRICT switches `49f93399464197d0b63a9aeae73a2e2243325857) | PRESERVE and inspect all adapters, closure fields, replay/cache, seeds, provenance, and resumability. |
| Multi-seed ablation summary | promotion and fix | identical blob SHA `7b3f528df8d08765e84d93658afba3b96d516d96) | Same source bytes on both branches; correctness review still required. |
| Ablation sanitizer metadata tests | promotion / fix | promotion blob `cb18bd9717a054c2d316982f0a0629193b1bb6a9` | INSPECT — HOLD. Test suite currently exposes workflow/config wiring mismatch. |

## Configuration parity blockers

The following discrepancies are observed and must be resolved before the affected family can be marked PASS:

1. `LLM_TEMPERATURE`: promotion ablation uses 0.25; fix ablation defaults to 0.3; protocol config specifies 0.25.
2. PySR population: ablation runner uses `population_size=50`; `config/repro.yaml` specifies 33.
3. Workflow CI values differ between branch variants: promotion config exports PYSR generation/population values 1000/33, while fix/workflow material includes 10000/100 in relevant CI settings. Confirm whether these are truly distinct PySR knobs; if so document their mapping and why. Otherwise align them.
4. `ci_phase3_ablation.yml` has its own environment settings. Verify every shared research parameter against the canonical config and explicitly document any intentional Phase 3 override.
5. The sanitizer metadata test expects `ci_runner_repro.yml` not to shadow model/temperature from `config/repro.yaml`; current workflow/test combination must be made consistent.

Use `config/repro.yaml` as the candidate research-parameter source of truth. Any legitimate CI-only override must be explicit, justified, and tested. Compare values and semantics across YAML, Python, shell runners, workflow env, and tests—not merely variable names.

## Review status summary

- PASS — INCLUDE (provisional static review): strict JSON collision handling; LLM metadata bool rejection; shared timeout-stop behavior.
- Candidate to preserve: PCA bounded cleanup and the Phase 3 ablation workflow/runner/closure chain.
- INSPECT — HOLD: LLM wrapper policy, routing integration, symbolic engine integration, competing benchmark runner variants, ablation runner variants, configuration parity, sanitizer tests.
- Not reviewed to completion: the full contents and call graph for every changed file in the requested directories, all test coverage, all source branches, and generated-result consumers.

## Next review pass

Continue file-by-file through the requested directories, including callers, tests, config consumers, and generated-result readers. For every eventual inclusion, record the exact source branch, source commit, and blob SHA in this ledger. No source-code integration or master update is authorized by this inventory alone.
