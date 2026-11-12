# Core-295 Thompson antecedent-volume retrieval audit 9

**Date:** 2026-11-12  
**Branch:** `promotion/rerun-code-review`  
**Status:** antecedent volumes identified; 1917 full OCR opened; 1911 and 1913 page-level lineage remains unresolved.

## Why these volumes matter

The fourth Thompson note in tome 175 (1922), pp.65–68, cites three earlier *Comptes rendus* references in its footnotes: tome 153 (1911), p.1401; tome 156 (1913), p.1401; tome 164 (1917), p.1433. These citations appear in the primary OCR at `turn357274view0`, lines 3419–3425.

The citations should be followed directly. Do not assume the fourth note is merely an extension of the three 1922 tome-174 notes.

## Tome 164 (1917): Internet Archive volume and OCR are available

- Item: https://archive.org/details/comptesrendusheb164acad
- Full OCR: https://archive.org/stream/comptesrendusheb164acad/comptesrendusheb164acad_djvu.txt
- Metadata identifies tome 164, January–June 1917, 1,086 pages, ABBYY OCR, page-number metadata and page-image assets.
- Item metadata: `turn378878view1`, lines 202–275 and 295–364.
- Full OCR opened: `turn536069view0`.

The current retrieval service intermittently times out on full-text find/open operations for this 61,627-line OCR. The cited printed p.1433 has not yet been isolated, and no Thompson formula from that page has been inspected.

## Tome 153 (1911): Internet Archive scan and Wikisource index located

- Internet Archive item: https://archive.org/details/comptesrendusheb153acad
- Commons scan record: https://commons.wikimedia.org/wiki/File:Comptes_rendus_hebdomadaires_des_s%C3%A9ances_de_l%27Acad%C3%A9mie_des_sciences_(IA_comptesrendusheb153acad).pdf
- The scan record identifies tome 153 (1911), 1,616 pages, from MBLWHOI Library, and links the IA item: `turn783444view0`, lines 122–144 and 159–161.
- IA item metadata identifies tome 153 (1911), 1,620 pages, ABBYY OCR and downloadable full-text, HOCR, OCR index, page-number JSON and JP2 assets: `turn717411view0`, lines 202–277 and 297–370.
- Following the full-text download is blocked by the current retrieval service's 4 MiB response cap.

The Wikisource volume contents index is available at https://fr.wikisource.org/wiki/Comptes_rendus_de_l%E2%80%99Acad%C3%A9mie_des_sciences/Tome_153,_1911/Table_des_mati%C3%A8res (`turn673233view0`). A search of its OCR index for “Thompson” finds only Silvanus-P. Thompson's unrelated harmonic-analysis paper at p.88 (`turn717616view0`). Thus the tome-153 p.1401 citation is not yet corroborated as a W.-R. Thompson paper by the volume's index; the citation may be to another antecedent or the OCR/page citation needs visual verification. Do not assign authorship until p.1401 is inspected.

## Tome 156 (1913): Gallica scan located

- Wikimedia Commons scan: https://commons.wikimedia.org/wiki/File:Comptes_rendus_hebdomadaires_des_s%C3%A9ances_de_l%E2%80%99Acad%C3%A9mie_des_sciences,_tome_156,_1913.djvu
- Gallica digital identifier: `bpt6k3109m`.
- 2,124-page DjVu scan, 38.86 MB; source identified as Gallica; record marks it public domain.
- Evidence: `turn897519search0`.

The printed p.1401 must be mapped to a scan frame and inspected. The Gallica endpoint remains blocked in the current retrieval service.

## Next steps

1. Inspect tome 164 printed p.1433, including the surrounding note and footnotes; do not rely on global text search alone.
2. Map tome 156 printed p.1401 to the Gallica scan frame and inspect the page.
3. Resolve tome 153 printed p.1401. Its volume index does not identify a W.-R. Thompson entry, so verify the 1922d footnote and the actual page before assigning a source.
4. Compare these antecedents against the 1922d formula and the 1922a–c discrete-generation model. Keep source-family and independent statistical-unit decisions open until that comparison is complete.

## Evidence boundary

This audit records primary volume access and retrieval constraints. No equation is transcribed from the antecedent volumes; no candidate or catalogue row is accepted. No experiment, script, validator, test, solver, workflow or live protocol was run.
