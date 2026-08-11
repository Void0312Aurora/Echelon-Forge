# F-16 Target Geometry Human Review Findings

Status: `2026-06-12` visual review recorded / runtime interface held; repaired
items are tracked by TG-P6-R10.

This note records the first visual review of the retired intermediate triage
dashboard.
It also uses:

- [component_binding_report_20260611.json](review_packets/f16c_20260611/component_binding_report_20260611.json)
- [surface_component_candidate_20260611.json](review_packets/f16c_20260611/surface_component_candidate_20260611.json)
- [review_point_diagnostics_20260611.json](review_packets/f16c_20260611/review_point_diagnostics_20260611.json)
- [fine_geometry_proxy_candidate_20260611.json](review_packets/f16c_20260611/fine_geometry_proxy_candidate_20260611.json)

Follow-up: [subagent_correction_results_20260612.md](subagent_correction_results_20260612.md)
records the scoped correction pass for radar/IFF, nozzle, and review semantics.

## Summary Judgment

The TG-P6 visual triage surface is useful, but the current geometry must not
enter `TG-P7` runtime integration yet.

- `P6` can remain a review-only candidate: the outer proxies, surface-component
  candidates, review points, and triage cards now expose the open issues.
- `P7` remains held: side-sign convention, nose radar/IFF boxes,
  engine/nozzle boxes, and surface-to-runtime-component handoff are still
  blocking.
- These artifacts must not be described as true F-16 engineering geometry, true
  internal component layout, or an accepted runtime damage model.

## Visual Findings

| Area | Finding | Decision |
| --- | --- | --- |
| Left/right wings and roots | `left_*` components bind as a group to `right_wing`/`right_wing_root`, while `right_*` components bind to `left_wing`/`left_wing_root`. In top and front views this is a systemic mirrored placement, not six isolated component-box errors. | Fix the side-coordinate convention or left/right naming map first; hold wing, wing-root, control-surface actuator, and wing-fuel-cell runtime handoff. |
| Nose/radar/IFF | `apg68_radar_array` and `iff_interrogator` have `0.0` overlap with `nose_radome` and centers outside the region. Visually the legacy component boxes are height/axis drifted from the corrected radome silhouette. | Do not accept `surface_nose_radome` handoff until radar/IFF/nose boxes or mapping are repaired. |
| 4 m / 6 m nose-axis review points | `nose_axis_4m` is in `forward_fuselage`, nearest to `cockpit_crew_station` at `0.2 m`, with `6` candidate components. `nose_axis_6m` is nearest to `nose_radome`, but it sits in the `apg68_radar_array` box while remaining about `0.349524 m` from the outer radome. | The 4 m case is explainable as an outer-shape/candidate-component issue; the 6 m case exposes radome versus radar-box inconsistency. Both remain diagnostic-only. |
| Engine core | `engine_core` has low overlap with `aft_fuselage_engine`, but its center remains inside the aft engine region and the isolated views look like an aft bay/nozzle/tail-root cross-region boundary. | Accept placement as a review-only cross-region candidate; record semantics instead of treating low overlap as an automatic bad box. |
| Nozzle/vertical tail | `afterburner_nozzle` currently binds to `vertical_tail`, while `surface_engine_nozzle` links nozzle, engine core, and fuel control. The visual relationship is not clean. | Repair nozzle box ownership and region assignment; hold `surface_engine_nozzle` and `surface_vertical_tail_skin`. |
| Center spar / center fuselage | `wing_spar_center` is a wide thin span across fuselage/root semantics; low overlap can match a center-spar cross-region structure. `surface_center_fuselage_skin` also has four clean direct links. | Accept the four clean center-fuselage links as review-only candidates; hold `wing_spar_center` for cross-region semantics instead of treating it as automatically wrong. |
| Canopy | `surface_canopy` lacks a dedicated runtime surface component and only links to `cockpit_crew_station`. | Add `dedicated_canopy_surface_component` or explicitly hold this surface. |
| Intake | `surface_intake_lip_and_duct` lacks `dedicated_intake_lip_or_duct_component` and links to the still-unreviewed `engine_core`. | Add an intake/lip runtime component or hold this surface. |
| Horizontal tails | Left and right horizontal-tail surfaces have no internal component links. | Add left/right horizontal-tail actuator or surface components before review can pass. |
| Forward fuselage skin | `surface_forward_fuselage_skin` is the only non-review surface. It directly links `cockpit_crew_station`, `inertial_navigation_unit`, and `nose_avionics_bay`. | Keep as a relatively clean candidate surface; still not runtime accepted. |
| Above/below review points | `above_4m` and `below_4m` have no nearby component candidates and are visually far from useful outer/component hits. | Keep as diagnostic sanity points only. |

## Required Repairs

1. Fix the side-sign or left/right naming convention, then regenerate component
   binding, surface candidates, and triage.
2. Repair the `apg68_radar_array`, `iff_interrogator`, and `nose_radome`
   height/axis relationship.
3. Repair the `afterburner_nozzle`, `surface_engine_nozzle`, and
   `vertical_tail` handoff; record `engine_core` as a cross-region boundary
   candidate first.
4. Add explicit runtime surface components for `surface_canopy`,
   `surface_intake_lip_and_duct`, and the left/right horizontal tails, or record
   held decisions.
5. Give `wing_spar_center` cross-region semantics; split or reposition it only
   if that semantic review fails.

## Accepted Boundary

- Accepted: keep TG-P6 review artifacts as review-only evidence.
- Accepted: keep `surface_forward_fuselage_skin` as the relatively clean
  candidate surface.
- Not accepted: connecting current surface-component candidates to near-fuze,
  continuous-rod, or fragmentation runtime projection.
- Not accepted: claiming true internal component geometry, true lethality
  probability, or weapon-specific kill conclusions.
