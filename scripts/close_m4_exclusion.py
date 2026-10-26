#!/usr/bin/env python3
"""Close the M4 (HybridSystemLLMNN) exclusion: make every derived number agree with the flags.

scripts/mark_m4_unverified.py flags the stored M4 rows that have no formula
("exclude_from_reported_results": true).  That leaves three kinds of derived data still computed
WITH the excluded rows.  This script fixes them, non-destructively and idempotently:

  1. per-test ``comparison`` (winner / scores / rankings / advantages) and the test-level ``winner``
     are recomputed from the non-excluded results, using the SAME rules as
     run_comparative_suite_benchmark_v2.py::_compare (valid = success, finite, r2 > 0; rank key =
     (r2 - 1e-5 * formula_complexity for the two symbolic methods, -time); advantages vs the winner).
     The previous winner is kept in comparison["winner_before_exclusion"].
  2. test-level per-method dicts (extrap_r2_far, extrap_rmse_far, extrap_error_pct, pca_test_r2) hold
     M4 numbers too.  A non-null M4 entry is MOVED to test["excluded_method_values"][<dict>][<method>]
     and set to null, so nothing is lost and nothing excluded stays in a field that tables read.
  3. the noise-sweep / sample-complexity CSVs carry M4 rows (R2 ~ 1.0, no formula column).  Two columns
     are appended to every row of those CSVs: provenance_status, exclude_from_reported_results
     (filled only on the M4 rows).  No existing cell is changed.

    python scripts/close_m4_exclusion.py                # dry run: what would change
    python scripts/close_m4_exclusion.py --apply        # write
    python scripts/close_m4_exclusion.py --check        # exit 1 if anything is still stale (audit use)
    python scripts/close_m4_exclusion.py --selftest     # prove compare() reproduces every stored
                                                        # comparison (before and after --apply)
    python scripts/close_m4_exclusion.py --consumers    # scripts that read M4 rows but never mention
                                                        # exclude_from_reported_results
"""
import argparse, csv, io, json, math, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
RES = ROOT / "hypatiax/data/results"
SKIP_PARTS = ("exploratory", "exp1_ablation_pre_prompt_fix")
FLAG = "exclude_from_reported_results"
STATUS = "unverified_no_formula"
M4_PREFIX = "HybridSystemLLMNN"
SYMBOLIC = {"SymbolicEngineWithLLM (tools)", "HybridDiscoverySystem v50_2 (tools)"}
PER_METHOD_DICTS = ("extrap_r2_far", "extrap_rmse_far", "extrap_error_pct", "pca_test_r2")
CSV_COLS = ("provenance_status", FLAG)


def _active(p: pathlib.Path) -> bool:
    return not any(part in SKIP_PARTS for part in p.relative_to(RES).parts)


def _finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _complexity(formula) -> int:                     # == BaseMethod._formula_complexity
    if not formula or formula in ("N/A", ""):
        return 9999
    return len(formula.replace(" ", ""))


def excluded_names(test: dict) -> list:
    res = test.get("results") or {}
    return [n for n, r in res.items() if isinstance(r, dict) and r.get(FLAG) is True]


def compare(results: dict, excluded=()) -> dict:
    """Same rules as _compare in run_comparative_suite_benchmark_v2.py / _pca.py, minus `excluded`."""
    valid = {
        n: r["r2"] for n, r in results.items()
        if isinstance(r, dict) and n not in excluded and r.get("success")
        and _finite(r.get("r2")) and r["r2"] > 0
    }
    if not valid:
        return {"winner": "None", "scores": {}, "rankings": {}, "advantages": [],
                "duplicates": {}, "y_scale": {}}

    def key(n):
        r = results[n]
        pen = 1e-5 * _complexity(r.get("formula")) if n in SYMBOLIC else 0.0
        t = r.get("time")
        return (valid[n] - pen, -(t if _finite(t) else 0.0))

    winner = max(valid, key=key)
    wr2 = valid[winner]
    return {
        "winner": winner,
        "scores": valid,
        "rankings": {m: i + 1 for i, m in enumerate(sorted(valid, key=key, reverse=True))},
        "advantages": [
            {"method": m, "diff": wr2 - r2, "pct": (wr2 - r2) / max(abs(r2), 1e-3) * 100}
            for m, r2 in sorted(valid.items(), key=lambda x: x[1], reverse=True) if m != winner
        ],
    }


