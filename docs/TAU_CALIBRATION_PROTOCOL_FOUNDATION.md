# Reviewer-facing foundation for training-only τ calibration

**Status:** Approved risk parameters and fixed-sequence selection method; calibration is not yet executable because the calibration equations, category counts, independence unit, candidate grid, and its order have not yet been fixed.  
**Applies to:** Stage 3 LLM boundary-degradation probe and the pure-LLM eligibility decision.  
**Approval date:** 2026-11-11  
**Branch:** `promotion/rerun-code-review`

## 1. Executive statement

We will calibrate the Stage 3 threshold `τ` using a predeclared calibration set that is disjoint from the 15 Core-15 benchmark equations. Calibration may use training data only. The selected `τ` will be frozen before any Core-15 benchmark evaluation and will not be revised using Core-15 outcomes, held-out target labels or scores, or extrapolation results.

The approved operating criteria are:

| Criterion | Approved value | Status and rationale |
|---|---:|---|
| Minimum absolute LLM edge recovery | (R^2_{LLM,edge} \geq 0.99) | Grounded in the manuscript's primary recovery criterion |
| Relative edge-recovery margin | (\delta=0.00) | LLM edge (R^2) must be no worse than ensemble edge (R^2); no unsupported tolerance is introduced |
| Maximum bad-routing risk | (\alpha=0.05) | Explicit, predeclared 5% risk budget; a protocol choice, not a manuscript result |
| Confidence bound | One-sided 95% | Matches the 5% risk budget |
| Minimum calibration size per category | 59 independent equations if zero bad routes are observed for one fixed, pre-specified threshold | Exact one-sided binomial bound for a single test; threshold/category multiplicity can require more |

The implementation convention at the routing boundary is inclusive: (\Delta \leq \tau) is eligible for pure-LLM routing, provided all other gates pass. This equality convention is a project decision, not a boundary rule specified by the manuscript.

## 2. Evidence from the manuscript and repository

The main manuscript identifies (R^2 \geq 0.99) as its primary recovery criterion and (R^2 \geq 0.999999) as a stricter near-exact recovery criterion. It separately defines catastrophic failure as (R^2 < -10). These criteria serve different purposes:

- (0.99) is the approved absolute edge-recovery floor for this calibration protocol.
- (0.999999) remains the manuscript's stricter near-exact reporting criterion; it is not substituted for the calibration floor.
- (-10) remains a catastrophic-failure reporting threshold only. It is far too permissive to serve as the pure-LLM calibration floor.

The manuscript's Stage 3 definition computes the degradation statistic from the LLM-proposed formula on training rows and on the upper 20% of training samples ordered by projection onto the first PCA direction:

[
\Delta = R^2_{LLM,train} - R^2_{LLM,edge}.
]

Stage 3 states that (\Delta>\tau) activates ensemble mode; Stage 5 states that pure LLM requires (\Delta<\tau), leaving equality unspecified. The project has adopted (\Delta\leq\tau) for pure-LLM eligibility.

The manuscript does not supply a numeric (\tau), a calibration dataset, a reproducible calibration estimator, or a statistical risk guarantee for threshold selection. The 5% risk budget, 95% one-sided confidence level, zero-margin comparison, and minimum sample-size rule are therefore explicit protocol decisions rather than claims about the original experiments.

## 3. Define the bad-routing event before calibration

For each eligible calibration unit and each candidate threshold (\tau), define the pure-LLM decision using the same gates and the same Stage 3 statistic intended for evaluation. A **bad route** is a calibration unit for which the candidate rule would permit pure-LLM routing but either approved edge-recovery condition fails:

1. Absolute recovery fails: (R^2_{LLM,edge}<0.99); or
2. Relative recovery fails: (R^2_{LLM,edge}<R^2_{ensemble,edge}), corresponding to the approved zero margin (\delta=0.00).

Equivalently, a permitted pure-LLM route is acceptable only when both

[
R^2_{LLM,edge}\geq 0.99
\quad\text{and}\quad
R^2_{LLM,edge}-R^2_{ensemble,edge}\geq 0.
]

