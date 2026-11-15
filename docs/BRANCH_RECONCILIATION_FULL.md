# Full branch and code reconciliation register

Updated: 2026-11-14

## Scope and status rules

Requested source scope:
- `hypatiax/core/`
- `hypatiax/experiments/benchmarks/`
- `hypatiax/tools/`
- coupled configuration, runners, tests, scripts and GitHub workflows that affect reproducibility, ablation continuity, provenance or benchmark safety.

Status:
- **PASS — INCLUDE (static)** means static review only; no tests are implied.
- **APPLIED — USER TEST** means changed on this branch; tests remain for the user.
- **HOLD** means do not consolidate until the stated contract or safety issue is resolved.
- **PRESERVE** means retain as a separate experiment/audit path, not necessarily as the canonical benchmark.
- **REJECT WHOLE-FILE PORT** means do not take the competing file wholesale; isolated fixes may still be ported.

`master` is reference-only and has not been modified. This work is on `integration/consolidated-work`. No source branch, local stash or user work was deleted or cleaned up. No tests were run.

## Branch map

| Branch | Head commit | Comparison / disposition |
|---|---|---|
| `master` | `c80da69c6fe7987db1bd3a46da7ac17a035d3008` | Untouched reference |
| `promotion/rerun-code-review` | `7852a256c8d5708949463dc856f4e53044ebc85c` | Preferred source base; broadest reviewed implementation; 1,722 commits ahead, 2 behind |
| `fix/rerun-blockers` | `df09b77a2eba6e883b6a4b523d465320e5587c34` | Selective fixes only; 166 ahead; config and behavior regressions prevent wholesale merge |
| `fix/hybriddiscovery-timeout-repair` | `9d1bce1acb27aac6a1afb911daedae2df6803ad3` | Select bounded timeout/process cleanup and regression tests; 6 commits |
| `rerun/integration` | `d38aa940c5fcafcb4c8e8edf6cd73ef1a273def6` | Mostly inherited/duplicate changes; 140 commits; do not use HDS file that retries after hard timeout |
| `audit-main` | `3f04eeba7f62f16ba08c5d75c18efce435877ce0` | Older audit lineage; 102 commits; several files superseded by promotion |
| `sync/hypatiax-package-to-master` | `f232865c3ed08310aa5fa11ef1ab04d82b323b6e` | 4 unique commits, 115 changed paths overall; 11 scoped package paths are older variants |
| `integration/ci-workflow-fixes` | `f009b9ac9ebae98013e6d00b5cde4f21ce4c3b51` | Workflow lineage; 16 commits; important orchestration defects remain |
| `ci/update-smoke` | `a13a8cb9bf67feac4f494592b700c3de4219a917` | Four unique commits; scoped source tree matches integration/CI |
| `enable-fresh-rerun-dispatch` | `681624196fecc58bc06befe30776417e1680275a` | Workflow-only; references a missing launcher |
| `publication-readiness-review` | not re-recorded in this pass | Documentation-only; no source code consolidation |
| `integration/consolidated-work` | `f4588601dad81cbc4e7e0f64c1c6b5b4790d94c1` | Working consolidation branch; documentation and selective safe fixes only |
| `audit-master` | not re-recorded in this pass | 0 commits ahead / 15 behind; no unique source changes |
| `dependabot/pip/build-1.6.1` | not re-recorded in this pass | Dependency-only; separate compatibility review |
| `dependabot/pip/cachetools-7.3.0` | not re-recorded in this pass | Dependency-only; separate compatibility review |
| `dependabot/pip/kagglesdk-0.1.28` | not re-recorded in this pass | Dependency-only; separate compatibility review |
| `dependabot/pip/nltk-3.10.4` | not re-recorded in this pass | Dependency-only; separate compatibility review |
| `dependabot/pip/platformdirs-4.12.4` | not re-recorded in this pass | Dependency-only; separate compatibility review |
| `dependabot/pip/pure-eval-0.2.4` | not re-recorded in this pass | Dependency-only; separate compatibility review |

