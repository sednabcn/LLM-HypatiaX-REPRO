# Core-295 proposed-record audit 1: source attribution and formula representation

**Status:** documentation and proposed-record correction only. No equation is accepted, no benchmark ranges or generators are approved, and no experiment or validator was run.

## Marcus outer-sphere electron-transfer record

The prior `CHEM-MARCUS-001` draft combined the Marcus activation-barrier expression with a transition-state prefactor `kappaET*kB*T/h`. The cited Marcus (1956) Part I primary-source abstract describes the rate as the solution collision number multiplied by the activated-state Boltzmann factor, not that Eyring-style prefactor. The manifest now uses a collision-frequency symbol `Z` in the rate expression.

The classical parabolic barrier expression
`DeltaG_dagger=(lambda+DeltaG0)^2/(4lambda)`
is retained as a modern Marcus parameterization, but is explicitly marked for separate source and assumption verification. It must not be represented as a verbatim transcription from Marcus (1956) without checking the original paper's notation and derivation.

**Remaining acceptance blocker:** the exponential activated-rate form overlaps structurally with the excluded Arrhenius/generic rate-law families. A distinct electron-transfer mechanism does not by itself establish structural distinctness. The record remains `proposed`.

Primary source: Marcus, R. A. (1956), “On the Theory of Oxidation-Reduction Reactions Involving Electron Transfer. I,” *Journal of Chemical Physics* 24(5), 966–978, DOI 10.1063/1.1742723. Publisher metadata and the primary-source abstract were checked; the exact equation/page transcription remains outstanding.

## LaTeX representation corrections

- `CHEM-LANGMUIR-001`: removed doubled backslashes from the stored LaTeX command sequence.
- `CHEM-MARCUS-001`: corrected the LaTeX command sequence and aligned the displayed rate expression with the corrected collision-frequency prefactor.
- These are serialization/representation corrections only; they do not add or split equation records.

## Other primary-source caveats retained

- `PHYS-PLANCK-SPECTRUM-001` uses the modern wavelength spectral-intensity form from OpenStax. Planck's 1901 original presentation uses its own spectral-density conventions; do not claim the modern wavelength formula is a verbatim original transcription.
- `CHEM-BEER-LAMBERT-001` uses the IUPAC modern decadic spectral-power relation. Beer (1852) is historical lineage only until the original equation page is directly verified.
- `BIO-TUMOR-TURNOVER-001` remains blocked by the embedded hyperbolic Emax/IC50 saturation term's overlap with the excluded Michaelis–Menten family.
- `CHEM-FICK-FLUX-001` remains blocked pending cross-domain structural comparison with Fourier heat flux and Ohm transport forms.

## Current catalogue state

The manifest remains `draft`, with 19 proposed records and zero accepted entries. All train/extrapolation ranges and deterministic generator contracts remain pending. Source records remain provenance leads, not accepted equations.

No scientific experiment, live API call, repository validator, or GitHub Actions workflow was run.
