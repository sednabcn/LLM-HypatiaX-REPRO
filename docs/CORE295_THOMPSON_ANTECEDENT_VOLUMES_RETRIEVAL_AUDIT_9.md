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


## Addendum 4 — volume 164 page 235 is Bordas, not Thompson; adapter isolation improved

The tome-164 (1917) table of contents identifies the well-known Ichneumonid paper as L. Bordas, “Sur le rôle des Ichneumonides dans la lutte contre les parasites des arbres forestiers,” p.235. It is not a W.R. Thompson paper and must not be treated as the antecedent cited by Thompson's 1922d note. The same table's Parasitologie section lists Roubaud p.453 and other unrelated entries; no Thompson title is visible in the indexed contents (Wikisource tome-164 contents, source turn879267search0). The OCR-rendered “i433” therefore remains unresolved; it is not safe to normalize it to 235 or any other nearby page.

The 1922d antecedent citations remain unresolved: tome 153 (1911), p.1401; tome 156 (1913), p.1401; and tome 164 (1917), OCR “i433”. BnF states that the historical *Comptes rendus* collection is digitized through Gallica, providing the preferred primary-source retrieval route (source turn809822search0). Tome 156 has a digitized Commons volume record with 2,124 pages (source turn809822search7), but the cited page still requires inspection.

### Adapter concurrency correction

The Core-295 adapter previously supplied hashed arrays by temporarily replacing module-level `generate_data` and `generate_extrap_data` functions. That was vulnerable to cross-talk if equations were ever run concurrently in one process. Replaced the monkeypatch with an explicit optional `dataset_override` argument to `exp1_ablation.run_condition`; the no-override Core-15 generation path remains unchanged, and Core-295 passes the exact pre-generated arrays directly. Each invocation makes defensive copies. Changes:
- `hypatiax/experiments/benchmarks/exp1_ablation.py`, commit `5b9a7f86247d9d57c6816c8c10fff0ef60e0e1c0`, blob `e633cb3e57e988bdac82616c6fb088f91d1798cf`.
- `hypatiax/experiments/benchmarks/core295_adapters/common.py`, commit `c6f6e1d6df7d8663205d0f1cb8e1730d2e2ef028`, blob `ad479b89b419313fb1be2f4b32c3ad3a8a4a6792`.

Both file contents were re-fetched after commit. No tests or execution were performed; the change is source-inspected only.


## Addendum 5 — volume-index cross-check and exact-page route failures

The Wikisource table of contents for tome 153 (1911) lists Silvanus-P. Thompson's harmonic-analysis note at p.88, but not William-R. Thompson. A targeted search of that index finds no printed p.1401 entry. This is evidence that the volume-index OCR/index does not corroborate the 1922d citation; it does **not** prove that the cited article does not exist, because the index is subject-classified and may omit or mis-OCR entries (sources turn507550view0 and turn507550view3).

The tome-164 (1917) contents similarly identify L. Bordas's Ichneumonid paper at p.235, while no W.R. Thompson entry appears in the indexed contents. The direct Wikisource page routes attempted for tome 153 p.1401, tome 156 p.1401, and tome 164 p.433 were inaccessible to the retrieval interface (sources turn565832view0, turn565832view1, turn565832view2). Do not infer article identity from these failed opens. BHL confirms a 1913 volume record for tome 156, but the p.1401 article remains unidentified (source turn322426search2).

Conclusion unchanged: the 1922d footnote's three antecedent references are not yet verified at page-image level. No Thompson formula transcription, candidate promotion, or independence assignment is justified.


## Addendum 6 — 1923 mathematical synthesis identified; publication form unresolved

A separate 1923 Thompson item is now corroborated: “La théorie mathématique de l'action des parasites entomophages.” Cambridge's bibliography cites it as *Revue générale des sciences pures et appliquées*, 11 pp.; a later bibliography gives volume 34 (1923), pp.202–210. A contemporary 1923 notice in *Le Naturaliste canadien* describes it as a Paris publication and calls it an early application of mathematics to entomology (sources turn104852search3, turn794797search6, turn794797search11). The differing citation forms (11-page standalone item versus journal volume/page range) are not reconciled. No full primary text or equation-bearing scan was retrieved in this audit.

