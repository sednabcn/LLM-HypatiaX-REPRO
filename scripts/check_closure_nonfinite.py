#!/usr/bin/env python3
"""Check how Phase 2 closure treats non-finite / failed:* Pure LLM rows.

Questions answered:
  1. Is every (equation, seed) pair present in BOTH arms (n stays 15, pairing intact)?
  2. Are -inf rows with status 'failed:*' counted as catastrophic (R2 < -10), not missing?
  3. Does nan_or_missing stay 0 for the Pure LLM arm?
  4. With --run-closure: does scripts/phase2_close.py report the same n, the same
     catastrophic rate and the same nan_or_missing as this independent computation?
     (A mismatch means the closure script drops or reclassifies failed rows.)

The closure's schema check requires fields that the Pure LLM runner does not write
(status, formula, bypass_used, ...). v3 adds an adapter that builds a TEMP copy of the
P rows with those fields derived from fields P already has, and feeds the copy to the
closure. p2/ is never touched. Any required field with no mapping stops the run with a
list (never guessed); supply it with --map FIELD=SOURCE_FIELD.

Writes nothing to p2/. Rows are never edited. With --write-sidecar it writes a
display-label map (raw status kept) for the report and amendment A4.

Usage (repo root):
  python scripts/check_closure_nonfinite.py --run-closure \
      --a-name pure_llm --r2-field extrap_r2_far
Exit code: 0 all checks pass, 1 a check failed, 2 input problem.
"""
import argparse, collections, contextlib, hashlib, glob, json, math, re, subprocess, sys, tempfile
from pathlib import Path

CAT = -10.0
DECL = ("P: 3 calls, cap 1400 s + 300 s; HDS: 3600 s. HDS sees data statistics, "
        "P does not. HDS gets 3 candidates from one call, P gets 3 samples from three calls.")


def load(pattern):
    rows = []
    for f in sorted(glob.glob(pattern)):
        for ln in Path(f).read_text().splitlines():
            if ln.strip():
                r = json.loads(ln)          # json.loads accepts -Infinity / NaN
                r["_file"] = f
                rows.append(r)
    return rows


def value(row, field):
    v = row.get(field, row.get("r2"))
    if isinstance(v, str):
        s = v.strip().lower()
        v = {"-inf": -math.inf, "-infinity": -math.inf, "inf": math.inf,
             "infinity": math.inf, "nan": math.nan}.get(s)
    return v


def classify(v):
    """own rule: non-finite negative infinity and finite < -10 are catastrophic."""
    if v is None:
        return "missing"
    if isinstance(v, float) and math.isnan(v):
        return "missing"
    if v == -math.inf:
        return "catastrophic"
    if v == math.inf:
        return "missing"      # +inf is not a valid R2; flag as missing
    return "catastrophic" if v < CAT else "ok"


PIPELINE_MAP = {"model_id": "model_id_returned", "code_version": "git_commit",
                "config_hash": "config_sha256"}


def verify_evaluator(P, H, path):
    """P and HDS used the same evaluator iff P's recorded sha256 equals the sha256 of the
    scorer file as committed at the commit named in HDS's evaluator_version label."""
    labels = {r.get("evaluator_version") for r in H}
    if len(labels) != 1:
        return False, f"HDS rows carry {len(labels)} evaluator labels", None
    label = next(iter(labels))
    m = re.match(r"^(.+)@([0-9a-f]{7,40})$", str(label))
    if not m:
        return False, f"cannot parse HDS evaluator label {label!r}", None
    shas = {r.get("evaluator_sha256") for r in P}
    if len(shas) != 1 or None in shas:
        return False, f"P rows carry evaluator_sha256 values {sorted(map(str, shas))[:3]}", None
    g = subprocess.run(["git", "show", f"{m.group(2)}:{path}"], capture_output=True)
    if g.returncode:
        return False, f"git show {m.group(2)}:{path} failed: {g.stderr.decode()[:80]}", None
    h = hashlib.sha256(g.stdout).hexdigest()
    ok = h in shas
    return ok, f"P sha {next(iter(shas))[:8]} vs {path}@{m.group(2)} sha {h[:8]}", label


