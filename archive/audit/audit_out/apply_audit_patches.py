#!/usr/bin/env python3
"""Apply two audit patches from the repo root.  Preview first:

    python3 apply_audit_patches.py --dry-run
    python3 apply_audit_patches.py

  1. all-domains hybrid: delete the (gated) Gaussian normalisation hint.
     Clean-run prompts stay byte-identical (the line becomes a blank line).
  2. ensemble: delete the canonical Kelly fallback (a canned ground-truth answer).

Safety: every required anchor must match exactly once; otherwise that patch is skipped
and the file is left untouched.  The patched source must still parse.  Re-running is safe
(already-applied patches are reported and skipped).
"""
import argparse
import ast
import sys
from pathlib import Path

ALL_DOMAINS = "hypatiax/core/generation/hybrid_all_domains_llm_nn/hybrid_system_llm_nn_all_domains.py"
ENSEMBLE = "hypatiax/core/generation/hybrid_defi_llm_nn/hybrid_ensemble_system_defi_domain.py"

GAUSS_OLD_DEF = '''        _norm_hint = "" if _hints_disabled() else (
            "6. If the task involves a probability density or distribution, include the FULL "
            "normalization constant (e.g. 1/(sigma*sqrt(2*pi)) for Gaussian)")
'''
GAUSS_NEW_DEF = '''        _norm_hint = ""   # deleted, not gated: the Gaussian normalisation hint is target-formula text
'''
GAUSS_OLD_USE = "5. Use numpy: np.sqrt, np.log, np.exp, etc.\n{_norm_hint}\n"
GAUSS_NEW_USE = "5. Use numpy: np.sqrt, np.log, np.exp, etc.\n\n"

CANON_OLD_FN = '''def canonical_fallback_allowed() -> bool:
    """The canned Kelly answer is a ground-truth leak.  Fail-closed: it is used only when
    a human explicitly opts in (HYPATIAX_ALLOW_CANONICAL_FALLBACK=1) AND the run is not
    strict-live.  An unset variable therefore never enables the bypass."""
    return _flag("HYPATIAX_ALLOW_CANONICAL_FALLBACK") and not strict_live_mode()


'''
CANON_OLD_CONST = '''CANONICAL_KELLY = """
def formula(expected_fee_apy, il_risk):
    risk_aversion = 2.0
    f_star = expected_fee_apy / (risk_aversion * il_risk**2)
    return np.minimum(f_star, 1.0)
"""


'''
CANON_OLD_USE = '''    if no_code and canonical_fallback_allowed():
        # The canned Kelly answer is a ground-truth leak: label it.
        llm_result = {"python_code": CANONICAL_KELLY, "formula": "min(mu/(lambda*sigma^2),1.0)"}
        prov.update(llm_called=False, bypass_kind="canonical_fallback",
                    llm_source="canonical_fallback")
        print("\u26a0  local fallback for: " + desc[:50] + " (no usable LLM code)")
        print("Using canonical fallback (labelled bypass_kind=canonical_fallback).")
    elif no_code:
        print("No usable LLM code and canonical fallback not enabled; LLM arm recorded as failed.")
'''
CANON_NEW_USE = '''    if no_code:
        print("No usable LLM code; LLM arm recorded as failed (no canned answer is substituted).")
'''
CANON_OPT_MSG = (
    '''"HYPATIAX_DISABLE_PROMPT_HINTS=1 (canonical fallback is enabled only if "
              "HYPATIAX_ALLOW_CANONICAL_FALLBACK=1)")''',
    '''"HYPATIAX_DISABLE_PROMPT_HINTS=1")''',
)
CANON_OPT_DOC = (
    '''The canonical Kelly
    fallback is itself a ground-truth leak, so it is labelled
    bypass_kind="canonical_fallback" and is DISABLED when both
    HYPATIAX_DISABLE_HARDCODED=1 and HYPATIAX_DISABLE_PROMPT_HINTS=1 are set
    (a clean live run must not silently substitute the answer).''',
    '''The former canonical Kelly
    fallback (a canned ground-truth answer) has been deleted.''',
)

PATCHES = [
    {
        "name": "delete gated Gaussian hint (all-domains hybrid)",
        "path": ALL_DOMAINS,
        "required": [(GAUSS_OLD_DEF, GAUSS_NEW_DEF), (GAUSS_OLD_USE, GAUSS_NEW_USE)],
        "optional": [],
    },
    {
        "name": "delete canonical Kelly fallback (ensemble)",
        "path": ENSEMBLE,
        "required": [(CANON_OLD_FN, ""), (CANON_OLD_CONST, ""), (CANON_OLD_USE, CANON_NEW_USE)],
        "optional": [CANON_OPT_MSG, CANON_OPT_DOC],
    },
]


def run(patch, write):
    path = Path(patch["path"])
    if not path.is_file():
        return "ERROR", f"file not found: {path} (run from the repo root)"
    src = path.read_text(encoding="utf-8")
    req = patch["required"]
    counts = [src.count(old) for old, _ in req]

    if all(c == 0 for c in counts) and all(new in src for _, new in req if new):
        return "SKIP", "already applied"
    if any(c != 1 for c in counts):
        return "ERROR", (f"anchors matched {counts} times (need exactly 1 each); nothing changed. "
                         "The file differs from what I saw - paste the surrounding lines.")

    out = src
    for old, new in req:
        out = out.replace(old, new)
    warnings = []
    for old, new in patch["optional"]:
        if out.count(old) == 1:
            out = out.replace(old, new)
        else:
            warnings.append(f"optional text not updated (edit by hand): {old[:50]!r}...")
    try:
        ast.parse(out)
    except SyntaxError as e:
        return "ERROR", f"patched source would not parse ({e}); nothing changed"

    if write:
        path.write_text(out, encoding="utf-8")
    verb = "patched" if write else "would patch"
    return "OK", verb + ("; " + "; ".join(warnings) if warnings else "")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    args = ap.parse_args(argv)
    failed = False
    for patch in PATCHES:
        status, msg = run(patch, write=not args.dry_run)
        print(f"[{status:5s}] {patch['name']}: {msg}")
        failed |= status == "ERROR"
    if not args.dry_run and not failed:
        print("\nNext: confirm nothing is left, then run the tests:")
        print(f"  grep -n '_norm_hint' {ALL_DOMAINS}")
        print(f"  grep -n -i 'canonical_fallback\\|CANONICAL_KELLY\\|ALLOW_CANONICAL' {ENSEMBLE}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
