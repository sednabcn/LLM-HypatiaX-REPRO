#!/usr/bin/env python3
"""Resumable, metadata-only source discovery for the Core-295 equation project.

This script searches Crossref for bibliographic leads across the five target
domains, deduplicates DOI records, and writes a review queue. It NEVER extracts
or invents equations, changes the canonical catalogue, or marks entries accepted.
Primary-source inspection and structural review remain human decisions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "config" / "core295_catalogue.json"
DEFAULT_QUEUE = ROOT / "data" / "core295_discovery_queue.jsonl"
API = "https://api.crossref.org/works"
DOMAINS = {
    "Chemistry": [
        "electrochemical adsorption surface thermodynamics",
        "chemical reaction kinetics transport mass transfer",
        "phase equilibrium activity coefficient thermodynamics",
        "electrode kinetics Butler Volmer electrosorption",
        "colloid polymer rheology chemical engineering constitutive",
    ],
    "Biology": [
        "population ecology host parasite predator prey dynamics",
        "physiological transport biomechanics muscle cardiovascular",
        "epidemiology infectious disease transmission compartment model",
        "plant growth photosynthesis ecological interaction model",
        "neurobiology membrane electrophysiology kinetics",
    ],
    "Physics": [
        "continuum mechanics constitutive equation fluid stress",
        "electromagnetism electrodynamics constitutive material relation",
        "heat conduction radiation transport physical equation",
        "quantum mechanics scattering transport physical model",
        "nonlinear dynamics wave optics statistical physics equation",
    ],
    "DeFi AMM": [
        "automated market maker invariant decentralized exchange liquidity",
        "constant function market maker bonding curve",
        "concentrated liquidity automated market maker pricing",
        "stable swap invariant crypto asset exchange",
        "decentralized exchange liquidity pool fee invariant",
    ],
    "DeFi Risk": [
        "decentralized finance lending liquidation collateral risk model",
        "smart contract lending protocol health factor liquidation",
        "collateralized debt position liquidation mechanism",
        "on chain credit risk interest rate model",
        "decentralized finance oracle risk protocol mechanism",
    ],
}
ALLOWED_TYPES = {
    "journal-article", "proceedings-article", "book-chapter",
    "book", "report", "standard", "posted-content",
}


def clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def first(item: dict, key: str) -> str:
    value = item.get(key)
    if isinstance(value, list):
        return clean_text(value[0]) if value else ""
    return clean_text(value)


def doi_key(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value)
    return value


def load_known(manifest_path: Path) -> tuple[set[str], dict[str, int], int]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    known = set()
    for source in data.get("source_register", []):
        if isinstance(source, dict):
            doi = source.get("doi") or ""
            if doi:
                known.add(doi_key(str(doi)))
            url = str(source.get("url") or "").lower()
            match = re.search(r"10\.\d{4,9}/[-._;()/:a-z0-9]+", url)
            if match:
                known.add(doi_key(match.group(0)))
    for entry in data.get("entries", []):
        for source_id in entry.get("source_ids", []):
            known.add("source-id:" + str(source_id))
    accepted = Counter(
        e.get("domain") for e in data.get("entries", [])
        if e.get("status") == "accepted"
    )
    return known, {d: accepted[d] for d in DOMAINS}, len(data.get("entries", []))


def load_queue(path: Path) -> tuple[set[str], int]:
    keys: set[str] = set()
    count = 0
    if not path.exists():
        return keys, count
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            count += 1
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            doi = doi_key(str(item.get("doi") or ""))
            if doi:
                keys.add(doi)
    return keys, count


def crossref_search(query: str, rows: int, offset: int, timeout: int,
                    mailto: str | None) -> list[dict]:
    params = {
        "query.bibliographic": query,
        "rows": str(rows),
        "offset": str(offset),
        "select": "DOI,title,author,published,issued,created,type,container-title,volume,issue,page,URL,abstract,score,subject",
    }
    if mailto:
        params["mailto"] = mailto
    url = API + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url, headers={"User-Agent": "Core295SourceDiscovery/1.0 (metadata-only; "
                                    "mailto=" + (mailto or "not-specified") + ")"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("message", {}).get("items", [])


def publication_year(item: dict) -> int | None:
    for field in ("published", "issued", "created"):
        date = item.get(field, {}).get("date-parts", [])
        if date and date[0] and isinstance(date[0][0], int):
            return date[0][0]
    return None


def normalize(item: dict, domain: str, query: str) -> dict | None:
    doi = doi_key(str(item.get("DOI") or ""))
    if not doi:
        return None
    title = first(item, "title")
    if not title:
        return None
    authors = []
    for author in item.get("author", []) or []:
        name = " ".join(x for x in (
            clean_text(author.get("given")), clean_text(author.get("family"))
        ) if x)
        if name:
            authors.append(name)
    raw_type = clean_text(item.get("type"))
    if raw_type and raw_type not in ALLOWED_TYPES:
        return None
    digest = hashlib.sha256((domain + "|" + doi).encode()).hexdigest()[:12]
    return {
        "record_id": f"DISC-{domain.upper().replace(' ', '-')}-{digest}",
        "domain": domain,
        "title": title,
        "authors": authors,
        "year": publication_year(item),
        "container_title": first(item, "container-title"),
        "volume": clean_text(item.get("volume")),
        "issue": clean_text(item.get("issue")),
        "page": clean_text(item.get("page")),
        "doi": doi,
        "url": clean_text(item.get("URL")) or "https://doi.org/" + doi,
        "abstract_metadata": clean_text(item.get("abstract")),
        "crossref_type": raw_type,
        "crossref_score": item.get("score"),
        "discovery_query": query,
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "review_status": "metadata_lead_unverified",
        "equation_verified": False,
        "structural_review_complete": False,
        "accepted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--max-results-per-query", type=int, default=100,
                        help="Crossref results per query (1–1000)")
    parser.add_argument("--offset", type=int, default=0,
                        help="Result offset; use successive offsets for deeper passes")
    parser.add_argument("--sleep", type=float, default=1.0,
                        help="Delay between Crossref requests in seconds")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--mailto", default=None,
                        help="Optional contact email for Crossref polite pool")
    parser.add_argument("--domains", nargs="*", choices=list(DOMAINS),
                        help="Defaults to all five domains")
    parser.add_argument("--dry-run", action="store_true",
                        help="Search and report without appending to the queue")
    args = parser.parse_args()

    if not 1 <= args.max_results_per_query <= 1000:
        parser.error("--max-results-per-query must be between 1 and 1000")
    if args.offset < 0 or args.sleep < 0 or args.timeout < 1:
        parser.error("offset/sleep/timeout must be non-negative (timeout > 0)")
    if not args.manifest.is_file():
        print(f"ERROR: manifest not found: {args.manifest}", file=sys.stderr)
        return 2

    try:
        known, accepted_counts, current_entries = load_known(args.manifest)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read manifest: {exc}", file=sys.stderr)
        return 2

    queued, old_queue_count = load_queue(args.queue)
    seen = known | queued
    domains = args.domains or list(DOMAINS)
    new_records: list[dict] = []
    request_count = 0
    errors: list[str] = []
    print(f"Catalogue entries: {current_entries}; accepted by domain: "
          + ", ".join(f"{d}={accepted_counts[d]}" for d in DOMAINS))
    print("Priority order: " + ", ".join(
        f"{d} (shortfall {max(0, 59-accepted_counts[d])})"
        for d in sorted(domains, key=lambda x: accepted_counts[x])
    ))

    for domain in sorted(domains, key=lambda x: accepted_counts[x]):
        for query in DOMAINS[domain]:
            try:
                items = crossref_search(
                    query, args.max_results_per_query, args.offset,
                    args.timeout, args.mailto
                )
                request_count += 1
                added = 0
                for raw in items:
                    record = normalize(raw, domain, query)
                    if not record:
                        continue
                    key = doi_key(record["doi"])
                    if key in seen:
                        continue
                    seen.add(key)
                    new_records.append(record)
                    added += 1
                print(f"[{domain}] {query}: {len(items)} results, {added} new DOI leads")
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                errors.append(f"{domain} / {query}: {exc}")
                print(f"WARNING: {errors[-1]}", file=sys.stderr)
            if args.sleep:
                time.sleep(args.sleep)

    if new_records and not args.dry_run:
        args.queue.parent.mkdir(parents=True, exist_ok=True)
        with args.queue.open("a", encoding="utf-8") as handle:
            for record in new_records:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Requests: {request_count}; new leads: {len(new_records)}; "
          f"existing queue records: {old_queue_count}")
    if args.dry_run:
        print("Dry run: queue was not changed.")
    else:
        print(f"Queue: {args.queue}")
    print("SAFETY: records are bibliographic leads only; no equations were "
          "extracted, verified, accepted, or added to the canonical catalogue.")
    if errors:
        print(f"Completed with {len(errors)} request errors; rerun to resume "
              "and deduplicate successful results.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
