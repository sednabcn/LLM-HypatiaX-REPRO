"""Static regression guards for the Exp2 PCA typed-contract subprocess boundary.

These checks intentionally do not import the benchmark runner or launch a worker.
"""

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = (
    REPO_ROOT
    / "hypatiax"
    / "experiments"
    / "benchmarks"
    / "run_comparative_suite_benchmark_pca.py"
)


def _runner_and_worker():
    source = RUNNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(RUNNER_PATH))
    worker_node = next(
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "_SUBPROCESS_WORKER"
            for target in node.targets
        )
    )
    return source, ast.literal_eval(worker_node)


def test_pca_adapter_builds_a_declaration_only_typed_problem_spec():
    source, _ = _runner_and_worker()

    assert '_meta.get("discovery_problem_spec")' in source
    assert "def _remap_declared_contract_mapping" in source
    assert "contains undeclared variable" in source
    assert '"variable_names": list(safe_names)' in source
    assert '"contract_origin": "exp2_protocol_adapter"' in source
    assert '"physical_declarations_inferred": False' in source
    assert '"training_only_search_validation": {' in source
    assert '_meta["discovery_problem_spec"] = _contract_spec' in source


def test_pca_worker_deserializes_and_audits_the_typed_contract():
    _, worker = _runner_and_worker()

    assert "from hypatiax.tools.symbolic.discovery_contracts import discovery_problem_from_dict" in worker
    assert "_typed_problem = discovery_problem_from_dict(_problem_spec)" in worker
    assert "tuple(_typed_problem.variable_names) != tuple(var_names)" in worker
    assert '_meta["discovery_problem"] = _typed_problem' in worker
    assert "metadata=_meta" in worker
    assert '"discovery_problem_contract": _contract_audit' in worker
    assert '_benchmark_provenance.update({' in worker


def test_pca_selector_is_forwarded_without_changing_the_v50_2_default():
    source, worker = _runner_and_worker()

    assert 'choices=["v50_2", "v60"]' in source
    assert 'def _resolve_hybrid_implementation(cli_value=None)' in source
    assert 'or os.environ.get("HYPATIAX_HYBRID_IMPLEMENTATION")' in source
    assert 'engine.get("implementation", "v50_2")' in source
    assert '_tc_kwargs["hybrid_implementation"] = getattr(' in source
    assert 'kwargs.get("hybrid_implementation", "v50_2")' in worker
