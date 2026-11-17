# Training-Based Extrapolation Potential Analysis

## 1. Purpose and scope

This guide defines a training-only analysis for describing the *potential* of the six Exp2 methods to extrapolate beyond their observed training domain.

The analysis uses training artifacts and the known scientific structure of the benchmark equations. It does **not** calculate far-region predictions, far-region R², far-region RMSE, or any other score that requires extrapolation targets.

The central distinction is:

- **Training-based extrapolation potential:** evidence in the learned representation that makes extrapolation more or less plausible.
- **Empirical extrapolation performance:** measured agreement between predictions and ground truth outside the training domain.

Training-only evidence can support a reasoned hypothesis about extrapolation. It cannot establish actual out-of-domain accuracy. Reports must preserve this distinction and must not present a potential assessment as a substitute for empirical evaluation.

This is a documentation and analysis protocol. It does not prescribe launching experiments, fitting models, calling an LLM, or changing the existing benchmark workflow.

## 2. Research questions

For each method and equation, the training-only analysis should answer:

1. Did the method recover the known physical or mathematical structure?
2. Is the learned representation simpler than, or needlessly more complicated than, the reference law?
3. Is the learned relationship dimensionally and physically admissible?
4. Are fitted parameters and discovered structures stable across repeated training runs?
5. Do training residuals indicate systematic structure that the model has not captured?
6. What evidence supports or weakens the hypothesis that the learned model will remain meaningful outside the training range?

The analysis must identify unavailable evidence explicitly. Missing formulas, inaccessible parameters, or absent repeated runs should be reported as **not assessable**, not silently treated as a failure or success.

## 3. Evidence dimensions

Assess each dimension independently. Do not collapse them into one unqualified score.

### 3.1 Functional-form recovery

Compare the learned equation or model structure with the reference scientific relationship.

For the three Feynman examples:

| Equation | Reference relationship | Structural properties to inspect |
|---|---|---|
| Newtonian gravitational force | $F = G m_1 m_2 / r^2$ | Linear dependence on each mass, inverse-square dependence on separation, symmetry under exchanging the masses |
| Kinetic energy | $KE = \frac{1}{2}mv^2$ | Linear dependence on mass, quadratic dependence on speed, non-negative energy for non-negative mass |
| Reduced mass | $\mu = \frac{m_1m_2}{m_1+m_2}$ | Symmetry under exchanging masses, positive value for positive masses, correct limiting behaviour |

Record separately:
- exact recovery;
- structurally equivalent recovery (algebraically different but equivalent);
- partial recovery (some dependencies are correct);
- non-recovery;
- not assessable (for example, a black-box predictor with no interpretable representation).

Numerical coefficient agreement should account for units, feature transformations, and the physical constants used by the benchmark. Do not call an equation equivalent merely because it fits the observed training rows.

### 3.2 Model and expression complexity

For symbolic expressions, record reproducible complexity measures such as:
- expression-tree node count;
- number of operators and distinct operator types;
- number of free constants;
- nesting depth;
- presence of unconstrained fractional or negative powers;
- number of additive correction terms.

For neural and composite models, record relevant architecture size, trainable parameter count, and the structure of any symbolic base and learned residual/correction.

Complexity is a risk indicator, not a verdict. A complex expression can be justified by the physics, while a short expression can still be wrong. Compare complexity only within clearly defined representation families or report the raw measures without ranking unlike models.

### 3.3 Dimensional and physical consistency

Where units and feature semantics are known, check:
- dimensional homogeneity of every additive term;
- units of constants and outputs;
- expected sign and positivity constraints;
- symmetries and invariances;
- limiting behaviour implied by the physical law;
- domain restrictions for division, roots, logarithms, and powers.

For black-box methods, perform only checks supported by their documented input/output contract and available training artifacts. If internal structure is inaccessible, mark structural checks as not assessable rather than inferring correctness from a low training loss.

### 3.4 Parameter and structure stability

Where multiple training runs already exist, compare:
- discovered expression structure or equivalence class;
- fitted constants after accounting for units and equivalent parameterizations;
- selected features and transformations;
- neural initialization sensitivity;
- residual-correction magnitude and shape;
- method availability or failure frequency.

Use the same training protocol when comparing runs. Report the number of runs, seeds, and whether data splits were held fixed. One run cannot establish stability; mark it as not assessed.

