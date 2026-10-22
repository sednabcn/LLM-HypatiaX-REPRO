#!/usr/bin/env python3
"""Gate for bypass_audit.py output.

usage: check_bypass_audit.py <new.csv> [baseline.csv] [--allow-new-bypass] [--allow-count-drift]

Hard invariants (always enforced):
  I1  every bypassed task must be restored to the LLM path by HYPATIAX_DISABLE_HARDCODED=1
      (switch_on_returns_None == True)
Baseline comparison (only when baseline.csv is given):
  B1  per-suite task counts unchanged            (skip with --allow-count-drift)
  B2  no task newly bypassed vs. baseline        (skip with --allow-new-bypass)
  B3  tasks that disappeared from the audit      (same switch as B1)
Newly un-bypassed tasks are reported as notices, never failures.
Writes a Markdown report to $GITHUB_STEP_SUMMARY when set.
"""
import csv, os, sys, collections

def load(p):
    with open(p, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["bypassed"] = r["bypassed_when_switch_off"].strip() == "True"
        r["restored"] = r["switch_on_returns_None"].strip() == "True"
        r["key"] = (r["suite"], r["id_or_domain"], r["description"])
    return rows

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    new = load(args[0])
    base = load(args[1]) if len(args) > 1 and os.path.isfile(args[1]) else None
    fails, notes = [], []

    # I1
    for r in new:
        if r["bypassed"] and not r["restored"]:
            fails.append(f"I1 switch does NOT restore LLM path: [{r['suite']}] {r['id_or_domain']} ({r['method']})")

    cnt = collections.Counter(r["suite"] for r in new)
    byp = collections.Counter(r["suite"] for r in new if r["bypassed"])

    if base is None:
        notes.append("No baseline CSV found - only invariant I1 was checked.")
    else:
        bcnt = collections.Counter(r["suite"] for r in base)
        bbyp = collections.Counter(r["suite"] for r in base if r["bypassed"])
        nk, bk = {r["key"] for r in new}, {r["key"] for r in base}
        nbyp = {r["key"] for r in new if r["bypassed"]}
        bbypk = {r["key"] for r in base if r["bypassed"]}

        if "--allow-count-drift" not in flags:
            for s in sorted(set(cnt) | set(bcnt)):
                if cnt[s] != bcnt[s]:
                    fails.append(f"B1 task count drift in suite '{s}': baseline {bcnt[s]} -> now {cnt[s]}")
            for k in sorted(bk - nk):
                fails.append(f"B3 task vanished from audit: [{k[0]}] {k[1]}")
        else:
            notes.append("count drift allowed (--allow-count-drift)")

        newly = sorted(nbyp - bbypk)
        for k in newly:
            msg = f"B2 newly bypassed task: [{k[0]}] {k[1]} - {k[2][:70]}"
            (notes if "--allow-new-bypass" in flags else fails).append(msg)
        for k in sorted(bbypk - nbyp):
            notes.append(f"no longer bypassed: [{k[0]}] {k[1]}")

    # report
    lines = ["### bypass_audit gate", "", "| suite | tasks | bypassed |", "|---|---|---|"]
    for s in sorted(cnt):
        lines.append(f"| {s} | {cnt[s]} | {byp[s]} |")
    lines += ["", f"**Result: {'FAIL' if fails else 'PASS'}**"]
    if fails: lines += ["", "Failures:"] + [f"- {x}" for x in fails]
    if notes: lines += ["", "Notes:"] + [f"- {x}" for x in notes]
    report = "\n".join(lines)
    print(report)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(report + "\n")
    for x in fails: print(f"::error::{x}")
    for x in notes: print(f"::notice::{x}")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
