"""Source-level regression tests (no torch / API key) for ledger L54 and L18/L28."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NN_DEFI = ROOT / "hypatiax/core/generation/hybrid_defi_system/hybrid_system_nn_defi_domain.py"
RUN_ALL = ROOT / "run_all.sh"


def test_l54_no_predictions_is_none_not_zero():
    src = NN_DEFI.read_text(encoding="utf-8")
    block = src.split('final_r2_status = "no_predictions"')[1][:200]
    assert re.search(r"rmse\s*=\s*None", block) and re.search(r"mse\s*=\s*None", block)
    pre = src.split('final_r2_status = "no_predictions"')[0][-300:]
    assert re.search(r"final_r2\s*=\s*None", pre), "no-predictions branch must not score 0.0"
    assert "final_r2 = 0.0" not in src
    assert "if np.isfinite(mse) else 0.0" not in src, "non-finite MSE must not become RMSE 0.0"


def test_l54_evaluation_dict_is_none_safe():
    src = NN_DEFI.read_text(encoding="utf-8")
    assert "float(final_r2) if final_r2 is not None else None" in src


def test_l18_instability_deferred_in_full_runs():
    s = RUN_ALL.read_text(encoding="utf-8")
    deferred = re.search(r'_DEFERRED_STEPS="([^"]*)"', s)
    assert deferred and {"instability", "exp2_all_domains_pca_4060"}.issubset(set(deferred.group(1).split()))
    assert 'RUN_DEFERRED' in s
    # still a valid step name so an explicit --step instability keeps working
    assert re.search(r'_STEP_ORDER="[^"]*\binstability\b', s)
