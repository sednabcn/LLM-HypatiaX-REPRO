#!/usr/bin/env python3
"""
phase4_close_unified.py - Phase 4 (evaluation and reporting) and Step 5 (M3/M4) closure for HDS v50_2,
together with the static code audit of the Exp-1 ablation package, in one file.

One file, five subcommands:
  close     results closure: reads saved Phase 3 rows and the Phase 2 Pure-LLM rows, runs gates A-K,
            writes machine-readable tables, claim ledger and verdict (exit 0 = CLOSED, 1 = NOT CLOSED,
            2 = input error). It never runs an experiment.
  audit     static code audit (ast + re, stdlib only) of exp1_ablation.py and the files around it:
            gates A0-A8, with severity, file:line, offending line and a fix hint. PASS means "no known
            bad pattern", not "proved correct".
  list      which files the audit would read.
  all       audit, then close; the audit result becomes gate K of the closure. Use this to close Phase 4.
  selftest  runs the audit selftest and the closure selftest.

Pre-specified definitions for `close` (edit ONLY before the first Phase 4 analysis; the file is
committed and its sha256 is written into the output):
  recovered   : status == "ok", value finite, value >= threshold; failed/timed-out/errored rows count
                as NOT recovered (denominator = all attempted cases).
  thresholds  : 0.99 (primary, cross-condition) and 0.999999 (strict near-exact).
  splits      : far = extrap_r2_far (equals the primary r2), medium = extrap_r2_medium, train = train_r2.
  catastrophic: status != "ok", or far value non-finite, or far value < CAT_R2 (0.0).
  r2 deltas   : R2 clipped to [-1, 1] before averaging.
  unit        : the equation (seeds averaged); equation x seed pairs are descriptive only.
  confirmatory: far split at the primary threshold, 3 contrasts (full-P, llm_acceptance-full,
                pysr_prior-full), exact two-sided sign test, Holm over the 3. Everything else is
                exploratory and labelled so.

Closure gates (CLOSED only if every gate is PASS or WARN):
  A inputs and coverage   B provenance of Phase 3 rows   C evaluator pin   D r2 == extrap_r2_far
  E data parity           F Phase 3 closure artefact     G evaluator regression tests (ss_tot guard)
  H power statement       I tree clean
  J M3/M4 decision (decision-report Step 5): CONFIRMED only if the rerun rows (--m3-rows/--m4-rows)
    are auditable (formula on ok rows, generation_path, llm_called, bypass_used False, clean_run True,
    one commit, clean tree); otherwise EXPLORATORY_OR_OMIT (WARN). CONFIRMED means auditable, not favourable.
  K static code audit: PASS = CLOSED, WARN = CLOSED_WITH_CAVEATS, or OPEN with --audit-gate report (the
    default: recorded, not blocking), FAIL = OPEN with --audit-gate block. Not run under `close` (WARN).

Audit gates: A0 coverage, A1 data generation, A2 regime split, A3 metrics, A4 results format,
A5 fairness, A6 proxy metrics, A7 statistics, A8 recall control. Suppress a reviewed finding with
`# audit: ignore[D2]` on or above the line.

Usage
  python phase4_close_unified.py all   --root . --phase3-dir phase3_out --phase3-closure phase3_closure_out/<file> \
        [--m3-rows 'm3/*.jsonl'] [--m4-rows 'm4/*.jsonl'] [--extra-glob 'scripts/phase3_*.py'] [--audit-gate block]
  python phase4_close_unified.py close --phase3-dir phase3_out --phase3-closure phase3_closure_out/<file>
  python phase4_close_unified.py audit --root . [--out phase_ablation_code_audit] [--fail-on HIGH]
  python phase4_close_unified.py list  --root .
  python phase4_close_unified.py selftest

Provenance: sections 1 and 2 are the unchanged logic of phase-ablation.py and phase4_close.py (v2). Edits:
audit selftest/main renamed audit_selftest/(removed), cmd_audit stores LAST_AUDIT; closure num() renamed
fnum(), selftest/main renamed, argument setup split into close_args(), gate K added.
"""
from __future__ import annotations

# ========================================================================================
# SECTION 1 - static code audit (phase-ablation.py)
# ========================================================================================

import argparse
import ast
import json
import math
import re
import sys
import tempfile
import textwrap
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional

SEV = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
GATES = {"A0": "A0_coverage", "A1": "A1_data_generation", "A2": "A2_regime_split", "A3": "A3_metrics",
         "A4": "A4_results_format", "A5": "A5_fairness", "A6": "A6_proxy_metrics",
         "A7": "A7_statistics", "A8": "A8_recall_control"}
LAST_AUDIT = None   # set by cmd_audit so the closure can read the result
MARKERS = ("PHASE_ABLATION_CODE_CLOSED", "PHASE_ABLATION_CODE_CLOSED_WITH_CAVEATS", "PHASE_ABLATION_CODE_OPEN")

# rule -> (gate, title, fix hint)
META: Dict[str, tuple] = {
    "H0": ("A0", "File cannot be parsed", "Fix the syntax error; no AST rule could run on this file."),
    "H1": ("A0", "Primary driver not found", "Pass --primary / --files, or run from the repo root."),
    "H2": ("A0", "Audit rule crashed", "Report this: the rule is skipped for this file."),
    "D1": ("A1", "Unseeded or global RNG", "Use rng = np.random.default_rng(stable_seed(seed, equation)) and pass rng down; "
           "never rely on np.random.* module state."),
    "D2": ("A1", "Seed depends on loop position, hash() or the clock",
           "Derive seeds from (seed, equation NAME) with zlib.crc32, not enumerate/index/hash/time, so that "
           "--equations subsets, reordering and PYTHONHASHSEED cannot change the data."),
    "D3": ("A1", "Data regenerated inside the condition loop",
           "Build Xtr/ytr/blocks once per (equation, seed) before the condition loop and hand the same arrays to every condition."),
    "D4": ("A1", "Noise added to test targets", "Add noise to ytr only: ytr_obs = ytr + rng.normal(...); keep y_test/y_near/y_far noiseless."),
    "D5": ("A1", "Random split in an extrapolation study", "Train on the sampling box, test on blocks strictly beyond its upper edge; "
           "a shuffled split measures interpolation."),
    "D6": ("A1", "Fit/transform uses test or regime data", "Fit scalers, PySR and the LLM prompt on training arrays only."),
    "R1": ("A2", "Regime bounds overlap or are inverted", "Define near/medium/far as disjoint intervals beyond train hi, e.g. "
           "{'near':(0,.5),'medium':(.5,2),'far':(2,9)} in units of the training width."),
    "R2": ("A2", "Regime boundary from data quantiles or sorted slices",
           "Place regimes relative to the TRAINING max/min per variable, not percentiles of pooled data."),
    "R3": ("A2", "Regime metrics copied or computed from mixed arrays",
           "Each regime has its own array; call metrics(y_true[r], pred(X[r])) once per regime."),
    "R4": ("A2", "Correlation-like variable may be extrapolated", "Mark such variables extrap=False and sample them inside the training range in every regime."),
    "M1": ("A3", "Non-canonical or invalid R2", "Import the one canonical R2 (core/r2_canonical.py); squared correlation is not R2."),
    "M2": ("A3", "Unguarded R2 denominator", "Return r2=None with reason='zero_target_variance' when ss_tot <= 1e-12*max(1, sum(y**2))."),
    "M3": ("A3", "Non-finite sentinel or JSON NaN", "Store null + reason; write with json.dumps(clean(row), allow_nan=False)."),
    "M4": ("A3", "No relative RMSE next to R2", "Report rel_rmse = rmse / mean(|y|) beside R2 in every block."),
    "M5": ("A3", "Exception swallowed into data", "Record error=f'{type(e).__name__}: {e}' and EXCLUDE the row; never substitute 0/-inf/NaN."),
    "M6": ("A3", "R2 floored at source", "Store the raw R2 (or null+reason); apply floors (-1, -10) only in the analysis."),
    "F1": ("A4", "Provenance field missing from result rows", "Each row: equation, condition, seed, commit, versions, budget_s, fit_time_s, llm_mode_used."),
    "F2": ("A4", "Per-shard / non-row output", "Write ONE jsonl, one row per (equation, condition, seed); shard by --seed-list and cat the shards."),
    "F3": ("A4", "Merge without duplicate guard", "Fail on duplicate (equation, condition, seed) keys; never last-writer-wins across shards."),
    "F4": ("A4", "Result artefact problem", "Regenerate with the audited pipeline; quarantine legacy and *_rescued_* / pre_fix files."),
    "X1": ("A5", "Search budget not uniform", "One wall-clock budget (timeout_in_seconds=budget) for every system; no per-system iteration counts."),
    "X2": ("A5", "PySR not deterministic", "PySRRegressor(random_state=seed, deterministic=True, parallelism='serial', temp_equation_file=True, ...)."),
    "X3": ("A5", "LLM response not cached or temperature unpinned", "temperature=0, pinned model id, disk cache keyed by sha256(model+prompt) "
           "(equation, seed) so reruns replay."),
    "P1": ("A6", "validation_score used as evidence", "Report validation_score as a diagnostic only; never gate, rank or test on it."),
    "P2": ("A6", "More than one complexity measure", "Recompute complexity once (sympy node count) for every system."),
    "P3": ("A6", "Selection on an extrapolation metric", "Choose expressions on training/validation data only; far/near/test are for reporting."),
    "S1": ("A7", "Unpaired test on a paired design", "Use paired tests per equation (same data per seed): Wilcoxon signed-rank, exact McNemar, sign test."),
    "S2": ("A7", "Several tests, no multiplicity control", "Holm-adjust across equations (and across the three primary comparisons)."),
    "S3": ("A7", "Primary comparison arm missing", "Compare H vs P, H vs N, N vs P; the ablation needs a no-LLM arm."),
    "S4": ("A7", "Too few seeds", ">= 10 (target 30) seeds per (equation, condition); seeds are nested in equations."),
    "S5": ("A7", "mean / nanmean of R2 hides failures", "Floor R2 explicitly (-1), count nulls as failures, summarise with the median."),
    "L1": ("A8", "No obfuscated / non-textbook equations", "Add '<name> (obf)' twins (renamed variables, perturbed constants) and non-textbook laws."),
    "L2": ("A8", "Ground truth or equation name reaches the LLM", "Prompt may contain data, variable names and units only; no formula, "
           "no equation name (keep test_no_equation_hints green)."),
}

BLOCKS = {
    "stable seed (fixes D1/D2)": '''\
import zlib
def stable_seed(seed: int, equation: str, stream: str = "data"):
    """Independent of equation order, --equations subsets and PYTHONHASHSEED."""
    return [int(seed), zlib.crc32(equation.encode()), zlib.crc32(stream.encode())]
rng = np.random.default_rng(stable_seed(seed, eq.name))     # data for (equation, seed): built ONCE''',
    "metrics with null+reason and relative RMSE (fixes M1-M3, M4, M6)": '''\
def metrics(y, yhat) -> dict:
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    out = dict(n=int(y.size), y_var=float(np.var(y)))
    if not np.all(np.isfinite(yhat)):
        return dict(out, r2=None, rmse=None, rel_rmse=None, reason="nonfinite_prediction")
    rmse = float(np.sqrt(np.mean((y - yhat) ** 2)))
    out.update(rmse=rmse, rel_rmse=rmse / (float(np.mean(np.abs(y))) or 1.0))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    if ss_tot <= 1e-12 * max(1.0, float(np.sum(y ** 2))):
        return dict(out, r2=None, reason="zero_target_variance")
    r2 = 1.0 - float(np.sum((y - yhat) ** 2)) / ss_tot
    return dict(out, r2=r2 if math.isfinite(r2) else None, reason=None if math.isfinite(r2) else "nonfinite_r2")''',
    "PySR fairness (fixes X1/X2)": '''\
PySRRegressor(niterations=1_000_000, timeout_in_seconds=budget, random_state=seed,
              deterministic=True, parallelism="serial", temp_equation_file=True, verbosity=0, progress=False)''',
    "LLM replay cache (fixes X3)": '''\
import hashlib, json, pathlib
def cached_llm(client, model, prompt, cache_dir="llm_cache"):
    key = hashlib.sha256(f"{model}\\n{prompt}".encode()).hexdigest()
    p = pathlib.Path(cache_dir) / f"{key}.json"
    if p.exists():
        return json.loads(p.read_text())["text"]
    text = client.messages.create(model=model, temperature=0, max_tokens=1000,
                                  messages=[{"role": "user", "content": prompt}]).content[0].text
    p.parent.mkdir(exist_ok=True); p.write_text(json.dumps({"text": text}))
    return text''',
    "row writer (fixes F1/F2, M3)": '''\
rec = dict(equation=name, condition=cond, seed=seed, commit=git_commit(), versions=versions(),
           budget_s=budget, fit_time_s=t, llm_mode_used=mode, train=m_tr, regimes=m_reg, error=None)
with open(out, "a") as f:
    f.write(json.dumps(clean(rec), allow_nan=False) + "\\n")     # one row per (equation, condition, seed)''',
}


@dataclass
class Finding:
    rule: str
    sev: str
    file: str
    line: int
    msg: str
    code: str = ""
    fix: str = ""

    @property
    def gate(self) -> str:
        return META[self.rule][0]


# ----------------------------------------------------------------------------------------
# AST helpers
# ----------------------------------------------------------------------------------------
def u(n) -> str:
    try:
        return ast.unparse(n)
    except Exception:                                            # noqa: BLE001
        return ""


def dotted(n) -> str:
    """'np.random.default_rng' for the func of a call; tolerates chained calls/subscripts."""
    parts: List[str] = []
    while True:
        if isinstance(n, ast.Attribute):
            parts.append(n.attr)
            n = n.value
        elif isinstance(n, ast.Call):
            n = n.func
        elif isinstance(n, ast.Subscript):
            n = n.value
        elif isinstance(n, ast.Name):
            parts.append(n.id)
            break
        else:
            break
    d = ".".join(reversed(parts))
    return "np." + d[6:] if d.startswith("numpy.") else d


def last(d: str) -> str:
    return d.split(".")[-1] if d else ""


def num(n) -> Optional[float]:
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
        return float(n.value)
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
        v = num(n.operand)
        return None if v is None else (-v if isinstance(n.op, ast.USub) else v)
    return None


def nonfinite(n) -> bool:
    d = u(n).replace(" ", "")
    return bool(re.fullmatch(r"-?(np|numpy|math)\.(inf|nan|NINF|PINF|NaN|Inf)", d) or
                re.fullmatch(r"float\(['\"][-+]?(inf|infinity|nan)['\"]\)", d, re.I) or
                re.fullmatch(r"-float\(['\"](inf|infinity)['\"]\)", d, re.I))