The edge subset, evaluator, handling of invalid/non-finite predictions, and ensemble comparator must be identical and predeclared across calibration units. An invalid or missing score must not be silently dropped or counted as a successful route; it must be handled conservatively as a failed eligibility/acceptance outcome according to the frozen evaluation specification.

This event definition is a proposed operationalization of the approved absolute and relative criteria. Before any calibration run, its implementation must be checked against the actual prediction and scoring interfaces so that the comparator is genuinely available and evaluated on the same edge rows. Do not substitute a different NN-based central-versus-tail probe: the manuscript's Core-15 Stage 3 is an LLM-formula probe on the upper 20% of training rows.

## 4. Statistical foundation for the 59-equation minimum

Let (p) be the probability of a bad route for a fixed, predeclared category and a fixed candidate routing rule. Under independent, identically distributed Bernoulli calibration units, if (n) units are observed and (k) bad routes occur, use a one-sided exact Clopper–Pearson upper confidence bound (U) at confidence level 95%.

For zero observed bad routes ((k=0)), the exact upper bound is

[
U=1-\alpha_c^{1/n},
]

where (\alpha_c=0.05) is the one-sided tail probability (not to be confused with any model blend coefficient). Requiring (U\leq0.05) gives

[
1-0.05^{1/n}\leq0.05
\quad\Longleftrightarrow\quad
n\geq\frac{\log(0.05)}{\log(0.95)}.
]

The smallest integer satisfying this is (n=59). At (n=59), the one-sided upper bound is approximately 0.0495; at (n=58), it is above 0.05. Thus, 59 independent units with zero observed bad routes support the stated 95%-confidence upper risk bound of 5% for **one fixed, pre-specified candidate threshold and one risk claim** under the binomial assumptions.

**The number 59 is conditional, not universal.** If one or more bad routes are observed, the required sample size is larger and must be recalculated using the exact one-sided binomial bound for the observed failure count. Do not retain the 59 minimum as sufficient when (k>0). The operational rule is to require the exact upper bound (U(n,k)\leq0.05); otherwise the category is not certified and pure-LLM routing remains disabled for it.

For a general failure count k, the one-sided Clopper–Pearson upper bound is the (1−δ) quantile of a Beta distribution with parameters (k+1) and (n−k), with usual boundary handling. Equivalently, reject H0:p_bad ≥ ε when the exact one-sided binomial p-value is at most δ. The implementation should use a trusted statistical library or independently tested exact calculation, not a normal approximation.

## 5. Independence, categories, and multiplicity

The binomial guarantee applies to independent calibration units. Counting many algebraic variants, parameterizations, or noisy replicates of the same underlying equation as independent observations would overstate the effective sample size.

Before calibration, document the sampling frame and define the independent unit. Where equations share a generating family, functional template, or source problem, use a defensible grouping strategy (for example, one independent unit per family or a statistically justified cluster-level procedure). If independence cannot be defended, do not claim the simple 59-equation guarantee.

The guarantee is **per category**, not a pooled total across categories. Do not pool categories merely to reach the minimum. Pooling is permissible only if justified in advance by a defensible common-risk assumption and reported as such. Separate per-category guarantees do not imply a simultaneous guarantee that every category is certified; any all-categories claim requires another correction or a valid simultaneous procedure across categories. Seeds, noise levels, and repeated runs of the same equation are not independent trials: count each independent equation (or defensible independent equation family) once. The guarantee applies to the calibration population. Applying it to Core-15 assumes the Core-15 equations are exchangeable with, or otherwise represented by, that predeclared calibration population; this is an assumption, not a theorem.

## 6. Selecting among candidate thresholds: fixed-sequence testing

The approved selection procedure is **fixed-sequence testing**, not Bonferroni over the threshold grid. Before calibration outcomes are examined, declare a finite grid in order from the strictest threshold (smallest \(\tau\), permitting the fewest pure-LLM routes) to the laxest (largest \(\tau\)). The order must be frozen in the manifest. With the routing convention \(\Delta\leq\tau\), this means candidate values are strictly increasing.

