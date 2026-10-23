#!/usr/bin/env python3
"""Option 3, Phase 4: recovery at two thresholds, catastrophic-failure rate, provenance
and paired comparison against a reference run.

  summarize_recovery.py --dir full=PATH --dir probe=PATH ... --reference full
Row/layout handling mirrors Gate C in ci_runner_repro.yml (tests[].results{method: row}).
Rows are paired by (domain/equation-id[#seed], method); overlap is reported so a schema
mismatch shows up as overlap=0 instead of a silent empty table.
"""
import argparse, json, math, os, sys
from collections import Counter, defaultdict
from pathlib import Path

R2_KEYS = ("r2", "r2_test", "best_r2", "R2", "r2_train")
FORMULA_KEYS = ("formula", "expression", "discovered_formula", "best_formula", "python_code")
ID_KEYS = ("equation", "equation_name", "name", "test_name", "id")
SKIP = ("checkpoint", "disclosure", "summary")


def first(d, keys):
    for k in keys:
        if d.get(k) not in (None, ""):
            return d[k]
    return None


def norm(m):
    return str(m or "").lower().replace("-", "").replace("_", "").replace(" ", "")


def r2_of(row):
    for k in R2_KEYS:
        v = row.get(k)
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if math.isfinite(f) and f <= 1.01:
            return f
    return None


def mk(row, method, eid, src):
    seed = row.get("seed")
    return {"method": norm(row.get("method") or row.get("model") or method), "id": eid + (f"#s{seed}" if seed is not None else ""),
            "r2": r2_of(row), "has_formula": first(row, FORMULA_KEYS) is not None,
            "llm_source": str(row.get("llm_source") or "unrecorded"), "src": src}


def iter_rows(data, src):
    if isinstance(data, dict) and isinstance(data.get("tests"), list):
        for i, t in enumerate(data["tests"]):
            if not isinstance(t, dict):
                continue
            eid = f"{t.get('domain', '')}/{first(t, ID_KEYS) or i}"
            res = t.get("results")
            if isinstance(res, dict):
                for m, row in res.items():
                    if isinstance(row, dict):
                        yield mk(row, m, eid, src)
            elif isinstance(res, list):
                for row in res:
                    if isinstance(row, dict):
                        yield mk(row, "", eid, src)
        return
    if isinstance(data, dict):
        for k in ("results", "equation_results", "data", "rows"):
            if isinstance(data.get(k), (list, dict)) and k in data:
                yield from iter_rows(data[k], src)
                return
        yield mk(data, "", first(data, ID_KEYS) or src, src)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                yield mk(item, "", f"{first(item, ID_KEYS) or i}", src)


