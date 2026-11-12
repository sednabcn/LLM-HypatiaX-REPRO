# Core-295 Thompson 1922 primary-source retrieval audit 2

**Date:** 2026-11-12  
**Branch:** `promotion/rerun-code-review`  
**Status:** source-location progress only; no equation candidate accepted.

## New primary-source route located

The complete bibliographic volume is digitized in two independent repositories:

1. **Wikisource, Tome 174 (January–June 1922):** the volume table of contents explicitly lists W.-R. Thompson's “Théorie de l’action des parasites entomophages. Les formules mathématiques du parasitisme cyclique” at printed page 1201. It also lists the follow-on papers at pp.1433 and 1647. The Wikisource volume is associated with the DjVu scan `Comptes rendus hebdomadaires des séances de l’Académie des sciences, tome 174, 1922.djvu`.
   - Table of contents: https://fr.wikisource.org/wiki/Comptes_rendus_de_l%E2%80%99Acad%C3%A9mie_des_sciences/Tome_174,_1922/Table_des_mati%C3%A8res
   - Search/open evidence: `turn181838view1` (especially lines 109–116 and 266–275); `turn221315search0`.
2. **Biodiversity Heritage Library:** volume 174 (1922) appears as BHL item 31193, with download PDF, all-pages, JPEG 2000 and OCR/text options advertised on the item page. The web retrieval service returned HTTP 403 when opening the item, so the scan/OCR was not inspected in this pass.
   - Item: https://www.biodiversitylibrary.org/item/31193
   - Search evidence: `turn402430search0`; open attempt `turn181838view0` failed 403.
   - Field mirror page: https://field.biodiversitylibrary.org/page/6964467 (`turn402430search3`).

## What is verified

- The volume's own table of contents places Thompson's first cyclic-parasitism communication at p.1201 and attributes it to W.-R. Thompson.
- The same volume lists the second and third related communications at pp.1433 and 1647.
- A separate volume 175 table of contents lists the fourth paper at p.65 (`turn221315search1`).
- The bibliographic sequence is corroborated by specialist bibliographies (`turn402430search1`, `turn402430search8`).

## What is not verified

- The equation-bearing printed pages have not yet been visually inspected.
- No formula has been transcribed from the primary source.
- No claim is made about the exact mathematical structure, assumptions, or equivalence of the four communications.
- No candidate, source-family count, or statistical-independence unit is added to the Core-295 catalogue.

## Next retrieval actions

1. Navigate from the Wikisource volume index to the DjVu page corresponding to printed p.1201 and inspect the page image, not OCR alone.
2. If Wikisource does not expose the page reliably, use the BHL volume's page-level download/IIIF routes or Internet Archive partner copy; do not infer the formula from secondary summaries.
3. Inspect pp.1433, 1647 and volume 175 p.65 as a single derivation lineage before proposing any distinct equation.
4. Compare the inspected formulas against Thompson 1924, Lotka 1923, Bailey 1931/1933 and Nicholson–Bailey 1935; keep the source-family identifier separate from the independent statistical-unit identifier.

## Scope boundary

This is source-discovery and retrieval documentation only. No scientific experiment, script, validator, test, solver, workflow, or live protocol was run. Human review remains required for faithful transcription, model interpretation, structural inequivalence, and independence.
