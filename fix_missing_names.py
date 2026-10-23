#!/usr/bin/env python3
"""
fix_missing_names.py -- adds the two names the scanner reported as undefined.
Run from the repo root:   python3 fix_missing_names.py            (apply)
                          python3 fix_missing_names.py --check    (report only)
Idempotent; writes <file>.bak before editing; verifies with pyflakes afterwards.
"""
import re, shutil, subprocess, sys
from pathlib import Path

BM = Path("hypatiax/experiments/benchmarks")
PCA = BM / "run_comparative_suite_benchmark_pca.py"
V2 = BM / "run_comparative_suite_benchmark_v2.py"

KILL = '''

def _kill_thread(thread_id) -> bool:
    """Best-effort hard stop of a Python thread by injecting SystemExit.

    Returns True if the exception was scheduled, False if the thread already
    exited or the id is invalid (a harmless race). LIMITS: the exception is only
    delivered when the thread next executes Python bytecode, so it cannot
    interrupt a blocking C/Julia call (e.g. PySR inside juliacall) -- an
    orphaned Julia subprocess must still be terminated via its Popen handle.
    """
    if not thread_id:
        return False
    n = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_ulong(thread_id), ctypes.py_object(SystemExit))
    if n > 1:  # affected more than one thread state: undo, never leave it armed
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(thread_id), None)
        return False
    return n == 1
'''


def patch(path: Path, anchor_re: str, text: str, marker: str, check: bool) -> str:
    if not path.exists():
        return f"MISSING FILE {path}"
    src = path.read_text()
    if re.search(marker, src, re.M):
        return f"already present in {path.name}"
    m = re.search(anchor_re, src, re.M)
    if not m:
        return f"ANCHOR NOT FOUND in {path.name} (insert manually)"
    if check:
        return f"WOULD PATCH {path.name}"
    shutil.copy(path, str(path) + ".bak")
    path.write_text(src[:m.end()] + text + src[m.end():])
    return f"patched {path.name}"


def pyflakes_undefined(path: Path, name: str) -> int:
    r = subprocess.run([sys.executable, "-m", "pyflakes", str(path)], capture_output=True, text=True)
    return sum(f"undefined name '{name}'" in l for l in (r.stdout + r.stderr).splitlines())


def main():
    check = "--check" in sys.argv
    print(patch(PCA, r"^from typing import Any, Dict, List, Optional[ \t]*$", KILL,
                r"^def _kill_thread\(", check))
    print(patch(V2, r"^import warnings[ \t]*$", "\nimport subprocess", r"^import subprocess[ \t]*$", check))
    if not check:
        for p, n in ((PCA, "_kill_thread"), (V2, "subprocess")):
            if p.exists():
                c = pyflakes_undefined(p, n)
                print(f"pyflakes: undefined '{n}' in {p.name}: {c}  {'OK' if c == 0 else 'STILL BROKEN'}")


if __name__ == "__main__":
    main()