def strs(node) -> List[str]:
    return [n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def ids(node) -> set:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def base_name(n) -> str:
    while isinstance(n, (ast.Attribute, ast.Subscript)):
        n = n.value
    return n.id if isinstance(n, ast.Name) else ""


R2_TEXT = re.compile(r"r2|r_squared|rsquared", re.I)
METRIC_TEXT = re.compile(r"r2|rmse|mse|mae|score|metric", re.I)
R2_NAME = re.compile(r"(^|_)(r2|r_squared|rsquared|r2_score)(_|$)", re.I)
METRIC_NAME = re.compile(r"(^|_)(r2|rmse|mse|mae|score|metric|metrics|error|loss)(_|$)", re.I)
TEST_TAG = re.compile(r"(^|_)(test|te|near|med|medium|far|ext|extrap|extrapolation|ood|holdout|hold_out|eval)(_|$)", re.I)
REGIME_TAGS = {"near": "near", "medium": "medium", "med": "medium", "mid": "medium", "far": "far", "train": "train"}


def regime_tag(name: str) -> Optional[str]:
    for tok in re.split(r"[^A-Za-z0-9]+", name.lower()):
        if tok in REGIME_TAGS:
            return REGIME_TAGS[tok]
    return None


class Ctx:
    """One parsed source file plus the indexes the rules need."""

    def __init__(self, path: Path, root: Path):
        self.path = path
        try:
            self.rel = str(path.resolve().relative_to(root.resolve()))
        except ValueError:
            self.rel = str(path)
        self.name = path.name
        self.src = path.read_text(encoding="utf-8", errors="replace")
        self.lines = self.src.splitlines()
        self.findings: List[Finding] = []
        self.store: Dict[str, list] = defaultdict(list)          # cross-file evidence
        self.syntax_error: Optional[SyntaxError] = None
        try:
            self.tree = ast.parse(self.src, filename=str(path))
        except SyntaxError as e:
            self.tree, self.syntax_error = None, e
        self.parents: Dict[ast.AST, ast.AST] = {}
        self.calls: List[tuple] = []
        self.funcs: List[ast.AST] = []
        self.enum_names: set = set()
        self.consts: Dict[str, float] = {}
        self.imports: set = set()
        toks: set = set()
        if self.tree is not None:
            for p in ast.walk(self.tree):
                for ch in ast.iter_child_nodes(p):
                    self.parents[ch] = p
                if isinstance(p, ast.Call):
                    self.calls.append((p, dotted(p.func)))
                elif isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.funcs.append(p)
                    toks.add(p.name.lower())
                elif isinstance(p, ast.Import):
                    self.imports.update(a.asname or a.name for a in p.names)
                elif isinstance(p, ast.ImportFrom):
                    self.imports.update(a.asname or a.name for a in p.names)
                    toks.add((p.module or "").lower())
                elif isinstance(p, (ast.For, ast.comprehension)):
                    it, tg = p.iter, p.target
                    if isinstance(it, ast.Call) and dotted(it.func) == "enumerate" and isinstance(tg, ast.Tuple) \
                            and tg.elts and isinstance(tg.elts[0], ast.Name) and "seed" not in u(it).lower():
                        self.enum_names.add(tg.elts[0].id)
                if isinstance(p, ast.Name):
                    toks.add(p.id.lower())
                elif isinstance(p, ast.Attribute):
                    toks.add(p.attr.lower())
                elif isinstance(p, ast.keyword) and p.arg:
                    toks.add(p.arg.lower())
                elif isinstance(p, ast.arg):
                    toks.add(p.arg.lower())
                elif isinstance(p, ast.Constant) and isinstance(p.value, str) and len(p.value) < 200:
                    toks.add(p.value.lower())
            for st in self.tree.body:
                if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
                    v = num(st.value)
                    if v is not None:
                        self.consts[st.targets[0].id] = v
        self.tokens = toks
        self.token_text = "\n".join(sorted(toks))
        self.role = self._role()
        self.writes_results = any(
            d in ("json.dump", "pickle.dump") or last(d) in ("write_text", "to_json", "to_csv")
            or (d == "open" and len(c.args) > 1 and isinstance(c.args[1], ast.Constant) and str(c.args[1].value)[:1] in "wa")
            for c, d in self.calls)

    def _role(self) -> str:
        n, rel = self.name.lower(), self.rel.replace("\\", "/").lower()
        if re.search(r"metric|r2_canonical|json_safe|recovery", n):
            return "metrics"
        if re.search(r"summar|stats|contribution|merge|overlay|flatten|analy|close|report", n):
            return "analysis"
        if "/tools/" in rel or "/core/" in rel:
            return "library"
        return "driver"

    # -- reporting ---------------------------------------------------------------------
    def line(self, ln: int) -> str:
        return self.lines[ln - 1].strip()[:150] if 0 < ln <= len(self.lines) else ""

    def suppressed(self, ln: int, rule: str) -> bool:
        for k in (ln, ln - 1):
            if 0 < k <= len(self.lines):
                m = re.search(r"#\s*audit:\s*ignore(?:\[([^\]]*)\])?", self.lines[k - 1])
                if m and (m.group(1) is None or rule in [x.strip() for x in m.group(1).split(",")]):
                    return True
        return False

    def add(self, rule: str, sev: str, node, msg: str):
        ln = node if isinstance(node, int) else getattr(node, "lineno", 0)
        if self.suppressed(ln, rule):
            return
        self.findings.append(Finding(rule, sev, self.rel, ln, msg, self.line(ln), META[rule][2]))

    # -- tree navigation -----------------------------------------------------------------
    def up(self, node):
        p = self.parents.get(node)
        while p is not None:
            yield p
            p = self.parents.get(p)

    def func_of(self, node):
        return next((p for p in self.up(node) if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef))), None)

    def in_test(self, node) -> bool:
        """Inside a selftest/smoke/dry-run helper: mutation code and toy budgets are intentional there."""
        fn = self.func_of(node) if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else node
        while fn is not None:
            if re.search(r"selftest|smoke|dry_?run|^test_|_test$|^_?mutat", fn.name, re.I):
                return True
            fn = self.func_of(fn)
        return False

    def stmt_of(self, node):
        return next((p for p in [node, *self.up(node)] if isinstance(p, ast.stmt)), None)


# ========================================================================================
# Per-file rules.  Each takes a Ctx and calls ctx.add(rule, severity, node_or_line, message).
# ========================================================================================
FILE_RULES = []


def rule(fn):
    FILE_RULES.append(fn)
    return fn


# ---------------------------------------- A1 -------------------------------------------
LEGACY_DRAWS = {"rand", "randn", "randint", "uniform", "normal", "choice", "shuffle", "permutation", "random",
                "random_sample", "standard_normal", "sample", "beta", "gamma", "poisson", "exponential"}
STD_DRAWS = {"random", "uniform", "gauss", "choice", "choices", "shuffle", "sample", "randint", "randrange", "normalvariate"}


@rule
def r_D1(c: Ctx):
    for call, d in c.calls:
        l = last(d)
        if l in ("default_rng", "RandomState") and (d.startswith("np.random") or d in ("default_rng", "RandomState")):
            seedless = not call.args and not any(k.arg in ("seed",) for k in call.keywords)
            none_seed = call.args and isinstance(call.args[0], ast.Constant) and call.args[0].value is None
            if seedless or none_seed:
                c.add("D1", "HIGH", call, f"{d}() without a seed: every run draws different data")
        elif d == "np.random.seed":
            fn = c.func_of(call)
            looped = any(isinstance(p, (ast.For, ast.While)) for p in c.up(call))
            c.add("D1", "MEDIUM" if (fn is not None or looped) else "LOW", call,
                  "global np.random.seed(): draw order across equations/conditions silently changes the data"
                  + (" (called inside a function/loop)" if (fn is not None or looped) else " (module level)"))
        elif d.startswith("np.random.") and l in LEGACY_DRAWS:
            c.add("D1", "MEDIUM", call, f"{d}() draws from the global RNG; results depend on call order")
        elif d.startswith("random.") and "random" in c.imports and l in STD_DRAWS | {"seed"}:
            c.add("D1", "MEDIUM", call, f"stdlib {d}() uses global state; use a seeded numpy Generator")


CLOCK = {"time.time", "time.time_ns", "time.perf_counter", "time.monotonic", "datetime.now", "datetime.datetime.now",
         "datetime.utcnow", "os.urandom", "uuid.uuid4", "secrets.randbits", "random.randint", "random.random"}
POS_NAMES = {"ei", "eq_idx", "eq_i", "eqi", "equation_idx", "eq_index", "case_idx", "case_i", "idx_eq", "e_idx", "eidx"}


def seed_exprs(call, d):
    ex = []
    if last(d) in ("default_rng", "RandomState", "seed", "SeedSequence", "manual_seed") and call.args:
        ex.append(call.args[0])
    ex += [k.value for k in call.keywords if k.arg in ("seed", "random_state", "rng_seed", "seed_value")]
    return ex


@rule
def r_D2(c: Ctx):
    for call, d in c.calls:
        for ex in seed_exprs(call, d):
            inner = {dotted(n.func) for n in ast.walk(ex) if isinstance(n, ast.Call)}
            names = ids(ex)
            if "hash" in inner:
                c.add("D2", "HIGH", call, "seed uses hash(): str hashes change with PYTHONHASHSEED, data is not reproducible")
            elif inner & CLOCK:
                c.add("D2", "HIGH", call, "seed taken from the clock/OS entropy: not reproducible")
            elif any(last(x) == "index" for x in inner):
                c.add("D2", "HIGH", call, "seed uses list.index(): data changes when the equation list is subset or reordered")
            elif names & c.enum_names:
                c.add("D2", "HIGH", call, f"seed uses enumerate position {sorted(names & c.enum_names)}: a --equations subset "
                                          "or reorder changes the data for every equation")
            elif names & POS_NAMES:
                c.add("D2", "MEDIUM", call, f"seed uses positional index {sorted(names & POS_NAMES)}: check it is stable under subsetting")


GEN_RE = re.compile(r"^(sample_block|generate\w*|make_(data|dataset|blocks?|samples?|split\w*)|gen_\w+|build_(data|dataset|blocks?)\w*"
                    r"|create_(data|dataset)\w*|sample_(train|test|regime|points|data)\w*)$")
COND_RE = re.compile(r"(?<![a-z])(cond|method|system|arm|runner|variant|ablat|pipeline|baseline)", re.I)
RUNFN_RE = re.compile(r"^(run|fit|evaluate|eval)_(cond|method|arm|system|pysr|hypatia|baseline)\w*$", re.I)


@rule
def r_D3(c: Ctx):
    for call, d in c.calls:
        if not GEN_RE.match(last(d)):
            continue
        seeded = any(re.search(r"seed|rng", t, re.I) for t in [u(call)])
        loop = next((p for p in c.up(call) if isinstance(p, ast.For) and COND_RE.search(u(p.target) + " " + u(p.iter))), None)
        fn = c.func_of(call)
        if loop is not None:
            c.add("D3", "MEDIUM" if seeded else "HIGH", call,
                  f"{d}() is called inside the loop over conditions ({u(loop.iter)[:40]}): each condition may see different data"
                  + ("" if seeded else "; the call carries no seed/rng at all"))
        elif fn is not None and RUNFN_RE.match(fn.name) and fn.name != last(d):
            c.add("D3", "MEDIUM", call, f"{d}() is called inside per-condition function {fn.name}(): conditions regenerate their own data")


Y_TEST = re.compile(r"^y_?(test|te|true|near|med|medium|far|ext|extrap|extrapolation|ood|eval|holdout|hold_out)(_|$)|^(test|true|far|near|ood)_y$", re.I)
NOISE = re.compile(r"noise|randn|\.normal\(|standard_normal|rng\.|random", re.I)
X_TEST = re.compile(r"^(x|y)_?(test|te|near|med|medium|far|ext|extrap|ood|eval|holdout|hold_out|val)(_|$)", re.I)


@rule
def r_D4(c: Ctx):
    if c.tree is None:
        return
    for n in ast.walk(c.tree):
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub)):
            for a, b in ((n.left, n.right), (n.right, n.left)):
                if Y_TEST.match(base_name(a)) and NOISE.search(u(b)):
                    c.add("D4", "HIGH", n, f"noise added to '{base_name(a)}': test targets must stay noiseless (noise only on training y)")
                    break
                if base_name(a) in ("y", "y_all", "y_full") and re.search(r"noise|randn|\.normal\(", u(b), re.I):
                    fn = c.func_of(n)
                    if fn is not None and re.search(r"near|far|extrap|test", u(fn), re.I):
                        c.add("D4", "MEDIUM", n, f"noise added to '{base_name(a)}' in a function that also builds test/regime data: "
                                                  "verify noise reaches the training targets only")
        elif isinstance(n, ast.AugAssign) and isinstance(n.op, (ast.Add, ast.Sub)) and Y_TEST.match(base_name(n.target)) and NOISE.search(u(n.value)):
            c.add("D4", "HIGH", n, f"noise accumulated into '{base_name(n.target)}'")


@rule
def r_D5(c: Ctx):
    for call, d in c.calls:
        l = last(d)
        if l == "train_test_split":
            shuf = [k.value for k in call.keywords if k.arg == "shuffle"]
            if shuf and isinstance(shuf[0], ast.Constant) and shuf[0].value is False:
                c.add("D5", "LOW", call, "train_test_split(shuffle=False): ordered split; confirm the held-out part is beyond the training range")
            elif c.role == "library":
                c.add("D5", "LOW", call, "random train_test_split in library code: fine for internal validation/early stopping; "
                                         "a problem only if the held-out part is reported as test/near/medium/far")
            else:
                c.add("D5", "HIGH", call, "random train_test_split: test points lie inside the training range (interpolation, not near/medium/far)")
        elif l in ("KFold", "ShuffleSplit", "StratifiedKFold", "cross_val_score"):
            c.add("D5", "MEDIUM", call, f"{l}: shuffled resampling is not an extrapolation protocol")


@rule
def r_D6(c: Ctx):
    for call, d in c.calls:
        l = last(d)
        if l in ("fit", "fit_transform", "partial_fit", "discover", "train", "fit_predict"):
            args = list(call.args) + [k.value for k in call.keywords]
            bad = [base_name(a) for a in args if X_TEST.match(base_name(a))]
            if bad:
                c.add("D6", "CRITICAL" if l in ("fit", "fit_transform", "partial_fit", "fit_predict") else "HIGH", call,
                      f"{d}() receives {bad}: the model/scaler/prompt sees test or regime data (leakage)")


# ---------------------------------------- A2 -------------------------------------------
ORDER = ["near", "medium", "far"]


def _interval(v):
    if isinstance(v, (ast.Tuple, ast.List)) and len(v.elts) == 2:
        a, b = num(v.elts[0]), num(v.elts[1])
        return (a, b) if a is not None and b is not None else None
    if isinstance(v, ast.Dict):
        kv = {k.value: num(x) for k, x in zip(v.keys, v.values) if isinstance(k, ast.Constant)}
        for lo, hi in (("lo", "hi"), ("min", "max"), ("low", "high"), ("start", "end")):
            if kv.get(lo) is not None and kv.get(hi) is not None:
                return kv[lo], kv[hi]
    return None


def _check_regimes(c: Ctx, where, regs: Dict[str, tuple]):
    if len(regs) < 2:
        return
    prev, prev_name = None, None
    for r in ORDER:
        if r not in regs:
            continue
        lo, hi = regs[r]
        if lo >= hi:
            c.add("R1", "HIGH", where, f"regime '{r}' has lo >= hi: {regs[r]}")
        if prev is not None and lo < prev - 1e-12:
            c.add("R1", "HIGH", where, f"regimes '{prev_name}' and '{r}' overlap or are out of order: {regs[prev_name]} vs {regs[r]}")
        prev, prev_name = max(hi, prev if prev is not None else hi), r


@rule
def r_R1(c: Ctx):
    if c.tree is None:
        return
    names: Dict[str, tuple] = {}
    for n in ast.walk(c.tree):
        if isinstance(n, ast.Dict):
            regs = {}
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and isinstance(k.value, str) and k.value.lower() in ("near", "medium", "med", "mid", "far"):
                    iv = _interval(v)
                    if iv:
                        regs["medium" if k.value.lower() in ("med", "mid") else k.value.lower()] = iv
            _check_regimes(c, n, regs)
        elif isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            m = re.match(r"^(near|medium|mid|far)(_(range|bounds|regime|frac|window))?$", n.targets[0].id, re.I)
            iv = _interval(n.value) if m else None
            if iv:
                names["medium" if m.group(1).lower() == "mid" else m.group(1).lower()] = iv
    _check_regimes(c, 1, names)


REGIME_NAME = re.compile(r"near|medium|far|extrap|regime|ood|boundar", re.I)


@rule
def r_R2(c: Ctx):
    for call, d in c.calls:
        l = last(d)
        if l in ("quantile", "percentile", "nanpercentile", "nanquantile"):
            st, fn = c.stmt_of(call), c.func_of(call)
            tgt = u(st.targets[0]) if isinstance(st, ast.Assign) else ""
            if REGIME_NAME.search(tgt) or (fn is not None and REGIME_NAME.search(fn.name)):
                c.add("R2", "MEDIUM", call, "regime boundary taken from a data quantile: not guaranteed strictly beyond the training range")
        elif l in ("argsort", "sort_values", "nlargest", "nsmallest"):
            fn = c.func_of(call)
            if fn is not None and re.search(r"extrap|regime|near_far|split_(near|far)", fn.name, re.I):
                c.add("R2", "MEDIUM", call, f"{l}() in {fn.name}(): sorted/sliced regimes can overlap the training data; "
                                            "build them from the training max/min per variable")


