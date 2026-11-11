# Core-295 source verification audit 36: Butler–Volmer convention and Nernst–Planck ionic flux

**Date:** 2026-11-11  
**Status:** verification/correction of discovery-batch 30 leads only. No equation is added to the formal catalogue or counted toward 295.

## 1. Butler–Volmer electrode kinetics: historical and notation corrections

### Historical source lineage

Dickinson and Wain (2020), *The Butler–Volmer equation in electrochemical theory: Origins, value, and practical application*, Journal of Electroanalytical Chemistry 872, 114145, DOI 10.1016/j.jelechem.2020.114145, review the original literature and distinguish empirical, engineer's and practical forms.

The review makes an important historical correction:
- Butler's 1924 papers developed a kinetic interpretation of the Nernst equilibrium potential and transition-state/balance-point ideas; they did **not** derive the general electrode rate equation now commonly called Butler–Volmer.
- Erdey-Grúz and Volmer (1930) considered reversible anodic and cathodic contributions for a hydrogen-electrode rate-determining step.
- Later Butler work and subsequent electrochemical engineering conventions contributed to the forms now used.

Thus Butler 1924 is part of the conceptual lineage, but should not be described as the source of the complete modern current–overpotential equation.

### Recommended modern form

The 2020 review defines \(f=F/(RT)\) and writes an engineer's form:
\[
i=i_0\left[
\exp(\alpha_a f\eta)
-\exp(-\alpha_c f\eta)
\right],
\]
for the reference-concentration form, with concentration/activity correction factors added in more general practical expressions. Here \(\alpha_a,\alpha_c\) are dimensionless transfer coefficients and \(\eta\) is overpotential relative to the Nernst equilibrium potential.

**Critical convention:** in the recommended engineer's convention, the transfer coefficients are not multiplied by the total electron number \(n\). Older textbook forms often write \(\alpha nF\eta/(RT)\); this is a different coefficient convention and must not be mixed with the unscaled transfer-coefficient definition. For a single elementary one-electron step, \(n=1\) and the forms coincide. Multi-electron overall reactions may consist of multiple elementary steps and cannot automatically be represented by a single Butler–Volmer relation with an arbitrary total \(n\).

The review emphasizes that Butler–Volmer is an empirical/phenomenological two-way activated redox relation. It is inappropriate for many multistep electrocatalytic reactions or solid-insertion processes unless the assumed rate-determining elementary step and concentration dependencies are justified.

### Family boundary

- Nernst gives the equilibrium potential and defines the zero-overpotential reference.
- Butler–Volmer gives net interfacial current under polarization.
- Tafel laws are high-overpotential asymptotes of Butler–Volmer.
- Linear small-overpotential response is a local approximation.
- Anodic and cathodic partial currents are the two terms of one net-current equation.

These are related components/limits of one electrode-kinetics family, not independent equation candidates. Marcus outer-sphere electron transfer is a different microscopic model with a quadratic free-energy barrier; the two models should be compared at the level of their complete rate expressions, not their shared activated-exponential terminology.

**Disposition:** modern forms and historical lineage verified. Discovery batch 30's equation should be corrected to use \(\alpha_aF\eta/(RT)\) and \(\alpha_cF\eta/(RT)\) under the stated modern convention, or else explicitly document the alternative \(n\)-scaled transfer-coefficient convention. Keep Butler–Volmer discovery-only pending the exact reaction step, reference concentration/activity and coefficient convention.

## 2. Nernst–Planck ionic flux: source and unit convention

An authoritative electrochemical transport treatment gives the dilute-solution ionic molar flux as:
\[
\mathbf J_i
=-D_i\nabla c_i
-z_i u_{m,i}F c_i\nabla\phi
+c_i\mathbf v,
\]
where \(u_{m,i}\) is the ionic mobility under the source's molar mobility convention. Using the Nernst–Einstein relation \(u_{m,i}=D_i/(RT)\) gives:
\[
\mathbf J_i
=-D_i\nabla c_i
-\frac{z_iFD_i}{RT}c_i\nabla\phi
+c_i\mathbf v.
\]
The second expression is therefore not a notation-free identity: it assumes the ideal dilute-solution mobility–diffusivity relation. The source's electrochemical cell modeling treatment labels the terms diffusion, migration and convection and gives flux units mol m\(^{-2}\) s\(^{-1}\).

The species balance is:
\[
\frac{\partial c_i}{\partial t}
=-\nabla\cdot\mathbf J_i+R_i.
\]
The balance equation, flux law and Poisson/electroneutrality closure form a coupled electrodiffusion system. They must not be counted as independent equation entries when the chosen model is the complete Nernst–Planck/Poisson–Nernst–Planck system.

### Boundary and source limitations

The simple Nernst–Planck law uses ideal dilute-solution electrochemical potentials. Nonideal concentrated electrolytes require activity-gradient terms and possibly cross-diffusion/thermodynamic-factor corrections. The mobility–diffusivity relation, concentration convention, electric-potential reference, valence, convection frame and boundary conditions must all be fixed. A page-level transcription from the selected primary electrochemical transport text is still required before source_verified status.

**Disposition:** mathematical form and unit conventions checked; keep discovery-only pending a selected primary/textbook source edition, dilute vs nonideal solution contract, Poisson vs electroneutral closure and a coupled vector/PDE adapter.

## 3. Corrections to discovery batch 30

1. Butler–Volmer's historical attribution must not imply that Butler's 1924 paper directly introduced the modern rate equation.
2. The transfer-coefficient convention must be explicit. Under the 2020 review's engineer's form, use \(\alpha_aF\eta/(RT)\) and \(\alpha_cF\eta/(RT)\), not an additional total-electron factor \(n\).
3. The Nernst–Planck diffusivity form assumes the Nernst–Einstein mobility relation; keep the mobility form and diffusivity form distinct until the unit convention is fixed.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, electrode measurements or transport experiments were run. This is source and convention review only.
