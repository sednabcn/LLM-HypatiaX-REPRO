"""Regression coverage for imports required by the isolated symbolic worker."""

import ast
from pathlib import Path


def test_isolated_worker_imports_hashlib_for_typed_v60_contract_digest():
    repository_root = Path(__file__).resolve().parents[1]
    runner_path = (
        repository_root
        / "hypatiax"
        / "experiments"
        / "benchmarks"
        / "run_comparative_suite_benchmark_v2.py"
    )
    module = ast.parse(runner_path.read_text(encoding="utf-8"))

    worker_assignment = next(
        node
        for node in module.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "_SUBPROCESS_WORKER"
            for target in node.targets
        )
    )
    worker_source = ast.literal_eval(worker_assignment.value)
    worker_module = ast.parse(worker_source)

    imported_names = {
        alias.name
        for node in worker_module.body
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert "hashlib" in imported_names
    assert "hashlib.sha256" in worker_source
