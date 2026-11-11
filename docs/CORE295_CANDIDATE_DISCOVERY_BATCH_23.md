# Core-295 candidate discovery batch 23: Chemistry Rideal–Eley surface-reaction kinetics

**Status:** primary mechanism tracing and modern rate-law cross-check only. No equation is accepted or counted toward the 59 Chemistry target.

## 1. Rideal–Eley (Langmuir–Rideal) mechanism

**Primary source trail:**
- Rideal (1939), “A note on a simple molecular mechanism for heterogeneous catalytic reactions,” *Mathematical Proceedings of the Cambridge Philosophical Society* 35(1), 130–132, DOI [10.1017/S030500410002082X](https://doi.org/10.1017/S030500410002082X).
- Eley & Rideal (1940), “Parahydrogen Conversion on Tungsten,” *Nature* 146, 401–402, DOI [10.1038/146401d0](https://doi.org/10.1038/146401d0).
- [IUPAC Gold Book: Langmuir–Rideal mechanism](https://goldbook.iupac.org/terms/view/L03453).

The defining mechanistic distinction is that one reactant is adsorbed while the second reacts directly from the gas phase. For a simple competitive-adsorption case in which reactant A adsorbs and gas-phase B reacts with A*, an engineering form is:

\[
-r_A'=
\frac{kP_AP_B}
{1+K_AP_A+K_CP_C}.
\]

Here \(P_A,P_B,P_C\) are gas partial pressures, \(K_A,K_C\) adsorption constants for A and a competitively adsorbed product/inhibitor C, and \(k\) a surface-reaction rate coefficient. This explicit form is shown in the University of Michigan Elements of Chemical Reaction Engineering Eley–Rideal example; it is a modern cross-check, not a verbatim equation from Rideal's 1939 note.

## 2. Distinction from Langmuir–Hinshelwood

For the bimolecular Langmuir–Hinshelwood mechanism in Batch 15, both reactants are adsorbed and the surface reaction occurs between two adsorbed species. Under competitive adsorption and a common site balance, its denominator is squared:

\[
r_{LH}\propto
\frac{K_AK_BP_AP_B}
{(1+K_AP_A+K_BP_B)^2}.
\]

For the Rideal–Eley mechanism, one reactant remains in the gas phase and only the adsorbed species occupies the surface sites; the simple denominator is first power:

\[
r_{ER}\propto
\frac{K_AP_AP_B}
{1+K_AP_A+K_CP_C}.
\]

The exponent and adsorbed-species set arise from the different elementary mechanisms, not from algebraic rearrangement. A rate law must not be assigned to a catalyst/reaction without experimental or mechanistic evidence that the corresponding pathway is operative.

## 3. Primary-source and model limits

The 1940 Eley–Rideal tungsten paper discusses a surface-interchange mechanism for para/ortho hydrogen conversion and argues against an alternative mechanism based on two adsorbed hydrogen atoms. It is evidence for the gas-phase/adsorbed-species mechanism, but the general engineering rate expression above is a later model form with explicit competitive adsorption.

The 1939 Rideal note is a short mechanistic proposal, not a general rate-law derivation for every heterogeneous catalytic reaction. The 1940 experimental paper studies a specific hydrogen/tungsten system. Keep the historical mechanism evidence separate from the later general rate expression.

## Source-family and overlap controls

- Langmuir adsorption coverage, site balance and the Rideal–Eley rate expression are linked; the surface coverage relation is not a separate equation count for each catalyst.
- Langmuir–Hinshelwood and Rideal–Eley are distinct surface-reaction mechanisms: two adsorbed reactants versus one adsorbed plus one gas-phase reactant. Keep separate mathematical candidates but cluster them within heterogeneous surface catalysis.
- Product inhibition, competitive adsorption, adsorption of additional species and algebraic rearrangements do not create separate families unless the elementary mechanism changes.
- Langmuir's single-site monolayer assumptions do not apply universally; heterogeneous sites, dissociative adsorption, multisite adsorption and transport limitations require separate mechanistic models.
- Core-15 exclusions remain active. Do not introduce Arrhenius temperature dependence as a new equation family.

## Acceptance requirements

Record the elementary reaction mechanism, adsorbed species, gas-phase species, site balance, adsorption/desorption equilibrium assumptions, rate-determining step, pressure/activity convention, catalyst surface state, temperature and transport limitations. The primary mechanism source and the modern explicit rate-law source must both be cited; do not present the engineering example as the original 1939 equation.

All records remain candidates. No Chemistry entry is accepted; no experiment or workflow has been run.