def selected_formula(r):
    cf, si = r.get("candidate_formulas"), r.get("selected_index")
    if isinstance(cf, list) and isinstance(si, int) and 0 <= si < len(cf):
        return cf[si]
    return None            # no candidate selected (e.g. failed:no_calls)


BYPASS_OFF = {None, "", "none", "None", "off", "disabled", "not_used", "no_bypass", "false", "False", False}
BYPASS_ON = {"hardcoded", "bypass", "used", "on", "enabled", "true", "True", True}


def _bypass(r):
    """True / False when bypass_kind is a known value, None when unknown (never guessed)."""
    k = r.get("bypass_kind")
    if k in BYPASS_OFF:
        return False
    if k in BYPASS_ON:
        return True
    return None


# derivations for closure-required fields that P rows lack; everything else needs --map
KNOWN = {
    "formula": selected_formula,
    "status": lambda r: r.get("r2_status"),
    "bypass_used": _bypass,
}


def adapt(P, H, extra_map, closure_text=None, consts=None):
    consts = consts or {}
    """Return (adapted P rows, report, unresolved, ignored). Originals are not modified."""
    req = set.intersection(*[set(r) for r in H]) - {"_file"}
    have = set.intersection(*[set(r) for r in P]) - {"_file"}
    missing = sorted(req - have)
    ignored = []
    if closure_text is not None:      # only fields the closure script actually names
        refd = [f for f in missing
                if f"'{f}'" in closure_text or f'"{f}"' in closure_text]
        ignored = [f for f in missing if f not in refd]
        missing = refd
    fns, unresolved = {}, []
    for f in missing:
        if f in consts:
            fns[f] = (lambda r, v=consts[f]: v)
        elif f in extra_map:
            src = extra_map[f]
            fns[f] = (lambda r, s=src: r.get(s))
        elif f in KNOWN:
            fns[f] = KNOWN[f]
        else:
            unresolved.append(f)
    out = []
    for r in P:
        n = dict(r)
        for f, fn in fns.items():
            if n.get(f) is None:
                n[f] = fn(r)
        out.append(n)
    if "bypass_used" in fns and "bypass_used" not in extra_map:
        if any(n.get("bypass_used") is None for n in out):
            unresolved.append("bypass_used")
    pkeys = sorted(set.union(*[set(r) for r in P]) - {"_file"})
    report = {}
    for f in missing:
        hv = sorted({repr(r.get(f))[:60] for r in H})[:5]
        pv = sorted({repr(n.get(f))[:60] for n in out})[:5] if f in fns else None
        stem = f.strip("_").split("_")[0]
        sugg = [k for k in pkeys if stem in k.lower()][:6]
        report[f] = {"source": ("constant (--set)" if f in consts else extra_map.get(f, "built-in rule" if f in KNOWN else None)),
                     "P_values": pv, "HDS_values": hv, "P_fields_like_it": sugg}
    return out, report, sorted(set(unresolved)), ignored


@contextlib.contextmanager
def _workdir(keep):
    if keep:
        Path(keep).mkdir(parents=True, exist_ok=True)
        yield keep
    else:
        with tempfile.TemporaryDirectory() as t:
            yield t


def write_adapted(rows, td):
    Path(td).mkdir(parents=True, exist_ok=True)
    paths = collections.defaultdict(list)
    for r in rows:
        paths[r["_file"]].append({k: v for k, v in r.items() if k != "_file"})
    outp = []
    for f, rs in sorted(paths.items()):
        q = Path(td) / Path(f).name
        q.write_text("\n".join(json.dumps(x) for x in rs) + "\n")   # keeps -Infinity / NaN
        outp.append(str(q))
    return outp


def per_equation_rate(rows, field, kind):
    by = collections.defaultdict(list)
    for r in rows:
        by[r["equation"]].append(1.0 if classify(value(r, field)) == kind else 0.0)
    return {e: sum(v) / len(v) for e, v in by.items()}, by