For symbolic expressions, compare canonicalized or algebraically equivalent forms where possible. Literal string equality is not a reliable measure of structural stability.

### 3.5 Training residual diagnostics

Use residuals on the exact training rows used to fit the final predictor. If a separate validation subset is drawn from within the training domain, report it separately as in-domain validation; it is not extrapolation evidence.

Inspect:
- residuals against each input feature;
- residuals against fitted values;
- residual magnitude across bins within the training domain;
- systematic curvature, trends, heteroscedasticity, or clusters;
- residual autocorrelation where observations have a meaningful order;
- residual behaviour of the base model versus the final corrected predictor.

A residual pattern may indicate a misspecified functional form or a missing feature. Random-looking residuals are useful evidence of in-domain fit, but do not prove extrapolation validity.

### 3.6 Training-domain coverage and feature dependence

Document the training range, units, transformations, and sampling density for every input feature. Identify which features are coupled by the data-generation process.

For multivariate equations, inspect each feature's learned dependence separately. A model trained on variation in one feature may not have learned the correct dependence on another feature. A single split or a single extrapolation direction cannot support a general claim about all directions.

Training-only feature perturbations must remain inside the observed training domain. They can help diagnose local sensitivity but must not be described as out-of-domain tests.

## 4. Method-specific interpretation

The following descriptions identify what evidence to inspect. They are not fixed rankings; the actual assessment must be based on artifacts produced by the specific method run.

### 4.1 PureLLM Baseline

Inspect the generated equation, reasoning trace if retained, constants, units, and consistency across independent prompts or runs.

Positive evidence includes recovery of the reference law, correct units and limiting behaviour, and stable equations across runs. A plausible explanation or a formula that matches a few training examples is not sufficient by itself.

If the method only emits predictions and no inspectable equation, functional-form recovery is not assessable.

### 4.2 ImprovedNN

Inspect architecture, feature preprocessing, regularization, training and in-domain validation learning curves, initialization sensitivity, and residual patterns.

A small training loss demonstrates fit to the training data, not physical-law recovery. Without explicit physical constraints or a validated interpretable representation, the neural network's behaviour outside the observed range remains weakly identified by training evidence alone.

Record whether preprocessing is included in the retained predictor and whether any validation rows were excluded from fitting.

### 4.3 EnhancedHybridSystemDeFi

Inspect the base physical/symbolic predictor and the learned residual correction as separate components, then inspect the final composed predictor.

Positive evidence includes a physically correct base law, a small and stable correction, and residuals without systematic structure. A large correction, a correction that dominates the base, or an unavailable/unverified base predictor weakens the physical interpretation.

Do not assess the base formula alone when the final predictor includes an accepted residual correction.

### 4.4 HybridSystemLLMNN

Inspect the LLM-derived base structure, neural correction, preprocessing, and final composition.

Assess whether the base equation has the right dependencies and whether the neural correction is small, stable, and supported by residual patterns. A flexible neural correction may improve training fit while weakening the guarantee that the final predictor preserves the physical law.

The final composed predictor, not an isolated base formula, is the object of assessment.

### 4.5 SymbolicEngineWithLLM

Inspect the discovered expression, operator set, constants, dimensional consistency, complexity, and repeated-run recovery.

A compact expression equivalent to the reference law is strong structural evidence. An expression with arbitrary exponents, nested transformations, or many fitted constants may be a local approximation even when training residuals are small.

Record search configuration and resource limits. A low-budget search outcome should not be interpreted as evidence that the method cannot discover a better expression.

### 4.6 HybridDiscoverySystem

Inspect the final discovered expression and any learned or optimized components, including the search configuration and repeated-run variability.

Pay particular attention to expression complexity, arbitrary fractional powers, constants that compensate for the sampled domain, and whether the expression preserves known symmetries and limiting behaviour.

Compare the discovered expression with simpler physically valid candidates. A complex expression with a small training residual should be described as a possible overfit unless independent structural evidence supports it.

## 5. Reporting rubric

Use qualitative labels per evidence dimension:

| Label | Meaning |
|---|---|
| Strong evidence | Direct, reproducible evidence supports the property being assessed |
| Partial evidence | Some relevant properties are supported, but important mismatches or gaps remain |
| Weak evidence | Available evidence contradicts the property or shows substantial unresolved problems |
| Not assessable | Required artifacts or repeated observations are unavailable |

