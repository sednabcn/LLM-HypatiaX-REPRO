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


## Addendum — exact footnote checked against the volume OCR

The volume-175 OCR was reopened at the exact printed location (Internet Archive full OCR, printed pp.65–66; source `turn692343view0`, lines 3415–3447). It confirms the three citations are literally rendered as:
- tome 153 (1911), p.1401;
- tome 156 (1913), p.1401;
- tome 164 (1917), p.1433.

This confirms that the earlier antecedent trail was not merely a line-offset or summary error. It does **not**, by itself, prove that those three cited pages are Thompson's own papers, nor that they contain the mathematical model. The 1911 volume's Wikisource table of contents search surfaced no W.-R. Thompson entry; BHL's searchable tome-153 item surfaced only several unrelated title entries, none at p.1401 in the current result. The correct interpretation is therefore: **three citations made by Thompson in 1922; authorship and subject of the cited pages remain unverified**. Do not label them as Thompson's 1911/1913/1917 communications until the actual page images are read.

A separate bibliography source records W.R. Thompson's 1913 note “Sur la spécificité des parasites entomophages” in *Comptes Rendus des Séances de la Société de Biologie* 75, pp.510–521 (not the *Académie des Sciences* tome 156, p.1401). This is a distinct publication and must not be silently substituted for the footnote citation: `turn637739search2`.

The 1922d paper's opening phrase “Dans une Communication précédente” remains a direct assertion that a previous communication derived the formula, but the three footnotes' exact page identities and their relation to that communication still need page-level resolution. The first three 1922 notes' lineage is unchanged.

## Core-295 shard-driver code-inspection correction

A separate code inspection found that `scripts/core295_run_shard.py` referenced `validity[var]` inside the input-range loop before assigning and validating `validity = entry.get("input_validity_bounds")`. The assignment and shape/finite-bound validation have been moved before the range loop. The duplicate later validation block was removed.

- Corrective commit: `df5fe9b53d40748d9ed44457bfb30bb563ab48a2`
- Re-fetched file blob SHA: `55180479ff63aaaefb3866bea6797889985c6a42`
- This is a source-level correction verified by re-fetching the committed file. No driver execution, tests, validators, experiments, or workflows were run.


## Addendum 2 — 1917 citation page number remains OCR-ambiguous

The primary OCR at `turn692343view0`, line 3425, renders the third reference as `t. 164, 1917, p. i433`. The tome-164 (January–June 1917) Wikisource contents index is available and contains no Thompson entry; a search for “1433” also finds no such page in that index (`turn540992search0`, `turn316325view0`, `turn711779view0`). Since the volume is a first-semester 1917 volume, “1433” is not safe to treat as a verified printed page number. The OCR may have introduced a leading character, and the actual reference could be a lower page number; only the scan can resolve it.

Accordingly:
- The volume number and year are OCR-rendered as tome 164 (1917), but the page number is **unverified**.
- The 1911 and 1913 references likewise remain unverified at page-image level.
- The 1917 tome's contents index does not establish that W.-R. Thompson authored an article in that volume.
- No antecedent is attributed to Thompson, no exact citation corrected by guesswork, and no source-family decision is made.

Primary volume-175 text remains the evidence for what the 1922 note cites; page-image inspection of each cited volume is still the next required action.
