"""CLEAR_CHECKPOINT must apply to exp1_ablation (it used to cover exp2_feynman only)."""
import pathlib

SRC = (pathlib.Path(__file__).resolve().parents[3] / "run_all.sh").read_text()


def test_exp1_ablation_honours_clear_checkpoint():
    step = SRC[SRC.index("_exp1_ablation_step()"):]
    step = step[: step.index("PYPROV")]
    assert 'CLEAR_CHECKPOINT' in step and 'exp1_ablation_checkpoint*.json' in step
    assert 'mv "${_f}"' in step          # moved to a backup dir, not deleted
