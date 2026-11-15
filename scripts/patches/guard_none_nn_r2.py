#!/usr/bin/env python3
"""Guard hybrid_predict against a failed NN (train_nn returns r2=None).

Dry run by default; pass --apply to write. Every edit must match exactly
once, otherwise nothing is written.
"""
import argparse
import difflib
import sys
from pathlib import Path

TARGET = Path(
    "hypatiax/core/generation/hybrid_all_domains_llm_nn/"
    "hybrid_system_llm_nn_all_domains.py"
)

EDITS = [
    (
        "verbose NN print tolerates r2=None",
        '''            print(f"  [HYBRID] NN R²: {nn_metrics['r2']:.4f}")
''',
        '''            _nn_r2_txt = (
                f"{nn_metrics['r2']:.4f}"
                if nn_metrics.get("r2") is not None
                else "n/a (NN failed)"
            )
            print(f"  [HYBRID] NN R²: {_nn_r2_txt}")
''',
    ),
    (
        "failed NN maps to -inf so it cannot outrank a successful LLM",
        '''        nn_r2 = nn_metrics.get("r2", 0)
''',
        '''        # None = NN failed (train_nn failure dict); nan = undefined target
        # (rule A) and is left as is. A failed NN must never outrank the LLM.
        nn_r2 = nn_metrics.get("r2")
        if nn_r2 is None:
            nn_r2 = -np.inf
''',
    ),
    (
        "NN-fallback branch tolerates rmse=None",
        '''            final_rmse = nn_metrics["rmse"]
            reason = "NN fallback (LLM failed)"
''',
        '''            final_rmse = nn_metrics.get("rmse")
            if final_rmse is None:
                final_rmse = float("inf")
            reason = "NN fallback (LLM failed)"
''',
    ),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    src = TARGET.read_text(encoding="utf-8")
    new, bad = src, False
    for name, old, repl in EDITS:
        n = new.count(old)
        print(f"[{'ok' if n == 1 else 'FAIL'}] {name}: {n} match(es)")
        if n != 1:
            bad = True
            continue
        new = new.replace(old, repl)
    if bad:
        print("Refusing to write: every edit must match exactly once.")
        return 2

    sys.stdout.writelines(
        difflib.unified_diff(
            src.splitlines(True), new.splitlines(True),
            f"a/{TARGET}", f"b/{TARGET}",
        )
    )
    if args.apply:
        TARGET.write_text(new, encoding="utf-8")
        print("applied")
    else:
        print("dry run; pass --apply to write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
