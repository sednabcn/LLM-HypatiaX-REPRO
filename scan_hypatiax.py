#!/usr/bin/env python3
"""Scan LLM-HypatiaX-REPRO/hypatiax for errors.

Usage (from repo root):
    python3 scan_hypatiax.py                # scan ./hypatiax
    python3 scan_hypatiax.py --root path    # custom repo root
    python3 scan_hypatiax.py --json out.json

Checks:
  1. Python syntax errors (ast.parse)
  2. pyflakes findings (undefined names, unused imports) if pyflakes is installed
  3. Unresolvable intra-package imports (hypatiax.*)
  4. Risky patterns: bare except, silent 'except ...: pass'
  5. Flag audit: HYPATIAX_DISABLE_HARDCODED / HYPATIAX_DISABLE_PROMPT_HINTS
     - fail-open defaults (get(..., "0") / default False)
     - run_all.sh, CI workflows and shell scripts must export both =1
  6. bash -n on *.sh, YAML parse on workflows/configs, JSON validity (non-results)
Exit code: 1 if any ERROR, else 0.
"""
import argparse, ast, json, os, re, subprocess, sys
from pathlib import Path

FLAGS = ("HYPATIAX_DISABLE_HARDCODED", "HYPATIAX_DISABLE_PROMPT_HINTS")
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache",
             ".pytest_cache", "build", "dist", ".ipynb_checkpoints"}
SKIP_PATH_PARTS = ("data/results",)  # large generated outputs

findings = []  # (severity, category, path, line, message)


def add(sev, cat, path, line, msg):
    findings.append((sev, cat, str(path), line, msg))


def walk(root, exts):
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        if any(p in dp.replace("\\", "/") for p in SKIP_PATH_PARTS):
            continue
        for fn in fns:
            if fn.endswith(exts):
                yield Path(dp) / fn


