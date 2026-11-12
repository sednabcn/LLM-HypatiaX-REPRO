# Core-295 Thompson 1922 primary-source OCR audit 6

**Date:** 2026-11-12  
**Branch:** `promotion/rerun-code-review`  
**Status:** primary-source full text retrieved; mathematical content partially exposed by OCR; visual formula verification pending; no candidate accepted.

## Major retrieval breakthrough: Internet Archive full text is accessible

The BHL record's “View at Internet Archive” route resolves to the digitized volume:

- Internet Archive item: https://archive.org/details/comptesrendusheb174acad/
- Full OCR text: https://archive.org/stream/comptesrendusheb174acad/comptesrendusheb174acad_djvu.txt
- Item identifier: `comptesrendusheb174acad`
- Volume: *Comptes rendus hebdomadaires des séances de l'Académie des sciences*, tome 174, January–June 1922.
- IA item metadata records 1,832 pages, ABBYY OCR/HOCR, page-number confidence metadata, page-number JSON and downloadable PDF/JP2 assets. The separate Commons DjVu scan reports 1,817 pages; do not conflate the two page-index systems.
- Evidence: IA book page `turn163614view0`, lines 177–242 and 247–260; downloadable full text `turn569902view0`; OCR passage `turn924590view0`.

This is the first successful retrieval of the article's primary-source full text, unlike the earlier bibliographic-only results.

## Thompson 1922a, pp.1201–1204: primary OCR now exposes the model

The OCR identifies the article title and author at lines 65029–65038, then its modelling assumptions and equations:

- Initial host count (n), initial parasite count (p).
- Host reproductive multiplier per generation (h), parasite reproductive multiplier per generation (s).
- Separate factors (l) and (f) convert female offspring/reproductive counts to total host and parasite counts, depending on sex proportions.
- The model assumes one parasite egg per attacked host and attacks only on hosts not already parasitized.
- The OCR shows generation-indexed host counts, host maturation counts and parasite counts, followed by closed-form finite geometric-series expressions (numbered (1)–(5)).
- Source passage: `turn924590view0`, lines 65029–65107 and 65109–65192.

The OCR mangles several mathematical glyphs, subscripts, exponents and brackets. Therefore this audit does **not** publish a reconstructed closed-form expression as an exact transcription. The scan image must be checked before a formula record is drafted.

## Thompson 1922b, pp.1433–1435: explicit continuation of the same derivation

The second note opens by saying it has demonstrated in the first note the general host/parasite count formula under the same initial counts, reproductive multipliers and sex-ratio factors. It reuses the same one-egg-per-attacked-host and un-parasitized-host-only assumptions, then studies:
- equal host and parasite reproductive multipliers;
- parasite reproduction greater than host reproduction;
- parasite reproduction less than host reproduction;
- time/generation count until host elimination;
- parasitism percentages.

The OCR gives equations numbered (1)–(13), including special-case formulae, but several are typographically corrupted. Source: `turn639641view0`, lines 77316–77470.

This is not independent evidence of a wholly new governing model: it explicitly extends the first note's model and derives special cases and time-to-elimination expressions.

## Thompson 1922c, pp.1647–1649: numerical illustration, not an independent model

The third note states that the earlier notes developed the essential formulas and that it now considers the simplest cyclic-parasitism cases. It reuses the same host/parasite generation equations and gives a numerical example (n=1000), (p=10), (s=3), (h=2), (f=2), followed by a generation table. It explicitly says more factors will be studied later and treats the simplest cases as an idealized baseline.

Source: `turn457908view0`, lines 89215–89256 and 89264–89286.

The third note therefore appears to be an application/interpretation of the prior formula family, not an independent governing equation. Its text cites the earlier communications (OCR citation text says volume 164, likely an OCR error for volume 174; check image).

## Source-family implication

The primary OCR supports treating the 1922a–c notes as one connected derivation family:
- 1922a: foundational discrete-generation host/parasite counting model;
- 1922b: analytical cases and time-to-elimination consequences of the same model;
- 1922c: numerical illustration and interpretation.

The fourth note in volume 175, pp.65–68, remains to be inspected. Until that note is compared, do not finalize the full family boundary. In any case, do not count each of the first three notes as a separate independent equation merely because they have different titles/pages.

## Exact next steps

1. Retrieve the IA page-number JSON and map printed pp.1201–1204 to the correct IA physical page indices; note the IA and Commons scan indices differ.
2. Obtain page images for pp.1201–1204 and compare every symbol with the OCR before transcribing equations (1)–(5).
3. Repeat for pp.1433–1435, pp.1647–1649 and volume 175 pp.65–68.
4. Compare the resulting governing model to Bailey 1931/1933, Lotka 1923 and Nicholson–Bailey 1935 for structural lineage and source-family deduplication.
5. Only then draft a proposed equation record for human review.

## Evidence boundary

Primary-source full-text OCR was retrieved and inspected. No page image has yet been visually inspected, and no exact formula transcription is asserted. No Core-295 candidate is accepted, no catalogue entry is added, and no statistical-independence unit is assigned. No experiment, script, validator, test, solver, workflow or live protocol was run.
