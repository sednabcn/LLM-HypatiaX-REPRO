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


## Source verification and transcription template

Use the [Core-295 source verification and equation transcription template](templates/CORE295_EQUATION_SOURCE_REVIEW_TEMPLATE.md) for the full human review record. It captures primary-source identity, artifact hashes, printed and PDF pagination, page-image transcription checks, model assumptions and units, E0–E5 comparison, source-family and statistical-unit rationale, generator contract, and independent sign-off.

A machine-readable starting point is also provided at [core295_candidate_record.template.json](templates/core295_candidate_record.template.json). It is intentionally incomplete and is not an accepted catalogue entry; populate and review it before adapting its fields into the canonical catalogue schema.


## Evidence-assembled review packets

The extraction queue can be assembled into individual, deterministic human-review packets with [`scripts/core295_prepare_candidate_reviews.py`](../scripts/core295_prepare_candidate_reviews.py). See the [open-access retrieval and extraction guide](CORE295_OPEN_ACCESS_RETRIEVAL.md#assemble-human-review-packets) for inputs, matching rules and usage. Packets embed the full source-review template and supporting bibliographic/retrieval metadata, but remain proposed, unverified, E5/unresolved and unaccepted. The helper does not modify the canonical catalogue or source queues.


## Candidate evidence-readiness report

Use [`scripts/core295_candidate_readiness_report.py`](../scripts/core295_candidate_readiness_report.py) after packet preparation to report operational evidence gaps, missing PDF artifacts, packet coverage and accepted shortfalls by domain. The output is `data/core295_candidate_readiness.md`. Its “ready for human source-page review” category is strictly an evidence-linkage check, not scientific acceptance or proof of distinctness/independence. See the [retrieval guide](CORE295_OPEN_ACCESS_RETRIEVAL.md#candidate-evidence-readiness-report).


## Human decision records and candidate staging

The [review decision template](templates/core295_review_decision.template.json) captures gate outcomes, evidence, reviewer identities/dates, E0–E5 classification, source-family and statistical-unit rationale, and final disposition. The [staging helper](../scripts/core295_stage_reviewed_candidate.py) checks for complete human sign-off and emits a standalone `structurally_reviewed` staging JSON. It never sets `accepted`, writes to the canonical catalogue, or substitutes for catalogue-wide equivalence review and source-register checks. See the [controlled staging procedure](CORE295_OPEN_ACCESS_RETRIEVAL.md#human-decision-record-and-controlled-staging).


## Catalogue-wide promotion audit

Run `python scripts/core295_audit_staged_promotions.py` after staging candidates. This read-only report checks staged IDs and fingerprints against the catalogue, verifies source IDs against the embedded source register, flags source-ID reuse and domain/family mismatches, and checks statistical-unit/source-family consistency and human sign-off metadata. It does not edit the catalogue, certify scientific validity, or authorize acceptance. See the [audit procedure](CORE295_OPEN_ACCESS_RETRIEVAL.md#catalogue-wide-staged-promotion-audit).


## Non-applying catalogue proposal

After the read-only promotion audit is clear, [`core295_build_catalogue_proposal.py`](../scripts/core295_build_catalogue_proposal.py) can generate a proposed catalogue snapshot and unified diff. It reruns the audit, records input hashes and appends only `structurally_reviewed` entries. It leaves the canonical catalogue untouched and never accepts candidates. The diff still requires explicit maintainer inspection and separate approval before application.


## Approval and application controls

A two-maintainer approval template and guarded applier are now available: [approval template](templates/core295_catalogue_application_approval.template.json) and [application script](../scripts/core295_apply_approved_catalogue_proposal.py). The applier requires explicit `--apply`, exact input hashes, two distinct approvers, scientific-review attestations, a separate application authorization, append-only integrity checks, structural validation, and an exact pre-application backup. It leaves the catalogue draft and does not accept entries.
