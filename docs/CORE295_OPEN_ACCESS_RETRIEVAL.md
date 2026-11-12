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


## Candidate evidence-readiness report

After preparing packets, generate an operational gap report:

```bash
python scripts/core295_candidate_readiness_report.py
python scripts/core295_candidate_readiness_report.py --stdout
```

The report matches extraction leads to retrieval provenance and discovery metadata, checks whether the referenced PDF is locally present, checks for a corresponding review packet, and summarizes missing evidence fields and accepted-equation shortfalls by domain. It writes `data/core295_candidate_readiness.md` by default.

“Ready” means only that the packet has the expected evidence links for a human source-page review. It is not scientific readiness, source verification, equation acceptance, structural inequivalence or statistical independence. The report is read-only with respect to catalogue, queues and packets; it performs no OCR, symbolic validation, tests or experiments.


## Human decision record and controlled staging

Use the [machine-readable review decision template](templates/core295_review_decision.template.json) for each candidate. Record explicit pass/hold/fail decisions, evidence, dates and reviewers. E5 is a hold; only an independently reviewed E4 candidate can proceed under the current strict draft policy.

After completing the candidate record and decision record, the staging helper can produce a standalone proposed catalogue entry:

```bash
python scripts/core295_stage_reviewed_candidate.py \
  --candidate path/to/completed_candidate.json \
  --decision path/to/completed_review_decision.json \
  --output data/core295_staging/DOMAIN-CANDIDATE.json
```

The helper blocks unless all required review gates pass, the E4 rationale is recorded, source-family and statistical-unit assignments are documented, and two distinct reviewers and dates are supplied. It writes a new staging artifact only; it refuses to overwrite an existing output. The staged status is `structurally_reviewed`, never `accepted`. It does not edit the canonical catalogue or validate scientific correctness.

Before a maintainer manually adds any staged record to the catalogue, they must inspect it, verify every `source_id` exists in the source register, compare it against all current and proposed catalogue entries (including cross-domain and Core-15 exclusions), and consider source-family clustering and the frozen sampling frame. Catalogue validation is a separate, explicitly authorized step. Acceptance remains a separate human decision and is never performed by this helper.


## Catalogue-wide staged-promotion audit

After generating one or more staging JSON files, run the read-only consistency audit:

```bash
python scripts/core295_audit_staged_promotions.py
python scripts/core295_audit_staged_promotions.py --stdout
```

The audit compares staged candidates with the canonical catalogue and embedded source register. It flags equation-ID/fingerprint collisions, missing or duplicate source-register IDs, source-domain mismatches, shared source IDs requiring family review, source-family cross-domain reuse, statistical-unit/source-family conflicts, missing or inconsistent reviewer decisions, and invalid staging status. It writes a Markdown report only; it does not modify the catalogue or staged records.

A clean report means only that these mechanical checks found no issue. It is not a scientific acceptance, a complete pairwise proof of structural inequivalence, or evidence of statistical independence. A maintainer must still inspect primary sources and review the complete catalogue and sampling design before any separate catalogue change.


## Build a non-applying catalogue proposal

Once staged candidates have passed the catalogue-wide audit, create a proposed catalogue snapshot and unified diff:

```bash
python scripts/core295_build_catalogue_proposal.py \
  --output data/core295_proposals/core295_catalogue.proposed.json \
  --diff data/core295_proposals/core295_catalogue.diff
```

The command reruns the read-only audit against the same catalogue and staging directory. It stops if there are no staged records, any audit blocker/error, duplicate IDs, or if the staged set changes during assembly. Audit warnings are carried into the proposal manifest for maintainer disposition.

The proposal appends only `structurally_reviewed` entries, preserves the canonical catalogue's draft status, records the canonical input SHA-256 and hashes of staged inputs, and emits a unified diff. It does not set accepted flags, edit the canonical catalogue, or run the catalogue validator. Outputs are new files and are never overwritten.

A maintainer must inspect the complete diff, verify source-page evidence and all cross-candidate structural/sampling implications, resolve or explicitly disposition warnings, and separately authorize any application. The proposal is not a merge request, scientific acceptance, or permission to apply changes.
