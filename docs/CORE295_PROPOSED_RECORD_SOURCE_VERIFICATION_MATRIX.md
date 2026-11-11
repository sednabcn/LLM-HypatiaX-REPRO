# Core-295 proposed-record source-verification coverage matrix

**Date:** 2026-11-11  
**Scope:** all 19 currently proposed equation records in `config/core295_catalogue.json`. This is a navigation and review-status document, not a catalogue decision. It does not change record status, source counts, accepted counts or sampling-frame state.

## 1. Record-by-record coverage

| Proposed record | Domain | Audit | Source evidence | Current disposition / principal blocker |
|---|---|---:|---|---|
| CHEM-HENRY-001 | Chemistry | 20 | OpenStax modern Henry relation and coefficient units | Held; name gas/solvent, temperature and ranges. Cross-domain linear-proportionality policy. |
| CHEM-LANGMUIR-001 | Chemistry | 25 | Langmuir 1918 primary Eq. (8) coverage and Eq. (9) adsorbed amount | Held; same rational saturation form as MM/Hill-one; Core-15 cross-domain exclusion ruling and surface/range contract. |
| CHEM-MARCUS-001 | Chemistry | 18 | Marcus 1956 primary source role plus IUPAC classical barrier | Held; collision-frequency vs Eyring prefactor choice and Arrhenius/generic rate-law structural-overlap ruling. |
| BIO-HILL-MUSCLE-001 | Biology | 21 | Hill 1938 original PDF, Eq. (2) at printed p. 162 | Held; correct source page metadata and freeze muscle preparation, temperature, force/velocity convention and ranges. Not Hill ligand binding. |
| PHYS-POISEUILLE-001 | Physics | 22 | OpenStax University Physics 1 §14.7, Eq. 14.19 | Held; physically constrained Reynolds-number, geometry and fluid-property generator; distinguish modern viscosity-explicit form from original historical lineage. |
| PHYS-PLANCK-SPECTRUM-001 | Physics | 21 | Planck 1901 original Eq. (13) plus isotropic (c/4) conversion | Held; explicitly use spectral exitance (M_\lambda), not ambiguous (I_\lambda); freeze wavelength/temperature range and output convention. |
| PHYS-THIN-LENS-001 | Physics | 22 | OpenStax University Physics 3 §2.4, Eq. 2.19 and sign conventions | Held; signed object/image/focal-length domain, exclude (d_o=f); lens-maker relation remains same optics family. |
| AMM-BALANCER-WEIGHTED-001 | DeFi AMM | 24 | Official weighted-math docs and fetched V2 WeightedMath code | Held; immutable implementation commit, three-token adapter, token scaling, weight sampling and fixed-point rounding. Equal two-token weights reduce to excluded CP. |
| RISK-MORPHO-LIF-001 | DeFi Risk | 11 | Official docs and pinned Morpho Blue implementation | Held; full LLTV/unit/oracle/share/rounding adapter and family dependence with other liquidation incentives. |
| RISK-EULER-AUCTION-001 | DeFi Risk | 13 | Official docs and pinned EVK Liquidation.sol | Held; full risk-adjusted collateral valuation, unit, oracle and rounding contract; compare in same liquidation-incentive family as Morpho. |
| RISK-COMPOUND-BORROW-KINK-001 | DeFi Risk | 11 | Official Compound III docs and pinned Comet implementation | Held; exact market parameters and per-second scale; family dependence with Aave-style utilization-kink curves. |
| AMM-DODO-PMM-BASE-SHORTAGE-001 | DeFi AMM | 8 | Official PMM math docs and pinned DODO V2 code | Held; exact pool/version, parameter domain, fixed-point/rounding and state-transition adapter. |
| CHEM-RAOULT-VAPOR-001 | Chemistry | 20 | OpenStax Chemistry 2e ideal-solution equation | Held; original 1887 equation-page transcription and structural comparison with Henry's same bare proportionality form. |
| BIO-FICK-CARDIAC-OUTPUT-001 | Biology | 23 | Fick 1870 original report; modern equation is mass-balance transcription | Held; define steady-state/system boundary, oxygen-content units and physiological ranges. Distinct from Fick diffusion law. |
| RISK-UNISWAP-V3-GEOMETRIC-TWAP-001 | DeFi Risk | 10 | Official Uniswap v3 oracle docs and pinned OracleLibrary | Held; averaging-estimand policy, token orientation/decimals, tick floor and time-window contract. Same broad oracle family as v2. |
| RISK-UNISWAP-V2-ARITHMETIC-TWAP-001 | DeFi Risk | 10 | Official Uniswap v2 oracle docs and pinned periphery code | Held; averaging-estimand policy, orientation, UQ112x112, timestamp wrap and window contract. Same broad oracle family as v3. |
| CHEM-FICK-FLUX-001 | Chemistry | 26 | Fick 1855 original p. 66 local transfer relation | Held; cross-domain linear-gradient transport equivalence with Fourier/Ohm must be resolved; do not split first law/PDE. |
| CHEM-BEER-LAMBERT-001 | Chemistry | 20 | IUPAC modern decadic Beer–Lambert expression | Held; original Beer 1852 equation-page transcription, wavelength/species and concentration/path range. One family with Lambert/absorbance/transmission forms. |
| BIO-TUMOR-TURNOVER-001 | Biology | 19 | De Buck et al. 2014 primary Eq. 9, printed p. 547 | Held; drug-specific PK input, tumour-diameter state, time units, clinical range and turnover-family dependence. |

