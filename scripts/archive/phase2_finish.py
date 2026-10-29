#!/usr/bin/env python3
"""phase2_finish.py (v3) - run every Phase 2 caveat check that can be automated.

Save as scripts/phase2_finish.py and run from the repo root:

    python scripts/phase2_finish.py --all
    python scripts/phase2_finish.py --steps dirty rows evaluator   # subset
    python scripts/phase2_finish.py --all --declare "rows/G3=env flags not recorded; export line in shell history only"

Steps (each prints a status and is written to phase2_finish_out/report.json):
  dirty      what differed from the P commit; untracked runner files (sha256 + mtime evidence);
             does the config that ran (rows' config_sha256) match the working file?          (G8)
  rows       45 rows, one commit, prompt TEMPLATE hash, per-equation rendered prompt hash, one timeout,
             one model, bypass evidence, schema validation + proposed schema                 (G3,G4,G6,G8,G9)
  evaluator  committed r2_canonical blob hash == P rows' evaluator_sha256, file clean        (G7)
  hashes     G1: control (current tree) + generator at each HDS commit (git worktree) + generator diff
  closures   medium, train and call-1 closures for P through check_closure_nonfinite.py
  runtime    does runtime_s cover LLM time? worst-case bound against the time cap
  engine     is engine_version "5.4" assigned inside hybrid_system_v50_2.py?
  binder     did the post-hoc binder rule touch any real row? (P candidates with defaulted params)
  listing8   prints the ss_tot guard actually used by the evaluator and by the supplement text
  amend      writes a draft amendment A5 with the outcomes (never touches phase2_pure_llm_amendments.md)

Statuses
  PASS       check holds.
  EXPLAINED  does not hold literally, cause identified and evidence recorded. Goes into A5.
  DECLARED   FAIL/MANUAL that you chose to accept with --declare KEY=reason. The reason is stored verbatim in A5.
  FAIL       real problem, or evidence missing.
  MANUAL     needs a human read; the evidence is written to phase2_finish_out/.

It cannot make dirty P rows retroactively clean. Standard library only (jsonschema, pyyaml optional).

v3 changes (second real run): untracked runner files handled (and no longer re-flagged once committed), config evidence
computed before any early return, call-1 closure uses the row system label, schema step proposes enum additions and shows
the runner's own --validate output, G1 adds a generator diff between the HDS and P commits plus call-path greps, binder
step answers "did it matter?", listing8 prints the real guard, new DECLARED status.
"""
import argparse, collections, datetime, glob, hashlib, json, os, re, shutil, statistics, subprocess, sys, tempfile
from pathlib import Path

RESULTS = []  # (step, status, message)
STATE = {}
DECLARED = {}
CRITICAL = ("baseline_pure_llm", "symbolic_engine", "hybrid_system_v50_2", "r2_canonical", "p2_data",
            "run_pure_llm_arm", "exp1_ablation", "prompt", "phase2_pure_llm_config", "requirements")
CODE_EXT = (".py", ".yaml", ".yml", ".toml", ".cfg", ".txt")


def say(step, status, msg):
    if status in ("FAIL", "MANUAL"):
        for k, why in DECLARED.items():
            if step == k or step.startswith(k):
                status, msg = "DECLARED", f"{msg} || DECLARED CAVEAT: {why}"
                break
    RESULTS.append((step, status, msg))
    print(f"[{status}] {step}: {msg}")


def run(cmd, cwd=None, env=None, check=False):
    p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    if check and p.returncode:
        raise RuntimeError(f"{' '.join(cmd)}\n{p.stdout}\n{p.stderr}")
    return p


def git(args, root):
    return run(["git", "-C", str(root)] + args)


def git_raw(root, args):
    return subprocess.run(["git", "-C", str(root)] + args, capture_output=True).stdout


def load_rows(pattern):
    rows = []
    for f in sorted(glob.glob(pattern)):
        for ln in open(f, encoding="utf-8"):
            if ln.strip():
                r = json.loads(ln)
                r["_file"] = f
                rows.append(r)
    return rows


def p_rows(a):
    return load_rows(str(a.p2 / "pure_llm_*.jsonl"))


def fail_lines(text, n=8):
    return [l.strip() for l in text.splitlines() if re.match(r"\s*(\[FAIL\]|FAIL)", l)][:n]


def p_commit(a):
    if a.p_commit:
        return a.p_commit
    cs = {str(r.get("git_commit", "")).replace("+dirty", "") for r in p_rows(a)} - {""}
    return cs.pop() if len(cs) == 1 else "11c8cc3"


def config_hash_variants(raw):
    """The runner's hashing scheme is unknown to this script, so try the plausible ones."""
    out = {"raw-bytes": hashlib.sha256(raw).hexdigest()}
    try:
        import yaml
        obj = yaml.safe_load(raw.decode("utf-8"))
        for name, kw in (("json-sorted", {"sort_keys": True}),
                         ("json-sorted-compact", {"sort_keys": True, "separators": (",", ":")}),
                         ("json-sorted-default-str", {"sort_keys": True, "default": str})):
            out[name] = hashlib.sha256(json.dumps(obj, **kw).encode("utf-8")).hexdigest()
    except Exception:
        pass
    return out