@rule
def r_R3(c: Ctx):
    if c.tree is None:
        return
    for n in ast.walk(c.tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                tag_t = None
                if isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant) and isinstance(t.slice.value, str):
                    tag_t = regime_tag(t.slice.value)
                elif isinstance(t, ast.Name):
                    tag_t = regime_tag(t.id)
                if tag_t not in ("medium", "far"):
                    continue
                vt = set()
                for x in ast.walk(n.value):
                    if isinstance(x, ast.Name):
                        vt.add(regime_tag(x.id))
                    elif isinstance(x, ast.Constant) and isinstance(x.value, str):
                        vt.add(regime_tag(x.value))
                vt.discard(None)
                if vt and tag_t not in vt and "near" in vt and not isinstance(n.value, ast.Constant):
                    c.add("R3", "HIGH", n, f"'{tag_t}' regime assigned from 'near' ({u(n.value)[:50]}): metrics copied between regimes")
    for call, d in c.calls:
        if METRIC_NAME.search(last(d)) or last(d) in ("r2_score", "mean_squared_error", "compute_metrics", "evaluate"):
            tags = {regime_tag(base_name(a)) for a in call.args if isinstance(a, (ast.Name, ast.Attribute, ast.Subscript))}
            tags.discard(None)
            if len(tags) > 1:
                cmp_ = re.search(r"extrapolation|degrad|gap|drop|ratio|compar|delta|generali[sz]ation", last(d), re.I)
                c.add("R3", "MEDIUM" if cmp_ else "HIGH", call,
                      f"{d}() mixes arrays from regimes {sorted(tags)}: R2/RMSE not from the same arrays"
                      + ("; the name suggests a train-vs-regime comparison: verify it gets per-regime scalars/arrays, not a pooled array"
                         if cmp_ else ""))


@rule
def r_R4(c: Ctx):
    if c.tree is None:
        return
    held = re.search(r"extrap\s*=\s*False|held[_ ]?in|hold[_ ]?in|inside[_ ]?train|within[_ ]?train|\[-1,\s*1\]|\(-1,\s*1\)|bounded", c.src, re.I)
    if held:
        return
    for n in ast.walk(c.tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.lower() in ("rho", "corr", "correlation", "corr_coef", "correlation_coefficient"):
            c.add("R4", "MEDIUM", n, f"variable '{n.value}' is bounded by definition ([-1,1]); no held-in flag found, so the far regime may leave its valid range")
            return


# ---------------------------------------- A3 -------------------------------------------
def _is_r2_formula(n) -> bool:
    return (isinstance(n, ast.BinOp) and isinstance(n.op, ast.Sub) and num(n.left) == 1.0
            and isinstance(n.right, ast.BinOp) and isinstance(n.right.op, ast.Div))


def _canonical_file(c: Ctx) -> bool:
    r = c.rel.replace("\\", "/")
    return "r2_canonical" in r or r.endswith("core/metrics.py")


@rule
def r_M1(c: Ctx):
    if c.tree is None:
        return
    for fn in c.funcs:
        form = [n for n in ast.walk(fn) if _is_r2_formula(n)]
        if form and re.search(r"mean|var|ss_tot|sst|tot", u(fn), re.I) and not c.in_test(fn):
            c.store["r2_impls"].append((fn.name, fn.lineno, _canonical_file(c)))
            if not _canonical_file(c):
                c.add("M1", "LOW" if c.role == "analysis" else "MEDIUM", fn,
                      f"local R2 implementation {fn.name}(): duplicates the canonical definition and can drift from it")
    for n in ast.walk(c.tree):
        if isinstance(n, ast.Assign) and any(R2_NAME.search(base_name(t) or u(t)) for t in n.targets):
            for x in ast.walk(n.value):
                if isinstance(x, ast.Call) and last(dotted(x.func)) in ("corrcoef", "pearsonr", "corr"):
                    c.add("M1", "HIGH", n, "R2 computed as a (squared) correlation: it ignores bias/scale and inflates extrapolation scores")
                    break
    if not _canonical_file(c) and any(isinstance(n, ast.ImportFrom) and (n.module or "").startswith("sklearn.metrics")
                                      and any(a.name == "r2_score" for a in n.names) for n in ast.walk(c.tree)) \
            and "r2_canonical" not in c.token_text:
        c.add("M1", "LOW", 1, "sklearn r2_score imported without r2_canonical: handles constant targets/non-finite predictions differently")


def _positive_den(d) -> bool:
    """'<positive const> + x**2' is >= the constant, so it can never be zero."""
    if isinstance(d, ast.BinOp) and isinstance(d.op, ast.Add):
        for a, b in ((d.left, d.right), (d.right, d.left)):
            v = num(a)
            if v is not None and v > 0 and isinstance(b, ast.BinOp) and isinstance(b.op, ast.Pow):
                e = num(b.right)
                if e is not None and e > 0 and e % 2 == 0:
                    return True
    return False


_GUARD = re.compile(r"eps|1e-|maximum|max\(|clip|where|isclose|> ?0|!= ?0", re.I)


@rule
def r_M2(c: Ctx):
    for fn in c.funcs:
        for n in ast.walk(fn):
            if _is_r2_formula(n) and not c.in_test(n):
                den = n.right.right
                if isinstance(den, ast.Name):
                    guarded = any(isinstance(x, (ast.Compare, ast.IfExp)) and den.id in ids(x) for x in ast.walk(fn)) or \
                        any(isinstance(x, ast.Call) and last(dotted(x.func)) in ("where", "maximum", "clip", "max") and den.id in ids(x) for x in ast.walk(fn))
                else:
                    guarded = bool(_GUARD.search(u(den)))
                if not guarded and not _positive_den(den):
                    c.add("M2", "HIGH", n, f"R2 denominator '{u(den)[:40]}' is never checked for zero variance: inf/NaN R2 on constant targets")


METRIC_KEY = re.compile(r"(^|_)(r2|rmse|mse|mae|score|metric)(_|$)", re.I)
BENIGN_PREFIX = re.compile(r"^(best|max|min|cur|current|prev|running|worst|init)", re.I)
JSON_SAFE = re.compile(r"json_safe|sanitize|nan_to_none|clean|safe_json|jsonable|allow_nan")


@rule
def r_M3(c: Ctx):
    if c.tree is None:
        return
    for n in ast.walk(c.tree):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and isinstance(k.value, str) and METRIC_KEY.search(k.value) and nonfinite(v):
                    c.add("M3", "HIGH", n, f"metric '{k.value}' set to {u(v)}: a sentinel that reaches JSON as -Infinity/NaN")
        elif isinstance(n, ast.Assign) and nonfinite(n.value):
            for t in n.targets:
                key = t.slice.value if isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant) and isinstance(t.slice.value, str) else base_name(t)
                if isinstance(key, str) and METRIC_KEY.search(key) and not BENIGN_PREFIX.match(key):
                    c.add("M3", "HIGH", n, f"'{key}' = {u(n.value)}: store null + reason instead of a non-finite sentinel")
        elif isinstance(n, ast.Return) and n.value is not None and nonfinite(n.value):
            fn = c.func_of(n)
            if fn is not None and re.search(r"r2|metric|score|rmse|evaluate|compute", fn.name, re.I):
                internal = c.role == "library" and re.search(r"fitness|loss|objective|cost|penalty|energy|reward", fn.name, re.I)
                c.add("M3", "LOW" if internal else "HIGH", n,
                      f"{fn.name}() returns {u(n.value)}: callers will store it and JSON will carry -Infinity/NaN"
                      + (" (internal optimiser sentinel: confirm it never reaches a result row)" if internal else ""))
    safe_file = JSON_SAFE.search(c.token_text) is not None
    for call, d in c.calls:
        if d in ("json.dump", "json.dumps") and not safe_file:
            ok = any(k.arg == "allow_nan" and isinstance(k.value, ast.Constant) and k.value.value is False for k in call.keywords)
            if not ok:
                c.add("M3", "LOW" if c.role == "library" else "MEDIUM", call, f"{d}() without allow_nan=False and no sanitiser in this file: NaN/-Infinity literals can be written")
        elif last(d) == "nan_to_num" and METRIC_TEXT.search(u(call)):
            c.add("M3", "MEDIUM", call, "np.nan_to_num on a metric silently turns failures into 0/huge numbers")


@rule
def r_M4(c: Ctx):
    if c.tree is None or c.role == "library":
        return
    consts = {n.value.lower(): n for n in ast.walk(c.tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    if "r2" in consts and any(k in consts for k in ("rmse", "rmse_test", "rmse_far")) and \
            not re.search(r"rel_rmse|relative_rmse|nrmse|rrmse|rel_err|relative_error", c.token_text):
        c.add("M4", "MEDIUM", consts["r2"], "R2 and RMSE are produced but no relative RMSE: R2 alone can mask scale-dependent failures")


@rule
def r_M5(c: Ctx):
    if c.tree is None:
        return
    for n in ast.walk(c.tree):
        if not isinstance(n, ast.ExceptHandler):
            continue
        broad = n.type is None or u(n.type) in ("Exception", "BaseException")
        body = [s for s in n.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Call)
                                         and re.match(r"(print|logging|logger|log|warnings)", dotted(s.value.func)))]
        silent = not body or all(isinstance(s, (ast.Pass, ast.Continue)) for s in body)
        converts = False
        for s in body:
            if isinstance(s, ast.Return) and (s.value is None or isinstance(s.value, ast.Constant) or nonfinite(s.value)):
                converts = True
            if isinstance(s, ast.Assign) and (num(s.value) is not None or nonfinite(s.value)) and \
                    any(METRIC_KEY.search(base_name(t) or "") for t in s.targets):
                converts = True
        t = next((p for p in c.up(n) if isinstance(p, ast.Try)), None)
        risky = t is not None and re.search(r"fit|predict|r2|rmse|metric|discover|evaluate|score", u(ast.Module(body=t.body, type_ignores=[])), re.I)
        if converts and risky:
            c.add("M5", "HIGH", n, "failure of a fit/predict/metric step is converted into a number: failed runs enter the statistics as data")
        elif silent and broad:
            c.add("M5", "MEDIUM" if risky else "LOW", n,
                  "broad except with an empty body around a fit/predict/metric step: failures vanish without a trace" if risky else
                  "broad except with an empty body (parsing/bookkeeping): fine only if the skipped item can never be a result row")


@rule
def r_M6(c: Ctx):
    if c.role == "analysis":
        return
    for call, d in c.calls:
        if last(d) in ("max", "maximum", "clip", "fmax", "minimum") and R2_TEXT.search(u(call)):
            if any((num(a) is not None and num(a) < 0) for a in call.args[1:]):
                c.add("M6", "MEDIUM", call, "R2 floored/clipped where it is computed: the raw value is lost and sensitivity to the floor cannot be checked")


# ---------------------------------------- A4 (per file) ---------------------------------
def _has(c: Ctx, pat: str) -> bool:
    return any(re.search(pat, t) for t in c.tokens)


@rule
def r_F2(c: Ctx):
    if c.tree is None or c.role != "driver" or not c.writes_results:
        return
    for n in ast.walk(c.tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and re.search(r"shard", n.value, re.I) and len(n.value) < 120:
            c.add("F2", "MEDIUM", n, "results are written per shard: mixing old and new shard files is how the legacy results were contaminated")
            break
    appends = any(d == "open" and len(cl.args) > 1 and isinstance(cl.args[1], ast.Constant) and str(cl.args[1].value).startswith("a")
                  for cl, d in c.calls)
    if not appends and "jsonl" not in c.token_text:
        c.add("F2", "LOW", 1, "no append-mode jsonl writer: results are rewritten as one aggregate file, not one row per (equation, condition, seed)")


@rule
def r_F3(c: Ctx):
    if c.role != "analysis" or not re.search(r"merge|overlay|combine|consolidate|flatten|aggregate", c.name, re.I):
        return
    guard = re.search(r"duplicate|\bdups?\b|\bseen\b|already|collision|conflict|not in |setdefault|Counter\(", c.src, re.I)
    if guard:
        return
    for call, d in c.calls:
        if last(d) in ("update", "extend", "append") and re.search(r"load|json|read", u(call), re.I):
            c.add("F3", "MEDIUM", call, "shards are merged with no duplicate-key check: later shards silently overwrite earlier ones (last-writer-wins)")
            return
    c.add("F3", "LOW", 1, "merge/overlay script with no duplicate-key guard found")


# ---------------------------------------- A5 -------------------------------------------
BUDGET_KW = {"timeout_in_seconds": "time", "time_budget": "time", "time_limit": "time", "maxtime": "time", "max_time": "time",
             "budget": "time", "budget_s": "time", "time_budget_s": "time", "niterations": "iter", "n_iterations": "iter"}
ITER_BINDING_MAX = 100_000                     # >= this is effectively "run until the clock stops"


@rule
def r_X1(c: Ctx):
    def val(n):
        v = num(n)
        return c.consts.get(n.id) if v is None and isinstance(n, ast.Name) else v

    def rec(kw, v, ln, who):
        if v is not None:
            c.store["budget"].append((BUDGET_KW[kw], kw, v, ln, who))

    for call, d in c.calls:
        if last(d) in ("SimpleNamespace", "Namespace") or c.in_test(call):
            continue
        for k in call.keywords:
            if k.arg in BUDGET_KW:
                rec(k.arg, val(k.value), call.lineno, d or "call")
        if last(d) == "add_argument" and call.args and isinstance(call.args[0], ast.Constant):
            opt = str(call.args[0].value).lstrip("-").replace("-", "_")
            if opt in BUDGET_KW:
                dv = next((val(k.value) for k in call.keywords if k.arg == "default"), None)
                rec(opt, dv, call.lineno, f"argparse --{opt}")
        if last(d) == "PySRRegressor":
            kws = {k.arg: k.value for k in call.keywords if k.arg}
            ni = val(kws["niterations"]) if "niterations" in kws else None
            if ni is not None and ni < ITER_BINDING_MAX and not any(k in kws for k in ("timeout_in_seconds", "timeout")):
                c.add("X1", "MEDIUM", call, f"PySR budget is an iteration count (niterations={ni:g}), not wall-clock: not matched compute across systems")
    for fn in c.funcs:
        a = fn.args
        pos = a.posonlyargs + a.args
        pairs = list(zip(pos[len(pos) - len(a.defaults):], a.defaults)) + [(x, y) for x, y in zip(a.kwonlyargs, a.kw_defaults) if y is not None]
        for arg, dv in pairs:
            if arg.arg in BUDGET_KW:
                rec(arg.arg, val(dv), dv.lineno, f"default of {fn.name}()")


@rule
def r_X2(c: Ctx):
    for call, d in c.calls:
        if last(d) != "PySRRegressor":
            continue
        kws = {k.arg: k.value for k in call.keywords if k.arg}
        spread = any(k.arg is None for k in call.keywords)
        rs = kws.get("random_state")
        if (rs is None and not spread) or (isinstance(rs, ast.Constant) and rs.value is None):
            c.add("X2", "HIGH", call, "PySRRegressor without random_state: every run explores a different search")
        det = kws.get("deterministic")
        par = kws.get("parallelism")
        serial = (isinstance(par, ast.Constant) and par.value == "serial") or \
                 (num(kws.get("procs")) == 0 and isinstance(kws.get("multithreading"), ast.Constant) and kws["multithreading"].value is False)
        if isinstance(par, ast.Constant) and par.value in ("multithreading", "multiprocessing"):
            c.add("X2", "HIGH", call, f"parallelism='{par.value}' cannot be made reproducible")
        elif not serial and not spread:
            c.add("X2", "MEDIUM", call, "PySR is not forced serial (parallelism='serial'): results differ between runs even with random_state")
        if not (isinstance(det, ast.Constant) and det.value is True) and not spread:
            c.add("X2", "MEDIUM", call, "PySRRegressor without deterministic=True")
        if spread:
            c.add("X2", "LOW", call, "PySRRegressor(**kwargs): determinism settings cannot be verified statically")


LLM_CALLS = ("messages.create", "chat.completions.create", "completions.create", "generate_content", "messages.stream")


@rule
def r_X3(c: Ctx):
    cache = re.search(r"cache|memo|lru_cache|replay|hashlib|sha256|md5", c.token_text)
    for call, d in c.calls:
        if not any(d.endswith(s) for s in LLM_CALLS):
            continue
        kws = {k.arg: k.value for k in call.keywords if k.arg}
        t = num(kws["temperature"]) if "temperature" in kws else None
        tprob = "temperature" not in kws or (t is not None and t > 0)
        why = "temperature not set" if "temperature" not in kws else (
            f"temperature={t:g}" if t is not None else "temperature is not a literal (cannot verify it is pinned)")
        if not cache and tprob:
            c.add("X3", "HIGH", call, f"LLM call with {why} and no response cache in this file: reruns cannot reproduce the same expression")
        elif not cache:
            c.add("X3", "MEDIUM", call, "LLM call without a response cache: a rerun can still differ (model drift, nondeterministic decoding)")
        elif tprob:
            c.add("X3", "LOW", call, f"cached LLM call but {why}: first-run variation is frozen by the cache; fine only if the cache is keyed by (equation, seed)")
        m = kws.get("model")
        if isinstance(m, ast.Constant) and isinstance(m.value, str) and re.search(r"latest|preview", m.value):
            c.add("X3", "MEDIUM", call, f"unpinned model id '{m.value}': the model can change under the experiment")


# ---------------------------------------- A6 -------------------------------------------
STAT_FUNCS = {"spearmanr", "pearsonr", "kendalltau", "mannwhitneyu", "wilcoxon", "ttest_ind", "ttest_rel", "ttest_1samp",
              "kruskal", "corrcoef", "corr", "pointbiserialr", "ranksums"}
SEL_FUNCS = {"max", "min", "sorted", "argmax", "argmin", "nlargest", "nsmallest", "idxmax", "idxmin"}


@rule
def r_P1(c: Ctx):
    if c.tree is None:
        return
    seen = set()
    for n in ast.walk(c.tree):
        hit = (isinstance(n, ast.Name) and n.id == "validation_score") or (isinstance(n, ast.Attribute) and n.attr == "validation_score") \
            or (isinstance(n, ast.Constant) and n.value == "validation_score")
        if not hit:
            continue
        for p in c.up(n):
            if isinstance(p, ast.Call):
                l = last(dotted(p.func))
                if l in STAT_FUNCS or l in SEL_FUNCS:
                    if p.lineno not in seen:
                        seen.add(p.lineno)
                        c.add("P1", "HIGH", p, f"validation_score feeds {l}(): a proxy is being used as evidence/selection")
                    break
            if isinstance(p, ast.Compare):
                if all(isinstance(o, (ast.Is, ast.IsNot)) for o in p.ops) or \
                        all(isinstance(x, ast.Constant) and x.value is None for x in p.comparators):
                    break
                if p.lineno not in seen:
                    seen.add(p.lineno)
                    c.add("P1", "MEDIUM", p, "validation_score is compared against a value: if it gates or ranks results it is a proxy used as evidence")
                break
            if isinstance(p, ast.stmt):
                break


@rule
def r_P2(c: Ctx):
    if c.tree is None:
        return
    fam = c.store["complexity"]
    for n in ast.walk(c.tree):
        if isinstance(n, ast.Attribute) and n.attr == "complexity" and isinstance(n.ctx, ast.Load):
            fam.append(("PySR-reported .complexity", n.lineno))
        elif isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) and n.slice.value == "complexity" and isinstance(n.ctx, ast.Load):
            fam.append(("PySR-reported ['complexity']", n.lineno))
        elif isinstance(n, ast.Call) and last(dotted(n.func)) in ("count_ops", "preorder_traversal", "node_count", "count_nodes",
                                                                   "expr_size", "tree_size", "expression_size"):
            fam.append(("expression node count", n.lineno))
        elif isinstance(n, ast.Assign) and "complex" in " ".join(u(t) for t in n.targets).lower():
            v = u(n.value)
            if re.search(r"\blen\(", v):
                fam.append(("string/sequence length", n.lineno))
            elif re.search(r"\.split\(|findall", v):
                fam.append(("token count", n.lineno))


