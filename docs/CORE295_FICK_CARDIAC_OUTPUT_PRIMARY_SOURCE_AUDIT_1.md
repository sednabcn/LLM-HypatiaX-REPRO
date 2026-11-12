# Core-295 Fick cardiac-output primary-source audit 1

Date: 2026-11-12

Candidate: `BIO-FICK-CARDIAC-OUTPUT-001`

## Primary-source verification

Adolf Fick, “Ueber die Messung des Blutquantums in den Herzventrikeln,” report to the Physico-Medical Society of Würzburg, 9 July 1870, *Sitzungsberichte für das Gesellschaftsjahr 1870*, Neue Folge 2, pp. XVI–XVII.

The original one-page report is available as a scan reproduced from the U.S. National Library of Medicine History of Medicine collection. Fick proposes measuring an animal's oxygen uptake over a known time interval and measuring oxygen content in arterial and venous blood samples. He states that the difference in oxygen content gives the oxygen taken up by each cubic centimetre of blood passing through the lungs; dividing total oxygen uptake per time by this arteriovenous oxygen-content difference gives blood volume passing per time. Dividing by heart beats gives stroke volume. Fick also describes the analogous carbon-dioxide calculation as a check.

The original report states the mass-balance reasoning in prose; the familiar compact algebraic equation is a modern notation for that balance, not a verbatim displayed formula from the 1870 page:

\[
Q=\frac{\dot V_{O_2}}{C_{aO_2}-C_{vO_2}}.
\]

A modern explicit rendering is given by Laszlo (2004), who states the same equation and identifies mixed venous blood as the required venous sample.

## Correct model roles and units

The catalogue record omitted the predicted output. Correct roles:
- independent inputs: \(\dot V_{O_2}, C_{aO_2}, C_{vO_2}\);
- dependent output: cardiac output \(Q\).

Use consistent units:
- \(\dot V_{O_2}\): mL O2 min\(^{-1}\);
- \(C_{aO_2},C_{vO_2}\): mL O2 L\(^{-1}\) blood;
- \(Q\): L blood min\(^{-1}\).

The ratio then has units L min\(^{-1}\). The denominator must be strictly positive for the usual systemic oxygen-extraction convention.

## Physiological scope and limitations

- The original proposal concerns whole-body oxygen uptake and arterial/venous oxygen-content differences, under a steady measurement interval.
- The modern direct Fick method uses a mixed-venous (pulmonary-arterial) sample, not an arbitrary peripheral or central venous sample.
- Oxygen uptake measured over the interval must correspond to the blood flow and oxygen-content samples from the same physiological steady state.
- Shunts, incomplete mixing, rapidly changing oxygen stores, or non-steady oxygen consumption invalidate the simple balance or introduce bias.
- Fick's original prose also mentions a carbon-dioxide balance. That is a related application of the same indicator/mass-balance principle, not a second independent equation candidate.
- The original report presents a method and a calculation example using existing data; it is not a population sampling distribution for benchmark inputs.

## Catalogue disposition

Correct the missing dependent variable to Q and preserve the modern equation as a source-derived algebraic rendering of Fick's original prose. Do not claim the compact expression is printed verbatim in 1870. Keep train/extrapolation ranges unset; no universal clinical ranges should be inferred from this historical method note. Candidate remains proposed and generator pending.

## Sources

- Fick (1870), original scanned report, “Ueber die Messung des Blutquantums in den Herzkammern,” pp. XVI–XVII, scan reproduced from U.S. National Library of Medicine History of Medicine collection: https://www.w.mriquestions.com/uploads/3/4/5/7/34572113/fick_original.pdf
- Laszlo (2004), “Respiratory measurements of cardiac output: from elegant idea to useful test,” *Journal of Applied Physiology* 96(2), modern explicit equation and mixed-venous scope: https://doi.org/10.1152/japplphysiol.01074.2001
- Historical bibliographic record and scan link: https://historyofmedicine.com/id/251

No scripts, validators, tests, workflows, live experiments or scientific simulations were run.
