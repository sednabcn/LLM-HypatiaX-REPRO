# Phase 2 run spec: Pure LLM baseline vs HDS v50_2, matched time budget

Draft of 27 October 2026. Companion files: `phase2_pure_llm_config.yaml` (run config), `phase2_row_schema.json` (per-case row schema), `reflatten_fields.py` (sensitivity re-flatten).

**What this is and is not.** This is the run design for the comparison Option 3 specifies for Phase 2: Pure LLM against full HDS v50_2 on identical equations, splits, seeds, evaluation rules and time budget. It has not been run. The Pure LLM runner was not available when this was written, so the config keys describe the interface the runner needs, not an existing command line. Items marked **VERIFY** were read from existing rows or code and not re-checked against the runner. Items marked **DECIDE** have no safe default and must be set before the first run.

## 1. Starting point

Already established for the PySR-only vs HDS comparison (45 + 45 rows, 15 equations, seeds 42, 99, 123):

- Both systems were scored by the same wrapper (`exp1_ablation._safe_r2`, which calls `r2_scored`) with the frozen scorer `hypatiax/core/r2_canonical.py` (SHA-256 `7d5395ed…`, matches `freeze_manifest.json`; label `r2_canonical@8f11733`). Sign-flip credit is off.
- Split IDs match between systems for every case checked (Arrhenius and Impermanent Loss, all seeds).
- The `r2` field of every p2 row is `extrap_r2_far` (verified for all 90 rows).
- HDS rows come from the `hypatia` block (LLM enabled), not `hypatia_nollm`.
- HDS runtime: median 128 s, maximum 729 s, 0 of 45 rows above 1,400 s.

The Pure LLM arm must meet the same conditions. Section 7 turns them into gates.

## 2. Decisions to settle before the first run

| ID | Decision | Recommended default | Why it matters |
|---|---|---|---|
| D1 | Time budget B | 1,400 s wall-clock per case, the PySR-only budget (1,100 + 300) | One number shared by all three systems; see section 3 |
| D2 | How HDS meets B | R0: reuse the existing 45 rows as "compliant by observation". R1: rerun HDS with `timeout_s = 1400` | R1 is needed only if the text will say "equal budget" without qualification |
| D3 | Pure LLM prompt inputs | Exactly what the HDS LLM stage receives, nothing more (**DECIDE**) | If either prompt includes the equation name, "recovery" partly measures recall of textbook formulas; parity keeps the comparison fair but the interpretation must say so |
| D4 | Constant fitting | None: score the formula as emitted | A fitted variant is a different system and must be a separate labelled arm |
| D5 | Sampling | One sample per (equation, seed); temperature and `max_tokens` equal to the HDS LLM stage (**DECIDE**) | As far as I know the Messages API has no sampling seed (**VERIFY** in the current docs), so `seed` fixes the data only and LLM variance is not controlled by it |
| D6 | Retries | Allowed on API error or unparseable output, up to a fixed maximum (**DECIDE**), all inside B and all counted in `n_llm_calls` | An unbounded retry loop is a hidden budget |
| D7 | Timeouts | Row is written with `status = timeout`, `r2 = null`, and counts as not recovered | Dropping timed-out cases would flatter the slower system |

## 3. Time budget

**What "matched" means here.** Matched cap, not matched spend. All systems get the same hard wall-clock cap B per case. Because the Pure LLM will probably finish in a small fraction of B (not measured; the dry run in section 8 measures it), the cap is a ceiling on the worst case. Actual spend is therefore reported separately: `runtime_s`, `n_llm_calls`, `input_tokens`, `output_tokens` for every row.

**Definition.** Wall-clock seconds from case start to the final formula being returned. It includes every LLM call, retry and any fitting. It excludes data generation and scoring. Enforcement is a hard kill (subprocess timeout), not a cooperative check.

| System | Declared cap | Observed |
|---|---|---|
| PySR-only | 1,400 s (1 attempt × 1,100 + 300) | about 1,110 s in the one record inspected |
| HDS v50_2 | 3,600 s (3 attempts × 1,100 + 300) | median 128 s, max 729 s, 0 of 45 above 1,400 s |
| Pure LLM (proposed) | 1,400 s | not measured |

**Why 1,400 s.** PySR-only needs about 1,100 s to run its search, so any lower common cap would cut PySR-only off and change that arm. HDS never used more than 729 s, so a 1,400 s cap does not bind on any observed HDS row. One number across all three systems means a single statement covers every pairwise comparison.