TESTISH = re.compile(r"(^|[_\W])(far|near|medium|extrap\w*|ood|test|holdout)([_\W]|$)", re.I)
METRICW = re.compile(r"r2|rmse|score|loss|err|mse|mae", re.I)


@rule
def r_P3(c: Ctx):
    if c.role == "analysis":
        return
    for call, d in c.calls:
        if last(d) in SEL_FUNCS:
            t = u(call)
            if TESTISH.search(t) and METRICW.search(t):
                c.add("P3", "HIGH", call, f"{last(d)}() ranks/selects on a far/near/test metric: model selection on the evaluation data")


# ---------------------------------------- A7 -------------------------------------------
STAT_TESTS = {"wilcoxon", "mannwhitneyu", "ttest_ind", "ttest_rel", "ttest_1samp", "binomtest", "binom_test", "fisher_exact",
              "chi2_contingency", "kruskal", "ranksums", "f_oneway", "mcnemar", "permutation_test", "sign_test"}
UNPAIRED = {"mannwhitneyu", "ttest_ind", "ranksums", "kruskal", "f_oneway"}


@rule
def r_S1_S2(c: Ctx):
    tests = [(call, last(d)) for call, d in c.calls if last(d) in STAT_TESTS]
    for call, l in tests:
        if l in UNPAIRED:
            c.add("S1", "HIGH", call, f"{l}() is unpaired: every seed of every equation shares data across conditions (paired design), "
                                      "and seeds are nested in equations, so p-values are anti-conservative/invalid")
    if len(tests) >= 2 and not re.search(r"holm|bonferroni|multipletests|fdr|benjamini|sidak|hochberg", c.token_text):
        c.add("S2", "MEDIUM", tests[0][0], f"{len(tests)} statistical tests and no multiplicity correction (Holm/Bonferroni/FDR)")


SEEDS_NAME = re.compile(r"^(seeds?|seed_list|n_?seeds|num_seeds|n_runs)$", re.I)


@rule
def r_S4(c: Ctx):
    if c.tree is None:
        return

    def report(node, k, how):
        if k < 3:
            c.add("S4", "HIGH", node, f"{how}: {k} seed(s): no per-equation inference is possible")
        elif k < 10:
            c.add("S4", "MEDIUM", node, f"{how}: {k} seeds < 10 (the closure gate needs >= 10, the protocol targets 30)")

    for n in ast.walk(c.tree):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and SEEDS_NAME.match(n.targets[0].id):
            v = n.value
            if isinstance(v, (ast.List, ast.Tuple, ast.Set)) and v.elts and all(isinstance(e, ast.Constant) and isinstance(e.value, int) for e in v.elts):
                report(n, len(v.elts), f"{n.targets[0].id} is a hard-coded list")
            elif num(v) is not None and re.match(r"^(n_?seeds|num_seeds|seeds)$", n.targets[0].id, re.I):
                report(n, int(num(v)), f"{n.targets[0].id} = {num(v):g}")
        elif isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == "seed" \
                and isinstance(n.iter, ast.Call) and dotted(n.iter.func) == "range" and len(n.iter.args) == 1 and num(n.iter.args[0]) is not None:
            report(n, int(num(n.iter.args[0])), "loop 'for seed in range(k)'")
    for call, d in c.calls:
        if last(d) == "add_argument" and call.args and isinstance(call.args[0], ast.Constant) \
                and re.match(r"^--(n[-_])?seeds$", str(call.args[0].value)):
            dv = next((num(k.value) for k in call.keywords if k.arg == "default"), None)
            if dv is not None and dv < 10:
                c.add("S4", "LOW", call, f"--seeds defaults to {dv:g} (< 10)")


@rule
def r_S5(c: Ctx):
    for call, d in c.calls:
        l = last(d)
        t = u(call)
        if l in ("nanmean", "nanmedian") and re.search(r"r2|r_squared", t, re.I):
            c.add("S5", "MEDIUM", call, f"{l}() over R2 drops nulls: degenerate/failed runs disappear instead of counting as failures")
        elif l in ("mean", "average") and re.search(r"r2|r_squared", t, re.I):
            recv = call.func.value if isinstance(call.func, ast.Attribute) else (call.args[0] if call.args else None)
            if isinstance(recv, ast.Compare):
                continue                                              # (r2 < thr).mean() is a failure rate
            fn = c.func_of(call)
            scope = u(fn) if fn is not None else c.src
            if not re.search(r"isfinite|clip|maximum|floor|max\(|isnan", scope):
                c.add("S5", "MEDIUM", call, "mean of R2 with no floor/finite filter: one catastrophic run dominates the average")


# ---------------------------------------- A8 (per file collectors) ---------------------
TEXTBOOK = ["kinetic energy", "ideal gas", "gravitational", "allometric", "michaelis", "logistic growth", "henderson", "price impact",
            "constant product", "value at risk", "liquidation", "portfolio", "arrhenius", "rate law", "impermanent loss", "black-scholes",
            "black_scholes", "snell", "coulomb", "ohm", "bernoulli", "planck", "newton", "hooke", "lotka", "nguyen"]
LEAK_NAME = re.compile(r"(true|ground_?truth|target|gt|oracle|reference|gold)_(formula|expr(ession)?|equation|law|latex)$|^(formula|ground_truth)$", re.I)
PIPE_FN = re.compile(r"discover|fit|run|llm|prompt|hypatia|query|ask|generate|propose|solve", re.I)
EQNAME_FV = re.compile(r"eq(uation)?[_.]?(name|key|id|label|title)|case[_.]?name|problem[_.]?name|law[_.]?name|benchmark[_.]?name", re.I)


