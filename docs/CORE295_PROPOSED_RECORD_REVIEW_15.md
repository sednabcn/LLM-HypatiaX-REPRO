# Core-295 proposed equation records — review pass 15

**Status:** one additional Chemistry record drafted as proposed. It is not accepted, scientifically reviewed, structurally reviewed or eligible for shard planning.

## CHEM-FICK-FLUX-001 — one-dimensional diffusive flux law

The original Fick paper, “Ueber Diffusion,” *Annalen der Physik* 170(1) (1855), 59–86, is available as a publisher scan. On printed page 66, Fick writes the amount transferred through a layer of cross-section \(Q\) over time \(dt\) as proportional to the concentration gradient:

\[
dM=-Q\,k\,\frac{dy}{dx}\,dt.
\]

Dividing by area and time gives the modern one-dimensional flux form:

\[
J=-D\frac{\partial C}{\partial x}.
\]

Here \(J\) is diffusive mass or molar flux, \(D\) is diffusivity, and \(C\) is concentration. The original notation maps \(k\) to diffusivity and \(y\) to concentration. The same page derives a diffusion PDE from the local flux law; the PDE and constant-cross-section specialization are linked derivations, not separate independent equation candidates.

**Critical structural caveat:** this is a linear gradient-transport law, algebraically analogous to Fourier heat flux and Ohm current density. It is source-distinct but may not be structurally distinct under the Core-295 equivalence policy. It remains proposed until cross-domain fingerprint/family review resolves whether it can count independently. Do not accept it merely because it has a different physical interpretation.

**Benchmark blockers:** define species, medium, concentration convention, diffusivity units/range, coordinate direction and flux orientation; specify no advection, homogeneous medium and constant diffusivity; freeze a deterministic scalar gradient generator. The diffusion PDE is not a second record.

## Proposed-record inventory

- Chemistry: CHEM-HENRY-001, CHEM-LANGMUIR-001, CHEM-MARCUS-001, CHEM-RAOULT-VAPOR-001, CHEM-FICK-FLUX-001.
- Biology: BIO-HILL-MUSCLE-001, BIO-FICK-CARDIAC-OUTPUT-001.
- Physics: PHYS-POISEUILLE-001, PHYS-PLANCK-SPECTRUM-001, PHYS-THIN-LENS-001.
- DeFi AMM: AMM-BALANCER-WEIGHTED-001, AMM-DODO-PMM-BASE-SHORTAGE-001.
- DeFi Risk: RISK-MORPHO-LIF-001, RISK-EULER-AUCTION-001, RISK-COMPOUND-BORROW-KINK-001, RISK-UNISWAP-V3-GEOMETRIC-TWAP-001, RISK-UNISWAP-V2-ARITHMETIC-TWAP-001.
- All seventeen records are proposed; none is accepted.
- Ranges and generator contracts remain pending.

No experiment, validator execution, live API call or GitHub Actions workflow was run.
