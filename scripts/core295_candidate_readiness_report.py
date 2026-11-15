#!/usr/bin/env python3
"""Report Core-295 evidence gaps and human-review readiness without accepting candidates."""
from __future__ import annotations
import argparse, hashlib, json, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = ("Chemistry", "Biology", "Physics", "DeFi AMM", "DeFi Risk")
DEFAULTS = {
    "leads": ROOT / "data/core295_equation_review_queue.jsonl",
    "provenance": ROOT / "data/core295_open_access/provenance.jsonl",
    "discovery": ROOT / "data/core295_discovery_queue.jsonl",
    "catalogue": ROOT / "config/core295_catalogue.json",
    "packets": ROOT / "data/core295_candidate_review_packets",
    "output": ROOT / "data/core295_candidate_readiness.md",
}

def read_jsonl(path):
    rows, malformed = [], 0
    if not path.exists(): return rows, malformed
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict): rows.append(obj)
                else: malformed += 1
            except json.JSONDecodeError: malformed += 1
    return rows, malformed

def load_json(path):
    if not path.exists(): return {}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except (OSError, json.JSONDecodeError): return {}

def doi(value):
    value = str(value or "").strip().lower()
    return re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value)

def indexes(rows):
    by_doi, by_id = {}, {}
    for row in rows:
        d = doi(row.get("doi"))
        ident = str(row.get("source_record_id") or row.get("record_id") or "").strip()
        if d: by_doi.setdefault(d, row)
        if ident: by_id.setdefault(ident, row)
    return by_doi, by_id

def lookup(row, ix):
    d, ident = ix
    rid = str(row.get("source_record_id") or "").strip()
    if rid and rid in ident: return ident[rid]
    return d.get(doi(row.get("doi")))

def packet_name(row):
    raw = "|".join((doi(row.get("doi")), str(row.get("source_sha256") or ""),
                    str(row.get("pdf_page_index") or ""), str(row.get("snippet_sha256") or "")))
    return "CORE295-REVIEW-" + hashlib.sha256(raw.encode()).hexdigest()[:16] + ".md"