@rule
def r_L(c: Ctx):
    if c.tree is None:
        return
    for n in ast.walk(c.tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and len(n.value) < 80:
            low = n.value.lower()
            for t in TEXTBOOK:
                if t in low:
                    c.store["textbook"].append((t, n.lineno))
                    break
    if re.search(r"obf|obfuscat|disguis|non_?textbook|novel_law|perturbed", c.token_text):
        c.store["obf"].append(1)
    for call, d in c.calls:
        if not PIPE_FN.search(last(d)):
            continue
        for k in call.keywords:
            if k.arg and LEAK_NAME.search(k.arg):
                c.add("L2", "HIGH", call, f"keyword '{k.arg}' hands the ground-truth expression to {d}()")
        for a in list(call.args) + [k.value for k in call.keywords]:
            for x in ast.walk(a):
                nm = x.id if isinstance(x, ast.Name) else x.attr if isinstance(x, ast.Attribute) else \
                    (x.slice.value if isinstance(x, ast.Subscript) and isinstance(x.slice, ast.Constant) and isinstance(x.slice.value, str) else "")
                if nm and LEAK_NAME.search(nm):
                    c.add("L2", "HIGH", call, f"'{nm}' is passed into {d}(): the pipeline can read the answer")
                    break
    for n in ast.walk(c.tree):
        if not isinstance(n, ast.JoinedStr):
            continue
        st, fn = c.stmt_of(n), c.func_of(n)
        tgt = u(st.targets[0]) if isinstance(st, ast.Assign) else ""
        if not (re.search(r"prompt|query|message|content|instruction", tgt, re.I) or (fn is not None and re.search(r"prompt", fn.name, re.I))):
            continue
        for fv in n.values:
            if isinstance(fv, ast.FormattedValue):
                t = u(fv.value)
                if LEAK_NAME.search(t):
                    c.add("L2", "HIGH", n, f"prompt interpolates '{t}': the ground-truth expression is in the LLM prompt")
                elif EQNAME_FV.search(t):
                    c.add("L2", "MEDIUM", n, f"prompt interpolates the equation name '{t}': enables recall of a textbook law instead of discovery")
                elif re.fullmatch(r"(\w+[.])?domain", t):
                    c.add("L2", "LOW", n, f"prompt interpolates '{t}': a domain hint raises recall on textbook laws (acceptable if the same for the no-LLM arm's priors)")


# ========================================================================================
# Package-level rules (cross-file)
# ========================================================================================
def _emit(findings: List[Finding], c: Optional[Ctx], rule_id: str, sev: str, line: int, msg: str):
    if c is not None:
        before = len(c.findings)
        c.add(rule_id, sev, line, msg)
        findings.extend(c.findings[before:])
        del c.findings[before:]
    else:
        findings.append(Finding(rule_id, sev, "<package>", 0, msg, "", META[rule_id][2]))


def pkg_rules(ctxs: List[Ctx], primary: str) -> List[Finding]:
    out: List[Finding] = []
    # H1 primary driver present
    if not any(c.name == primary for c in ctxs):
        _emit(out, None, "H1", "HIGH", 0, f"primary driver '{primary}' was not found among the {len(ctxs)} audited files")
    # F1 provenance fields in row-writing drivers
    fields = [("seed", r"(^|_)seeds?($|_)", "HIGH"), ("commit", r"(^|_)(git|commit|sha)(_|$)|rev[-_]parse", "MEDIUM"),
              ("library versions", r"__version__|importlib|(^|_)versions?($|_)|platform|freeze", "MEDIUM"),
              ("budget", r"budget|timeout|time_limit|(^|_)(max)?time(_|$)", "MEDIUM"),
              ("fit time", r"fit_time|elapsed|wall|perf_counter|runtime|(^|_)time(_|$)", "LOW"),
              ("llm_mode_used", r"llm_mode", "MEDIUM")]
    drivers = [c for c in ctxs if c.tree is not None and c.role == "driver" and c.writes_results
               and (re.match(r"exp1", c.name) or "pysrregressor" in c.tokens or "hypatia" in c.token_text)]
    for c in drivers:
        for label, pat, sev in fields:
            if not _has(c, pat):
                _emit(out, c, "F1", sev, 1, f"result rows never record {label}")
    # X1 budgets
    allb = [(c, *b) for c in ctxs for b in c.store["budget"]]
    time_vals = sorted({b[3] for b in allb if b[1] == "time"})
    if len(time_vals) > 1:
        for c, kind, kw, v, ln, who in allb:
            if kind == "time":
                _emit(out, c, "X1", "HIGH", ln, f"wall-clock budget {kw}={v:g} ({who}); the package uses {len(time_vals)} different values {time_vals}")
    it_vals = sorted({b[3] for b in allb if b[1] == "iter" and b[3] < ITER_BINDING_MAX})
    if len(it_vals) > 1:
        for c, kind, kw, v, ln, who in allb:
            if kind == "iter" and v < ITER_BINDING_MAX:
                _emit(out, c, "X1", "MEDIUM", ln, f"iteration budget {kw}={v:g} ({who}); values differ across the package: {it_vals}")
    # P2 complexity measures
    fams: Dict[str, list] = defaultdict(list)
    for c in ctxs:
        for name, ln in c.store["complexity"]:
            fams[name].append((c, ln))
    if len(fams) > 1:
        for name, lst in fams.items():
            c, ln = lst[0]
            _emit(out, c, "P2", "MEDIUM", ln, f"complexity measured as '{name}' ({len(lst)} site(s)); package also uses {sorted(set(fams) - {name})}. "
                                               "Cross-system comparisons need one measure")
    # S3 arms
    blob = "\n".join(c.src for c in ctxs)
    arms = dict(hypatia=re.search(r"hypatia|hds", blob, re.I), pysr=re.search(r"pysr", blob, re.I),
                nollm=re.search(r"no[_\- ]?llm|nollm|llm[_\- ]?off|without[_\- ]?llm|(use|enable)_llm\s*=\s*False|disable_llm\s*=\s*True|skip_llm", blob, re.I))
    if not arms["nollm"]:
        _emit(out, None, "S3", "HIGH", 0, "no 'no-LLM' arm found anywhere in the audited code: without Hypatia-without-LLM the ablation cannot separate the LLM from the pipeline")
    for k, label in (("hypatia", "Hypatia"), ("pysr", "PySR")):
        if not arms[k]:
            _emit(out, None, "S3", "HIGH" if k == "hypatia" else "MEDIUM", 0, f"no {label} arm found in the audited code")
    # L1 recall control
    tb = {t for c in ctxs for t, _ in c.store["textbook"]}
    obf = any(c.store["obf"] for c in ctxs)
    if not obf:
        where = max((c for c in ctxs if c.store["textbook"]), key=lambda c: len(c.store["textbook"]), default=None)
        ln = where.store["textbook"][0][1] if where else 0
        _emit(out, where, "L1", "MEDIUM", ln,
              (f"{len(tb)} textbook-named equations ({', '.join(sorted(tb)[:6])}...) and no obfuscated/non-textbook twin" if len(tb) >= 3 else
               "equation registry not located in the audited files, and no obfuscated/non-textbook equations anywhere")
              + ": LLM gains cannot be separated from recall of memorised laws")
    return out


# ========================================================================================
# Results-artefact scan (F4): legacy literals, rescued/mixed shards, missing commit
# ========================================================================================
NONFINITE_LIT = re.compile(r'(?<![\w".])(-?Infinity|NaN)(?![\w"])')


def scan_results(rdir: Path, root: Path, max_bytes: int = 50_000_000) -> List[Finding]:
    out: List[Finding] = []
    if not rdir.exists():
        return out

    def rel(p):
        try:
            return str(p.resolve().relative_to(root.resolve()))
        except ValueError:
            return str(p)

    files = sorted(p for p in rdir.rglob("*") if p.is_file() and p.suffix in (".json", ".jsonl"))
    rescued = [p for p in files if "_rescued_" in p.name]
    shards = [p for p in files if re.search(r"_shard\d+", p.name) and "_rescued_" not in p.name and "checkpoint" not in p.name]
    stale = sorted({p.parent for p in files if re.search(r"pre_?(prompt_)?fix|exploratory|backup|stale|\bold\b", str(p.parent), re.I)})
    n_bad = 0
    for p in files:
        if p.stat().st_size > max_bytes:
            continue
        txt = p.read_text(errors="replace")
        m = NONFINITE_LIT.search(txt)
        if m:
            n_bad += 1
            if n_bad <= 40:
                cnt = len(NONFINITE_LIT.findall(txt))
                out.append(Finding("F4", "HIGH", rel(p), txt.count("\n", 0, m.start()) + 1,
                                   f"{cnt} non-finite literal(s) ({m.group(1)}...) in a result file: legacy writer; strict JSON parsers reject it",
                                   txt[max(0, m.start() - 30): m.end() + 10].replace("\n", " "), META["F4"][2]))
        if re.search(r"exp1_ablation_results(?!.*shard)", p.name) and p.suffix == ".json" and not re.search(r"commit|git_sha|provenance", txt[:2_000_000]):
            out.append(Finding("F4", "MEDIUM", rel(p), 1, "canonical results file records no git commit: rows cannot be tied to a code version", "", META["F4"][2]))
    if n_bad > 40:
        out.append(Finding("F4", "HIGH", rel(rdir), 0, f"... and {n_bad - 40} more result files with non-finite literals", "", META["F4"][2]))
    if rescued:
        out.append(Finding("F4", "MEDIUM", rel(rdir), 0, f"{len(rescued)} files named *_rescued_*: results were salvaged from other runs; make sure none feeds the analysis",
                           rel(rescued[0]), META["F4"][2]))
    if len(shards) > 1:
        out.append(Finding("F4", "MEDIUM", rel(rdir), 0, f"{len(shards)} per-shard result files next to merged ones: mixed old/new shards are possible; "
                                                      "analyse ONE canonical jsonl", rel(shards[0]), META["F4"][2]))
    for s in stale[:10]:
        out.append(Finding("F4", "LOW", rel(s), 0, "stale/pre-fix result directory sits inside the results tree: quarantine it so it cannot be analysed by mistake", "", META["F4"][2]))
    return out


# ========================================================================================
# Discovery, driver, gates, report
# ========================================================================================
SEED_FILES = [
    "hypatiax/experiments/benchmarks/exp1_ablation.py", "hypatiax/experiments/benchmarks/exp1_five_system.py",
    "hypatiax/experiments/benchmarks/extrap_r2_far.py", "hypatiax/experiments/benchmarks/run_instability_suite.py",
    "hypatiax/experiments/benchmarks/hypatia.py",
    "hypatiax/core/metrics.py", "hypatiax/core/r2_canonical.py", "hypatiax/core/json_safe.py", "hypatiax/core/recovery_eval.py",
    "hypatiax/tools/utils/pca_split_utils.py",
    "hypatiax/tools/symbolic/hybrid_system_v50_2.py", "hypatiax/tools/symbolic/symbolic_engine.py",
    "hypatiax/tools/symbolic/physics_aware_regressor.py",
    "hypatiax/core/base_pure_llm/baseline_pure_llm_defi_discovery.py",
    "exp1_llm_contribution.py", "scripts/ci/ablation_multiseed_summary.py", "scripts/ci/overlay_partial_ablation.py",
    "scripts/run_phase3_ablation.py", "scripts/tools/summarize_exp1_logs.py", "scripts/tools/merge_instability_shards.py",
    "audit_out/merge_exp1_ablation_shards.py",
]
SKIP_DIRS = {"archive", "__pycache__", ".git", "venv", ".venv", "node_modules", "outputs", "tests", "hypatiax.egg-info", "results",
             "data", "exploratory", "build", "dist", "site-packages", "docs", "p2", "p2_dry", "triage_out"}
REFERENCE = {"exp1_multiseed.py", "phase-ablation-close.py", "phase-ablation-close__1_.py", "phase-ablation.py"}


def discover(root: Path, primary: str, extra_globs=(), include_archive=False, include_reference=False) -> List[Path]:
    found: List[Path] = [root / r for r in SEED_FILES if (root / r).exists()]
    skip = SKIP_DIRS - ({"archive"} if include_archive else set())
    me = Path(__file__).resolve()
    for p in root.rglob("*.py"):
        parts = set(p.relative_to(root).parts[:-1])
        if parts & skip or p.resolve() == me or p.name.startswith("test_"):
            continue
        if p.name in REFERENCE and not include_reference:
            continue
        if p.name == primary:
            found.append(p)
            continue
        try:
            head = p.read_text(errors="replace")[:300_000]
        except OSError:
            continue
        if re.search(r"exp1[_-]?ablation|exp1_five|ablation_multiseed", head):
            found.append(p)
    for g in extra_globs:
        found += [p for p in root.glob(g) if p.is_file()]
    seen, uniq = set(), []
    for p in found:
        k = p.resolve()
        if k not in seen and p.name not in ({"phase-ablation.py"} if not include_reference else set()):
            seen.add(k)
            uniq.append(p)
    return uniq


def run_audit(root: Path, files: List[Path], primary: str, results_dir: Optional[Path]) -> dict:
    ctxs = [Ctx(p, root) for p in files]
    for c in ctxs:
        if c.tree is None:
            e = c.syntax_error
            c.add("H0", "HIGH", (e.lineno or 1) if e else 1, f"syntax error: {e.msg if e else '?'}; no rule ran on this file")
            continue
        for fn in FILE_RULES:
            try:
                fn(c)
            except Exception as e:                                           # noqa: BLE001
                tb = e.__traceback__
                while tb is not None and tb.tb_next is not None:
                    tb = tb.tb_next
                c.add("H2", "MEDIUM", 1, f"rule {fn.__name__} crashed: {type(e).__name__}: {e} "
                                         f"(auditor line {tb.tb_lineno if tb else '?'}); its findings are missing for this file")
    findings = [f for c in ctxs for f in c.findings]
    findings += pkg_rules(ctxs, primary)
    if results_dir is not None:
        findings += scan_results(results_dir, root)
    uniq: Dict[tuple, Finding] = {}
    for f in findings:
        uniq.setdefault((f.rule, f.file, f.line, f.msg), f)
    findings = sorted(uniq.values(), key=lambda f: (SEV[f.sev], f.gate, f.file, f.line))
    gates = {}
    for g, name in GATES.items():
        fs = [f for f in findings if f.gate == g]
        st = "FAIL" if any(f.sev in ("CRITICAL", "HIGH") for f in fs) else ("CAVEAT" if fs else "PASS")
        cnt = Counter(f.sev for f in fs)
        gates[name] = dict(status=st, counts={k: cnt[k] for k in SEV if cnt[k]}, rules=sorted({f.rule for f in fs}),
                           summary=("; ".join(f"{k} {META[k][1].lower()}" for k in sorted({f.rule for f in fs}))[:230] or "no known bad pattern found"))
    statuses = [v["status"] for v in gates.values()]
    overall = "PHASE_ABLATION_CODE_OPEN" if "FAIL" in statuses else \
        ("PHASE_ABLATION_CODE_CLOSED_WITH_CAVEATS" if "CAVEAT" in statuses else "PHASE_ABLATION_CODE_CLOSED")
    files_info = [dict(file=c.rel, role=c.role, lines=len(c.lines), findings=sum(1 for f in findings if f.file == c.rel)) for c in ctxs]
    return dict(overall=overall, gates=gates, findings=[asdict(f) | dict(gate=f.gate, title=META[f.rule][1]) for f in findings],
                files=files_info, primary=primary, root=str(root), results_dir=str(results_dir) if results_dir else None)


def write_report(path: Path, res: dict):
    L = [f"# Exp-1 ablation code audit: {res['overall']}", "",
         f"root `{res['root']}`; primary driver `{res['primary']}`; {len(res['files'])} files audited"
         + (f"; results scanned `{res['results_dir']}`" if res["results_dir"] else ""), "",
         "Static analysis: PASS means no known bad pattern was found, not that the code is correct. "
         "Use `phase-ablation-close.py` on the package output as the regression test.", "",
         "## Gates", "", "| gate | status | findings | summary |", "|---|---|---|---|"]
    for k, v in res["gates"].items():
        L.append(f"| {k} | {v['status']} | {', '.join(f'{n} {s.lower()}' for s, n in v['counts'].items()) or '0'} | {v['summary']} |")
    L += ["", "## Files audited", "", "| file | role | lines | findings |", "|---|---|---|---|"]
    L += [f"| `{f['file']}` | {f['role']} | {f['lines']} | {f['findings']} |" for f in res["files"]]
    L += ["", "## Findings", ""]
    for g, name in GATES.items():
        fs = [f for f in res["findings"] if f["gate"] == g]
        if not fs:
            continue
        L += [f"### {name} ({res['gates'][name]['status']})", ""]
        for f in fs:
            loc = f"{f['file']}:{f['line']}" if f["line"] else f["file"]
            L.append(f"- **[{f['sev']}] {f['rule']}** `{loc}` {f['msg']}")
            if f["code"]:
                L.append(f"  - code: `{f['code']}`")
            L.append(f"  - fix: {f['fix']}")
        L.append("")
    L += ["## Reference building blocks (from the exp1_multiseed methodology)", ""]
    for title, code in BLOCKS.items():
        L += [f"**{title}**", "", "```python", code, "```", ""]
    path.write_text("\n".join(L) + "\n")


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, float):
        return o if math.isfinite(o) else None
    return o


def cmd_audit(a) -> int:
    root = Path(a.root).resolve()
    if a.files:
        files = [Path(f) if Path(f).is_absolute() else (Path.cwd() / f if (Path.cwd() / f).exists() else root / f) for f in a.files]
        files = [f for f in files if f.exists()]
    else:
        files = discover(root, a.primary, a.extra_glob or [], a.include_archive, a.include_reference)
    rdir = None
    if not a.no_results_scan:
        rdir = Path(a.results_dir) if a.results_dir else root / "hypatiax" / "data" / "results" / "ablation"
        rdir = rdir if rdir.exists() else None
    global LAST_AUDIT
    res = run_audit(root, files, a.primary, rdir)
    LAST_AUDIT = res
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for m in MARKERS:
        (out / m).unlink(missing_ok=True)
    (out / res["overall"]).write_text(res["overall"] + "\n")
    (out / "phase_ablation_code_audit.json").write_text(json.dumps(clean(res), indent=2, allow_nan=False))
    write_report(out / "phase_ablation_code_audit.md", res)
    if not a.quiet:
        print(f"{res['overall']}   ->  {out}   ({len(files)} files, {len(res['findings'])} findings)")
        for k, v in res["gates"].items():
            print(f"  {v['status']:7s} {k:22s} {v['summary'][:120]}")
        for f in res["findings"]:
            if f["rule"] in ("H0", "H2"):
                print(f"  [{f['sev']}] {f['rule']} {f['file']}  {f['msg'][:170]}")
        top = [f for f in res["findings"] if SEV[f["sev"]] <= SEV[a.fail_on]]
        for f in top[: a.show]:
            print(f"  [{f['sev']}] {f['rule']} {f['file']}:{f['line']}  {f['msg'][:130]}")
        if len(top) > a.show:
            print(f"  ... {len(top) - a.show} more at or above {a.fail_on} in the report")
    return 1 if any(SEV[f["sev"]] <= SEV[a.fail_on] for f in res["findings"]) else 0


def cmd_list(a) -> int:
    root = Path(a.root).resolve()
    files = discover(root, a.primary, a.extra_glob or [], a.include_archive, a.include_reference)
    for p in files:
        print(p.relative_to(root) if p.is_relative_to(root) else p)
    print(f"{len(files)} files" + ("" if any(p.name == a.primary for p in files) else f"   (WARNING: primary '{a.primary}' not found)"))
    return 0


# ========================================================================================
# Selftest: a package seeded with one instance of every bug, and a clean twin
# ========================================================================================
BUGGY_DRIVER = r"""
import json, time, random
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from scipy import stats
from scipy.stats import mannwhitneyu, wilcoxon, spearmanr
from pysr import PySRRegressor
import anthropic

REGIMES = {"near": (0.0, 0.6), "medium": (0.5, 2.0), "far": (2.0, 9.0)}
SEEDS = [42, 123, 99]
EQUATIONS = ["Kinetic Energy", "Ideal Gas Law", "Michaelis-Menten", "Allometric Scaling"]
VARS = [("s1", 0.01, 0.3), ("rho", -1, 1)]
np.random.seed(0)
random.seed(1)


def gen_data(eq):
    return np.random.rand(100, 2)


def r2(y, yhat):
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    return 1 - ss_res / ss_tot


def r2_corr(y, yhat):
    r2 = np.corrcoef(y, yhat)[0, 1] ** 2
    return r2


def safe_r2(y, yhat):
    try:
        return r2(y, yhat)
    except Exception:
        return float("-inf")


def far_edge(X_all):
    far_lo = np.percentile(X_all, 90)
    return far_lo


def run(client, X, y, X_test, y_test, rows, validation_score, far_vals, r2_list, r2_val, true_formula, eq_name, domain, hypatia):
    rng = np.random.default_rng()
    for ei, name in enumerate(EQUATIONS):
        rng = np.random.default_rng([42, ei])
        rng2 = np.random.default_rng(hash(name))
        rng3 = np.random.default_rng(int(time.time()))
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3)
        y_test_noisy = y_test + rng.normal(0, 0.1, 5)
        for cond in ["pysr_only", "hypatia"]:
            data = gen_data(name)
            model = PySRRegressor(niterations=40, timeout_in_seconds=600)
            model.fit(X_test, y_test)
            res = {"r2": 1.0, "rmse": 2.0}
            res["near"] = r2_score(y_near, p_near)
            res["far"] = res["near"]
            far_r2 = near_r2
            score = r2_score(y_near, pred_far)
            floor = max(r2_val, -1.0)
            if validation_score > 0.5:
                pass
            best = max(rows, key=lambda r: r["far_r2"])
            rho_s = spearmanr(validation_score, far_vals)
            u = mannwhitneyu(far_vals, far_vals)
            w = wilcoxon(far_vals)
            m = np.nanmean(r2_list)
            complexity = len(str(name))
            complexity2 = sum(1 for _ in preorder_traversal(name))
            msg = client.messages.create(model="claude-sonnet-latest", messages=[])
            prompt = f"Find the law for {eq_name} in {domain}"
            hypatia.discover(X, y, ground_truth_formula=true_formula)
            with open(f"exp1_ablation_results_shard{ei}.json", "w") as f:
                json.dump(res, f)
"""

BUGGY_HYBRID = r"""
from pysr import PySRRegressor

def build(seed):
    return PySRRegressor(niterations=100, timeout_in_seconds=300, random_state=seed, deterministic=True, parallelism="serial")
"""

BUGGY_MERGE = r"""
import json, glob
merged = {}
for p in glob.glob("exp1_ablation_results_shard*.json"):
    merged.update(json.load(open(p)))
json.dump(merged, open("exp1_ablation_results.json", "w"))
"""

CLEAN_METRICS = r"""
import math
import numpy as np


def metrics(y, yhat):
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    out = dict(n=int(y.size), y_var=float(np.var(y)))
    if not np.all(np.isfinite(yhat)):
        return dict(out, r2=None, rmse=None, rel_rmse=None, reason="nonfinite_prediction")
    rmse = float(np.sqrt(np.mean((y - yhat) ** 2)))
    out.update(rmse=rmse, rel_rmse=rmse / (float(np.mean(np.abs(y))) or 1.0))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    if ss_tot <= 1e-12 * max(1.0, float(np.sum(y ** 2))):
        return dict(out, r2=None, reason="zero_target_variance")
    r2 = 1.0 - float(np.sum((y - yhat) ** 2)) / ss_tot
    return dict(out, r2=r2 if math.isfinite(r2) else None, reason=None if math.isfinite(r2) else "nonfinite_r2")
"""

