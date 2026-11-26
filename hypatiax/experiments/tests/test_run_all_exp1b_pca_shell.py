"""Regression tests for the exp1b_pca run_all.sh shell wrapper."""

from pathlib import Path
import re
import subprocess


def test_exp1b_pca_bash_c_payload_is_valid_shell():
    """Catch quoting regressions hidden inside run_all.sh's nested bash -c string."""
    repo_root = Path(__file__).resolve().parents[3]
    run_all = (repo_root / "run_all.sh").read_text(encoding="utf-8")

    start = re.search(r'^run exp1b_pca .* bash -c "\n', run_all, flags=re.MULTILINE)
    assert start is not None, "exp1b_pca run_all.sh step was not found"

    remainder = run_all[start.end() :]
    end = re.search(r'^"\s*$', remainder, flags=re.MULTILINE)
    assert end is not None, "exp1b_pca bash -c payload has no closing delimiter"

    raw_payload = remainder[: end.start()]
    # Decode the escapes applied by the outer bash double-quoted argument.
    payload = re.sub(r'\\(["$\\])', r'\1', raw_payload)
    checked = subprocess.run(
        ["bash", "-n", "-c", payload],
        check=False,
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0, checked.stderr
