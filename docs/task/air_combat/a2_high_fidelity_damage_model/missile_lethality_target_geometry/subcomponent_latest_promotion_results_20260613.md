# TG-P6-R21 Latest Subcomponent Promotion Results

Status: `2026-06-13` pass as review-only latest placement promotion; `TG-P7`
runtime activation remains held for cross-region ownership.

Chinese companion:
[subcomponent_latest_promotion_results_20260613.zh.md](subcomponent_latest_promotion_results_20260613.zh.md).

## Scope

R21 promotes the already-reviewed R19/R20 latest subcomponent placements from
the diagnostic candidate layer into the review-only generation rules. It does
not activate runtime damage projection and does not claim true F-16 internal
engineering geometry.

Promoted receiver priors:

- R18 retained: `iff_interrogator`, `inertial_navigation_unit`.
- R21 added: `apg68_radar_array`, `cockpit_crew_station`,
  `center_fuselage_fuel_cell`, `engine_core`, `afterburner_nozzle`,
  `left_wing_fuel_cell`, `right_wing_fuel_cell`.

Promoted held split segments:

- R18 retained: `engine_core_afterburner_segment`,
  `engine_core_hot_section_segment`.
- R21 added: `engine_core_forward_compressor_segment`,
  `wing_spar_center_left_inner_wing_segment`,
  `wing_spar_center_right_inner_wing_segment`.

## Result

Generated packet:
[review_packets/f16c_20260611/manifest.json](review_packets/f16c_20260611/manifest.json).

Key counts after regeneration:

- `internal_component_prior_shape_promotion_count=9`
- `cross_region_held_segment_shape_promotion_count=5`
- `airframe_constraint_silhouette_exposure_item_count=0`
- `airframe_constraint_size_or_shape_review_item_count=0`
- `subcomponent_shape_placement_candidate_count=0`
- `runtime_active_component_count=0`

The shape-placement report is intentionally empty after promotion:
[subcomponent_shape_placement_candidate_20260611.json](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json).
The retired view index is recorded as historical audit context only.

## Boundary

- Runtime near-fuze, continuous-rod, and fragment projection behavior is
  unchanged.
- `engine_core` and `wing_spar_center` still require explicit ownership
  acceptance, split, or deliberate held treatment before `TG-P7`.
- The promoted shapes are public-size or mesh-review proxies, not authoritative
  F-16 component boundaries.
- No real-weapon Pk, kill, breakup, debris, or wreck claim is made.

## Validation

```bash
python -m py_compile tools/geometry/airframe_geometry_review.py
pytest -q tests/tools/test_airframe_geometry_review.py
python tools/geometry/airframe_geometry_review.py --out docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611
```

Focused test result: `2 passed`.