CLEAN_DRIVER = r"""
import argparse, hashlib, json, math, pathlib, platform, subprocess, time, zlib
import numpy as np
import sympy as sp
from pysr import PySRRegressor
from hypatiax.core.r2_canonical import metrics

CONDITIONS = ["pysr_only", "hypatia", "hypatia_nollm"]
REGIMES = {"near": (0.0, 0.5), "medium": (0.5, 2.0), "far": (2.0, 9.0)}
NAMES = ["Kinetic Energy", "Kinetic Energy (obf)", "Ideal Gas Law", "Michaelis-Menten", "Arrhenius"]


def Var(name, lo, hi, extrap=True):
    return (name, lo, hi, extrap)


RHO = Var("rho", -1, 1, extrap=False)


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, float) and not math.isfinite(o):
        return None
    return o


def stable_seed(seed, equation):
    return [int(seed), zlib.crc32(equation.encode())]


def git_commit():
    return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()


def versions():
    return dict(python=platform.python_version(), numpy=np.__version__)


def common_complexity(expr):
    return sum(1 for _ in sp.preorder_traversal(expr))


def cached_llm(client, model, prompt, cache_dir="llm_cache"):
    key = hashlib.sha256((model + prompt).encode()).hexdigest()
    p = pathlib.Path(cache_dir) / (key + ".json")
    if p.exists():
        return json.loads(p.read_text())["text"]
    text = client.messages.create(model=model, temperature=0, max_tokens=1000,
                                  messages=[{"role": "user", "content": prompt}]).content[0].text
    p.write_text(json.dumps({"text": text}))
    return text


def fit_pysr(X, y, seed, budget):
    m = PySRRegressor(niterations=1000000, timeout_in_seconds=budget, random_state=seed, deterministic=True,
                      parallelism="serial", temp_equation_file=True)
    m.fit(X, y)
    return m


def build_data(name, seed, sample_block):
    rng = np.random.default_rng(stable_seed(seed, name))
    Xtr, ytr = sample_block(rng, None)
    ytr_obs = ytr + rng.normal(0, 0.01 * ytr.std(), ytr.shape)
    blocks = {r: sample_block(rng, r) for r in REGIMES}
    return Xtr, ytr, ytr_obs, blocks


def main(sample_block, runners):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--budget", type=float, default=1100.0)
    a = ap.parse_args()
    for seed in range(a.seeds):
        for name in NAMES:
            Xtr, ytr, ytr_obs, blocks = build_data(name, seed, sample_block)
            for cond in CONDITIONS:
                t0 = time.time()
                rec = dict(equation=name, condition=cond, seed=seed, commit=git_commit(), versions=versions(),
                           budget_s=a.budget, error=None)
                try:
                    pred = runners[cond](Xtr, ytr_obs, seed, a.budget)
                    rec["fit_time_s"] = time.time() - t0
                    rec["llm_mode_used"] = getattr(pred, "llm_mode_used", None)
                    rec["train"] = metrics(ytr, pred.predict(Xtr))
                    rec["regimes"] = {r: metrics(blocks[r][1], pred.predict(blocks[r][0])) for r in REGIMES}
                except Exception as e:
                    rec["error"] = type(e).__name__ + ": " + str(e)
                with open("exp1_all_runs.jsonl", "a") as f:
                    f.write(json.dumps(clean(rec), allow_nan=False) + "\n")
"""


def audit_selftest(_a=None) -> int:
    failures: List[str] = []

    def mk(tmp: Path, files: Dict[str, str]):
        for rel_, txt in files.items():
            p = tmp / rel_
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(txt)

    def audit(tmp: Path):
        root = tmp
        files = discover(root, "exp1_ablation.py")
        rdir = root / "hypatiax" / "data" / "results" / "ablation"
        return run_audit(root, files, "exp1_ablation.py", rdir if rdir.exists() else None)

    # ---- buggy package: every rule must fire --------------------------------------------
    tmp = Path(tempfile.mkdtemp())
    mk(tmp, {"hypatiax/experiments/benchmarks/exp1_ablation.py": BUGGY_DRIVER,
             "hypatiax/tools/symbolic/hybrid_system_v50_2.py": BUGGY_HYBRID,
             "audit_out/merge_exp1_ablation_shards.py": BUGGY_MERGE,
             "hypatiax/data/results/ablation/exp1_ablation/exp1_ablation_results.json": '{"far": {"r2": -Infinity}}',
             "hypatiax/data/results/ablation/exp1_ablation/fixc3_baseline__shard0_rescued_1.json": "{}"})
    res = audit(tmp)
    found = {f["rule"] for f in res["findings"]}
    expected = {"D1", "D2", "D3", "D4", "D5", "D6", "R1", "R2", "R3", "R4", "M1", "M2", "M3", "M4", "M5", "M6", "F1", "F2", "F3", "F4",
                "X1", "X2", "X3", "P1", "P2", "P3", "S1", "S2", "S3", "S4", "S5", "L1", "L2"}
    missing = sorted(expected - found)
    ok1 = not missing and res["overall"] == "PHASE_ABLATION_CODE_OPEN"
    print(f"{'ok  ' if ok1 else 'FAIL'} buggy package   -> {res['overall']}; rules fired {len(found & expected)}/{len(expected)}"
          + (f"; MISSING {missing}" if missing else ""))
    if not ok1:
        failures.append("buggy")
        print("     gates:", {k: v["status"] for k, v in res["gates"].items()})
    for gname in ("A1_data_generation", "A2_regime_split", "A3_metrics", "A4_results_format", "A5_fairness", "A6_proxy_metrics",
                  "A7_statistics", "A8_recall_control"):
        if res["gates"][gname]["status"] != "FAIL":
            failures.append(f"gate {gname} not FAIL on buggy package")
            print(f"FAIL gate {gname} should FAIL on the buggy package, got {res['gates'][gname]['status']}")

    # ---- suppression comment ------------------------------------------------------------
    tmp2 = Path(tempfile.mkdtemp())
    mk(tmp2, {"hypatiax/experiments/benchmarks/exp1_ablation.py":
              "import numpy as np\nrng = np.random.default_rng()  # audit: ignore[D1]\n"})
    r2_ = audit(tmp2)
    sup_ok = not any(f["rule"] == "D1" for f in r2_["findings"])
    print(f"{'ok  ' if sup_ok else 'FAIL'} suppression     -> D1 {'suppressed' if sup_ok else 'NOT suppressed'}")
    if not sup_ok:
        failures.append("suppression")

    # ---- syntax error is reported, not fatal -------------------------------------------
    tmp3 = Path(tempfile.mkdtemp())
    mk(tmp3, {"hypatiax/experiments/benchmarks/exp1_ablation.py": "def broken(:\n"})
    r3 = audit(tmp3)
    syn_ok = any(f["rule"] == "H0" for f in r3["findings"]) and r3["overall"] == "PHASE_ABLATION_CODE_OPEN"
    print(f"{'ok  ' if syn_ok else 'FAIL'} syntax error    -> {'H0 reported' if syn_ok else 'not reported'}")
    if not syn_ok:
        failures.append("syntax")

    # ---- missing primary ----------------------------------------------------------------
    tmp4 = Path(tempfile.mkdtemp())
    mk(tmp4, {"scripts/run_phase3_ablation.py": "x = 1\n"})
    r4 = audit(tmp4)
    prim_ok = any(f["rule"] == "H1" for f in r4["findings"])
    print(f"{'ok  ' if prim_ok else 'FAIL'} primary missing -> {'H1 reported' if prim_ok else 'not reported'}")
    if not prim_ok:
        failures.append("primary")

    # ---- clean twin: nothing at or above MEDIUM ----------------------------------------
    tmp5 = Path(tempfile.mkdtemp())
    mk(tmp5, {"hypatiax/experiments/benchmarks/exp1_ablation.py": CLEAN_DRIVER, "hypatiax/core/r2_canonical.py": CLEAN_METRICS})
    r5 = audit(tmp5)
    noisy = [f for f in r5["findings"] if SEV[f["sev"]] <= SEV["MEDIUM"]]
    ok5 = not noisy and r5["overall"] in ("PHASE_ABLATION_CODE_CLOSED", "PHASE_ABLATION_CODE_CLOSED_WITH_CAVEATS")
    print(f"{'ok  ' if ok5 else 'FAIL'} clean package   -> {r5['overall']}; findings >= MEDIUM: {len(noisy)}")
    if not ok5:
        failures.append("clean")
        for f in noisy:
            print(f"     [{f['sev']}] {f['rule']} {f['file']}:{f['line']} {f['msg'][:110]}")

    # ---- outputs are strict JSON ----------------------------------------------------------
    try:
        json.loads(json.dumps(clean(res), allow_nan=False))
        print("ok   strict json     -> report serialises with allow_nan=False")
    except ValueError as e:
        failures.append("json")
        print("FAIL strict json    ->", e)

    print("SELFTEST", "PASSED" if not failures else f"FAILED: {failures}")
    return 0 if not failures else 1

def audit_args(p, out_default="phase_ablation_code_audit"):
    p.add_argument("--root", default=".")
    p.add_argument("--primary", default="exp1_ablation.py", help="the driver whose presence is required")
    p.add_argument("--extra-glob", nargs="*", default=None, help="extra files relative to --root, e.g. 'scripts/phase3_*.py'")
    p.add_argument("--include-archive", action="store_true", help="also audit files under archive/")
    p.add_argument("--include-reference", action="store_true", help="also audit exp1_multiseed.py / phase-ablation-close.py")
    p.add_argument("--files", nargs="*", default=None, help="audit exactly these files instead of auto-discovery")
    p.add_argument("--out", default=out_default, help="audit output dir (under `all`: <out-dir>/code_audit)")
    p.add_argument("--fail-on", default="HIGH", choices=list(SEV), help="audit exit 1 if any finding is at least this severe")
    p.add_argument("--results-dir", default=None, help="results tree to scan for legacy literals (default hypatiax/data/results/ablation)")
    p.add_argument("--no-results-scan", action="store_true")
    p.add_argument("--show", type=int, default=25, help="findings printed to the terminal")
    p.add_argument("--quiet", action="store_true")


# ========================================================================================
# SECTION 2 - results closure (phase4_close.py v2, gates A-K)
# ========================================================================================
import argparse
import glob
import hashlib
import importlib
import json
import math
import os
import random
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

# ----------------------------------------------------------------- pre-specified constants
THRESHOLDS = (0.99, 0.999999)
PRIMARY = 0.99
CAT_R2 = 0.0
R2_CLIP = (-1.0, 1.0)
ALPHA = 0.05
BOOT_N = 10000
BOOT_SEED = 0
WIRED = ("llm_acceptance", "pysr_prior")
UNTESTED = {
    "probe": "lives in the v3c DeFi pipeline; untested here, not shown to have no effect",
    "complexity_routing": "only gate is `if False and ...` (symbolic_engine.py:1812); identical to full by construction",
    "nn_augmentation": "lives in the v3c DeFi pipeline; untested here, not shown to have no effect",
    "blend_weight": "lives in the v3c DeFi pipeline; untested here, not shown to have no effect",
}
SPLITS = {"far": ["extrap_r2_far", "r2", "r2_raw"],
          "medium": ["extrap_r2_medium"],
          "train": ["train_r2"]}
RUNTIME_KEYS = ["runtime_s", "runtime", "elapsed_s", "time_s"]
PINNED_EVALUATOR = "7d5395ed"
CONTRASTS = [("full", "P", "full minus Pure LLM"),
             ("llm_acceptance", "full", "llm_acceptance-ablated minus full"),
             ("pysr_prior", "full", "pysr_prior-ablated minus full")]


# ----------------------------------------------------------------- helpers
def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def read_rows(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def val(row, keys):
    for k in keys:
        if k in row and row[k] is not None:
            v = fnum(row[k])
            if v is not None:
                return v
    return None


def status_ok(row):
    return row.get("status", "ok") == "ok"


def recovered(row, split, t):
    v = val(row, SPLITS[split])
    return status_ok(row) and v is not None and math.isfinite(v) and v >= t


def catastrophic(row):
    v = val(row, SPLITS["far"])
    return (not status_ok(row)) or v is None or (not math.isfinite(v)) or v < CAT_R2


def clipped(row, split):
    v = val(row, SPLITS[split])
    if (not status_ok(row)) or v is None or not math.isfinite(v):
        return R2_CLIP[0] if v is not None or not status_ok(row) else None
    return min(max(v, R2_CLIP[0]), R2_CLIP[1])


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    return None if n == 0 else (xs[n // 2] if n % 2 else 0.5 * (xs[n // 2 - 1] + xs[n // 2]))


def sd(xs):
    if len(xs) < 2:
        return None
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def sign_p(pos, neg):
    n = pos + neg
    if n == 0:
        return 1.0
    m = min(pos, neg)
    return min(1.0, 2.0 * sum(math.comb(n, i) for i in range(m + 1)) / 2 ** n)


def min_nontied(m, alpha=ALPHA):
    n = 1
    while 2.0 / 2 ** n > alpha / m:
        n += 1
    return n


def holm(pvals):
    order = sorted(pvals, key=pvals.get)
    m, adj, run = len(order), {}, 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, (m - i) * pvals[k]))
        adj[k] = run
    return adj


def boot_ci(deltas):
    if not deltas:
        return None
    rng = random.Random(BOOT_SEED)
    n = len(deltas)
    means = sorted(sum(deltas[rng.randrange(n)] for _ in range(n)) / n for _ in range(BOOT_N))
    return [means[int(0.025 * BOOT_N)], means[int(0.975 * BOOT_N) - 1]]


def git_info(ignore):
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        lines = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError):
        return "nogit", None
    dirty = [l for l in lines if not any(l[3:].strip().strip('"').startswith(p) for p in ignore)]
    return commit, dirty


# ----------------------------------------------------------------- evaluator regression tests
def _as_r2(res):
    if isinstance(res, (int, float)):
        return float(res), None
    if isinstance(res, dict):
        for k in ("r2", "r2_raw", "value"):
            if k in res and fnum(res[k]) is not None:
                return float(res[k]), res.get("status")
    if isinstance(res, (tuple, list)) and res and fnum(res[0]) is not None:
        return float(res[0]), (res[1] if len(res) > 1 else None)
    return None, None


def evaluator_tests(spec):
    """Returns (status, detail). status is PASS / FAIL / INCONCLUSIVE."""
    try:
        import numpy as np
        mod, _, fn = spec.partition(":")
        sys.path.insert(0, os.getcwd())
        f = getattr(importlib.import_module(mod), fn)
    except Exception as e:
        return "INCONCLUSIVE", f"cannot import evaluator {spec}: {type(e).__name__}: {e}"
    x = np.linspace(0, 10, 100)
    ref = lambda y, p: 1.0 - float(np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2))
    cases = []
    y1 = np.sin(x) + 2.0
    cases.append(("T1 ordinary target, perfect prediction", y1, y1.copy(), "close", 1.0, 1e-9))
    y2 = 1e-7 * np.sin(x)
    cases.append(("T2 tiny-variance target (ss_tot < 1e-10), perfect prediction", y2, y2.copy(), "close", 1.0, 1e-6))
    p3 = y2 + 0.1 * float(y2.std()) * np.cos(7 * x)
    cases.append(("T3 tiny-variance target, imperfect prediction", y2, p3, "close", ref(y2, p3), 1e-3))
    y4 = np.full(100, 3.0)
    cases.append(("T4 constant target, wrong prediction", y4, y4 + 1.0, "not_good", None, None))
    problems, notes = [], []
    for name, y, p, mode, expect, tol in cases:
        try:
            r, st = _as_r2(f(y, p))
        except Exception as e:
            return "INCONCLUSIVE", f"evaluator call failed on '{name}': {type(e).__name__}: {e}"
        if r is None:
            return "INCONCLUSIVE", f"unrecognised evaluator return shape on '{name}'"
        if mode == "close":
            ok = math.isfinite(r) and abs(r - expect) <= tol
        else:
            ok = (not math.isfinite(r)) or r < 0.99
        notes.append(f"{name}: r2={r!r} status={st!r} -> {'ok' if ok else 'BAD'}")
        if not ok:
            problems.append(name)
    return ("FAIL" if problems else "PASS"), "; ".join(notes)


