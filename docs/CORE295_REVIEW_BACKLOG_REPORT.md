# Core-295 equation review backlog report

## Purpose

`scripts/core295_build_review_report.py` turns the unverified extraction queue into a domain-grouped human-review backlog. It reports queue coverage, catalogue accepted/proposed counts, metadata completeness, and exact normalized-snippet collisions.

It is a reporting tool, not a scientific validator. It does not parse mathematics, compare symbolic expressions, verify the source, establish independence, modify the queue/catalogue, or accept candidates.

## Usage

Preview the report in the terminal:

```bash
python scripts/core295_build_review_report.py --stdout
```

Write the default Markdown report:

```bash
python scripts/core295_build_review_report.py
```

Show all leads rather than the default top 20 per domain:

```bash
python scripts/core295_build_review_report.py --top 0
```

Choose alternate input/output files:

```bash
python scripts/core295_build_review_report.py \
  --queue data/core295_equation_review_queue.jsonl \
  --catalogue config/core295_catalogue.json \
  --output data/core295_review_backlog.md
```

## What it reports

- Number of valid and malformed JSONL records.
- Per-domain extraction queue size and current catalogue accepted shortfall against the configured target.
- A nine-field provenance/evidence completeness checklist: DOI, title, domain, source record ID, source URL, source PDF SHA-256, PDF page index, snippet and snippet SHA-256.
- Exact collisions after Unicode normalization and whitespace collapsing, grouped for manual inspection.
- A prioritized list per domain, with more complete provenance fields shown first.

The completeness score is not a quality or confidence score. Exact text collisions may be duplicate downloads, common boilerplate, repeated equations, or extraction artefacts. The report deliberately does not perform fuzzy matching because broad text similarity can hide materially different equations or create misleading matches.

## Human review remains mandatory

For each candidate, inspect the original PDF and verify source identity/version, printed pagination and equation number. Transcribe the complete governing equation or coupled system, variables, units, assumptions and validity regime. Then assign source-family identity, assess Core-15 overlap and E0–E5 structural distinctness, and justify the independent statistical unit separately. Only the established human review process may update catalogue status.

The script reads the queue and catalogue only. It writes a Markdown report to the selected output path; it never changes candidate records or the canonical catalogue. It performs no network access, OCR, experiments, validators, solvers, CI workflows, or live protocol calls.
