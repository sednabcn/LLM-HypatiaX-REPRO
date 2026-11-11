# Core-295 candidate discovery batch 17: Biology cardiovascular and muscle mechanics

**Status:** primary-source tracing only. No equation is accepted or counted toward the 59 Biology target.

## 1. Fick principle for cardiac output (1870)

**Primary source:** Adolf Fick, “Ueber die Messung des Blutquantums in den Herzventrikeln,” *Sitzungsberichte der Physikalisch-Medizinischen Gesellschaft zu Würzburg*, Neue Folge 2 (1870), XVI–XVII (also cited as pp. 16–17). A historical facsimile pointer is available [here](https://historyofmedicine.com/id/251).

At steady state, oxygen uptake by the lungs equals blood flow multiplied by the arterial–mixed-venous oxygen-content difference:

\[
\dot Q=
\frac{\dot V_{O_2}}{C_{aO_2}-C_{vO_2}}.
\]

Here \(\dot Q\) is cardiac output, \(\dot V_{O_2}\) oxygen consumption per unit time, and \(C_{aO_2},C_{vO_2}\) arterial and mixed-venous oxygen contents per unit blood volume. The same mass-balance principle can be applied to another indicator when the relevant uptake and concentration difference are measured.

**Boundary:** this is a conservation-of-mass measurement principle under steady-state conditions, not a generic flow equation. Specify oxygen content rather than partial pressure, steady-state oxygen uptake, mixed venous sampling and absence of significant shunt or unmeasured oxygen uptake. Fick's 1855 diffusion law is a separate physical transport relation despite the shared author's name.

## 2. Frank's two-element arterial Windkessel (1899)

**Primary source:** Otto Frank, “Die Grundform des arteriellen Pulses,” *Zeitschrift für Biologie* 37 (1899), 483–526; English translation by Sagawa, Lie & Schaefer (1990), [DOI 10.1016/0022-2828(90)91459-k](https://doi.org/10.1016/0022-2828(90)91459-k). A modern equation history is given in [A brief history of arterial wave mechanics](https://doi.org/10.1007/s11517-009-0440-5).

Frank models the arterial tree as a single compliant compartment with peripheral resistance. In modern two-element notation:

\[
C\frac{dP}{dt}=Q_{in}-\frac{P-P_v}{R},
\]

where \(C\) is arterial compliance, \(R\) peripheral resistance, \(P\) arterial pressure, \(P_v\) downstream/venous pressure and \(Q_{in}\) cardiac inflow. During diastole with closed valves and approximately constant \(P_v\), the pressure excess decays exponentially:

\[
P(t)-P_v=(P_{es}-P_v)e^{-t/(RC)}.
\]

The 1899 paper used its own notation and derived the pressure decay from a compliant arterial compartment and outflow resistance; the modern \(RC\) notation is a later translation.

**Boundary:** the two-element Windkessel is a lumped hemodynamic model. The three-element extension adds characteristic impedance to better represent systolic/wave effects; it is a model extension, not an independent algebraic variant of Frank's original two-element system. Spatial wave propagation is outside the lumped model's validity.

## 3. Hill muscle force–velocity relation (1938)

**Primary source:** A. V. Hill, “The heat of shortening and the dynamic constants of muscle,” *Proceedings of the Royal Society B* 126(843) (1938), 136–195, DOI [10.1098/rspb.1938.0050](https://doi.org/10.1098/rspb.1938.0050). The original paper derives the characteristic relation from excess heat production and mechanical work during isotonic shortening; the equation appears in Part II, around pp. 174–177.

The characteristic force–velocity relation is:

\[
(P+a)(v+b)=(P_0+a)b,
\]

where \(P\) is load, \(v\) shortening velocity, \(P_0\) isometric force, \(a\) has force units and is associated with shortening heat per unit distance, and \(b\) has velocity units and characterizes the load dependence of extra energy liberation.

**Boundary:** the original experiments concern stimulated isolated skeletal muscle under controlled isotonic shortening. The relation is hyperbolic and phenomenological; it should not be assumed to describe all muscle states, eccentric contractions or all physiological conditions. The Hill muscle equation is unrelated to the Hill ligand-binding equation in Batch 14 despite sharing the eponym.

## Source-family and benchmark controls

- Fick cardiac output is an oxygen mass-balance measurement. It is not interchangeable with Fick's diffusion law or a generic concentration-gradient flux law.
- Frank's two-element Windkessel and the modern RC pressure-decay form are one model family. The three-element model adds characteristic impedance and must be treated as a model extension with its own state/input/output definition, not a cosmetic rearrangement.
- Hill's force–velocity curve and its derived power curve \(P v\), maximum-power point and linearized reciprocal forms are linked consequences of one characteristic relation.
- The Fick principle, Windkessel and Hill force–velocity relation are separate physiological source families (cardiac output, arterial hemodynamics, skeletal-muscle mechanics), but sample independence still requires a declared unit and data-generation design.
- The Hill force–velocity equation must not be confused with Hill's cooperative ligand-binding equation; keep distinct source IDs and family labels.

## Acceptance requirements

For Fick, specify oxygen uptake units, oxygen content units, sampling sites and steady-state assumptions. For Windkessel, specify compliance, resistance, venous pressure, inflow waveform, initial pressure and whether two- or three-element model. For Hill muscle mechanics, specify muscle type, temperature, tetanic state, load, shortening regime, isometric force, and units of a and b. Every accepted entry requires a source page, exact transcription and benchmark adapter.

All records remain candidates. No Biology entry is accepted; no experiment or workflow has been run.