# ----------------------------------------------------------------- M3 / M4 decision (Step 5)
def m34_decision(label, pattern):
    files = sorted(glob.glob(pattern)) if pattern else []
    base = {"label": label, "files": files}
    if not files:
        return {**base, "rows": 0, "decision": "EXPLORATORY_OR_OMIT",
                "reasons": ["no controlled rerun supplied: drop headline claims or label them exploratory"]}
    try:
        rows = [r for f in files for r in read_rows(f)]
    except (OSError, ValueError) as e:
        return {**base, "rows": 0, "decision": "EXPLORATORY_OR_OMIT", "reasons": [f"unreadable: {e}"]}
    reasons = []
    if not rows:
        reasons.append("no rows")
    n_ok = [r for r in rows if status_ok(r)]
    k = sum(1 for r in n_ok if not r.get("formula"))
    if k:
        reasons.append(f"{k} ok rows have no formula (output not inspectable)")
    for key in ("generation_path", "llm_called", "bypass_used"):
        k = sum(1 for r in rows if key not in r or r[key] is None)
        if k:
            reasons.append(f"{k} rows lack {key}")
    k = sum(1 for r in rows if r.get("bypass_used") is True or "bypass" in str(r.get("generation_path", "")).lower())
    if k:
        reasons.append(f"{k} rows used a bypass")
    if any(r.get("clean_run") is not True for r in rows):
        reasons.append("clean_run not True on every row")
    commits = {r.get("git_commit") for r in rows}
    if len(commits) != 1 or None in commits:
        reasons.append("git_commit not single/present")
    if any(r.get("code_dirty") is not False for r in rows):
        reasons.append("code_dirty not False on every row")
    return {**base, "rows": len(rows), "sha256": {f: sha_file(f) for f in files},
            "decision": "EXPLORATORY_OR_OMIT" if reasons else "CONFIRMED", "reasons": reasons}


# ----------------------------------------------------------------- analysis
def per_equation(rows, split, t):
    acc = defaultdict(list)
    for r in rows:
        acc[r["equation"]].append(1.0 if recovered(r, split, t) else 0.0)
    return {e: sum(v) / len(v) for e, v in acc.items()}


def per_equation_r2(rows, split):
    acc = defaultdict(list)
    for r in rows:
        c = clipped(r, split)
        if c is not None:
            acc[r["equation"]].append(c)
    return {e: sum(v) / len(v) for e, v in acc.items()}


def summarise(rows):
    out = {"n_cases": len(rows)}
    for split in SPLITS:
        avail = [r for r in rows if val(r, SPLITS[split]) is not None]
        s = {"n_with_value": len(avail)}
        if avail:
            for t in THRESHOLDS:
                k = sum(recovered(r, split, t) for r in rows)
                s[f"recovery@{t}"] = {"k": k, "n": len(rows), "rate": k / len(rows)}
            fin = [val(r, SPLITS[split]) for r in avail if status_ok(r) and math.isfinite(val(r, SPLITS[split]))]
            s["median_r2_ok_rows"] = median(fin)
        out[split] = s
    k = sum(catastrophic(r) for r in rows)
    out["catastrophic"] = {"k": k, "n": len(rows), "rate": k / len(rows) if rows else None,
                           "definition": f"status!=ok or far non-finite or far < {CAT_R2}"}
    out["status_counts"] = {s: sum(1 for r in rows if r.get("status", "ok") == s)
                            for s in sorted({r.get("status", "ok") for r in rows})}
    rt = [fnum(r[k]) for r in rows for k in RUNTIME_KEYS if k in r and fnum(r[k]) is not None][:len(rows)]
    out["runtime_s"] = {"n": len(rt), "total": sum(rt) if rt else None, "median": median(rt)}
    seeds = sorted({int(r["seed"]) for r in rows})
    rates = []
    for sd_ in seeds:
        sub = [r for r in rows if int(r["seed"]) == sd_]
        rates.append(sum(recovered(r, "far", PRIMARY) for r in sub) / len(sub))
    out["seed_variability_far@primary"] = {"seeds": seeds, "rates": rates, "sd": sd(rates)}
    return out


def contrast(a_rows, b_rows):
    """A minus B at equation level; returns list of dict, one per (split, metric)."""
    res = []
    for split in SPLITS:
        if not any(val(r, SPLITS[split]) is not None for r in a_rows) or \
           not any(val(r, SPLITS[split]) is not None for r in b_rows):
            continue
        for t in THRESHOLDS:
            a, b = per_equation(a_rows, split, t), per_equation(b_rows, split, t)
            eqs = sorted(set(a) & set(b))
            d = [a[e] - b[e] for e in eqs]
            pos, neg = sum(x > 0 for x in d), sum(x < 0 for x in d)
            res.append({"split": split, "metric": f"recovery@{t}", "n_equations": len(eqs),
                        "A_better": pos, "B_better": neg, "tied": len(d) - pos - neg,
                        "mean_delta": sum(d) / len(d) if d else None, "ci95": boot_ci(d),
                        "p_sign": sign_p(pos, neg)})
        a, b = per_equation_r2(a_rows, split), per_equation_r2(b_rows, split)
        eqs = sorted(set(a) & set(b))
        d = [a[e] - b[e] for e in eqs]
        pos, neg = sum(x > 0 for x in d), sum(x < 0 for x in d)
        res.append({"split": split, "metric": "clipped_r2", "n_equations": len(eqs),
                    "A_better": pos, "B_better": neg, "tied": len(d) - pos - neg,
                    "mean_delta": sum(d) / len(d) if d else None, "ci95": boot_ci(d),
                    "p_sign": sign_p(pos, neg)})
    return res


# ----------------------------------------------------------------- output writers
def tex_esc(s):
    return str(s).replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")


def write_tex(path, summ, paired):
    L = [r"% generated by phase4_close.py; do not edit by hand",
         r"\begin{tabular}{lrrrrrr}", r"\toprule",
         r"Config & n & far@0.99 & far@0.999999 & medium@0.99 & train@0.99 & catastrophic\\", r"\midrule"]

    def rate(s, sp, t):
        d = s.get(sp, {}).get(f"recovery@{t}")
        return "n/a" if d is None else f"{d['k']}/{d['n']}"
    for c, s in summ.items():
        L.append(f"{tex_esc(c)} & {s['n_cases']} & {rate(s,'far',0.99)} & {rate(s,'far',0.999999)} & "
                 f"{rate(s,'medium',0.99)} & {rate(s,'train',0.99)} & {s['catastrophic']['k']}/{s['catastrophic']['n']}\\\\")
    L += [r"\bottomrule", r"\end{tabular}", "", r"\medskip", "",
          r"\begin{tabular}{llrrrrr}", r"\toprule",
          r"Contrast (A$-$B) & Kind & A better & B better & tied & $p$ (Holm) & mean $\Delta$\\", r"\midrule"]
    for p in paired:
        if p["split"] == "far" and p["metric"] == f"recovery@{PRIMARY}":
            L.append(f"{tex_esc(p['contrast'])} & {p['kind']} & {p['A_better']} & {p['B_better']} & {p['tied']} & "
                     f"{p['p_holm']:.3f} & {p['mean_delta']:+.3f}\\\\")
    L += [r"\bottomrule", r"\end{tabular}"]
    Path(path).write_text("\n".join(L) + "\n", encoding="utf-8")


def write_csv(path, rows, cols):
    lines = [",".join(cols)]
    for r in rows:
        lines.append(",".join("" if r.get(c) is None else json.dumps(r[c]) if isinstance(r[c], (list, dict)) else str(r[c]) for c in cols))
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


# ----------------------------------------------------------------- main
def run(a):
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    seeds = [int(s) for s in a.seeds.split(",") if s.strip()]
    gates = []

    def gate(gid, status, detail):
        gates.append({"id": gid, "status": status, "detail": detail})
        print(f"  [{status}] {gid} - {detail}")

    # ---- load
    p3 = Path(a.phase3_dir)
    files = {"full": p3 / "full.jsonl", **{c: p3 / f"{c}.jsonl" for c in WIRED}}
    p_files = sorted(glob.glob(a.p_rows))
    missing = [str(f) for f in files.values() if not f.exists()]
    if missing or not p_files:
        print(f"missing inputs: {missing or ''} {'(no P rows for ' + a.p_rows + ')' if not p_files else ''}", file=sys.stderr)
        return 2, None
    data = {k: read_rows(f) for k, f in files.items()}
    data["P"] = [r for f in p_files for r in read_rows(f)]
    sources = {**{k: str(f) for k, f in files.items()}, "P": p_files}

    print("== PHASE 4 CLOSURE")
    # ---- A inputs and coverage
    want = {(None, s) for s in seeds}
    problems = []
    keys = {}
    for k, rows in data.items():
        for r in rows:
            for need in ("equation", "seed"):
                if need not in r:
                    print(f"{k}: row lacks '{need}'; keys: {sorted(r)}", file=sys.stderr)
                    return 2, None
        if not any(val(r, SPLITS['far']) is not None for r in rows):
            print(f"{k}: no far-split R2 under {SPLITS['far']}; first row keys: {sorted(rows[0]) if rows else []}", file=sys.stderr)
            return 2, None
        ks = [(r["equation"], int(r["seed"])) for r in rows]
        if len(ks) != len(set(ks)):
            problems.append(f"{k}: duplicate (equation, seed)")
        keys[k] = set(ks)
    full_keys = keys["full"]
    eqs = sorted({e for e, _ in full_keys})
    exp = {(e, s) for e in eqs for s in seeds}
    if len(eqs) != a.n_equations:
        problems.append(f"full has {len(eqs)} equations, expected {a.n_equations}")
    for k in keys:
        if not exp <= keys[k]:
            problems.append(f"{k}: missing {len(exp - keys[k])} of {len(exp)} (equation, seed) pairs")
    gate("A inputs and coverage", "FAIL" if problems else "PASS",
         "; ".join(problems) or f"{len(exp)} pairs x {len(data)} configs present ({len(eqs)} equations, seeds {seeds})")
    for k in data:  # restrict to the expected grid
        data[k] = [r for r in data[k] if (r["equation"], int(r["seed"])) in exp]

    # ---- B provenance of Phase 3 rows
    p3rows = [r for k in ("full", *WIRED) for r in data[k]]
    bad = []
    commits = {r.get("git_commit") for r in p3rows}
    if len(commits) != 1 or None in commits:
        bad.append(f"git_commit not single/present: {sorted(map(str, commits))}")
    if any(r.get("code_dirty") is not False for r in p3rows):
        bad.append("code_dirty not False on every row")
    if any(r.get("clean_run") is not True for r in p3rows):
        bad.append("clean_run not True on every row")
    if any(r.get("bypass_used") or "bypass" in str(r.get("generation_path", "")).lower() for r in p3rows):
        bad.append("bypass used on some rows")
    if any(status_ok(r) and r.get("llm_called") is not True for r in data["full"]):
        bad.append("an ok full row has llm_called != True")
    pb = [r for r in data["P"] if r.get("bypass_used") is True]
    if pb:
        bad.append(f"{len(pb)} P rows have bypass_used True")
    note = "" if any("bypass_used" in r for r in data["P"]) else " (P rows carry no bypass_used; covered by Phase 2 closure)"
    gate("B provenance (single commit, clean, no bypass, live LLM)", "FAIL" if bad else ("WARN" if note else "PASS"),
         "; ".join(bad) or f"commit {next(iter(commits))[:7]}, {len(p3rows)} rows clean{note}")

    # ---- C evaluator pin
    shas = {str(r.get("evaluator_sha256", ""))[:8] for r in p3rows}
    msg = []
    if shas != {a.expected_evaluator_sha[:8]}:
        msg.append(f"row evaluator shas {sorted(shas)}, want {a.expected_evaluator_sha[:8]}")
    if Path(a.evaluator_path).exists():
        fs = sha_file(a.evaluator_path)[:8]
        if fs != a.expected_evaluator_sha[:8]:
            msg.append(f"file {a.evaluator_path} sha {fs}")
    else:
        msg.append(f"{a.evaluator_path} not found")
    gate("C evaluator pin", "FAIL" if msg else "PASS", "; ".join(msg) or f"sha {a.expected_evaluator_sha[:8]} on rows and file")

    # ---- D r2 == extrap_r2_far (G2)
    dif = [r for r in p3rows if "r2" in r and "extrap_r2_far" in r and r["r2"] is not None and r["extrap_r2_far"] is not None
           and not (fnum(r["r2"]) == fnum(r["extrap_r2_far"]) or abs(fnum(r["r2"]) - fnum(r["extrap_r2_far"])) <= 1e-12)]
    nboth = sum(1 for r in p3rows if "r2" in r and "extrap_r2_far" in r)
    gate("D r2 == extrap_r2_far (G2)", "FAIL" if dif or nboth == 0 else "PASS",
         f"{len(dif)} mismatching rows" if dif else (f"{nboth} rows compared" if nboth else "no row carries both fields"))

    # ---- E data parity
    def hashes(rows):
        return {(r["equation"], int(r["seed"])): (r.get("train_data_sha256"), r.get("far_data_sha256")) for r in rows}
    hf = hashes(data["full"])
    mism = [(k, e) for k in WIRED for e, h in hashes(data[k]).items() if hf.get(e) != h]
    hp = hashes(data["P"])
    pcomp = [e for e in hf if hp.get(e, (None, None))[0] is not None and hp[e][0] != "unknown"]
    pm = [e for e in pcomp if hp[e] != hf[e]]
    detail = f"{len(mism)} Phase 3 hash mismatches"
    detail += f"; P compared on {len(pcomp)} pairs, {len(pm)} mismatches" if pcomp else "; P rows carry no data hashes (Phase 2 closure covers P vs HDS parity)"
    gate("E data parity across configs", "FAIL" if mism or pm else ("WARN" if not pcomp else "PASS"), detail)

    # ---- F Phase 3 closure artefact
    cl = Path(a.phase3_closure) if a.phase3_closure else None
    if cl is None or not cl.exists():
        gate("F Phase 3 closure artefact", "FAIL", "pass --phase3-closure <file from phase3_closure_out/>; Phase 4 builds on a closed Phase 3")
    else:
        verdict = "format not recognised; sha recorded"
        st = "PASS"
        try:
            j = json.loads(cl.read_text(encoding="utf-8"))
            for k in ("closed", "ok", "passed"):
                if isinstance(j, dict) and k in j:
                    st, verdict = ("PASS" if j[k] is True else "FAIL"), f"{k}={j[k]!r}"
                    break
            else:
                for k in ("verdict", "status", "result"):
                    if isinstance(j, dict) and k in j:
                        txt = str(j[k]).upper()
                        st = "FAIL" if ("NOT" in txt or "FAIL" in txt or "OPEN" in txt) else "PASS"
                        verdict = f"{k}={j[k]!r}"
                        break
        except (OSError, ValueError):
            verdict = "not JSON; existence and sha recorded"
        gate("F Phase 3 closure artefact", st, f"{cl} sha {sha_file(cl)[:8]}; {verdict}")

    # ---- G evaluator regression tests
    if a.skip_evaluator_tests:
        gate("G evaluator regression tests", "INCONCLUSIVE", "skipped by --skip-evaluator-tests (counts as not closed)")
    else:
        st, d = evaluator_tests(a.evaluator)
        gate("G evaluator regression tests", st, d)

    # ---- analysis
    summ = {k: summarise(data[k]) for k in ("P", "full", *WIRED)}
    paired, pv = [], {}
    for A, B, label in CONTRASTS:
        for r in contrast(data[A], data[B]):
            r.update({"contrast": label, "A": A, "B": B, "kind": "exploratory"})
            if r["split"] == "far" and r["metric"] == f"recovery@{PRIMARY}":
                r["kind"] = "confirmatory"
                pv[label] = r["p_sign"]
            paired.append(r)
    adj = holm(pv) if pv else {}
    for r in paired:
        r["p_holm"] = adj.get(r["contrast"]) if r["kind"] == "confirmatory" else None
    mn = min_nontied(len(CONTRASTS))
    conf = {r["A"]: r for r in paired if r["kind"] == "confirmatory"}
    power = []
    for A in WIRED:
        r = conf.get(A)
        nt = None if r is None else r["A_better"] + r["B_better"]
        power.append({"gate": A, "non_tied_equations": nt, "needed_for_holm": mn,
                      "statement": ("underpowered: cannot reach Holm-level significance" if nt is not None and nt < mn
                                    else "power sufficient to reach Holm-level significance if the effect is consistent")})
    gate("H power statement", "PASS", "; ".join(f"{p['gate']}: {p['non_tied_equations']} non-tied of {mn} needed" for p in power))

    commit, dirty = git_info([a.out_dir.rstrip("/") + "/", "phase3_out", "phase3_closure_out", "p2_"])
    if dirty is None:
        gate("I phase4 tree clean", "WARN", "git not available")
    elif dirty and not a.allow_dirty:
        gate("I phase4 tree clean", "FAIL", f"{len(dirty)} changed paths, e.g. {dirty[:3]}")
    else:
        gate("I phase4 tree clean", "PASS" if not dirty else "WARN", f"HEAD {commit[:7]}" + (" (dirty accepted)" if dirty else ""))

    m34 = {"M3": m34_decision("M3", a.m3_rows), "M4": m34_decision("M4", a.m4_rows)}
    exploratory = [k for k, v in m34.items() if v["decision"] != "CONFIRMED"]
    gate("J M3/M4 decision (Step 5)", "WARN" if exploratory else "PASS",
         "; ".join(f"{k}: {v['decision']}" + (f" ({'; '.join(v['reasons'])})" if v["reasons"] else "") for k, v in m34.items()))

    ar = getattr(a, "audit_result", None)
    if ar is None:
        gate("K code audit (static)", "WARN", "not run in this invocation; use the `all` subcommand to audit the code and close together")
    else:
        n_hi = sum(1 for f in ar["findings"] if f["sev"] in ("CRITICAL", "HIGH"))
        st = {"PHASE_ABLATION_CODE_CLOSED": "PASS", "PHASE_ABLATION_CODE_CLOSED_WITH_CAVEATS": "WARN"}.get(ar["overall"])
        enforce = getattr(a, "audit_gate", "report") == "block"
        if st is None:
            st = "FAIL" if enforce else "WARN"
        gate("K code audit (static)", st,
             f"{ar['overall']}: {n_hi} critical/high of {len(ar['findings'])} findings in {len(ar['files'])} files"
             + (" (recorded, NOT blocking; --audit-gate block enforces it)" if st == "WARN" and ar["overall"].endswith("OPEN") else ""))

    closed = all(g["status"] in ("PASS", "WARN") for g in gates)
    verdict = "CLOSED" if closed else "NOT CLOSED"

    # ---- write
    results = {
        "verdict": verdict, "gates": gates,
        "definitions": {"thresholds": THRESHOLDS, "primary": PRIMARY, "catastrophic_r2": CAT_R2, "r2_clip": R2_CLIP,
                        "unit": "equation (seeds averaged)", "confirmatory": "far@primary, Holm over 3, exact sign test"},
        "summary": summ, "paired": paired, "power": power, "m34_decision": m34,
        "code_audit": None if ar is None else {"overall": ar["overall"], "n_findings": len(ar["findings"]),
                                               "gates": {k: v["status"] for k, v in ar["gates"].items()}},
        "untested_gates": UNTESTED,
        "claim_limits": [
            "Only llm_acceptance and pysr_prior are ablated; the four others are untested, not 'no effect'.",
            "Unreachable ablation rows tie by construction and carry no evidence.",
            "No repeat-full noise-floor control exists; seed-to-seed variation is reported but not separated from run noise.",
            "pysr_prior seed removal was verified manually, not from rows.",
            "M3/M4: a claim may be headline only if its decision above is CONFIRMED; otherwise drop it or label it exploratory.",
            "The noise-sweep evidence is not checked by this script: label it exploratory until verified against the code.",
            "Manuscript numbers must be generated from phase4_results.json / the CSVs, never copied by hand.",
            "The static code audit finding PASS means no known bad pattern, not proof of correctness; this results closure is the regression test."],
        "git_commit": commit,
    }
    (out / "phase4_results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    write_csv(out / "config_summary.csv",
              [{"config": c, "n": s["n_cases"],
                **{f"{sp}@{t}": (s[sp].get(f"recovery@{t}") or {}).get("rate") for sp in SPLITS for t in THRESHOLDS},
                "catastrophic_rate": s["catastrophic"]["rate"], "runtime_total_s": s["runtime_s"]["total"],
                "seed_sd_far@primary": s["seed_variability_far@primary"]["sd"]} for c, s in summ.items()],
              ["config", "n"] + [f"{sp}@{t}" for sp in SPLITS for t in THRESHOLDS] +
              ["catastrophic_rate", "runtime_total_s", "seed_sd_far@primary"])
    write_csv(out / "paired.csv", paired,
              ["contrast", "kind", "split", "metric", "n_equations", "A_better", "B_better", "tied", "mean_delta", "ci95", "p_sign", "p_holm"])
    write_csv(out / "per_equation.csv",
              [{"config": k, "equation": e, "far@0.99": per_equation(data[k], "far", 0.99).get(e),
                "far@0.999999": per_equation(data[k], "far", 0.999999).get(e)} for k in summ for e in eqs],
              ["config", "equation", "far@0.99", "far@0.999999"])
    write_tex(out / "phase4_tables.tex", summ, paired)
    ledger = {"script": sha_file(__file__), "git_commit": commit,
              "inputs": {k: ([{"path": f, "sha256": sha_file(f)} for f in v] if isinstance(v, list)
                             else {"path": v, "sha256": sha_file(v)}) for k, v in sources.items()},
              "outputs": {f: sha_file(out / f) for f in ("phase4_results.json", "config_summary.csv", "paired.csv",
                                                         "per_equation.csv", "phase4_tables.tex")},
              "evidence_labels": {"confirmatory": [r["contrast"] for r in paired if r["kind"] == "confirmatory"],
                                  "exploratory": "all other contrasts, splits, thresholds",
                                  "m34": {k: v["decision"] for k, v in m34.items()},
                                  "planned_or_unverified": ["noise-sweep evidence", "untested gates"]
                                                           + [f"{k} headline claims" for k in exploratory]}}
    if ar is not None and getattr(a, "audit_json", None) and Path(a.audit_json).exists():
        ledger["code_audit"] = {"overall": ar["overall"], "path": str(a.audit_json), "sha256": sha_file(a.audit_json)}
    (out / "claim_ledger.json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    (out / "phase4_closure.json").write_text(json.dumps({"verdict": verdict, "gates": gates, "git_commit": commit}, indent=2),
                                             encoding="utf-8")
    print(f"\nPHASE 4 {verdict}  (outputs in {out}/)")
    for c, s in summ.items():
        fr = s["far"].get(f"recovery@{PRIMARY}")
        print(f"  {c:16s} far@{PRIMARY}: {fr['k']}/{fr['n']}  catastrophic {s['catastrophic']['k']}/{s['catastrophic']['n']}"
              if fr else f"  {c:16s} no far data")
    return (0 if closed else 1), results


