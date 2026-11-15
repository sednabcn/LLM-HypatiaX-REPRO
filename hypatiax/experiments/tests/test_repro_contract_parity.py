"""Offline static checks for canonical rerun settings and safety ordering."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "config" / "repro.yaml"
RUN_ALL = ROOT / "run_all.sh"
ABLATION = ROOT / "hypatiax" / "experiments" / "benchmarks" / "exp1_ablation.py"
PORTFOLIO = ROOT / "hypatiax" / "experiments" / "benchmarks" / "portfolio_variance_v3c2.py"


def test_canonical_llm_and_pysr_values_are_aligned():
    cfg = CONFIG.read_text(encoding="utf-8")
    run = RUN_ALL.read_text(encoding="utf-8")
    ablation = ABLATION.read_text(encoding="utf-8")
    assert 'llm_model:     "claude-sonnet-4-6"' in cfg
    assert "llm_temperature: 0.25" in cfg
    assert 'LLM_TEMPERATURE="${LLM_TEMPERATURE:-0.25}"' in run
    assert 'LLM_MODEL="${LLM_MODEL:-claude-sonnet-4-6}"' in run
    assert 'os.environ.get("LLM_TEMPERATURE", "0.25")' in ablation
    assert "population_size= 33," in ablation
    assert "population_size: 33" in cfg


def test_portfolio_seed_zero_and_early_guard():
    src = PORTFOLIO.read_text(encoding="utf-8")
    assert "BENCHMARK_SEED = 42 if _resolved_seed is None else _resolved_seed" in src
    assert src.index("from hypatiax.core.enforce_flags import enforce") < src.index("sys.exit(0)")
