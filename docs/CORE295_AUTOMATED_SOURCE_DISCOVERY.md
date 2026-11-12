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

1. Review DOI, title, publication type, venue, date, pagination and publisher URL.
2. Retrieve the original paper, standard, textbook or pinned official implementation.
3. Confirm that the source actually contains the proposed governing equation and record its printed page/equation number.
4. Transcribe variables, units, assumptions, regime and limitations from the source.
5. Compare the complete governing operator against Core-15 exclusions and existing candidate families using the draft E0–E5 policy.
6. Record source-family and statistical-unit decisions separately.
7. Only a human reviewer may promote an equation through the catalogue's review states. Do not mark an entry accepted solely because Crossref found a DOI or an abstract mentions a model.

## Limits and safety

- The script requires outbound HTTPS access to Crossref when run.
- It uses only Python's standard library; no API key is required.
- It does not run scientific experiments, validators, solvers, GitHub Actions, or live DeFi RPC/API calls.
- It does not commit or push results. The user reviews the queue and decides whether to update the canonical manifest.
- It is a repeatable discovery assistant, not an autonomous scientific reviewer and cannot guarantee that 295 defensibly distinct equations exist in the available source universe.
