#!/usr/bin/env python3
"""
test_trajectory_monitor.py

Standalone test for the three trajectory-monitor functions added in
exp3_nguyen12_hybrid50v_02_patched.py (_read_pysr_hof_snapshot,
_poll_hof_dir_proc, _fit_with_pysr_trajectory), without needing PySR,
Julia, or an Anthropic API key installed.

HOW IT AVOIDS NEEDING THE REAL SCRIPT'S DEPENDENCIES: the three functions
are extracted directly from the target script's source via `ast`, and
exec'd in an isolated namespace -- this runs exactly the code that's
actually in the file, but skips the module-level side effects (API key
checks, argparse, PySRRegressor imports) that would otherwise fire just
from importing it normally.

WHAT'S FAKED: a MockPySRRegressor that, instead of running a real
evolutionary search, writes a sequence of hall_of_fame.csv snapshots to
disk over a few hundred milliseconds -- the same file format and the same
"appears on disk incrementally, out from under the calling process"
behavior real PySR exhibits, which is the specific thing the poller
process has to handle correctly.

Run:
    python3 test_trajectory_monitor.py [path/to/exp3_nguyen12_hybrid50v_02_patched.py]

Exit code 0 = all tests passed.
"""
import ast
import csv
import shutil
import sys
import tempfile
import time
import traceback
from pathlib import Path

DEFAULT_SCRIPT = Path(__file__).parent / "exp3_nguyen12_hybrid50v_02_patched.py"

REQUIRED_FUNCS = (
    "_read_pysr_hof_snapshot",
    "_poll_hof_dir_proc",
    "_fit_with_pysr_trajectory",
)


def load_functions(script_path, names):
    """Extract just the named top-level function defs from `script_path`
    via AST and exec them in a fresh namespace -- runs the real code
    without triggering the rest of the script's module-level side effects
    (API key checks, argparse, PySRRegressor/sklearn imports, etc.)."""
    src = Path(script_path).read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(script_path))

    ns = {}
    exec(
        "import csv, pathlib, time, os, multiprocessing as mp\n"
        "import numpy as np\n",
        ns,
    )

    found = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            mod = ast.Module(body=[node], type_ignores=[])
            ast.fix_missing_locations(mod)
            code = compile(mod, filename=str(script_path), mode="exec")
            exec(code, ns)
            found.add(node.name)

    missing = set(names) - found
    if missing:
        raise RuntimeError(
            f"Could not find function(s) {sorted(missing)} as top-level "
            f"defs in {script_path}. Extraction only handles top-level "
            f"`def name(...):` blocks, not nested/decorated ones."
        )
    return ns


class MockPySRRegressor:
    """Stands in for a real PySRRegressor. `.fit()` writes a sequence of
    hall_of_fame.csv snapshots to disk over `write_delays`, simulating an
    evolutionary search that improves its best equation a few times before
    converging -- exactly the incremental-disk-write behavior the poller
    has to observe correctly. `.predict()` evaluates whatever the LAST
    written row's equation was, using Python `**` syntax internally even
    though the CSV (like real PySR) stores `^`.
    """

    def __init__(self, **kwargs):
        self.params = dict(kwargs)
        self._final_expr_py = None

    def set_params(self, **kwargs):
        self.params.update(kwargs)
        return self

    def fit(self, X, y, variable_names=None):
        import numpy as np

        output_directory = Path(self.params["output_directory"])
        run_id = self.params["run_id"]
        run_dir = output_directory / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        csv_path = run_dir / "hall_of_fame.csv"

        # A short "search" that improves its best-loss guess three times,
        # with real wall-clock gaps -- long enough for a fast poller
        # (poll_seconds well under these gaps) to observe each state.
        stages = [
            # (Complexity, Loss, Equation) -- '^' for power, PySR-style
            (3.0, 1.5e-1, "x1 + x1"),
            (5.0, 2.0e-3, "x1 * 2.0 + 0.001"),
            (7.0, 1.0e-9, "(x1 ^ 2.0) - (x1 ^ 2.0) + (x1 * 2.0)"),  # == 2*x1
        ]
        for complexity, loss, equation in stages:
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["Complexity", "Loss", "Equation"])
                w.writeheader()
                w.writerow({"Complexity": complexity, "Loss": loss, "Equation": equation})
            time.sleep(0.12)

        self._final_expr_py = stages[-1][2].replace("^", "**")
        self._X = np.asarray(X)
        self._var_names = variable_names

    def predict(self, X):
        import numpy as np
        ns = {vn: np.asarray(X)[:, i] for i, vn in enumerate(self._var_names)}
        return eval(self._final_expr_py, {"__builtins__": {}}, ns)


