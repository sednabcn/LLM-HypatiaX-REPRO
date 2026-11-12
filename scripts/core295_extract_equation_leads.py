#!/usr/bin/env python3
"""Create page-referenced, unverified equation-snippet leads from OA PDFs.

Requires the external Poppler utility pdftotext. The script never modifies the
canonical equation catalogue or accepts/validates a scientific equation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF_DIR = ROOT / "data" / "core295_open_access"
DEFAULT_PROVENANCE = DEFAULT_PDF_DIR / "provenance.jsonl"
DEFAULT_OUTPUT = ROOT / "data" / "core295_equation_review_queue.jsonl"

# Deliberately broad recall-oriented patterns: these are review cues, not parsers.
MATH_CUES = re.compile(
    r"(?:=|≈|≃|∝|≤|≥|≠|→|↔|\b(?:d\w*/d\w+|\w+_\w+)\b|"
    r"\\(?:frac|sum|prod|int|partial|Delta|nabla)|"
    r"\b(?:equation|where|governed by|rate of change|functional response|"
    r"mass balance|energy balance|constitutive relation|invariant)\b)",
    re.IGNORECASE,
)
NUMBERED = re.compile(r"\(\s*\d+[a-z]?\s*\)\s*$|^\s*\[\s*\d+\s*\]")
WHITESPACE = re.compile(r"\s+")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                value = json.loads(line)
                if isinstance(value, dict):
                    rows.append(value)
            except json.JSONDecodeError:
                continue
    return rows


def extract_pages(pdf: Path, executable: str, timeout: int,
                  max_chars: int) -> list[str]:
    completed = subprocess.run(
        [executable, "-layout", "-enc", "UTF-8", str(pdf), "-"],
        check=False, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=timeout,
    )
    if completed.returncode:
        detail = (completed.stderr or "").strip()[:1000]
        raise RuntimeError(f"pdftotext exited {completed.returncode}: {detail}")
    if len(completed.stdout) > max_chars:
        raise RuntimeError(f"extracted text exceeds {max_chars} character cap")
    return completed.stdout.split("\f")


def candidate_windows(page_text: str, context: int, min_chars: int,
                      max_chars: int) -> list[tuple[str, int, int]]:
    lines = [WHITESPACE.sub(" ", line).strip() for line in page_text.splitlines()]
    hits = [i for i, line in enumerate(lines)
            if len(line) >= min_chars and (MATH_CUES.search(line) or NUMBERED.search(line))]
    windows = []
    occupied: set[int] = set()
    for index in hits:
        lo, hi = max(0, index-context), min(len(lines), index+context+1)
        if any(i in occupied for i in range(lo, hi)):
            continue
        snippet = "\n".join(line for line in lines[lo:hi] if line)
        snippet = snippet[:max_chars]
        if snippet:
            windows.append((snippet, lo+1, hi))
            occupied.update(range(lo, hi))
    return windows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, default=DEFAULT_PDF_DIR)
    parser.add_argument("--provenance", type=Path, default=DEFAULT_PROVENANCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--pdftotext", default="pdftotext")
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--max-chars-per-pdf", type=int, default=20_000_000)
    parser.add_argument("--context-lines", type=int, default=1)
    parser.add_argument("--min-line-chars", type=int, default=12)
    parser.add_argument("--max-snippet-chars", type=int, default=1800)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.timeout < 1 or args.max_chars_per_pdf < 1 or args.context_lines < 0:
        parser.error("timeout/max-chars must be positive and context-lines non-negative")
    executable = shutil.which(args.pdftotext)
    if not executable:
        print("ERROR: pdftotext (Poppler) not found; install it and retry.", file=sys.stderr)
        return 2
    if not args.pdf_dir.is_dir():
        print(f"ERROR: PDF directory not found: {args.pdf_dir}", file=sys.stderr)
        return 2

    provenance = read_jsonl(args.provenance)
    by_path = {str(Path(row.get("local_file", "")).resolve()): row
               for row in provenance if row.get("local_file")}
    existing = set()
    for row in read_jsonl(args.output):
        key = (row.get("source_sha256"), row.get("pdf_page"), row.get("snippet_sha256"))
        existing.add(key)

    pdfs = sorted(args.pdf_dir.glob("*.pdf"))
    added = 0
    failures = 0
    for pdf in pdfs:
        try:
            digest = sha256_file(pdf)
            source = by_path.get(str(pdf.resolve()), {})
            if source.get("sha256") and source["sha256"] != digest:
                raise RuntimeError("PDF hash does not match retrieval provenance")
            pages = extract_pages(pdf, executable, args.timeout, args.max_chars_per_pdf)
            source_info = {
                "doi": source.get("doi"),
                "title": source.get("title"),
                "domain": source.get("domain"),
                "source_record_id": source.get("source_record_id"),
                "source_url": source.get("final_source_url"),
                "pdf_path": str(pdf),
                "source_sha256": digest,
                "extracted_at": datetime.now(timezone.utc).isoformat(),
            }
            for page_number, page_text in enumerate(pages, start=1):
                if not page_text.strip():
                    continue
                for snippet, first_line, last_line in candidate_windows(
                    page_text, args.context_lines, args.min_line_chars,
                    args.max_snippet_chars
                ):
                    snippet_hash = hashlib.sha256(snippet.encode("utf-8")).hexdigest()
                    key = (digest, page_number, snippet_hash)
                    if key in existing:
                        continue
                    record = {
                        **source_info,
                        "pdf_page_index": page_number,
                        "snippet_first_text_line": first_line,
                        "snippet_last_text_line": last_line,
                        "snippet": snippet,
                        "snippet_sha256": snippet_hash,
                        "review_status": "unverified_extraction_lead",
                        "equation_verified": False,
                        "printed_page_number_verified": False,
                        "structural_review_complete": False,
                        "accepted": False,
                    }
                    if not args.dry_run:
                        args.output.parent.mkdir(parents=True, exist_ok=True)
                        with args.output.open("a", encoding="utf-8") as out:
                            out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    existing.add(key)
                    added += 1
            print(f"{pdf.name}: extracted {len(pages)} PDF pages")
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            failures += 1
            print(f"WARNING {pdf}: {exc}", file=sys.stderr)

    print(f"PDFs: {len(pdfs)}; candidate snippets: {added}; failures: {failures}")
    print("Page values are PDF page indices, not verified printed pagination.")
    print("OCR is not performed; scanned/image-only pages may yield no candidates.")
    print("All snippets remain unverified; no catalogue entries were accepted.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
