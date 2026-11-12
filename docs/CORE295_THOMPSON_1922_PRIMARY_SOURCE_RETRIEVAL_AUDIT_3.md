# Core-295 Thompson 1922 primary-source retrieval audit 3

**Date:** 2026-11-12  
**Branch:** `promotion/rerun-code-review`  
**Status:** additional archive route identified; scan page still not inspected; no equation candidate accepted.

## New retrieval findings

### Wikisource volume index is reliable bibliographic evidence, not yet the scan page

The volume's own table of contents confirms the first Thompson paper at printed p.1201 and lists the later communications at pp.1433 and 1647. The volume index identifies an underlying DjVu file, but the linked volume-level Wikisource work page is not actually created, and a guessed article subpage is inaccessible. Therefore this is not yet a successful page-image retrieval.

- Volume index: https://fr.wikisource.org/wiki/Comptes_rendus_de_l%E2%80%99Acad%C3%A9mie_des_sciences/Tome_174,_1922/Table_des_mati%C3%A8res
- Thompson at p.1201 and later papers at pp.1433/1647: `turn541373view0`, lines 266–275, 582–591, 855–860.
- Volume page navigation leads to a non-existent Wikisource work page: `turn560131view0`, lines 48–59 and 82–86.

### BHL has two volume records for 1922

Two BHL catalogue records surfaced for the same journal and year:
- https://www.biodiversitylibrary.org/item/31193
- https://www.biodiversitylibrary.org/item/31146

Both describe *Comptes rendus hebdomadaires des séances de l’Académie des sciences*, 1922, held by MBLWHOI Library and marked not in copyright. BHL advertises page selection, part/book downloads and an Internet Archive viewing route. However, opening either item through the current retrieval service returned HTTP 403; neither the scan nor its OCR was inspected.
- `turn265808search2`, `turn265808search3`; open failure `turn175391view0`.

### Google Books identifies a full-volume digital book

Google Play Books lists volume 174, dated January 1922, as a free ebook of 1,854 pages:
- https://play.google.com/store/books/details/Acad%C3%A9mie_des_sciences_France_Comptes_rendus_hebdom?id=vm8xAQAAMAAJ
- `turn175391view2`, lines 15–27.

This is a new retrieval lead, not proof that the exact Thompson pages are available for preview or downloadable. The Google Books search-within-volume endpoint was not accessible through the current retrieval service.

### Archival preservation cross-check

The ISSN Portal's digital-reproduction record lists both Internet Archive (1846–1976) and Gallica (1835–1965) as preservation holders for the journal. This supports pursuing Internet Archive and Gallica as alternate repositories, but does not identify the exact volume's current access URL.
- `turn265808search1`.

## Current evidence boundary

- Primary-source bibliographic placement of the Thompson communications is verified from the volume index.
- A complete-volume Google Books record and two BHL catalogue records are identified.
- No equation-bearing page image or primary OCR has been inspected.
- No formula is transcribed, no candidate is accepted, and no statistical independence unit is assigned.
- Do not infer the equation from the paper title or secondary summaries.

## Next actions

1. Resolve the Google Books volume's page-preview availability through a normal reader route or a library/partner copy.
2. Follow the BHL Internet Archive viewer route for both item IDs and identify the underlying Internet Archive identifier; retrieve only if openly accessible.
3. Search Gallica's catalogue/OCR for volume 174 and the exact page range around 1201–1204.
4. Once pp.1201–1204 are visually inspected, retrieve pp.1433–1435, 1647–1649 and volume 175 pp.65–68 to assess whether the four communications are one derivation family or contain genuinely distinct governing structures.

## Scope boundary

No experiment, script, validator, test, solver, workflow, or live protocol was run. Source retrieval remains incomplete; human scientific review is required for transcription, interpretation, structural inequivalence and statistical independence.
