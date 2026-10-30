#!/usr/bin/env python3
"""
ablation_conditions.py  --  Step 4: named vs neutral descriptions, blind flag, cache salt.

What it does
  plan : builds NAMED and NEUTRAL versions of every benchmark case, withholds
         ground truth from case metadata, runs a leakage check on the neutral
         set, and writes the condition table (arm x description x blind x salt).
  run  : for every (condition, seed) it patches get_llm_prior so each call gets
         the condition's cache_salt and blind flag, calls YOUR runner, and
         records how many prior calls were actually intercepted.

Conditions (LLM arms get both description types; non-LLM arms run once):
  pysr_only, hypatia_nollm   description n/a     (no LLM, text unused)
  pure_llm  / hypatia        named   -> blind=False
  pure_llm  / hypatia        neutral -> blind=True
cache_salt = "<run_tag>|<arm>|<description>|blind=<bool>"  so cached answers
cannot leak between conditions.

Runner contract (write a thin adapter around your existing code):
    runner(cases, case_ids, arm, seed, condition, out_dir) -> JSON-serialisable
  cases = list of (description, X, y, var_names, metadata) tuples.

Usage
  python ablation_conditions.py plan --out cond_plan   # protocol: hypatiax/protocols/ (override: LLM_SENS_PROTOCOL=module:Class)
  python ablation_conditions.py run  --plan cond_plan --runner my_adapter:run \
      --prior-target hypatiax.core.llm:get_llm_prior --seeds 42 99 123
Patch EVERY module that imported get_llm_prior with `from x import get_llm_prior`
(repeat --prior-target); patching only the defining module misses those copies.
`run` warns if an LLM arm made zero intercepted prior calls.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib
import inspect
import json
import os
import pickle
import re
import sys
from pathlib import Path

ARMS = {"pysr_only": False, "hypatia_nollm": False, "pure_llm": True, "hypatia": True}
KEEP_META = {"extrapolation_test", "split_index", "noise_frac_train",
             "train_ranges", "description_named", "seed"}
ALLOWED_META_STR = {"neutral", "<withheld>"}


# ----------------------------------------------------------------- conditions
def build_conditions(arms, run_tag):
    conds = []
    for arm in arms:
        if not ARMS[arm]:
            conds.append(dict(id=f"{arm}__na", arm=arm, description="n/a",
                              blind=None, cache_salt=None, case_set="named"))
            continue
        for desc in ("named", "neutral"):
            blind = desc == "neutral"
            conds.append(dict(
                id=f"{arm}__{desc}", arm=arm, description=desc, blind=blind,
                cache_salt=f"{run_tag}|{arm}|{desc}|blind={blind}", case_set=desc))
    return conds


# ------------------------------------------------------------------- neutralise
def _withhold(meta):
    m = dict(meta)
    if "ground_truth" in m:
        m["ground_truth"] = "<withheld>"
    return m


def neutralise(case):
    desc, X, y, names, meta = case
    nn = [f"x{i}" for i in range(len(names))]
    nm = {k: v for k, v in meta.items() if k in KEEP_META}
    nm["domain"] = "neutral"
    nm["description_named"] = False
    ev = meta.get("test_range_extrapolated_var")
    if ev:
        nm["test_range_extrapolated_var"] = {
            "var": nn[names.index(ev["var"])], "range": ev["range"]}
    nm["ground_truth"] = "<withheld>"
    new_desc = f"Find the function y = f({', '.join(nn)}) that fits the data."
    return (new_desc, X, y, nn, nm)


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from _strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _strings(v)


def leak_check(case, cid):
    desc, _, _, names, meta = case
    assert all(re.fullmatch(r"x\d+", n) for n in names), f"{cid}: names {names}"
    assert re.fullmatch(r"Find the function y = f\(x\d+(, x\d+)*\) that fits the data\.", desc), \
        f"{cid}: description {desc!r}"
    for s in _strings({k: v for k, v in meta.items() if k not in {"train_ranges"}}):
        if s in meta or s in ALLOWED_META_STR or re.fullmatch(r"x\d+|var|range|<withheld>", s):
            continue
        raise AssertionError(f"{cid}: unexpected string in neutral metadata: {s!r}")


# ------------------------------------------------------------------- patching
def _wrap(orig, salt, blind, log, strict):
    params = inspect.signature(orig).parameters
    has_kw = any(p.kind is p.VAR_KEYWORD for p in params.values())

    def w(*a, **k):
        for name, val in (("cache_salt", salt), ("blind", blind)):
            if name in params or has_kw:
                if name in k and k[name] != val:
                    log["overrides"] += 1
                k[name] = val
            elif strict:
                raise TypeError(f"get_llm_prior has no '{name}' parameter; "
                                f"cannot enforce this condition")
            else:
                log["missing_params"].add(name)
        log["calls"] += 1
        return orig(*a, **k)
    return w


@contextlib.contextmanager
def patched(targets, salt, blind, log, strict=True):
    saved = []
    try:
        for t in targets:
            mod, attr = t.split(":")
            m = importlib.import_module(mod)
            orig = getattr(m, attr)
            saved.append((m, attr, orig))
            setattr(m, attr, _wrap(orig, salt, blind, log, strict))
        yield
    finally:
        for m, attr, orig in saved:
            setattr(m, attr, orig)


# ------------------------------------------------------------------- commands
def _load(spec):
    mod, name = spec.split(":")
    try:
        return getattr(importlib.import_module(mod), name)
    except ModuleNotFoundError as e:
        # bare protocol module name -> look in hypatiax/protocols/ as well
        if "." not in mod and e.name == mod:
            return getattr(importlib.import_module(f"hypatiax.protocols.{mod}"), name)
        raise


def cmd_plan(a):
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    proto = _load(a.protocol)()
    domains = a.domains or proto.get_all_domains()
    named, neutral, ids, truth = [], [], [], {}
    for d in domains:
        for i, case in enumerate(proto.load_test_data(d, a.n)):
            cid = f"{d}:{i:02d}"
            truth[cid] = case[4].get("ground_truth")
            ids.append(cid)
            named.append((case[0], case[1], case[2], case[3], _withhold(case[4])))
            nc = neutralise(case)
            leak_check(nc, cid)
            neutral.append(nc)
    conds = build_conditions(a.arms, a.run_tag)
    for name, obj in (("cases_named", named), ("cases_neutral", neutral), ("case_ids", ids)):
        (out / f"{name}.pkl").write_bytes(pickle.dumps(obj))
    (out / "truth_registry.json").write_text(json.dumps(truth, indent=1))
    manifest = dict(run_tag=a.run_tag, n=a.n, n_cases=len(ids), domains=domains,
                    conditions=conds, ground_truth_withheld_from_metadata=True,
                    note="Residual leak: numeric ranges are unchanged and can hint at units.")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"{len(ids)} cases; leak check passed on neutral set; {len(conds)} conditions")
    for c in conds:
        print(" ", c["id"], "| blind =", c["blind"], "| salt =", c["cache_salt"])


def cmd_run(a):
    plan = Path(a.plan)
    man = json.loads((plan / "manifest.json").read_text())
    sets = {k: pickle.loads((plan / f"cases_{k}.pkl").read_bytes())
            for k in ("named", "neutral")}
    ids = pickle.loads((plan / "case_ids.pkl").read_bytes())
    runner = _load(a.runner)
    os.environ.setdefault("LLM_SENS_TRUTH", str(plan / "truth_registry.json"))
    out = Path(a.out or plan / "results")
    report = []
    only = getattr(a, "only", None) or []
    known = {c["id"] for c in man["conditions"]}
    unknown = [o for o in only if o not in known]
    if unknown:
        sys.exit(f"unknown condition id(s): {unknown}; known: {sorted(known)}")
    prefix = getattr(a, "prefix", None)
    for c in man["conditions"]:
        if only and c["id"] not in only:
            continue
        for seed in a.seeds:
            # flat layout (--prefix): one file per condition+seed directly in `out`
            f = (out / f"{prefix}_{c['id']}_seed{seed}.json") if prefix \
                else (out / c["id"] / f"seed{seed}.json")
            if f.exists() and not a.force:
                print("skip (exists):", f)
                continue
            f.parent.mkdir(parents=True, exist_ok=True)
            log = {"calls": 0, "overrides": 0, "missing_params": set(), "prompts": []}
            if ARMS[c["arm"]]:
                # one cached LLM draw per seed (hypatia.py docs: cache_salt=f"seed{seed}")
                salt = f'{c["cache_salt"]}|seed{seed}'
                ctx = contextlib.ExitStack()
                ctx.enter_context(patched(a.prior_target, salt, c["blind"], log,
                                          strict=not a.allow_missing_params))
                for h in (getattr(a, "hook", None) or []):
                    ctx.enter_context(_load(h)(salt, c["blind"], log))
            else:
                ctx = contextlib.nullcontext()
            with ctx:
                res = runner(cases=sets[c["case_set"]], case_ids=ids, arm=c["arm"],
                             seed=seed, condition=c, out_dir=f.parent)
            f.write_text(json.dumps(res, default=str, indent=1))
            row = dict(condition=c["id"], seed=seed, prior_calls=log["calls"],
                       overrides=log["overrides"],
                       missing_params=sorted(log["missing_params"]),
                       prompt_samples=log["prompts"][:2])
            report.append(row)
            if ARMS[c["arm"]] and log["calls"] == 0:
                print(f"WARNING {c['id']} seed {seed}: 0 intercepted prior calls. "
                      f"Add --prior-target (pure_llm) / --hook (hypatia) for the LLM call path.",
                      file=sys.stderr)
            print(row)
    rp = out / (getattr(a, "report_name", None) or "run_report.json")
    if rp.exists():   # several invocations may share one shard report: merge, newest wins
        try:
            prev = json.loads(rp.read_text())
        except Exception:
            prev = []
        keys = {(r["condition"], r["seed"]) for r in report}
        report = [r for r in prev if (r["condition"], r["seed"]) not in keys] + report
    rp.write_text(json.dumps(report, indent=1))


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    pl = s.add_parser("plan")
    pl.add_argument("--protocol",
                    default=__import__("os").environ.get("LLM_SENS_PROTOCOL",
                    "hypatiax.protocols.experiment_protocol_defi_llm_sensitive:DeFiLLMSensitiveProtocol"))
    pl.add_argument("--domains", nargs="*")
    pl.add_argument("--n", type=int, default=40)
    pl.add_argument("--arms", nargs="+", default=list(ARMS), choices=list(ARMS))
    pl.add_argument("--run-tag", default="exp1")
    pl.add_argument("--out", default="cond_plan")
    pl.set_defaults(f=cmd_plan)
    r = s.add_parser("run")
    r.add_argument("--plan", default="cond_plan")
    r.add_argument("--runner", required=True)
    r.add_argument("--prior-target", action="append", default=[],
                   help="module:function, repeat for every import site")
    r.add_argument("--seeds", nargs="+", type=int, default=[42, 99, 123])
    r.add_argument("--out")
    r.add_argument("--force", action="store_true")
    r.add_argument("--hook", action="append", default=[],
                   help="module:factory(salt, blind, log) -> context manager (e.g. the Hypatia arm hook)")
    r.add_argument("--only", nargs="*", default=[], help="run only these condition ids")
    r.add_argument("--prefix", help="flat output files named <prefix>_<condition>_seed<N>.json")
    r.add_argument("--report-name", help="file name for the run report (default run_report.json)")
    r.add_argument("--allow-missing-params", action="store_true",
                   help="don't fail if get_llm_prior lacks cache_salt/blind (NOT recommended)")
    r.set_defaults(f=cmd_run)
    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