**HDS handling (D2).**

- **R0, reuse.** The HDS rows carry `timeout_s = 3600`, so the closure script's "single timeout_s" check still fails and needs `--declare-unequal-timeout`. The honest label is "HDS declared cap 3,600 s; every observed run finished within 729 s". This is an observation, not an equal-budget run. It also depends on `runtime_s` covering the whole case; in the one record inspected, `runtime_s` equals `sr_time_s` while `llm_time_s` (7.3 s) is listed separately, so whether LLM time is inside `runtime_s` should be confirmed.
- **R1, rerun.** Rerun the 45 HDS cases with `timeout_s = 1400`. At the observed median of 128 s that is about 1.6 hours; at the observed maximum for every case it would be 9.1 hours. Reruns will not reproduce the old rows exactly (LLM and search nondeterminism), so archive the old rows under a separate directory and report both.

Recommendation: R0 for closing Phase 2, R1 only if a claim needs the words "equal time budget".

**Optional arms, clearly labelled and outside the primary comparison.** A best-of-k Pure LLM arm, with k set to the mean number of LLM calls HDS makes, answers whether HDS's advantage is just more samples. Selection among samples must use training-split R² only. Selecting on `extrap_r2_far` would leak the test regime into the choice.

## 4. Design

- **Systems:** `pure_llm` (new) against `hds_v50_2` (existing rows, or rerun under R1). PySR-only already exists and stays a separate, exploratory comparison.
- **Equations (15):** Allometric Scaling, Arrhenius, Constant Product, Gravitational Force, Henderson-Hasselbalch, Ideal Gas Law, Impermanent Loss, Kinetic Energy, Liquidation Price, Logistic Growth, Michaelis-Menten, Portfolio Std Dev, Price Impact, Rate Law, Value at Risk.
- **Seeds:** 42, 99, 123. 45 cases, 45 rows expected.
- **Data:** the runner imports `generate_data` and `generate_extrap_data` from `exp1_ablation.py` and does not reimplement them (defaults seen in the source: N = 200, noise 0.05 of the target standard deviation, `test_size = 0.2`, extrapolation N = 100; **VERIFY** that the experiment does not override them). The split for `(equation, seed)` must be the one HDS used.
- **Environment:** as exported by `env_repro.sh`: `HYPATIAX_DISABLE_HARDCODED=1`, `HYPATIAX_DISABLE_PROMPT_HINTS=1`, `HYPATIAX_R2_SIGN_FLIP=0`, `HYPATIAX_STRICT=1`. Run from a clean tree on `audit/step1-cleanup` (Phase 1 tag `phase1-closed`), with `git rev-parse HEAD` and a dirty flag in every row.
- **Preconditions from the Phase 1 checklist:** generation paths logged (every row has `llm_called`, `generation_path`, `formula`); the hardcoded bypass off (`bypass_used = false`, and do not pass `--allow-bypass` to the closure script); evaluator settled (the relative-tolerance policy in `r2_canonical.py` replaces the absolute `ss_tot` guard; confirm `test_r2_policy.py` has near-constant-target cases, since only its existence is known); quarantine list exists (noise sweep B5, M3/M4 narrative, stale Supplement B appendices stay out of headline claims).

## 5. Analysis, declared before any Pure LLM result exists

- **Primary comparison:** `hds_v50_2` minus `pure_llm`.
- **Primary metric:** recovery rate, `extrap_r2_far >= 0.99`, mean over seeds per equation. The unit of analysis is the equation, because seeds within an equation are not independent.
- **Interval and test:** the paired bootstrap interval over equations and the sign test already produced by `phase2_close.py`. The sign test is descriptive: with 5 non-tied equations the smallest two-sided p is 0.0625, and 6 non-tied equations all favouring one system give 0.031. Power depends on how many equations separate the systems, so seeds do not help; more equations would.
- **Claim rule:** write a directional claim ("HDS recovers more than Pure LLM") only if the primary interval excludes 0. Otherwise write "no difference detected" or "suggestive direction".
- **Exploratory, labelled as such:** the strict threshold (0.999999), the catastrophic rate (R² below −10), and the sensitivity fields `extrap_r2_medium` and `train_r2`. No correction is applied, and none of them is promoted if it looks better than the primary.
- **Reporting rules:** report counts by `r2_status`, not mean R² (scores below −100 are recorded as −Infinity by the scorer). Per-equation tables go next to the pooled numbers.
- **Amendments:** any change after the first row is written goes in `phase2_pure_llm_amendments.md` with a date.

