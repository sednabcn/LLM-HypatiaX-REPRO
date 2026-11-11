# Core-295 source verification audit 65: Basel IRB expected-loss decomposition

**Date:** 2026-11-11  
**Status:** source verification of the author-pool expected-loss candidate; no equation is added to the formal catalogue or counted toward 295.

## 1. Primary standard

Basel Committee on Banking Supervision, *Basel Framework*, CRE35, “IRB approach: treatment of expected losses and provisions,” particularly CRE35.2–CRE35.3.

The framework defines expected loss for non-defaulted corporate, sovereign, bank and retail exposures under the IRB approach as probability of default multiplied by loss-given-default. It defines the expected-loss amount as that expected-loss rate multiplied by exposure at default.

## 2. Formula and units

Let:
- \(PD\) be probability of default over the specified risk horizon;
- \(LGD\) be the fraction of exposure lost conditional on default;
- \(EAD\) be exposure value at the default event.

Then:
\[
EL_{\mathrm{rate}}=PD\cdot LGD,
\qquad
EL_{\mathrm{amount}}=PD\cdot LGD\cdot EAD.
\]
PD and LGD are dimensionless decimals; EAD is a currency amount. The product is an expected currency loss over the specified horizon.

The Basel standard treats defaulted exposures differently in some approaches, using a best estimate of expected loss rather than mechanically applying the non-defaulted PD/LGD expression. The formula is a regulatory credit-risk decomposition, not a complete probability model for PD or LGD.

## 3. Structural classification

This is a standard multiplicative expected-loss decomposition. It is related to, but not the same as, the Merton/Black–Cox structural default models that can supply a PD, or a collateral/liquidation model that can supply an LGD. Those upstream models are not embedded in the EL identity.

Do not count separately:
- \(EL_{\mathrm{rate}}=PD\cdot LGD\);
- \(EL_{\mathrm{amount}}=EL_{\mathrm{rate}}\cdot EAD\);
- rearrangements solving for PD, LGD or EAD;
- alternative horizons or unit conversions.

The expected-loss identity is useful as a common accounting aggregation for DeFi lending pools, but by itself it does not provide a new structural equation family. A DeFi adapter must define EAD at default, the default horizon, collateral realization/auction costs in LGD, and how protocol bad debt and recoveries are recognized.

## 4. Decision

**Disposition:** retain as a source-backed DeFi credit-risk accounting identity and validation check, not as an independent Core-295 structural equation. The Basel source is registered as candidate_reference for provenance; do not add a proposed/accepted equation record. The PD, LGD and EAD components must be modeled as separate input families only where they have independent, defensible sources and sampling units.

No experiments, loss estimates, validators, solvers, workflows, paid compute, API calls, on-chain reads or transactions were run. This is standards-level source review only.
