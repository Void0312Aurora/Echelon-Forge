# R18 Subcomponent Shape Promotion Results

Generated: 2026-06-13

Update: R21 later promoted the accepted latest placements, so the current
shape-placement packet is now an empty queue. The R18 metrics below are retained
as historical evidence. See
[subcomponent_latest_promotion_results_20260613.md](subcomponent_latest_promotion_results_20260613.md).

## Outputs

| Artifact | Path |
| --- | --- |
| Internal prior JSON | [review_packets/f16c_20260611/internal_component_prior_candidate_20260611.json](review_packets/f16c_20260611/internal_component_prior_candidate_20260611.json) |
| Internal prior CSV | [review_packets/f16c_20260611/internal_component_prior_candidate_20260611.csv](review_packets/f16c_20260611/internal_component_prior_candidate_20260611.csv) |
| Cross-region segment JSON | [review_packets/f16c_20260611/cross_region_held_component_segments_20260611.json](review_packets/f16c_20260611/cross_region_held_component_segments_20260611.json) |
| Cross-region segment CSV | [review_packets/f16c_20260611/cross_region_held_component_segments_20260611.csv](review_packets/f16c_20260611/cross_region_held_component_segments_20260611.csv) |
| Airframe constraint JSON | [review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.json](review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.json) |
| Remaining shape-placement JSON | [review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json) |
| Remaining shape-placement views | Retired intermediate shape-placement views; current visual result is [whole_airframe_contour_dashboard.html](review_packets/f16c_20260611/whole_airframe_contour_dashboard.html) |
| Current empty-queue overview | Retired from the current final-result surface |

## Result

R18 promotes the four R17 shape-placement candidates that fully removed
whole-airframe silhouette exposure into review-only prior generation rules.
It does not accept runtime damage geometry.

Promoted prior rules:

- `iff_interrogator`: internal receiver prior changes from an OBB box to a
  rounded-LRU ellipsoid while preserving the nominal public APX-family LRU
  dimensions.
- `inertial_navigation_unit`: internal receiver prior changes from an OBB box
  to a rounded-LRU ellipsoid while preserving nominal LN-260-class dimensions.

Promoted held segment rules:

- `engine_core_afterburner_segment`: held engine segment changes from an
  x-axis cylinder to an x-axis capsule and applies the measured `0.207628 m`
  R17 center-offset candidate.
- `engine_core_hot_section_segment`: held engine segment changes from an
  x-axis cylinder to an ellipsoid.

| Metric | Value |
| --- | ---: |
| Promoted internal receiver priors | 2 |
| Promoted held split segments | 2 |
| Promoted items total | 4 |
| Airframe constraint items | 34 |
| Silhouette exposure items after promotion | 10 |
| Size/shape review items after promotion | 10 |
| Remaining shape-placement candidates | 10 |
| Remaining candidates that reduce exposure | 9 |
| Remaining candidates that fully resolve exposure | 0 |
| Remaining unresolved candidates | 10 |
| Current outside samples after promotion | 56 |
| Candidate outside samples after promotion | 25 |
| Candidate outside sample reduction after promotion | 31 |
| Runtime active components or segments | 0 |

## Remaining Review Items

These items still need better size evidence, tapered/cross-section geometry, or
cross-region centerline placement before any runtime activation:

- `apg68_radar_array`
- `cockpit_crew_station`
- `center_fuselage_fuel_cell`
- `engine_core`
- `afterburner_nozzle`
- `left_wing_fuel_cell`
- `right_wing_fuel_cell`
- `engine_core_forward_compressor_segment`
- `wing_spar_center_left_inner_wing_segment`
- `wing_spar_center_right_inner_wing_segment`

## Boundary

R18 only moves zero-exposure R17 candidates from the design-candidate layer into
the review-only generation rules. Runtime near-fuze projection still uses the
existing activation boundary, and cross-region ownership remains held for
`engine_core` and `wing_spar_center`.