def check_python(repo, pkg):
    py_files = list(walk(pkg, (".py",)))
    modules = set()
    for f in py_files:
        rel = f.relative_to(repo).with_suffix("")
        parts = list(rel.parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        modules.add(".".join(parts))
    have_pyflakes = subprocess.run([sys.executable, "-m", "pyflakes", "--version"],
                                   capture_output=True).returncode == 0
    if not have_pyflakes:
        add("INFO", "pyflakes", pkg, 0, "pyflakes not installed (pip install pyflakes) - skipped")

    for f in py_files:
        try:
            src = f.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            add("ERROR", "read", f, 0, str(e)); continue
        try:
            tree = ast.parse(src, filename=str(f))
        except SyntaxError as e:
            add("ERROR", "syntax", f, e.lineno or 0, f"{e.msg}"); continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    add("WARN", "bare-except", f, node.lineno, "bare 'except:'")
                body = node.body
                if len(body) == 1 and isinstance(body[0], ast.Pass):
                    add("WARN", "silent-except", f, node.lineno, "exception swallowed with 'pass'")
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0 \
                    and node.module.split(".")[0] == "hypatiax":
                if node.module not in modules:
                    add("ERROR", "import", f, node.lineno, f"module not found: {node.module}")
                else:
                    sub = [a.name for a in node.names if a.name != "*"]
                    for n in sub:
                        full = f"{node.module}.{n}"
                        if full in modules:
                            continue
                        mod_file = next((m for m in py_files
                                         if m.relative_to(repo).with_suffix("").as_posix().replace("/", ".")
                                         .removesuffix(".__init__") == node.module), None)
                        if mod_file and not re.search(rf"\b(def|class)\s+{re.escape(n)}\b|^\s*{re.escape(n)}\s*=|import\s+.*\b{re.escape(n)}\b",
                                                      mod_file.read_text(errors="replace"), re.M):
                            add("WARN", "import", f, node.lineno, f"'{n}' not obviously defined in {node.module}")
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.split(".")[0] == "hypatiax" and a.name not in modules:
                        add("ERROR", "import", f, node.lineno, f"module not found: {a.name}")

        # flag audit (python)
        for i, line in enumerate(src.splitlines(), 1):
            for flag in FLAGS:
                if flag in line:
                    if re.search(rf"get\(\s*['\"]{flag}['\"]\s*,\s*['\"]?(0|false|)['\"]?\s*\)", line, re.I) \
                            or re.search(rf"get\(\s*['\"]{flag}['\"]\s*\)", line):
                        add("ERROR", "flag-fail-open", f, i,
                            f"{flag} defaults to OFF - must fail closed (default '1')")
        if have_pyflakes:
            r = subprocess.run([sys.executable, "-m", "pyflakes", str(f)], capture_output=True, text=True)
            for ln in (r.stdout + r.stderr).splitlines():
                m = re.match(r".*?:(\d+):(?:\d+:?)?\s*(.*)", ln)
                if not m:
                    continue
                msg = m.group(2)
                sev = "ERROR" if re.search(r"undefined name|syntax|invalid|redefinition of unused.*from line", msg) else "INFO"
                if sev == "INFO" and "imported but unused" in msg:
                    continue  # noise
                add(sev, "pyflakes", f, int(m.group(1)), msg)
    return py_files


def files_reading_flags(py_files):
    return {str(f) for f in py_files if any(fl in f.read_text(errors="replace") for fl in FLAGS)}


def check_shell_and_ci(repo):
    targets = [p for p in repo.glob("*.sh")] + list((repo / "hypatiax").rglob("*.sh")) \
        + list((repo / ".github" / "workflows").glob("*.y*ml")) if (repo / ".github").exists() \
        else list(repo.glob("*.sh"))
    seen_launcher = False
    for f in targets:
        if any(p in str(f).replace("\\", "/") for p in SKIP_PATH_PARTS):
            continue
        txt = f.read_text(errors="replace")
        is_ci = f.suffix in (".yml", ".yaml")
        if f.suffix == ".sh":
            r = subprocess.run(["bash", "-n", str(f)], capture_output=True, text=True)
            if r.returncode:
                add("ERROR", "shell-syntax", f, 0, r.stderr.strip()[:300])
        if f.name == "run_all.sh" or is_ci:
            seen_launcher = True
            for flag in FLAGS:
                m = re.search(rf"{flag}\s*[:=]\s*['\"]?(\w+)", txt)
                if not m:
                    add("ERROR", "flag-missing", f, 0, f"{flag} not set")
                elif m.group(1) != "1":
                    add("ERROR", "flag-wrong", f, 0, f"{flag}={m.group(1)} (must be 1)")
                elif f.suffix == ".sh" and not re.search(rf"export\s+{flag}\b", txt):
                    add("ERROR", "flag-not-exported", f, 0, f"{flag} set but not 'export'ed - children won't see it")
        if is_ci:
            try:
                import yaml
                yaml.safe_load(txt)
            except ImportError:
                pass
            except Exception as e:
                add("ERROR", "yaml", f, 0, str(e)[:300])
    if not seen_launcher:
        add("WARN", "flag-missing", repo, 0, "no run_all.sh / CI workflow found to audit")


def check_json_yaml(pkg):
    for f in walk(pkg, (".json",)):
        try:
            json.loads(f.read_text(encoding="utf-8", errors="replace"))
        except Exception as e:
            add("ERROR", "json", f, 0, str(e)[:200])
    for f in walk(pkg, (".yaml", ".yml")):
        try:
            import yaml
            yaml.safe_load(f.read_text(errors="replace"))
        except ImportError:
            break
        except Exception as e:
            add("ERROR", "yaml", f, 0, str(e)[:200])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="repo root (contains hypatiax/)")
    ap.add_argument("--json", help="write findings to this JSON file")
    ap.add_argument("--quiet-info", action="store_true")
    a = ap.parse_args()
    repo = Path(a.root).resolve()
    pkg = repo / "hypatiax"
    if not pkg.is_dir():
        sys.exit(f"hypatiax/ not found under {repo}")

    py_files = check_python(repo, pkg)
    readers = files_reading_flags(py_files)
    if not readers:
        add("ERROR", "flag-unconsumed", pkg, 0,
            "no Python file under hypatiax/ reads the HYPATIAX_DISABLE_* flags - exporting them has no effect")
    check_shell_and_ci(repo)
    check_json_yaml(pkg)

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    findings.sort(key=lambda x: (order[x[0]], x[1], x[2], x[3]))
    counts = {k: 0 for k in order}
    for sev, cat, path, line, msg in findings:
        counts[sev] += 1
        if sev == "INFO" and a.quiet_info:
            continue
        rel = os.path.relpath(path, repo)
        print(f"[{sev:5}] {cat:16} {rel}:{line}  {msg}")
    print(f"\n{len(py_files)} Python files scanned | "
          f"{counts['ERROR']} errors, {counts['WARN']} warnings, {counts['INFO']} info")
    print(f"Files reading the flags: {len(readers)}")
    if a.json:
        Path(a.json).write_text(json.dumps(
            [dict(severity=s, category=c, path=p, line=l, message=m) for s, c, p, l, m in findings], indent=1))
    sys.exit(1 if counts["ERROR"] else 0)


if __name__ == "__main__":
    main()
