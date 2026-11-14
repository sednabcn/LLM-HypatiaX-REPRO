"""Offline static checks for canonical rerun settings and safety ordering."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT.parent / "config" / "repro.yaml"
RUN_ALL = ROOT.parent / "run_all.sh"
ABLATION = ROOT / "experiments" / "benchmarks" / "exp1_ablation.py"
PORTFOLIO = ROOT / "experiments" / "benchmarks" / "portfolio_variance_v3c2.py"


def test_canonical_llm_and_pysr_values_are_aligned():
    cfg, run, ablation = (p.read_text(encoding="utf-8") for p in (CONFIG, RUN_ALL, ABLATION))
    assert re.search(r'^llm_model:\\s*"claude-sonnet-4-6"\\s*$', cfg, re.M)
    assert re.search(r'^llm_temperature:\\s*0\\.25\\s*$', cfg, re.M)
    assert 'LLM_TEMPERATURE="${LLM_TEMPERATURE:-0.25}"' in run
    assert 'LLM_MODEL="${LLM_MODEL:-claude-sonnet-4-6}"' in run
    assert 'os.environ.get("LLM_TEMPERATURE", "0.25")' in ablation
    assert re.search(r'population_size\\s*=\\s*33\\s*,', ablation)
    assert re.search(r'^\\s*population_size:\\s*33\\s*$', cfg, re.M)


def test_portfolio_seed_zero_and_early_guard():
    src = PORTFOLIO.read_text(encoding="utf-8")
    assert "BENCHMARK_SEED = 42 if _resolved_seed is None else _resolved_seed" in src
    assert src.index("from hypatiax.core.enforce_flags import enforce") < src.index("sys.exit(0)")
