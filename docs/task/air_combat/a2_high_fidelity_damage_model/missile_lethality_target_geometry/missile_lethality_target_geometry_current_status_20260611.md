# A2 Target Geometry Current Status

Status: `2026-06-11` TG-P5 review packet and diagnostics complete. The parent entry and issue have
moved F-16 geometry refinement from issue tracking into an executable
subproject; the first source/axis/scale manifest, outer-region candidate,
component-binding report, offline review page, and test-point distance
diagnostics are generated.

Chinese canonical:
[missile_lethality_target_geometry_current_status_20260611.zh.md](missile_lethality_target_geometry_current_status_20260611.zh.md).

## Known Facts

| Item | Current fact | Impact |
| --- | --- | --- |
| Runtime visual model | `examples/viz/web_viz/static/assets/air/f16_c_falcon_carlos_maciel/f16_c_falcon_carlos_maciel.glb` | Can remain the front-end visual asset |
| Audit model | `examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf` | Geometry review should read nodes, meshes, and bounds from glTF |
| Source and license | Sketchfab `F16-C Falcon`, Carlos.Maciel, CC-BY-4.0 | Suitable as a mainline outer-review candidate with attribution and boundaries |
| Public dimensions | Current F-16C database records length `15.06 m`, wingspan `9.96 m`, height `4.88 m` | Geometry proxies need dimension-scale audit against these orders of magnitude |
| Current hitboxes | Merged envelope about `15.3 m x 9.8 m x 1.2 m` | Length/width are close to public order; height is severely low |
| Exposed symptom | A 4 m nose-aspect close-to-shape point can produce no component damage | Requires outer distance, component distance, and candidate-component diagnostics |
| TG-P1 manifest | [review_packets/f16c_20260611/manifest.json](review_packets/f16c_20260611/manifest.json) | Scaled candidate model is about `+0.09%` length, `-3.37%` wingspan, and `-4.50%` height; legacy hitbox height is about `-75.41%` |
| Node semantics | Actual glTF mesh nodes are `Object_*`; intake metadata retains hints such as `Canopy01_1` and `EngineL01_17` | P2 cannot rely only on glTF node names; it needs position rules and manual mapping |
| TG-P2 outer regions | [f16c_geometry_mapping_candidate_20260611.json](review_packets/f16c_20260611/f16c_geometry_mapping_candidate_20260611.json) | Generated `14` low-fidelity regions; `x=4m` falls in `forward_fuselage`, while `x=6m` falls in `nose_radome` |
| TG-P4 review packet | [scene.html](review_packets/f16c_20260611/scene.html), [top.svg](review_packets/f16c_20260611/top.svg), [side.svg](review_packets/f16c_20260611/side.svg), [front.svg](review_packets/f16c_20260611/front.svg) | Three views overlay outer regions, legacy hitboxes, component boxes, and numbered review points |
| TG-P3 component binding | [component_binding_report_20260611.json](review_packets/f16c_20260611/component_binding_report_20260611.json), [component_binding_report_20260611.csv](review_packets/f16c_20260611/component_binding_report_20260611.csv) | All `22` components have candidate regions; `7` need human review |
| TG-P5 distance diagnostics | [review_point_diagnostics_20260611.json](review_packets/f16c_20260611/review_point_diagnostics_20260611.json), [review_point_diagnostics_20260611.csv](review_packets/f16c_20260611/review_point_diagnostics_20260611.csv) | Covers `10` review points; `6` are inside outer regions; `nose_axis_4m` is `0.2 m` from the nearest component with `6` candidate components |
| TG-P6 design draft | [fine_geometry_proxy_design_20260611.md](fine_geometry_proxy_design_20260611.md) | Defines the order for moving from boxes to oriented boxes, thin prisms, convex hulls, and simplified shell meshes |

## Current Boundary

- This status proves only that the TG-P1 source/scale manifest, TG-P2
  outer-region candidate, TG-P3 component-binding report, TG-P4 review packet,
  and TG-P5 test-point distance diagnostics are complete; it does not prove
  runtime integration is complete.
- The Sketchfab model is an outer-review candidate, not a source of true
  internal component boundaries.
- The old FlightGear F-16 is archived as a strong GPLv2 source candidate and
  must not enter mainline derived geometry.
- Runtime near-fuze projection remains unchanged until review packets and
  diagnostics justify an integration decision.

## Next Step

1. Human-review the `7` `needs_review` rows in
   `component_binding_report_20260611.csv`, especially left/right coordinate
   signs and `wing_spar_center`.
2. Continue `TG-P6` implementation: emit `fine_geometry_proxy_candidate_20260611.json` and advance coarse boxes into
   oriented-box, convex-hull, or simplified-shell candidates before any runtime
   integration review.

## Validation Reminder

Each round should at least run:

```bash
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry
```

Current focused test:

```bash
pytest -q tests/tools/test_airframe_geometry_review.py
```

Result: `2 passed`.