For each candidate in that order, test the unsafe-risk null hypothesis

\[
H_{0,j}: p_{\mathrm{bad}}(\tau_j)\geq\varepsilon
\]

against the alternative that the bad-route probability is below \(\varepsilon\), using an exact one-sided binomial test at level \(\delta=0.05\). Proceed to the next, more permissive candidate only if the current null is rejected. Stop at the first candidate that is not certified. The selected threshold is the last candidate that passed. If the strictest candidate does not pass, no threshold is certified and that category remains on ensemble routing. If every candidate passes, the laxest candidate is selected.

This fixed-sequence gatekeeping procedure controls the family-wise probability of falsely certifying one or more unsafe thresholds at \(\delta\), for any finite grid size, provided the tests are valid and the sequence was fixed in advance. To see why, consider the first unsafe candidate in the ordered sequence. Certifying any unsafe candidate requires that this first unsafe candidate pass its level-`δ` test; under its null, that false-pass probability is at most \(\delta\). No Bonferroni division by the number of thresholds is required. The procedure is conservative in search efficiency: a poorly placed early candidate that cannot be certified stops the search, even if later candidates might otherwise have passed. The grid and order are therefore substantive pre-calibration design choices.

For zero observed bad routes, each fixed-sequence test at level \(\delta\) has the minimum sample size

\[
n\geq\left\lceil\frac{\log(\delta)}{\log(1-\varepsilon)}\right\rceil.
\]

At \(\varepsilon=\delta=0.05\), this is 59 independent equations per category, whether the predeclared grid contains 1, 5, or 50 candidates. With observed bad routes, use the exact one-sided binomial test (or equivalent exact Clopper–Pearson upper bound) for the actual \(n,k\); do not rely on the zero-failure minimum. Certification requires the exact upper bound to be no greater than \(\varepsilon\).

For planning with \(\delta=0.05\), the zero-failure minimum varies with the predeclared tolerated bad-route rate:

| Tolerated bad-route rate \(\varepsilon\) | 0.05 | 0.10 | 0.15 | 0.20 | 0.25 |
|---:|---:|---:|---:|---:|---:|
| Minimum independent equations | 59 | 29 | 19 | 14 | 11 |

These are feasibility calculations, not a recommendation to loosen \(\varepsilon\). Count eligible, disjoint, training-only independent calibration equations by category **before** choosing a risk-control procedure or changing \(\varepsilon\). If a category has too few independent equations, options are: (a) leave it on ensemble routing; (b) predeclare a pooled threshold only if a common-risk population assumption is scientifically defensible; or (c) choose a looser \(\varepsilon\) in advance with an explicit scientific justification and disclose it. Do not change \(\varepsilon\) after seeing the counts or outcomes without documenting the protocol deviation. If simultaneous guarantees across categories are required, the category family needs its own error allocation or valid simultaneous procedure; the per-category fixed-sequence guarantee alone does not supply it.

The bad-route event in Section 3—including the absolute edge-`R²` floor, relative margin against the ensemble, edge-row construction, evaluator, and invalid-score handling—must be frozen before calibration. These choices define the Bernoulli outcome and cannot be tuned after seeing calibration results.

## 7. Data separation, freeze, and fail-closed policy

The approved sequence is:

1. Predeclare the calibration population, category membership, independent unit, and equation identities.
2. Confirm that no calibration equation is one of the 15 Core-15 benchmark equations and record a machine-checkable disjointness assertion.
3. Compute the Stage 3 statistic and the predeclared edge-recovery outcomes using training data only.
4. Apply the frozen fixed-sequence exact binomial tests at level \(\delta\), stopping at the first candidate not certified; certify only candidates with bad-route risk below \(\varepsilon\).
5. Record the selected (\tau), calibration data manifest/hash, code and evaluator versions, category, sample count, bad-route count, confidence bound, and selection-procedure details.
6. Freeze the threshold and its provenance before any Core-15 benchmark evaluation.
7. At Core-15 evaluation, apply the frozen threshold without revision. Do not feed Core-15 outcomes, held-out target labels/scores, or extrapolation results back into calibration.

