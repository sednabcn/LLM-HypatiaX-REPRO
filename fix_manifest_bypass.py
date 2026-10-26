"""Patch scripts/make_quarantine_manifest.py: bypass_audit.csv is a per-task audit table, not
result rows, so report it as EVIDENCE with real counts instead of proposing it for quarantine.
usage: python3 fix_manifest_bypass.py scripts/make_quarantine_manifest.py"""
import pathlib, sys

p = pathlib.Path(sys.argv[1]); s = p.read_text()
if "evidence" in s:
    sys.exit("already patched - nothing to do.")
old = '''    proposed = []
    bp = root / "bypass_audit.csv"
    if bp.is_file():
        with open(bp, newline="") as fh:
            rows = list(csv.DictReader(fh))
        proposed.append({"path": "bypass_audit.csv", "n_rows": len(rows), "sha256": sha(bp),
                         "git": commit_of(root, "bypass_audit.csv"),
                         "reason": "rows generated while a hardcoded-formula bypass was reachable; "
                                   "regenerate with HYPATIAX_DISABLE_HARDCODED=1 or keep exploratory"})
'''
new = '''    proposed, evidence = [], []
    bp = root / "bypass_audit.csv"
    if bp.is_file():
        with open(bp, newline="") as fh:
            rows = list(csv.DictReader(fh))
        yes = lambda v: str(v).strip().lower() == "true"
        bypassed = [r for r in rows if yes(r.get("bypassed_when_switch_off"))]
        evidence.append({
            "path": "bypass_audit.csv", "sha256": sha(bp), "git": commit_of(root, "bypass_audit.csv"),
            "what": "per-task audit of the hardcoded-formula bypass (these are tasks, not result rows)",
            "n_tasks": len(rows),
            "n_bypassed_when_switch_off": len(bypassed),
            "n_not_restored_by_switch_on": sum(1 for r in rows if not yes(r.get("switch_on_returns_None"))),
            "bypassed_tasks": [f"{r.get('suite')}:{r.get('id_or_domain')}" for r in bypassed],
        })
'''
old2 = '"quarantined": quarantined, "proposed": proposed}'
new2 = '"quarantined": quarantined, "proposed": proposed, "evidence": evidence}'
if s.count(old) != 1 or s.count(old2) != 1:
    sys.exit("script differs from the expected text - nothing changed.")
p.write_text(s.replace(old, new).replace(old2, new2)); print("patched:", p)
