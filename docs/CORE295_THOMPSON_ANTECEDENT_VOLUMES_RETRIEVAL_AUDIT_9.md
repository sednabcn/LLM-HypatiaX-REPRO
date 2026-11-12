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


## Core-295 shard output-write correction

A second source-level inspection found the shard driver opened the output in binary-exclusive mode (`"xb"`) while also passing `encoding="utf-8"` and writing a decoded string. Python rejects an encoding argument in binary mode, so this would fail at artifact emission after the adapter calls. The driver now writes the canonical JSON bytes directly to the exclusive binary stream.

- Corrective commit: `b287a3124c29f8f3e6b6a40e6065d4032248b8f1`
- Re-fetched file blob SHA: `464b38a301bdb28aea08f71f0179326132ae1360`
- Source-level correction only; no driver execution or test was performed.


## Core-295 statistical-unit uniqueness guard

A further inspection found that the task planner required each accepted record to carry an `independence_unit_id`, but did not enforce uniqueness across the 295 records. The shard driver likewise checked presence but not uniqueness. That left a gap between the declared 295-independent-unit calibration design and the executable preflight.

Both now require non-empty string identifiers and reject any repeated `independence_unit_id`. Repeated `source_family_id` values remain permitted because source-family clustering is distinct from the statistical independence unit.

- Planner commit: `1ef2149146796c1e0c021808712bf5405cf7a993`; re-fetched blob SHA: `8d6b2a554810fb02c147d40442bf40dd6316a136`.
- Shard-driver commit: `50c3f7f8c2c78a87eb0c00c5e72ca46a6bb6f2be`; re-fetched blob SHA: `f69927911df1346901e0278b3ef9c7cb3bb0b55a`.
- Source-level corrections verified by re-fetch only. No planner, driver, tests, validators, experiments, or workflows were run.


## Core-295 planner validity-bound ordering correction

A separate read-through of `scripts/core295_plan_tasks.py` found the same ordering defect previously corrected in the shard driver: the planner accessed `validity[variable]` while checking input ranges before assigning and validating `input_validity_bounds`. This would prevent task planning from reaching its intended fail-closed validation.

The planner now validates the complete input-validity map and its finite, increasing bounds before checking train/extrapolation ranges, and removes the duplicate later block.

- Corrective commit: `e9b447639660ac4aa444427eb83b6809aa80fad0`
- Re-fetched content SHA: `127ad7c4a17d370205312afcdb9cc8d88d87fae3`
- Verified by re-fetch only; no planner invocation, tests, validators, or experiments.


## Planner and adapter contract follow-through

After correcting the planner's validity-bound ordering, the shared scalar adapter and all five domain wrappers were inspected at source level. The wrappers for Chemistry, Biology, Physics, DeFi AMM and DeFi Risk all delegate to the same explicit-scalar adapter; they are routing labels, not domain-specific scientific generators. That adapter rejects non-`explicit_scalar` model classes and dynamic states, so the wider model classes allowed by the planner/driver are not yet executable through these wrappers. This remains a deliberate fail-closed limitation, not evidence that the full 295-domain workload is ready.

The adapter precomputes dataset hashes from the same deterministic Core-15 generator functions that `run_condition` calls again for each arm. The precomputed arrays are not passed into `run_condition`; identity depends on the generation routines remaining deterministic under the same seed and configuration. Before execution is authorized, a later implementation review should either pass the exact arrays into the run function or capture hashes from the arrays actually consumed, to make provenance direct rather than inferential.

No adapter, planner, driver, tests, validators, workflows, or experiments were run during this inspection.


## Dataset provenance correction — exact arrays now enter every arm

The shared scalar adapter previously generated and hashed Core-295 train/test/extrapolation arrays, then called `exp1.run_condition`, which regenerated those arrays independently for each arm. Although the same deterministic generator and seed were used, the recorded hashes were not direct hashes of the arrays consumed by the model calls.

The adapter now temporarily overrides the two Core-15 data-generator functions while each arm runs. It supplies fresh copies of the exact pre-generated arrays that were hashed by the adapter, and restores the original generator functions in a `finally` block. Thus all three arms receive byte-identical values for a given equation/seed, and the dataset hashes now describe the arrays actually passed through the unchanged `run_condition` data-loading interface. The default Core-15 generator path is untouched outside this narrow adapter context.

- Adapter commit: `f24ff5deb57d3f9e5c8b7524b810678cd5215262`
- Re-fetched adapter blob SHA: `58b5a64e77a9f6b606c613dfb2dfd7912e128283`
- Implementation uses a scoped override and restores both functions even if an arm raises.
- This is source-level inspection and re-fetch verification only. No adapter invocation, tests, planner, driver, validator, workflow, model/API call, or experiment was run.