# ---------------------------------------------------------------------------
# Individual tests
# ---------------------------------------------------------------------------

def test_read_snapshot_missing_file(ns, tmp_path):
    result = ns["_read_pysr_hof_snapshot"](tmp_path / "does_not_exist.csv")
    assert result is None, "expected None for a missing file"


def test_read_snapshot_empty_file(ns, tmp_path):
    p = tmp_path / "empty.csv"
    p.write_text("Complexity,Loss,Equation\n")  # header only, no data rows
    result = ns["_read_pysr_hof_snapshot"](p)
    assert result is None, "expected None for a header-only (no data rows) file"


def test_read_snapshot_picks_lowest_loss(ns, tmp_path):
    p = tmp_path / "hof.csv"
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Complexity", "Loss", "Equation"])
        w.writeheader()
        w.writerow({"Complexity": 3, "Loss": 0.5, "Equation": "x1"})
        w.writerow({"Complexity": 7, "Loss": 0.001, "Equation": "x1 * 2.0"})  # best
        w.writerow({"Complexity": 11, "Loss": 0.01, "Equation": "x1 * 2.0 + 0.0"})
    snap = ns["_read_pysr_hof_snapshot"](p, label="TEST", iteration=1, elapsed_seconds=1.23)
    assert snap is not None
    assert snap["best_loss"] == 0.001, snap
    assert snap["best_expression"] == "x1 * 2.0", snap
    assert snap["hall_of_fame_rows"] == 3, snap
    assert snap["label"] == "TEST" and snap["iteration"] == 1
    assert snap["source_size_bytes"] > 0 and snap["source_mtime_ns"] > 0


def test_poller_captures_multiple_updates(ns, tmp_path):
    """Write 3 CSV states with real delays (mimicking PySR) in a background
    thread, run the poller against the same path, and check it captured
    more than one distinct snapshot -- not just the final state."""
    import multiprocessing as mp
    import threading

    csv_path = tmp_path / "hof.csv"

    def writer():
        stages = [(3, 0.5, "x1"), (5, 0.01, "x1*2"), (7, 1e-9, "x1*2.0+0.0")]
        for complexity, loss, equation in stages:
            with open(csv_path, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["Complexity", "Loss", "Equation"])
                w.writeheader()
                w.writerow({"Complexity": complexity, "Loss": loss, "Equation": equation})
            time.sleep(0.1)

    manager = mp.Manager()
    queue = manager.Queue()
    stop_event = manager.Event()
    t_start = time.time()

    poller = mp.Process(
        target=ns["_poll_hof_dir_proc"],
        args=(str(csv_path), 0.03, "TEST", queue, stop_event, t_start),
        daemon=True,
    )
    poller.start()

    t = threading.Thread(target=writer)
    t.start()
    t.join()
    time.sleep(0.05)  # let the poller's last _try_poll see the final write
    stop_event.set()
    poller.join(timeout=5)

    snaps = []
    while not queue.empty():
        snaps.append(queue.get())

    assert len(snaps) >= 2, f"expected >=2 distinct snapshots, got {len(snaps)}: {snaps}"
    losses = [s["best_loss"] for s in snaps]
    assert losses == sorted(losses, reverse=True) or losses[-1] == min(losses), (
        f"expected losses to trend downward as the mock search 'improves', got {losses}"
    )
    assert snaps[-1]["best_expression"] == "x1*2.0+0.0"


