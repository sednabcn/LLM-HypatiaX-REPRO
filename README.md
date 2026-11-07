# LLM-HypatiaX-REPRO

Reproducibility repository for **HypatiaX**, a research project on LLM-guided symbolic regression and hybrid learning systems. The codebase contains experiment implementations, execution protocols, result-validation utilities, reproducibility configuration, and GitHub Actions workflows.

## Repository layout

```text
.
├── .github/
│   ├── scripts/          # CI and artifact-processing helpers
│   └── workflows/        # Experiment, validation, and maintenance workflows
├── config/
│   └── repro.yaml        # Reproducibility and experiment configuration
├── docs/                 # Reports, closure records, and diagrams
├── hypatiax/
│   ├── core/             # Models, generation systems, metrics, and training
│   ├── experiments/      # Benchmark implementations and experiment tests
│   ├── protocols/        # Experiment protocols
│   └── tools/            # Symbolic, validation, and utility components
├── scripts/              # Figure/table generation and audit utilities
├── run_all.sh            # Local experiment pipeline entry point
├── env_repro.sh          # Local reproducibility environment setup
├── setup_environment.sh  # Environment setup helper
├── requirements.txt      # Pinned Python dependencies
├── pyproject.toml        # Python package metadata
└── LICENSE
```

The repository also includes root-level audit and reproducibility utilities, experiment-specific configuration files, and archived historical scripts. Those archives are retained as project history and are not the primary execution entry points.

## Main entry points

| Path | Purpose |
|---|---|
| `run_all.sh` | Runs the local experiment pipeline; supports selecting a step and dry-run mode |
| `env_repro.sh` | Sets local environment variables and checks that the repository's `hypatiax` package is imported |
| `config/repro.yaml` | Central reproducibility configuration |
| `hypatiax/experiments/benchmarks/` | Benchmark and experiment implementations |
| `hypatiax/protocols/` | Experiment protocol definitions |
| `scripts/` | Figure/table generation and audit-related utilities |
| `.github/workflows/ci_runner_repro.yml` | GitHub Actions runner for reproducibility experiments |
| `.github/workflows/ci_pipeline_check.yml` | Completion, result, and qualification checks |

## GitHub Actions workflows

The maintained workflow set includes:

| Workflow | Role |
|---|---|
| `ci_runner_repro.yml` | Dispatches and executes reproducibility experiments, including supported shard and multi-experiment runs |
| `ci_pipeline_check.yml` | Checks committed outputs, computes completion status, qualifies results, and reports pipeline status |
| `ci_pipeline_validate.yml` | Runs the repository's pipeline validation path |
| `ci_phase3_ablation.yml` | Phase 3 ablation workflow |
| `ci_r2_policy.yml` | Enforces the configured R² scoring policy |
| `ci_bypass_audit.yml` | Audits safeguards against bypassed model outputs or prompts |
| `ci_smoke_test_exp3.yml` | Smoke-checks the exp3 workflow path |
| `claude.yml` | Repository assistant workflow |
| `clean-old-workflows.yml` | Removes old workflow runs according to its configured retention policy |
| `cleanup-cache-actions.yml` | Performs configured Actions cache cleanup |

Legacy orchestration definitions are not documented as supported run entry points. Use `ci_runner_repro.yml` for experiment dispatch and `ci_pipeline_check.yml` for completion and qualification checks.

## Local setup

The package metadata declares Python 3.8 or newer. The pinned dependency set is in `requirements.txt`; the experiment environment also relies on external tooling such as Julia/PySR and, for live LLM runs, the relevant provider API credentials.

Create and activate a virtual environment, then install the repository dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

The dependency file includes a PyTorch CPU package index and a broad, pinned scientific/ML stack. Installation may therefore be substantial and can depend on platform support for individual packages. Review `setup_environment.sh` and the experiment-specific requirements before preparing a production reproduction environment.

From the repository root, initialize the local reproducibility environment with:

```bash
source env_repro.sh
```

This exports the repository on `PYTHONPATH`, sets the strict reproducibility safeguards, and checks that Python resolves `hypatiax` from the current checkout. It does not install dependencies or provision Julia.

## Running experiments

`run_all.sh` is the local orchestration entry point. It accepts either `--step` or a step name, and supports `--from` and `--dry-run`.

Examples:

```bash
# Print the pipeline commands without executing them
./run_all.sh --dry-run

# Print the commands for one experiment step
./run_all.sh --step exp1 --dry-run

# Run one experiment step
./run_all.sh --step exp1
```

The valid step names are defined in `_STEP_ORDER` near the beginning of `run_all.sh`. A selected step may still require prerequisites, data, API credentials, Julia/PySR, and experiment-specific configuration. A dry run displays the planned commands; it does not establish that a full experiment can complete successfully.

For local live-LLM runs, provide the API key expected by the selected experiment. By default, `run_all.sh` enforces the clean-run safeguards `HYPATIAX_DISABLE_HARDCODED=1` and `HYPATIAX_DISABLE_PROMPT_HINTS=1`, enables strict exception handling, and disables the legacy R² sign-flip policy. The script documents a separate, explicitly opted-in legacy mode; do not use that mode for headline reproducibility runs.

## GitHub Actions experiment dispatch

Open the repository's **Actions** tab and select **HypatiaX - runner (repro)** (`.github/workflows/ci_runner_repro.yml`). Choose an experiment and review the inputs before dispatching.

The runner supports single-experiment dispatch and an optional `experiments` input for fan-out into separate runs. The fan-out path uses the repository secret `DISPATCH_PAT`; configure it only if that feature is needed. The accepted experiment IDs and input behavior are defined in the workflow itself and should be treated as authoritative.

Use **HypatiaX - checkpoint** (`.github/workflows/ci_pipeline_check.yml`) to check committed outputs, inspect incomplete task sets, and run the qualification gate. A successful dispatch means that a workflow was queued; it does not by itself mean that the experiment completed or passed qualification.

## Results and documentation

Experiment outputs are organized under:

```text
hypatiax/data/results/
```

The exact result subdirectory depends on the experiment. Consult the runner workflow's experiment metadata and the corresponding experiment implementation before interpreting or moving result files.

Project documentation and reports are under `docs/`. The repository includes phase-closure documentation and report source/output files. Workflow-specific behavior, inputs, permissions, and dispatch conditions are defined in the corresponding YAML files under `.github/workflows/`.

## License

This reproducibility repository is licensed under the **Apache License 2.0**.

```text
Copyright 2026 PhD Ruperto P. Bonet Chaple

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

Original **HypatiaX** work © PhD Ruperto P. Bonet Chaple. See [`LICENSE`](./LICENSE) for the full license text.
