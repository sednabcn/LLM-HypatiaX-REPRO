# Core-295 source verification audit 27: Nernst electrochemical equilibrium and Debye–Hückel limiting activity law

**Date:** 2026-11-11  
**Status:** verification of discovery-batch leads only. No equation is added to the formal catalogue or counted toward 295.  
**Scope:** discovery batch 25 leads Nernst and Debye–Hückel. This audit checks primary historical context and modern authoritative definitions.

## 1. Nernst equation

### 1.1 Original 1889 source

Walther Nernst, *Die elektromotorische Wirksamkeit der Jonen*, Zeitschrift für Physikalische Chemie 4 (1889), 129–181, DOI 10.1515/zpch-1889-0412. The original theory relates an electrode potential difference to a logarithm of the ratio between the metal's dissolution pressure (P) and the ionic osmotic pressure (p). A modern historical account transcribes the original form as a constant proportional to (T\ln(P/p)). Nernst's original notation and physical model are not the same as the later general whole-cell reaction-quotient notation.

### 1.2 Modern general equation

IUPAC Gold Book 09068 defines the equilibrium electrode potential for a reduction reaction:
[
E_{eq}=E^\circ-\frac{RT}{zF}\sum_i\nu_i\ln a_i,
]
where (z) is the electron number, (
u_i) are signed stoichiometric coefficients (positive for products, negative for reactants), and (a_i) are dimensionless activities relative to standard states.

For a whole electrochemical cell this is commonly written:
[
E_{cell}=E_{cell}^\circ-\frac{RT}{nF}\ln Q.
]
The (Q) convention must match the written reaction direction. Reversing the cell reaction changes the sign and reciprocal of (Q). Using concentrations instead of activities is an ideal-solution approximation or requires a formal potential that absorbs the nonideality.

**Family boundary:** the reaction quotient, single-electrode expression, whole-cell expression, concentration-cell special case and 298.15 K base-10 form are related representations of one equilibrium-potential law. The standard-potential/equilibrium-constant identity and Gibbs-energy conversion are not extra candidates.

**Disposition:** modern equation and original historical lineage verified. Retain as a strong Chemistry source lead, discovery-only, pending a fixed reaction/stoichiometry/activity convention and a structural-family decision against other logarithmic chemical-potential relations.

## 2. Debye–Hückel limiting law

### 2.1 Original 1923 source and correct observable

Peter Debye and Erich Hückel, *Zur Theorie der Elektrolyte. I. Gefrierpunktserniedrigung und verwandte Erscheinungen*, Physikalische Zeitschrift 24 (1923), 185 onward. The original paper develops the ionic-atmosphere correction to the thermodynamic potential and introduces activity-coefficient corrections. It derives the low-concentration square-root dependence from the ionic-atmosphere length, which varies with the square root of ionic concentration. The paper distinguishes the osmotic coefficient (f_0) from an activity coefficient (f_a); these are not interchangeable observables.

The modern Debye–Hückel limiting law is most safely stated for the mean molal activity coefficient of an electrolyte:
[
\log_{10}\gamma_{\pm}
=-A\,|z_+z_-|\sqrt{I},
]
where (I=\tfrac12\sum_i m_i z_i^2) is molal ionic strength, (z_+) and (z_-) are the cation/anion charge numbers, and (A) depends on solvent and temperature. For a uni-univalent electrolyte, (|z_+z_-|=1).

The common single-ion expression (log_{10}\gamma_i=-Az_i^2\sqrt I) is a theoretical convention-dependent form, not a separately measurable thermodynamic quantity. IUPAC notes that an individual ion's activity cannot be determined on a purely thermodynamic basis because the counter-ion contribution cannot be separated. For benchmark use, prefer the mean ionic activity coefficient unless the single-ion convention is explicitly fixed.

### 2.2 Validity and related equations

The limiting law applies only at sufficiently low ionic strength, where finite ion-size corrections are negligible. A common aqueous rule of thumb is around (I\lesssim0.01) mol kg(^{-1}) for uni-univalent electrolytes; the exact useful range depends on solvent, temperature and electrolyte. The extended Debye–Hückel equation introduces an ion-size parameter:
[
\log_{10}\gamma_{\pm}
=-\frac{A|z_+z_-|\sqrt I}{1+B a\sqrt I}.
]
Davies and Bates–Guggenheim are further approximations/conventions, not separate instances of the limiting law.

**Family boundary:** limiting, extended, Davies and other activity-coefficient corrections belong to one electrolyte nonideality family. The activity coefficient, osmotic coefficient, freezing-point depression and conductivity corrections are different observables derived within the same ionic-atmosphere theory; do not count them as one another's algebraic variants, but do not treat them as independent equation units without a clear system-level policy.

**Disposition:** original ionic-atmosphere theory and the modern mean-activity limiting law are source-supported. Retain as a strong Chemistry source lead, discovery-only, pending solvent/temperature/ionic-strength units, mean-ion convention and a parameter-validity contract.

## 3. Corrections to discovery batch 25

The Debye–Hückel lead in discovery batch 25 should be interpreted as the **mean ionic activity coefficient** form, not an unconstrained experimentally measurable single-ion coefficient. The original 1923 paper's (f_0) osmotic coefficient and (f_a) activity coefficient must remain distinguished. The Nernst lead should distinguish Nernst's original dissolution-pressure/osmotic-pressure electrode model from the modern general whole-cell reaction-quotient equation.

No source-register or equation-catalogue record was changed. The formal manifest remains 128 source records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, electrochemical measurements or solution-activity measurements were performed. This is historical and reference-source review only.
