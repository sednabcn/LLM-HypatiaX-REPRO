#!/usr/bin/env python3
"""Anchor-based hardening of baseline_pure_llm_defi_discovery.py.

Edits the file by TEXT ANCHORS (not line numbers), tolerates CRLF, never
guesses: an edit whose anchors are not found exactly once is SKIPPED and
reported. Default is a dry run; pass --write to save (a .bak copy is kept).

  python3 apply_baseline_hardening.py hypatiax/core/base_pure_llm/baseline_pure_llm_defi_discovery.py
  python3 apply_baseline_hardening.py <file> --write
"""
import shutil, sys

path = sys.argv[1]
write = "--write" in sys.argv
raw = open(path, "rb").read().decode("utf-8")
crlf = "\r\n" in raw
t = raw.replace("\r\n", "\n")
report = []

def once(s, needle, what):
    n = s.count(needle)
    if n != 1:
        report.append(("SKIP", what, f"anchor found {n}x (need exactly 1)"))
        return -1
    return s.index(needle)

# 1. module docstring note (cosmetic)
a = "  FIX 4 — _generate_specialized_prompt() now warns when a use_specialized\n           case reaches the final return \"\" without matching any branch,\n           preventing silent degradation to the standard prompt.\n\"\"\"\n"
i = once(t, a, "docstring note")
if i >= 0:
    note = ("\nAUDIT PATCH (release hardening):\n"
            "  * Equation-specific hints (Nernst/Clausius/Fourier/Gaussian templates), the\n"
            "    specialised formula prompts (liquidation, Kelly, ...), the data-derived\n"
            "    OLS/stats parameter hints and the generic Gaussian normalisation hint are\n"
            "    DELETED, not gated: a deleted hint cannot be re-enabled by a flag typo.\n"
            "    The FIX 1-4 notes above describe code that no longer exists.\n"
            "  * R^2 is scored by core.r2_canonical.r2_scored (single policy); the local\n"
            "    ss_tot/_is_const copy is removed. Each row records r2_status and whether\n"
            "    the legacy sign-flip credit (HYPATIAX_R2_SIGN_FLIP) was active.\n\"\"\"\n")
    t = t[:i] + a[:-4] + note + t[i+len(a):]
    report.append(("OK", "docstring note", ""))

# 2. import
imp = "from hypatiax.protocols.experiment_protocol_defi import DeFiExperimentProtocol\n"
new_imp = "from hypatiax.core.r2_canonical import r2_scored, sign_flip_enabled\n"
if new_imp in t:
    report.append(("OK", "import r2_scored", "already present"))
else:
    i = once(t, imp, "import r2_scored")
    if i >= 0:
        t = t[:i+len(imp)] + new_imp + t[i+len(imp):]
        report.append(("OK", "import r2_scored", ""))

# 3. generate_formula body: hints/specialised/OLS-stats -> single generic prompt
g = t.find("    def generate_formula(")
s3 = "        desc_lower = description.lower()\n"
e3 = "        # Provenance is computed BEFORE the API call"
si = t.find(s3, g) if g >= 0 else -1
ei = t.find(e3, si) if si >= 0 else -1
if si < 0 or ei < 0 or t.count(e3) != 1:
    report.append(("SKIP", "generate_formula body", "start/end anchor missing"))
else:
    new_body = (
        "        # Equation-specific prompt hints, specialised prompts, data-derived\n"
        "        # (OLS/stats) parameter hints and the hardcoded-formula short-circuit are\n"
        "        # DELETED. Every task gets the same generic prompt built from the task\n"
        "        # description, variable names and the task-spec constants. X and y are\n"
        "        # accepted only for call-site compatibility and are never used here.\n"
        "        metadata = dict(metadata or {})\n"
        "        disable_hc = _flag(\"HYPATIAX_DISABLE_HARDCODED\")\n"
        "        disable_hints = _flag(\"HYPATIAX_DISABLE_PROMPT_HINTS\")\n"
        "        metadata.pop(\"_x_stats\", None)   # stats leaked by older callers are never used\n"
        "        metadata.pop(\"_y_stats\", None)\n"
        "        use_specialized = False\n"
        "        prompt = self._generate_standard_prompt(\n"
        "            description, domain, variable_names, metadata\n"
        "        )\n\n")
    t = t[:si] + new_body + t[ei:]
    report.append(("OK", "generate_formula body", ""))
    old_doc = ("            X: Optional feature matrix (n_samples, n_features).  When provided\n"
               "               for biology/chemistry equations, analytical OLS parameters are\n"
               "               computed and embedded in the returned formula — no LLM call.\n"
               "            y: Optional target vector (n_samples,).  Required when X is given.")
    new_doc = ("            X, y: Accepted for call-site compatibility only. They are NOT used:\n"
               "               no data-derived parameters are fitted or embedded in the prompt,\n"
               "               and no LLM-free formula is ever returned.")
    if t.count(old_doc) == 1:
        t = t.replace(old_doc, new_doc)

