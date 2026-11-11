# Core-295 proposed equation records — review pass 5

**Status:** one additional Physics record drafted as proposed. It is not accepted, scientifically reviewed, structurally reviewed or eligible for shard planning.

## PHYS-THIN-LENS-001 — thin-lens imaging relation

Source: OpenStax *University Physics Volume 3*, §2.4, Eq. 2.19.

\[
\frac{1}{d_o}+\frac{1}{d_i}=\frac{1}{f},
\qquad
d_i=\frac{f d_o}{d_o-f}.
\]

The source states the thin-lens approximation and gives explicit sign conventions: image distance is positive for a real image on the opposite side of the object and negative for a virtual image; focal length is positive for a converging lens and negative for a diverging lens. The benchmark adapter stores signed image distance.

**Range blockers:** the singularity at \(d_o=f\) must be excluded; object distance and focal length must be nonzero; sample generation must preserve sign conventions and distinguish real/virtual images. The source derives the lens-maker relation in the same section; keep the thin-lens imaging relation and lens-maker relation clustered within geometric optics and do not count sign variants or rearrangements independently.

## Proposed-record inventory

- Chemistry: CHEM-HENRY-001, CHEM-LANGMUIR-001, CHEM-MARCUS-001.
- Biology: BIO-HILL-MUSCLE-001.
- Physics: PHYS-POISEUILLE-001, PHYS-PLANCK-SPECTRUM-001, PHYS-THIN-LENS-001.
- All seven records are proposed; none is accepted.
- Ranges and generator contracts remain pending.

No experiment, validator execution, live API call or GitHub Actions workflow was run.