def _mtime(p):
    return datetime.datetime.fromtimestamp(Path(p).stat().st_mtime).isoformat(timespec="seconds")


# ---------------------------------------------------------------- steps
def step_dirty(a):
    root, cfg = a.repo_root, a.config_path
    commit = p_commit(a)
    STATE["p_commit"] = commit
    rows = p_rows(a)
    if rows and not any(str(r.get("git_commit", "")).endswith("+dirty") for r in rows):
        STATE["dirty_explained"] = True
        return say("dirty", "PASS", "P rows are not marked +dirty")
    if git(["cat-file", "-e", commit + "^{commit}"], root).returncode:
        return say("dirty", "FAIL", f"commit {commit} not found in this clone (git fetch?)")
    names = git(["diff", "--name-only", commit], root).stdout.split()
    untracked = git(["ls-files", "--others", "--exclude-standard"], root).stdout.split()
    patch = a.out / "dirty_vs_p_commit.patch"
    patch.write_text(git(["diff", commit], root).stdout, encoding="utf-8")
    (a.out / "dirty_vs_p_commit.stat.txt").write_text(
        git(["diff", "--stat", commit], root).stdout + "\n--- git status --short ---\n" + git(["status", "--short"], root).stdout +
        "\n--- untracked ---\n" + "\n".join(untracked), encoding="utf-8")

    def crit(n):
        return n.endswith(CODE_EXT) and any(k in n for k in CRITICAL)

    allowed = set(a.runner_files)
    hits = [n for n in names if crit(n)]
    u_hits = [n for n in untracked if crit(n)]
    other = [n for n in hits if n != cfg and n not in allowed]
    u_other = [n for n in u_hits if n not in allowed]
    if other or u_other:
        parts = []
        if other:
            parts.append(f"tracked run-critical files differ from {commit[:8]}: {other}")
        if u_other:
            parts.append(f"run-critical files not under version control: {u_other}")
        return say("dirty", "FAIL", "; ".join(parts) + f". The P rows are not tied to a commit. If these are the runner "
                   f"files, pass them with --runner-files; otherwise commit/record them or rerun under a logged amendment. Patch: {patch}")

    # evidence for the runner files (the code that actually produced the rows)
    row_files = sorted(glob.glob(str(a.p2 / "pure_llm_*.jsonl")))
    first_rows = min((Path(f).stat().st_mtime for f in row_files), default=None)
    ev, newer = [], False
    for n in sorted(allowed):
        pth = root / n
        if not pth.exists():
            continue
        sha = hashlib.sha256(pth.read_bytes()).hexdigest()
        in_commit = git(["cat-file", "-e", f"{commit}:{n}"], root).returncode == 0
        if first_rows is None:
            when = ""
        elif pth.stat().st_mtime < first_rows:
            when = ", older than the first P row file"
        else:
            when, newer = ", NEWER than the first P row file", True
        ev.append(f"{n} sha256={sha[:16]}.. mtime={_mtime(pth)} {'UNTRACKED' if n in untracked else 'tracked'}"
                  f"{'' if in_commit else ', absent from ' + commit[:8]}{when}")
    STATE["runner_evidence"] = ev
    for e in ev:
        print("  runner file: " + e)

    cfg_state, cfg_note = "none", ""
    if cfg in hits:
        d = git(["diff", commit, "--", cfg], root).stdout.splitlines()
        changed = [l for l in d if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        print(f"  config diff vs {commit[:8]} ({len(changed)} changed lines):")
        for l in changed[:40]:
            print("   " + l)
        want = {r.get("config_sha256") for r in rows} - {None}
        work_v = config_hash_variants((root / cfg).read_bytes())
        comm_v = config_hash_variants(git_raw(root, ["show", f"{commit}:{cfg}"]))
        mw = [k for k, v in work_v.items() if v in want]
        mc = [k for k, v in comm_v.items() if v in want]
        if mw:
            cfg_state, cfg_note = "working", f"{cfg} differs from the commit ({len(changed)} lines) and its hash ({mw[0]}) equals the rows' config_sha256, so the config that ran is the working file"
        elif mc:
            cfg_state, cfg_note = "committed", f"rows' config_sha256 matches the COMMITTED {cfg}; it was edited after the run"
        else:
            cfg_state, cfg_note = "unknown", f"{cfg} differs and the rows' config_sha256 matches neither version under {sorted(work_v)}"
    if not names and not u_hits:
        return say("dirty", "MANUAL", f"tree equals {commit[:8]} now but rows say +dirty; whatever was dirty at run time is gone. "
                   "Check git reflog/stash and state it in A5, or rerun under a logged amendment")
    if cfg_state in ("committed", "unknown") or newer:
        return say("dirty", "MANUAL", "; ".join(x for x in [cfg_note, "; ".join(ev) if newer else ""] if x) +
                   ". Cannot show the working files are what ran. See dirty_vs_p_commit.stat.txt")
    STATE["dirty_explained"] = True
    say("dirty", "EXPLAINED", f"dirty marker explained by: {cfg_note + '; ' if cfg_note else ''}runner files not committed at {commit[:8]} "
        f"[{'; '.join(ev) or 'none'}]. 'Unchanged since the run' is inferred from mtimes, not proven. Commit them now "
        f"(git add {' '.join(sorted(allowed))} {cfg}), and put these hashes plus phase2_finish_out/dirty_vs_p_commit.patch in A5")


def step_rows(a):
    rows = p_rows(a)
    if not rows:
        return say("rows", "FAIL", f"no rows at {a.p2}/pure_llm_*.jsonl")
    keys = collections.Counter((r.get("equation"), r.get("seed")) for r in rows)
    dup = [k for k, v in keys.items() if v > 1]
    say("rows/G6", "PASS" if len(rows) == 45 and not dup else "FAIL", f"{len(rows)} rows, duplicates={dup}")

    def single(field, step, label):
        vals = collections.Counter(str(r.get(field)) for r in rows)
        say(step, "PASS" if len(vals) == 1 and "None" not in vals else "FAIL", f"{label} ({field}): {dict(vals)}")

    single("git_commit", "rows/G8", "single commit")
    dirty = [r for r in rows if str(r.get("git_commit", "")).endswith("+dirty")]
    cd = collections.Counter(str(r.get("code_dirty")) for r in rows)
    if dirty or cd.get("True"):
        st = "EXPLAINED" if STATE.get("dirty_explained") else "FAIL"
        say("rows/G8", st, f"dirty rows: {len(dirty)}; code_dirty values: {dict(cd)} (None = field not recorded). "
            f"{'Cause identified in the dirty step; put it in A5.' if st == 'EXPLAINED' else 'See the dirty step.'}")
    else:
        say("rows/G8", "PASS", f"no dirty rows; code_dirty values: {dict(cd)}")
    single("timeout_s", "rows/G4", "one timeout")
    single("model_id_returned", "rows/G7", "one model id")

    pk = sorted({k for r in rows for k in r if "prompt" in k.lower() and ("sha" in k.lower() or "hash" in k.lower())})
    tmpl = [k for k in pk if "template" in k.lower()]
    rend = [k for k in pk if k not in tmpl]
    if not tmpl:
        say("rows/G4", "FAIL", f"no prompt TEMPLATE hash field found (keys seen: {pk})")
    for k in tmpl:
        single(k, "rows/G4", "one prompt template hash")
    for k in rend:
        by_eq = collections.defaultdict(set)
        for r in rows:
            by_eq[r.get("equation")].add(str(r.get(k)))
        bad = [e for e, v in by_eq.items() if len(v) != 1]
        distinct = {next(iter(v)) for v in by_eq.values() if len(v) == 1}
        say("rows/G4", "FAIL" if bad else "PASS",
            f"rendered prompt hash ({k}) is per-equation by design: {len(distinct)} distinct values for {len(by_eq)} equations, " +
            (f"but differs across seeds for {bad[:5]}" if bad else "identical across seeds within each equation"))

    # G3: bypass evidence
    flag_keys = sorted({k for r in rows for k in r if any(s in k.lower() for s in ("bypass", "flag", "disable", "hint", "hardcod"))})
    kinds = dict(collections.Counter(str(r.get("bypass_kind")) for r in rows))
    llm = dict(collections.Counter(str(r.get("llm_attempted")) for r in rows))
    flags = collections.Counter(json.dumps(r.get("bypass_flags"), sort_keys=True) for r in rows)
    if "null" not in flags and len(flags) == 1:
        bad = [k for k in flags if "false" in k.lower() and ("hardcoded" in k.lower() or "hint" in k.lower())]
        say("rows/G3", "FAIL" if bad else "PASS", f"bypass_flags: {dict(flags)}; bypass_kind: {kinds}; llm_attempted: {llm}")
    else:
        ev = []
        for fn in (a.repo_root / "phase2_a3_p_kwargs.json", a.repo_root / "p2_pure_llm_full_run.log"):
            if fn.exists():
                t = fn.read_text(errors="ignore")
                for env in ("HYPATIAX_DISABLE_PROMPT_HINTS", "HYPATIAX_DISABLE_HARDCODED"):
                    m = re.search(env + r"\W{1,6}(\w+)", t)
                    if m:
                        ev.append((fn.name, env, m.group(1)))
        hist = []
        for hfile in ("~/.zsh_history", "~/.bash_history"):
            pth = Path(os.path.expanduser(hfile))
            if pth.exists():
                hist += [f"{pth.name}: {l.strip()[:110]}" for l in pth.read_text(errors="ignore").splitlines()
                         if "export" in l and "HYPATIAX_DISABLE_PROMPT_HINTS" in l and "HYPATIAX_DISABLE_HARDCODED" in l]
        on = {e for _, e, v in ev if v in ("1", "true", "True")}
        base = (f"rows carry no bypass_flags (flag-like keys present: {flag_keys}); bypass_kind: {kinds}; llm_attempted: {llm}. "
                f"Shell history shows {len(hist)} export line(s) setting both flags (WEAK evidence: it shows the command was typed, not that the "
                f"full-run shell had it){': ' + hist[-1] if hist else ''}. ")
        if len(on) == 2:
            say("rows/G3", "EXPLAINED", base + f"Both flags appear as on in {ev}, but that is the render gate/log, not per-row evidence.")
        else:
            say("rows/G3", "FAIL", base + "No gate/log file shows both flags on. Real gap: either rerun with bypass_flags recorded in the rows, "
                "or accept it explicitly with --declare 'rows/G3=<what evidence you do have>'")

    # G9: schema
    schema = a.repo_root / "phase2_row_schema.json"
    try:
        import jsonschema
    except ImportError:
        return say("rows/G9", "MANUAL", "pip install jsonschema, or run: python scripts/run_pure_llm_arm.py --validate")
    if not schema.exists():
        return say("rows/G9", "MANUAL", f"{schema} not found; commit it to the repo root and rerun")
    sch = json.load(open(schema))
    val = jsonschema.Draft202012Validator(sch)
    errs = []
    for r in rows:
        rr = {k: v for k, v in r.items() if k != "_file"}
        for e in val.iter_errors(rr):
            errs.append((r.get("equation"), r.get("seed"), e.message, list(e.path), e.validator, e.instance))
    if not errs:
        return say("rows/G9", "PASS", "all rows validate against phase2_row_schema.json")
    req, enum_add, other = collections.Counter(), collections.defaultdict(set), []
    for eq, sd, m, path, kind, inst in errs:
        mm = re.match(r"'(.+?)' is a required property", m)
        if mm:
            req.update([mm.group(1)])
        elif kind == "enum" and len(path) == 1:
            enum_add[path[0]].add(inst)
        else:
            other.append((eq, sd, m[:120]))
    rp = run([sys.executable, "scripts/run_pure_llm_arm.py", "--validate"], cwd=a.repo_root,
             env=dict(os.environ, PYTHONPATH=str(a.repo_root / "scripts")))
    runner_ok = rp.returncode == 0
    tail = " | ".join((rp.stdout + rp.stderr).strip().splitlines()[-4:])[:400]
    (a.out / "runner_validate.log").write_text(rp.stdout + rp.stderr, encoding="utf-8")
    prop = json.loads(json.dumps(sch))
    prop["required"] = [k for k in sch.get("required", []) if k not in req]
    for k, vals in enum_add.items():
        if k in prop.get("properties", {}) and "enum" in prop["properties"][k]:
            prop["properties"][k]["enum"] += sorted(v for v in vals if v not in prop["properties"][k]["enum"])
    prop["$comment"] = (f"PROPOSED by phase2_finish.py: removed from required {sorted(req)}; enum additions {dict((k, sorted(v)) for k, v in enum_add.items())}. "
                        "Apply only via a logged amendment.")
    (a.out / "phase2_row_schema.proposed.json").write_text(json.dumps(prop, indent=1), encoding="utf-8")
    summary = (f"{len(errs)} schema errors; required-but-absent fields: {dict(req)}; enum violations: "
               f"{dict((k, sorted(v)) for k, v in enum_add.items())}; other: {other[:3]}; runner --validate "
               f"{'passes' if runner_ok else 'FAILS: ' + tail}")
    if not other and runner_ok:
        say("rows/G9", "EXPLAINED", summary + ". Schema file and runner disagree. Proposed schema in phase2_finish_out/phase2_row_schema.proposed.json; log in A5")
    else:
        say("rows/G9", "FAIL", summary + ". Proposed schema in phase2_finish_out/phase2_row_schema.proposed.json (apply via amendment, then rerun). "
            "Fields absent from rows that cannot be derived (e.g. input_tokens/output_tokens) are a real logging gap")


def step_evaluator(a):
    path = a.evaluator_path
    blob = git(["show", f"{a.evaluator_commit}:{path}"], a.repo_root)
    if blob.returncode:
        return say("evaluator", "FAIL", f"cannot read {path} at {a.evaluator_commit}: {blob.stderr.strip()}")
    committed_raw = hashlib.sha256(git_raw(a.repo_root, ["show", f"{a.evaluator_commit}:{path}"])).hexdigest()
    seen = {r.get("evaluator_sha256") for r in p_rows(a)}
    st = git(["status", "--short", path], a.repo_root).stdout.strip()
    ok = seen == {committed_raw} and not st
    say("evaluator/G7", "PASS" if ok else "FAIL",
        f"committed blob sha256={committed_raw[:16]}..; rows={[s[:16] for s in seen if s]}; file status={st or 'clean'}")


def _emit(root, hf):
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(root), str(root / "scripts")]),
               HYPATIAX_DISABLE_PROMPT_HINTS="1", HYPATIAX_DISABLE_HARDCODED="1")
    env.pop("HYPATIAX_LLM_MODEL", None)
    return run([sys.executable, "scripts/run_pure_llm_arm.py", "--data-fn", "p2_data:generate_case",
                "--emit-data-hashes", str(hf), "--p2-dir", str(STATE.get("p2_dir", "p2"))], cwd=root, env=env), env