def mean(d):
    return sum(d.values()) / len(d) if d else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pure-llm", default="p2/pure_llm_*.jsonl")
    ap.add_argument("--hds", default="p2/hds_*.jsonl")
    ap.add_argument("--r2-field", default="extrap_r2_far")
    ap.add_argument("--a-name", default="pure_llm")
    ap.add_argument("--closure", default="scripts/phase2_close.py")
    ap.add_argument("--expect-equations", type=int, default=15)
    ap.add_argument("--run-closure", action="store_true")
    ap.add_argument("--write-sidecar", metavar="PATH",
                    help="write display-label map JSON, e.g. p2_pure_llm_status_relabel.json")
    ap.add_argument("--tol", type=float, default=1e-3)
    ap.add_argument("--map", action="append", default=[], metavar="FIELD=SOURCE",
                    help="derive closure-required field FIELD for P rows from P field SOURCE")
    ap.add_argument("--set", action="append", default=[], metavar="FIELD=VALUE",
                    help="set closure-required field FIELD to the constant VALUE on every P row. "
                         "Only with evidence the value is true for P (e.g. evaluator_version "
                         "after showing the evaluator file hash is identical)")
    ap.add_argument("--out-dir", default=None, metavar="DIR",
                    help="keep the closure output (manifest, marker file) and the adapted P rows "
                         "in DIR instead of a temp dir that is deleted")
    ap.add_argument("--pipeline", action="store_true",
                    help="standard Phase 2 mapping, no other flags needed: model_id, code_version, "
                         "config_hash from the P runner's own fields; bypass_kind 'live' = no bypass "
                         "(baseline sets it by construction); evaluator_version verified from git")
    ap.add_argument("--evaluator-file", default="hypatiax/core/r2_canonical.py")
    ap.add_argument("--bypass-off", default="", metavar="V1,V2",
                    help="bypass_kind values that mean the bypass was NOT used (e.g. live); "
                         "confirm in the baseline code before passing")
    ap.add_argument("--no-adapt", action="store_true",
                    help="feed the raw P rows to the closure (old behaviour)")
    a = ap.parse_args()

    extra_map = dict(m.split("=", 1) for m in a.map)
    consts = dict(m.split("=", 1) for m in a.set)
    BYPASS_OFF.update(v for v in a.bypass_off.split(",") if v)
    P, H = load(a.pure_llm), load(a.hds)
    if not P or not H:
        sys.exit(f"no rows: pure={len(P)} hds={len(H)} (check globs)")
    fails = []

    def check(name, ok, detail=""):
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))
        if not ok:
            fails.append(name)

    # 1. pairing
    kp = collections.Counter((r["equation"], r["seed"]) for r in P)
    kh = collections.Counter((r["equation"], r["seed"]) for r in H)
    eq_p, eq_h = {k[0] for k in kp}, {k[0] for k in kh}
    check("one row per (equation, seed) in P", max(kp.values()) == 1,
          f"{len(P)} rows, dup keys={[k for k, c in kp.items() if c > 1][:3]}")
    check("one row per (equation, seed) in HDS", max(kh.values()) == 1, f"{len(H)} rows")
    check("same (equation, seed) keys in both arms", set(kp) == set(kh),
          f"only P={sorted(set(kp)-set(kh))[:3]} only HDS={sorted(set(kh)-set(kp))[:3]}")
    check(f"n equations == {a.expect_equations}", len(eq_p & eq_h) == a.expect_equations,
          f"P={len(eq_p)} HDS={len(eq_h)} shared={len(eq_p & eq_h)}")

    # 2. failed:* rows
    failed = [r for r in P if str(r.get("r2_status", "")).startswith("failed")]
    print(f"\nfailed:* rows in P: {len(failed)}")
    for r in failed:
        v = value(r, a.r2_field)
        print(f"  {r['equation']} seed={r['seed']} status={r.get('r2_status')} "
              f"stage={r.get('error_stage')} {a.r2_field}={v!r} -> own class: {classify(v)}")
    bad = [r for r in failed if classify(value(r, a.r2_field)) != "catastrophic"]
    check("every failed:* row with non-finite R2 is catastrophic, not missing",
          not bad, f"{len(bad)} not catastrophic")

    # 3. own rates
    cat_p, _ = per_equation_rate(P, a.r2_field, "catastrophic")
    cat_h, _ = per_equation_rate(H, a.r2_field, "catastrophic")
    mis_p, _ = per_equation_rate(P, a.r2_field, "missing")
    mis_h, _ = per_equation_rate(H, a.r2_field, "missing")
    print(f"\nown rates (mean over equations of per-equation seed mean), field={a.r2_field}")
    print(f"  catastrophic  P={mean(cat_p):.3f}  HDS={mean(cat_h):.3f}")
    print(f"  nan_or_missing P={mean(mis_p):.3f}  HDS={mean(mis_h):.3f}")
    check("nan_or_missing is 0 for P", mean(mis_p) == 0.0)

    # 4. static scan + live closure
    cp = Path(a.closure)
    if cp.exists():
        pat = re.compile(r"failed|r2_status|startswith|isfinite|isnan|isinf|inf\b|continue|dropna|\bdrop")
        print(f"\nstatic scan of {cp} (read these lines; a filter on status would drop rows):")
        for i, ln in enumerate(cp.read_text().splitlines(), 1):
            if pat.search(ln):
                print(f"  {i}: {ln.strip()[:140]}")
    else:
        print(f"\n{cp} not found; static scan skipped")

    if a.run_closure:
        if not cp.exists():
            sys.exit(f"--run-closure needs {cp}")
        # phase2_close.py has no --r2-field option: it scores each row's `r2`.
        # So the closure and this script only agree if r2 == the chosen field.
        diff = []
        for r in P + H:
            f, g = r.get(a.r2_field), r.get("r2")
            if f is None or g is None:
                continue
            if f != g and not (isinstance(f, float) and isinstance(g, float)
                               and math.isnan(f) and math.isnan(g)):
                diff.append((r["equation"], r["seed"], f, g))
        check(f"row r2 equals {a.r2_field} (closure scores r2)", not diff,
              f"{len(diff)} rows differ, e.g. {diff[:2]}")
        with _workdir(a.out_dir) as td:
            pure_paths = sorted(glob.glob(a.pure_llm))
            if not a.no_adapt:
                ctext = cp.read_text()
                if a.pipeline:
                    for k, v in PIPELINE_MAP.items():
                        extra_map.setdefault(k, v)
                    BYPASS_OFF.add("live")
                    ok, detail, label = verify_evaluator(P, H, a.evaluator_file)
                    check("same evaluator in both arms (P hash == committed file at HDS commit)",
                          ok, detail)
                    if not ok:
                        print("\nRESULT: FAILED: ", fails)
                        sys.exit(1)
                    consts.setdefault("evaluator_version", label)
                    dirty = sorted({str(r.get("git_commit")) for r in P
                                    if str(r.get("git_commit", "")).endswith("+dirty")})
                    if dirty:
                        print(f"WARNING: P rows ran on a dirty tree {dirty}; record the diff in A4")
                adapted, rep, unresolved, ignored = adapt(P, H, extra_map, ctext, consts)
                print("\nadapter: fields HDS rows have, P rows lack, and the closure names")
                if ignored:
                    print(f"  not named in {cp.name}, left alone: {ignored}")
                if not rep:
                    print("  none (P rows already complete)")
                for f, d in rep.items():
                    lines = [str(i) for i, ln in enumerate(ctext.splitlines(), 1)
                             if f"'{f}'" in ln or f'"{f}"' in ln][:4]
                    print(f"  {f}: source={d['source']}  closure lines={lines}")
                    print(f"      P->{d['P_values']}  HDS has {d['HDS_values']}")
                    if d["source"] is None or f in unresolved:
                        print(f"      P fields that look related: {d['P_fields_like_it']}")
                if "bypass_used" in rep:
                    print("  bypass_kind values in P:",
                          sorted({repr(r.get('bypass_kind')) for r in P}))
                if unresolved:
                    L = ctext.splitlines()
                    print("\nhow the closure uses the unmapped fields (read before mapping):")
                    for f in unresolved:
                        for i, ln in enumerate(L, 1):
                            if f"'{f}'" in ln or f'"{f}"' in ln:
                                print(f"--- {f} @ line {i}")
                                for j in range(max(0, i - 3), min(len(L), i + 2)):
                                    print(f"  {j+1}: {L[j].rstrip()[:130]}")
                check("every missing required field has a mapping", not unresolved,
                      f"unmapped: {unresolved}; add --map FIELD=SOURCE for each "
                      "(HDS example values are printed above)")
                if unresolved:
                    print("\nRESULT: FAILED: ", fails)
                    sys.exit(1)
                pure_paths = write_adapted(adapted, str(Path(td) / "adapted_pure_llm"))
            cmd = [sys.executable, str(cp), "--pure-llm", *pure_paths,
                   "--hds", *sorted(glob.glob(a.hds)), "--a-name", a.a_name,
                   "--out-dir", str(Path(td) / "closure_out"), "--declare-unequal-timeout", DECL]
            out = subprocess.run(cmd, capture_output=True, text=True)
        txt = out.stdout + out.stderr
        print("\n--- closure output (tail) ---")
        print("\n".join(txt.splitlines()[-18:]))
        check("closure script ran without a usage/argument error",
              "usage:" not in txt and "unrecognized arguments" not in txt,
              f"returncode={out.returncode}")
        completed = "Paired comparison" in txt
        check("closure completed (printed the paired comparison)", completed,
              "closure stopped on a blocking check; see output above" if not completed else "")
        if not completed:
            print("\nRESULT: FAILED: ", fails)
            sys.exit(1)
        m = re.search(r"n=(\d+) equations", txt)
        check("closure n equations == own n", bool(m) and int(m.group(1)) == len(eq_p & eq_h),
              f"closure={m.group(1) if m else 'not found'} own={len(eq_p & eq_h)}")
        for label, own_a, own_b in (("catastrophic_r2", mean(cat_p), mean(cat_h)),
                                    ("nan_or_missing_r2", mean(mis_p), mean(mis_h))):
            m = re.search(rf"^\s*{label}\S*:\s*([\d.]+)\s*->\s*([\d.]+)", txt, re.M)
            if not m:
                check(f"closure reports {label}", False, "line not found")
                continue
            ca, cb = float(m.group(1)), float(m.group(2))
            check(f"closure {label}: P matches own", abs(ca - own_a) <= a.tol,
                  f"closure={ca:.3f} own={own_a:.3f}")
            check(f"closure {label}: HDS matches own", abs(cb - own_b) <= a.tol,
                  f"closure={cb:.3f} own={own_b:.3f}")
        m = re.search(r"^\s*nan_or_missing_r2\S*:\s*([\d.]+)", txt, re.M)
        check("closure nan_or_missing for P is 0", bool(m) and float(m.group(1)) == 0.0)

    # sidecar: display labels, raw status kept, rows untouched
    if a.write_sidecar:
        side = []
        for r in P:
            raw = r.get("r2_status")
            if raw == "failed:no_calls" or r.get("error_stage") == "no_calls":
                disp = "all candidates produced non-finite training R2"
            else:
                disp = raw
            side.append({"equation": r["equation"], "seed": r["seed"],
                         "raw_r2_status": raw, "raw_error_stage": r.get("error_stage"),
                         "n_calls": r.get("n_calls"), "display_label": disp,
                         "own_class": classify(value(r, a.r2_field))})
        Path(a.write_sidecar).write_text(json.dumps(side, indent=1) + "\n")
        print(f"\nwrote {a.write_sidecar} ({len(side)} rows; p2/ rows not modified)")

    print("\nRESULT:", "ALL CHECKS PASSED" if not fails else f"FAILED: {fails}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