## 6. Per-case output

One JSON object per line, one file per seed: `p2/pure_llm_seed{seed}.jsonl`. The schema is `phase2_row_schema.json`. It keeps every field already in the HDS rows and adds:

| New field | Purpose |
|---|---|
| `r2_field`, plus `extrap_r2_near/medium/far` and `train_r2` in the row | Sensitivity checks need no `_source` lookup, and `r2 == extrap_r2_far` is checkable on the row itself |
| `r2_raw`, `r2_status` | `r2_raw` is `r2_checked` on the same arrays, before the −100 floor; `r2_status` is what `r2_scored` returned. Without them a −Infinity row cannot be classified |
| `timed_out` | Separates a timeout from an error |
| `git_commit`, `code_dirty` | Run provenance; `code_dirty` must be false |
| `prompt_sha256`, `temperature`, `model_returned` | Prompt and sampling parity; `model_returned` is the model name echoed by the API, to catch silent alias changes |
| `n_llm_calls`, `input_tokens`, `output_tokens` | Spend, reported next to the cap |

For `pure_llm` rows the schema enforces `llm_called = true`, `bypass_used = false`, `code_dirty = false` and at least one call. Python's `json` writes `-Infinity`, which is not strict JSON; the existing scripts read it and any new reader must too.

## 7. Gates

Phase 2 for this comparison closes only if all pass. Commands are in section 8: step 3 (schema) covers G8's dirty flag and G9, step 4 covers G1 to G8, step 6 covers G10. The schema and the step 4 snippet were each tested on a synthetic fixture with planted defects, not on real rows.

| Gate | Condition |
|---|---|
| G1 | `split_id` equals the HDS row's for every (equation, seed); no case without an HDS counterpart |
| G2 | `r2 == extrap_r2_far` in every row |
| G3 | `llm_called` true and `bypass_used` false in every row |
| G4 | One `timeout_s` value (equal to B) and one `prompt_sha256` across all `pure_llm` rows |
| G5 | `formula` stored for every row with `status = ok` |
| G6 | Exactly 45 rows, no duplicate (equation, seed) |
| G7 | `model_id` and `evaluator_version` identical to the HDS rows |
| G8 | `code_dirty` false and one `git_commit` across rows |
| G9 | Every row has `r2_raw` and `r2_status` |
| G10 | `phase2_close.py` runs with no FAIL other than a declared one |

## 8. Procedure

```bash
git switch audit/step1-cleanup && git status --short      # tree must be clean
source env_repro.sh
git tag phase2-pure-llm-start

# 1. Dry run: plumbing and timing only (names below are the proposed interface)
python <runner> --config phase2_pure_llm_config.yaml --equations "Kinetic Energy" --seeds 42 --dry-run
# Freeze the prompt first and record its hash. If the prompt changes after the
# dry run, discard the dry-run row and log the change in the amendments file.

# 2. Full run
python <runner> --config phase2_pure_llm_config.yaml

# 3. Schema check (pip install jsonschema)
python - <<'EOF'
import json, glob
from jsonschema import Draft202012Validator as V
v = V(json.load(open('phase2_row_schema.json')))
bad = [(f, i+1, e.message[:80]) for f in glob.glob('p2/pure_llm_*.jsonl')
       for i, l in enumerate(open(f)) for e in v.iter_errors(json.loads(l))]
print('schema errors:', len(bad)); print(bad[:10])
EOF

# 4. Gates G1-G7 on the rows
python - <<'EOF'
import json, glob, math, collections
def load(pat): return [json.loads(l) for f in sorted(glob.glob(pat)) for l in open(f) if l.strip()]
A = load('p2/pure_llm_*.jsonl'); B = load('p2/hds_*.jsonl')
key = lambda r: (r['equation'], r['seed'])
a = {key(r): r for r in A}; b = {key(r): r for r in B}
print('G6 rows', len(A), 'unique', len(a), '(expected 45)')
print('G1 split_id mismatches:', [k for k in a if k in b and a[k]['split_id'] != b[k]['split_id']])
print('G1 cases without HDS counterpart:', [k for k in a if k not in b])
for f in ['model_id', 'evaluator_version']:
    print('G7', f, 'pure_llm', {r[f] for r in A}, 'hds', {r[f] for r in B})
print('G3 bypass_used', dict(collections.Counter(r['bypass_used'] for r in A)),
      'llm_called', dict(collections.Counter(r['llm_called'] for r in A)))
print('G4 timeout_s', {r['timeout_s'] for r in A}, '| distinct prompt hashes', len({r['prompt_sha256'] for r in A}))
print('G8 git_commit values:', {r['git_commit'] for r in A})
print('G5 status ok but empty formula:', sum(1 for r in A if r['status'] == 'ok' and not r['formula']))
same = lambda x, y: x == y or (isinstance(x, float) and isinstance(y, float) and math.isnan(x) and math.isnan(y))
print('G2 r2 != extrap_r2_far:', sum(1 for r in A if r['r2'] is not None and not same(r['r2'], r['extrap_r2_far'])))
EOF

# 5. Verify the primary field on ALL rows (pure_llm, hds, pysr_only), then sensitivity sets
python scripts/reflatten_fields.py --check-only
python scripts/reflatten_fields.py --sens p2_med=extrap_r2_medium --sens p2_train=train_r2 --force

# 6. Primary closure (A side is the Pure LLM; add --declare-unequal-timeout only under R0)
python scripts/phase2_close.py --pure-llm p2/pure_llm_*.jsonl --hds p2/hds_*.jsonl \
  --a-name pure_llm --out-dir phase2_out_purellm \
  --declare-unequal-timeout "HDS declared cap 3600 s, observed max 729 s; Pure LLM cap 1400 s"

# 7. Sensitivity closures, same command with p2_med/ and p2_train/ and separate --out-dir
```

