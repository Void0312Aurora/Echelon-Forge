# Sensor / Situation Realism P0 Reference Notes

Status: `2026-05-16` P0 Reference Excerpt.

This document only records the lineage of public methods used by the current P0, and does not serve as a model-grade truth database.

## 1. `SNR -> Pd`

- `Public source support`:
  - Albersheim equation / radar detection literature
  - MathWorks Radar Toolbox public documentation description of detectability / probability of detection
- `This repository P0 approach`:
  - Do not directly implement Marcum Q
  - First compute a normalized `snr_db`
  - Then use a logistic curve to approximate `Pd(SNR, Pfa)`
- `Nature`:
  - Belongs to `engineering approximation`
  - The goal is to restore correct monotonicity and threshold sense, not to reproduce strict detection statistics

## 2. `M-of-N confirm`

- `Public source support`:
  - Common in public textbooks on multi-target tracking and radar track initiation: `2-of-3`, `3-of-4`
  - MathWorks tracking examples also commonly use tentative -> confirmed confirmation window semantics
- `This repository P0 approach`:
  - fighter radar default suggests `2-of-3`
  - Only do single-track confirmation, no complex association
- `Nature`:
  - Belongs to `public engineering practice`
  - Not model-specific parameters

## 3. `alpha-beta filter`

- `Public source support`:
  - The alpha-beta filter is a standard low-order filter in basic target tracking textbooks
  - [kalmanfilter.net](https://kalmanfilter.net/alphabeta.html) provides a popular public explanation
- `This repository P0 approach`:
  - Only do Cartesian position/velocity prediction update
  - Do not output full covariance
- `Nature`:
  - Belongs to `standard public algorithm`
  - Lower precision than Kalman, but sufficient as a P0 skeleton

## 4. `DataLink report`

- `Public source support`:
  - Public materials on Link 16 / tactical datalink generally emphasize that what is shared is track / surveillance report, not raw point plots
- `This repository P0 approach`:
  - Break the pattern of 'directly writing to the receiver's ContactList after sharing a contact'
  - Change to `ReportTrack` style message entering `TrackManager`
- `Nature`:
  - Belongs to `architecture semantic correction`
  - Not a protocol-level high-fidelity implementation

## 5. `Radio line-of-sight formula`

- `Public source support`:
  - Common first-order approximation: `3.57 * (sqrt(h1) + sqrt(h2))`
- `This repository P0 approach`:
  - Keep the existing formula, only continue to use for datalink physical constraints
- `Nature`:
  - Belongs to `public engineering approximation`
  - Not equivalent to full terrain/refraction/electromagnetic propagation modeling
