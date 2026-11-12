# Core-295 Biology source retrieval audit: Bailey (1933) BHL article

**Date:** 2026-11-12  
**Status:** primary bibliographic record and open scan route located; equation-bearing pages not yet inspected.  
**Candidate:** none created.  
**Domain:** Biology — host/parasite population interaction.

## Source located

Victor Albert Bailey, “The quantitative theory of interaction between different species of animals,” *Journal and Proceedings of the Royal Society of New South Wales*, volume 66, issue 2, pp. 387–393. Biodiversity Heritage Library (BHL) article record: https://www.biodiversitylibrary.org/part/360060. DOI: https://doi.org/10.5962/p.360060.

BHL's article-level record identifies Bailey as author, the journal, volume, issue, pagination, and an article PDF download. The Royal Society of New South Wales' own volume-66 index independently lists Bailey's article at pp. 387–393. The University of Melbourne's biographical bibliography also lists this paper among Bailey's mathematical publications.

## Date / issue metadata discrepancy

BHL records the article publication date as 31 March 1933. The Royal Society of New South Wales volume index labels volume 66 as 1932 and places Bailey's paper at pp. 387–393. Treat the volume/year convention and BHL issue date as distinct metadata fields; do not silently normalize the source to 1932 or 1933 until the original issue title page and article imprint are checked.

## What is known, and what is not

An accessible secondary abstract describes a general P-host-species / Q-parasite-species interaction system and reports a steady-state condition involving P and Q, with two solvable P=Q=1 cases showing oscillations about steady values. This is a retrieval clue only. It does not provide the primary equations, exact notation, functional assumptions, or page-level derivation.

The BHL record exposes an article PDF route, but the BHL page and article route returned HTTP 403 to the current retrieval interface. Consequently, the scan itself has not been inspected. No formula is transcribed here.

## Structural-family implications

Bailey's 1933 article is part of the same author's broader 1931–1933 host/parasite mathematical programme as:
- “The Interaction between Hosts and Parasites” (1931), *Quarterly Journal of Mathematics* os-2(1), 68–77.
- “On the Interaction between Several Species of Hosts and Parasites” (1933), *Proceedings of the Royal Society A* 143, 75–88.
- “Non-continuous Interaction between Hosts and Parasites” (1933), *Mathematical Proceedings of the Cambridge Philosophical Society* 29(4), 487–491.

Do not treat the four publications as four independent statistical units or four structurally distinct equations based on titles. The 1933 BHL paper may be a shorter/earlier statement of the multi-species theory; inspect the equations and derivation lineage across all Bailey papers before assigning source-family IDs or E0–E5 classes.

The Royal Society archive's referee reports RR/49/1–3 relate specifically to the separate *Proceedings of the Royal Society A* paper (DOI 10.1098/rspa.1933.0204). They are not peer-review evidence for the BHL article and must not be conflated.

## Disposition and next retrieval steps

- Record as a high-priority primary-source retrieval lead, not an equation candidate.
- Obtain the BHL article PDF through an alternate BHL client/API, partner-library holding, or Royal Society of New South Wales archive.
- Inspect printed pp. 387–393 and capture the complete system, definitions, assumptions, equilibrium conditions, and page/line evidence.
- Compare directly with Bailey 1931, Bailey's 1933 *Proceedings A* paper, Bailey's 1933 non-continuous paper, Lotka's 1920/1923 work, and Thompson's host-parasite formulations.
- Keep all candidates proposed and generator-pending until primary transcription and structural review are complete.

## Sources checked

- BHL article record and PDF availability: https://www.biodiversitylibrary.org/part/360060
- BHL field mirror metadata: https://field.biodiversitylibrary.org/part/360060
- Royal Society of New South Wales volume 66 index: https://www.royalsoc.org.au/jprocrsnsw-vol-66/
- Royal Society of New South Wales DOI index: https://www.royalsoc.org.au/wp-content/uploads/2025/12/RSNSW_Journal_Index_20251230.html
- University of Melbourne Bailey bibliography: https://asap.unimelb.edu.au/bsparcs/physics/P000031p.htm
- Secondary abstract used only as a retrieval clue: https://eurekamag.com/research/023/937/023937519.php

**Execution boundary:** no source PDF was inspected, no equations were accepted, and no code, validators, tests, experiments, workflows, or live protocol calls were run.
