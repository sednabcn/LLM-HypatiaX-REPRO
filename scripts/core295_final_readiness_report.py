#!/usr/bin/env python3
"""Read-only, fail-closed static readiness audit for Core-295."""
from __future__ import annotations
import argparse, json, re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = ("Chemistry", "Biology", "Physics", "DeFi AMM", "DeFi Risk")

def load_json(path, label, blockers):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        blockers.append(f"{label}: {exc}"); return {}

def load_jsonl(path, label, blockers):
    rows=[]
    if not path.exists(): return rows
    for n,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        try:
            row=json.loads(line)
            if isinstance(row,dict): rows.append(row)
            else: blockers.append(f"{label}:{n}: row is not an object")
        except json.JSONDecodeError as exc: blockers.append(f"{label}:{n}: malformed JSONL: {exc}")
    return rows

def present(v): return v is not None and v != "" and v != [] and v != {}

def build(a):
    b=[]; cat=load_json(a.catalogue,"catalogue",b); tau=load_json(a.tau,"tau manifest",b)
    entries=cat.get("entries",[]) if isinstance(cat.get("entries"),list) else []
    srcs=cat.get("source_register",[]) if isinstance(cat.get("source_register"),list) else []
    src={x.get("source_id"):x for x in srcs if isinstance(x,dict) and x.get("source_id")}
    counts={d:Counter() for d in DOMAINS}; ids=Counter(); fps=Counter()
    units=set(); fam_by_unit={}
    for i,e in enumerate(entries):
        if not isinstance(e,dict): b.append(f"entries[{i}] is not an object"); continue
        d=e.get("domain"); eid=e.get("equation_id",f"index-{i}")
        if d not in counts: b.append(f"{eid}: invalid domain {d!r}"); continue
        counts[d][e.get("status","missing")]+=1; ids[eid]+=1; fps[e.get("structural_fingerprint")]+=1
        refs=e.get("source_ids")
        if not isinstance(refs,list) or not refs or not any(r in src and src[r].get("domain") in (d,"cross-domain") for r in refs):
            b.append(f"{eid}: no registered source in matching domain")
        if e.get("status")=="accepted":
            for field in ("reviewer","reviewed_on","equivalence_review","independence_unit_id","source_family_id"):
                if not present(e.get(field)): b.append(f"{eid}: accepted row missing {field}")
            review=e.get("equivalence_review")
            if isinstance(review,dict) and (review.get("classification")!="E4" or not present(review.get("rationale"))):
                b.append(f"{eid}: accepted row requires E4 equivalence classification and rationale")
            unit=e.get("independence_unit_id"); family=e.get("source_family_id")
            if present(unit):
                units.add(unit)
                if unit in fam_by_unit and fam_by_unit[unit]!=family: b.append(f"{eid}: independence unit maps to conflicting source families")
                fam_by_unit[unit]=family
    for label,c in (("equation IDs",ids),("fingerprints",fps)):
        n=sum(1 for k,v in c.items() if k and v>1)
        if n: b.append(f"duplicate {label}: {n}")
    domains={}
    for d in DOMAINS:
        total=sum(counts[d].values()); accepted=counts[d]["accepted"]
        domains[d]={"total":total,"accepted":accepted,"by_status":dict(counts[d])}
        if accepted!=59: b.append(f"{d}: {accepted}/59 accepted")
        if total>59: b.append(f"{d}: {total} rows exceeds cap of 59")
    if len(entries)!=295: b.append(f"catalogue has {len(entries)}/295 entries")
    if cat.get("status")!="ready": b.append(f"catalogue status is {cat.get('status')!r}, not ready")
    frame=cat.get("sampling_frame") if isinstance(cat.get("sampling_frame"),dict) else {}
    frame_fields=("source_universe","inclusion_exclusion_rules","selection_method","independent_statistical_unit","source_family_definition")
    missing_frame=[k for k in frame_fields if not present(frame.get(k))]
    if frame.get("status")!="frozen" or missing_frame: b.append("sampling frame incomplete: "+", ".join(missing_frame or ["status"]))
    protocol=tau.get("approved_protocol",{}) if isinstance(tau.get("approved_protocol"),dict) else {}
    tau_fields=("calibration_equations","candidate_tau_values","category_list","category_definition","independence_justification","frozen_edge_definition","calibration_data_manifest_sha256","calibration_code_commit","evaluator_version")
    missing_tau=[k for k in tau_fields if not present(tau.get(k))]
    if tau.get("status")!="ready_for_calibration" or missing_tau: b.append("tau manifest incomplete: "+", ".join(missing_tau or ["status"]))
    pipeline={}
    for label,path in (("discovery",a.discovery),("OA provenance",a.oa),("equation leads",a.leads)):
        pipeline[label]={"path":str(path),"records":len(load_jsonl(path,label,b))}
    pipeline["review_packets"]=len(list(a.packets.glob("*.md"))) if a.packets.exists() else 0
    pipeline["staged_records"]=len(list(a.staged.rglob("*.json"))) if a.staged.exists() else 0
    workflows={}
    for label,path in (("runner",a.runner),("fresh_rerun",a.fresh),("smoke",a.smoke)):
        try: text=path.read_text(encoding="utf-8")
        except OSError as exc: text=""; b.append(f"{label} workflow unreadable: {exc}")
        workflows[label]={"exists":bool(text),"workflow_dispatch":"workflow_dispatch:" in text,
            "exp295_ablation":bool(re.search(r"(?<![A-Za-z0-9_])exp295_ablation(?![A-Za-z0-9_])",text)),
            "exp295":bool(re.search(r"(?<![A-Za-z0-9_])exp295(?![A-Za-z0-9_])",text)),
            "exp295b":bool(re.search(r"(?<![A-Za-z0-9_])exp295b(?![A-Za-z0-9_])",text)),
            "n_shards":"n_shards" in text,"JULIA_NUM_THREADS":"JULIA_NUM_THREADS" in text}
    if not workflows["runner"]["exp295_ablation"] or not workflows["runner"]["exp295"]: b.append("runner workflow does not register exp295_ablation and exp295")
    if not workflows["runner"]["exp295b"]: b.append("exp295b is not registered")
    if not workflows["runner"]["n_shards"]: b.append("runner workflow has no visible shard input")
    try:
        design=a.design.read_text(encoding="utf-8")
        if "Open decisions before freezing" in design: b.append("structural-equivalence policy remains a draft with open decisions")
    except OSError as exc: b.append(f"design protocol unreadable: {exc}")
    return {"report_schema":"core295-final-readiness-v1","status":"READY_FOR_AUTHORIZED_RERUN" if not b else "NOT_READY",
        "scope":"static evidence/configuration audit only; not scientific certification or run authorization",
        "scientific_runs_executed":False,"validators_executed":False,"workflow_dispatched":False,
        "blockers":b,"evidence":{"catalogue":{"status":cat.get("status"),"entries":len(entries),"source_records":len(srcs),
        "domains":domains,"sampling_frame_status":frame.get("status"),"sampling_frame_missing_fields":missing_frame,
        "accepted_independence_units":len(units)},"tau_calibration":{"status":tau.get("status"),"approved_protocol":protocol,
        "equations":len(tau.get("calibration_equations",[])) if isinstance(tau.get("calibration_equations"),list) else None,
        "candidate_tau_values":len(tau.get("candidate_tau_values",[])) if isinstance(tau.get("candidate_tau_values"),list) else None,
        "missing_ready_fields":missing_tau},"source_pipeline":pipeline,"workflow_static_audit":workflows,
        "stage_mapping":{"mapping_status":"verified correspondence; Core-295 implementation absent","exp295_ablation":"exp1_ablation — per-equation ablation execution","exp295":"exp1_ablation_aggregate — same-run shard merge and aggregate ablation analysis",
        "exp295b":"exp1_five — separate five-system comparison"}}}

