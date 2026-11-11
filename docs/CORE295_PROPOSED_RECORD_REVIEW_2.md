# Core-295 proposed equation records — review pass 2

**Status:** one additional Biology record drafted as proposed. It is not accepted, scientifically reviewed, structurally reviewed or eligible for shard planning.

## BIO-HILL-MUSCLE-001 — Hill muscle force–velocity relation

Primary source: A. V. Hill (1938), “The heat of shortening and the dynamic constants of muscle,” *Proceedings of the Royal Society B*, 126(843), 136–195, DOI [10.1098/rspb.1938.0050](https://doi.org/10.1098/rspb.1938.0050).

The characteristic relation is:

\[
(P+a)(V+b)=(P_0+a)b,
\]

where \(P\) is load/force, \(V\) shortening velocity, \(P_0\) isometric force, \(a\) a force-dimension constant and \(b\) a velocity-dimension constant. The scalar output adapter currently stores the algebraically solved velocity:

\[
V=\frac{b(P_0-P)}{P+a}.
\]

The second expression is the same characteristic relation, not a separate equation candidate. Contemporary physiological sources reproduce Hill's equation and explain its steady isotonic shortening interpretation. The original paper concerns muscle heat production and shortening dynamics; the model should be benchmarked only under a specified muscle preparation and contraction protocol.

**Provisional assumptions:** steady isotonic concentric shortening; tetanic activation; approximately constant load during the measurement; positive parameters; explicit treatment of the series-elastic element and sign convention.

**Outstanding before source verification or acceptance:**
1. Check the equation's exact page and notation against the Royal Society original scan (the source register currently points to pp. 174–177).
2. Freeze muscle type/preparation, temperature, activation and load protocol.
3. Define scientifically defensible force and velocity ranges, including the region where the hyperbolic approximation is reliable.
4. Define a deterministic scalar generator, units and extrapolation policy.
5. Review whether source-family or application dependencies make it unsuitable as an independent statistical unit.

The Hill muscle relation is not the Hill ligand-binding equation and is not the Core-15 Michaelis–Menten exclusion. Nevertheless, the exclusion list remains binding: **Michaelis–Menten itself must not be included**. Its source remains in the discovery bibliography only.

## Current proposed-record inventory

- Chemistry: CHEM-HENRY-001, CHEM-LANGMUIR-001, CHEM-MARCUS-001.
- Biology: BIO-HILL-MUSCLE-001.
- All four are proposed; none is accepted.
- Train/extrapolation ranges and generator contracts remain pending for every record.

No experiment, validator execution, live API call or GitHub Actions workflow was run.
