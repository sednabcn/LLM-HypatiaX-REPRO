# Core-295 source verification audit 23: Fick 1870 cardiac-output mass-balance principle

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** proposed record BIO-FICK-CARDIAC-OUTPUT-001 and source BIO-FICK-1870. The original 1870 scanned report is now accessible and was checked directly.

## 1. Original source and transcription boundary

Adolf Fick, *Ueber die Messung des Blutquantums in den Herzventrikeln*, Sitzungsberichte der Physikalisch-Medicinischen Gesellschaft zu Würzburg, Neue Folge 2, pp. XVI–XVII (1870), Fourteenth session, 9 July 1870.

The original report does not print the modern symbolic equation. It states the measurement principle in words:
- measure the amount of oxygen an animal takes up from air over a known time;
- take arterial and venous blood samples during the same experimental interval and measure their oxygen contents;
- the difference in oxygen content gives the amount of oxygen taken up by each unit volume of blood passing through the lungs;
- divide the total oxygen uptake per time by this per-volume oxygen difference to obtain blood flow through the lungs;
- dividing by heart beats over the interval gives stroke volume.
The report also describes a corresponding carbon-dioxide calculation as a check on the oxygen-derived value.

Thus the modern equation is a faithful mass-balance transcription of the original prose, not a verbatim displayed equation from Fick's page.

## 2. Modern equation and unit contract

Let:
- (dot V_{O_2}) be oxygen uptake/consumption per unit time;
- (C_{aO_2}) be arterial oxygen content per unit blood volume;
- (C_{vO_2}) be mixed-venous oxygen content per unit blood volume;
- (Q) be blood flow/cardiac output.

The conservation relation is
[
dot V_{O_2}=Q(C_{aO_2}-C_{vO_2}),
]
hence
[
Q=\frac{\dot V_{O_2}}{C_{aO_2}-C_{vO_2}}.
]
For (dot V_{O_2}) in mL O\(_2\)/min and oxygen contents in mL O\(_2\)/L blood, (Q) is L blood/min. If contents are in mL/dL, convert them consistently before division.

The denominator must be positive for the usual systemic arterial-minus-mixed-venous oxygen extraction convention. A nonpositive or near-zero difference makes the calculation invalid or unstable.

## 3. Physiological assumptions and limits

The benchmark adapter must make explicit:
- oxygen uptake and arterial/mixed-venous oxygen contents refer to the same time interval and physiological state;
- oxygen uptake is at steady state (or the relevant oxygen-storage/transient terms are negligible);
- the sampled venous blood represents the mixed venous return for the circulation being measured;
- blood flow is the flow through the sampled vascular bed/system;
- oxygen content units, not merely oxygen partial pressures or saturations, are used.

The original 1870 note also uses a CO\(_2\)-based calculation as an independent check. That check is not a second Fick cardiac-output equation. Stroke volume (=Q/	ext{heart rate}) is a derived output and should not be counted separately.

## 4. Structural and domain classification

This is a physiological conservation/mass-balance measurement relation. It is not a dynamic ODE and not the same as Fick's law of diffusion:
- cardiac-output Fick: flow = metabolic uptake rate / arteriovenous content difference;
- diffusion Fick: flux = negative diffusivity times a concentration gradient.

The shared surname does not establish one equation family. The two relations have different variables, physical dimensions, governing balances and scientific domains.

**Disposition:** original source prose and modern mass-balance transcription verified. Retain as a credible Biology candidate, held pending a precise steady-state/system boundary, content units, and physiologically defensible input ranges. Do not count the CO\(_2\) cross-check or stroke-volume conversion as additional equations.

## 5. Catalogue and experiment status

No catalogue record, source status, proposed count or accepted count was changed. The formal catalogue remains at 128 source records, 19 proposed records and zero accepted records; the sampling frame remains unfrozen.

No experiments, solvers, validators, workflows, paid compute, API calls, blood sampling or clinical measurements were performed. This is historical source review and dimensional analysis only.