def recomputed(test: dict) -> dict:
    """Return the comparison this test SHOULD carry, given its excluded rows."""
    ex = excluded_names(test)
    old = test.get("comparison") or {}
    new = compare(test["results"], ex)
    new["duplicates"] = {k: [n for n in v if n not in ex] for k, v in (old.get("duplicates") or {}).items()
                         if len([n for n in v if n not in ex]) > 1}
    new["y_scale"] = old.get("y_scale", {})
    new["excluded_from_comparison"] = ex
    new["winner_before_exclusion"] = old.get("winner_before_exclusion", old.get("winner"))
    return new


def fix_test(test: dict) -> bool:
    """Apply the recompute to one test in place; return True if anything changed."""
    ex = excluded_names(test)
    if not ex:
        return False
    before = json.dumps(test, sort_keys=True, default=str)
    new = recomputed(test)
    test["comparison"] = new
    test["winner"] = new["winner"]
    moved = test.setdefault("excluded_method_values", {})
    for d in PER_METHOD_DICTS:
        cur = test.get(d)
        if isinstance(cur, dict):
            for m in ex:
                if cur.get(m) is not None:
                    moved.setdefault(d, {})[m] = cur[m]
                    cur[m] = None
    if not moved:
        del test["excluded_method_values"]
    return json.dumps(test, sort_keys=True, default=str) != before


def _tests(data):
    t = data.get("tests") if isinstance(data, dict) else None
    return [x for x in t if isinstance(x, dict) and isinstance(x.get("results"), dict)] if isinstance(t, list) else []


def json_files():
    for p in sorted(RES.rglob("*.json")):
        if not _active(p):
            continue
        try:
            yield p, json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue


def csv_files():
    for p in sorted(RES.rglob("*.csv")):
        if _active(p) and "method" in p.read_text(encoding="utf-8", errors="replace").split("\n", 1)[0]:
            yield p


# ------------------------------------------------------------------ CSV
def _csv_rows(p):
    raw = p.read_bytes().decode("utf-8")
    eol = "\r\n" if "\r\n" in raw else "\n"
    return list(csv.reader(io.StringIO(raw, newline=""))), eol, raw.endswith(("\n", "\r\n"))


def csv_state(p):
    """(n_m4_rows, n_m4_rows_flagged, has_columns)"""
    rows, _, _ = _csv_rows(p)
    h = rows[0]
    if "method" not in h:
        return 0, 0, False
    mi = h.index("method")
    has = all(c in h for c in CSV_COLS)
    n = f = 0
    for r in rows[1:]:
        if len(r) > mi and r[mi].startswith(M4_PREFIX):
            n += 1
            if has and r[h.index(FLAG)].strip().lower() == "true":
                f += 1
    return n, f, has


def fix_csv(p, apply):
    rows, eol, trailing = _csv_rows(p)
    h = rows[0]
    mi = h.index("method")
    if not any(len(r) > mi and r[mi].startswith(M4_PREFIX) for r in rows[1:]):
        return 0
    if all(c in h for c in CSV_COLS) and csv_state(p)[0] == csv_state(p)[1]:
        return 0
    for c in CSV_COLS:
        if c not in h:
            h.append(c)
    si, fi = h.index(CSV_COLS[0]), h.index(FLAG)
    n = 0
    for r in rows[1:]:
        if not r:
            continue
        r.extend([""] * (len(h) - len(r)))
        if r[mi].startswith(M4_PREFIX):
            r[si], r[fi] = STATUS, "True"
            n += 1
    if apply:
        buf = io.StringIO(newline="")
        csv.writer(buf, lineterminator=eol).writerows(rows)
        out = buf.getvalue()
        if not trailing:
            out = out.rstrip("\r\n")
        p.write_bytes(out.encode("utf-8"))
    return n


