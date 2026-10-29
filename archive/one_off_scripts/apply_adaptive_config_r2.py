#!/usr/bin/env python3
"""Apply the canonical-R2 migration to hypatiax/core/training/adaptive_config.py by text
anchors (no line numbers), so it works on a locally drifted copy.  Dry run by default.

    python apply_adaptive_config_r2.py [--apply] [path/to/adaptive_config.py]

Idempotent: reports 'already migrated' if the canonical import is present.  If any anchor is
missing it changes NOTHING and says which one, so you can patch that spot by hand.
"""
import re, sys, pathlib

args = [a for a in sys.argv[1:] if a != "--apply"]
apply = "--apply" in sys.argv
path = pathlib.Path(args[0] if args else "hypatiax/core/training/adaptive_config.py")
src = path.read_text()

if "from hypatiax.core.r2_canonical import" in src and "r2_checked(y, y_pred)" in src:
    print("already migrated:", path); sys.exit(0)

IMPORT = "from hypatiax.core.r2_canonical import r2_checked, selection_score\n"
OLD_RE = re.compile(
    r"(?P<ind>[ \t]*)ss_res\s*=\s*float\(np\.sum\(\(y - y_pred\) \*\* 2\)\)\n"
    r"[ \t]*ss_tot\s*=\s*float\(np\.sum\(\(y - np\.mean\(y\)\) \*\* 2\)\)\n"
    r"[ \t]*r2\s*=\s*float\(1 - ss_res / ss_tot\) if ss_tot > 1e-10 else \(1\.0 if ss_res < 1e-10 else 0\.0\)\n")
NEW = '''{i}# R2-CANONICAL: single scoring policy (hypatiax/core/r2_canonical.py).  The old
{i}# absolute 1e-10 guard on ss_tot scored tiny-scale targets (Newton ~1e-11) as 1.0
{i}# or 0.0 regardless of the prediction; the canonical guard is RELATIVE.  A degenerate
{i}# (constant) target is now NaN and a failed prediction -inf; neither can be selected.
{i}r2, r2_status = r2_checked(y, y_pred)
'''
PRINT_OLD = 'print(f"   [seed={seed}] R²={r2:.4f}  train_loss={final_train_loss:.6f}")'
PRINT_NEW = ('note = "" if r2_status == "ok" else f"  [{r2_status}]"\n{i}'
             'print(f"   [seed={seed}] R²={r2:.4f}  train_loss={final_train_loss:.6f}{note}")')
SEL_OLD, SEL_NEW = "if r2 > best_r2:", "if selection_score(r2) > best_r2:"
DOC_OLD = "    Returns:\n        (best_model, best_r2, final_train_loss)\n"
DOC_NEW = DOC_OLD + ("\n    best_r2 is the canonical R² of the selected seed.  If no seed has a defined, finite\n"
                     "    R² (e.g. a constant target), best_model is None and best_r2 is -inf.\n")

problems = []
def need(cond, what):
    if not cond: problems.append(what)

need(src.count("import numpy as np\n") == 1, "exactly one 'import numpy as np' line")
m = OLD_RE.search(src); need(m and len(OLD_RE.findall(src)) == 1, "the 3-line ss_res/ss_tot/r2 block (once)")
need(src.count(PRINT_OLD) == 1 and re.search(r"^[ \t]*" + re.escape(PRINT_OLD), src, re.M), "the verbose R² print line (once)")
need(src.count(SEL_OLD) == 1, "'if r2 > best_r2:' (once)")
need(src.count(DOC_OLD) == 1, "the 'Returns:' docstring block of train_with_config (once)")
if problems:
    print("NOT APPLIED - anchors not found, file left untouched:")
    for p in problems: print("  -", p)
    sys.exit(1)

out = src.replace("import numpy as np\n", "import numpy as np\n\n" + IMPORT, 1)
m = OLD_RE.search(out); ind = m.group("ind")
out = out[:m.start()] + NEW.replace('{i}', ind) + out[m.end():]
pm = re.search(r"^([ \t]*)" + re.escape(PRINT_OLD), out, re.M)
out = out[:pm.start()] + pm.group(1) + PRINT_NEW.replace("{i}", pm.group(1)) + out[pm.end():]
out = out.replace(SEL_OLD, SEL_NEW, 1).replace(DOC_OLD, DOC_NEW, 1)
compile(out, str(path), "exec")
if apply:
    path.write_text(out); print("applied:", path)
else:
    print("dry run OK - all anchors found; re-run with --apply")
