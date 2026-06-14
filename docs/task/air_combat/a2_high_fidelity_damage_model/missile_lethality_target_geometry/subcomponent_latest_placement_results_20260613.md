# R20 Latest Subcomponent Placement Candidate Results

Generated: 2026-06-13

Update: R21 promoted these latest placements into review-only generation rules,
so the current shape-placement packet is now an empty queue. The R20 metrics
below are retained as historical evidence. See
[subcomponent_latest_promotion_results_20260613.md](subcomponent_latest_promotion_results_20260613.md).

## Outputs

| Artifact | Path |
| --- | --- |
| Candidate JSON | [review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json) |
| Candidate CSV | [review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.csv](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.csv) |
| Review views | Retired intermediate shape-placement views; current visual result is [whole_airframe_contour_dashboard.html](review_packets/f16c_20260611/whole_airframe_contour_dashboard.html) |
| Current empty-queue overview | Retired from the current final-result surface |

## Result

R20 resolves the two R19 leftovers and changes the visual review surface to show
only the latest subcomponent candidate layer. Older current, R17 shape, and R19
centerline geometries remain in JSON/CSV as trace fields, but they are no longer
drawn in the main review image legend.

New R20 latest candidates:

- `apg68_radar_array`: moves the preserved aperture volume to a radome /
  forward-fuselage interface candidate instead of keeping it centered near the
  radome tip.
- `cockpit_crew_station`: moves the preserved crew envelope under the canopy /
  forward-fuselage envelope instead of keeping it on the nose-side placement.

| Metric | Value |
| --- | ---: |
| Latest subcomponent candidates | 10 |
| Latest candidates that fully resolve exposure | 10 |
| Latest candidates still unresolved | 0 |
| Latest outside samples | 0 |
| Reduction versus current exposed shapes | 56 |
| Incremental reduction after R19 | 3 |
| Runtime active components or segments | 0 |

## Visual Legend

- Gray: whole-airframe mesh-derived wireframe silhouette.
- Blue: latest subcomponent candidate.

## Boundary

R20 still does not activate runtime projection or claim true internal
engineering geometry. It only produces the latest review candidate geometry
that clears sampled whole-airframe silhouettes while preserving nominal
dimensions.