The adapter remains limited to explicit scalar equations. The five domain wrappers still route to this same adapter; this provenance fix does not expand model-class coverage or constitute scientific acceptance of any catalogue entry.


## Addendum 3 — volume indexes narrow the antecedent trail

The Wikisource alphabetical contents for tome 153 (1911) explicitly lists **Silvanus-P. Thompson**, “Nouvelle méthode d’analyse harmonique par la sommation algébrique d’ordonnées déterminées,” at p.88. This is Silvanus P. Thompson, not W. R. Thompson, and is not the 1922d footnote's cited p.1401. A full-text search of the tome-153 contents page finds no other “Thompson” entry. Therefore the tome-153 index does not support attribution of a W. R. Thompson communication to that volume. The separate p.1401 citation still needs page-image identification; do not conflate the p.88 Silvanus-P. Thompson note with it. Source: Wikisource tome-153 contents, lines 203–206 (turn118683view0; targeted find turn497697view0).

For tome 164 (January–June 1917), the volume's Gallica-derived DjVu record reports 1,070 scan pages, while the 1922d OCR renders the cited page as `i433` / 1433. A printed page 1433 cannot occur in this volume as described; the OCR reference is therefore corrupted or otherwise misread and must not be treated as a valid page number. The tome-164 contents index also has no “Thompson” entry (turn935836search1, turn583314view0, targeted find turn105470view0). This strengthens the conclusion that the 1917 citation is unresolved and likely contains OCR error, but does not identify the intended page or article.

Tome 156 (1913) has a Gallica-derived 2,124-page DjVu scan, digital identifier `bpt6k3109m`; this is a concrete primary-volume retrieval route, not yet a page-level identification. Its scan record and metadata are documented at turn935836search0.

No equation has been transcribed from any of these cited antecedent pages. No source-family attribution, candidate acceptance, or catalogue update follows from this bibliographic narrowing.


## Correction to Addendum 3 — tome 153 does contain a W. R. Thompson paper, but not at p.1401

A targeted reinspection of the full tome-153 alphabetical contents resolved an important ambiguity. The index lists **two different Thompsons**:

- **William-R. Thompson**, “Sur une Tachinaire parasite à stade intracuticulaire,” p.83, under “Insectes.”
- **Silvanus-P. Thompson**, “Nouvelle méthode d’analyse harmonique par la sommation algébrique d’ordonnées déterminées,” p.88, under “Analyse harmonique.”

Thus the earlier statement that tome 153 had no W. R. Thompson entry was too broad and is corrected here. However, the 1922d footnote cites tome 153 **p.1401**, not p.83. The index therefore establishes a genuine W. R. Thompson communication in the 1911 volume, but does not establish that it is the item cited at p.1401 or that it contains the formula referred to in 1922d. The p.83 title is entomological and is a distinct source lead; inspect its page and compare its contents before deciding whether it is relevant to the cyclic-parasitism model. The p.88 Silvanus-P. Thompson paper remains a different author and subject. Evidence: tome-153 contents page and targeted search (`turn118683view0`, `turn497697view0`); the tome-153 index entry is also corroborated by the search result for a 1915 bibliography excerpt (`turn498798search1`), which itself cites the same title but appears to associate it with a later volume and is not used to override the primary tome-153 index.

The tome-164 conclusion remains unchanged: its 1,070-page scan cannot contain printed p.1433, and its contents index has no Thompson entry. Tome 156 p.1401 remains to be identified at page level. No equation has yet been transcribed from the 1911 p.83 item or either cited p.1401 page; no candidate acceptance or source-family decision is made.


## Addendum 3 — separate 1915 Thompson tachinaire paper identified

A new indexed volume search surfaced William-R. Thompson's “Sur une Tachinaire parasite à stade intracuticulaire” in *Comptes rendus de l'Académie des sciences*, tome 160 (1915), p.83 (the volume contents index lists the title under “Insectes”; source turn991123search0). A contemporaneous entomological bibliography also cites this paper as tome 160, pp.83–86 (source turn991123search13). This resolves the earlier ambiguity around the p.83 lead: it is a genuine Thompson paper, but it is in **tome 160 (1915)**, not tome 153 (1911), and its subject is a tachinaire parasite. It must not be substituted for the 1922d footnote's tome-153, p.1401 citation.

This is a distinct bibliographic lead only. The equation-bearing content has not been inspected, and no evidence currently links this biological note to the cyclic-parasitism formula. It is not accepted as a Core-295 equation or assigned an independence unit.

The 1922d footnote trail remains unresolved at the cited page images: tome 153 p.1401, tome 156 p.1401, and tome 164 with OCR-rendered page “i433”. Continue to verify those exact references rather than inferring them from nearby Thompson bibliography entries.