This 1923 synthesis is a high-priority retrieval target because it may summarize the 1922 cyclic-parasitism notes and/or present a revised mathematical treatment. It must not be counted as a separate equation merely because it is a separate publication. Compare its governing state variables, transition law, assumptions, and derivation against the 1922 notes and the 1924 Marseille treatment before any structural classification. The 1923 *A criticism of the “Sequence” theory of parasitic control* is a different work (Annals of the Entomological Society of America 16(2), 115–128; DOI 10.1093/aesa/16.2.115) and is not evidence for the mathematical synthesis (source turn794797search2).


## Addendum 7 — 1923 synthesis content clues and 1927 applied-model papers

The 1923 synthesis's bibliographic form is better corroborated than in Addendum 6: Cambridge's 1939 retrospective bibliography cites the 1923 item as *Revue générale des sciences*, 11 pages; another bibliography gives *Revue générale des sciences pures et appliquées*, volume 34, pp.202–210. A 1923 contemporary review in *Le Naturaliste canadien* independently identifies the Paris publication and calls it an early mathematical treatment of entomology (sources turn932299search2, turn885158search36, turn189715search34). These records support the existence and general bibliographic identity, but not the exact issue/page convention or a primary equation transcription.

A secondary French-language historical account describes the 1923 theory as covering single and multiple parasitism, probability, host/parasite generation synchrony, and hyperparasitism, with possible cyclic and non-cyclic population outcomes (source turn885158search34). Treat these as retrieval clues, not verified equations or exact claims attributable to the primary paper until the 1923 text is inspected.

A second high-priority primary target is Thompson's “A Method for the Approximate Calculation of the Progress of Introduced Parasites of Insect Pests,” *Bulletin of Entomological Research* 17(3), March 1927, pp.273–277, DOI 10.1017/S0007485300019325. Its abstract states that it applies simple mathematical methods to quantitative increase of introduced entomophagous parasites and practical parasitological operations; the paper is access-gated in the publisher record (source turn932299search0). The 1927 companion, “On the Effect of Methods of Mechanical Control on the Progress of Introduced Parasites of Insect Pests,” *Bulletin of Entomological Research* 18(1), pp.13–16, DOI 10.1017/S0007485300019623, is described by a secondary abstract as mathematically analyzing temporary destruction of hosts and parasites (source turn932299search3). These 1927 papers may contain applied variants or extensions of the same Thompson host–parasite model family; do not treat them as independent equation families without comparing the full governing assumptions and operators.

The ISSN record confirms that the journal's historical digitization is represented in Gallica and Internet Archive holdings, with coverage extending through 1968 (source turn885158search1). A targeted volume-34 / Gallica / Internet Archive search did not retrieve the 1923 article scan in this pass. Retrieval remains open; no equations have been transcribed and no catalogue status changed.


## Addendum 8 — cross-check against Thompson's 1927–1939 retrospective bibliography

The Cambridge publisher page for Thompson's 1927 “A Method for the Approximate Calculation of the Progress of Introduced Parasites of Insect Pests” is especially useful: its own references explicitly cite the 1922 *Comptes Rendus* notes, a *Revue Générale des Sciences* item dated 15 April 1923, the 1923 *Annales de la Société Entomologique d'Amérique* item, and the 1924 Marseille paper. This supports the existence of the 1923 *Revue* item and its date, but does not settle its exact title or pagination (source turn900600search1).

