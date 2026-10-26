#!/usr/bin/env python3
"""Close Step 1 / Phase 1 of the LLM-HypatiaX-REPRO audit.

    python scripts/close_phase1.py              # audit only (read-only) -> PASS/FAIL/MANUAL table
    python scripts/close_phase1.py --apply      # dry run: show every diff, write nothing
    python scripts/close_phase1.py --apply --write   # write the patches + regression tests

  Extra options
    --json PATH           also write the audit (per checklist item) as JSON
    --run-bypass-audit    additionally execute scripts/bypass_audit.py (not read-only)
    env PHASE1_ROOT=...   repo root, if the script is not in <repo>/scripts/

Design (same conventions as scripts/migrate_r2_repro.py)
  * Code is located by anchor text / the ``ast`` module, never by line number,
    so it applies to a working tree that has drifted from GitHub master.
  * Idempotent: a patch whose "already fixed" predicate holds is skipped.
  * Every rewritten .py file is re-parsed before it is written.
  * Nothing is written without ``--write``.

What it fixes (Phase 1 items from STEP1-PHASE1-TO-CLOSE)
  P1  metrics.py: __main__ self-tests contradicted the doctests (NaN / -inf policy);
      unused _REL_EPS removed; compute_near_perfect_rate unified to ``>=`` and
      non-finite scores never count as passes (same rule as is_recovered).
  P2  hybrid_system_v50_2._r2_np          -> delegates to r2_canonical.r2_checked
  P3  baseline_pure_llm_defi_discovery    -> evaluator delegates to r2_checked
  P4  failed rows no longer report r2 = 0.0 -> -inf (a failure, never a score)
  P5  one catastrophic definition (metrics.CATASTROPHIC_THRESHOLD, NaN/-inf counted)
      in the noise sweep
  P6  provenance: ``generation_path`` added; ``bypass_kind`` derived from
      ``llm_called`` instead of a literal (v50_2 is patched through the AST, no text anchors)
  P9  M4 (hybrid_system_llm_nn_all_domains.py): private ss_tot R2 -> r2_checked
  P7  sign-flip / bypass flag state written into the sweep JSON and the protocol block
  P8  regression tests: hypatiax/experiments/tests/test_phase1_close.py
  P10 run_comparative_suite_benchmark_v2.py: private ss_tot R2 -> r2_checked / refusal
      a  rmse-algebra R2 fallback removed (no y_pred => unavailable, never 1.0 by tolerance)
      b  NN-correction strategy scoring -> r2_checked (non-finite never selected)
      c  synthetic y_pred ('algebraic_reconstruction') removed: no fabricated predictions
      d  rmse-algebra R2 fallback removed in the HybridSystemLLMNN adapter

Audit coverage (rolled up to the six rows of Phase1_Closure_Checklist.xlsx)
  1 provenance   2 hardcoded bypass   3 M4 formula output
  4 R2 policy / evaluator guard   5 noise sweep   6 quarantine (AUDIT/)

What it cannot fix (reported as MANUAL by the audit)
  * M4 stored output (rerun or downgrade to exploratory)
  * Supplement A Listing 8
  * regenerating / quarantining the 11 historical bypassed rows
  * stored rows produced via the removed 'algebraic_reconstruction' path (audit lists them; quarantine)
"""
from __future__ import annotations

import argparse
import ast
import difflib
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import tokenize

ROOT = pathlib.Path(os.environ.get("PHASE1_ROOT") or pathlib.Path(__file__).resolve().parents[1]).resolve()
PKG = ROOT / "hypatiax"
MARK = "PHASE1-FIX"

F_METRICS = PKG / "core/metrics.py"
F_V50 = PKG / "tools/symbolic/hybrid_system_v50_2.py"
F_BASE = PKG / "core/base_pure_llm/baseline_pure_llm_defi_discovery.py"
F_SWEEP = PKG / "experiments/benchmarks/run_noise_sweep_benchmark.py"
F_PCA = PKG / "experiments/benchmarks/run_comparative_suite_benchmark_pca.py"
F_V2 = PKG / "experiments/benchmarks/run_comparative_suite_benchmark_v2.py"
F_TESTS = PKG / "experiments/tests/test_phase1_close.py"
BASELINE_JSON = PKG / "experiments/tests/r2_legacy_baseline.json"

# files scanned for "failed row reports r2 = 0.0"
FAILED_ROW_GLOBS = ["tools/symbolic/*.py", "core/generation/**/*.py",
                    "experiments/benchmarks/run_comparative_suite_benchmark_*.py"]


