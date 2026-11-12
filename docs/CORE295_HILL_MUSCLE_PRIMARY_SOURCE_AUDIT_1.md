# Core-295 Hill muscle primary-source audit 1

Date: 2026-11-12

Candidate: `BIO-HILL-MUSCLE-001`

## Primary-source verification

A. V. Hill (1938), “The Heat of Shortening and the Dynamic Constants of Muscle,” *Proceedings of the Royal Society of London B* 126(843), 136–195, DOI 10.1098/rspb.1938.0050. The original publisher scan is accessible through the Royal Society/Wiley-hosted PDF and a university-hosted mirror.

Hill's characteristic equation is stated in Part II and summarized in the paper's summary. On printed p.174, Hill derives the relation from the experimentally observed linear dependence of the rate of extra energy liberation on load. On printed p.177, he gives the empirical relation between load and speed of shortening under isotonic contraction and a concrete frog sartorius example:

\[
(P+14.35)(v+1.03)=87.6.
\]

The example is for a frog sartorius muscle in Ringer's solution at 0 °C, with the muscle tetanically stimulated at 11.4 shocks/s. Hill reports the measured curve using the mean of two observations in a series and reverse, with 5–6 mm shortening. In the source's units, P and a are gram-weight, v and b are cm/s, and the right-hand constant is gram-weight·cm/s.

Comparing this with the characteristic equation
\[
(P+a)(v+b)=(P_0+a)b
\]
gives \(a=14.35\) gram-weight, \(b=1.03\) cm/s, and \((P_0+a)b=87.6\). Thus \(P_0=87.6/1.03-14.35\approx70.65\) gram-weight. The latter is an algebraic reconstruction from the source's printed example, not a separately transcribed measurement. Preserve the source-unit convention rather than silently mixing SI and gram-weight.

## Correct model roles

The catalogue equation predicts shortening velocity \(V\). Therefore:
- independent variable: applied load \(P\);
- dependent variable: shortening velocity \(V\);
- fixed parameters: isometric force \(P_0\), Hill force/shortening-heat constant \(a\), and velocity constant \(b\).

The current record omitted the dependent output variable. Correct this role assignment.

## Scope and limits

- Specific source-grounded case: frog sartorius, Ringer's solution, 0 °C, tetanic stimulation, isotonic shortening.
- Positive shortening convention: \(0\le P\le P_0\), with \(V\ge0\); at \(P=P_0\), \(V=0\).
- The example's parameter values are one preparation/condition, not universal constants for all skeletal muscle.
- Hill reports the temperature coefficient of b as approximately 2.05 per 10 °C and notes that b scales with muscle length; temperature and geometry therefore cannot be varied while holding b fixed.
- The rectangular hyperbola is an empirical characteristic under maintained tetanic activation and approximately constant load; it is not a general transient contraction law or a full excitation-contraction model.
- The paper discusses limitations due to non-uniform contraction and relaxation and uses controlled isotonic shortening to isolate the relation.

## Catalogue disposition

Narrow the record to Hill's frog sartorius example at 0 °C and correct the missing dependent variable. Preserve source values in gram-weight and cm/s, or apply a documented full unit conversion in a later adapter. Keep train/extrapolation ranges unset: the printed example supplies a worked parameter set and observations, not a statistically adequate sampling distribution. Candidate remains proposed and generator pending.

## Sources

- Hill (1938), Royal Society original article DOI and OCR text: https://doi.org/10.1098/rspb.1938.0050
- Hill (1938), full scanned article mirror; printed pp.174 and 177 contain the derivation and worked frog sartorius equation: https://math.nyu.edu/~peskin/eb_lecture_notes/Hill_AV_1938.pdf
- Hill (1938), publisher page and article abstract: https://royalsocietypublishing.org/doi/10.1098/rspb.1938.0050
- Hill equation context and muscle force-velocity review: https://pmc.ncbi.nlm.nih.gov/articles/6593051/

No scripts, validators, tests, workflows, live experiments or scientific simulations were run.
