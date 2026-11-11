# Core-295 proposed equation records — review pass 12

**Status:** one additional Biology record drafted as proposed. It is not accepted, scientifically reviewed, structurally reviewed or eligible for shard planning.

## BIO-FICK-CARDIAC-OUTPUT-001 — Fick oxygen mass-balance relation

The direct Fick cardiac-output relation is:

\[
Q=\frac{\dot V_{O_2}}{C_{aO_2}-C_{vO_2}}.
\]

Here \(Q\) is cardiac output, \(\dot V_{O_2}\) is whole-body oxygen uptake per unit time, \(C_{aO_2}\) is arterial oxygen content, and \(C_{vO_2}\) is mixed venous oxygen content. With \(\dot V_{O_2}\) in mL O\(_2\)/min and the content difference in mL O\(_2\)/L blood, \(Q\) is L/min.

**Primary source:** Adolf Fick (1870), “Ueber die Messung des Blutquantums in den Herzventrikeln,” *Sitzungsberichte der Physikalisch-Medizinischen Gesellschaft zu Würzburg*, Neue Folge 2, XVI–XVII. The Garrison-Morton-Norman record links a Hathi Trust digital facsimile. The scan endpoint currently returns access denied, so the original page equation remains to be checked. Geerts, Aarts & Jansen (2011), *British Journal of Clinical Pharmacology*, 71, 316–330, explicitly describes the oxygen mass balance and the direct Fick method.

**Assumptions:** steady-state oxygen balance; oxygen uptake in the lungs transferred into blood; no material pulmonary oxygen consumption/storage; representative arterial and mixed venous oxygen contents; no unaccounted shunt or mixing failure.

**Benchmark blockers:** obtain and transcribe the original 1870 pages; define a physiologically coherent steady-state input domain; enforce \(C_{aO_2}>C_{vO_2}\); specify mixed-venous sampling; freeze units and deterministic generation. This is one mass-balance family: do not count algebraic rearrangements or the carbon-dioxide analogue independently.

## Proposed-record inventory

- Chemistry: CHEM-HENRY-001, CHEM-LANGMUIR-001, CHEM-MARCUS-001, CHEM-RAOULT-VAPOR-001.
- Biology: BIO-HILL-MUSCLE-001, BIO-FICK-CARDIAC-OUTPUT-001.
- Physics: PHYS-POISEUILLE-001, PHYS-PLANCK-SPECTRUM-001, PHYS-THIN-LENS-001.
- DeFi AMM: AMM-BALANCER-WEIGHTED-001, AMM-DODO-PMM-BASE-SHORTAGE-001.
- DeFi Risk: RISK-MORPHO-LIF-001, RISK-EULER-AUCTION-001, RISK-COMPOUND-BORROW-KINK-001.
- All fourteen records are proposed; none is accepted.
- Ranges and generator contracts remain pending.

No experiment, validator execution, live API call or GitHub Actions workflow was run.
