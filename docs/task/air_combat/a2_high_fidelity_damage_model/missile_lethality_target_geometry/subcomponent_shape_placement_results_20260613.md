# R17 Subcomponent Shape Placement Candidate Results

Generated: 2026-06-13

Update: the packet has since been regenerated through R21. R17 originally
created `14` shape-placement candidates; R18 promoted `4` zero-exposure
candidates into review-only generation rules, R19 added centerline candidates,
R20 added latest placement candidates, and R21 promoted the accepted latest
placements. The current JSON/CSV below therefore now report
`shape_placement_candidate_count=0` and `runtime_active_component_count=0`;
the R17 metrics below are retained as historical evidence.

## Outputs

| Artifact | Path |
| --- | --- |
| Candidate JSON | [review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json) |
| Candidate CSV | [review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.csv](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.csv) |
| Review views | [review_packets/f16c_20260611/subcomponent_shape_placement_views/index.html](review_packets/f16c_20260611/subcomponent_shape_placement_views/index.html) |
| Current empty-queue overview | [review_packets/f16c_20260611/subcomponent_shape_placement_views/overview_latest_triptych.svg](review_packets/f16c_20260611/subcomponent_shape_placement_views/overview_latest_triptych.svg) |

## Result

R17 adds a review-only shape-placement layer for the `14` R16 items whose current
receiver priors or held split segments still exposed samples outside the
whole-airframe top/side/front silhouettes.

The candidate layer preserves nominal public or declared dimensions. It changes
only the review shape family and, for one item, the measured R16 center-shift
candidate. It does not shrink components to make them fit and does not activate
runtime damage behavior.

| Metric | Value |
| --- | ---: |
| Source constraint items | 34 |
| Source silhouette exposure items | 14 |
| Shape-placement candidates | 14 |
| Nominal dimensions preserved | 14 |
| Candidates that reduce exposure | 13 |
| Candidates that fully resolve exposure | 4 |
| Candidates still unresolved | 10 |
| Candidates with no improvement | 1 |
| Current outside samples | 63 |
| Candidate outside samples | 25 |
| Outside sample reduction | 38 |
| Runtime active components | 0 |

Representative candidates:

- `iff_interrogator`: `rounded_lru_ellipsoid`, resolves silhouette exposure from `1` to `0` outside samples.
- `inertial_navigation_unit`: `rounded_lru_ellipsoid`, resolves silhouette exposure from `1` to `0`.
- `engine_core_afterburner_segment`: `segmented_engine_afterburner_capsule` plus `0.207628 m` center-shift candidate, resolves exposure from `4` to `0`.
- `cockpit_crew_station`: current ellipsoid remains exposed (`5` to `5`), so it needs a new placement/envelope model rather than another simple shape swap.

## Boundary

This is not accepted runtime geometry. The report is a design candidate layer
between R16 diagnostics and any later prior-rule update. Items still unresolved
after R17 need better size evidence, tapered/cross-section models, or
cross-region centerline geometry before runtime activation.