def _check(root, hf):
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(root), str(root / "scripts")]))
    return run([sys.executable, "scripts/run_pure_llm_arm.py", "--data-fn", "p2_data:generate_case",
                "--check-hds-hashes", str(hf)], cwd=root, env=env)


def _cmp_hashfiles(f1, f2):
    h1, h2 = json.load(open(f1)), json.load(open(f2))
    if not (isinstance(h1, dict) and isinstance(h2, dict)):
        return None
    ks = set(h1) | set(h2)
    diff = [k for k in sorted(ks) if json.dumps(h1.get(k), sort_keys=True) != json.dumps(h2.get(k), sort_keys=True)]
    sub = collections.Counter()
    for k in diff:
        v1, v2 = h1.get(k), h2.get(k)
        if isinstance(v1, dict) and isinstance(v2, dict):
            sub.update(s for s in set(v1) | set(v2) if v1.get(s) != v2.get(s))
    return len(ks), diff, sub


def step_hashes(a):
    """G1. A control is needed: if the CURRENT tree cannot reproduce the rows' hashes, a mismatch at the HDS commit means nothing."""
    root = a.repo_root
    STATE["p2_dir"] = str(a.p2)
    pc = STATE.get("p_commit") or p_commit(a)
    fa, fb = a.out / "hashes_current_A.json", a.out / "hashes_current_B.json"
    pa, _ = _emit(root, fa)
    pb, _ = _emit(root, fb)
    if pa.returncode or pb.returncode or not fa.exists() or not fb.exists():
        return say("hashes/G1-control", "FAIL", f"emit on current tree failed: {((pa.stderr or pa.stdout) + (pb.stderr or pb.stdout))[-300:]}")
    cmp_ab = _cmp_hashfiles(fa, fb)
    if cmp_ab and cmp_ab[1]:
        return say("hashes/G1-control", "FAIL", f"generator not deterministic across processes: {len(cmp_ab[1])} of {cmp_ab[0]} keys differ between two emits")
    q = _check(root, fa)
    (a.out / "hashes_control.log").write_text(q.stdout + q.stderr, encoding="utf-8")
    control_ok = q.returncode == 0
    say("hashes/G1-control", "PASS" if control_ok else "FAIL",
        "current tree reproduces the P rows' data hashes (control only, tautological for G1)" if control_ok else
        "even the CURRENT tree does not reproduce the P rows' data hashes (see hashes_control.log); HDS-commit comparison is inconclusive")
    cp = run(["grep", "-n", "-E", r"generate_data\(|def generate_case|n_train|n_samples|noise|seed", "hypatiax/experiments/benchmarks/exp1_ablation.py",
              "scripts/p2_data.py"], cwd=root)
    (a.out / "call_paths.txt").write_text(cp.stdout, encoding="utf-8")

    shas = list(a.hds_commit)
    if not shas:
        for run_id in a.runs:
            p = run(["gh", "run", "view", str(run_id), "--json", "headSha"], cwd=root)
            if p.returncode:
                say("hashes/CI-sha", "MANUAL", f"gh failed for run {run_id}: {p.stderr.strip()[:120]}")
                continue
            sha = json.loads(p.stdout)["headSha"]
            say("hashes/CI-sha", "PASS", f"run {run_id} head SHA = {sha}")
            shas.append(sha)
    if not shas:
        return say("hashes", "FAIL", "no HDS commit: pass --hds-commit SHA (CI head SHA of the HDS runs)")
    for sha in sorted(set(shas)):
        wt = Path(tempfile.mkdtemp(prefix="hds_wt_"))
        shutil.rmtree(wt)
        try:
            run(["git", "-C", str(root), "worktree", "add", "--detach", str(wt), sha], check=True)
            (wt / "scripts").mkdir(exist_ok=True)
            for f in ("scripts/run_pure_llm_arm.py", "scripts/p2_data.py", "phase2_pure_llm_config.yaml", "phase2_row_schema.json"):
                if (root / f).exists():
                    shutil.copy(root / f, wt / f)
            env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(wt), str(wt / "scripts")]))
            pr = run([sys.executable, "-c", "import hypatiax;print(list(hypatiax.__path__)[0])"], cwd=wt, env=env)
            loc = pr.stdout.strip()
            if not loc or str(wt.resolve()) not in str(Path(loc).resolve()):
                say("hashes/G1", "FAIL", f"at {sha[:8]} hypatiax imports from {loc or pr.stderr[-120:]!r}, not the HDS worktree (editable install?)")
                continue
            hf = a.out / f"hds_hashes_{sha[:8]}.json"
            p, _ = _emit(wt, hf)
            if p.returncode or not hf.exists():
                say("hashes/G1", "FAIL", f"emit at {sha[:8]} failed: {(p.stderr or p.stdout)[-300:]}")
                continue
            gen_note = ""
            try:
                files = git(["diff", "--name-only", sha, pc, "--", "*.py"], root).stdout.split()
                gen = [f for f in files if re.search(r"generat|exp1_ablation|equation|noise|dataset|data_|r2_canonical", f)]
                (a.out / f"gen_diff_{sha[:8]}.patch").write_text(git(["diff", sha, pc, "--"] + gen, root).stdout if gen else "", encoding="utf-8")
                gen_note = (f" Generator-like files changed between {sha[:8]} and {pc[:8]}: {gen[:8]} (diff in gen_diff_{sha[:8]}.patch)." if gen else
                            f" NO generator-like .py file changed between {sha[:8]} and {pc[:8]}, so the mismatch points to the call path "
                            "(p2_data vs how exp1_ablation builds each HDS case): compare the two in call_paths.txt.")
            except Exception as e:  # noqa
                gen_note = f" (generator diff failed: {e})"
            cmp_ = _cmp_hashfiles(hf, fa)
            q = _check(root, hf)
            (a.out / f"hashes_check_{sha[:8]}.log").write_text(q.stdout + q.stderr, encoding="utf-8")
            detail = ""
            if cmp_:
                detail = f" Direct compare vs current tree: {len(cmp_[1])}/{cmp_[0]} keys differ" + (f" (fields {dict(cmp_[2])})" if cmp_[2] else "") + "."
            if q.returncode == 0:
                say("hashes/G1", "PASS", f"generator at {sha[:8]} reproduces the P rows' train/far data hashes.{detail}")
            elif control_ok:
                say("hashes/G1", "FAIL", f"control passes but generator at {sha[:8]} does NOT.{detail}{gen_note} HDS rows carry no data hash, so G1 cannot "
                    "be certified after the fact. Options: rerun HDS with train/far hash logging, or accept with --declare 'hashes/G1=<reason>'")
            else:
                say("hashes/G1", "FAIL", f"inconclusive at {sha[:8]} (control failed too).{detail}{gen_note}")
        except Exception as e:  # noqa
            say("hashes/G1", "FAIL", f"{sha[:8]}: {str(e)[:300]}")
        finally:
            run(["git", "-C", str(root), "worktree", "remove", "--force", str(wt)])


