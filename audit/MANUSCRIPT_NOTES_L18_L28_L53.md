# Manuscript actions that follow from L18, L28 and L53 (decided 2026-11-03 / 2026-11-07)

Text-only; no code or data needed. Locations are those named in the 13 Oct submission-blocker report.

## L18 / L28 -- instability suite deferred (report item A2)
The instability suite is not run in this study. Remove or qualify every statement that depends on it:
- Main Section 1 (run-to-run instability); Section 2.1 ("30 independent runs per task"); Section 2.2
  ("first to quantify LLM instability"); Section 7.4 Stage 2 ("strongly predictive of II > 0.05");
  Section 9.2 ("All 30 independent stochastic runs"); Section 11.4; Section 11.5 (the
  "instability-extrapolation correlation"); Section 11.6 principle 3.
- Delete the labels "Regime A/B/C" (Regime C is never defined) and the GaussianCDF "proximate cause".
- Section 10.10 already says no multi-run Instability Index is reported; make the rest consistent with it.

## L53 -- no held-out OOD score for M4, Pure LLM, NN, System 3 (report items A1, B2)
- Report extrapolation / OOD results for HDS (HybridDiscoverySystem v50_2) and PySR only.
- State that M4, Pure LLM, ImprovedNN and System 3 were not scored on the far region.
- Do not claim "robust" or "best" extrapolation for any method outside that pair.

## Also disclose (from the ledger, no code change)
- L39: the Feynman-domain guard forces the LLM path (force_llm) for five domains.
- L06: the headline number is in-sample unless HYPATIAX_HOLDOUT=1 was set; label it, and report the
  held-out llm / nn / blend R^2 as the primary figure after the rerun.
- Two sampling settings: engine and CI use temperature 0.25; DeFi benchmark direct calls use 0.0;
  PureLLMBaseline sends no temperature under SDK >= 1.0 (report as "API default").

## L45 - far-extrapolation regime is a 4x rescaling of near
`generate_extrap_data` draws "near" from 1.0-1.5x and "far" from 4.0-6.0x the training
maximum with the same RNG seed, so X_far = 4 * X_near exactly. For a fitted law with the
same homogeneity degree as the target (power laws, ratio-dependent functions), R2 is
identical in both regimes and RMSE scales by 4^k (observed ratios 1, 0.25, 4, 16, 64, 2.83).
In run 42483985513, 23 of 45 arm-rows show identical finite near/far R2: 14 non-saturated
rows across 7 of the 15 equations, and 9 saturated at 1.0. For those equations far is not
independent evidence; it only separates models that are not scale-equivariant.
