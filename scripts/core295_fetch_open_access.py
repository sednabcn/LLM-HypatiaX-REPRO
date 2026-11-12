#!/usr/bin/env python3
"""Fetch explicitly OA PDFs for Core-295 leads, with provenance and safety checks.

OpenAlex is used only to locate an OA location. A record is downloaded only
when OpenAlex marks the work open access and supplies a PDF URL. The script
does not bypass authentication/paywalls, infer legal permissions, OCR papers,
extract equations, or modify the canonical catalogue.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUEUE = ROOT / "data" / "core295_discovery_queue.jsonl"
DEFAULT_OUT = ROOT / "data" / "core295_open_access"
OPENALEX = "https://api.openalex.org/works/https://doi.org/"


def public_https_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("URL must be HTTPS with a hostname and no embedded credentials")
    host = parsed.hostname.rstrip(".")
    try:
        ip = ipaddress.ip_address(host)
        addresses = [ip]
    except ValueError:
        addresses = [ipaddress.ip_address(row[4][0]) for row in socket.getaddrinfo(
            host, parsed.port or 443, type=socket.SOCK_STREAM
        )]
    if not addresses or any(not ip.is_global for ip in addresses):
        raise ValueError("URL resolves to a non-public IP address")
    return url


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_https_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


OPENER = urllib.request.build_opener(SafeRedirect())


def get_json(url: str, timeout: int, mailto: str | None) -> dict[str, Any]:
    public_https_url(url)
    headers = {"User-Agent": "Core295-OA-retrieval/1.0"}
    if mailto:
        headers["From"] = mailto
    request = urllib.request.Request(url, headers=headers)
    with OPENER.open(request, timeout=timeout) as response:
        payload = response.read(5_000_001)
    if len(payload) > 5_000_000:
        raise ValueError("metadata response exceeded 5 MB")
    return json.loads(payload.decode("utf-8"))


def fetch_pdf(url: str, destination: Path, timeout: int, max_bytes: int,
              mailto: str | None) -> tuple[str, int, str]:
    public_https_url(url)
    headers = {"User-Agent": "Core295-OA-retrieval/1.0", "Accept": "application/pdf"}
    if mailto:
        headers["From"] = mailto
    request = urllib.request.Request(url, headers=headers)
    digest = hashlib.sha256()
    total = 0
    prefix = bytearray()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix(destination.suffix + ".part")
    try:
        with OPENER.open(request, timeout=timeout) as response, temp.open("wb") as out:
            content_type = response.headers.get("Content-Type", "").split(";")[0].lower()
            if content_type not in ("application/pdf", "application/octet-stream", ""):
                raise ValueError(f"unexpected content type: {content_type}")
            while True:
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError(f"PDF exceeds size cap ({max_bytes} bytes)")
                if len(prefix) < 8:
                    prefix.extend(chunk[:8 - len(prefix)])
                digest.update(chunk)
                out.write(chunk)
        if not bytes(prefix).startswith(b"%PDF-"):
            raise ValueError("download did not begin with a PDF signature")
        temp.replace(destination)
        return digest.hexdigest(), total, content_type
    except Exception:
        temp.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--provenance", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--max-bytes", type=int, default=50 * 1024 * 1024)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument("--mailto", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.limit < 1 or args.max_bytes < 1024 or args.timeout < 1 or args.sleep < 0:
        parser.error("limit >= 1, max-bytes >= 1024, timeout > 0, sleep >= 0 required")
    if not args.queue.is_file():
        print(f"ERROR: queue not found: {args.queue}", file=sys.stderr)
        return 2
    provenance = args.provenance or (args.output_dir / "provenance.jsonl")
    completed_downloads: set[str] = set()
    records = []
    with args.queue.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            doi = str(item.get("doi") or "").strip().lower()
            if doi:
                records.append(item)
    if provenance.exists():
        with provenance.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    prior = json.loads(line)
                    if prior.get("doi") and prior.get("status") == "downloaded":
                        completed_downloads.add(str(prior["doi"]).lower())
                except json.JSONDecodeError:
                    continue
    processed = 0
    failures = 0
    for item in records:
        doi = str(item.get("doi") or "").strip().lower()
        if not doi or doi in completed_downloads:
            continue
        if processed >= args.limit:
            break
        processed += 1
        result = {
            "doi": doi, "title": item.get("title"), "domain": item.get("domain"),
            "source_record_id": item.get("record_id"),
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "status": "not_downloaded", "openalex_work_url": OPENALEX + urllib.parse.quote(doi, safe=""),
        }
        try:
            work = get_json(result["openalex_work_url"], args.timeout, args.mailto)
            oa = work.get("open_access") or {}
            location = work.get("best_oa_location") or {}
            pdf_url = location.get("pdf_url")
            result.update({
                "openalex_id": work.get("id"),
                "is_open_access": bool(oa.get("is_oa")),
                "oa_status": oa.get("oa_status"),
                "license_reported_by_openalex": oa.get("license"),
                "best_oa_landing_page": location.get("landing_page_url"),
                "best_oa_pdf_url": pdf_url,
                "version": location.get("version"),
                "host_type": location.get("host_type"),
            })
            if not oa.get("is_oa") or not pdf_url:
                result["status"] = "no_explicit_oa_pdf_location"
            elif args.dry_run:
                result["status"] = "oa_pdf_candidate_dry_run"
            else:
                name = hashlib.sha256(doi.encode()).hexdigest()[:20] + ".pdf"
                path = args.output_dir / name
                digest, size, content_type = fetch_pdf(
                    pdf_url, path, args.timeout, args.max_bytes, args.mailto
                )
                result.update({
                    "status": "downloaded", "local_file": str(path),
                    "sha256": digest, "size_bytes": size, "content_type": content_type,
                    "final_source_url": pdf_url,
                })
            print(f"{doi}: {result['status']}")
        except (urllib.error.URLError, TimeoutError, OSError, ValueError,
                json.JSONDecodeError, KeyError) as exc:
            failures += 1
            result["status"] = "retrieval_error"
            result["error"] = str(exc)
            print(f"WARNING {doi}: {exc}", file=sys.stderr)
        if not args.dry_run:
            provenance.parent.mkdir(parents=True, exist_ok=True)
            with provenance.open("a", encoding="utf-8") as out:
                out.write(json.dumps(result, ensure_ascii=False) + "\\n")
        if args.sleep:
            time.sleep(args.sleep)
    print(f"Processed {processed}; retrieval errors {failures}; dry_run={args.dry_run}")
    print("No OCR, equation extraction, catalogue promotion, or licence/legal determination was performed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