def _one_closure(a, field, pure_glob, hds_glob, tag):
    # the closure takes the system name from each row's own label ('pure_llm'); --a-name must equal it
    out = a.out / f"closure_{tag}"
    cmd = [sys.executable, str(a.repo_root / "scripts" / "check_closure_nonfinite.py"), "--run-closure", "--a-name", "pure_llm",
           "--pure-llm", pure_glob, "--hds", hds_glob, "--r2-field", field, "--out-dir", str(out)] + a.adapter_args
    p = run(cmd, cwd=a.repo_root)
    (a.out / f"closure_{tag}.log").write_text(p.stdout + p.stderr, encoding="utf-8")
    res = [l for l in p.stdout.splitlines() if l.startswith("RESULT")]
    return p.returncode == 0 and any("PASSED" in l for l in res), (res or ["no RESULT line"])[0], fail_lines(p.stdout + p.stderr), p


def step_closures(a):
    root, sc = a.repo_root, a.repo_root / "scripts"
    for name, field, d in (("medium", "extrap_r2_medium", "p2_med"), ("train", "train_r2", "p2_train")):
        r = run([sys.executable, str(sc / "derive_pure_fields.py"), "--field", field, "--out", d], cwd=root)
        if r.returncode:
            say(f"closures/{name}", "FAIL", f"derive failed: {(r.stderr or r.stdout)[-200:]}")
            continue
        ok, res, fl, _ = _one_closure(a, field, f"{d}/pure_llm_*.jsonl", f"{d}/hds_*.jsonl", name)
        say(f"closures/{name}", "PASS" if ok else "FAIL",
            f"{res} (log: closure_{name}.log; train is NOT like-for-like: P train R2 is best of 3)" + ("" if ok else f" failing: {fl}"))
    r = run([sys.executable, str(sc / "run_pure_llm_arm.py"), "--emit-call1-set", "p2_call1", "--data-fn", "p2_data:generate_case"],
            cwd=root, env=dict(os.environ, PYTHONPATH=str(sc)))
    if r.returncode:
        return say("closures/call1", "FAIL", f"emit failed: {(r.stderr or r.stdout)[-200:]}")
    ok, res, fl, p = _one_closure(a, "extrap_r2_far", "p2_call1/pure_llm_*.jsonl", "p2/hds_*.jsonl", "call1")
    if ok:
        say("closures/call1", "PASS", f"{res} (secondary result; the closure labels these rows 'pure_llm' because it reads the system name from "
            "each row, so name the output folder/report line 'call 1 only')")
    else:
        tail = "\n".join((p.stdout + p.stderr).strip().splitlines()[-12:])
        say("closures/call1", "FAIL", f"{res}; failing lines: {fl}. Tail of closure_call1.log:\n{tail}")


