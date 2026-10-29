#!/usr/bin/env python3
"""
audit_and_fix.py - investigate (and where safe, fix) the six open items in todonext.txt.

Default mode is READ-ONLY: it prints a report and writes audit_report.md.
Add --apply to make edits. Every edited file gets a .bak copy first.

Items
  1  benchmark_results.json mismatch (methods/rows/domains, claims that cite it, merge of per-domain runs)
  2  Item 11 + remaining unverified blocks (Kruskal-Wallis, power analysis, timing, scalability, repro paths)
  3  noise-level "off by 10x" correction vs shard files (noise_level / threshold_used)
  4  bracketed working notes ([Unverified...], [Removed...], [Withdrawn...])
  5  main paper correction notes + unsupported "near-zero extrapolation error"
  6  threshold entries for 2% / 20% noise and the stale print line in the sweep script

Example
  python audit_and_fix.py --supp supp.tex --paper main.tex --bench benchmark_results.json \
      --exp2-dir feynman-tests/exp2 --shards 'noise_shards/*.json' \
      --sweep-script run_noise_sweep_benchmark.py --run-all run_all.sh
  # then, to apply item 4 / 5 / 6 / merge edits:
  python audit_and_fix.py ... --apply --brackets comment --thr-new 0.995
"""
import argparse, glob, json, math, os, re, shutil, sys

EXPECTED_METHODS = 6
EXPECTED_DOMAINS = 11
EXPECTED_NOISE_PCT = [0.0, 0.05, 0.1, 0.5, 1.0]      # corrected levels, percent
OLD_NOISE_PCT = [0.0, 0.5, 1.0, 5.0, 10.0]           # original (suspect) labels
REPORT = []


def out(s=""):
    print(s)
    REPORT.append(s)


def head(n, title):
    out(f"\n## Item {n}: {title}")


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def backup_write(path, text):
    shutil.copy2(path, path + ".bak")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    out(f"  wrote {path} (backup: {path}.bak)")


def missing(label, path):
    out(f"  SKIPPED - {label} not found: {path!r}. Pass the right path to enable this check.")


def line_of(text, idx):
    return text.count("\n", 0, idx) + 1


# --------------------------------------------------------------------------- Item 1
def collect_tests(d):
    """Return list of tests from a result JSON of shape {'tests':[{'description','results':{method:{...}}}]}."""
    return d.get("tests", []) if isinstance(d, dict) else []


def summarize_bench(path):
    d = json.load(open(path))
    tests = collect_tests(d)
    methods, domains = set(), set()
    rows = 0
    for t in tests:
        for m in t.get("results", {}):
            methods.add(m)
            rows += 1
        dom = t.get("domain") or t.get("category")
        if dom:
            domains.add(dom)
    return tests, methods, domains, rows


def item1(a):
    head(1, "benchmark_results.json mismatch")
    if not a.bench or not os.path.exists(a.bench):
        missing("benchmark_results.json", a.bench)
    else:
        tests, methods, domains, rows = summarize_bench(a.bench)
        out(f"  {a.bench}: {len(tests)} tests, {rows} method-rows, {len(methods)} methods, {len(domains)} domains")
        for m in sorted(methods):
            out(f"    method: {m}")
        if len(methods) < EXPECTED_METHODS:
            out(f"  MISMATCH: file has {len(methods)} methods, paper/supplement describe {EXPECTED_METHODS}.")
    if a.exp2_dir and os.path.isdir(a.exp2_dir):
        files = sorted(glob.glob(os.path.join(a.exp2_dir, "*.json")))
        out(f"  per-domain runs in {a.exp2_dir}: {len(files)} files")
        merged, allm = [], set()
        for f in files:
            try:
                t = collect_tests(json.load(open(f)))
            except Exception as e:
                out(f"    could not parse {f}: {e}")
                continue
            ms = {m for x in t for m in x.get("results", {})}
            allm |= ms
            merged.extend(t)
            out(f"    {os.path.basename(f)}: {len(t)} tests, {len(ms)} methods")
        out(f"  union of methods across per-domain runs: {len(allm)}")
        if len(allm) >= EXPECTED_METHODS:
            out("  -> six-method data exists in the per-domain runs; a merge can regenerate benchmark_results.json.")
        else:
            out("  -> per-domain runs also have <6 methods; re-run exp2_feynman with an explicit --methods list "
                "(check the default in run_comparative_suite_benchmark_v2.py).")
        if a.apply and merged:
            dest = a.merge_out
            json.dump({"tests": merged}, open(dest, "w"), indent=2)
            out(f"  wrote merged file {dest} ({len(merged)} tests) - verify before citing it.")
    else:
        missing("exp2 per-domain directory (--exp2-dir)", a.exp2_dir)
    if a.supp and os.path.exists(a.supp):
        t = read(a.supp)
        pat = re.compile(r"29\s*/\s*30|27\s*/\s*30|benchmark_results\.json|six-method|PureLLM recount", re.I)
        hits = [(line_of(t, m.start()), m.group(0)) for m in pat.finditer(t)]
        out(f"  claims in supplement that depend on the six-method file: {len(hits)}")
        for ln, s in hits[:40]:
            out(f"    line {ln}: {s}")
        out("  If the six-method file can't be produced, rewrite each of these to cite only the M3/M4 file.")
    if a.paper and os.path.exists(a.paper):
        t = read(a.paper)
        for m in re.finditer(r"benchmark_results\.json|random[- ]split", t, re.I):
            out(f"    main paper line {line_of(t, m.start())}: {m.group(0)}")


