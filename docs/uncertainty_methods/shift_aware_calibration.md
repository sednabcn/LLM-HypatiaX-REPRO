# Distribution-shift-aware calibration

## Core idea

Calibration methods adjust uncertainty estimates using held-out calibration
data. Under distribution shift, ordinary exchangeability-based split conformal
guarantees generally do not apply without additional assumptions. Shift-aware
approaches try to adapt calibration to a specified change in the input
distribution or to local/group structure.

This is a calibration layer, not a standalone uncertainty estimator. It needs
a base predictor or uncertainty estimate and a clearly defined calibration
score.

## Shift settings

- Covariate shift: p(X) changes while p(Y | X) remains stable.
- Label/prior shift: the target marginal changes; methods and assumptions differ.
- Concept shift: p(Y | X) changes. Covariate reweighting alone cannot generally
  repair this.
- Local/group shift: calibration may differ across known groups or regions.
- Extrapolation/support failure: test inputs lie outside calibration support;
  no weighting trick can recover missing information without stronger
  structural assumptions.

## Candidate techniques

- Weighted conformal: reweight calibration scores using density ratios under
  covariate-shift assumptions.
- Local/Mondrian conformal: calibrate within groups or neighborhoods.
- Adaptive/online conformal: update calibration sequentially under a specified
  protocol; dependence and adaptivity assumptions must be stated.
- Shift detection: diagnose changes in feature distributions or support. A
  detector is diagnostic, not a coverage guarantee.

## Required diagnostics

- Definition and evidence for the assumed shift type.
- Calibration and evaluation support overlap.
- Importance-weight distribution, clipping policy, and effective sample size.
- Group/local calibration sample counts.
- Shift detector statistic, threshold, false-positive behavior, and drift.
- Coverage and width by group, distance, and shift severity.
- Explicit status when support is insufficient; do not extrapolate calibration
  weights beyond observed support silently.

## Evaluation plan

Construct controlled synthetic covariate shift where p(Y | X) is held fixed,
then separately test concept shift where it changes. Verify weighted methods
under their intended assumptions and show degradation when assumptions fail.
Include support-disjoint test regions to ensure the system reports unsupported
calibration rather than claiming guaranteed coverage.

## Guarantee language

Ordinary split conformal has a finite-sample marginal guarantee under
exchangeability. Weighted/local variants have method-specific assumptions and
may offer only approximate or restricted guarantees. No method in this
repository should claim distribution-free coverage under arbitrary
extrapolation. Report extra-domain coverage as empirical coverage on the
tested points, with support and assumption diagnostics.

## Template

See `hypatiax/tools/uncertainty_methods/templates/shift_aware_template.py`.
