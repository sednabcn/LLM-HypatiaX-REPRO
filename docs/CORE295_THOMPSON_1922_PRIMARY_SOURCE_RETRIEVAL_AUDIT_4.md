# Core-295 Thompson 1922 primary-source retrieval audit 4

**Date:** 2026-11-12  
**Branch:** `promotion/rerun-code-review`  
**Status:** full-volume primary scan located; exact article pages not yet inspected; no equation candidate accepted.

## Material breakthrough: the complete scan is openly mirrored

The previous retrieval attempts treated BHL and the Google Books record as the only practical routes. A direct Wikimedia Commons file record identifies the actual complete 1,817-page DjVu scan and its original source as the Bibliothèque nationale de France (Gallica).

- Commons file record: https://commons.wikimedia.org/wiki/File:Comptes_rendus_hebdomadaires_des_s%C3%A9ances_de_l%E2%80%99Acad%C3%A9mie_des_sciences,_tome_174,_1922.djvu
- Original file link (37.32 MB, 2,435 × 3,025 pixels, 1,817 pages): linked as “Original file” on the Commons record.
- Gallica digital identifier: `bpt6k3127j`.
- Gallica ARK: https://gallica.bnf.fr/ark:/12148/bpt6k3127j
- Commons record states the scan comes from Gallica and is marked public domain.
- Evidence: `turn271016view1`, especially lines 101–106, 121–143 and 228–245; category listing confirms the volume and scan dimensions at `turn629501view1`, lines 418–427.

The web retrieval service still returns 403 when opening the Gallica ARK, but the complete file itself is available as a Wikimedia Commons original-file link. This is a genuine primary-scan location, unlike the earlier bibliographic-only leads.

## Article location confirmed

The volume's table of contents lists:
- Thompson, “Théorie de l’action des parasites entomophages. Les formules mathématiques du parasitisme cyclique,” printed p.1201.
- Thompson, “Étude mathématique de l’action des parasites entomophages. Durée du cycle parasitaire et accroissement de la proportion d’hôtes parasités,” printed p.1433.
- Thompson, “Étude de quelques cas simples de parasitisme cyclique chez les insectes entomophages,” printed p.1647.
- Volume 175 lists the fourth communication at printed p.65.

Evidence: `turn183334search0`, `turn183334search1`.

## Remaining retrieval task

The original DjVu is 1,817 pages, while the article references are printed pagination. The exact mapping from printed page 1201 to DjVu frame number has not yet been established in the retrieval service. Gallica's direct viewer route is 403 here; the Commons record provides the full-file link, but no frame extraction or image inspection has been performed in this pass.

Next:
1. Use the DjVu page index or page text to map printed pp.1201–1204 to scan frames.
2. Inspect the scan image visually and transcribe only what is legible; cross-check OCR against the page image.
3. Repeat for pp.1433–1435, 1647–1649 and volume 175 pp.65–68 to test derivation lineage.
4. Do not accept any equation until assumptions, variables, dynamics and source page are independently reviewed.

## Evidence boundary

A complete primary-source scan has now been located. The mathematical content remains uninspected: no formula has been transcribed, no candidate accepted, and no source-family or statistical-independence unit assigned. No experiment, script, validator, test, solver, workflow or live protocol was run.