# ----------------------------------------------------------------- selftest
def _stub_evaluator(d, guard):
    body = ("import numpy as np\n"
            "def r2_checked(y, p):\n"
            "    y=np.asarray(y,float); p=np.asarray(p,float)\n"
            "    sst=float(np.sum((y-y.mean())**2))\n")
    body += ("    if sst <= 1e-10: return (float('nan'), 'degenerate')\n" if guard == "absolute"
             else "    if sst <= 1e-12*max(1.0, float(np.mean(y**2))*len(y)*0) and float(np.ptp(y))==0.0: return (float('nan'), 'degenerate')\n")
    body += "    return (1.0 - float(np.sum((y-p)**2))/sst, 'ok')\n"
    p = Path(d) / ("stub_" + guard + ".py")
    p.write_text(body, encoding="utf-8")
    return p.stem


def close_selftest():
    d = Path(tempfile.mkdtemp(prefix="p4_selftest_"))
    rng = random.Random(1)
    eqs = [f"Eq{i:02d}" for i in range(15)]
    seeds = [42, 99, 123]
    (d / "p3").mkdir()
    (d / "p2").mkdir()
    ev = d / "r2_canonical.py"
    ev.write_text("# evaluator stand-in\n", encoding="utf-8")
    esha = sha_file(ev)

    def row(eq, s, comp, r2, **kw):
        return {"status": "ok", "equation": eq, "seed": s, "r2": r2, "extrap_r2_far": r2, "extrap_r2_medium": r2,
                "train_r2": min(1.0, r2 + 0.01), "runtime_s": 100.0, "formula": "f", "generation_path": "hds_live",
                "llm_called": True, "bypass_used": False, "clean_run": True, "code_dirty": False, "git_commit": "c" * 40,
                "evaluator_sha256": esha, "ablated_component": comp,
                "train_data_sha256": f"t{eq}{s}", "far_data_sha256": f"f{eq}{s}", **kw}
    for comp in ("full", *WIRED):
        rows = []
        for i, e in enumerate(eqs):
            for s in seeds:
                r2 = 0.9999 if (i % 3 != 0 or (comp == "pysr_prior" and i in (3, 6))) else 0.5
                rows.append(row(e, s, None if comp == "full" else comp, r2))
        (d / "p3" / f"{comp}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    for s in seeds:
        rows = [{"status": "ok", "equation": e, "seed": s, "r2": 0.9999 if i % 2 == 0 else 0.3, "runtime_s": 5.0}
                for i, e in enumerate(eqs)]
        (d / "p2" / f"pure_llm_seed{s}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    (d / "closure.json").write_text(json.dumps({"verdict": "CLOSED"}), encoding="utf-8")
    good, bad = _stub_evaluator(d, "relative"), _stub_evaluator(d, "absolute")
    base = ["--phase3-dir", str(d / "p3"), "--p-rows", str(d / "p2" / "pure_llm_seed*.jsonl"),
            "--evaluator-path", str(ev), "--expected-evaluator-sha", esha[:8], "--phase3-closure", str(d / "closure.json"),
            "--allow-dirty", "--out-dir"]
    sys.path.insert(0, str(d))
    ok = True
    m4 = [{"status": "ok", "equation": e, "seed": 42, "formula": "f", "generation_path": "hds_live", "llm_called": True,
           "bypass_used": False, "clean_run": True, "code_dirty": False, "git_commit": "c" * 40} for e in eqs]
    (d / "m4_good.jsonl").write_text("".join(json.dumps(r) + "\n" for r in m4), encoding="utf-8")
    m3 = [{**r, "formula": None} for r in m4]
    (d / "m3_bad.jsonl").write_text("".join(json.dumps(r) + "\n" for r in m3), encoding="utf-8")
    code, res = run(parse(base + [str(d / "out_good"), "--evaluator", f"{good}:r2_checked",
                                  "--m4-rows", str(d / "m4_good.jsonl"), "--m3-rows", str(d / "m3_bad.jsonl")]))
    ok &= code == 0 and res["verdict"] == "CLOSED"
    ok &= res["m34_decision"]["M4"]["decision"] == "CONFIRMED" and res["m34_decision"]["M3"]["decision"] == "EXPLORATORY_OR_OMIT"
    print(f"selftest good evaluator -> exit {code} (want 0)\n")
    code, res = run(parse(base + [str(d / "out_bad"), "--evaluator", f"{bad}:r2_checked"]))
    ok &= code == 1 and any(g["id"].startswith("G") and g["status"] == "FAIL" for g in res["gates"])
    print(f"selftest absolute-guard evaluator -> exit {code} (want 1, gate G FAIL)\n")
    code, res = run(parse(base + [str(d / "out_skip"), "--skip-evaluator-tests"]))
    ok &= code == 1
    print(f"selftest skipped evaluator tests -> exit {code} (want 1)\n")
    # corrupt provenance: a bypass row must fail B
    rows = read_rows(d / "p3" / "full.jsonl")
    rows[0]["bypass_used"] = True
    (d / "p3" / "full.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    code, res = run(parse(base + [str(d / "out_byp"), "--evaluator", f"{good}:r2_checked"]))
    ok &= code == 1 and any(g["id"].startswith("B") and g["status"] == "FAIL" for g in res["gates"])
    print(f"selftest bypass row -> exit {code} (want 1, gate B FAIL)\n")
    print("SELFTEST", "PASSED" if ok else "FAILED", f"(files in {d})")
    return 0 if ok else 1


def close_args(ap):
    ap.add_argument("--phase3-dir", default="phase3_out", help="holds full.jsonl, llm_acceptance.jsonl, pysr_prior.jsonl")
    ap.add_argument("--p-rows", default="p2/pure_llm_seed*.jsonl", help="Phase 2 Pure-LLM rows (glob)")
    ap.add_argument("--phase3-closure", default=None, help="file from phase3_closure_out/ proving Phase 3 closed")
    ap.add_argument("--m3-rows", default=None, help="glob of controlled M3 rerun rows (omit if none exist)")
    ap.add_argument("--m4-rows", default=None, help="glob of controlled M4 rerun rows (omit if none exist)")
    ap.add_argument("--out-dir", default="phase4_closure_out")
    ap.add_argument("--seeds", default="42,99,123")
    ap.add_argument("--n-equations", type=int, default=15)
    ap.add_argument("--evaluator", default="hypatiax.core.r2_canonical:r2_checked", help="module:function under test")
    ap.add_argument("--evaluator-path", default="hypatiax/core/r2_canonical.py")
    ap.add_argument("--expected-evaluator-sha", default=PINNED_EVALUATOR)
    ap.add_argument("--skip-evaluator-tests", action="store_true", help="records INCONCLUSIVE: the run is then NOT CLOSED")
    ap.add_argument("--allow-dirty", action="store_true")
    ap.add_argument("--audit-gate", choices=["report", "block"], default="report",
                    help="static code audit OPEN: report = record as WARN (default), block = FAIL the closure")


def parse(argv=None):
    ap = argparse.ArgumentParser(description="Phase 4 results closure")
    close_args(ap)
    return ap.parse_args(argv)


# ========================================================================================
# SECTION 3 - unified CLI
# ========================================================================================
def cmd_close(a) -> int:
    code, _ = run(a)
    return code


def cmd_all(a) -> int:
    if not a.out:
        a.out = str(Path(a.out_dir) / "code_audit")
    cmd_audit(a)                                  # prints and writes the audit; gate K applies the policy
    a.audit_result = LAST_AUDIT
    a.audit_json = Path(a.out) / "phase_ablation_code_audit.json"
    return cmd_close(a)


def unified_selftest() -> int:
    ok = audit_selftest() == 0
    print()
    ok &= close_selftest() == 0
    print()
    # wiring of gate K: an audit that is OPEN (no primary driver) must be WARN by default and FAIL under block
    d = Path(tempfile.mkdtemp(prefix="p4u_selftest_"))
    ar_root = d / "pkg"
    ar_root.mkdir()
    (ar_root / "x.py").write_text("x = 1\n")
    ap = argparse.ArgumentParser()
    audit_args(ap)
    aa = ap.parse_args(["--root", str(ar_root), "--out", str(d / "audit"), "--quiet", "--no-results-scan"])
    cmd_audit(aa)
    ok &= LAST_AUDIT is not None and LAST_AUDIT["overall"] == "PHASE_ABLATION_CODE_OPEN"
    print(f"selftest gate K wiring: audit result {LAST_AUDIT['overall'] if LAST_AUDIT else None} (want OPEN)")
    print("UNIFIED SELFTEST", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    close_args(sub.add_parser("close", help="results closure (gates A-J; K reports 'not run')"))
    audit_args(sub.add_parser("audit", help="static code audit of the Exp-1 ablation package"))
    audit_args(sub.add_parser("list", help="show which files the audit would read"))
    p_all = sub.add_parser("all", help="code audit, then results closure with the audit as gate K")
    audit_args(p_all, out_default=None)
    close_args(p_all)
    sub.add_parser("selftest", help="audit selftest + closure selftest + gate K wiring")
    a = ap.parse_args(argv)
    if a.cmd == "selftest":
        return unified_selftest()
    if a.cmd == "audit":
        return cmd_audit(a)
    if a.cmd == "list":
        return cmd_list(a)
    if a.cmd == "close":
        return cmd_close(a)
    return cmd_all(a)


if __name__ == "__main__":
    sys.exit(main())