# --------------------------------------------------------------------------- helpers
def has_ss_tot(src: str) -> bool:
    """True only if ``ss_tot`` is used as an identifier in code (comments/docstrings ignored)."""
    try:
        return any(t.type == tokenize.NAME and t.string == "ss_tot"
                   for t in tokenize.generate_tokens(io.StringIO(src).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return bool(re.search(r"\bss_tot\b", src))


def rel(p: pathlib.Path) -> str:
    return p.relative_to(ROOT).as_posix()


def read(p: pathlib.Path) -> str:
    return p.read_text(encoding="utf-8")


def function_span(src: str, name: str) -> tuple[int, int] | None:
    """1-based inclusive (start, end) line span of top-level/method ``name``."""
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            start = min([n.lineno] + [d.lineno for d in n.decorator_list])
            return start, n.end_lineno
    return None


def replace_function(src: str, name: str, new_text: str) -> str:
    span = function_span(src, name)
    if span is None:
        raise LookupError(f"function {name!r} not found")
    lines = src.splitlines(keepends=True)
    a, b = span
    return "".join(lines[:a - 1]) + new_text.rstrip("\n") + "\n" + "".join(lines[b:])


def sub_once(src: str, old: str, new: str, what: str) -> str:
    if src.count(old) != 1:
        raise LookupError(f"{what}: anchor found {src.count(old)}x (expected 1)")
    return src.replace(old, new)


# --------------------------------------------------------------------------- patches
# Each patch: (id, file, ok(src)->bool, apply(src)->src)
def _metrics_ok(s):
    return ('assert compute_r2([5, 5, 5], [5, 5, 5]) == 1.0' not in s
            and "_REL_EPS" not in s and "np.mean(arr > threshold)" not in s)


def _metrics_apply(s: str) -> str:
    # 1) __main__ self-tests: make the asserts agree with the doctests / canonical policy.
    a = s.index("    # Regression tests for the evaluator guard / NaN handling")
    b = s.index('    print("✓ All metrics self-tests passed")')
    new_block = f'''    # Regression tests ({MARK}): assertions match the canonical policy (and the
    # doctests above): degenerate target -> NaN, non-finite prediction -> -inf.
    assert abs(compute_r2([1e-6, 2e-6, 3e-6], [1e-6, 2e-6, 4e-6]) - 0.5) < 1e-9, \\
        "small-scale target must not be treated as constant"
    assert compute_r2([1, 2, 3], [1, float("inf"), 3]) == float("-inf")
    assert math.isnan(compute_r2([5, 5, 5], [5, 5, 5])), "constant target is NaN, never 1.0"
    assert math.isnan(compute_r2([5, 5, 5], [5, 5, 6])), "constant target is NaN, never 0.0"
    assert evaluate_all([1, 2, 3], [float("nan")] * 3)["catastrophic"] is True
    try:
        compute_r2([1, float("nan")], [1, 2])
    except ValueError:
        pass
    else:
        raise AssertionError("NaN y_true must raise")

'''
    s = s[:a] + new_block + s[b:]
    # 2) unused constant
    s = re.sub(r"# Constant-target detection is RELATIVE.*?_REL_EPS = 1e-12\n\n?", "", s, flags=re.S)
    # 3) one comparison rule: >= (as is_recovered) and non-finite never passes
    s = sub_once(s, "return float(np.mean(arr > threshold))",
                 f"return float(np.mean(np.isfinite(arr) & (arr >= threshold)))  # {MARK}: >=, as is_recovered",
                 "near_perfect")
    s = s.replace("Fraction of tasks whose R² exceeds *threshold*.",
                  "Fraction of tasks whose R² is >= *threshold* (same rule as ``is_recovered``).")
    return s


_V50_NEW = f'''def _r2_np(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Plain numpy R² ({MARK}: delegates to the canonical policy).

    Degenerate target -> NaN (never 1.0); non-finite prediction -> -inf.
    """
    from hypatiax.core.r2_canonical import r2_checked
    return r2_checked(y_true, y_pred)[0]
'''


def _v50_r2_ok(s):
    sp = function_span(s, "_r2_np")
    return bool(sp) and "r2_checked" in "".join(s.splitlines(keepends=True)[sp[0] - 1:sp[1]])


def _v50_r2_apply(s: str) -> str:
    return replace_function(s, "_r2_np", _V50_NEW)


def _byte_offsets(src: str):
    sb = src.encode("utf-8")
    starts = [0]
    for ln in sb.split(b"\n")[:-1]:
        starts.append(starts[-1] + len(ln) + 1)
    return sb, starts


def _v50_prov_edits(src: str) -> list[tuple[int, int, str]]:
    """Byte-range edits found via the AST (no text anchors, so drift-proof).

    For every dict literal holding both ``llm_called`` and ``bypass_kind``:
      * llm_called is a real expression (success row) and bypass_kind is the literal "none"
            -> bypass_kind = "live" if (<llm_called expr>) else "none"
      * generation_path missing -> add it (error rows get "error")
    """
    tree = ast.parse(src)
    sb, starts = _byte_offsets(src)

    def off(line, col):
        return starts[line - 1] + col

    edits: list[tuple[int, int, str]] = []
    for d in ast.walk(tree):
        if not isinstance(d, ast.Dict):
            continue
        keys = {k.value: (k, v) for k, v in zip(d.keys, d.values)
                if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        if "bypass_kind" not in keys or "llm_called" not in keys:
            continue
        bk_key, bk = keys["bypass_kind"]
        _, llm = keys["llm_called"]
        is_false = isinstance(llm, ast.Constant) and llm.value is False
        llm_src = ast.get_source_segment(src, llm)
        if not is_false and isinstance(bk, ast.Constant) and bk.value == "none":
            edits.append((off(bk.lineno, bk.col_offset), off(bk.end_lineno, bk.end_col_offset),
                          f'"live" if ({llm_src}) else "none"'))
        if "generation_path" not in keys:
            if is_false:
                gp = '"error"' if "error" in keys else '"symbolic"'
            else:
                gp = f'"symbolic+llm" if ({llm_src}) else "symbolic"'
            ind = " " * bk_key.col_offset
            end = off(bk.end_lineno, bk.end_col_offset)
            edits.append((end, end, f',\n{ind}"generation_path": {gp}'))
    return edits


def _v50_prov_ok(s):
    return not _v50_prov_edits(s)


def _v50_prov_apply(s: str) -> str:
    edits = _v50_prov_edits(s)
    if not edits:
        raise LookupError("v50: no dict literal with both llm_called and bypass_kind found. Send:\n"
                          "    grep -n -B6 -A6 '\"bypass_kind\"' hypatiax/tools/symbolic/hybrid_system_v50_2.py")
    sb, _ = _byte_offsets(s)
    for a_, b_, txt in sorted(edits, key=lambda e: (e[0], e[1]), reverse=True):
        sb = sb[:a_] + txt.encode("utf-8") + sb[b_:]
    return sb.decode("utf-8")


_BASE_RE = re.compile(
    r"( +)ss_res = np\.sum\(\(y_true - y_pred\) \*\* 2\)\n"
    r" +ss_tot = np\.sum\(\(y_true - np\.mean\(y_true\)\) \*\* 2\)\n"
    r".*?_r2_status = \"constant_target_mismatch\"\n", re.S)


_BASE_HEAL = re.compile(
    r" *# PHASE1-FIX: derived from the measured outcome, not the pre-call literal\n"
    r" *\"bypass_kind\": \"live\" if _response_received else \"none\",\n")


P3B = "PHASE1-FIX-P3b"
_P3_OLD = re.compile(
    r"( *)# PHASE1-FIX: canonical R\^2 \(hypatiax\.core\.r2_canonical\.r2_checked\)\.\n"
    r"(?: *#[^\n]*\n){2}"
    r" *from hypatiax\.core\.r2_canonical import r2_checked as _r2_checked\n"
    r" *(\w+), (\w+) = _r2_checked\(y_true, y_pred\)\n")


def _p3_block(ind: str, r2v: str, stv: str) -> str:
    return (f"{ind}# {P3B}: canonical R^2 (hypatiax.core.r2_canonical.r2_checked). A degenerate target keeps the\n"
            f"{ind}# evaluator's existing contract pinned by test_baseline_regressions: exact match -> 1.0,\n"
            f"{ind}# mismatch -> -inf. The 1e6 + N(0,1) offset case is scored on its spread, not its offset.\n"
            f"{ind}from hypatiax.core.r2_canonical import r2_checked as _r2_checked\n"
            f"{ind}{r2v}, {stv} = _r2_checked(y_true, y_pred)\n"
            f"{ind}if {stv} == \"degenerate_target\":\n"
            f"{ind}    _match = bool(np.allclose(y_pred, y_true, rtol=1e-9, atol=1e-30))\n"
            f"{ind}    {r2v} = 1.0 if _match else float(\"-inf\")\n"
            f"{ind}    {stv} = \"constant_target_match\" if _match else \"constant_target_mismatch\"\n")


def _base_r2_ok(s):
    return P3B in s


def _base_r2_fallback(s: str):
    """Locate the evaluator block by structure when the exact regex misses.

    Span = the ``ss_res =`` line just before the first ``ss_tot`` line preceding the first
    ``constant_target`` token, through the last line (within 30) mentioning ``constant_target``.
    Names of the R^2 / status variables are read from the span itself; ambiguity -> LookupError.
    """
    lines = s.splitlines(keepends=True)
    first = next((i for i, ln in enumerate(lines) if "constant_target" in ln), None)
    if first is None:
        return None
    tot = next((i for i in range(first, max(first - 40, -1), -1) if re.search(r"\bss_tot\s*=", lines[i])), None)
    if tot is None:
        raise LookupError("baseline: no ss_tot assignment above the constant_target branch")
    res = next((i for i in range(tot, max(tot - 6, -1), -1) if re.search(r"\bss_res\s*=", lines[i])), tot)
    last = max(i for i in range(first, min(first + 30, len(lines))) if "constant_target" in lines[i])
    # extend to the end of the enclosing if/elif/else chain
    ind = len(lines[res]) - len(lines[res].lstrip())
    end = last
    def _cont(t: str) -> bool:
        w = len(t) - len(t.lstrip())
        return (not t.strip()) or w > ind or (w == ind and re.match(r"\s*(else|elif)\b", t) is not None)
    while end + 1 < len(lines) and _cont(lines[end + 1]):
        end += 1
    while not lines[end].strip():
        end -= 1
    span = "".join(lines[res:end + 1])
    st = set(re.findall(r"(\w*r2_status\w*|\w*status\w*)\s*=\s*[\"']constant_target", span))
    if len(st) != 1:
        raise LookupError(f"baseline: cannot identify status variable (candidates: {sorted(st)})")
    status_var = st.pop()
    lhs = [v for v in re.findall(r"^\s*(\w+)\s*=", span, re.M)
           if v not in {"ss_res", "ss_tot", status_var}]
    r2_names = [v for v in dict.fromkeys(lhs) if re.fullmatch(r"r2|r_?squared|r2_score|r2_val", v)]
    if len(r2_names) != 1:
        raise LookupError(f"baseline: cannot identify the R^2 variable (candidates: {list(dict.fromkeys(lhs))})")
    return res, end, " " * ind, r2_names[0], status_var


def _base_r2_apply(s: str) -> str:
    h = _P3_OLD.search(s)  # heal the first version of this patch (it changed the constant-target contract)
    if h:
        return s[:h.start()] + _p3_block(h.group(1), h.group(2), h.group(3)) + s[h.end():]
    m = _BASE_RE.search(s)
    if m:
        ind, r2v, stv = m.group(1), "r2", "_r2_status"
        a_, b_ = m.start(), m.end()
        lines_new = None
    else:
        try:
            fb = _base_r2_fallback(s)
        except LookupError as e:
            raise LookupError(f"{e}. Send the output of:\n    grep -n -B14 -A14 constant_target_match "
                              "hypatiax/core/base_pure_llm/baseline_pure_llm_defi_discovery.py") from None
        if fb is None:
            raise LookupError("baseline: no constant_target token found")
        res, end, ind, r2v, stv = fb
        offs = [0]
        for ln in s.splitlines(keepends=True):
            offs.append(offs[-1] + len(ln))
        a_, b_ = offs[res], offs[end + 1]
    new = _p3_block(ind, r2v, stv)
    return s[:a_] + new + s[b_:]


def _base_prov_ok(s):
    return "generation_path" in s and not _BASE_HEAL.search(s)


def _base_prov_apply(s: str) -> str:
    # heal: an earlier version of this script overrode bypass_kind on the error row with
    # "live if response received"; the repo's own tests define it as the PATH ("live"), so drop it.
    s = _BASE_HEAL.sub("", s)
    if "generation_path" not in s:
        s = sub_once(s, '                "llm_attempted": True,\n                **_prov,',
                     f'                "llm_attempted": True,\n                **_prov,\n'
                     f'                "generation_path": "pure_llm_api",  # {MARK}',
                     "baseline success provenance")
        s = sub_once(s, '                "error_stage": "post_response" if _response_received else "api_request",\n                **_prov,',
                     '                "error_stage": "post_response" if _response_received else "api_request",\n'
                     f'                **_prov,\n'
                     f'                "generation_path": "pure_llm_api" if _response_received else "pure_llm_api_failed",  # {MARK}',
                     "baseline error provenance")
    return s


F_M4 = PKG / "core/generation/hybrid_all_domains_llm_nn/hybrid_system_llm_nn_all_domains.py"
_M4_RES = re.compile(r"^([ \t]*)ss_res\s*=\s*np\.sum\(\(\s*(\w+)\s*-\s*(\w+)\s*\)\s*\*\*\s*2\)[^\n]*\n", re.M)


def _ctx(path: pathlib.Path, token: str, before: int = 4, after: int = 10) -> str:
    ls = read(path).splitlines()
    keep = sorted({k for i, ln in enumerate(ls) if re.search(token, ln)
                   for k in range(max(0, i - before), min(len(ls), i + after + 1))})
    return "\n".join(f"{k + 1:6}: {ls[k]}" for k in keep) or "(no match)"


def _m4_ok(s):
    return not has_ss_tot(s)


def _m4_apply(s: str) -> str:
    """Replace each ``ss_res/ss_tot -> r2`` block by one r2_checked call (arg order read from ss_res)."""
    lines = s.splitlines(keepends=True)
    out, i, n = [], 0, 0
    while i < len(lines):
        m = _M4_RES.match(lines[i])
        if m:
            j = next((k for k in range(i + 1, min(i + 12, len(lines)))
                      if re.search(r"ss_res\s*/\s*(ss_tot|\(?\s*ss_tot)", lines[k])), None)
            if j is not None and any(re.search(r"\bss_tot\s*=", lines[k]) for k in range(i, j + 1)):
                tgt = re.match(r"\s*(\w+)\s*=", lines[j])
                if not tgt:
                    raise LookupError(f"M4: cannot read R^2 target name at line {j + 1}: {lines[j].strip()!r}")
                ind, yt, yp = m.group(1), m.group(2), m.group(3)
                out.append(f"{ind}# {MARK}: canonical R^2 (degenerate target -> NaN, non-finite pred -> -inf)\n"
                           f"{ind}from hypatiax.core.r2_canonical import r2_checked as _r2_checked\n"
                           f"{ind}{tgt.group(1)} = _r2_checked({yt}, {yp})[0]\n")
                i, n = j + 1, n + 1
                continue
        out.append(lines[i])
        i += 1
    new = "".join(out)
    if not n:
        raise LookupError("M4: no ss_res/ss_tot block matched. Code around ss_tot (paste this):\n" + _ctx(F_M4, r"\bss_tot\b"))
    if has_ss_tot(new):
        raise LookupError(f"M4: {n} block(s) rewritten but ss_tot still appears; refusing partial patch. Code around ss_tot (paste this):\n" + _ctx(F_M4, r"\bss_tot\b"))
    return new


def _sweep_ok(s):
    return MARK in s and "_CATASTROPHIC_R2_THRESHOLD: float = 0.90" not in s


def _sweep_apply(s: str) -> str:
    s = sub_once(s, "_CATASTROPHIC_R2_THRESHOLD: float = 0.90",
                 f"# {MARK}: one catastrophic definition for the whole repo (R2 < -1; NaN/-inf counted)\n"
                 "from hypatiax.core.metrics import CATASTROPHIC_THRESHOLD as _CATASTROPHIC_R2_THRESHOLD\n"
                 f"_RUN_FLAGS: dict = {{}}  # {MARK}: filled by main() from enforce()",
                 "sweep threshold")
    s = s.replace("(R2 < 0.90)", "(R2 < metrics.CATASTROPHIC_THRESHOLD, or non-finite)")
    # non-finite rows of a method that actually ran are catastrophic (not "missing cells")
    s = sub_once(s, "                if not _r2_ok:\n                    n_nonfinite += 1\n",
                 "                if not _r2_ok:\n                    n_nonfinite += 1\n"
                 f"                    if res:  # {MARK}: NaN/-inf from a method that ran = catastrophic\n"
                 "                        n_catastrophic += 1\n"
                 "                        catastrophic_failures.append(\n"
                 "                            {\"equation\": eq_name, \"method\": method, \"r2\": float(\"-inf\")}\n"
                 "                        )\n",
                 "sweep nonfinite")
    s = sub_once(s, "    from hypatiax.core.enforce_flags import enforce; enforce()  # fail-closed flag guard",
                 "    global _RUN_FLAGS\n"
                 "    from hypatiax.core.enforce_flags import enforce\n"
                 f"    _RUN_FLAGS = enforce()  # fail-closed flag guard; state recorded in output ({MARK})",
                 "sweep enforce")
    s = sub_once(s, "        json.dump(agg, f, indent=2, default=str)",
                 f"        agg[\"run_flags\"] = dict(_RUN_FLAGS)  # {MARK}: sign-flip / bypass flag state\n"
                 "        json.dump(agg, f, indent=2, default=str)",
                 "sweep dump")
    return s


def _v2_ok(s):
    return "r2_sign_flip_enabled" in s


def _v2_apply(s: str) -> str:
    return sub_once(s, '                "noise_level": 0.0 if noiseless else _HYPATIAX_NOISE_LEVEL,',
                    '                "noise_level": 0.0 if noiseless else _HYPATIAX_NOISE_LEVEL,\n'
                    f'                "r2_sign_flip_enabled": os.environ.get("HYPATIAX_R2_SIGN_FLIP", "0"),  # {MARK}',
                    "v2 protocol")


# ---- P10: run_comparative_suite_benchmark_v2.py -- private R^2 + fabricated y_pred
P10 = f"{MARK}-P10"

# a) lines ~2254: R^2 rebuilt from rmse with an absolute tolerance (returns 1.0 on a constant target)
_V2A_RE = re.compile(
    r"^([ \t]*)elif np\.isfinite\(rmse_val\) and rmse_val >= 0:\n"
    r"(?:[^\n]*\n)*?"
    r"(?=\1else:\n\1[ \t]+return self\._unavailable\(\n[ \t]*\"r2=0 and no y_pred or rmse)", re.M)
_V2A_MSG = '"r2=0 and no y_pred or rmse: formula evaluation failed silently"'
_V2A_TRUTHY = 'y_pred_arr = eval_.get("y_pred") or result.get("y_pred")'


def _v2a_ok(s):
    return f"{P10}a" in s


def _v2a_apply(s: str) -> str:
    s, n = _V2A_RE.subn("", s)
    if n != 1:
        raise LookupError(f"v2 P10a: rmse-algebra branch matched {n}x (expected 1). "
                          "Code around it (paste this):\n" + _ctx(F_V2, r"rmse_val >= 0"))
    s = sub_once(s, _V2A_MSG,
                 f'"r2=0 and no y_pred: R2 cannot be verified ({P10}a: rmse-algebra fallback removed)"',
                 "v2 P10a message")
    # `a or b` on an ndarray raises "truth value is ambiguous"; and [] / 0-length must not fall through
    ind = re.search(rf"^([ \t]*){re.escape(_V2A_TRUTHY)}$", s, re.M)
    if ind:
        i = ind.group(1)
        s = s.replace(ind.group(0),
                      f'{i}y_pred_arr = eval_.get("y_pred")  # {P10}a: explicit None test, not truthiness\n'
                      f'{i}if y_pred_arr is None:\n{i}    y_pred_arr = result.get("y_pred")')
    return s


# b) lines ~2509-2537: NN-correction strategies scored with max(ss_tot, 1e-300)
_V2B_TOT = re.compile(r"^([ \t]*)ss_tot[ \t]*=[ \t]*float\(np\.sum\(\(y - np\.mean\(y\)\) \*\* 2\)\)\n"
                      r"(?=[ \t]*\n[ \t]*# Strategy A)", re.M)
# score statement AND its comparison are matched together, so a duplicate `if r2_log > best_r2:` elsewhere is never hit
_V2B_LOG = re.compile(r"r2_log\s*=\s*float\(1\.0\s*-\s*np\.sum\(\(y - y_log_corrected\) \*\* 2\)\s*"
                      r"/\s*max\(ss_tot,\s*1e-300\)\)[ \t]*\n([ \t]*)if r2_log > best_r2:")
_V2B_LIN = re.compile(r"r2_lin\s*=\s*float\(1\.0\s*-\s*np\.sum\(\(y - y_lin_corrected\) \*\* 2\)\s*"
                      r"/\s*max\(ss_tot,\s*1e-300\)\)[ \t]*\n([ \t]*)if r2_lin > best_r2:")


def _v2b_ok(s):
    return f"{P10}b" in s


def _v2b_apply(s: str, F=None) -> str:
    F = F or F_V2
    def one(s, rx, repl, what):
        new, n = rx.subn(repl, s)
        if n != 1:
            raise LookupError(f"{F.name} P10b {what}: matched {n}x (expected 1). Code around it (paste this):\n"
                              + _ctx(F, r"\bss_tot\b|r2_log|r2_lin"))
        return new
    s = one(s, _V2B_TOT, lambda m: (f"{m.group(1)}# {P10}b: canonical R^2 (no private ss_tot / 1e-300 guard)\n"
                                    f"{m.group(1)}from hypatiax.core.r2_canonical import r2_checked as _r2_checked\n"),
            "ss_tot")
    for rx, v, y_, nm in ((_V2B_LOG, "r2_log", "y_log_corrected", "strategy A"),
                          (_V2B_LIN, "r2_lin", "y_lin_corrected", "strategy B")):
        s = one(s, rx, lambda m, v=v, y_=y_: (f"{v} = _r2_checked(y, {y_})[0]  # {P10}b\n"
                                              f"{m.group(1)}if np.isfinite({v}) and {v} > best_r2:"), nm)
    return s


# c) lines ~2740-2760: y_pred fabricated from the reported R^2 + noise, then re-scored as if real
def _v2c_ok(s):
    return '_ypred_source = "algebraic_reconstruction"' not in s


def _v2c_apply(s: str) -> str:
    lines = s.splitlines(keepends=True)
    ends = [i for i, ln in enumerate(lines) if "algebraic reconstruction failed" in ln]
    if len(ends) != 1:
        raise LookupError(f"v2 P10c: end marker found {len(ends)}x (expected 1)")
    e = ends[0]
    exc = next((i for i in range(e, max(e - 12, -1), -1)
                if re.match(r"\s*except Exception as _rec_exc:", lines[i])), None)
    if exc is None:
        raise LookupError("v2 P10c: cannot find the `except ... _rec_exc` line above the end marker")
    ind = re.match(r"[ \t]*", lines[exc]).group(0)
    t = next((i for i in range(exc - 1, max(exc - 80, -1), -1)
              if re.fullmatch(rf"{ind}try:\s*", lines[i])), None)
    if t is None:
        raise LookupError("v2 P10c: cannot find the matching `try:` for the reconstruction block")
    if "algebraic_reconstruction" not in "".join(lines[t:e + 1]):
        raise LookupError("v2 P10c: located block does not set the algebraic_reconstruction source; refusing")
    new = (f"{ind}# {P10}c: removed. This branch FABRICATED y_pred from the reported R^2 plus noise and\n"
           f"{ind}# then re-scored it as if it were the LLM's output. Without real predictions the row keeps\n"
           f"{ind}# its reported values and the NN correction is skipped (see the y_pred source log below).\n"
           f'{ind}self._log("y_pred unavailable: synthetic reconstruction disabled (Phase 1)")\n')
    return "".join(lines[:t]) + new + "".join(lines[e + 1:])


# d) lines ~2773: same rmse-algebra R^2 as (a), in the HybridSystemLLMNN adapter
_V2D_RE = re.compile(
    r"^([ \t]*)elif r2v == 0\.0 and np\.isfinite\(rmse\) and rmse >= 0:\n"
    r"(?:[^\n]*\n)*?"
    r"[ \t]*r2v = float\(1\.0 - \(rmse \*\* 2 \* len\(y\)\) / ss_tot\)\n", re.M)


def _v2d_ok(s):
    return f"{P10}d" in s


def _v2d_apply(s: str) -> str:
    def repl(m):
        i = m.group(1)
        return (f"{i}elif r2v == 0.0:\n"
                f"{i}    # {P10}d: rmse-algebra R^2 removed (absolute tolerance returned 1.0 on a constant\n"
                f"{i}    # target). Without y_pred the reported value is unverifiable: keep it, say so.\n"
                f'{i}    self._log("r2==0.0 with no y_pred: unverifiable, kept as reported")\n')
    s, n = _V2D_RE.subn(repl, s)
    if n != 1:
        raise LookupError(f"v2 P10d: rmse-algebra branch matched {n}x (expected 1). "
                          "Code around it (paste this):\n" + _ctx(F_V2, r"r2v == 0\.0"))
    return s


def _for_pca(fn, s):
    """Run a v2 patch on the pca benchmark (same code; F_V2 is only used for error context)."""
    global F_V2
    old, F_V2 = F_V2, F_PCA
    try:
        return fn(s)
    finally:
        F_V2 = old


PATCHES = [
    ("P1 metrics self-tests / >= / _REL_EPS", F_METRICS, _metrics_ok, _metrics_apply),
    ("P2 v50_2 _r2_np -> r2_checked", F_V50, _v50_r2_ok, _v50_r2_apply),
    ("P6 v50_2 provenance", F_V50, _v50_prov_ok, _v50_prov_apply),
    ("P3 baseline evaluator -> r2_checked", F_BASE, _base_r2_ok, _base_r2_apply),
    ("P9 M4 private ss_tot R2 -> r2_checked", F_M4, _m4_ok, _m4_apply),
    ("P6 baseline provenance", F_BASE, _base_prov_ok, _base_prov_apply),
    ("P5+P7 noise-sweep catastrophic + flags", F_SWEEP, _sweep_ok, _sweep_apply),
    ("P7 v2 protocol block: sign-flip state", F_V2, _v2_ok, _v2_apply),
    ("P10a v2 rmse-algebra R2 fallback removed", F_V2, _v2a_ok, _v2a_apply),
    ("P10b v2 NN-correction scoring -> r2_checked", F_V2, _v2b_ok, _v2b_apply),
    ("P11 pca NN-correction scoring -> r2_checked", F_PCA, _v2b_ok, lambda s: _v2b_apply(s, F_PCA)),
    ("P10c v2 no synthetic y_pred reconstruction", F_V2, _v2c_ok, _v2c_apply),
    ("P10d v2 adapter rmse-algebra R2 removed", F_V2, _v2d_ok, _v2d_apply),
    ("P11a pca rmse-algebra R2 fallback removed", F_PCA, _v2a_ok, lambda s: _for_pca(_v2a_apply, s)),
    ("P11c pca no synthetic y_pred reconstruction", F_PCA, _v2c_ok, lambda s: _for_pca(_v2c_apply, s)),
    ("P11d pca adapter rmse-algebra R2 removed", F_PCA, _v2d_ok, lambda s: _for_pca(_v2d_apply, s)),
]

# --------------------------------------------------------------------------- P4 failed rows
_ZERO = re.compile(r"""((?:["']r2["']\s*:\s*)|(?:\br2\s*=\s*))0\.0(?![\d.eE])""")
_FAIL_CTX = re.compile(r"""["']success["']\s*:\s*False|success\s*=\s*False|["']error["']\s*:|\berror\s*=""")
WINDOW = 8


def failed_row_hits(src: str) -> list[int]:
    """0-based line indexes with ``r2: 0.0`` inside a failure context."""
    lines = src.splitlines()
    out = []
    for i, ln in enumerate(lines):
        if _ZERO.search(ln):
            ctx = lines[max(0, i - WINDOW): i + WINDOW + 1]
            if any(_FAIL_CTX.search(c) for c in ctx):
                out.append(i)
    return out


def failed_row_files() -> list[pathlib.Path]:
    seen: dict[pathlib.Path, None] = {}
    for g in FAILED_ROW_GLOBS:
        for p in sorted(PKG.glob(g)):
            if "tests" not in p.parts and p.suffix == ".py":
                seen[p] = None
    return list(seen)


def failed_row_apply(src: str) -> str:
    lines = src.splitlines(keepends=True)
    for i in failed_row_hits(src):
        lines[i] = _ZERO.sub(lambda m: m.group(1) + 'float("-inf")', lines[i])
        if MARK not in lines[i]:
            lines[i] = lines[i].rstrip("\n") + f"  # {MARK}: failure, not a score\n"
    return "".join(lines)


# --------------------------------------------------------------------------- tests (P8)
TEST_SRC = '''"""Phase 1 closure regression suite (generated by scripts/close_phase1.py).

Covers: canonical R^2 edge cases, metrics.py self-consistency, one catastrophic /
recovery comparison rule, no ``r2 = 0.0`` on failed rows, per-row provenance.
"""
import ast
import math
import pathlib
import re
import subprocess
import sys

import numpy as np
import pytest

from hypatiax.core import metrics
from hypatiax.core.r2_canonical import r2_checked

ROOT = pathlib.Path(__file__).resolve().parents[3]
PKG = ROOT / "hypatiax"
RNG = np.random.default_rng(0)


# ------------------------------------------------------------- R^2 edge cases
def test_constant_target_is_nan_never_one_or_zero():
    assert math.isnan(metrics.compute_r2([5, 5, 5], [5, 5, 5]))
    assert math.isnan(metrics.compute_r2([5, 5, 5], [5, 5, 6]))
    assert r2_checked([5, 5, 5], [5, 5, 5])[1] == "degenerate_target"


def test_nonfinite_prediction_is_minus_inf():
    assert metrics.compute_r2([1, 2, 3], [1, float("nan"), 3]) == float("-inf")
    assert metrics.compute_r2([1, 2, 3], [1, float("inf"), 3]) == float("-inf")


def test_nonfinite_target_raises():
    with pytest.raises(ValueError):
        metrics.compute_r2([1, float("nan")], [1, 2])


@pytest.mark.parametrize("scale", [1e-23, 1e-19, 1e-11, 1e-6, 1.0, 1e6])
def test_tiny_and_large_scale_targets_are_scored(scale):
    y = np.linspace(1.0, 2.0, 50) * scale
    assert r2_checked(y, y)[0] == pytest.approx(1.0)
    assert r2_checked(y, y * 1.5)[0] < 0.99      # a wrong model never reads as 1.0


def test_offset_target_is_scored_on_spread_not_offset():
    y = 1e6 + RNG.normal(size=200)
    val, status = r2_checked(y, np.full_like(y, 1e6))     # constant guess at the offset
    assert status == "ok" and val < 0.01                  # old guard returned 1.0 here


def test_near_constant_target_scored_when_spread_is_real():
    y = 1.0 + 1e-6 * np.arange(100)
    assert r2_checked(y, y)[0] == pytest.approx(1.0)
    assert r2_checked(y, np.full_like(y, y.mean()))[0] == pytest.approx(0.0, abs=1e-9)


def test_matches_sklearn_when_available():
    skm = pytest.importorskip("sklearn.metrics")
    yt = RNG.normal(size=200)
    yp = yt + RNG.normal(scale=0.1, size=200)
    assert metrics.compute_r2(yt, yp) == pytest.approx(skm.r2_score(yt, yp), abs=1e-10)


# ------------------------------------------------------------- metrics.py self-consistency
def test_metrics_module_selftest_passes():
    r = subprocess.run([sys.executable, "-m", "hypatiax.core.metrics"], capture_output=True,
                       text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


def test_metrics_main_asserts_do_not_contradict_doctests():
    src = (PKG / "core/metrics.py").read_text()
    assert "== 1.0\\n    assert compute_r2([5, 5, 5], [5, 5, 6]) == 0.0" not in src
    assert "_REL_EPS" not in src


# ------------------------------------------------------------- one comparison rule
def test_recovery_and_near_perfect_use_the_same_rule():
    for v in (0.99, 0.9899999, 1.0, float("nan"), float("-inf")):
        assert metrics.is_recovered(v) == (metrics.compute_near_perfect_rate([v], 0.99) == 1.0)


def test_catastrophic_counts_nan_and_minus_inf():
    assert metrics.compute_catastrophic_rate([0.9, float("nan"), float("-inf"), 0.5]) == 0.5


def test_sweep_uses_the_metrics_catastrophic_threshold():
    src = (PKG / "experiments/benchmarks/run_noise_sweep_benchmark.py").read_text()
    assert "CATASTROPHIC_THRESHOLD as _CATASTROPHIC_R2_THRESHOLD" in src
    assert "_CATASTROPHIC_R2_THRESHOLD: float = 0.90" not in src


# ------------------------------------------------------------- failed rows
_ZERO = re.compile(r"""((?:["']r2["']\\s*:\\s*)|(?:\\br2\\s*=\\s*))0\\.0(?![\\d.eE])""")
_FAIL = re.compile(r"""["']success["']\\s*:\\s*False|success\\s*=\\s*False|["']error["']\\s*:|\\berror\\s*=""")


def _scan_files():
    pats = ["tools/symbolic/*.py", "core/generation/**/*.py",
            "experiments/benchmarks/run_comparative_suite_benchmark_*.py"]
    for g in pats:
        for p in sorted(PKG.glob(g)):
            if "tests" not in p.parts:
                yield p


def test_no_failed_row_reports_r2_zero():
    bad = []
    for p in _scan_files():
        lines = p.read_text().splitlines()
        for i, ln in enumerate(lines):
            if _ZERO.search(ln) and any(_FAIL.search(c) for c in lines[max(0, i - 8): i + 9]):
                bad.append(f"{p.relative_to(ROOT)}:{i + 1}")
    assert not bad, "failed rows must be -inf/NaN, not 0.0:\\n  " + "\\n  ".join(bad)


# ------------------------------------------------------------- provenance
def _pure_llm_dicts():
    tree = ast.parse((PKG / "core/base_pure_llm/baseline_pure_llm_defi_discovery.py").read_text())
    for n in ast.walk(tree):
        if isinstance(n, ast.Dict):
            keys = {k.value: v for k, v in zip(n.keys, n.values)
                    if isinstance(k, ast.Constant) and isinstance(k.value, str)}
            if isinstance(keys.get("method"), ast.Constant) and keys["method"].value == "pure_llm":
                yield keys


def test_every_pure_llm_row_logs_llm_called_and_generation_path():
    rows = list(_pure_llm_dicts())
    assert len(rows) >= 2                                   # success + error rows at least
    for keys in rows:
        assert "llm_called" in keys, "PureLLM row without llm_called"
        assert "generation_path" in keys, "PureLLM row without generation_path"


def test_bypass_kind_is_not_a_bare_literal_in_v50_success_row():
    tree = ast.parse((PKG / "tools/symbolic/hybrid_system_v50_2.py").read_text())
    for d in ast.walk(tree):
        if isinstance(d, ast.Dict):
            k = {x.value: v for x, v in zip(d.keys, d.values) if isinstance(x, ast.Constant) and isinstance(x.value, str)}
            if "bypass_kind" in k and "llm_called" in k and not (
                    isinstance(k["llm_called"], ast.Constant) and k["llm_called"].value is False):
                assert not isinstance(k["bypass_kind"], ast.Constant), "success row has a literal bypass_kind"
                assert "generation_path" in k


def test_v50_r2_np_delegates_to_canonical():
    src = (PKG / "tools/symbolic/hybrid_system_v50_2.py").read_text()
    start = src.index("def _r2_np")
    body = src[start: src.index("\\ndef ", start + 5)]
    assert "r2_checked" in body and "ss_tot" not in body


def test_baseline_evaluator_delegates_to_canonical():
    src = (PKG / "core/base_pure_llm/baseline_pure_llm_defi_discovery.py").read_text()
    assert "PHASE1-FIX-P3b" in src and "_r2_checked(y_true, y_pred)" in src


def test_sweep_records_flag_state():
    src = (PKG / "experiments/benchmarks/run_noise_sweep_benchmark.py").read_text()
    assert \'agg["run_flags"]\' in src and "_RUN_FLAGS = enforce()" in src


def test_v2_has_no_private_r2_or_fabricated_ypred():
    src = (PKG / "experiments/benchmarks/run_comparative_suite_benchmark_v2.py").read_text()
    names = {n.id for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Name)}
    assert "ss_tot" not in names, "v2 still re-implements R^2"
    assert '_ypred_source = "algebraic_reconstruction"' not in src, "v2 fabricates y_pred"


def test_v2_safe_r2_delegates_to_canonical():
    src = (PKG / "experiments/benchmarks/run_comparative_suite_benchmark_v2.py").read_text()
    start = src.index("def _safe_r2")
    assert "r2_canonical" in src[start: start + 1500]


def test_hardcoded_bypass_function_is_never_called():
    src = (PKG / "core/base_pure_llm/baseline_pure_llm_defi_discovery.py").read_text()
    calls = [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Call)
             and getattr(n.func, "attr", getattr(n.func, "id", "")) == "_try_hardcoded_formula"]
    assert not calls, "hardcoded-formula bypass is being called"

# ------------------------------------------------------------- repo hygiene / pca / legacy scorers
def test_every_package_file_parses_and_has_no_conflict_markers():
    bad = []
    for p in PKG.rglob("*.py"):
        t = p.read_text(encoding="utf-8", errors="replace")
        if re.search(r"^(<<<<<<< |>>>>>>> )", t, re.M):
            bad.append(f"{p.relative_to(ROOT)}: conflict marker")
        try:
            ast.parse(t)
        except SyntaxError as e:
            bad.append(f"{p.relative_to(ROOT)}: {e}")
    assert not bad, "\\n".join(bad)


def test_pca_benchmark_has_no_private_r2_or_fabricated_ypred():
    src = (PKG / "experiments/benchmarks/run_comparative_suite_benchmark_pca.py").read_text()
    names = {n.id for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Name)}
    assert not {"ss_tot", "_ss_tot"} & names, "pca re-implements R^2"
    assert '_ypred_source = "algebraic_reconstruction"' not in src, "pca fabricates y_pred"


@pytest.mark.parametrize("rel", [
    "tools/symbolic/symbolic_engine.py",
    "experiments/benchmarks/exp3_nguyen12_consolidated.py",
    "core/training/baseline_neural_network_defi_improved.py",
])
def test_legacy_scorers_use_canonical_r2(rel):
    src = (PKG / rel).read_text()
    names = {n.id for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Name)}
    assert "ss_tot" not in names and "r2_canonical" in src

'''


# --------------------------------------------------------------------------- audit
CHECKLIST = {
    1: "Per-row provenance (llm_called, path, formula)",
    2: "Disable hardcoded-formula bypass",
    3: "M4 missing formula output",
    4: "Evaluator guard and R2 policy",
    5: "Noise-sweep check",
    6: "Quarantine of unresolved results",
}
PATCH_ITEM = {"P1": 4, "P2": 4, "P3": 4, "P6": 1, "P5+P7": 4, "P7": 4, "P9": 3,
              "P10a": 4, "P10b": 4, "P10c": 1, "P10d": 4, "P11": 4, "P11a": 4, "P11c": 1, "P11d": 4}
Row = tuple  # (item, check, status, detail); status: PASS | FAIL | MANUAL | NOEVID


def safe_read(p: pathlib.Path):
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def find_py(name: str):
    hits = [p for p in PKG.rglob(name) if "tests" not in p.parts]
    return sorted(hits)[0] if hits else None


def audit(run_bypass_audit: bool = False) -> list[Row]:
    rows: list[Row] = []

    def add(item, name, status, detail):
        rows.append((item, name, status, detail))

    def chk(item, name, ok, detail):
        add(item, name, "PASS" if ok else "FAIL", detail)

    # ---- automatable patches (1, 4)
    for pid, path, ok, _ in PATCHES:
        item = PATCH_ITEM.get(pid.split()[0], 4)
        src = safe_read(path)
        if src is None:
            add(item, pid, "FAIL", f"{rel(path)} not found")
            continue
        try:
            chk(item, pid, ok(src), rel(path))
        except Exception as e:  # noqa: BLE001
            add(item, pid, "FAIL", f"predicate error: {e}")

    hits = {}
    for p in failed_row_files():
        h = failed_row_hits(read(p))
        if h:
            hits[rel(p)] = [i + 1 for i in h]
    chk(4, "P4 failed rows report r2 != 0.0", not hits,
        "; ".join(f"{k}:{v}" for k, v in hits.items()) or "none found")
    chk(4, "P8 regression tests present", F_TESTS.is_file(), rel(F_TESTS))

    if F_METRICS.is_file():
        r = subprocess.run([sys.executable, "-m", "hypatiax.core.metrics"],
                           capture_output=True, text=True, cwd=ROOT)
        chk(4, "metrics self-test (python -m hypatiax.core.metrics)", r.returncode == 0,
            (r.stderr.strip().splitlines() or ["ok"])[-1])

    try:
        left = json.loads(read(BASELINE_JSON))["files"]
        still = [f for f in left if (ROOT / f).is_file() and has_ss_tot(read(ROOT / f))]
        chk(4, "R2 re-implementations (ss_tot) remaining", not still,
            f"{len(still)} legacy file(s): " + ", ".join(pathlib.Path(f).name for f in still))
    except Exception as e:  # noqa: BLE001
        add(4, "R2 re-implementations (ss_tot) remaining", "MANUAL", f"baseline unreadable: {e}")

    # Supplement A Listing 8: look for the old absolute guard in docs
    cand = []
    for p in ROOT.rglob("*"):
        if p.suffix in {".tex", ".md"} and ".git" not in p.parts and p.is_file():
            t = safe_read(p) or ""
            if re.search(r"ss.{0,3}tot", t) and re.search(r"1e-10|10\^\{-10\}", t):
                cand.append(rel(p))
    add(4, "Supplement A Listing 8 guard", "MANUAL",
        ("old-guard text in: " + ", ".join(cand[:6]) + " -> compare with r2_checked") if cand
        else "no .tex/.md mentions the absolute guard; Listing 8 not in repo, compare manually")

    # ---- 1: provenance in EHSDeFi
    ehs = find_py("hybrid_ensemble_system_defi_domain.py")
    if ehs is None:
        add(1, "EHSDeFi provenance fields", "MANUAL", "hybrid_ensemble_system_defi_domain.py not found")
    else:
        t = read(ehs)
        chk(1, "EHSDeFi provenance fields", "llm_called" in t and "generation_path" in t, rel(ehs))

    # ---- 2: bypass
    base = safe_read(F_BASE)
    if base is None:
        add(2, "_try_hardcoded_formula never called", "MANUAL", f"{rel(F_BASE)} not found")
    else:
        calls = [n.lineno for n in ast.walk(ast.parse(base)) if isinstance(n, ast.Call)
                 and getattr(n.func, "attr", getattr(n.func, "id", "")) == "_try_hardcoded_formula"]
        chk(2, "_try_hardcoded_formula never called", not calls,
            f"called at line(s) {calls}" if calls else rel(F_BASE))
    ba = ROOT / "scripts/bypass_audit.py"
    if not ba.is_file():
        add(2, "scripts/bypass_audit.py", "MANUAL", "script not found")
    elif run_bypass_audit:
        r = subprocess.run([sys.executable, str(ba)], capture_output=True, text=True, cwd=ROOT)
        chk(2, "scripts/bypass_audit.py exits 0", r.returncode == 0,
            (r.stdout.strip().splitlines() or r.stderr.strip().splitlines() or ["no output"])[-1])
    else:
        add(2, "scripts/bypass_audit.py", "MANUAL", "present; re-run with --run-bypass-audit")
    csv_ = ROOT / "bypass_audit.csv"
    if not csv_.is_file():
        add(2, "bypass_audit.csv per-task probe", "MANUAL", "bypass_audit.csv missing: run scripts/bypass_audit.py")
    else:
        import csv as _csv
        _rows = list(_csv.DictReader(csv_.open(encoding="utf-8", errors="replace")))
        _hit = [r for r in _rows if str(r.get("bypassed_when_switch_off")).lower() == "true"]
        chk(2, "bypass_audit.csv: no task is bypassed", not _hit,
            f"{len(_rows)} tasks probed (these are tasks, not result rows), {len(_hit)} bypassed")

    # ---- 3: M4
    m4 = find_py("hybrid_system_llm_nn_all_domains.py")
    if m4 is None:
        add(3, "M4 engine (HybridSystemLLMNN) static check", "MANUAL", "hybrid_system_llm_nn_all_domains.py not found")
    else:
        t = read(m4)
        chk(3, "M4 engine has no private ss_tot R2", not has_ss_tot(t), rel(m4))
        chk(3, "M4 engine logs llm_called", "llm_called" in t, rel(m4))
    _mk = ROOT / "scripts/mark_m4_unverified.py"
    if _mk.is_file():
        import importlib.util as _ilu2
        _sp2 = _ilu2.spec_from_file_location("mk", _mk); _m2 = _ilu2.module_from_spec(_sp2); _sp2.loader.exec_module(_m2)
        _un = _m2.unflagged()
        chk(3, "stored M4 rows without a formula are flagged or rerun", not _un,
            f"{sum(n for _, n in _un)} unflagged row(s) in {len(_un)} file(s): run scripts/mark_m4_unverified.py (dry run), then --apply or rerun M4"
            if _un else "none unflagged")
    else:
        add(3, "M4 stored output", "MANUAL", "rerun HybridSystemLLMNN or downgrade stored M4 results to exploratory")

    # ---- 5: noise sweep
    chk(5, "enforce_flags.py present", find_py("enforce_flags.py") is not None,
        "hypatiax/core/enforce_flags.py")
    v2 = safe_read(F_V2)
    if v2 is None:
        add(5, "Noise injection code (read it)", "MANUAL", f"{rel(F_V2)} not found")
    else:
        chk(5, "noise is added to the scored target before the split (static read)",
            "_y = _y + _noise" in v2 and "added to ALL targets before the train/test split" in v2
            and "_noisy_tests.append((_desc, _X, _y," in v2, rel(F_V2))
    bad = tot = 0
    for p in ROOT.rglob("noise_sweep_*.json"):
        try:
            txt = json.dumps(json.loads(read(p)))
        except Exception:  # noqa: BLE001
            continue
        tot += 1
        if any(int(m.group(1)) > 0 for m in re.finditer(r'"n_above_noise_ceiling":\s*(\d+)', txt)):
            bad += 1
    add(5, "Noise-sweep ceiling audit (stored shards)",
        "MANUAL" if not tot else ("FAIL" if bad else "PASS"),
        f"{tot} shard(s) scanned, {bad} with n_above_noise_ceiling > 0")

    # ---- 5/1: v2 _safe_r2 must be the canonical scorer (and the sign-flip opt-in must default off)
    if v2 is not None:
        sp = function_span(v2, "_safe_r2")
        body = "".join(v2.splitlines(keepends=True)[sp[0] - 1:sp[1]]) if sp else ""
        chk(4, "v2 _safe_r2 delegates to r2_canonical", "r2_canonical" in body, rel(F_V2))
        chk(4, "v2 records enforce() flag state (run_flags) in result files", '"run_flags": dict(_RUN_FLAGS)' in v2, rel(F_V2))
        _ef = safe_read(PKG / "core/enforce_flags.py") or ""
        chk(4, "enforce_flags fails closed on sign-flip", "HYPATIAX_ALLOW_LEGACY" in _ef and "raise RuntimeError" in _ef,
            "HYPATIAX_R2_SIGN_FLIP != off raises unless HYPATIAX_ALLOW_LEGACY=1")

    # ---- repo hygiene: syntax + merge-conflict markers (a file that does not import cannot be audited)
    broken, conflicts, fabricated = [], [], []
    for p in PKG.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        t = safe_read(p) or ""
        if re.search(r"^(<<<<<<< |>>>>>>> )", t, re.M):
            conflicts.append(rel(p))
        try:
            ast.parse(t)
        except SyntaxError:
            broken.append(rel(p))
        if "tests" not in p.parts and '_ypred_source = "algebraic_reconstruction"' in t:
            fabricated.append(rel(p))
    chk(4, "all hypatiax/*.py parse", not broken, ", ".join(broken) or "ok")
    chk(4, "no committed merge-conflict markers", not conflicts, ", ".join(conflicts) or "none")
    chk(1, "no code path fabricates y_pred (algebraic_reconstruction)", not fabricated,
        ", ".join(fabricated) or "none")

    # ---- repo hygiene: syntax + merge-conflict markers (a file that does not import cannot be audited)
    broken, conflicts, fabricated = [], [], []
    for p in PKG.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        t = safe_read(p) or ""
        if re.search(r"^(<<<<<<< |>>>>>>> )", t, re.M):
            conflicts.append(rel(p))
        try:
            ast.parse(t)
        except SyntaxError:
            broken.append(rel(p))
        if "tests" not in p.parts and '_ypred_source = "algebraic_reconstruction"' in t:
            fabricated.append(rel(p))
    chk(4, "all hypatiax/*.py parse", not broken, ", ".join(broken) or "ok")
    chk(4, "no committed merge-conflict markers", not conflicts, ", ".join(conflicts) or "none")
    chk(1, "no code path fabricates y_pred (algebraic_reconstruction)", not fabricated,
        ", ".join(fabricated) or "none")

    # ---- 6: stored rows produced by the removed fabricated-y_pred path
    _skip = {".git", ".venv", "venv", "node_modules", "site-packages", "__pycache__", "AUDIT"}  # AUDIT/ names the check itself
    syn = []
    for p in ROOT.rglob("*"):
        if (p.suffix in {".json", ".csv", ".jsonl"} and p.is_file() and not (_skip & set(p.parts))
                and p.stat().st_size < 64_000_000 and "algebraic_reconstruction" in (safe_read(p) or "")):
            syn.append(rel(p))
    add(6, "Stored rows with fabricated y_pred (algebraic_reconstruction)",
        "PASS" if not syn else "MANUAL",
        "none found" if not syn else f"{len(syn)} file(s) -> list in the quarantine manifest: "
        + ", ".join(syn[:5]) + (" ..." if len(syn) > 5 else ""))

    # ---- 6: stored results still carrying bypass contamination
    _qc = ROOT / "scripts/quarantine_contaminated.py"
    if _qc.is_file():
        import importlib.util as _ilu
        _sp = _ilu.spec_from_file_location("qc", _qc); _m = _ilu.module_from_spec(_sp); _sp.loader.exec_module(_m)
        _left = _m.scan()
        chk(6, "contaminated result files outside quarantine", not _left,
            f"{len(_left)} file(s): run scripts/quarantine_contaminated.py (dry run), then --apply or regenerate"
            if _left else "none")

    # ---- 6: quarantine
    adir = ROOT / "AUDIT"
    if not adir.is_dir():
        add(6, "AUDIT/ directory", "NOEVID", "AUDIT/ not found in repo")
    else:
        q = [p for p in adir.rglob("*") if "quarantine" in p.name.lower()]
        files = sum(1 for p in adir.rglob("*") if p.is_file())
        add(6, "AUDIT/ quarantine manifest", "PASS" if q else "MANUAL",
            f"{files} file(s); manifest: {rel(q[0])}" if q else f"{files} file(s), no *quarantine* manifest: review and create one")
    return rows


def rollup(rows: list[Row]) -> dict[int, str]:
    """Map each checklist row to the spreadsheet's status vocabulary."""
    out = {}
    for item in CHECKLIST:
        st = [r[2] for r in rows if r[0] == item]
        if "FAIL" in st:
            out[item] = "Partial" if "PASS" in st else "Open"
        elif "NOEVID" in st and "PASS" not in st:
            out[item] = "Not evidenced"
        elif "MANUAL" in st or "NOEVID" in st:
            out[item] = "Unverified"
        else:
            out[item] = "Closed" if st else "Not evidenced"
    return out


# --------------------------------------------------------------------------- main
def show(rows: list[Row]) -> int:
    w = max(len(r[1]) for r in rows)
    roll = rollup(rows)
    for item, title in CHECKLIST.items():
        print(f"\n[{item}] {title}  ->  {roll[item]}")
        for it, name, status, detail in rows:
            if it == item:
                print(f"    [{status:6}] {name:<{w}}  {detail}")
    n_fail = sum(1 for r in rows if r[2] == "FAIL")
    n_man = sum(1 for r in rows if r[2] in ("MANUAL", "NOEVID"))
    n_closed = sum(1 for v in roll.values() if v == "Closed")
    print(f"\n  {n_fail} FAIL, {n_man} MANUAL  |  checklist rows closed: {n_closed}/{len(CHECKLIST)}  ->  Phase 1 is "
          f"{'NOT closed' if n_fail else 'closed for automatable items' + (' (manual items remain)' if n_man else '')}")
    return n_fail


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="show patches (dry run unless --write)")
    ap.add_argument("--write", action="store_true", help="with --apply: write files")
    ap.add_argument("--json", metavar="PATH", help="write the audit result as JSON")
    ap.add_argument("--run-bypass-audit", action="store_true", help="also execute scripts/bypass_audit.py")
    a = ap.parse_args()

    if not a.apply:
        print(f"Phase 1 audit (read-only)  root={ROOT}")
        rows = audit(a.run_bypass_audit)
        n_fail = show(rows)
        if a.json:
            pathlib.Path(a.json).parent.mkdir(parents=True, exist_ok=True)
            pathlib.Path(a.json).write_text(json.dumps({
                "rollup": {CHECKLIST[k]: v for k, v in rollup(rows).items()},
                "checks": [dict(item=i, check=n, status=s, detail=d) for i, n, s, d in rows],
            }, indent=2), encoding="utf-8")
            print(f"  wrote {a.json}")
        return 1 if n_fail else 0

    changed: dict[pathlib.Path, str] = {}
    errors: list[str] = []
    for pid, path, ok, fn in PATCHES:
        try:
            src = changed.get(path) or read(path)
            if ok(src):
                print(f"  skip   {pid}  (already fixed)")
                continue
            new = fn(src)
            ast.parse(new)
            changed[path] = new
            print(f"  patch  {pid}")
        except Exception as e:  # noqa: BLE001
            errors.append(f"{pid}: {type(e).__name__}: {e}")
            print(f"  ERROR  {pid}: {e}")
    for p in failed_row_files():
        src = changed.get(p, read(p))
        if failed_row_hits(src):
            new = failed_row_apply(src)
            ast.parse(new)
            changed[p] = new
            print(f"  patch  P4 failed rows -> -inf  {rel(p)}  ({len(failed_row_hits(src))} line(s))")

    for p, new in changed.items():
        diff = difflib.unified_diff(read(p).splitlines(), new.splitlines(), rel(p), rel(p), lineterm="", n=1)
        print("\n".join(diff))

    if errors:
        print("\nPatches that could not be applied (working tree has drifted, fix by hand):")
        print("  " + "\n  ".join(errors))

    if not a.write:
        print(f"\nDry run: {len(changed)} file(s) would change. Re-run with --apply --write.")
        return 2 if errors else 0

    for p, new in changed.items():
        p.write_text(new, encoding="utf-8")
    if not F_TESTS.is_file() or read(F_TESTS) != TEST_SRC:
        F_TESTS.parent.mkdir(parents=True, exist_ok=True)
        F_TESTS.write_text(TEST_SRC, encoding="utf-8")
        print(f"  wrote  {rel(F_TESTS)}")
    mig = ROOT / "scripts/migrate_r2_repro.py"
    if mig.is_file():  # shrink the ratchet list now that copies are gone
        subprocess.run([sys.executable, str(mig), "--write-baseline"], cwd=ROOT, check=False)
    print(f"\nWrote {len(changed)} file(s). Now run:\n  pytest hypatiax/experiments/tests -q\n"
          f"  python scripts/close_phase1.py")
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