def step_runtime(a):
    rows = load_rows(str(a.p2 / "hds_*.jsonl"))
    recs = []
    for r in rows:
        src = r.get("_source", "")
        if "::" not in src:
            continue
        f, rest = src.split("::", 1)
        try:
            k, blk = rest.split("/", 1)
            h = json.load(open(a.repo_root / f))[k][blk]
        except Exception:
            continue
        rt, tot, sr, llm = r.get("runtime_s"), h.get("total_time_s"), h.get("sr_time_s"), h.get("llm_time_s")
        if rt is None or tot is None:
            continue
        recs.append((rt, tot, sr, llm or 0.0))
    tp = run(["grep", "-n", "-E", "sr_time_s|total_time_s|llm_time_s", "hypatiax/tools/symbolic/hybrid_system_v50_2.py",
              "hypatiax/experiments/benchmarks/exp1_ablation.py"], cwd=a.repo_root)
    (a.out / "runtime_timers_grep.txt").write_text(tp.stdout, encoding="utf-8")
    if not recs:
        return say("runtime", "MANUAL", "could not load source JSON blocks from _source")
    n = len(recs)
    eq_total = sum(abs(rt - tot) < 1e-6 for rt, tot, _, _ in recs)
    additive = sum(sr is not None and abs(tot - (sr + llm)) < 0.05 for _, tot, sr, llm in recs)
    sr_only = sum(sr is not None and llm > 0.05 and abs(tot - sr) < 0.05 for _, tot, sr, llm in recs)
    worst = max(rt + llm for rt, _, _, llm in recs)
    med_rt = statistics.median(rt for rt, _, _, _ in recs)
    med_inc = statistics.median(rt + llm for rt, _, _, llm in recs)
    head = f"{n} HDS rows: runtime_s == total_time_s in {eq_total}; total == sr+llm in {additive}; total == sr (llm>0) in {sr_only}."
    if eq_total < n:
        return say("runtime", "FAIL", head + " runtime_s is not total_time_s for every row")
    if additive >= 0.9 * n:
        return say("runtime", "PASS", head + " total_time_s includes LLM time")
    if sr_only >= 0.9 * n:
        ok = worst <= a.budget_cap
        msg = (head + f" total_time_s equals sr_time_s, so either sr_time_s already wraps the LLM stage or runtime_s EXCLUDES LLM time "
               f"(read runtime_timers_grep.txt). Worst case (runtime+llm): max {worst:.0f}s vs cap {a.budget_cap:.0f}s; HDS median "
               f"{med_rt:.0f}s reported vs {med_inc:.0f}s worst-case, so the closure's runtime ratio may be slightly understated.")
        return say("runtime", "EXPLAINED" if ok else "FAIL", msg + (" The never-binding budget conclusion survives either way." if ok else " The cap may have bound."))
    say("runtime", "MANUAL", head + " pattern is mixed; read runtime_timers_grep.txt")