Then provide an overall **training-based extrapolation potential** classification:

- **Higher potential:** the final predictor recovers the relevant physical structure, is dimensionally/physically consistent, has justified complexity, and has stable training evidence.
- **Moderate potential:** some structural evidence is favourable, but there are material gaps such as partial law recovery, limited stability evidence, or unresolved residual structure.
- **Lower potential:** the learned representation conflicts with known physical structure, contains unexplained complexity, or has substantial systematic training residuals.
- **Undetermined:** artifacts are insufficient to make a defensible assessment.

These labels describe the strength of the training-based rationale, not measured extrapolation accuracy. The report should include the evidence and caveats behind every label. Do not compute a weighted aggregate unless weights and decision rules are specified and justified in advance.

## 6. Per-method, per-equation report template

Create one record for each of the 18 method–equation combinations.

| Field | Required content |
|---|---|
| Method and equation | Exact method name and target equation |
| Training data scope | Row count, feature ranges, units, transformations, split identifier |
| Final predictor | Formula, architecture, or composed predictor identifier |
| Functional-form recovery | Exact / equivalent / partial / not recovered / not assessable |
| Complexity | Raw measures appropriate to the model family |
| Dimensional consistency | Pass / partial / fail / not assessable, with rationale |
| Physical constraints | Checks performed and outcomes |
| Stability | Runs/seeds examined and observed consistency |
| Residual diagnostics | Patterns and plots/statistics derived only from training rows |
| Evidence gaps | Missing artifacts or checks |
| Potential classification | Higher / moderate / lower / undetermined |
| Rationale | Concise evidence-linked explanation |

For a six-method comparison, present the 18 records in a matrix and retain the per-record rationale. Do not rank methods solely by their training loss.

## 7. Separation from empirical extrapolation evaluation

Maintain two separate result tracks:

**Track A — training-based potential**
- Uses training artifacts and, where clearly labelled, in-domain validation artifacts.
- Examines physical structure, complexity, consistency, stability, and training residuals.
- Does not generate or score far-region predictions.
- Does not report far-region R², RMSE, coverage, or claims of demonstrated extrapolation accuracy.

**Track B — empirical extrapolation**
- Uses held-out inputs outside the training domain and their ground truth.
- Evaluates actual predictions with appropriate metrics and uncertainty diagnostics.
- Reports feature-wise and joint extrapolation directions and distances.
- Must retain prediction/target provenance and row scopes for independent verification.

The tracks may be compared in a later scientific analysis: does training-based potential agree with measured extrapolation? Such a comparison must not retroactively use Track B outcomes to assign Track A labels.

## 8. Recommended application to the three Feynman equations

For each equation, assess the dependencies independently:

- **Newtonian gravity:** mass-one dependence, mass-two dependence, inverse-square separation dependence, mass-exchange symmetry, and units of the gravitational constant.
- **Kinetic energy:** linear mass dependence, quadratic speed dependence, non-negative energy, and units.
- **Reduced mass:** symmetry in the two masses, positivity, boundedness relative to the component masses, and limiting behaviour when one mass becomes much larger than the other.

For multivariate training data, record whether each dependency is identifiable from the sampled combinations. Correlated or insufficiently varied inputs can make individual effects impossible to distinguish from training evidence.

## 9. Limitations and claims discipline

1. No training-only diagnostic proves performance outside the observed domain.
2. Correct functional form is strong theoretical evidence, but implementation errors, units, feature transformations, and domain restrictions can still invalidate predictions.
3. Low training error and random-looking training residuals do not guarantee extrapolation.
4. In-domain validation is not extrapolation validation.
5. Repeated seeds on the same training range measure algorithmic stability, not robustness to arbitrary domain shift.
6. If a method exposes no interpretable structure, do not invent a physical explanation for its predictions.
7. A poor empirical extrapolation result can falsify a favourable training-based hypothesis; it should not be hidden or rewritten as a training-only success.
8. All conclusions must identify the exact final predictor, including preprocessing and accepted correction components.

## 10. Implementation boundary

This document specifies an analysis and reporting protocol only. It does not add a training-only evaluator, change the six method implementations, fit models, launch workers, run benchmarks, generate predictions, or call an LLM. Any future implementation should consume already-produced training artifacts and must enforce a clear boundary preventing access to far-region targets or metrics during Track A analysis.
