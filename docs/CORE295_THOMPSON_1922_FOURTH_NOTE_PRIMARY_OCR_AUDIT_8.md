# Core-295 Thompson 1922 fourth-note primary OCR audit 8

**Date:** 2026-11-12  
**Branch:** `promotion/rerun-code-review`  
**Status:** primary OCR for the fourth note retrieved; lineage hypothesis revised; page-image verification pending; no equation candidate accepted.

## Primary full-text retrieval succeeded

The Internet Archive item page for volume 175 is accessible and confirms:
- Volume 175, July–December 1922.
- 1,522 scanned pages, 400 PPI, OCR-converted with ABBYY.
- Download assets include full text, HOCR, OCR page index, page-number JSON, PDF, and single-page original/processed JP2 assets.
- Item identifier: `comptesrendusheb175acad`.
- Item page: https://archive.org/details/comptesrendusheb175acad
- Full OCR: https://archive.org/stream/comptesrendusheb175acad/comptesrendusheb175acad_djvu.txt
- Metadata and available files: `turn916416view0`, lines 202–274 and 294–363.

The earlier claim that the full OCR could not be retrieved was too pessimistic: opening the item page and following its “FULL TEXT” link exposes the complete OCR text. The page-number JSON and OCR page-index links redirect to a storage host rejected by the current retrieval service, so physical frame mapping remains blocked.

## Fourth note pp.65–68 is now textually inspected

The OCR locates Thompson's note at lines 3415–3577, printed pp.65–68:
- Title and author: lines 3415–3417.
- It opens by stating that the formula for growth in the proportion of parasitized hosts was demonstrated in an earlier communication: lines 3419–3425.
- The OCR states a relative reproductive-power parameter (a): parasite reproductive power is (a) times that of the host; initial host and parasite counts are (n) and (p), with equal sex proportions: lines 3432–3435.
- A formula is printed at lines 3437–3447, but OCR corrupts the numerator, exponents, brackets and denominator. No exact transcription is asserted.
- Numerical trajectories for (n=1000,p=10,a=1.5) and (n=10000,p=10,a=1.5) follow: lines 3448–3463.
- The equal-reproductive-power special case is separately printed at lines 3464–3487, again with OCR corruption.
- The note discusses the shape of the parasitism curve, dependence on initial host abundance and parasite/host reproductive power, and long delays before apparent control: lines 3489–3577.
- Source: `turn357274view0`, lines 3415–3577.

## Critical lineage correction: 1922d cites earlier papers, not the three 1922 volume-174 notes

The footnotes at lines 3423–3425 explicitly cite:
- *Comptes rendus*, tome 153 (1911), p.1401;
- tome 156 (1913), p.1401;
- tome 164 (1917), p.1433.

This means the fourth note's stated derivation lineage reaches back to Thompson's 1911, 1913 and 1917 communications. It does **not** explicitly cite the 1922a paper at tome 174, p.1201. The previous audit's assumption that 1922d simply extended the 1922a–c sequence is therefore unproven and must be withdrawn.

The first three 1922 notes remain strongly connected by their own primary OCR: 1922b explicitly extends 1922a, and 1922c applies their formulas. But 1922d must be compared separately against both the 1922a–c model and the cited 1911/1913/1917 antecedents before source-family membership is decided.

## New primary-source retrieval targets

Retrieve the cited antecedents from their own volumes:
- tome 153 (1911), p.1401;
- tome 156 (1913), p.1401;
- tome 164 (1917), p.1433.

Search the Internet Archive/BHL volume OCR and page-image assets for each, then compare their equations and assumptions with 1922d. These may be the actual parent lineage for the fourth note.

## Evidence and acceptance boundary

- The fourth note's full primary OCR text is now retrieved and inspected.
- The exact equation remains unverified because the OCR mangles the mathematical line; page images have not yet been inspected.
- The note's own citations establish a 1911/1913/1917 antecedent trail.
- No candidate is accepted, no catalogue row is added, and no source-family or independent statistical-unit decision is finalized.
- No experiment, script, validator, test, solver, workflow or live protocol was run.