def step_engine(a):
    p = run(["grep", "-rniE", "--include=*.py", r"engine_version|v50_2", "hypatiax"], cwd=a.repo_root)
    lines = [l for l in p.stdout.splitlines() if "/results/" not in l]
    (a.out / "engine_version_grep.txt").write_text("\n".join(lines), encoding="utf-8")
    assign = [l for l in lines if re.search(r"""engine_version["']?\s*[:=]\s*["']5\.4""", l, re.I)]
    files = sorted({l.split(":")[0] for l in assign})
    if assign and all(f.endswith("hybrid_system_v50_2.py") for f in files):
        say("engine", "PASS", f"engine_version 5.4 is assigned only in hybrid_system_v50_2.py (line {[l.split(':')[1] for l in assign][:5]})")
    elif assign:
        say("engine", "MANUAL", f"engine_version 5.4 assigned in {files}; see engine_version_grep.txt")
    else:
        say("engine", "MANUAL", f"no literal engine_version = 5.4 assignment among {len(lines)} hits; see engine_version_grep.txt")


def step_binder(a):
    H, P = load_rows(str(a.p2 / "hds_*.jsonl")), p_rows(a)
    hf = collections.Counter("def-function" if str(r.get("formula", "")).lstrip().startswith("def ") else
                             ("none" if not r.get("formula") else "expression") for r in H)
    cands = [c for r in P for c in (r.get("candidate_formulas") or []) if c]
    defaulted = sum(1 for c in cands if re.search(r"def\s+\w+\s*\([^)]*=", c))
    g = run(["grep", "-n", "-E", r"inspect\.signature|signature\(|cannot bind|\.bind\(", "hypatiax/experiments/benchmarks/exp1_ablation.py",
             "hypatiax/tools/symbolic/hybrid_system_v50_2.py"], cwd=a.repo_root)
    (a.out / "binder_grep.txt").write_text(g.stdout, encoding="utf-8")
    if defaulted == 0 and set(hf) <= {"expression"}:
        say("binder", "EXPLAINED", f"the binder rule was set post hoc (after dry-run output) but {defaulted} of {len(cands)} P candidates in the 45 real rows "
            f"have defaulted parameters, so it changed no scored row; HDS final formulas are {dict(hf)} (constants inlined, no signature). "
            "State both facts and the post-hoc timing in A5")
    else:
        say("binder", "MANUAL", f"HDS formulas {dict(hf)}; {defaulted} of {len(cands)} P candidates have defaulted parameters, so the binder rule may have "
            "changed scores. Read binder_grep.txt and rescore with the old binder to measure the effect")


