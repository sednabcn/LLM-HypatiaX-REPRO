# Core-295 Thompson 1922 primary-source retrieval audit 5

**Date:** 2026-11-12  
**Branch:** `promotion/rerun-code-review`  
**Status:** official Gallica retrieval interfaces identified; current retrieval environment blocks their endpoints; no equation candidate accepted.

## Official BnF APIs now documented

The Bibliothèque nationale de France publishes two official interfaces relevant to the located Gallica scan:

1. **Gallica Document API** supports bibliographic metadata, pagination/foliation, OCR text, table of contents, full-text occurrences and page thumbnails. The official documentation gives the page OCR route:
   `https://gallica.bnf.fr/RequestDigitalElement?O=<document-id>&E=ALTO&Deb=<physical-page-index>`
   It also documents the pagination service:
   `https://gallica.bnf.fr/services/Pagination?ark=<document-id>`
   and the plain-text route:
   `https://gallica.bnf.fr/ark:/12148/<document-id>.texteBrut`.
   Sources: https://api.bnf.fr/fr/api-document-de-gallica (`turn918569search4`); https://api.bnf.fr/index.php/fr/api-document-de-gallica (`turn918569search9`).

2. **Gallica IIIF API** exposes the document manifest, per-view image metadata and image pages:
   `https://gallica.bnf.fr/iiif/ark:/12148/<document-id>/manifest.json`
   `https://gallica.bnf.fr/iiif/ark:/12148/<document-id>/<view>/info.json`
   `https://gallica.bnf.fr/iiif/ark:/12148/<document-id>/<view>/full/full/0/native.jpg`
   Official BnF documentation states that the interface exposes the full Gallica image collection and is based on IIIF.
   Source: https://api.bnf.fr/api-iiif-de-recuperation-des-images-de-gallica (`turn918569search1`).

## Applied to Thompson's volume

Document identifier: `bpt6k3127j` (Gallica ARK `ark:/12148/bpt6k3127j`).

The documented calls needed are therefore:
- pagination: `/services/Pagination?ark=bpt6k3127j`;
- OCR page by page: `/RequestDigitalElement?O=bpt6k3127j&E=ALTO&Deb=<index>`;
- IIIF manifest: `/iiif/ark:/12148/bpt6k3127j/manifest.json`.

Important distinction: the API's `Deb` and IIIF `view` parameters are physical scan-frame indices, not necessarily the printed page number. The Pagination response must be used to map printed p.1201 to the correct physical frame. Do not assume `Deb=1201` or `f1201` is the correct page.

## Retrieval attempt and limitation

The current web retrieval service returned inaccessible/blocked responses for direct requests to all three Gallica routes (pagination, ALTO OCR and IIIF manifest/image). This is a transport/access limitation of the current retrieval path, not evidence that the BnF API itself is unavailable. The official documentation explicitly describes open access, subject to reasonable-use limits (`turn918569search0`, `turn918569search5`).

No OCR text or page image was retrieved in this turn. The scan's equation-bearing content remains uninspected.

## Next steps

1. Resolve the physical page index using the official Pagination response through a route that can access Gallica.
2. Retrieve ALTO for the mapped frame and adjacent frames, then compare its text and coordinates with the IIIF page image.
3. Visually inspect printed pp.1201–1204, not OCR alone; record the exact printed pagination and scan-frame IDs.
4. Continue with pp.1433–1435, 1647–1649 and volume 175 pp.65–68 to assess the four-paper derivation lineage.
5. Only after source-page inspection should a candidate be drafted for human scientific review.

## Evidence boundary

This audit documents official primary-source retrieval interfaces and failed access attempts. No formula is transcribed, no candidate is accepted, and no source-family or statistical-independence unit is assigned. No experiment, script, validator, test, solver, workflow or live protocol was run.