## 2. Cross-record structural decisions still required

The source checks reveal several policy decisions that affect more than one domain:

1. **Same algebra, different physical mechanism:** Henry and Raoult are both linear proportionalities but represent different equilibria. Langmuir, Michaelis–Menten and Hill-one occupancy share a rational saturation form. Fick, Fourier and Ohm share linear-gradient constitutive transport form. Marcus remains an activated exponential but has a quadratic driving-force barrier.
2. **One family, different estimands/mechanisms:** Uniswap v2 arithmetic TWAP and v3 geometric TWAP are different averaging estimands in one oracle family. Morpho LIF and Euler health-dependent discount are distinct incentive functions in one liquidation family. Compound III borrow kink is a utilization-rate family member, not an independent market merely because the protocol differs.
3. **Complete systems versus components:** the BYL719 tumour model is one PK/PD turnover ODE; Fick cardiac output is one mass-balance measurement relation; AMM invariant helper functions, swap equations and rounding routines are not automatically additional equations.
4. **Historical source versus modern adapter:** Planck's original equation is spectral energy density and the proposed spectral exitance requires the isotropic (c/4) conversion; Fick 1870 states cardiac-output measurement in prose; Fick 1855 gives a local transfer relation; Poiseuille's modern viscosity-explicit expression has later derivation lineage.

## 3. Common acceptance gates

No proposed record is accepted until its source review is accompanied by:
- a stable, unambiguous equation transcription and source/version citation;
- a declared equation output and complete variable/unit contract;
- physically valid train and extrapolation ranges, including coupled constraints;
- a deterministic parameter/data generator with domain-specific validity checks;
- a family-level and cross-domain structural-equivalence ruling;
- a declared statistical independent unit and source-family clustering;
- for protocol models, an immutable implementation commit and exact fixed-point/rounding/state-transition adapter.

Source verification is not scientific acceptance, and mathematical distinctness is not statistical independence.

## 4. Formal catalogue status

At the time of this matrix:
- source records: **128**;
- proposed equation records: **19**;
- accepted equation records: **0**;
- sampling frame: **not frozen**.

No experiment, validator, solver, workflow, paid compute, live API/protocol call, on-chain read or transaction was run for this matrix. No catalogue record status was changed.