def step_listing8(a):
    g = run(["git", "grep", "-n", "-E", r"ss_tot|r2_checked", "--", "*.py", "*.tex", "*.md", "*.txt"], cwd=a.repo_root)
    lines = [l for l in g.stdout.splitlines() if "/results/" not in l and "phase2_finish" not in l]
    (a.out / "listing8_compare.txt").write_text("\n".join(lines), encoding="utf-8")
    ev = [l for l in lines if l.startswith(a.evaluator_path + ":") and "ss_tot" in l]
    tex = [l for l in lines if re.match(r"[^:]+\.(tex|md):", l) and "ss_tot" in l]
    tests = [l for l in lines if "test_" in l.split(":")[0] and re.search(r"near|constant|degenerate", l, re.I)]
    say("listing8", "MANUAL", f"evaluator {a.evaluator_path} ss_tot lines ({len(ev)}): {[l[len(a.evaluator_path) + 1:][:150] for l in ev[:8]]}; "
        f"supplement/doc ss_tot lines ({len(tex)}): {[l[:150] for l in tex[:6]]}; test lines mentioning near/constant/degenerate: {len(tests)}. "
        "Decide: does the evaluator's guard equal Listing 8? If the code replaced the absolute 1e-10 guard (apply_adaptive_config_r2.py suggests it did), "
        "Listing 8 is stale and the supplement must be corrected. Full list in listing8_compare.txt")