# 4. specialised prompt method -> stub
s4 = "    def _generate_specialized_prompt("
e4 = "    def _generate_standard_prompt("
if t.count(s4) == 1 and t.count(e4) == 1 and t.index(s4) < t.index(e4):
    stub = ('    def _generate_specialized_prompt(\n'
            '        self, description: str, domain: str, variable_names: list[str], metadata: dict\n'
            '    ) -> str:\n'
            '        """Removed. The specialised prompts embedded the exact target formula and\n'
            '        Python code (liquidation, leverage, collateral, Kelly, capital efficiency,\n'
            '        ES) or data-fitted parameters (logistic, Michaelis-Menten, allometric,\n'
            '        Arrhenius), i.e. ground truth in the prompt. Kept as a stub returning ""\n'
            '        only so existing callers/audit scripts do not break. Do NOT add branches."""\n'
            '        return ""\n\n')
    t = t[:t.index(s4)] + stub + t[t.index(e4):]
    report.append(("OK", "specialised prompt -> stub", ""))
else:
    report.append(("SKIP", "specialised prompt -> stub", "anchors missing/ambiguous"))

# 4b. constants comment (documentation only)
c = '                constants_info += f"\\n  \u2022 {const_name} = {const_value}"\n'
ci = t.find(c)
if t.count(c) == 1 and "input parity" not in t:
    t = t[:ci+len(c)] + ("\n        # Constants are part of the task spec and are sent to EVERY system alike\n"
                         "        # (input parity); they are recorded verbatim in the row (prompt_constants).\n") + t[ci+len(c):]
    report.append(("OK", "constants comment", ""))

# 5. standard prompt: delete hint block, _norm_hint
s5 = "        # ── Domain-specific formula hints"
e5 = "            _norm_hint = \"\"\n"
si = t.find(s5)
ei = t.find(e5, si) if si >= 0 else -1
if t.count(s5) == 1 and ei >= 0:
    t = t[:si] + t[ei+len(e5):].lstrip("\n").join(["", ""]) if False else t[:si].rstrip("\n") + "\n\n" + t[ei+len(e5):].lstrip("\n")
    t = t.replace("{constants_info}{domain_hint}", "{constants_info}")
    t = t.replace("work element-wise on numpy arrays{_norm_hint}\"\"\"", "work element-wise on numpy arrays\"\"\"")
    if "{domain_hint}" in t or "_norm_hint" in t:
        report.append(("WARN", "standard prompt", "domain_hint/_norm_hint still referenced - check manually"))
    else:
        report.append(("OK", "standard prompt hints deleted", ""))
else:
    report.append(("SKIP", "standard prompt hints", "anchors missing/ambiguous"))

# 6. non-finite early return -> canonical value/status
old = '                    "r2": float("nan"),\n                    "r2_status": "nonfinite_prediction",'
new = '                    "r2": float("-inf"),\n                    "r2_status": "nonfinite_pred",'
if t.count(old) == 1:
    t = t.replace(old, new); report.append(("OK", "nonfinite early return", ""))
else:
    report.append(("SKIP", "nonfinite early return", f"found {t.count(old)}x"))

# 7. R^2 block -> r2_scored
s7 = "            ss_res = np.sum((y_true - y_pred) ** 2)\n"
e7 = "        except SyntaxError as e:"
si = t.find(s7)
ei = t.find(e7, si) if si >= 0 else -1
if t.count(s7) == 1 and ei >= 0:
    new_r2 = (
        "            # Single scoring policy (core.r2_canonical.r2_scored): relative degenerate\n"
        "            # tolerance, non-finite -> -inf, catastrophic floor, optional legacy\n"
        "            # sign-flip only when HYPATIAX_R2_SIGN_FLIP is set (recorded in the row).\n"
        "            r2_val, _r2_status = r2_scored(y_true, y_pred)\n"
        "            _scored = _r2_status == \"ok\"\n"
        "            result = {\n"
        "                \"mse\": float(mse),\n"
        "                \"mae\": float(mae),\n"
        "                \"rmse\": float(rmse),\n"
        "                \"r2\": float(r2_val),          # nan = degenerate target, -inf = failure\n"
        "                \"r2_status\": _r2_status,\n"
        "                \"r2_sign_flip\": bool(sign_flip_enabled()),\n"
        "                \"success\": _scored,           # anything not scored counts as a failure\n"
        "            }\n"
        "            if not _scored:\n"
        "                result[\"error\"] = f\"R2 not scored: {_r2_status}\"\n"
        "            return result\n\n")
    t = t[:si] + new_r2 + t[ei:]
    report.append(("OK", "R2 -> r2_scored", ""))
else:
    report.append(("SKIP", "R2 -> r2_scored", "anchor missing (already migrated by phase1?)"))

for st, what, why in report:
    print(f"[{st:4}] {what} {why}")
import ast
try:
    ast.parse(t)
except SyntaxError as e:
    print(f"RESULT DOES NOT PARSE ({e}); nothing written"); sys.exit(2)
if write:
    shutil.copy(path, path + ".bak")
    open(path, "wb").write((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))
    print(f"written {path} (backup {path}.bak)")
else:
    print("dry run: nothing written (use --write)")