def md(value):
    if value is None or value == "": return "—"
    return str(value).replace("|", r"\|").replace("\n", " ").replace("\r", " ")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in DEFAULTS:
        p.add_argument("--" + key, type=Path, default=DEFAULTS[key])
    p.add_argument("--stdout", action="store_true")
    a = p.parse_args()
    leads, bad_l = read_jsonl(a.leads)
    provenance, bad_p = read_jsonl(a.provenance)
    discovery, bad_d = read_jsonl(a.discovery)
    catalogue = load_json(a.catalogue)
    entries = catalogue.get("entries", []) if isinstance(catalogue.get("entries"), list) else []
    prov_ix, disc_ix = indexes(provenance), indexes(discovery)
    accepted, proposed = Counter(), Counter()
    for entry in entries:
        domain = entry.get("domain", "Unassigned")
        (accepted if entry.get("status") == "accepted" else proposed)[domain] += 1

    buckets, domain_rows, gaps = Counter(), defaultdict(list), Counter()
    packet_count = 0
    for row in leads:
        domain = row.get("domain") or "Unassigned"
        oa, bib = lookup(row, prov_ix), lookup(row, disc_ix)
        missing = []
        for label, key in (
            ("DOI", "doi"), ("title", "title"), ("domain", "domain"),
            ("source record ID", "source_record_id"), ("source URL", "source_url"),
            ("PDF SHA-256", "source_sha256"), ("PDF page index", "pdf_page_index"),
            ("snippet text", "snippet"), ("snippet SHA-256", "snippet_sha256"),
        ):
            if row.get(key) in (None, ""): missing.append(label)
        if oa is None: missing.append("matched OA provenance")
        elif oa.get("status") != "downloaded": missing.append("successful OA download")
        if oa and row.get("source_sha256") and oa.get("sha256") != row.get("source_sha256"):
            missing.append("PDF hash/provenance match")
        if bib is None: missing.append("matched bibliographic discovery record")
        pdf_path = row.get("pdf_path") or (oa or {}).get("local_file")
        if not pdf_path or not Path(str(pdf_path)).is_file():
            missing.append("locally available PDF artifact")
        packet = a.packets / packet_name(row)
        if not packet.is_file(): missing.append("generated human-review packet")
        else: packet_count += 1
        if not missing: level = "evidence packet ready for human source-page review"
        elif len(missing) <= 3: level = "near-ready; limited evidence gaps"
        else: level = "incomplete evidence"
        buckets[level] += 1
        for item in missing: gaps[item] += 1
        domain_rows[domain].append((row, level, missing, packet.name))

    target = catalogue.get("per_domain_target", 59)
    total_target = catalogue.get("target_equation_count", 295)
    lines = [
        "# Core-295 candidate evidence-readiness and review-gap report", "",
        "> Operational triage only. “Ready” means the evidence packet has expected metadata/artifact links for a human to inspect the original source. It does not mean the source is primary, the equation is correct, structurally distinct, independent, benchmarkable, or accepted.", "",
        "## Snapshot", "",
        "- Extraction leads: " + str(len(leads)),
        "- OA provenance records: " + str(len(provenance)),
        "- Bibliographic discovery records: " + str(len(discovery)),
        "- Catalogue entries: " + str(len(entries)),
        "- Catalogue accepted: " + str(sum(accepted.values())),
        "- Target: " + str(total_target) + " total; " + str(target) + " per domain",
        "- Existing review packets matched: " + str(packet_count) + "/" + str(len(leads)),
        "- Malformed JSONL records (leads/provenance/discovery): " + "/".join(map(str, (bad_l, bad_p, bad_d))),
        "",
        "## Evidence-readiness distribution", "",
        "| Triage category | Leads |", "|---|---:|"
    ]
    for label in ("evidence packet ready for human source-page review", "near-ready; limited evidence gaps", "incomplete evidence"):
        lines.append("| " + label + " | " + str(buckets[label]) + " |")
    lines += ["", "## Domain shortfall and review queue", "",
              "| Domain | Leads | Proposed catalogue | Accepted | Target | Accepted shortfall | Ready packets |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for domain in DOMAINS:
        rows = domain_rows.get(domain, [])
        ready = sum(not miss for _, _, miss, _ in rows)
        lines.append("| " + domain + " | " + str(len(rows)) + " | " + str(proposed[domain]) +
                     " | " + str(accepted[domain]) + " | " + str(target) + " | " +
                     str(max(0, target - accepted[domain])) + " | " + str(ready) + " |")
    for domain in sorted(set(domain_rows) - set(DOMAINS)):
        lines.append("| " + md(domain) + " | " + str(len(domain_rows[domain])) + " | " +
                     str(proposed[domain]) + " | " + str(accepted[domain]) + " | — | — | — |")
    lines += ["", "## Most common evidence gaps", "", "| Missing item | Leads affected |", "|---|---:|"]
    if gaps:
        for item, count in gaps.most_common(): lines.append("| " + md(item) + " | " + str(count) + " |")
    else: lines.append("| No operational evidence gaps detected | 0 |")
    lines += ["", "## Lead-level triage", "",
              "Triage is not a scientific confidence score. Inspect the original PDF even for a packet marked ready.", ""]
    for domain in (*DOMAINS, *sorted(set(domain_rows) - set(DOMAINS))):
        rows = domain_rows.get(domain, [])
        lines += ["### " + domain, ""]
        if not rows:
            lines += ["No extracted leads currently recorded.", ""]
            continue
        lines += ["| Title / DOI | Triage | Missing evidence | Packet |", "|---|---|---|---|"]
        for row, level, missing, packet in sorted(rows, key=lambda x: (len(x[2]), str(x[0].get("title", "")).casefold())):
            identity = md(row.get("title"))
            if row.get("doi"): identity += " / " + md(row.get("doi"))
            packet_cell = chr(96) + packet + chr(96) if (a.packets / packet).is_file() else "Not generated"
            lines.append("| " + identity + " | " + level + " | " +
                         (md(", ".join(missing)) if missing else "None detected") + " | " + packet_cell + " |")
    lines += ["", "## Mandatory scientific gates not automated", "",
              "A qualified reviewer must verify primary-source identity/version; inspect the original page image; record printed page and equation number; transcribe the complete governing equation/system; verify symbols, units, assumptions and validity; assess Core-15 overlap and E0–E5 equivalence; assign source-family and independent statistical-unit IDs with rationale; confirm deterministic generator and valid train/extrapolation ranges; and obtain independent review/sign-off.",
              "",
              "No status is changed by this report. It does not run OCR, symbolic algebra, validators, experiments, workflows, paid compute or live protocol calls. It does not modify the catalogue, queues or review packets.", ""]
    report = "\n".join(lines)
    if a.stdout: print(report)
    else:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(report, encoding="utf-8")
        print("Wrote " + str(a.output))
        print("Leads: " + str(len(leads)) + "; ready for human source-page review: " +
              str(buckets["evidence packet ready for human source-page review"]) +
              "; near-ready: " + str(buckets["near-ready; limited evidence gaps"]) +
              "; incomplete: " + str(buckets["incomplete evidence"]))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
