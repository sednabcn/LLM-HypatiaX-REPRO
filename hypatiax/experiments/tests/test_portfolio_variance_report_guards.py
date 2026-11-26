"""Static regression tests for optional and data-derived portfolio reporting."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "hypatiax/experiments/benchmarks/portfolio_variance_v3c2.py"


def test_portfolio_report_source_parses():
    ast.parse(SOURCE.read_text(encoding="utf-8"))


def test_portfolio_report_does_not_require_optional_pysr_rows():
    source = SOURCE.read_text(encoding="utf-8")
    section = source.split("# ── 6c: Section 6 paragraph", 1)[1].split(
        "# Seed-level audit values", 1
    )[0]
    assert "Np=paper_nums.get('pysr_N')" in section
    assert "if has_pysr else 'PySR-only comparison was unavailable" in section
    assert "paper_nums['pysr_N']" not in section
    assert "paper_nums['pysr_worst_far_r2']" not in section


def test_portfolio_footnote_uses_seed_audit_values_defined_before_it():
    source = SOURCE.read_text(encoding="utf-8")
    definition = source.index("_successful_observed = [")
    footnote = source.index("# ── 6d: DeFi table footnote")
    assert definition < footnote
    section = source.split("# ── 6d: DeFi table footnote", 1)[1].split(
        "# ── 6e: Corrected JSON", 1
    )[0]
    assert "observed_successes = sorted(_successful_observed)" in section


def test_portfolio_latex_caption_interpolates_configured_seed():
    source = SOURCE.read_text(encoding="utf-8")
    assert "fr'\\\\caption{{Portfolio Variance far-$R^2$" in source
    assert "Configured benchmark seed = {BENCHMARK_SEED}" in source


def test_portfolio_seed_table_is_skipped_without_both_arm_summaries():
    source = SOURCE.read_text(encoding="utf-8")
    guard = source.split("# ── 6b: LaTeX appendix seed-sweep table", 1)[1].split(
        "# ── 6c: Section 6 paragraph", 1
    )[0]
    assert "'pysr_N' in paper_nums" in guard
    assert "'hypatia_N' in paper_nums" in guard
    assert "df_hypatia is not None" in guard