def load(d):
    rows = []
    for f in sorted(Path(d).rglob("*.json")):
        if any(x in f.name for x in SKIP) or f.name.startswith("_"):
            continue
        try:
            rows.extend(iter_rows(json.loads(f.read_text()), f.name))
        except Exception:
            continue
    return rows


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", action="append", required=True, help="name=path (repeatable)")
    ap.add_argument("--reference", required=True)
    ap.add_argument("--primary", type=float, default=0.99)
    ap.add_argument("--strict", type=float, default=0.999999)
    ap.add_argument("--catastrophic-r2", type=float, default=0.0,
                    help="pre-specified: catastrophic = no finite R2, or R2 < this value")
    ap.add_argument("--method-filter", default="", help="comma-separated normalised substrings")
    ap.add_argument("--fail-on-source", default="local_fallback,hardcoded",
                    help="comma-separated llm_source values that fail the run ('' to disable)")
    ap.add_argument("--json", default="audit_out/recovery_summary.json")
    ap.add_argument("--md", default="")
    a = ap.parse_args()

    runs = {}
    for spec in a.dir:
        name, _, path = spec.partition("=")
        if not Path(path).is_dir():
            print(f"::warning::{name}: {path} not found - skipped")
            continue
        rows = load(path)
        if a.method_filter:
            keys = [k.strip() for k in a.method_filter.split(",") if k.strip()]
            rows = [r for r in rows if any(k in r["method"] for k in keys)]
        runs[name] = rows
    if a.reference not in runs:
        print(f"::error::reference '{a.reference}' has no rows")
        sys.exit(1)

    result, bad_source = {"runs": {}, "paired": {}}, []
    for name, rows in runs.items():
        by_m = defaultdict(list)
        for r in rows:
            by_m[r["method"]].append(r)
        mm = {}
        for m, rs in sorted(by_m.items()):
            n = len(rs)
            kp = sum(1 for r in rs if r["r2"] is not None and r["r2"] >= a.primary)
            ks = sum(1 for r in rs if r["r2"] is not None and r["r2"] >= a.strict)
            kc = sum(1 for r in rs if r["r2"] is None or r["r2"] < a.catastrophic_r2)
            src = Counter(r["llm_source"] for r in rs)
            mm[m] = {"n": n, "recovered_primary": kp, "recovered_strict": ks, "catastrophic": kc,
                     "primary_ci95": wilson(kp, n), "strict_ci95": wilson(ks, n),
                     "missing_formula": sum(1 for r in rs if not r["has_formula"]),
                     "llm_source": dict(src)}
            for s in [x.strip() for x in a.fail_on_source.split(",") if x.strip()]:
                if src.get(s):
                    bad_source.append(f"{name}/{m}: {src[s]} row(s) with llm_source={s}")
        result["runs"][name] = mm

    ref = {(r["method"], r["id"]): r for r in runs[a.reference]}
    for name, rows in runs.items():
        if name == a.reference:
            continue
        per = {}
        cur = {(r["method"], r["id"]): r for r in rows}
        for m in sorted({k[0] for k in cur} & {k[0] for k in ref}):
            ids = [k for k in cur if k[0] == m and k in ref]
            for tag, thr in (("primary", a.primary), ("strict", a.strict)):
                ok = lambda r: r["r2"] is not None and r["r2"] >= thr
                b = sum(1 for k in ids if ok(cur[k]) and not ok(ref[k]))   # gained vs reference
                c = sum(1 for k in ids if ok(ref[k]) and not ok(cur[k]))   # lost vs reference
                per[f"{m}|{tag}"] = {"overlap": len(ids), "gained": b, "lost": c,
                                     "mcnemar_exact_p": mcnemar_exact(b, c)}
        result["paired"][name] = per

    Path(a.json).parent.mkdir(parents=True, exist_ok=True)
    Path(a.json).write_text(json.dumps(result, indent=2))

    L = [f"### Option 3 recovery summary (primary R2>={a.primary}, strict R2>={a.strict}; "
         f"catastrophic: no finite R2 or R2<{a.catastrophic_r2})", "",
         "| run | method | n | primary | strict | catastrophic | no formula | llm_source |", "|---|---|---|---|---|---|---|---|"]
    for name, mm in result["runs"].items():
        for m, v in mm.items():
            n = v["n"]
            L.append(f"| {name} | {m} | {n} | {v['recovered_primary']}/{n} ({v['recovered_primary']/n:.2f}) | "
                     f"{v['recovered_strict']}/{n} ({v['recovered_strict']/n:.2f}) | "
                     f"{v['catastrophic']}/{n} ({v['catastrophic']/n:.2f}) | {v['missing_formula']} | {v['llm_source']} |")
    if result["paired"]:
        L += ["", f"**Paired vs `{a.reference}`** (gained/lost = equations recovered only in the row's run / only in the reference)", "",
              "| run | method | threshold | overlap | gained | lost | exact McNemar p |", "|---|---|---|---|---|---|---|"]
        for name, per in result["paired"].items():
            for k, v in per.items():
                m, tag = k.split("|")
                L.append(f"| {name} | {m} | {tag} | {v['overlap']} | {v['gained']} | {v['lost']} | {v['mcnemar_exact_p']:.3f} |")
                if v["overlap"] == 0:
                    print(f"::warning::{name}/{m}: zero paired overlap - id schema differs between runs")
    text = "\n".join(L)
    print(text)
    if a.md:
        with open(a.md, "a") as fh:
            fh.write(text + "\n")
    for b in bad_source:
        print(f"::error::{b}")
    sys.exit(1 if bad_source else 0)


if __name__ == "__main__":
    main()
