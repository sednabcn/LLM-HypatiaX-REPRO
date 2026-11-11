# Core-295 source verification audit 4: Windkessel hemodynamics and FitzHugh's original BVP system

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** two existing Biology source-register leads. This review checks exact model structure, source lineage, assumptions and catalogue implications; it does not freeze numerical ranges or a generator.

## 1. Biology: Frank's Windkessel model

### 1.1 Model and equation

Frank's 1899 paper, *Die Grundform des arteriellen Pulses*, introduced a lumped compliant arterial compartment with peripheral outflow resistance. The source register already contains BIO-WINDKESSEL-FRANK-1899; a 1990 English translation is indexed in PubMed (J Mol Cell Cardiol 22(3), 255–277; DOI 10.1016/0022-2828(90)91460-o).

The historical review by Parker (2009) describes Frank's original single-compliant-compartment construction and gives its diastolic pressure decay. A later physiological derivation makes the mass balance and the canonical two-element model explicit:

\[
Q_{in}=Q_{stored}+Q_{out},
\qquad
Q_{stored}=C\frac{dP}{dt},
\qquad
Q_{out}=\frac{P}{R}.
\]

With constant compliance C, constant peripheral resistance R, and reference/venous pressure set to zero, the model is

\[
C\frac{dP}{dt}+\frac{P}{R}=Q_{in}(t).
\]

Equivalently, for a nonzero reference pressure P_v, use Q_out=(P-P_v)/R and
\[
C\frac{dP}{dt}+\frac{P-P_v}{R}=Q_{in}(t).
\]
For diastole with Q_in=0, this gives
\[
P(t)-P_v=(P(0)-P_v)e^{-t/(RC)}.
\]

The 1998 *American Journal of Physiology* treatment explicitly derives the flow balance, compliance storage term, resistive outflow, the two-element time-domain equation (its Eq. 5), and the corresponding input impedance. The Parker historical review distinguishes Frank's 1899 model from later developments. The source register also contains BIO-WINDKESSEL-WESTERHOF-2009, a modern review of two- and three-element Windkessel models.

### 1.2 Assumptions and model boundary

The canonical two-element RC form requires:
- one lumped, compliant arterial compartment with spatially uniform pressure;
- linear, constant compliance and peripheral resistance over the modeled interval;
- negligible blood inertance and no explicit wave propagation/reflection;
- a declared downstream/reference pressure (zero only as a simplifying convention);
- a defined inflow Q_in(t), including the systolic/diastolic input schedule.

Frank also considered pressure-dependent compliance/resistance; those nonlinear cases must not be silently mixed with the constant-parameter two-element benchmark. Three-element Windkessel models add characteristic impedance and are model extensions, not merely another name for the same two-element equation.

### Finding and eligibility

This is a credible complete lumped ODE model lead, with a primary historical source identity and equation-level modern derivations. The scalar diastolic exponential is a solution of the ODE under zero inflow, not a second independent equation. Likewise, the frequency-domain impedance is a transform of the same linear model, not an independent entry.

Hold for exact primary-translation page transcription, a frozen constant- versus pressure-dependent compliance choice, reference-pressure convention, input waveform and physiological parameter/range contract. Do not count two-element and three-element models separately without a predeclared structural/family rule.

**Register links:** BIO-WINDKESSEL-FRANK-1899; BIO-WINDKESSEL-WESTERHOF-2009.

## 2. Biology: FitzHugh's 1961 Bonhoeffer–van der Pol (BVP) model

### 2.1 Exact original two-state system

FitzHugh (1961), *Impulses and Physiological States in Theoretical Models of Nerve Membrane*, *Biophysical Journal* 1(6), 445–466, DOI 10.1016/S0006-3495(61)86902-6, explicitly introduces a two-variable Bonhoeffer–van der Pol (BVP) model by generalizing the van der Pol relaxation oscillator. The original paper gives the system as Eqs. (1)–(3):

\[
\dot{x}=c\left(y+x-\frac{x^3}{3}+z\right),
\qquad
\dot{y}=-\frac{x-a+by}{c},
\]

with parameter restrictions

\[
1-\frac{2b}{3}<a<1,\qquad 0<b<1,\qquad b<c^2.
\]

Here x and y are the two state variables associated with excitability and refractoriness; z is stimulus intensity, corresponding to membrane current I in the Hodgkin–Huxley model. In the paper's z-clamp setting, z may be a specified function of time, including step, rectangular-pulse or idealized impulse inputs.

The paper shows the construction from the van der Pol equation and Liénard transformation, then adds the a, b and stimulus terms. It also states the model's intended role: a qualitative, two-state representative of excitable-oscillatory systems, rather than a quantitatively exact fit to every nerve membrane.

### 2.2 Distinction from Hodgkin–Huxley and later FHN forms

FitzHugh explicitly compares the BVP phase-plane model with the four-dimensional Hodgkin–Huxley (HH) model and notes that a suitable projection of HH phase space can produce a similar physiological-state diagram. That does not make the BVP equations an algebraic identity or a one-to-one exact reduction of the full HH system.

For catalogue purposes, transcribe the original 1961 BVP system above. Do not substitute a later textbook FitzHugh–Nagumo parameterization or treat a rescaled/rearranged form as a separate equation. The two coupled ODEs are one system-level unit; nullclines, phase-plane curves, fixed points and impulse responses are analyses/solutions of that system, not additional entries.

### Finding and eligibility

The original paper supplies the exact two-state equations, parameter inequalities, stimulus interpretation and qualitative modeling intent. This is a strong system-level candidate. It belongs to the broad excitable-cell family with HH and Morris–Lecar models, but its two-state cubic/recovery structure is not the same equation as the four-state HH conductance system.

Hold for a deterministic system adapter, stimulus waveform/input contract, initial-state policy, parameter sampling satisfying all three inequalities, scaling/units convention and an explicit family/dependence policy. Do not claim that the model is statistically independent of other excitable-cell candidates merely because its structure differs.

**Register link:** BIO-FITZHUGH-1961.

## 3. Updated screening decisions

| Lead | Source status | Structural assessment | Current decision |
|---|---|---|---|
| Frank 1899 Windkessel | Primary historical paper and 1990 translation identified; modern equation derivations located | Two-element lumped RC ODE; diastolic exponential and impedance are derived forms; three-element model is an extension | Hold for primary-page transcription, exact model variant and input/range contract |
| FitzHugh 1961 BVP | Primary paper and exact Eqs. (1)–(3) located in full text | Coupled two-state nonlinear ODE; related excitable-cell family but not identical to HH | Hold for system adapter, stimulus/initial-state contract and constrained parameter sampling |

## 4. Consequences for Core-295

1. Preserve the full Windkessel ODE and the full two-state BVP system as the equation units. Do not replace them with a single derived observable.
2. Keep source-family membership distinct from algebraic structural equivalence and from statistical independence.
3. Freeze model variants and conventions before generating data: constant versus nonlinear compliance for Windkessel; original 1961 BVP rather than later FHN parameterizations for FitzHugh.
4. Enforce physical/structural constraints in the deterministic generator, including positive R,C and the FitzHugh parameter inequalities.
5. Neither lead is accepted or counted toward the 59-per-domain target by this audit.

## 5. Work not performed

No formal catalogue entry was changed. No source status was upgraded. No candidate was accepted. No script, validator, solver, experiment, workflow, paid compute or live protocol/API call was run.
