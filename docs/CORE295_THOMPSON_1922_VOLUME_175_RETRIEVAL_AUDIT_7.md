# Core-295 Thompson 1922 volume 175 source retrieval audit 7

**Date:** 2026-11-12  
**Branch:** `promotion/rerun-code-review`  
**Status:** second primary volume located; fourth Thompson communication now has a distinct Internet Archive scan target; equation text not yet retrieved.

## Volume 175 is a separate Internet Archive item

The fourth 1922 communication is not in the previously retrieved volume 174 item. Its volume has a separate Internet Archive identifier:

- Item: `comptesrendusheb175acad`
- Book viewer: https://archive.org/details/comptesrendusheb175acad/
- The Internet Archive book-image service has indexed individual page images for this item. A surfaced image record identifies the volume and its contributing library (MBLWHOI Library), confirming that this is the correct 1922 volume 175 scan.
- Example page-image record: https://www.flickr.com/photos/internetarchivebookimages/20650593786/ (`turn713168search1` / `turn253934search3`). That image is scan page 1067 and displays printed p.1062; it is not Thompson's article page.
- The volume 175 Thompson note is bibliographically located at printed pp.65–68. Independent bibliographies and Cambridge's Thompson bibliography confirm title and pagination (`turn713168search0`, `turn713168search2`).

## What this changes

The fourth note must be retrieved from volume 175, not from the volume 174 OCR file. This corrects the remaining retrieval path:

- 1922a–c are in `comptesrendusheb174acad` (already OCR-retrieved and inspected at the text level).
- 1922d is in `comptesrendusheb175acad` (separate item; scan located, but article text not yet inspected).

Do not infer the 1922d formula from its title or from the preceding three papers. It may extend, specialize, or modify the model; the source page must decide.

## Access attempts and limits

The volume 175 Internet Archive full-text URL is:

`https://archive.org/stream/comptesrendusheb175acad/comptesrendusheb175acad_djvu.txt`

The web retrieval service rejected the complete OCR file because its response exceeds the tool's content-size limit. The IA metadata endpoint was also inaccessible through the web retrieval service in this pass. Search results exposed a page-image record for the correct volume, but not the Thompson page itself.

A page image showing printed p.1062 at scan page 1067 is not sufficient to infer a constant offset for p.65; front matter, missing leaves and pagination transitions can change the mapping. Do not guess the physical scan frame.

## Next retrieval steps

1. Obtain the IA page-number metadata for `comptesrendusheb175acad` and map printed pp.65–68 to scan frame IDs.
2. Retrieve OCR only for those frames, rather than requesting the full 4+ MB OCR file.
3. Retrieve the corresponding JP2/page images and verify every equation symbol visually.
4. Compare 1922d against 1922a–c and Thompson's 1923 review / 1924 stochastic treatment to determine whether it is a new governing structure or a continuation.
5. Update the source-family decision only after page-level inspection.

## Evidence boundary

The correct second primary-source volume and item identifier are established. No OCR or page image for Thompson's pp.65–68 was retrieved in this pass, no equation was transcribed, and no candidate or statistical-independence unit was accepted. No experiment, script, validator, test, solver, workflow or live protocol was run.
