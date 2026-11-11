# Core-295 candidate discovery batch 31: Bernoulli flow, Stokes drag and Young–Laplace capillarity

**Date:** 2026-11-11  
**Status:** discovery-only source leads. None is added to the formal catalogue or counted toward 295.  
**Domain focus:** Physics, especially fluid mechanics and interfacial mechanics.

## 1. Bernoulli mechanical-energy relation

**Source:** OpenStax University Physics Volume 1 §14.6, Eq. 14.16.

For steady flow of an incompressible, inviscid fluid along a streamline:
[
p+\frac12\rho v^2+\rho gh=\mathrm{constant}.
]
Between two points:
[
p_1+\frac12\rho v_1^2+\rho gh_1
=p_2+\frac12\rho v_2^2+\rho gh_2.
]

The source derives the relation from pressure work, kinetic-energy change and gravitational potential-energy change. The sum is mechanical energy per unit volume.

**Boundary and risks:** incompressible fluid, negligible viscosity/friction, steady flow, and application along a streamline. It is not valid as a universal pressure-speed relation in turbulent or strongly viscous flow. Pump work, shaft work, viscous dissipation and heat transfer require an extended energy equation. The constant-depth Bernoulli principle is a special case, not another equation.

**Family note:** Bernoulli is an energy integral of inviscid fluid momentum dynamics. It is related to Euler/Navier–Stokes flow, but it is not Poiseuille flow: the latter is a viscous laminar pressure-driven solution. Keep the Bernoulli equation and constant-height simplification in one family.

**Initial disposition:** credible scalar Physics lead; hold pending flow-regime and streamline/range contract and a derivation-family policy against Euler/Navier–Stokes.

## 2. Stokes drag on a sphere in creeping flow

**Sources:** G. G. Stokes (1851), *On the effect of the internal friction of fluids on the motion of pendulums*, Transactions of the Cambridge Philosophical Society 9, 8–106; Landau and Lifshitz, *Fluid Mechanics*, §20, Eq. 20.14; OpenStax University Physics Volume 1 §6.4.

For a sphere of radius (a) moving at relative speed (U) through a Newtonian fluid of dynamic viscosity (mu), the drag magnitude is:
[
F_D=6\pi\mu aU.
]
The vector force opposes the relative motion. The source derivation is the steady creeping-flow solution around a sphere; inertia terms are neglected.

**Boundary and risks:** low Reynolds number (strict creeping-flow limit (Rell1)); incompressible Newtonian fluid; isolated sphere; no nearby walls; no slip; steady relative motion. Finite-Reynolds corrections, wall corrections, non-spherical particles and non-Newtonian fluids are outside the simple law.

**Family note:** the terminal settling speed of a sphere is obtained by balancing Stokes drag against weight minus buoyancy; it is a derived output, not a second candidate. Stokes drag and Poiseuille flow are both special solutions of viscous fluid equations but have different geometries and state/observable relations. Whether they count as independent structures depends on the declared model-family unit.

**Initial disposition:** credible scalar Physics lead; hold pending the strict low-Reynolds domain and family-dependence policy with Poiseuille/Navier–Stokes.

## 3. Young–Laplace pressure jump across a curved interface

**Source:** authoritative surface-science/physical-chemistry text, *The Young–Laplace Equation: The Basic Law of Capillarity*, §1.2, Eq. 1.5; the source derives the spherical-drop special case by balancing mechanical work against surface-energy increase.

For an interface with uniform surface tension (gamma) and principal radii of curvature (R_1,R_2):
[
\Delta p=\gamma\left(\frac{1}{R_1}+\frac{1}{R_2}\right).
]
For a spherical liquid drop of radius (R), (Delta p=2gamma/R). A soap bubble has two interfaces and therefore a pressure excess (4gamma/R).

**Boundary and risks:** static or quasi-static interface, uniform isotropic surface tension, well-defined principal curvatures and consistent sign/orientation convention. Surface-tension gradients, bending stresses, dynamic curvature and contact-line effects require extensions.

**Family note:** this is a curvature-dependent interfacial pressure relation, not Bernoulli flow or Poiseuille resistance. The spherical-drop and soap-bubble forms are geometric/interface-count specializations, not independent equations.

**Initial disposition:** strong candidate lead; hold pending exact source-page citation, curvature/sign convention and a deterministic shape/geometry contract.

## 4. Batch-level structural decisions

| Lead | Structure | Principal issue | Initial decision |
|---|---|---|---|
| Bernoulli | Sum of pressure, kinetic and gravitational energy densities constant along streamline | Energy integral of inviscid fluid dynamics; strict streamline/flow assumptions | Hold; consider |
| Stokes drag | Linear viscous drag (6\pi\mu aU) for a sphere | Creeping-flow limit; derived from Stokes/Navier–Stokes special solution | Hold; consider |
| Young–Laplace | Pressure jump proportional to sum of principal curvatures | Interface geometry, sign convention and shape adapter | Hold; high priority |

Do not count Bernoulli's constant-height form, Stokes terminal settling speed, or spherical/soap-bubble Young–Laplace specializations as separate candidates.

## 5. Catalogue status and work not performed

No source-register or equation-catalogue record was changed. The formal manifest remains 128 source records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, validators, solvers, workflows, paid compute, API calls, flow measurements or surface-tension measurements were run. This is source discovery only.
