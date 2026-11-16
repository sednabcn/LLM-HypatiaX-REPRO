# Lightweight formula-prompt CLI test

The CLI checks the production strict zero-shot formula prompt without running the full experiment suite.

## Requirements

Use the repository's Python environment with pinned dependencies installed. Live mode also requires `ANTHROPIC_API_KEY`.

## Commands

Offline contract check (zero API calls):

```bash
python scripts/test_formula_prompt.py --mode offline
```

Live prompt check (exactly one LLM request by default):

```bash
export ANTHROPIC_API_KEY="..."
python scripts/test_formula_prompt.py --mode live --case-id 3
```

Run both checks in sequence (offline first, then one live request):

```bash
python scripts/test_formula_prompt.py --mode both --case-id 3
```

The default case ID `3` is Allometric Scaling. Other Core-15 cases can be selected with `--case-id 0` through `--case-id 14`. An explicit model can be selected with `--model MODEL_ID`.

## What it checks

- Offline: calls the real production prompt builder without constructing an API client; verifies exact ordered input signature instructions, numeric literal coefficient requirements, no coefficient fitting, and no embedded ground-truth formula; checks that the signature validator rejects undeclared parameters.
- Live: calls the production zero-shot `generate_formula` path once, with training arrays deliberately omitted from the prompt call; checks the returned function signature and temperature 0.25; evaluates the formula on deterministic training, outer-test, and extrapolation partitions.
- The live JSON report records formula/prompt/response hashes, token usage, metrics, and metric failures. A metric failure produces exit code 1 and is retained in the report.

## Boundaries

This is a prompt diagnostic, not a benchmark rerun. It does not invoke PySR, fit coefficients, retry the API call, send test or extrapolation data to the model, or change the existing benchmark arms. Live mode makes one request for one equation. It sets strict/no-hardcoded/no-prompt-hints/no-cache environment flags for the process.

Output defaults to `prompt_test_result.json` in the current directory and can be changed with `--output PATH`.