# Core-295 source verification audit 19: De Buck BYL719 tumour-growth turnover PK/PD equation

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** proposed record BIO-TUMOR-TURNOVER-001 and registered primary source De Buck et al. (2014), British Journal of Clinical Pharmacology, DOI 10.1111/bcp.12378.

## 1. Primary source and equation location

De Buck et al. (2014), *Population pharmacokinetics and pharmacodynamics of BYL719, a phosphoinositide 3-kinase antagonist, in adult patients with advanced solid malignancies*, British Journal of Clinical Pharmacology 78(3), 543–555, first published 11 March 2014. The final tumour-growth turnover model is equation 9 in the Population PK–PD analysis section, printed page 547.

The equation is:
[
\frac{dT}{dt}
=K_{growth}\left(1-\frac{E_{max}C}{C+IC_{50}}\right)
-K_{deg}T,
]
where (T) is the one-dimensional sum of longest tumour diameters, (C) is the plasma BYL719 concentration input, (K_{growth}) is a zero-order tumour growth rate, (K_{deg}) is a first-order tumour death rate, (E_{max}) is maximum pharmacodynamic inhibition, and (IC_{50}) is the plasma concentration at half-maximal inhibition. The authors constrained both (K_{growth}) and (K_{deg}) to be positive.

The source states that individual predicted concentrations from the study's (t_{lag}) PK model, using Bayesian post-hoc parameter estimates, were used as the input to equation 9. Each patient's model was initialized from that patient's baseline sum of tumour diameters.

## 2. Model interpretation and validity boundary

This is a drug-exposure-driven turnover ODE:
- the first term is a zero-order growth input reduced by a saturable Emax inhibition function;
- the second term is first-order loss proportional to the tumour-size state;
- concentration (C(t)) is an external PK input, not an independently modelled tumour state;
- the observed tumour state is a one-dimensional RECIST-style sum of lesion diameters, not tumour volume, mass, cell count or a generic tumour burden.

The equation is not a generic tumour growth law. It is a fitted PK/PD model for BYL719 in the studied advanced-solid-malignancy population. The paper reports 60 enrolled patients for PK analysis, 47 with evaluable PD data, 146 tumour-size measurements, and a model-specific drug concentration and parameter regime. The estimated typical (K_{growth}), (K_{deg}), and (IC_{50}) are empirical study estimates, not universal biological constants.

## 3. Structural family and overlap

The complete ODE is one coupled turnover model. Do not count as separate equations:
- the Emax saturation term (E_{max}C/(C+IC_{50}));
- the zero-order growth input;
- the first-order degradation term;
- a steady-state solution or analytic solution for constant concentration;
- the PK concentration input model, unless a separate complete PK system is deliberately selected.

The saturable exposure-response term is related to the broader Emax/Michaelis–Menten family, but the complete state equation combines it with zero-order production and first-order loss. This is structurally different from logistic or Gompertz autonomous growth, but related to other PK/PD turnover models. A family-level rule must decide whether one clinical drug-specific instantiation can count independently of other turnover models in the same PK/PD family.

## 4. Required benchmark contract

Before acceptance, freeze:
- the tumour-state definition as sum of longest lesion diameters and its unit;
- the BYL719 concentration input convention and units;
- (K_{growth}>0), (K_{deg}>0), (0leq E_{max}leq1), and (IC_{50}>0);
- baseline initial condition and treatment/input schedule;
- time unit (the paper reports growth/death rates per week);
- whether the benchmark evaluates this exact drug-specific PK/PD model or a general turnover family;
- valid training and extrapolation ranges grounded in the study, not arbitrary synthetic extrapolation.

A synthetic concentration trajectory must not be sampled independently of the PK assumptions if the intended model is the published PK/PD system. Conversely, if (C(t)) is treated as a prescribed input, that restriction must be explicit.

## 5. Decision

**Disposition:** equation and printed source location verified. Retain as a plausible, structurally distinct PK/PD turnover-model lead, but hold pending the clinical model scope, input trajectory, units, ranges and dependence policy for related turnover models. Do not split it into independent Emax, growth, degradation, steady-state or PK-input entries.

No catalogue record or status was changed. The formal catalogue remains at 128 source records, 19 proposed records and zero accepted records; the sampling frame remains unfrozen.

No experiments, solvers, validators, workflows, paid compute, API calls, clinical data retrieval or model fitting were run. This is source review only.
