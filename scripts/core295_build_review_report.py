#!/usr/bin/env python3
"""Build a human-review backlog from Core-295 equation extraction leads.

This is a reporting aid only. It never validates equations, changes the
canonical catalogue, or marks a candidate accepted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUEUE = ROOT / "data" / "core295_equation_review_queue.jsonl"
DEFAULT_CATALOGUE = ROOT / "config" / "core295_catalogue.json"
DEFAULT_REPORT = ROOT / "data" / "core295_review_backlog.md"
DOMAINS = ("Chemistry", "Biology", "Physics", "DeFi AMM", "DeFi Risk")
SPACE = re.compile(r"\s+")
PUNCT = re.compile(r"[^\w]+", re.UNICODE)


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    value["_queue_line"] = line_number
                    rows.append(value)
            except json.JSONDecodeError:
                rows.append({"_queue_line": line_number, "_invalid_json": True})
    return rows


def load_catalogue(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def normalized_snippet(value: str) -> str:
    value = SPACE.sub(" ", value.casefold()).strip()
    return PUNCT.sub(" ", value).strip()


def evidence_score(row: dict) -> tuple[int, list[str]]:
    # Equal-weight provenance/evidence fields; a score is not a scientific grade.
    fields = (
        ("DOI", "doi"),
        ("title", "title"),
        ("domain", "domain"),
        ("source record ID", "source_record_id"),
        ("source URL", "source_url"),
        ("PDF SHA-256", "source_sha256"),
        ("PDF page index", "pdf_page_index"),
        ("snippet", "snippet"),
        ("snippet SHA-256", "snippet_sha256"),
    )
    present, missing = 0, []
    for label, key in fields:
        value = row.get(key)
        if value is not None and value != "":
            present += 1
        else:
            missing.append(label)
    return present, missing


def md(value: object) -> str:
    return str(value if value not in (None, "") else "—").replace("|", "\\|").replace("\n", " ")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--top", type=int, default=20,
                        help="maximum leads shown per domain (default: 20; 0 means all)")
    parser.add_argument("--stdout", action="store_true",
                        help="write report to stdout instead of the output file")
    args = parser.parse_args()
    if args.top < 0:
        parser.error("--top must be non-negative")

    rows = read_jsonl(args.queue)
    catalogue = load_catalogue(args.catalogue)
    entries = catalogue.get("entries", []) if isinstance(catalogue.get("entries", []), list) else []
    accepted = defaultdict(int)
    proposed = defaultdict(int)
    for entry in entries:
        domain = entry.get("domain", "Unassigned")
        if entry.get("status") == "accepted":
            accepted[domain] += 1
        else:
            proposed[domain] += 1

    valid = [r for r in rows if not r.get("_invalid_json")]
    invalid_count = len(rows) - len(valid)
    grouped = defaultdict(list)
    for row in valid:
        domain = row.get("domain") or "Unassigned"
        score, missing = evidence_score(row)
        row["_evidence_score"] = score
        row["_missing_fields"] = missing
        grouped[domain].append(row)

    # Exact normalized text collisions are review flags only; no equivalence claim.
    duplicate_groups = defaultdict(list)
    for row in valid:
        normalized = normalized_snippet(str(row.get("snippet", "")))
        if normalized:
            duplicate_groups[hashlib.sha256(normalized.encode("utf-8")).hexdigest()].append(row)
    duplicates = [group for group in duplicate_groups.values() if len(group) > 1]

    lines = [
        "# Core-295 equation extraction review backlog",
        "",
        "> Generated report only. Snippets are unverified extraction leads. Similarity flags are not proof of equation identity or structural equivalence. No candidate is accepted by this report.",
        "",
        "## Snapshot",
        "",
        f"- Queue records: {len(rows)}",
        f"- Valid JSON records: {len(valid)}",
        f"- Invalid JSON lines: {invalid_count}",
        f"- Exact normalized-snippet collision groups: {len(duplicates)}",
        f"- Catalogue entries: {len(entries)}",
        f"- Catalogue accepted entries: {sum(accepted.values())}",
        "",
        "## Domain coverage",
        "",
        "| Domain | Queue leads | Catalogue proposed/non-accepted | Catalogue accepted | Target | Accepted shortfall |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for domain in DOMAINS:
        target = catalogue.get("per_domain_target", 59)
        lines.append(
            f"| {domain} | {len(grouped.get(domain, []))} | {proposed[domain]} | "
            f"{accepted[domain]} | {target} | {max(0, target-accepted[domain])} |"
        )
    unknown_domains = sorted(set(grouped) - set(DOMAINS))
    for domain in unknown_domains:
        lines.append(f"| {md(domain)} | {len(grouped[domain])} | {proposed[domain]} | {accepted[domain]} | — | — |")

    lines += ["", "## Review priority by domain", "",
              "Leads are ordered by metadata/evidence-field completeness, then source title and PDF page. Higher completeness only means easier provenance tracing; it does not mean higher scientific quality.",
              ""]
    for domain in (*DOMAINS, *unknown_domains):
        candidates = sorted(
            grouped.get(domain, []),
            key=lambda r: (-r["_evidence_score"], str(r.get("title", "")).casefold(),
                           int(r.get("pdf_page_index") or 0), int(r.get("_queue_line") or 0)),
        )
        lines += [f"### {domain}", ""]
        if not candidates:
            lines += ["No extraction leads currently recorded.", ""]
            continue
        lines += ["| Priority | Evidence fields | Title / DOI | PDF page index | Queue line | Missing provenance fields |",
                  "|---:|---:|---|---:|---:|---|"]
        shown = candidates if args.top == 0 else candidates[:args.top]
        for rank, row in enumerate(shown, 1):
            identity = md(row.get("title"))
            if row.get("doi"):
                identity += f" / {md(row.get('doi'))}"
            missing = ", ".join(row["_missing_fields"]) or "None"
            lines.append(
                f"| {rank} | {row['_evidence_score']}/9 | {identity} | "
                f"{md(row.get('pdf_page_index'))} | {row['_queue_line']} | {md(missing)} |"
            )
        if len(shown) < len(candidates):
            lines.append(f"| … | … | {len(candidates)-len(shown)} additional leads omitted; use --top 0 to show all | | | |")
        lines.append("")

    lines += ["## Exact snippet-collision flags", "",
              "These records share the same whitespace/punctuation-normalized extracted snippet. They may be duplicate downloads, repeated text, common definitions, or extraction artefacts. Inspect source pages before deciding whether to collapse anything.", ""]
    if not duplicates:
        lines.append("No exact normalized-snippet collisions detected.")
    else:
        for index, group in enumerate(sorted(duplicates, key=lambda g: (-len(g), str(g[0].get("title", "")))), 1):
            lines.append(f"### Collision group {index} ({len(group)} records)")
            for row in group:
                lines.append(
                    f"- {md(row.get('domain'))} — {md(row.get('title'))}; DOI {md(row.get('doi'))}; "
                    f"PDF page {md(row.get('pdf_page_index'))}; queue line {row['_queue_line']}; "
                    f"PDF SHA {md(row.get('source_sha256'))[:16]}…"
                )
            lines.append("")

    lines += [
        "## Required human-review decisions",
        "",
        "For each promising lead, inspect the original PDF and record: verified primary-source identity and version; printed page and equation number; complete governing equation/system (not a fragment); variable meanings, units, assumptions and validity regime; source-family ID; Core-15 overlap and E0–E5 structural-equivalence decision; independent statistical-unit rationale; and a separate reviewer decision. Do not infer printed pagination from the PDF page index.",
        "",
        "## Interpretation limits",
        "",
        "- Completeness score is a nine-field metadata checklist, not a confidence score.",
        "- Exact snippet collisions are advisory text matches, not algebraic or scientific equivalence.",
        "- No fuzzy semantic matching, symbolic comparison, OCR, equation reconstruction or source verification is performed.",
        "- The report does not modify the queue or canonical catalogue and never changes review/acceptance status.",
        "",
    ]
    report = "\n".join(lines)
    if args.stdout:
        print(report, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"Wrote {args.output} ({len(valid)} leads; {len(duplicates)} collision groups).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