The `--declare-unequal-timeout` text in step 6 applies to R0. Under R1 all rows carry `timeout_s = 1400` and the flag is dropped. If the `p2/` directory now also holds the old `pysr_*.jsonl` rows, step 5 still works, since it verifies and re-flattens every row it finds.

## 9. Cost

The matrix is 15 equations × 3 seeds = 45 cases. API cost and runtime per case are unknown until the dry run records `n_llm_calls`, token counts and `runtime_s`. Multiply those by 45 for the full run. Under R1 add the HDS rerun estimate from section 3.

## 10. Limits that stay whatever the result

- 15 equations, and seeds are replicates of the same equations, not new ones.
- Most of these are textbook formulas. A Pure LLM may recall them from a name or description, so a high recovery rate may measure recall. If the prompt must include the equation name for parity (D3), say so next to the result.
- With one LLM sample per case and no sampling seed, repeating the run will not give the same rows. Any rerun is a new run, not a reproduction.
- The existing HDS rows were produced by the `exp1_ablation` experiment and flattened into `p2/`; they were not launched as a dedicated Phase 2 run.


## 11. Values read from the code (added 27 October 2026)

- **LLM settings of the HDS stage:** `temperature = 0.3`, `max_tokens = 2000` (the `LLMConfig` default, not overridden), `n_candidates = 3`, model `claude-sonnet-4-6` (single value in all 90 rows). HDS makes up to `HYPATIA_MAX_RETRIES = 3` PySR attempts per case.
- **Prompt inputs (D3):** with `HYPATIAX_DISABLE_PROMPT_HINTS=1` the HDS prompt carries the domain, the variable names, data-pattern statistics and a physical-constants block. The equation name and description are withheld, and the worked example is a placeholder. A matched Pure LLM arm must receive the same inputs. Whether `PureLLMBaseline` builds its prompt the same way has **not** been checked.
- **Sample count (D5):** HDS asks for 3 candidate equations per LLM call and then refines them with PySR. A Pure LLM arm that returns one formula is not given the same number of attempts. Decide whether it also returns 3 candidates and how one is chosen (training R^2 only, never the extrapolation score), or label the difference.
- **Still undecided:** `max_calls_per_case`, the prompt hash, and the Pure LLM runner itself.
- **`split_id` caveat:** in the committed `p2/` rows `split_id` is `derived:` plus the first 12 characters of `sha256("equation|seed")`. It is identical for the two systems by construction, so the closure script's "identical split_id" check does not prove the splits match. They do match in the code: `exp1_ablation.generate_data` draws from `RandomState(seed)` and splits with `random_state=seed`, and every condition calls it with the same `(equation, seed)`. Gate G1 for the Pure LLM arm should therefore compare the data arrays or their hashes, not this label.
