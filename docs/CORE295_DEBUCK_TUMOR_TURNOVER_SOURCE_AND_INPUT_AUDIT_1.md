# Core-295 De Buck tumor-turnover source and input audit 1

Date: 2026-11-12

Candidate: `BIO-TUMOR-TURNOVER-001`

## Primary source and equation

De Buck et al. (2014), “Population pharmacokinetics and pharmacodynamics of BYL719, a phosphoinositide 3-kinase antagonist, in adult patients with advanced solid malignancies,” *British Journal of Clinical Pharmacology* 78(3), 543–555, DOI 10.1111/bcp.12378, PMCID PMC4243905.

The open-access primary article gives the final tumor growth-turnover model as Eq. (9). It defines tumor as the one-dimensional sum of individual tumor diameter measurements; (K_{growth}) is a zero-order tumor growth rate, (K_{deg}) a first-order tumor death rate, (E_{max}) the maximum pharmacodynamic effect, and (IC_{50}) the plasma concentration at 50% of maximum inhibitory effect. Individual predicted BYL719 plasma concentrations from the fitted PK model are supplied as the input function. Each patient's ODE is initialized at that patient's observed baseline tumor-diameter sum.

The source reports:
- (K_{growth}=0.581) cm week(^{-1}), fixed in the final model;
- (E_{max}=1), fixed in the final model;
- (K_{deg}=0.0123) week(^{-1}), estimated;
- (IC_{50}=101) ng mL(^{-1}) in the final parameter table (abstract rounds to 100 ng mL(^{-1})); BSV on (IC_{50}) was 154%;
- 47 patients had evaluable PD data, contributing 146 tumor-size measurements;
- the baseline sum of tumor diameters in the evaluable population ranged 2.4–21.5 cm.

The equation is
\[
\frac{dT}{dt}
=K_{growth}\left(1-\frac{E_{max}C(t)}{C(t)+IC_{50}}\right)
-K_{deg}T.
\]

## Correct model contract

This is an ODE with time as the independent variable, tumor diameter sum as the state/output, and a time-varying external concentration forcing (C(t)). Do not represent C as a static independent scalar sampled independently for each row.

- Time (t): weeks from baseline.
- State/output (T(t)): sum of longest diameters of measurable lesions, cm.
- Forcing input (C(t)): individual predicted BYL719 plasma concentration, ng mL(^{-1}), from the selected PK model and patient dosing history.
- Fixed final-model parameters: (K_{growth}=0.581) cm week(^{-1}), (E_{max}=1).
- Typical final-model estimates: (K_{deg}=0.0123) week(^{-1}), (IC_{50}=101) ng mL(^{-1}). These are population estimates, not universal biological constants.
- Initial condition: (T(0)) is the patient's observed baseline tumor-diameter sum.

The catalogue had the state variable but omitted the dependent output and described C as an independent variable without its time-series contract. Correct the role assignment to independent variables (t,C(t)), state/dependent output (T(t)).

## Scope and limits from the authors

The authors explicitly describe their implementation as empirical and caution that it cannot be generalized beyond the baseline tumor-size range represented in the population (about 2–20 cm). They note a natural untreated-growth boundary at (K_{growth}/K_{deg}), approximately 47 cm, under their fitted parameter values. This theoretical boundary is not a substitute for the authors' empirical generalization warning.

The PK model is a separate linked component. The original paper used a one-compartment disposition model with a transit-compartment absorption model, and also evaluated a lag-time PK alternative. Individual predicted concentrations from the lag-time model were used as the input to Eq. (9) in the final PK-PD analysis. A Core-295 reproduction must select and pin the same PK input convention or explicitly declare a modified input source.

The study enrolled patients with advanced solid malignancies receiving BYL719; it is not a universal tumor model. The authors acknowledge possible confounding of turnover parameters because serial tumor measurements before treatment were unavailable. The large between-subject variability on IC50 further cautions against treating a single population value as a general parameter.

## Structural overlap

The inhibition subexpression (E_{max}C/(C+IC_{50})) has a hyperbolic saturation form related to Michaelis-Menten. That subexpression alone does not establish full-model equivalence: the candidate is a tumor-state ODE with a zero-order growth term, first-order turnover and externally supplied PK forcing. Apply the frozen E0-E5 policy to the complete governing model and the Core-15 Michaelis-Menten exclusion; do not decide solely from the shared subexpression or the tumor application label.

## Catalogue disposition

Correct the ODE variable roles and explicitly represent (C(t)) as a PK-derived forcing function with a patient-specific initial condition. Record the source's fixed/estimated parameter status and empirical baseline-size boundary. Keep candidate proposed and generator pending specialized ODE/PK input contract. Do not create independent concentration samples or claim a generalizable biological law.

## Sources

- De Buck et al. (2014), open-access primary article and Eq. (9): https://pmc.ncbi.nlm.nih.gov/articles/PMC4243905/
- Publisher article page, parameter results and model details: https://bpspubs.onlinelibrary.wiley.com/doi/10.1111/bcp.12378
- PubMed record: https://pubmed.ncbi.nlm.nih.gov/24617631/

No scripts, validators, tests, workflows, live experiments or scientific simulations were run.
