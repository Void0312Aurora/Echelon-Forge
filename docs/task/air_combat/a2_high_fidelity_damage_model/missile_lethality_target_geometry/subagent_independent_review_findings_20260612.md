# F-16 Target Geometry Independent Subagent Review Findings

Status: `2026-06-12` independent subagent review recorded / review-only /
partially superseded by TG-P6-R10 corrections.

This note summarizes five read-only subagent reviews from an intermediate
isolated-view packet. That intermediate packet has since been removed from the
current final-result surface; the finding text is retained only as historical
review context. Current containment evidence is the whole-airframe projected
mesh contour plus the follow-up placement queue.

Follow-up: [subagent_correction_results_20260612.md](subagent_correction_results_20260612.md)
records the write-scoped correction pass. Radar/IFF and nozzle source boxes are
repaired there; at that R10 snapshot, side-sign and missing runtime receiver
relations remained held. Current regenerated-packet state is superseded by
[geometry_repair_results_20260612.md](geometry_repair_results_20260612.md).

The R9 isolated-packet snapshot contained `85` review-only pages: `22` current component
binding views, `45` surface-handoff or missing-link views, and `18` review-point
candidate-component views. These artifacts are not runtime damage geometry,
collision meshes, true F-16 engineering geometry, or real-weapon lethality
authority.

## Findings

| Group | Independent finding | Decision |
| --- | --- | --- |
| Side sign and wing side | Wing fuel cells, aileron actuators, leading-edge flap actuators, and beam points show a systemic side mismatch across component names, component `y` signs, region names, and nearest-region labels. | Repair the side-coordinate, region naming, or binding convention; hold wing, wing-root, and beam/wing projection handoff. |
| Nose/radar/forward fuselage | `apg68_radar_array` and `iff_interrogator` have zero overlap with `nose_radome` and sit off the radome in side view; `surface_nose_radome` has no clean direct links. `surface_forward_fuselage_skin` has three clean candidate links. | Keep forward-fuselage skin as a relatively clean review-only candidate; repair or hold radar/IFF; hold nose-radome handoff. |
| Engine/nozzle/vertical tail | `engine_core` is centered in the aft engine region and looks like a cross-region aft bay/nozzle/tail-root boundary case. `afterburner_nozzle` sits axially near the nozzle but is bound to `vertical_tail` and vertically mismatched to the nozzle proxy. | Accept `engine_core` placement as review-only cross-region semantics; repair `afterburner_nozzle`; hold `surface_engine_nozzle`; keep vertical-tail/rudder candidate while removing or repairing the nozzle link. |
| Missing runtime receivers | Canopy, intake lip/duct, and both horizontal-tail skins are valid outer-surface candidates, but lack explicit runtime surface/actuator receiver relations. | Accept as review findings; add/map dedicated receiver relations or explicitly hold those surfaces. |
| Center fuselage and large-span parts | `surface_center_fuselage_skin` has four clean direct links. `wing_spar_center` is a large thin span crossing fuselage and wing-root semantics, so low overlap is not automatically a bad box. `above_4m` and `below_4m` are no-near-candidate sanity points. | Accept clean center-fuselage links as review-only; hold `wing_spar_center` for cross-region semantics; keep above/below points diagnostic-only. |

## Repair Priority

1. Fix side convention or region/component naming before wing handoff.
2. Repair APG-68/IFF versus nose-radome height and axis relationship.
3. Repair `afterburner_nozzle` placement and binding.
4. Add or hold canopy, intake, and horizontal-tail runtime receiver relations.
5. Record cross-region semantics for `wing_spar_center` and `engine_core`.

## Accepted Review-Only Candidates

- `surface_forward_fuselage_skin` to cockpit, INS, and nose avionics candidates.
- Clean aft-engine-bay links for electrical power bus, engine fuel control unit, and tail hydraulic pump.
- Clean center-fuselage links for center fuel cell, data link terminal, flight control computer, and mission computer.
- Vertical-tail to `rudder_actuator` as a candidate relation; not the `afterburner_nozzle` relation.

## Boundary

Missing runtime relations do not mean the outer surfaces are absent. Large-span
low overlap is not automatically a bad box. A review point inside a legacy box
does not mean that legacy box has passed geometry review. Nothing here may be
used as runtime near-fuze, continuous-rod, or fragment projection authority.
