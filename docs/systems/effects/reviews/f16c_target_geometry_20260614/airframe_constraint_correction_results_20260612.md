# Airframe Constraint Correction Results - 2026-06-12

R16 starts the correction loop for actual-size receiver priors. It adds a
machine-readable whole-airframe silhouette diagnostic before changing more
component dimensions or placements.

## Outputs

| Artifact | Result |
| --- | --- |
| Constraint report | [airframe_constraint_correction_candidate_20260611.json](review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.json), [CSV](review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.csv) |
| Current latest-placement overview | Retired from the current final-result surface; use [whole_airframe_contour_dashboard.html](review_packets/f16c_20260611/whole_airframe_contour_dashboard.html) for the current visual result |
| Overview packet | [scene.html](review_packets/f16c_20260611/scene.html) |

## Counts

| Measure | Value |
| --- | ---: |
| checked items | `34` |
| receiver priors | `26` |
| held split segments | `8` |
| silhouette exposure items | `14` |
| center-shift reduces exposure | `1` |
| center-shift fully resolves exposure | `0` |
| size-or-shape review required | `13` |
| low-confidence but inside-airframe items | `9` |
| runtime active components | `0` |

## Current Findings

- The report uses shape-aware top/side/front sampling: OBBs use rectangle
  samples; ellipsoid, cylinder cross-section, and capsule projections avoid
  treating their bounding-box corners as geometry.
- `engine_core_afterburner_segment` is the only current item where a center
  shift reduces silhouette exposure without changing size.
- Remaining exposure items mostly require size, shape, or multi-region placement
  review rather than simple center movement. Examples include radar/IFF nose
  equipment, cockpit/INS, center and wing fuel cells, engine/nozzle geometry,
  and inner-wing spar segments.

## Boundary

This is a diagnostic and correction-candidate layer. It does not shrink
dimensions, does not apply center-shift candidates to the prior rules, does not
activate runtime damage components, and does not claim true internal F-16
engineering geometry.