The same publisher record for Thompson's 1928 “A Contribution to the Study of Biological Control and Parasite Introduction in Continental Areas” (Parasitology 20(1), pp.90–112) presents an 11-point synthesis of ecological control complexes, hyperparasites, equilibrium, and the introduction of natural enemies. The available extract is conceptual and does not itself expose a governing equation. Treat this as theoretical context, not a distinct equation candidate without primary full-text inspection (source turn712574search1; issue contents corroborate article and pagination at turn712574search37).

Thompson's 1929 “On Natural Control” (Parasitology 21(3), pp.269–281) has an accessible Cambridge PDF route but the indexed extract is introductory prose warning against misleading analogies; no equation was transcribed in this pass (source turn712574search0). A 1939 retrospective “Biological Control and the Theories of the Interactions of Populations” spans pp.299–388 and is a potentially important synthesis for tracing Thompson's mature model lineage, but must not be treated as an independent source family or as primary evidence for earlier formulae without checking its historical attributions (source turn712574search3).

The 1927 mechanical-control paper's abstract says it mathematically studies temporary reductions that affect hosts and parasites, but the Cambridge extract does not expose the formulae (source turn900600search0). A secondary abstract gives qualitative conclusions about equal versus unequal proportional destruction of hosts and parasites; this is a retrieval clue only, not a substitute for the primary derivation (source turn900600search3).

The 1923 item is therefore confirmed as a publication cited by Thompson himself in 1927, while its full title, issue pagination, and equation content remain open. No equations were transcribed and no catalogue status changed.


## Addendum 9 — 1939 author bibliography and contemporary 1923 review located

The 1939 Cambridge publisher record for Thompson's own 88-page retrospective (Parasitology 31(3), pp.299–388, DOI 10.1017/S0031182000012865) reproduces a reference list that explicitly identifies: 1922a, “Les formules mathématiques du parasitisme cyclique” (C.R. Acad. Sci. 174, 1201–1204); 1922b, “Durée du cycle parasitaire et accroissement de la proportion d'hôtes parasités” (174, 1433–1435); 1922c, “Étude de quelques cas simples de parasitisme cyclique” (174, 1647–1649); 1922d, “Accroissement de la proportion d'hôtes parasités dans le parasitisme cyclique” (175, 65–68); and 1923a, “La théorie mathématique de l'action des parasites entomophages,” listed as an 11-page item in *Revue générale des sciences pures et appliquées* (source turn294394search0; publisher page opened as turn968301view0). This is the strongest author-controlled bibliographic confirmation obtained so far. It also fixes the 1922a–d mapping: earlier index/search snippets sometimes misassigned b/c labels; use the 1939 author's own bibliography as the controlling citation sequence.

A digitized contemporary 1923 review in *Le Naturaliste canadien*, vol.50, p.144, lists Thompson's “La Théorie mathématique de l'action des parasites entomophages. Paris, 1923” and states that it uses algebraic formulae, logarithms, and probability to put both single and multiple parasitism into equations; it also names generation-sequence concordance and hyperparasitism as factors, and describes both cyclic and relatively stable population outcomes (source turn968301search20). This is contemporary evidence about the work's intended mathematical scope, but it is a review notice, not the primary 11-page paper and not an equation transcription. A separate 1930s historical survey repeats this account (source turn968301search23), but is not needed to establish the bibliographic lead.

The 1939 article itself is a major retrieval target: its historical introduction is identified by later scholarship as pp.301–327 (source turn968301search21), while the Cambridge publisher page exposes abstract and references but access to the full article is gated. It can guide model genealogy and point to source attributions, but equations copied or summarized there must be traced to the original paper before primary-source acceptance.

No primary 1923 equation image or full article text has yet been retrieved. The 1923 work remains one proposed source lead, not a separate accepted equation. No catalogue status changed.


## Addendum 10 — Gallica holding identified; exact 1923 issue still not isolated

