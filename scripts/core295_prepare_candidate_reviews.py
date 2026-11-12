#!/usr/bin/env python3
"""Build unverified Core-295 review packets from extracted leads and provenance."""
from __future__ import annotations
import argparse, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LEADS = ROOT / "data/core295_equation_review_queue.jsonl"
PROVENANCE = ROOT / "data/core295_open_access/provenance.jsonl"
DISCOVERY = ROOT / "data/core295_discovery_queue.jsonl"
TEMPLATE = ROOT / "docs/templates/CORE295_EQUATION_SOURCE_REVIEW_TEMPLATE.md"
OUT = ROOT / "data/core295_candidate_review_packets"

def read_jsonl(path: Path):
    rows, malformed = [], 0
    if not path.exists():
        return rows, malformed
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            try:
                item = json.loads(line)
                if isinstance(item, dict): rows.append(item)
                else: malformed += 1
            except json.JSONDecodeError: malformed += 1
    return rows, malformed

def doi_key(value):
    value = str(value or "").strip().lower()
    return re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value)

def indexes(rows):
    doi, rid = {}, {}
    for row in rows:
        key = doi_key(row.get("doi"))
        ident = str(row.get("source_record_id") or row.get("record_id") or "").strip()
        if key: doi.setdefault(key, row)
        if ident: rid.setdefault(ident, row)
    return doi, rid

def matched(lead, ix):
    doi, rid = ix
    ident = str(lead.get("source_record_id") or "").strip()
    if ident and ident in rid: return rid[ident]
    return doi.get(doi_key(lead.get("doi")))

def cell(value):
    if value is None or value == "": return "Not supplied"
    return str(value).replace("|", r"\|").replace("\r", " ").replace("\n", " ")

def code_fence(value):
    text = str(value or "[No extracted snippet supplied.]")
    tick = chr(96)
    runs = re.findall(re.escape(tick) + r"+", text)
    fence = tick * max(3, max((len(x) for x in runs), default=0) + 1)
    return fence + "text\n" + text + "\n" + fence