### Branch-family overlap and lineage

- `promotion/rerun-code-review` is the preferred base for core/benchmark implementation.
- `fix/rerun-blockers` contains valuable Phase 3 and audit work but is not a safe whole-branch merge. Its ablation runner lacks promotion's `dataset_override` interface; its default temperature and population settings drift; and it removes portfolio diagnostics and some symbolic package exports.
- `rerun/integration` has 10 scoped Python files identical to fix and 3 matching promotion; its distinct HDS implementation still retries after timeout.
- `audit-main` contains 17 scoped Python changes; 10 match integration/CI, while distinct DeFi/hybrid files are older than promotion.
- `sync/hypatiax-package-to-master` contains 11 scoped package changes; most are the same older audit lineage.
- `integration/ci-workflow-fixes` and `ci/update-smoke` share the same scoped source lineage.
- `fix/hybriddiscovery-timeout-repair` contributes targeted process cleanup and regression coverage; port only those bounded changes, not its old timeout-variable mapping.
- `integration/consolidated-work` already carries the broad experiment tree and Phase 3/audit artifacts. It was not replaced with a promotion-only tree; existing work is preserved.

## File-level reconciliation

The requested final columns are used below: head code, config, commits, branches, status and modification.

| Head code / file family | Config contract | Source commits | Branches | Status | Modification / decision |
|---|---|---|---|---|---|
| `hypatiax/core/llm_call.py` shared wrapper | Requested temperature 0.25; provider may reject/ignore it | promotion `1d6511c28b0802d077e8732e1aad4bcdd3c827ba`, fail-closed follow-up `d2e9ff8401c0838dafbf62c8e4f30c259b665138` | promotion, fix, rerun | HOLD | Keep promotion wrapper as comparison base. Decide strict fail-closed vs provider-default fallback with explicit `temperature_sent=false`. Never claim 0.25 was sent if not sent. |
| `hypatiax/core/llm_meta.py`, `llm_sens_adapter.py`, `exp3_nguyen12_consolidated.py` | Distinguish attempted/live/cached/empty/failed | promotion `c7604c25ddf36b459d0325e9346eb5581a03ba18`, `001d9a87f544fe22735c2b34847b652b8b477520`, `1292027c1db04286c6922ac1e2fa1650b3be60cf`; CI adapter `6ebf31f7a1dc` | promotion, fix, integration/CI | HOLD | Fix false `llm_called=True` and `llm_calls_ok` counts when API returns empty on failure or results come from cache. Provenance must be emitted at the provider/cache boundary. |
| `hypatiax/core/routing.py`, DeFi v3c and PCA callers | Shared edge fraction 0.15; calibrated tau must be versioned | routing `0f8f7248a91920319abe6db7be4359b06e2129b0`, validation `c38b81b5f346a5e534f38b5b0bb52c2139d07540`; v3c chain `406ced415b01`, `c4ef4dce4e96`, `05f6fff211e5`, `2ffc56861c7b`, `bf566d937c99`, `a1c4062a1cb4`, `fab95f7ebbc6`, `aaf2c21ffc77`, `fa3ccd974cb0`, `e3ee3237f29b`, `efc0fa15fac0`; PCA `89e53050a523`, `ff90977841a5`, `4e5003772d96`, `fb0b095a4c6d` | promotion | HOLD | `HYPATIAX_ROUTING_DELTA_TAU` is absent from canonical config, runner and workflow. Default routing fails closed to ensemble; default CI does not exercise the fitted-LLM route. |
| Strict JSON serialization and LLM metadata numeric checks | Collision-safe non-finite serialization; bool is not a number | promotion blob `cb18bd9717a054c2d316982f0a0629193b1bb6a9`; fix JSON lineage `5f2719885bcaeedf9cfdc45c5b41a3775dd7a14b` | promotion, fix | PASS — INCLUDE (static) | Retain promotion collision protection and bool rejection; do not replace with weaker fix variant. |
| DeFi LLM/NN hybrid | Shared wrapper; safe response text extraction | promotion / fix / audit variants | promotion, fix, audit-main, sync | HOLD | Promotion is preferred base. Replace direct `resp.content[0].text` indexing with first-text-block extraction to handle thinking blocks. |
| All-domains hybrid and pure LLM baseline | Shared provider provenance; distinct architecture labels | promotion and fix variants | promotion, fix, rerun, audit-main, sync | HOLD | Preserve robust text extraction and provenance. All-domains hybrid is plain MLP; NN-only ablation uses residual MLP. Do not conflate. |
| HybridDiscovery v50.2 timeout behavior | Per-attempt PySR timeout; no retry after hard timeout | promotion `ae3b302da62faca612c5e2669b4b95457cc1a07c`; repair `746670b68326470d2032f510df03e6d65620ebcf`; regression head `9d1bce1acb27aac6a1afb911daedae2df6803ad3` | promotion, fix/hybriddiscovery, rerun | PASS — INCLUDE (static) | Keep promotion behavior and timeout regression tests. Do not use rerun/integration HDS file that retries after timeout. |
| Random worker timeout | Per-attempt timeout | repair `07904977fb1ab9651f06f8304e3b2f768179d907` | fix/hybriddiscovery | HOLD | Compare against promotion v2 worker; do not duplicate without behavior diff. |
| PCA subprocess cleanup | Separate method/PySR timeouts; bounded kill and reap | repair `22c340b2a9a16864c3db38d91193dfda36d17964`, `40a6d97bc16a80d7ef79a96381e9484a1da36e62`, `b519f6f71067e49a29f78c6dbbd3b2a7bc2e4776` | fix/hybriddiscovery, promotion | HOLD / candidate | Promotion PCA runner still has unbounded cleanup `communicate()`. Port bounded cleanup only while preserving `FEYNMAN_METHOD_TIMEOUT` and `FEYNMAN_PYSR_TIMEOUT`; reject old mapping that assigns one FEYNMAN_TIMEOUT to both. |
| `exp1_ablation.py` | Model Sonnet 4.6; requested temp 0.25; niterations 1000; populations 30; population_size 33; PySR attempt 1100s; method 900s | promotion history `20ec5aa099c8`, `5b4856aad71f`, `c5ac9810f9a0`, `64f1b8f3f0ef`, `25a6a18c5e09`, `2920df5a1caa`, `e51762e5e930`, `3e11912e4ab7`, `65374a010640`, `5b9a7f86247d`, `b5cfb02bc213`, `100ab83c1b98`; fix history `fea104de8c5e`, `72748a72e637`, `0d32bef1286f`, `5f2719885bca`, `94421a450b7c`, `9faedb017938`, `5cc3ba3e3c5d`, `f2802ffe3235`, `1075973f91ab`, `ddb6016bd4c9`, `47d07813fc29`, `6f6eaf8f1ed2`, `00f87a313231`, `8d4f7625f61a`, `32c6d50df1bd` | promotion, fix, audit-main, sync | APPLIED — USER TEST | Current integration branch now defaults to 0.25 and population_size 33. Promotion's `dataset_override` API remains preferred; do not pair its adapters with fix ablation variant. |
| `config/repro.yaml` and `run_all.sh` | Candidate source of truth for model/temp, PySR settings and separate timeout budgets | promotion config `8df4fcb78efc517c526647a60d871ebd8c7c506e`; fix config `0739eb47c3d6432d732e9c327807cb9eced7115d`; config contract `e05e9597cc7efb4801ea98b7966901b76f9232e0` | promotion, fix, rerun, audit-main, sync | APPLIED — USER TEST / HOLD | Added `llm_temperature: 0.25`; runner defaults now export model and temperature. Remaining aliases `PYSR_GENERATIONS` and `PYSR_POPULATION` need semantic mapping before being equated with niterations or population_size. |
| Four-way matched ablation | Shared arrays/fingerprint; residual NN-only arm; shared wall clock | promotion additions; summary `7b3f528df8d08765e84d93658afba3b96d516d96` | promotion | PRESERVE | Keep. Shared data and wall clock do not establish equal compute budgets. |
| Five-system ablation | HDS v50.2 subprocess/no-LLM path | promotion branch | promotion | PRESERVE | Keep as distinct benchmark; task IDs and compute profile are not interchangeable with four-way arms. |
| `exp3_nguyen12_consolidated.py` | Cache key must cover model, candidate count, K, PySR budgets, timeouts and LLM gates | `77cb58c57969`, `32c154b8f5d6`, `96352321ba55`, `eb860b2da97a` | promotion, rerun | HOLD | Existing cache checks schema/sparse mode/targeted request but omits several effective settings. Empty return can be counted as successful LLM call. |
| Multi-seed ablation summary | Equation-level paired unit; missing/failed cells; Holm correction | shared blob `7b3f528df8d08765e84d93658afba3b96d516d96` | promotion, fix | PASS — INCLUDE (static) | Retain summary aggregation; user runs tests. |
| Phase 3 workflow, runner and closure | Distinct profile; 3600s wall clock is not the comparative 900s method timeout | workflow `25fa2a33eda1373e4129cdc45d06a7628149db3e`; modifications `d1425c26ca1e200d15782f00779560b40db62ec3`, `e0dd8f17e60b9332e5b5c07f2aeabece42987900`, `ec268966aa4cdb1e48fa439a0be8f19584db760c`, `60faedad596649f07f0657fe4fac301296612edd`, `14aa08e4223875cf2f4da32f34422f1a4161dd71`; runner/closure `9a2490287d7e5386cf1fe1eea8fee543bb36ecf6`, `49f93399464197d0b63a9aeae73a2e2243325857` | fix, audit-main, sync; removed in promotion | PRESERVE / HOLD | Retain Phase 3 code and workflow as a separate profile. Do not silently merge its budget into canonical comparative settings. |
| Core-295 catalogue/adapters | Target 295; current manifest 24 proposed, 0 accepted; generator pending | `040c50675109`, `0f006490aadb`, `300e790959d4`, `f24ff5deb57d`, `c6f6e1d6df7d` | promotion | HOLD | Keep planner/parser/adapters; do not call this a runnable 295-case benchmark until 295 entries are accepted/ready. |
| `extrap_r2_far.py` | No config change | promotion branch; integration branch has `import re` | promotion, rerun, audit-main, sync | PASS — INCLUDE (static) | Missing `re` import in promotion is already present on integration branch; do not reapply. |
| `portfolio_variance_v3c2.py` | Preserve seed 0; safety guard before any execution/early exit | integration branch working file | promotion/master-derived and fix lineages | APPLIED — USER TEST | Fixed `_resolve_seed() or 42` so explicit seed 0 survives; moved fail-closed guard ahead of work and early-exit paths. |
| Portfolio diagnostics and PCA split helpers | Audit diagnostics are separate from canonical routing split | fix branch deletes four diagnostics; promotion/master retain them | promotion/master, fix | PRESERVE | Keep bootstrap PCA, feature ranking, partition validation and PCA tail-error diagnostics. Do not conflate raw/transductive PCA with standardized training-only routing split. |
| `run_hybrid_system_benchmark.py` orchestration | Shards must consume task IDs and isolate checkpoints | `8d502fd516d3`, `0cafeaa9b91a` | integration/ci-workflow-fixes, ci/update-smoke | HOLD | Child consumers ignore task/shard IDs, shared checkpoint can collide, and substep failures can be lost. |
| `run_noise_sweep_benchmark.py` | Exact seed/noise metadata required for cache hit | `6ebf31f7a1dc`, `0cafeaa9b91a` | integration/ci-workflow-fixes, ci/update-smoke | HOLD | Missing noise metadata currently matches; latest-file fallback can reuse stale output. |
| `run_instability_suite.py` | Require minimum valid runs; classify failure frequency separately | `0cafeaa9b91a` | integration/ci-workflow-fixes, ci/update-smoke | HOLD | One valid run plus many failures can produce std=0 and be misclassified stable. |
| LLM-generated code in `hybrid_ensemble_system_defi_domain.py` | Never execute untrusted model code with unrestricted builtins | integration/CI branch | integration/ci-workflow-fixes, ci/update-smoke | REJECT WHOLE-FILE PORT | Replace unrestricted `exec(python_code, ns)` with restricted formula AST evaluator before production use. |
| Safe SymPy parser and validator callers | Preserve restricted parser for untrusted expressions | parser/tests deleted in integration/CI branch; validator changes use `sympify` | master/promotion vs integration/CI | HOLD | Do not port validator changes that bypass restricted parser. |
| `hypatiax/tools/symbolic/__init__.py` exports | Preserve lazy `__getattr__` and package-level imports | fix commit `1e1da868d101` | fix vs promotion | REJECT WHOLE-FILE PORT | Fix version removes lazy exports while leaving names in `__all__`; imports may fail. |
| Fresh rerun workflow | Workflow must call an existing launcher | `enable-fresh-rerun-dispatch` head `681624196fecc58bc06befe30776417e1680275a` | enable-fresh-rerun-dispatch, promotion, rerun | HOLD | `ci_fresh_rerun.yml` references missing `ci_runner/run_fresh_experiments.sh`; do not enable until launcher exists. |
| Dependabot branches | Dependency changes only | build 1.6.1; cachetools 7.3.0; kagglesdk 0.1.28; nltk 3.10.4; platformdirs 4.12.4; pure-eval 0.2.4 | dependabot/* | SEPARATE REVIEW | Keep out of source merge; assess dependency compatibility independently. |

## Canonical settings and separate profiles

Main comparative defaults to keep aligned:
- model: `claude-sonnet-4-6`
- requested temperature: `0.25` (provider support is separate; record sent/not sent)
- PySR niterations: `1000`
- populations: `30`
- population_size: `33`
- PySR attempt timeout: `1100s`
- method timeout: `900s`
- fit wall timeout: `1200s`

Keep separate profiles explicit:
- Phase 3 ablation wall-clock: `3600s`
- Feynman/PCA and instability have separately named timeout keys.
- physics fallback/detector settings are a fallback profile, not canonical PySR.
- four-way matched arms share data and wall clock, not necessarily equal compute.

## Outstanding blockers

1. Decide provider temperature policy: strict failure vs provider default with explicit `temperature_sent=false`.
2. Calibrate/version routing tau or explicitly label default CI as ensemble-only.
3. Distinguish live LLM calls from cache, empty results and failures.
4. Expand Exp3 cache fingerprint to all effective settings.
5. Version Phase 3 profile and retain its workflow without mixing budgets.
6. Fix actual sharding, checkpoint isolation and substep failure propagation.
7. Require exact noise metadata for noise-sweep cache hits.
8. Add minimum-valid-run criteria to instability analysis.
9. Replace unrestricted LLM-generated code execution and retain safe SymPy parser.
10. Port bounded PCA process cleanup without merging timeout budgets.
11. Add the missing fresh-rerun launcher or disable the workflow.
12. Complete Core-295 accepted manifest; current state is 24 proposed / 0 accepted.
13. Map `PYSR_GENERATIONS` and `PYSR_POPULATION` aliases by semantics before asserting parity.

## Changes applied on integration/consolidated-work

Commit `f4588601dad81cbc4e7e0f64c1c6b5b4790d94c1`:
- `config/repro.yaml`: added `llm_temperature: 0.25`.
- `run_all.sh`: added canonical default exports for `LLM_MODEL` and `LLM_TEMPERATURE`.
- `exp1_ablation.py`: changed default requested temperature from 0.3 to 0.25 and `population_size` from 50 to 33.
- `portfolio_variance_v3c2.py`: preserve explicit seed 0 and enforce safety flags before benchmark work and early exits.
- Added `hypatiax/experiments/tests/test_repro_contract_parity.py` with offline static assertions.

**Verification state:** changes are APPLIED — USER TEST. Tests were not executed. This commit does not resolve the provider temperature limitation or all remaining config aliases. No merge to `master` occurred.