The 1923 *Revue générale des sciences pures et appliquées* run is now confirmed as a digitized Gallica holding. The ISSN record identifies Gallica preservation for 1890–1947, and the BnF/partner catalogue gives the series ARK `12148/cb343784049/date` and links the full online collection (sources turn986838search0, turn986838search4). A direct attempt to open the year-filtered Gallica ARK from this retrieval interface failed (source turn494417view0); this is an access/tool limitation, not evidence that the 1923 volume is absent. A Wikisource resource page also points to Gallica facsimiles for the series (source turn986838search3). The Commons scan result found in this search is for an 1890s volume, not the required 1923 volume, and must not be mistaken for it (source turn986838search6).

The Cambridge 1939 author bibliography explicitly calls the 1923 mathematical work “La théorie mathématique de l'action des parasites entomophages” and lists it as an 11-page item in *Revue générale des sciences pures et appliquées* (source turn130659search1). Thompson's 1927 paper cites the journal issue date as 15 April 1923, giving a concrete issue-level retrieval target (source turn130659search3). The contemporary *Naturaliste canadien* notice at p.144 independently names the 1923 Paris publication and describes its mathematical scope (source turn130659search7); an Institut de France historical text reproduces the same contemporary description, including algebra, logarithms, probability, single/multiple parasitism, generation concordance, and hyperparasitism (source turn130659search8). These sources establish bibliographic identity and research scope, but none is the 11-page primary article.

Additional Thompson lead: his 1930 “The utility of mathematical methods in relation to work on biological control,” *Annals of Applied Biology* 17, pp.641–648, is cited in his 1939 reference list (source turn606499search0). It is likely useful for Thompson's mature methodological framing, but it is not evidence of a distinct governing equation. The 1939 retrospective itself is 88 pages (Parasitology 31, pp.299–388); its historical introduction is pp.301–327 according to a later population-ecology history (sources turn606499search0, turn606499search24).

Retrieval action for the next pass: query Gallica's year/issue catalogue for the 15 April 1923 issue and inspect its contents/title page, then obtain the 11-page article scan. Do not assign page numbers from the 1923 volume or infer the article's equation structure from the 1939 bibliography or contemporary review. No equation transcription, structural review, or catalogue promotion occurred.


## Addendum 11 — authoritative 1922 numbering reaffirmed; archive inventory narrowed

A fresh retrieval pass reconfirms that Thompson's 1939 Cambridge article gives the authoritative 1922a–d sequence and identifies 1923a as the 11-page *Revue générale* synthesis (source turn791193search1). A UCR-hosted pooled bibliography uses a shifted 1922 sequence (it labels the 1433 paper 1922c, the 1647 paper 1922d, and the 175/65 paper 1922e), so it is demonstrably inconsistent with Thompson's own retrospective list and must not be used to label the four 1922 papers (source turn791193search2). The Cambridge 1927 article independently cites the 15 April 1923 *Revue Générale des Sciences* issue (source turn791193search3).

The serial's digitized holdings are confirmed by the ISSN record and BnF-linked catalogue, which identify Gallica coverage 1890–1947 and the collection ARK `12148/cb343784049/date` (sources turn716211search1, turn716211search5). The Wikisource resource page points to Gallica facsimiles for the serial, but its indexed volume list currently shows selected years and does not expose the 1923 issue directly (source turn716211search8). The BHL record surfaced in this pass is a 1922 item, not the required 1923 volume; the Commons scan result is an 1890s volume and likewise not the target (sources turn716211search7, turn716211search9). A general serial catalogue confirms a 1923 run exists but provides no issue-level article locator (source turn716211search3). Thus the 15 April issue is bibliographically located, but no scan/page-image has yet been identified.

Separate 1923 paper clarification: Thompson's “A Criticism of the ‘Sequence’ Theory of Parasitic Control” is in *Annals of the Entomological Society of America* 16(2), 1 June 1923, pp.115–128; this is a different article from the mathematical *Revue* synthesis and should not be confused with it (source turn791193search0). No equations were transcribed from the sequence critique in this pass.

No catalogue change. The 1923 mathematical synthesis remains a source lead with strong author-controlled bibliographic identity but no primary equation evidence.
