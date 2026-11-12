# Core-295 automated source discovery

## Purpose

`scripts/core295_discover_sources.py` is a resumable, metadata-only discovery helper. It searches Crossref for bibliographic leads across Chemistry, Biology, Physics, DeFi AMM and DeFi Risk; deduplicates DOI records against the current catalogue and its own JSONL queue; and prioritizes domains with the largest shortfall from 59 accepted equations.

It does **not** discover or transcribe equations reliably, establish primary-source status, prove structural inequivalence, determine statistical independence, modify the canonical catalogue, or accept candidates. Those decisions require source inspection and scientific review. Crossref coverage is incomplete, especially for software/protocol documentation and some DeFi implementations, so this is one discovery channel rather than a complete literature search.

## Run

From the repository root, with Python 3.10+:

```bash
python scripts/core295_discover_sources.py
```

Each invocation processes one cursor page per query by default and saves a checkpoint in `data/core295_discovery_cursor.json`. Re-run the same command to continue from the saved cursor; increase the page budget for a deeper pass:

```bash
python scripts/core295_discover_sources.py
python scripts/core295_discover_sources.py --pages-per-query 5
```

The cursor checkpoint is written only after the corresponding page's new leads are appended to the queue. If interrupted between those writes, the page may be fetched again, but DOI deduplication prevents duplicate queue entries. Use `--cursor-state` to choose a separate checkpoint file. A `--dry-run` does not persist cursor progress.

Limit a pass to selected domains:

```bash
python scripts/core295_discover_sources.py --domains Chemistry Biology
```

Preview without changing the queue:

```bash
python scripts/core295_discover_sources.py --dry-run
```

Use the Crossref polite pool by supplying a contact address:

```bash
python scripts/core295_discover_sources.py --mailto researcher@example.org
```

The default output is `data/core295_discovery_queue.jsonl`. Each record is labelled `metadata_lead_unverified`, with `equation_verified=false`, `structural_review_complete=false`, and `accepted=false`. The script appends only new DOI records. Failed requests are reported; rerunning deduplicates successful records and continues discovery.

## Recommended review workflow

1. Review DOI, title, publication type, venue, date, pagination and publisher URL. Inspect `crossref_fulltext_links`, `crossref_license_metadata` and `crossref_resource_url` as retrieval leads; a PDF link or license URL is not by itself proof that the particular file is openly accessible or that reuse is permitted.
2. Retrieve the original paper, standard, textbook or pinned official implementation.
3. Confirm that the source actually contains the proposed governing equation and record its printed page/equation number.
4. Transcribe variables, units, assumptions, regime and limitations from the source.
5. Compare the complete governing operator against Core-15 exclusions and existing candidate families using the draft E0–E5 policy.
6. Record source-family and statistical-unit decisions separately.
7. Only a human reviewer may promote an equation through the catalogue's review states. Do not mark an entry accepted solely because Crossref found a DOI or an abstract mentions a model.

## Limits and safety

- The script requires outbound HTTPS access to Crossref when run.
- Crossref `link`, `license` and `resource` fields are preserved as publisher-supplied metadata. Links are not fetched, licenses are not legally interpreted, and no paywall or access control is bypassed. A reviewer must check the actual source version, access terms and page-level equation evidence.
- It uses only Python's standard library; no API key is required.
- It does not run scientific experiments, validators, solvers, GitHub Actions, or live DeFi RPC/API calls.
- It does not commit or push results. The user reviews the queue and decides whether to update the canonical manifest.
- It is a repeatable discovery assistant, not an autonomous scientific reviewer and cannot guarantee that 295 defensibly distinct equations exist in the available source universe.


## Open-access PDF retrieval

After reviewing the metadata leads, use [`scripts/core295_fetch_open_access.py`](../scripts/core295_fetch_open_access.py) and the [retrieval guide](CORE295_OPEN_ACCESS_RETRIEVAL.md) to locate and download explicitly OA PDFs through OpenAlex. This is a separate, opt-in command; it does not run as part of source discovery. It records file hashes and provenance, but does not OCR, extract equations, or accept candidates.