def packet_id(row):
    key = "|".join((doi_key(row.get("doi")), str(row.get("source_sha256") or ""),
                    str(row.get("pdf_page_index") or ""), str(row.get("snippet_sha256") or "")))
    return "CORE295-REVIEW-" + hashlib.sha256(key.encode()).hexdigest()[:16]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--leads", type=Path, default=LEADS)
    p.add_argument("--provenance", type=Path, default=PROVENANCE)
    p.add_argument("--discovery", type=Path, default=DISCOVERY)
    p.add_argument("--template", type=Path, default=TEMPLATE)
    p.add_argument("--output-dir", type=Path, default=OUT)
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--stdout-summary", action="store_true")
    a = p.parse_args()
    if not a.leads.is_file(): p.error("extraction lead queue not found: " + str(a.leads))
    if not a.template.is_file(): p.error("review template not found: " + str(a.template))
    leads, bad_l = read_jsonl(a.leads)
    prov, bad_p = read_jsonl(a.provenance)
    disc, bad_d = read_jsonl(a.discovery)
    prov_ix, disc_ix = indexes(prov), indexes(disc)
    template = a.template.read_text(encoding="utf-8")
    a.output_dir.mkdir(parents=True, exist_ok=True)
    created = skipped = miss_p = miss_d = 0
    for lead in leads:
        pid = packet_id(lead)
        target = a.output_dir / (pid + ".md")
        if target.exists() and not a.overwrite:
            skipped += 1
            continue
        oa, bib = matched(lead, prov_ix), matched(lead, disc_ix)
        miss_p += oa is None
        miss_d += bib is None
        authors = (bib or {}).get("authors", [])
        if isinstance(authors, list): authors = "; ".join(map(str, authors))
        source_url = lead.get("source_url") or (oa or {}).get("final_source_url")
        artifact_hash = lead.get("source_sha256") or (oa or {}).get("sha256")
        lines = [
            "# Candidate review packet: " + pid, "",
            "> **UNVERIFIED REVIEW LEAD — NOT AN ACCEPTED EQUATION.**",
            "> Evidence assembly only; source identity, printed pagination, transcription, model correctness, structural inequivalence and statistical independence remain unverified.", "",
            "## Automated disposition", "",
            "- Packet ID: " + pid,
            "- Prepared UTC: " + datetime.now(timezone.utc).isoformat(),
            "- Candidate status: proposed",
            "- Equation verified: false",
            "- Structural review complete: false",
            "- Equivalence classification: E5 (unresolved)",
            "- Accepted: false",
            "- Reviewer: not assigned", "",
            "## Extraction lead", "",
            "| Field | Value |", "|---|---|",
            "| DOI | " + cell(lead.get("doi")) + " |",
            "| Title | " + cell(lead.get("title")) + " |",
            "| Domain | " + cell(lead.get("domain")) + " |",
            "| Source record ID | " + cell(lead.get("source_record_id")) + " |",
            "| Source URL | " + cell(source_url) + " |",
            "| PDF path | " + cell(lead.get("pdf_path")) + " |",
            "| PDF SHA-256 | " + cell(artifact_hash) + " |",
            "| PDF page index (not printed page) | " + cell(lead.get("pdf_page_index")) + " |",
            "| Text line range | " + cell(str(lead.get("snippet_first_text_line")) + "–" + str(lead.get("snippet_last_text_line"))) + " |",
            "| Snippet SHA-256 | " + cell(lead.get("snippet_sha256")) + " |",
            "| Extracted UTC | " + cell(lead.get("extracted_at")) + " |", "",
            "### Extracted text — inspection cue only", "", code_fence(lead.get("snippet")), "",
            "Check the original page image and complete model context. The PDF page index is not printed pagination; extraction is not authoritative.", "",
            "## Open-access retrieval provenance", "",
            "- Match: " + ("matched" if oa else "not found"),
            "- OpenAlex work ID: " + cell((oa or {}).get("openalex_id")),
            "- OA status reported: " + cell((oa or {}).get("oa_status")),
            "- Licence metadata reported: " + cell((oa or {}).get("license_reported_by_openalex")),
            "- Landing page: " + cell((oa or {}).get("best_oa_landing_page")),
            "- PDF URL: " + cell((oa or {}).get("best_oa_pdf_url")),
            "- Retrieved SHA-256: " + cell((oa or {}).get("sha256")),
            "- Local artifact: " + cell((oa or {}).get("local_file")),
            "- Retrieval status: " + cell((oa or {}).get("status")), "",
            "OA metadata/download does not establish primary-source status, legal permission, version of record or equation correctness.", "",
            "## Bibliographic discovery record", "",
            "- Match: " + ("matched" if bib else "not found"),
            "- Record ID: " + cell((bib or {}).get("record_id")),
            "- Title: " + cell((bib or {}).get("title")),
            "- Authors: " + cell(authors),
            "- Year / venue: " + cell((bib or {}).get("year")) + " / " + cell((bib or {}).get("container_title")),
            "- DOI / URL: " + cell((bib or {}).get("doi")) + " / " + cell((bib or {}).get("url")),
            "- Crossref full-text links: " + cell(json.dumps((bib or {}).get("crossref_fulltext_links", []), ensure_ascii=False)), "",
            "Crossref is discovery metadata, not proof of a primary source or governing equation.", "",
            "## Human source and equation review template", "", template, "",
            "## Final machine status", "",
            "- source_verified: **false**",
            "- equation_verified: **false**",
            "- structural_review_complete: **false**",
            "- equivalence_classification: **E5**",
            "- independence_assessed: **false**",
            "- accepted: **false**", "",
            "This helper does not edit the catalogue or any input queue.", ""
        ]
        target.write_text("\n".join(lines), encoding="utf-8")
        created += 1
    summary = "\n".join([
        "# Candidate review packet preparation", "",
        "- Prepared UTC: " + datetime.now(timezone.utc).isoformat(),
        "- Leads read: " + str(len(leads)),
        "- Packets created/replaced: " + str(created),
        "- Existing packets skipped: " + str(skipped),
        "- Leads without OA provenance match: " + str(miss_p),
        "- Leads without discovery match: " + str(miss_d),
        "- Malformed JSONL lines (leads/provenance/discovery): " + "/".join(map(str, (bad_l, bad_p, bad_d))),
        "- Output directory: " + str(a.output_dir), "",
        "Every packet remains unverified, E5/unresolved and unaccepted. Missing evidence is not inferred.", ""
    ])
    if a.stdout_summary: print(summary, end="")
    else:
        (a.output_dir / "README.md").write_text(summary, encoding="utf-8")
        print(summary, end="")
    print("No OCR, scientific validation, equivalence check, catalogue update, experiment or acceptance was performed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
