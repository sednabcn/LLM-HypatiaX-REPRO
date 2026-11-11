# Core-295 candidate discovery batch 9: Biology tumor-growth and PK/PD primary equations

**Status:** primary-source tracing and equation-family review only. No equation is accepted or counted toward the 59 Biology target.

## 1. De Buck et al. (2014): clinical tumor-turnover model

**Primary source:** De Buck, S. S. et al., “Population pharmacokinetics and pharmacodynamics of BYL719 …”, *British Journal of Clinical Pharmacology* 78(3), 543–555, DOI [10.1111/bcp.12378](https://doi.org/10.1111/bcp.12378).

The primary article identifies the final tumor-growth turnover model as **Eq. 9**. The publisher's equation image and surrounding text give:

\[
\frac{dT}{dt}
=K_{growth}\left(1-\frac{E_{max}C}{C+IC_{50}}\right)-K_{deg}T.
\]

Here, \(T\) is the sum of longest tumor diameters (a one-dimensional size measure), \(C\) is plasma concentration, \(K_{growth}\) is a zero-order growth rate, \(K_{deg}\) is a first-order tumor-death rate, and \(E_{max}\), \(IC_{50}\) describe concentration-dependent inhibition. The source constrains \(K_{growth}\) and \(K_{deg}\) to be positive. The paper reports units consistent with cm/week for zero-order growth, week⁻¹ for the death rate and ng/mL for concentration/IC50.

**Important boundary:** this is not a generic tumor-volume growth law. The state variable is the sum of longest diameters, and the growth term is inhibited by drug concentration while a first-order loss term acts on tumor size. The formula is a clinical PK/PD turnover model, with the PK concentration profile supplied as an input. It should not be benchmarked as though concentration were an arbitrary independent scalar unless the input-generation and time-alignment contract is explicit.

## 2. Simeoni et al. (2004): exponential-to-linear growth and transit-compartment TGI

**Primary source:** Simeoni, M. et al., “Predictive pharmacokinetic-pharmacodynamic modeling of tumor growth kinetics in xenograft models after administration of anticancer agents”, *Cancer Research* 64(3), 1094–1101, DOI [10.1158/0008-5472.CAN-03-2524](https://doi.org/10.1158/0008-5472.CAN-03-2524).

The primary paper's abstract confirms the core model design: untreated tumors transition from early exponential to later linear growth; drug exposure reduces growth in proportion to proliferating tumor cells; a transit-compartment system represents delayed cell death. A later open comparison prints the natural-growth function and full transit ODE system. For untreated tumor weight \(w(t)\), that comparison gives:

\[
\frac{dw}{dt}
=\frac{\lambda_0 w(t)}
{\left[1+\left(\frac{\lambda_0}{\lambda_1}w(t)\right)^\psi\right]^{1/\psi}},
\qquad w(0)=w_0.
\]

For small \(w\), the denominator approaches one and growth is approximately exponential; for large \(w\), the growth rate approaches the constant \(\lambda_1\), giving an approximately linear phase. The comparison reports \(\psi=20\) for a sharp transition. The full treatment model adds a proliferating compartment, drug-dependent kill and sequential transit compartments; it is a coupled vector ODE system, not one extra scalar formula per compartment.

**Provenance boundary:** use the 2004 paper as the primary model source. The explicit displayed equation above is currently transcribed from the 2020 open comparison, which cites the Simeoni model; exact equation-number/page verification in the primary paper remains outstanding. Do not describe the comparison's equation number as Simeoni's original equation number.

## 3. Tumor growth families in the 2019 review: primary-source tracing still required

The tumor-dynamics review's Table 1 lists:
- Linear growth and linear growth with first-order shrinkage (Eqs. 1–2);
- Exponential growth and exponential growth with first-order shrinkage (Eqs. 3–4);
- Logistic growth (Eq. 5), which is excluded because Logistic Growth is a Core-15 model;
- Gompertz growth (Eqs. 6–7);
- Simeoni-style exponential-to-linear growth (Eq. 8).

The review maps the linear-growth/first-order-shrinkage structure to De Buck et al. and the Simeoni growth structure to Simeoni et al. The review is a discovery index, not the primary acceptance source. Gompertz equations in alternative forms (e.g. \(dT/dt=k_gT\ln(T_{max}/T)\) and \(d\ln T/dt=a-b\ln T\)) require a derivation/equivalence check; they must not be counted separately simply because one is written in log coordinates.

## 4. Source-family and benchmark controls

- De Buck Eq. 9 is a concentration-modulated tumor-turnover relation on a diameter-based state variable. Do not silently substitute tumor volume, mass or cell count.
- Simeoni's natural-growth function and its treatment/transit compartments form one coupled PK/PD source family. The number of transit compartments, parameterization, and algebraic rearrangements are not separate equation families.
- De Buck and Simeoni are distinct primary studies and different tumor-state/PKPD structures, but both belong to the broad oncology tumor-dynamics source cluster. They are not automatically independent statistical units.
- Logistic growth remains explicitly excluded. Do not reintroduce it as a special case, a Gompertz approximation or a reparameterized saturation law.
- If a scalar output is used, preserve the full system's deterministic data-generation contract and specify whether PK concentration is an input, generated state or observed covariate.
- Any accepted benchmark needs exact units, time basis, state definition, positive parameter bounds, treatment concentration range, initial conditions and a valid time horizon.

All equations remain candidates. No Biology entry is accepted, and no experiment or workflow has been run.