**Fail closed:** if the calibration set is missing, overlaps Core-15, is too small, violates the independence assumptions, has an uncertified risk bound, or lacks a valid fixed-sequence procedure, do not enable pure-LLM routing on the basis of an uncalibrated (\tau). Keep (\tau) unset and use the existing ensemble fallback.

## 8. What this protocol does—and does not—claim

This protocol makes the calibration choices auditable and reviewer-facing. It does not claim that:

- The manuscript originally specified (\alpha=0.05), a 95% one-sided bound, (\delta=0), or (n=59);
- A calibration dataset has already been assembled or checked for independence;
- A numeric (\tau) has been computed or frozen;
- The Core-15 six-gate ablation is implemented;
- Any scientific experiment, calibration run, or live model call has been executed.

The risk parameters and fixed-sequence method are approved, but calibration is not yet runnable until category feasibility, the candidate grid/order, calibration units, and frozen outcome definition are recorded. No experimental results are implied by this document.

## 9. Reviewer-facing concise justification

> We predefine a conservative pure-LLM eligibility rule requiring both an absolute edge-recovery score of (R^2\geq0.99) and non-inferiority to the ensemble edge score (zero relative margin). The absolute floor follows the manuscript's primary recovery criterion; the zero margin avoids introducing an unsupported tolerance. We set the tolerated bad-route probability to \(\varepsilon=0.05\) and the family-wise error rate to \(\delta=0.05\), using fixed-sequence exact binomial testing at level \(\delta\). Under independent equation-level Bernoulli observations, 59 calibration equations with zero observed bad routes are the smallest sample supporting an exact one-sided binomial upper bound no greater than 5% for one fixed, pre-specified threshold. A predeclared strictest-to-laxest fixed sequence controls threshold-grid family-wise error at \(\delta\) without a grid-size penalty; simultaneous claims across categories still require category-level multiplicity control. The minimum also increases when failures occur. Because threshold selection over multiple candidates can invalidate a naïve interval, (\tau) is selected only through the predeclared fixed-sequence exact-binomial procedure. Calibration uses training data from a predeclared equation set disjoint from Core-15, and the resulting threshold is frozen before Core-15 evaluation. If the assumptions or risk bound are not satisfied, the system defaults to ensemble routing rather than claiming an unsupported pure-LLM guarantee.

## 10. Machine-checkable pre-run manifest

The repository now includes `config/tau_calibration_manifest.json` as an intentionally incomplete draft and `scripts/validate_tau_calibration_manifest.py` as a pre-run validator. The validator extracts the current 15 equation names from the Core-15 catalogue in `exp1_ablation.py`, requires the manifest's exclusion list to match that catalogue exactly, rejects any calibration entry whose ID overlaps Core-15, requires a distinct independent-unit identifier within each category, and rejects fields that would import held-out/extrapolation outcomes. It also checks that the approved numerical protocol constants have not drifted. A ready manifest must additionally pin the calibration data-manifest hash, code commit, evaluator version, and per-equation source, canonical-formula, and training-row hashes.

Run the structural check with:

```bash
python scripts/validate_tau_calibration_manifest.py
```

The stricter readiness check is:

```bash
python scripts/validate_tau_calibration_manifest.py --require-ready
```

The current draft is expected to pass structural validation and fail the readiness check because no calibration equations, candidate thresholds, category definition, independence justification, edge-construction specification, or selection-aware procedure have been supplied. This is intentional. The validator does not calculate `τ`, certify the statistical assumptions, read benchmark outcomes, or launch any experiment. Passing the structural check is not evidence that calibration is ready or statistically valid; human review of the sampling frame and selected risk-control method remains necessary.

The validator and regression tests have been added but have **not been executed** in this review session. A subsequent local/CI test run must verify them before they are treated as operational safeguards.