def step_amend(a):
    body = ["", "## Amendment A5 (draft, " + datetime.date.today().isoformat() + ")",
            "- Post-closure checks run by scripts/phase2_finish.py. Outcomes (EXPLAINED = cause identified; DECLARED = accepted with stated reason):"]
    body += [f"  - [{s}] {st}: {m[:500]}" for st, s, m in RESULTS]
    body += ["- Runner files that produced the P rows (hashes of the working copies, unchanged-since-run inferred from mtime):"]
    body += [f"  - {e}" for e in STATE.get("runner_evidence", [])] or ["  - (dirty step not run)"]
    body += ["- Binder rule (bind by name, defaults untouched) was set after seeing dry-run output; applied to arm P only.",
             "- failed:no_calls rows (Michaelis-Menten seeds 42, 99) mean all three candidates had non-finite training R2; label kept in data, counted as catastrophic.",
             "- evaluator_version set to r2_canonical@8f11733 by stated constant, on hash evidence (see evaluator/G7)."]
    (a.out / "amendment_A5_draft.md").write_text("\n".join(body) + "\n", encoding="utf-8")
    say("amend", "PASS", f"draft written to {a.out}/amendment_A5_draft.md (review, then append yourself)")


STEPS = {"dirty": step_dirty, "rows": step_rows, "evaluator": step_evaluator, "hashes": step_hashes,
         "closures": step_closures, "runtime": step_runtime, "engine": step_engine, "binder": step_binder,
         "listing8": step_listing8, "amend": step_amend}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--steps", nargs="*", choices=list(STEPS))
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--p2", type=Path, default=Path("p2"))
    ap.add_argument("--out", type=Path, default=Path("phase2_finish_out"))
    ap.add_argument("--p-commit", default=None, help="default: the single git_commit in the P rows, minus +dirty")
    ap.add_argument("--evaluator-commit", default="8f11733")
    ap.add_argument("--evaluator-path", default="hypatiax/core/r2_canonical.py")
    ap.add_argument("--config-path", default="phase2_pure_llm_config.yaml")
    ap.add_argument("--runner-files", nargs="*", default=["scripts/run_pure_llm_arm.py", "scripts/p2_data.py"],
                    help="files that produced the P rows and were not committed at the P commit")
    ap.add_argument("--budget-cap", type=float, default=1400.0)
    ap.add_argument("--declare", nargs="*", default=[], metavar="KEY=REASON",
                    help="accept a FAIL/MANUAL step as a recorded caveat, e.g. 'rows/G3=env flags not recorded'")
    ap.add_argument("--hds-commit", nargs="*", default=[], help="CI head SHA(s) that produced the HDS rows")
    ap.add_argument("--runs", nargs="*", default=["40301286024", "40379400415"], help="CI run ids (needs gh)")
    ap.add_argument("--adapter-args", nargs=argparse.REMAINDER, default=None,
                    help="everything after this is passed to check_closure_nonfinite.py (put it LAST)")
    a = ap.parse_args()
    for d in a.declare:
        k, _, why = d.partition("=")
        if not k.strip() or not why.strip():
            ap.error(f"--declare needs KEY=REASON with a non-empty reason, got {d!r}")
        DECLARED[k.strip()] = why.strip()
    a.adapter_args = a.adapter_args or ["--map", "model_id=model_id_returned", "--map", "code_version=git_commit",
                                        "--map", "config_hash=config_sha256", "--bypass-off", "live",
                                        "--set", "evaluator_version=r2_canonical@8f11733"]
    a.repo_root = a.repo_root.resolve()
    a.out = (a.repo_root / a.out) if not a.out.is_absolute() else a.out
    a.out.mkdir(parents=True, exist_ok=True)
    a.p2 = (a.repo_root / a.p2) if not a.p2.is_absolute() else a.p2
    chosen = list(STEPS) if a.all or not a.steps else a.steps
    chosen = [s for s in STEPS if s in chosen]  # canonical order: dirty before rows, amend last
    for s in chosen:
        try:
            STEPS[s](a)
        except Exception as e:  # keep going so one failure does not hide the rest
            say(s, "FAIL", f"crashed: {e}")
    json.dump([{"step": s, "status": st, "message": m} for s, st, m in RESULTS], open(a.out / "report.json", "w"), indent=1)
    c = collections.Counter(st for _, st, _ in RESULTS)
    print("\nSUMMARY:", dict(c))
    if c.get("FAIL"):
        print("NOT YET CLEAN: resolve FAIL items, or accept each explicitly with --declare KEY=REASON")
    elif c.get("MANUAL"):
        print("NOT YET CLEAN: resolve the MANUAL items (evidence is in phase2_finish_out/)")
    elif c.get("EXPLAINED") or c.get("DECLARED"):
        print(f"CLOSED WITH DOCUMENTED CAVEATS: {c.get('EXPLAINED', 0)} explained, {c.get('DECLARED', 0)} declared; all must appear in A5 and the report")
    else:
        print("CLEAN CLOSE")
    sys.exit(1 if c.get("FAIL") else 0)


if __name__ == "__main__":
    main()
