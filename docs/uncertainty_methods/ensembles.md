# Ensemble uncertainty methods

## Core idea

An ensemble combines predictions from multiple fitted models. Members may
differ by random initialization, data resampling, architecture, feature
selection, or model family. The spread of member predictions is a measure of
disagreement, which can be a useful uncertainty signal.

For member predictions f_m(x), the ensemble mean is the average across members.
The across-member variance measures disagreement. It is not automatically a
well-calibrated predictive variance: members may share biases, training data,
architecture, or blind spots.

## Candidate designs

- Deep ensembles: independently initialized neural networks.
- Data-resampling ensembles: models fitted on bootstrap/subsampled datasets.
- Heterogeneous ensembles: distinct model families or symbolic hypotheses.
- Snapshot/seed ensembles: useful operationally but potentially highly correlated.

## Assumptions and failure modes

Members should represent meaningful variation. Correlated members can make
spread look deceptively small. All members can extrapolate incorrectly in the
same direction. Ensemble disagreement usually captures model variation, not
all irreducible observation noise. Do not label member standard deviation as a
prediction interval without a defensible noise model and calibration.

## Required outputs and diagnostics

- Member predictions (n_observations × n_members), member count, and failures.
- Ensemble mean, median, standard deviation, and requested empirical quantiles.
- Pairwise/member correlation or diversity diagnostics where useful.
- Optional aleatoric estimate only if each member models it explicitly.
- Training-data and model-family provenance for each member.

## Evaluation plan

Compare mean/median point performance with each member and simple baselines.
Evaluate empirical interval coverage and width only after specifying how
intervals are constructed or calibrated. Test ensembles with shared systematic
bias to ensure the diagnostics do not mistake disagreement for total uncertainty.
Plot member predictions and spread against horizon distance.

## Template

See `hypatiax/tools/uncertainty_methods/templates/ensemble_template.py`.
The template accepts already-fitted members; training an ensemble is an
explicit caller decision, not an implicit side effect of prediction.