# --------------------------------------------------------------------------- Item 2
UNVERIFIED_PATTERNS = {
    "Kruskal-Wallis": r"Kruskal",
    "power analysis": r"power analysis|statistical power|\bpower\s*=",
    "timing": r"\btiming\b|wall[- ]clock|runtime",
    "scalability": r"scalab",
    "manually entered": r"manually entered|hand[- ]entered|entered manually",
    "reproduction commands": r"python3?\s+\S+\.py|bash\s+\S+\.sh|\./run_all\.sh",
}


def item2(a):
    head(2, "Item 11 and remaining unverified content")
    if not (a.supp and os.path.exists(a.supp)):
        missing("supplement .tex", a.supp)
        return
    t = read(a.supp)
    m = re.search(r"Item\s*11\b.*", t)
    if m:
        out(f"  'Item 11' first appears at line {line_of(t, m.start())}:")
        out("    " + t[m.start():m.start() + 300].replace("\n", "\n    "))
        out("  (paste this block back to Claude to have the list updated)")
    else:
        out("  no 'Item 11' string found in the supplement; send the text of the list.")
    for label, pat in UNVERIFIED_PATTERNS.items():
        hits = [line_of(t, x.start()) for x in re.finditer(pat, t, re.I)]
        out(f"  {label}: {len(hits)} hit(s) at lines {hits[:15]}{' ...' if len(hits) > 15 else ''}")
    # reproduction-command paths: do they exist relative to --root?
    root = a.root or "."
    seen = set()
    for x in re.finditer(r"[\w./-]+\.(?:py|sh|json)\b", t):
        p = x.group(0)
        if p in seen or p.startswith("http"):
            continue
        seen.add(p)
        if not (os.path.exists(os.path.join(root, p)) or glob.glob(os.path.join(root, "**", os.path.basename(p)), recursive=True)):
            out(f"  path not found under {root!r}: {p} (line {line_of(t, x.start())})")


