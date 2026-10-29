#!/usr/bin/env python3
"""
scan_repo.py -- static error scan for LLM-HypatiaX-REPRO/hypatiax

Usage (from repo root):
    python3 scan_repo.py                      # scans ./hypatiax
    python3 scan_repo.py --root . --target hypatiax --report scan_report.txt
    python3 scan_repo.py --strict             # warnings also fail the exit code

Checks
  ERROR   python syntax errors / merge-conflict markers
  ERROR   unresolved local imports (hypatiax.* module file does not exist)
  ERROR   undefined names (needs `pip install pyflakes`; skipped if absent)
  ERROR   shell scripts failing `bash -n`
  ERROR   YAML / JSON files that do not parse
  ERROR   clean-run violations: code that sets/forces HYPATIAX_DISABLE_* to 0,
          or repro.yaml / run_all.sh / CI missing the flags
  ERROR   script paths in config/repro.yaml that do not exist
  ERROR   fail-open flag reads, prompt-hint leaks, live hardcoded bypass, absolute/offset-relative
          ss_tot evaluator guards (defects found auditing baseline_pure_llm_defi_discovery.py)
  WARN    model-string drift vs repro.yaml, unresolvable 3rd-party imports, -inf/nan JSON dumps,
          '*_deterministic' helpers that send no temperature
  WARN    bare `except:`, `except Exception: pass`, mutable default args,
          duplicate top-level function/class definitions, `== None`,
          hard-coded absolute home paths, TODO/FIXME/XXX markers (counted)
Exit code: 1 if any ERROR (or any WARN with --strict), else 0.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache",
             ".pytest_cache", ".ipynb_checkpoints", "build", "dist", ".eggs"}
FLAGS = ("HYPATIAX_DISABLE_HARDCODED", "HYPATIAX_DISABLE_PROMPT_HINTS")

findings: list[tuple[str, str, str, int, str]] = []  # (level, check, file, line, msg)


def add(level, check, path, line, msg):
    findings.append((level, check, str(path), line, msg))


def walk(root: Path, suffixes):
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in suffixes and not (set(p.parts) & SKIP_DIRS):
            yield p


def is_test_file(p: Path) -> bool:
    return p.name.startswith("test_") or p.name.endswith("_test.py") or "tests" in p.parts


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        add("ERROR", "io", p, 0, f"cannot read: {e}")
        return ""


# ───────────────────────── Python ─────────────────────────
def module_exists(repo: Path, dotted: str) -> bool:
    base = repo.joinpath(*dotted.split("."))
    return base.with_suffix(".py").exists() or (base / "__init__.py").exists() or base.is_dir()


def check_python(repo: Path, target: Path):
    pyflakes_ok = True
    try:
        import pyflakes.api  # noqa: F401
    except ImportError:
        pyflakes_ok = False
        add("WARN", "tooling", "-", 0, "pyflakes not installed -> undefined-name check skipped "
                                       "(pip install pyflakes)")

    todo = Counter()
    for p in walk(target, {".py"}):
        src = read(p)
        conflicts: list[int] = []
        # merge-conflict markers (level decided after parsing: inside a string/comment is harmless)
        for i, line in enumerate(src.splitlines(), 1):
            if re.match(r"^(<{7}|={7}|>{7})( |$)", line):
                conflicts.append(i)
            if re.search(r"\b(TODO|FIXME|XXX)\b", line):
                todo[str(p)] += 1
            if re.search(r"['\"]/(home|Users)/[A-Za-z0-9_.-]+/", line):
                add("WARN", "abs-path", p, i, "hard-coded absolute home path")
            # clean-run violations
            for f in FLAGS:
                if f in line and re.search(rf"{f}['\"]?\s*(\]\s*)?(=|,)\s*['\"]?0['\"]?", line) \
                        and "==" not in line and "!=" not in line:
                    if is_test_file(p):  # tests deliberately exercise the =0 / legacy path
                        continue
                    add("ERROR", "clean-run", p, i, f"{f} set to 0 in code")

        try:
            tree = ast.parse(src, filename=str(p))
        except SyntaxError as e:
            for ci in conflicts:
                add("ERROR", "merge-conflict", p, ci, "conflict marker (file does not parse)")
            add("ERROR", "syntax", p, e.lineno or 0, f"{e.msg}")
            continue
        if conflicts:
            add("WARN", "merge-conflict-like", p, conflicts[0],
                f"{len(conflicts)} conflict-looking line(s) {conflicts[:6]}, but the file parses -> probably inside "
                f"a string/comment; open the file and confirm no real merge is pending")

        top_defs = defaultdict(list)
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    add("WARN", "bare-except", p, node.lineno, "bare `except:`")
                elif (isinstance(node.type, ast.Name) and node.type.id in ("Exception", "BaseException")
                      and len(node.body) == 1 and isinstance(node.body[0], ast.Pass)):
                    add("WARN", "swallowed-exc", p, node.lineno, "`except Exception: pass` hides errors")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for d in node.args.defaults + [x for x in node.args.kw_defaults if x]:
                    if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                        add("WARN", "mutable-default", p, node.lineno, f"{node.name}(): mutable default arg")
            elif isinstance(node, ast.Compare):
                for op, c in zip(node.ops, node.comparators):
                    if isinstance(op, (ast.Eq, ast.NotEq)) and isinstance(c, ast.Constant) and c.value is None:
                        add("WARN", "eq-none", p, node.lineno, "use `is None` / `is not None`")
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                if node.module.split(".")[0] == "hypatiax" and not module_exists(repo, node.module):
                    add("ERROR", "import", p, node.lineno, f"unresolved import: {node.module}")
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.split(".")[0] == "hypatiax" and not module_exists(repo, a.name):
                        add("ERROR", "import", p, node.lineno, f"unresolved import: {a.name}")
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                top_defs[node.name].append(node.lineno)
        for name, lines in top_defs.items():
            if len(lines) > 1:
                add("WARN", "duplicate-def", p, lines[1],
                    f"`{name}` defined {len(lines)}x (lines {lines}); earlier ones are shadowed")

        if pyflakes_ok:
            import io
            import pyflakes.api
            import pyflakes.reporter

            out, err = io.StringIO(), io.StringIO()
            pyflakes.api.check(src, str(p), pyflakes.reporter.Reporter(out, err))
            for ln in out.getvalue().splitlines():
                m = re.match(r".*?:(\d+):(?:\d+:?)? (.*)", ln)
                if not m:
                    continue
                msg = m.group(2)
                if "undefined name" in msg:
                    add("ERROR", "undefined-name", p, int(m.group(1)), msg)
                elif "imported but unused" in msg or "unable to detect undefined" in msg:
                    continue  # noise; skip
                elif "undefined" in msg or "syntax" in msg.lower():
                    add("ERROR", "pyflakes", p, int(m.group(1)), msg)

    if todo:
        add("WARN", "todo", "-", 0, f"{sum(todo.values())} TODO/FIXME/XXX markers in {len(todo)} files "
                                    f"(top: {', '.join(f'{Path(k).name}={v}' for k, v in todo.most_common(3))})")


# ───────────────────────── Shell / YAML / JSON ─────────────────────────
def check_shell(root: Path):
    for p in walk(root, {".sh"}):
        r = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True)
        if r.returncode:
            add("ERROR", "bash-syntax", p, 0, r.stderr.strip().splitlines()[0] if r.stderr else "bash -n failed")


def check_yaml_json(root: Path):
    try:
        import yaml
    except ImportError:
        yaml = None
        add("WARN", "tooling", "-", 0, "PyYAML missing -> YAML checks skipped")
    for p in walk(root, {".yml", ".yaml", ".json"}):
        txt = read(p)
        try:
            if p.suffix == ".json":
                json.loads(txt)
            elif yaml:
                # GitHub workflows may contain ${{ }} -- still valid YAML
                list(yaml.safe_load_all(txt))
        except Exception as e:  # noqa: BLE001
            size = p.stat().st_size
            note = " [EMPTY FILE: interrupted write / failed shard rescue -> regenerate]" if size == 0 else f" [{size} bytes]"
            add("ERROR", "parse", p, getattr(getattr(e, "problem_mark", None), "line", 0) + 1,
                f"{type(e).__name__}: {str(e).splitlines()[0][:100]}{note}")


# ───────────────────────── Project-specific ─────────────────────────
def check_repro_config(repo: Path):
    cfg = repo / "config" / "repro.yaml"
    if not cfg.exists():
        add("ERROR", "config", cfg, 0, "config/repro.yaml missing")
        return
    try:
        import yaml
        data = yaml.safe_load(cfg.read_text())
    except Exception:
        return  # reported by check_yaml_json
    for name, b in (data.get("benchmarks") or {}).items():
        sc = (b or {}).get("script")
        if b and b.get("enabled") and sc and not (repo / sc).exists():
            add("ERROR", "config-path", cfg, 0, f"benchmarks.{name}.script not found: {sc}")
    lp = data.get("llm_provenance") or {}
    for key in ("disable_hardcoded", "disable_prompt_hints"):
        if lp.get(key) != 1:
            add("ERROR", "clean-run", cfg, 0, f"llm_provenance.{key} != 1")


def check_pipeline_flags(repo: Path):
    for fn in ("run_all.sh",):
        p = repo / fn
        if p.exists():
            t = read(p)
            for f in FLAGS:
                if not re.search(rf"export\s+{f}=", t):
                    add("ERROR", "clean-run", p, 0, f"{f} is never exported")
    for p in list((repo / ".github" / "workflows").glob("*.y*ml")) + list(repo.glob("ci_runner_repro.yml")):
        t = read(p)
        for f in FLAGS:
            if f in t and not re.search(rf'{f}:\s*"?1"?', t):
                add("WARN" if "audit" in p.name.lower() else "ERROR", "clean-run", p, 0,
                    f"{f} present but not set to 1"
                    + (" [audit workflow: confirm =0 is intentional and its results never feed headline tables]"
                       if "audit" in p.name.lower() else ""))
            if re.search(rf'{f}:\s*"?0"?', t):
                add("WARN" if "audit" in p.name.lower() else "ERROR", "clean-run", p, 0, f"{f} set to 0")



# ───────────────────────── Repo-specific (from baseline audit) ─────────────────────────
MODEL_RE = re.compile(r"claude-[a-z0-9]+(?:-[a-z0-9]+)*-\d[\w.-]*|claude-[a-z]+-\d(?:-\d+)?")
HINT_MARKERS = ("MANDATORY CODE TEMPLATE", "FORMULA HINT")


def check_repo_specific(repo: Path, target: Path):
    """Defects found by auditing baseline_pure_llm_defi_discovery.py, generalised."""
    # model string declared in repro.yaml
    cfg_model = None
    try:
        import yaml
        cfg_model = (yaml.safe_load((repo / "config" / "repro.yaml").read_text()) or {}).get("llm_model")
    except Exception:  # noqa: BLE001
        pass

    local_tops = {d.name for d in repo.iterdir() if d.is_dir()} | {f.stem for f in repo.glob("*.py")}
    # flat sibling imports (import hypatia / import hybrid_system_nn_defi_domain) resolve via sys.path
    local_tops |= {f.stem for f in repo.rglob("*.py") if not (set(f.parts) & SKIP_DIRS)}
    stdlib = getattr(sys, "stdlib_module_names", set())
    import importlib.util
    missing_3p = defaultdict(list)
    models_seen = defaultdict(list)

    for p in walk(target, {".py"}):
        src = read(p)
        lines = src.splitlines()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue

        # (a) fail-open flag reads: environ.get(FLAG, "")  /  default "0"
        for i, ln in enumerate(lines, 1):
            for f in FLAGS:
                if f in ln and re.search(r"(environ\.get|getenv)\(\s*['\"]%s['\"]\s*(,\s*['\"](0|)['\"])?\s*\)" % f, ln):
                    add("ERROR", "fail-open-flag", p, i,
                        f"{f} read with unset/0 default -> clean-run protection silently OFF when "
                        f"run outside run_all.sh (default must be 1)")

        # (a2) generic helper form: environ.get(name, "") in a file that handles the flags
        if any(f in src for f in FLAGS):
            for i, ln in enumerate(lines, 1):
                if re.search(r"environ\.get\(\s*name\s*,\s*['\"]['\"]\s*\)", ln) \
                        or re.search(r"getenv\(\s*name\s*(,\s*['\"]['\"])?\s*\)", ln):
                    add("ERROR", "fail-open-flag", p, i,
                        "flag helper treats an UNSET variable as OFF -> hints/bypass active outside run_all.sh")

        # (b) hint/template strings present but flag never consulted in the file
        if any(m in src for m in HINT_MARKERS) and "HYPATIAX_DISABLE_PROMPT_HINTS" not in src:
            add("ERROR", "prompt-leak", p, 0,
                "prompt hint templates present but HYPATIAX_DISABLE_PROMPT_HINTS is never checked")
        # (b2) ground-truth literal in a prompt tail that is not under the flag
        for i, ln in enumerate(lines, 1):
            ctx = "\n".join(lines[max(0, i - 4):i])
            if "sqrt(2*pi)" in ln and "e.g." in ln and "_norm_hint" not in ctx:
                add("WARN", "prompt-leak", p, i,
                    "closed-form formula literal inside prompt text; confirm it is gated by the hints flag")

        # (c) hardcoded-formula bypass must be a no-op
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_try_hardcoded_formula":
                for r in ast.walk(node):
                    if isinstance(r, ast.Return) and not (r.value is None or
                            (isinstance(r.value, ast.Constant) and r.value.value is None)):
                        add("ERROR", "hardcoded-bypass", p, r.lineno,
                            "_try_hardcoded_formula returns a value -> LLM bypass is live")

        # (d) evaluator constant-target guard
        for i, ln in enumerate(lines, 1):
            if re.search(r"ss_tot\s*>\s*1e-\d+", ln):
                add("WARN" if is_test_file(p) else "ERROR", "evaluator", p, i,
                    "absolute ss_tot guard (Supplement A Fix 5 / Listing 8 defect)"
                    + (" [test file: reference copy or stale re-implementation?]" if is_test_file(p) else ""))
            if re.search(r"_scale\s*=.*max\(np\.abs\(y_true\)\)\s*\*\*\s*2", ln):
                add("ERROR", "evaluator", p, i,
                    "constant-target tolerance is relative to max|y|^2 (offset), not spread: "
                    "a wrong prediction on y=1e6+N(0,1) scores R2=1.0")

        # (c2) files that generate formulas and may short-circuit the LLM, without consulting the flag
        if re.search(r"def\s+\w*(generate|get)_?\w*formula\w*\s*\(", src) and \
                re.search(r"hardcoded|HARDCODED|_GT_BRANCHES|known_formulas|GROUND_TRUTH_FORMULAS", src) and \
                "HYPATIAX_DISABLE_HARDCODED" not in src:
            add("ERROR", "hardcoded-bypass", p, 0,
                "formula generator mentions hardcoded/ground-truth branches but never checks "
                "HYPATIAX_DISABLE_HARDCODED (candidate for the report's '11 bypassed rows')")

        # (e) model-string drift vs repro.yaml
        for i, ln in enumerate(lines, 1):
            if "claude-" in ln and not ln.lstrip().startswith("#"):
                for m in MODEL_RE.findall(ln):
                    models_seen[m].append((p, i))

        # (f) third-party imports that do not resolve
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module.split(".")[0]]
            for n in names:
                if n in stdlib or n in local_tops or n == "hypatiax":
                    continue
                try:
                    if importlib.util.find_spec(n) is None:
                        missing_3p[n].append(p)
                except (ImportError, ValueError):
                    missing_3p[n].append(p)

        # (g) results JSON written with default allow_nan while -inf/nan are possible
        if re.search(r'float\(["\']-?inf["\']\)|float\(["\']nan["\']\)', src) and "json.dump" in src \
                and "allow_nan=False" not in src:
            add("WARN", "json-nan", p, 0,
                "emits -inf/nan and json.dump()s them -> non-standard JSON (Infinity/NaN) breaks strict parsers")

        # (h) docs claiming determinism where temperature is not sent
        if re.search(r"def\s+\w*_deterministic\w*\s*\(", src) and "temperature" not in re.sub(r"#.*|\"\"\".*?\"\"\"", "", src, flags=re.S):
            add("WARN", "determinism", p, 0,
                "function named *_deterministic but no temperature/seed is sent; run-to-run LLM variance expected")

    if cfg_model and models_seen:
        for m, locs in models_seen.items():
            resolver = "def resolve_model" in read(locs[0][0])  # file reads repro.yaml itself
            if m != cfg_model and not resolver:
                p, i = locs[0]
                add("WARN", "model-drift", p, i,
                    f"model '{m}' ({len(locs)} site(s)) != repro.yaml llm_model '{cfg_model}'")
    for n, ps in missing_3p.items():
        add("WARN", "missing-dep", ps[0], 0, f"third-party module '{n}' not importable here ({len(ps)} file(s))")


def run_tests(repo: Path, pattern: str):
    tests = sorted(p for p in repo.rglob(pattern) if not (set(p.parts) & SKIP_DIRS))
    if not tests:
        add("WARN", "tests", "-", 0, f"no files match --tests '{pattern}'")
        return
    seen = defaultdict(list)
    for t in tests:
        seen[t.name].append(t)
    for name, paths in seen.items():
        if len(paths) > 1:
            add("WARN", "tests", paths[1], 0, f"duplicate test file {name} in {len(paths)} places "
                f"({', '.join(str(x.parent.relative_to(repo)) for x in paths)}) -> keep one")
    for t in tests:  # one process per file: avoids basename collisions between duplicate test modules
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider", str(t)],
                           capture_output=True, text=True, cwd=t.parent)
        if r.returncode == 5:
            add("WARN", "tests", t, 0, "pytest collected 0 tests")
        elif r.returncode != 0:
            tail = [l for l in (r.stdout or r.stderr).strip().splitlines() if l.strip()][-1:] or ["failed"]
            add("ERROR", "tests", t, 0, f"pytest failed: {tail[0]}")


# ───────────────────────── Main ─────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="repo root")
    ap.add_argument("--target", default="hypatiax", help="package dir relative to root")
    ap.add_argument("--report", default="scan_report.txt")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--run-tests", action="store_true", help="also run pytest")
    ap.add_argument("--tests", default="test_baseline_regressions.py",
                    help="glob of test files for --run-tests (default: the baseline regression tests)")
    ap.add_argument("--verbose", action="store_true", help="do not collapse repetitive warnings per file")
    a = ap.parse_args()

    repo = Path(a.root).resolve()
    target = repo / a.target
    if not target.is_dir():
        sys.exit(f"target not found: {target}")
    sys.path.insert(0, str(repo))

    check_python(repo, target)
    check_shell(repo)
    check_yaml_json(repo)
    check_repro_config(repo)
    check_pipeline_flags(repo)
    check_repo_specific(repo, target)
    if a.run_tests:
        run_tests(repo, a.tests)

    if not a.verbose:
        noisy = {"swallowed-exc", "bare-except", "json-nan", "eq-none", "abs-path", "mutable-default"}
        grouped = defaultdict(list)
        keep = []
        for f in findings:
            (grouped[(f[0], f[1], f[2])] if f[0] == "WARN" and f[1] in noisy else keep).append(f) \
                if f[0] == "WARN" and f[1] in noisy else keep.append(f)
        for (lvl, chk, fp), items in grouped.items():
            lines_ = [str(i[3]) for i in items if i[3]]
            keep.append((lvl, chk, fp, items[0][3], f"{len(items)}x {items[0][4]}"
                         + (f" (lines {','.join(lines_[:8])}{'...' if len(lines_) > 8 else ''})" if lines_ else "")))
        findings[:] = keep

    order = {"ERROR": 0, "WARN": 1}
    findings.sort(key=lambda f: (order[f[0]], f[1], f[2], f[3]))
    errs = sum(f[0] == "ERROR" for f in findings)
    warns = len(findings) - errs
    lines = [f"{lvl:5} [{chk}] {Path(fp).relative_to(repo) if fp.startswith(str(repo)) else fp}"
             f"{':' + str(ln) if ln else ''}  {msg}" for lvl, chk, fp, ln, msg in findings]
    summary = f"\n== {errs} error(s), {warns} warning(s) in {a.target}/ =="
    out = "\n".join(lines) + summary
    print(out)
    Path(a.report).write_text(out + "\n")
    print(f"report written to {a.report}")
    sys.exit(1 if errs or (a.strict and warns) else 0)


if __name__ == "__main__":
    main()