# ------------------------------------------------------------------ reports
def stale():
    """Tests whose comparison/winner/per-method dicts still reflect an excluded row."""
    out = []
    for p, data in json_files():
        for t in _tests(data):
            ex = excluded_names(t)
            if not ex:
                continue
            c = t.get("comparison") or {}
            bad = (t.get("winner") in ex or c.get("winner") in ex
                   or any(m in (c.get("scores") or {}) or m in (c.get("rankings") or {}) for m in ex)
                   or any(a.get("method") in ex for a in (c.get("advantages") or []))
                   or any(isinstance(t.get(d), dict) and t[d].get(m) is not None
                          for d in PER_METHOD_DICTS for m in ex)
                   or t.get("winner") != c.get("winner"))
            if bad:
                out.append((p, t.get("description", "?")))
    return out


def csv_unflagged():
    res = []
    for p in csv_files():
        n, f, _ = csv_state(p)
        if n and n != f:
            res.append((p, n - f))
    return res


def consumers():
    """Python files that read the M4 method name but never mention the exclusion flag."""
    res = []
    for p in sorted(ROOT.rglob("*.py")):
        if any(x in p.parts for x in (".git", "tests", "__pycache__")) or p.name in (pathlib.Path(__file__).name,
                                                                                  "mark_m4_unverified.py"):
            continue
        s = p.read_text(encoding="utf-8", errors="replace")
        if M4_PREFIX in s and FLAG not in s:
            res.append(p.relative_to(ROOT))
    return res


def selftest():
    """Re-run compare() on every stored test and require it to reproduce the stored comparison
    (winner, scores, rankings, advantage order).  Before --apply the stored comparison was computed
    WITH the M4 rows, so excluded=() must match; after --apply it must match with the recorded
    exclusions.  Either way this proves the rules equal the benchmark's _compare."""
    n = ok = 0
    bad = []
    for p, data in json_files():
        for t in _tests(data):
            c = t.get("comparison") or {}
            if not c.get("scores"):
                continue
            n += 1
            new = compare(t["results"], c.get("excluded_from_comparison", []))
            same = (new["winner"] == c.get("winner") and new["rankings"] == c.get("rankings")
                    and set(new["scores"]) == set(c["scores"])
                    and all(abs(new["scores"][k] - c["scores"][k]) < 1e-12 for k in new["scores"])
                    and [a["method"] for a in new["advantages"]] == [a["method"] for a in c.get("advantages", [])])
            ok += same
            if not same:
                bad.append((p.relative_to(RES), t.get("description"), c.get("winner"), new["winner"]))
    return n, ok, bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--consumers", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        n, ok, bad = selftest()
        print(f"selftest: {ok}/{n} stored comparisons reproduced by compare()")
        for b in bad[:10]:
            print("  MISMATCH", *b)
        return 0 if ok == n and n > 0 else 1
    if a.consumers:
        c = consumers()
        print(f"{len(c)} python file(s) read M4 rows without mentioning {FLAG}:")
        for p in c:
            print("  ", p)
        return 0
    if a.check:
        s, cu = stale(), csv_unflagged()
        print(f"stale comparison/winner in {len(s)} test(s); {len(cu)} CSV file(s) with unflagged M4 rows")
        return 1 if (s or cu) else 0

    tests_changed = files_changed = winner_moves = 0
    for p, data in json_files():
        ch = 0
        for t in _tests(data):
            old = (t.get("comparison") or {}).get("winner_before_exclusion", (t.get("comparison") or {}).get("winner"))
            if fix_test(t):
                ch += 1
                winner_moves += old != t["winner"]
        if ch:
            tests_changed += ch
            files_changed += 1
            if a.apply:
                p.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")
    csv_rows = csv_n = 0
    for p in csv_files():
        n = fix_csv(p, a.apply)
        if n:
            csv_n += 1
            csv_rows += n
    print(f"JSON: {tests_changed} test(s) recomputed in {files_changed} file(s); winner changed in {winner_moves}")
    print(f"CSV:  {csv_rows} M4 row(s) flagged in {csv_n} file(s)")
    print("written" if a.apply else "dry run: nothing written (use --apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
