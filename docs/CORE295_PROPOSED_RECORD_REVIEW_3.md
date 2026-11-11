# Core-295 proposed equation records — review pass 3

**Status:** one additional Physics record drafted as proposed. It is not accepted, scientifically reviewed, structurally reviewed or eligible for shard planning.

## PHYS-POISEUILLE-001 — Poiseuille laminar tube-flow relation

Source: OpenStax, *University Physics Volume 1*, §14.7, “Viscosity and Turbulence,” Eq. 14.19.

\[
Q=\frac{(p_2-p_1)\pi r^4}{8\eta l}.
\]

Here \(Q\) is volumetric flow rate, \(p_2-p_1\) is the pressure drop along the tube, \(r\) is internal radius, \(\eta\) is dynamic viscosity and \(l\) is tube length. The source separately gives the hydraulic resistance \(R=8\eta l/(\pi r^4)\) in Eq. 14.18 and \(Q=(p_2-p_1)/R\); these are linked derivation steps, not additional equation candidates.

**Model assumptions to freeze:** steady laminar flow; incompressible Newtonian fluid; constant viscosity; straight, rigid, cylindrical tube; no-slip wall; fully developed parabolic velocity profile; negligible entrance/end effects.

**Benchmark constraints:** require \(p_2>p_1\), positive \(r,\eta,l\), and ensure the generated Reynolds number remains within the laminar regime. Do not create train/extrapolation ranges until the intended fluid, geometry and pressure regime are specified. Extrapolation must not silently cross into turbulence or a different constitutive regime.

## Proposed-record inventory

- Chemistry: CHEM-HENRY-001, CHEM-LANGMUIR-001, CHEM-MARCUS-001.
- Biology: BIO-HILL-MUSCLE-001.
- Physics: PHYS-POISEUILLE-001.
- All five records are proposed; none is accepted.
- Ranges and generator contracts remain pending.

No experiment, validator execution, live API call or GitHub Actions workflow was run.