def test_fit_with_trajectory_single_source_of_truth(ns, tmp_path):
    """The core regression test: run _fit_with_pysr_trajectory against the
    MockPySRRegressor and assert the returned (r2, best_expr) is derived
    from the SAME snapshot as trajectory[-1] -- this is the exact
    property whose absence caused the original N-4/N-7 corruption bug."""
    import numpy as np

    X = np.linspace(1.0, 3.0, 50).reshape(-1, 1)  # matches N1-style extrap domain
    y = 2.0 * X[:, 0]  # ground truth: y = 2*x1, matches the mock's final stage

    model = MockPySRRegressor()
    r2, best_expr, trajectory = ns["_fit_with_pysr_trajectory"](
        model, X, y, ["x1"], label="H",
        poll_seconds=0.02, output_dir=tmp_path / "_pysr_trajectory_runs",
    )

    assert trajectory, "expected a non-empty trajectory"
    assert len(trajectory) >= 2, f"expected multiple captured stages, got {len(trajectory)}"

    # The property that matters: best_expr returned to the caller MUST be
    # exactly the last trajectory entry's best_expression (post ^ -> **
    # normalization), not some independently-derived value.
    last_snap_expr = trajectory[-1]["best_expression"].replace("^", "**")
    assert best_expr == last_snap_expr, (
        f"SINGLE-SOURCE-OF-TRUTH VIOLATION: returned best_expr={best_expr!r} "
        f"does not match trajectory[-1].best_expression={last_snap_expr!r}. "
        f"This is exactly the corruption pattern found in the original "
        f"audit (N-4/N-7, seed 42) -- expression and trajectory must never "
        f"be able to disagree."
    )

    # And the reported R^2 should reflect the true, converged fit (mock's
    # final stage is exactly y = 2*x1, so R^2 should be ~1.0).
    assert r2 > 0.999, f"expected near-perfect R^2 for the converged mock fit, got {r2}"


def test_fit_with_trajectory_fallback_on_no_csv(ns, tmp_path):
    """If the CSV never gets written at all (e.g. PySR crashed before its
    first flush), _fit_with_pysr_trajectory must fall back to
    model.sympy()/model.predict() with a loud warning, not silently
    return garbage or crash."""
    import warnings
    import numpy as np

    class SilentMockPySRRegressor(MockPySRRegressor):
        def fit(self, X, y, variable_names=None):
            # Deliberately never writes hall_of_fame.csv
            self._final_expr_py = "x1 * 3.0"
            self._X = np.asarray(X)
            self._var_names = variable_names

        def sympy(self):
            import sympy as sp
            return sp.sympify("3.0*x1")

    X = np.linspace(1.0, 3.0, 20).reshape(-1, 1)
    y = 3.0 * X[:, 0]
    model = SilentMockPySRRegressor()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r2, best_expr, trajectory = ns["_fit_with_pysr_trajectory"](
            model, X, y, ["x1"], label="H",
            poll_seconds=0.02, output_dir=tmp_path / "_pysr_trajectory_runs_2",
        )
    assert trajectory == [], "expected an empty trajectory when no CSV was ever written"
    assert any("no hall_of_fame.csv snapshot readable" in str(w.message) for w in caught), (
        "expected a loud RuntimeWarning when falling back -- silent fallback "
        "is exactly the failure mode this design is supposed to avoid"
    )
    assert r2 > 0.999


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

TESTS = [
    test_read_snapshot_missing_file,
    test_read_snapshot_empty_file,
    test_read_snapshot_picks_lowest_loss,
    test_poller_captures_multiple_updates,
    test_fit_with_trajectory_single_source_of_truth,
    test_fit_with_trajectory_fallback_on_no_csv,
]


def main():
    script_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SCRIPT
    if not script_path.exists():
        print(f"ERROR: script not found: {script_path}")
        sys.exit(2)

    print(f"Extracting {REQUIRED_FUNCS} from {script_path} ...")
    ns = load_functions(script_path, REQUIRED_FUNCS)
    print("  OK — all three functions extracted without executing the "
          "rest of the script.\n")

    n_pass, n_fail = 0, 0
    for test_fn in TESTS:
        tmp_dir = Path(tempfile.mkdtemp(prefix="traj_test_"))
        name = test_fn.__name__
        try:
            test_fn(ns, tmp_dir)
            print(f"  PASS  {name}")
            n_pass += 1
        except AssertionError as e:
            print(f"  FAIL  {name}\n        {e}")
            n_fail += 1
        except Exception:
            print(f"  ERROR {name}")
            traceback.print_exc()
            n_fail += 1
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\n{n_pass} passed, {n_fail} failed")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
