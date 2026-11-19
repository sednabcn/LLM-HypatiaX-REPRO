from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "hypatiax" / "experiments" / "benchmarks" / "run_comparative_suite_benchmark_v2.py"
VALIDATOR = ROOT / "scripts" / "ci" / "validate_exp2_extrap_smoke.py"


def test_v50_2_worker_emits_explicit_non_native_implementation_provenance():
    source = BENCHMARK.read_text(encoding="utf-8")
    assert '_selected_implementation == "v50_2"' in source
    assert '"engine_family": "hybrid_discovery"' in source
    assert '"implementation_mode": "v50_2"' in source
    assert '"native_v60_pipeline": False' in source
    assert '"provenance_source": "hybrid_factory_selection"' in source


def test_v50_2_validator_requires_the_explicit_implementation_record():
    source = VALIDATOR.read_text(encoding="utf-8")
    assert 'implementation.get("engine_family") != "hybrid_discovery"' in source
    assert 'implementation.get("native_v60_pipeline") is True' in source



def test_hybrid_method_label_tracks_selected_implementation():
    source = BENCHMARK.read_text(encoding="utf-8")
    assert 'super().__init__(f"HybridDiscoverySystem {implementation} (tools)", verbose)' in source
    assert 'implementation=self._hybrid_implementation' in source
    assert 'hybrid_implementation=args.hybrid_implementation' in source
    assert '"HybridDiscoverySystem v60 (tools)"' in source