def markdown(r):
    e=r["evidence"]; out=["# Core-295 final readiness report","",f"**Status:** {r['status']}","",r["scope"],"",
    f"- Blockers: {len(r['blockers'])}","- Scientific runs executed: no","- Validators executed: no","- Workflow dispatched: no","","## Catalogue"]
    for d,x in e["catalogue"]["domains"].items(): out.append(f"- {d}: {x['accepted']}/59 accepted ({x['total']} total)")
    out += ["","## Tau calibration","",json.dumps(e["tau_calibration"],indent=2),"","## Workflow static audit","",json.dumps(e["workflow_static_audit"],indent=2),
    "","## Source pipeline","",json.dumps(e["source_pipeline"],indent=2),"","## Blockers"]
    out += [f"- {x}" for x in r["blockers"]] or ["- None"]
    out += ["","## Interpretation","","A ready status would be a static gate only, not authorization to run. Scientific review and user authorization remain separate. This report never accepts equations.",""]
    return "\n".join(out)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalogue",type=Path,default=ROOT/"config/core295_catalogue.json")
    p.add_argument("--tau",type=Path,default=ROOT/"config/tau_calibration_manifest.json")
    p.add_argument("--discovery",type=Path,default=ROOT/"data/core295_discovery_queue.jsonl")
    p.add_argument("--oa",type=Path,default=ROOT/"data/core295_open_access/provenance.jsonl")
    p.add_argument("--leads",type=Path,default=ROOT/"data/core295_equation_review_queue.jsonl")
    p.add_argument("--packets",type=Path,default=ROOT/"data/core295_candidate_review_packets")
    p.add_argument("--staged",type=Path,default=ROOT/"data/core295_staging")
    p.add_argument("--runner",type=Path,default=ROOT/".github/workflows/ci_runner_repro.yml")
    p.add_argument("--fresh",type=Path,default=ROOT/".github/workflows/ci_fresh_rerun.yml")
    p.add_argument("--smoke",type=Path,default=ROOT/".github/workflows/ci_runner_smoke.yml")
    p.add_argument("--design",type=Path,default=ROOT/"docs/CORE295_DESIGN_PROTOCOL.md")
    p.add_argument("--output-json",type=Path); p.add_argument("--output-md",type=Path)
    a=p.parse_args(); r=build(a); md=markdown(r)
    if a.output_json:
        with a.output_json.open("x",encoding="utf-8") as f: json.dump(r,f,indent=2); f.write("\n")
    if a.output_md:
        with a.output_md.open("x",encoding="utf-8") as f: f.write(md)
    if not a.output_json and not a.output_md: print(md)
    return 0 if r["status"]=="READY_FOR_AUTHORIZED_RERUN" else 1

if __name__=="__main__": raise SystemExit(main())