# --------------------------------------------------------------------------- Item 3
def find_key(obj, key):
    """Yield every value stored under `key` anywhere in a nested JSON structure."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                yield v
            yield from find_key(v, key)
    elif isinstance(obj, list):
        for v in obj:
            yield from find_key(v, key)


def item3(a):
    head(3, "noise-level 'off by 10x' correction vs shard files")
    files = sorted(glob.glob(a.shards)) if a.shards else []
    if not files:
        missing("noise shard files (--shards glob)", a.shards)
        return
    obs = {}
    for f in files:
        try:
            d = json.load(open(f))
        except Exception as e:
            out(f"  could not parse {f}: {e}")
            continue
        nl = sorted({round(float(x), 6) for x in find_key(d, "noise_level") if isinstance(x, (int, float))})
        th = sorted({float(x) for x in find_key(d, "threshold_used") if isinstance(x, (int, float))})
        out(f"  {os.path.basename(f)}: noise_level={nl} threshold_used={th}")
        for n in nl:
            obs.setdefault(n, set()).update(th)
    levels = sorted(obs)
    if not levels:
        out("  no noise_level fields found.")
        return
    # shard stores a fraction (script divides percent by 100); compare as percent
    pct = [round(x * 100, 6) for x in levels]
    pct_if_pct = [round(x, 6) for x in levels]
    out(f"  observed levels as fractions->percent: {pct}")
    for name, ref in (("corrected", EXPECTED_NOISE_PCT), ("original", OLD_NOISE_PCT)):
        if all(any(abs(p - r) < 1e-6 for r in ref) for p in pct):
            out(f"  -> consistent with the {name} labels {ref} if noise_level is a FRACTION.")
        if all(any(abs(p - r) < 1e-6 for r in ref) for p in pct_if_pct):
            out(f"  -> consistent with the {name} labels {ref} if noise_level is already in PERCENT.")
    out("  threshold per level:")
    for n in levels:
        out(f"    {n}: {sorted(obs[n])}")
    ths = {t for v in obs.values() for t in v}
    if len(ths) > 1:
        out(f"  Multiple thresholds in use {sorted(ths)} - add a sentence in Appendix H explaining why the two noise tables differ.")


# --------------------------------------------------------------------------- Item 4
def find_bracket_blocks(text, starts=("Unverified", "Removed", "Withdrawn")):
    """Return (start, end, kind) for each balanced [Kind ...] block."""
    blocks = []
    for m in re.finditer(r"\[(" + "|".join(starts) + r")\b", text):
        depth, i = 0, m.start()
        while i < len(text):
            c = text[i]
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    blocks.append((m.start(), i + 1, m.group(1)))
                    break
            i += 1
    return blocks


def item4(a):
    head(4, "bracketed working notes")
    if not (a.supp and os.path.exists(a.supp)):
        missing("supplement .tex", a.supp)
        return
    t = read(a.supp)
    blocks = find_bracket_blocks(t)
    out(f"  {len(blocks)} block(s) found")
    for s, e, k in blocks:
        out(f"    line {line_of(t, s)} [{k}] {len(t[s:e])} chars: {t[s:e][:90].replace(chr(10), ' ')}...")
    if a.apply and blocks:
        if a.brackets == "delete":
            new = t
            for s, e, _ in reversed(blocks):
                new = new[:s] + new[e:]
        elif a.brackets == "comment":
            new = t
            for s, e, _ in reversed(blocks):
                body = "\n".join("% " + ln for ln in t[s:e].splitlines())
                new = new[:s] + "% --- working note moved out of the text ---\n" + body + "\n" + new[e:]
        else:
            out("  --brackets must be 'comment' or 'delete' to apply.")
            return
        backup_write(a.supp, new)
    elif blocks:
        out("  (run with --apply --brackets comment|delete; 'comment' is reversible)")


# --------------------------------------------------------------------------- Item 5
PHRASE = re.compile(r"near[- ]zero extrapolation error", re.I)
NOTE = re.compile(r"\[(?:Correct(?:ed|ion)|Note|Fixed|Updated|Revised)[^\]]*\]|\\todo\{|%\s*(?:CORRECTION|FIXME|TODO)", re.I)


def item5(a):
    head(5, "main paper correction notes and unsupported phrase")
    for label, p in (("supplement", a.supp), ("main paper", a.paper)):
        if not (p and os.path.exists(p)):
            missing(label, p)
            continue
        t = read(p)
        out(f"  {label}: {len(NOTE.findall(t))} correction-style note(s)")
        for m in NOTE.finditer(t):
            out(f"    line {line_of(t, m.start())}: {t[m.start():m.start()+80].replace(chr(10), ' ')}")
        for m in PHRASE.finditer(t):
            out(f"    UNSUPPORTED PHRASE line {line_of(t, m.start())}: ...{t[max(0,m.start()-60):m.end()+40]!r}")
        if a.apply and PHRASE.search(t):
            new = PHRASE.sub(lambda m: "% UNSUPPORTED (flagged by audit): " + m.group(0) + "\n" + "extrapolation error as reported in the tables", t)
            out("  replacing phrase with neutral wording; review the sentence by hand.")
            backup_write(p, new)


# --------------------------------------------------------------------------- Item 6
def item6(a):
    head(6, "threshold entries and stale print line in the sweep script")
    for label, p in (("sweep script", a.sweep_script), ("run_all.sh", a.run_all)):
        if not (p and os.path.exists(p)):
            missing(label, p)
    if a.sweep_script and os.path.exists(a.sweep_script):
        t = read(a.sweep_script)
        stale = re.search(r"threshold\s*0\.9999\s*/\s*0\.995", t)
        if stale:
            out(f"  stale print line at line {line_of(t, stale.start())}: {t[stale.start()-40:stale.end()+40]!r}")
        # find threshold maps keyed by noise fractions, e.g. {0.0005: 0.99, 0.001: 0.99, 0.01: 0.995}
        dicts = list(re.finditer(r"(\w*[Tt][Hh][Rr][Ee][Ss][Hh]\w*)\s*=\s*\{([^{}]*)\}", t, re.S))
        for m in dicts:
            out(f"  threshold map '{m.group(1)}' at line {line_of(t, m.start())}: keys "
                f"{re.findall(r'([0-9.]+)\s*:', m.group(2))}")
        for lvl in ("0.02", "0.2", "0.20"):
            out(f"  entry for {lvl} present: {'yes' if re.search(r'(?<![0-9.])' + re.escape(lvl) + r'\s*:', t) else 'NO'}")
        if a.apply:
            if a.thr_new is None:
                out("  --thr-new is required to apply: choose ONE threshold for 2% and 20% so runner and aggregator agree "
                    "(runner uses 0.95, aggregator uses 0.995).")
            elif dicts:
                m = dicts[0]
                body = m.group(2)
                add = ""
                for lvl in ("0.02", "0.2"):
                    if not re.search(r"(?<![0-9.])" + re.escape(lvl) + r"\s*:", body):
                        add += f"    {lvl}: {a.thr_new},\n"
                new = t[:m.end(2)] + ("\n" if not body.rstrip().endswith(",") and body.strip() else "") + add + t[m.end(2):]
                new = new.replace("threshold 0.9999 / 0.995", f"thresholds per noise level (see threshold map; 2%/20% = {a.thr_new})")
                backup_write(a.sweep_script, new)
                out("  NOTE: also add the same entries to the aggregation script's map - the two must match.")
            else:
                out("  no threshold dict matched; patch by hand using the line numbers above.")
    if a.run_all and os.path.exists(a.run_all):
        t = read(a.run_all)
        m = re.search(r"NOISE_LEVELS=\S+", t)
        if m:
            out(f"  run_all.sh line {line_of(t, m.start())}: {m.group(0)}")
            out("  the sweep script reads singular NOISE_LEVEL (percent) or --noise-levels (fractions); "
                "plural NOISE_LEVELS is ignored. Launch one task per level or pass --noise-levels.")


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--supp", help="supplement .tex")
    ap.add_argument("--paper", help="main paper .tex")
    ap.add_argument("--bench", help="benchmark_results.json")
    ap.add_argument("--exp2-dir", help="feynman-tests/exp2 directory of per-domain JSONs")
    ap.add_argument("--merge-out", default="benchmark_results_merged.json")
    ap.add_argument("--shards", help="glob of noise shard JSONs")
    ap.add_argument("--sweep-script", help="run_noise_sweep_benchmark.py")
    ap.add_argument("--run-all", help="run_all.sh")
    ap.add_argument("--root", help="project root for checking reproduction-command paths")
    ap.add_argument("--apply", action="store_true", help="make edits (backups are written)")
    ap.add_argument("--brackets", choices=["comment", "delete"], default="comment")
    ap.add_argument("--thr-new", type=float, help="threshold to use for 2%% and 20%% noise")
    ap.add_argument("--only", type=int, nargs="*", help="run only these item numbers")
    a = ap.parse_args()
    items = {1: item1, 2: item2, 3: item3, 4: item4, 5: item5, 6: item6}
    out("# Audit report" + (" (APPLY mode)" if a.apply else " (read-only)"))
    for n, fn in items.items():
        if not a.only or n in a.only:
            fn(a)
    with open("audit_report.md", "w") as f:
        f.write("\n".join(REPORT) + "\n")
    print("\nreport saved to audit_report.md")


if __name__ == "__main__":
    main()
