#!/usr/bin/env python3
"""Apply the clean-run patch to the two symbolic-search files.

Run from the repo root:
    python3 apply_flag_patch.py --dry-run     # show diffs only
    python3 apply_flag_patch.py               # write changes (keeps *.bak)

Each edit must match exactly the expected number of places, otherwise the
script stops and changes nothing in that file.  Already-patched files are skipped.
"""
import argparse, difflib, re, shutil, sys
from pathlib import Path

PHYS = Path("hypatiax/tools/symbolic/physics_aware_regressor.py")
ENGINE = Path("hypatiax/tools/symbolic/symbolic_engine.py")
IMPORT = "from hypatiax.core.flags import clean_run"
MARK = "# [clean-run patch]"


def patch_physics(src: str) -> str:
    # 1) early return to the generic population inside _initialize_smart_population
    pat = re.compile(
        r'(def _initialize_smart_population\(self, variable_names, var_stats\):.*?\n'
        r'(?P<ind>[ ]+)d = self\.domain\.lower\(\) if self\.domain else "general"\n)',
        re.S,
    )
    m = pat.search(src)
    if not m:
        raise SystemExit("physics: _initialize_smart_population anchor not found")
    ind = m.group("ind")
    insert = (
        f"{ind}{MARK} no equation-specific seeds in a clean run\n"
        f"{ind}{IMPORT}\n"
        f"{ind}if clean_run():\n"
        f"{ind}    return self._init_general_population(variable_names, var_stats)\n"
    )
    src = src[: m.end()] + insert + src[m.end():]

    # 2) domain-keyed mutation blends: force domain "general" in a clean run
    line = re.compile(
        r'^(?P<ind>[ ]+)d(?P<sp>[ ]+)= self\.domain\.lower\(\) if self\.domain else "general"[ ]*$',
        re.M,
    )
    # skip the occurrence we just handled (it is followed by our MARK line)
    out, n, pos = [], 0, 0
    for mm in line.finditer(src):
        tail = src[mm.end(): mm.end() + 80]
        if MARK in tail:
            continue
        out.append(src[pos: mm.start()])
        i, s = mm.group("ind"), mm.group("sp")
        out.append(
            f'{i}{IMPORT} as _clean_run  {MARK}\n'
            f'{i}d{s}= "general" if _clean_run() else '
            f'(self.domain.lower() if self.domain else "general")'
        )
        pos, n = mm.end(), n + 1
    out.append(src[pos:])
    if n == 0:
        raise SystemExit("physics: no mutation-blend 'd = self.domain.lower()' line found")
    print(f"physics: patched {n} mutation-blend domain line(s)")
    return "".join(out)


def patch_engine(src: str) -> str:
    pat = re.compile(
        r'(?P<ind>[ ]+)_needs_inv_trig = _needs_basic_trig and any\(\s*'
        r'kw in _eq_hint\s*for kw in \((?P<kws>[^)]*)\)\s*\)',
        re.S,
    )
    m = pat.search(src)
    if not m:
        raise SystemExit("engine: _needs_inv_trig anchor not found")
    i = m.group("ind")
    new = (
        f"{i}{IMPORT} as _clean_run  {MARK}\n"
        f"{i}_needs_inv_trig = _needs_basic_trig and (\n"
        f"{i}    _clean_run()  # clean run: generic inverse-trig for the whole trig domain, no name matching\n"
        f"{i}    or any(kw in _eq_hint for kw in ({m.group('kws')}))\n"
        f"{i})"
    )
    return src[: m.start()] + new + src[m.end():]


def run(path: Path, fn, dry: bool):
    if not path.exists():
        raise SystemExit(f"{path} not found (run from the repo root)")
    old = path.read_text()
    if MARK in old:
        print(f"{path}: already patched, skipping")
        return
    new = fn(old)
    sys.stdout.writelines(
        difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                             f"a/{path}", f"b/{path}", n=2)
    )
    if not dry:
        shutil.copy2(path, str(path) + ".bak")
        path.write_text(new)
        print(f"{path}: written (backup: {path}.bak)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    run(PHYS, patch_physics, a.dry_run)
    run(ENGINE, patch_engine, a.dry_run)
