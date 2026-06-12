# R19 Subcomponent Centerline Placement Candidate Results

Generated: 2026-06-13

Update: R20 later resolved the two R19 leftovers and R21 promoted the accepted
latest placements into review-only generation rules. The current packet is now
an empty shape-placement queue; the R19 metrics below are retained as
historical evidence. See
[subcomponent_latest_promotion_results_20260613.md](subcomponent_latest_promotion_results_20260613.md).

## Outputs

| Artifact | Path |
| --- | --- |
| Candidate JSON | [review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json) |
| Candidate CSV | [review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.csv](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.csv) |
| Review views | [review_packets/f16c_20260611/subcomponent_shape_placement_views/index.html](review_packets/f16c_20260611/subcomponent_shape_placement_views/index.html) |
| Current empty-queue overview | [review_packets/f16c_20260611/subcomponent_shape_placement_views/overview_latest_triptych.svg](review_packets/f16c_20260611/subcomponent_shape_placement_views/overview_latest_triptych.svg) |

## Result

R19 adds a local centerline placement candidate for each of the `10` remaining
R18 shape-placement review items. It preserves nominal dimensions and the R17
candidate shape family, then applies a bounded centerline offset discovered by
the local silhouette search. The new centerline candidates are review-only and
are not runtime damage components.

| Metric | Value |
| --- | ---: |
| Remaining R18 shape-placement items | 10 |
| R19 centerline candidates | 10 |
| Nominal dimensions preserved | 10 |
| Centerline candidates that reduce exposure | 10 |
| Centerline candidates that fully resolve exposure | 8 |
| Centerline candidates still unresolved | 2 |
| Shape-candidate outside samples before R19 | 25 |
| Centerline-candidate outside samples after R19 | 3 |
| Incremental outside-sample reduction from R19 | 22 |
| Reduction versus current exposed shapes | 53 |
| Runtime active components or segments | 0 |

Centerline candidates that clear the sampled whole-airframe silhouettes:

- `center_fuselage_fuel_cell`
- `engine_core`
- `afterburner_nozzle`
- `left_wing_fuel_cell`
- `right_wing_fuel_cell`
- `engine_core_forward_compressor_segment`
- `wing_spar_center_left_inner_wing_segment`
- `wing_spar_center_right_inner_wing_segment`

Still unresolved after R19:

- `apg68_radar_array`: `2 -> 1` outside samples after the centerline candidate; needs a radome/radar-aperture cross-section model.
- `cockpit_crew_station`: `5 -> 2` outside samples after the centerline candidate; needs a canopy plus forward-fuselage crew-envelope model.

## Visual Legend

- Gray: whole-airframe mesh-derived wireframe silhouette.
- Red: current exposed shape.
- Amber or green: R17 shape candidate.
- Cyan: R19 centerline candidate that clears sampled exposure.
- Purple: R19 centerline candidate that still has sampled exposure.

## Boundary

R19 does not shrink nominal dimensions, does not claim true internal engineering
geometry, and does not activate runtime projection. The `8` zero-exposure
centerline candidates still need semantic review before being promoted to prior
or held-segment generation rules.
