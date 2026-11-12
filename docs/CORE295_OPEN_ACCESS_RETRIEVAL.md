# Core-295 open-access source retrieval

## Purpose

`scripts/core295_fetch_open_access.py` looks up DOI leads in OpenAlex and downloads a PDF only when OpenAlex explicitly reports the work as open access and supplies a best open-access PDF location. It records source metadata, reported OA status/licence, retrieval URL, local path, byte count and SHA-256 digest in a JSONL provenance file.

It does not interpret licences as legal advice, guarantee that the downloaded file is the version of record, bypass access controls, OCR or extract equations, modify the canonical catalogue, or accept candidates.

## Usage

Preview up to 20 DOI leads without downloading or writing provenance:

```bash
python scripts/core295_fetch_open_access.py --dry-run
```

Retrieve up to 20 eligible PDFs:

```bash
python scripts/core295_fetch_open_access.py
```

Increase the per-run cap or select alternate locations:

```bash
python scripts/core295_fetch_open_access.py --limit 50
python scripts/core295_fetch_open_access.py --queue path/to/queue.jsonl --output-dir data/core295_open_access
```

Defaults:
- Input: `data/core295_discovery_queue.jsonl`
- PDFs: `data/core295_open_access/`
- Provenance: `data/core295_open_access/provenance.jsonl`
- Maximum PDF size: 50 MiB
- Request timeout: 30 seconds
- One-second delay between DOI lookups

A completed DOI with status `downloaded` is skipped on later runs. A failed or unavailable DOI can be retried. SHA-256 is calculated over the downloaded bytes. The downloader validates HTTPS URLs, rejects hosts resolving to non-public IP addresses, checks redirects, enforces a size limit, and verifies the PDF magic signature before keeping the file.

## Review requirements

1. Confirm the DOI, title, authors, venue and publication version against the primary source.
2. Check the publisher/repository landing page and actual licence terms; OpenAlex's licence field is metadata, not a legal determination.
3. Inspect the PDF title page and printed page numbering.
4. Record the exact equation and page manually or through a separately reviewed extraction workflow.
5. Keep source-family and statistical-unit decisions separate.
6. Do not promote a candidate based solely on an OA flag or successful download.

## Safety and limitations

- Requires outbound HTTPS to OpenAlex and the OA host when run.
- No API key is required for basic OpenAlex access; `--mailto` optionally supplies contact metadata.
- Only HTTPS OA PDF locations are considered. No login, cookies, institutional credentials, paywall circumvention or live DeFi endpoints are used.
- PDF files may contain malicious or malformed content. Keep them in the designated data directory and use a patched PDF reader; the script does not parse or execute PDF content.
- The downloader is not run automatically and has not been run as part of this repository change.
- It does not run experiments, validators, solvers or GitHub Actions.


## Page-referenced equation snippet leads

After reviewing the downloaded PDFs, run the optional extraction helper:

```bash
python scripts/core295_extract_equation_leads.py --dry-run
python scripts/core295_extract_equation_leads.py
```

It requires Poppler's `pdftotext` executable. It extracts layout-preserving text page by page, flags broad equation-like lines and nearby context, and appends records to `data/core295_equation_review_queue.jsonl`. Each lead includes the source PDF SHA-256, DOI metadata where available, PDF page index, text-line range, snippet and snippet hash. Re-running deduplicates the same source-page-snippet tuple.

**Important:** PDF page index is not the printed page number. The patterns are recall-oriented cues, not mathematical parsing; tables, multi-line equations, scans and OCR-only content can be missed or fragmented. Every snippet is marked `unverified_extraction_lead`; a reviewer must inspect the PDF, verify printed pagination and equation transcription, and assess assumptions and structural distinctness. This helper never updates the canonical catalogue or accepts an equation.


## Equation snippet extraction

Once PDFs have been retrieved and their provenance reviewed, use [`scripts/core295_extract_equation_leads.py`](../scripts/core295_extract_equation_leads.py):

```bash
python scripts/core295_extract_equation_leads.py --dry-run
python scripts/core295_extract_equation_leads.py
```

Requires Poppler `pdftotext`. It checks each PDF against the retrieval provenance SHA-256, extracts text page by page, and stores equation-like snippets with source DOI, PDF page index, text-line span and snippet hash in `data/core295_equation_review_queue.jsonl`. Repeated runs deduplicate by PDF hash, page index and snippet hash.

The extraction is deliberately heuristic. Page index is not printed pagination; OCR is not performed; multi-line equations and scanned pages may be missed. All records remain `unverified_extraction_lead`, never accepted. A reviewer must compare each snippet against the original PDF and transcribe the complete governing equation, assumptions and printed page before structural review. No canonical catalogue is changed.


## Assemble human-review packets

After extraction, create one evidence packet per snippet:

```bash
python scripts/core295_prepare_candidate_reviews.py --stdout-summary
python scripts/core295_prepare_candidate_reviews.py
```

The helper reads the extraction queue, the retrieval provenance file and the Crossref discovery queue. It matches records by source record ID where available and otherwise by DOI, then assembles the snippet, source PDF hash/page index, retrieval metadata, bibliographic metadata and the full human review template into a deterministic Markdown packet under `data/core295_candidate_review_packets/`.

Existing packets are skipped by default. Use `--overwrite` only when intentionally regenerating packets from updated evidence. Missing or malformed supporting records are reported; they are not inferred. Each packet explicitly remains proposed, unverified, E5/unresolved and unaccepted. The helper does not edit any input queue or the canonical catalogue, and does not establish source primacy, equation correctness, structural distinctness or statistical independence.

The retrieval provenance writer uses actual JSONL record separators so these downstream readers can parse one provenance record per line.
