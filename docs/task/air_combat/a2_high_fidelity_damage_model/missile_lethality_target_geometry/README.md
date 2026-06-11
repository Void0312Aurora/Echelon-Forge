# A2 Target Outer-Shape And Component Geometry

Status: `2026-06-12` active follow-on / TG-P6 human review dashboard complete
and manual review required. This subproject promotes the
[Lethality Hitbox Geometry Fidelity Gap](../../../issues/lethality_hitbox_geometry_fidelity_gap/README.md)
into the maintained A2 follow-on surface for F-16 outer-shape, component-region,
and distance-diagnostic work.

Language:

- English companion: `README.md`
- Chinese canonical: [README.zh.md](README.zh.md)

Inputs:

- A2 pointer: [../README.md](../README.md)
- Geometry gap issue:
  [../../../issues/lethality_hitbox_geometry_fidelity_gap/README.md](../../../issues/lethality_hitbox_geometry_fidelity_gap/README.md)
- Geometry review design:
  [../../../issues/lethality_hitbox_geometry_fidelity_gap/geometry_visual_review_design_20260611.md](../../../issues/lethality_hitbox_geometry_fidelity_gap/geometry_visual_review_design_20260611.md)
- F-16 runtime GLB:
  [../../../../../examples/viz/web_viz/static/assets/air/f16_c_falcon_carlos_maciel/f16_c_falcon_carlos_maciel.glb](../../../../../examples/viz/web_viz/static/assets/air/f16_c_falcon_carlos_maciel/f16_c_falcon_carlos_maciel.glb)
- F-16 audit glTF:
  [../../../../../examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf](../../../../../examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf)
- Current F-16 damage geometry:
  [../../../../../examples/config/database/aircraft/units/f16c_block50.json](../../../../../examples/config/database/aircraft/units/f16c_block50.json)

## Purpose

The lethality chain can now report post-detonation loads, cut exposure, and
component failure facts, but target geometry is still too coarse. Outer shape,
hitboxes, component boxes, and test-point distances are currently mixed
together. This subproject turns F-16 outer shape, vulnerable component regions,
and distance diagnostics into reviewable data before any near-fuze projection
uses the new geometry.

This is not an attempt to reconstruct authoritative F-16 engineering geometry.
It creates a source-clear, scale-checked, human-reviewable low-fidelity proxy
for better near-miss, continuous-rod, and fragmentation projection diagnostics.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| F-16 visual asset | active candidate | Sketchfab CC-BY-4.0 GLB is in the registry | Runtime visualization only; not a per-frame collision mesh |
| F-16 audit asset | active candidate | glTF source package, extracted files, hashes, and attribution are retained | Supports outer-shape review, not true internal component boundaries |
| Old FlightGear F-16 | rejected for mainline derivation | Archived under `assets/archive`; strong GPLv2 FlightGear source candidate | Must not enter mainline derived geometry |
| Current hitboxes | known gap | The issue records 4 m nose-aspect near miss with no component damage | Must not be treated as true outer shape or true component layout |
| Runtime integration | held | This subproject starts with review packets and diagnostics | No main projection-path change before review |

## Scope

In scope:

- Build an F-16 geometry manifest with source, hashes, axes, scale,
  public-dimension checks, and envelope dimensions.
- Generate low-fidelity outer regions from the audit glTF model: nose, canopy,
  fuselage, intake, wings, wing roots, engine/nozzle, horizontal tail, and
  vertical tail.
- Bind current `f16c_block50.json` component boxes to outer regions and flag
  obviously oversized, undersized, misplaced, or out-of-envelope boxes.
- Emit a static review packet: HTML scene, top/side/front SVGs, manifest,
  component-binding table, and test-point diagnostics.
- Compute nearest outer-shape distance, nearest component distance, and
  candidate-component count for the MLF-5 nose, tail, beam, above, and below
  test points.
- After review-packet and distance-diagnostic acceptance, design finer outer
  proxies such as oriented boxes, convex hulls, or simplified shell meshes, and
  define whether continuous-rod/fragment paths should use path or swept
  intersection against them.
- Produce a runtime-interface decision for what near-fuze, continuous-rod, and
  fragmentation projection may consume.

Out of scope:

- No claim of true F-16C Block 50 engineering geometry, true internal equipment
  boundaries, or true weapon lethality.
- No probability tuning to hide geometry problems.
- No high-poly mesh as first-round per-frame collision geometry.
- No structural breakup, debris/wreck object, Pk, or weapon-specific kill
  conclusion.
- No reopening of archived MLF-2, MLF-3, MLF-4, or MLF-5 packages.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze scope, inputs, and forbidden claims. | Geometry issue exists. | README, task clusters, status, and dispatch queue exist. | pass |
| `P1 Source And Scale` | Parse glTF and confirm axes/public-dimension scaling. | Dual F-16 assets exist. | `manifest.json` records source, hashes, axes, and scale. | pass |
| `P2 Outer Regions` | Generate reviewable outer-shape regions. | P1 manifest exists. | Region JSON and three-view drawings show major regions. | pass |
| `P3 Component Binding` | Bind existing component boxes to outer regions. | P2 regions exist. | Binding report lists oversized, undersized, misplaced, and out-of-envelope items. | pass |
| `P4 Review Packet` | Generate HTML/SVG/CSV review packet. | P2/P3 data exist. | A reviewer can see outer shape, legacy boxes, components, and test points together. | pass |
| `P5 Lethality Diagnostics` | Explain test points as outer/component distances and candidate counts. | P4 packet exists. | The 4 m nose case has geometry/direction/candidate evidence beyond "not a direct hit". | pass |
| `P6 Fine Geometry Proxy` | Advance coarse boxes into shape-closer proxies. | P4/P5 review and diagnostics pass. | Review-only OBB, thin-prism, convex-hull candidates, mesh-derived silhouettes, distance deltas, and overlays exist. | pass as review candidate |
| `P7 Runtime Interface Decision` | Decide whether the outer proxy enters near-fuze projection. | P6 proxy passes review or is explicitly held. | A tested runtime integration or held decision exists. | planned |

## Task Clusters

- Task cluster plan:
  [missile_lethality_target_geometry_task_clusters_20260611.md](missile_lethality_target_geometry_task_clusters_20260611.md)
- Current status:
  [missile_lethality_target_geometry_current_status_20260611.md](missile_lethality_target_geometry_current_status_20260611.md)
- First dispatch queue:
  [missile_lethality_target_geometry_dispatch_queue_20260611.md](missile_lethality_target_geometry_dispatch_queue_20260611.md)
- Fine geometry proxy design draft:
  [fine_geometry_proxy_design_20260611.md](fine_geometry_proxy_design_20260611.md)

## Outputs And Evidence

Planned outputs:

- `tools/geometry/airframe_geometry_review.py`: read-only geometry review packet
  generator.
- `docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_<date>/`:
  HTML, SVG, manifest, CSV, and review summary.
- `f16c_geometry_mapping_candidate_<date>.json`: outer regions, source nodes,
  and candidate component bindings.
- Focused tests for JSON/schema checks, path existence, geometry-manifest
  validation, and at least one F-16 review-packet generation run.

Generated:

- [review_packets/f16c_20260611/manifest.json](review_packets/f16c_20260611/manifest.json):
  TG-P1 source, hash, axis, scale, and legacy-hitbox envelope comparison
  manifest.
- [review_packets/f16c_20260611/f16c_geometry_mapping_candidate_20260611.json](review_packets/f16c_20260611/f16c_geometry_mapping_candidate_20260611.json):
  TG-P2 first outer-region candidate with `14` low-fidelity review regions. It
  records that actual glTF nodes are `Object_*`, so node names alone must not
  drive classification.
- Three-view drafts:
  [top.svg](review_packets/f16c_20260611/top.svg),
  [side.svg](review_packets/f16c_20260611/side.svg),
  [front.svg](review_packets/f16c_20260611/front.svg).
- Component binding reports:
  [component_binding_report_20260611.json](review_packets/f16c_20260611/component_binding_report_20260611.json),
  [component_binding_report_20260611.csv](review_packets/f16c_20260611/component_binding_report_20260611.csv).
  All `22` current components have candidate outer regions; `7` need human
  review: `6` left/right wing naming versus coordinate-sign cases, and
  `wing_spar_center` spanning a single-side wing region.
- Offline review page: [scene.html](review_packets/f16c_20260611/scene.html).
  The three views now overlay outer regions, legacy hitboxes, component boxes,
  and numbered review points.
- Review-point distance diagnostics:
  [review_point_diagnostics_20260611.json](review_packets/f16c_20260611/review_point_diagnostics_20260611.json),
  [review_point_diagnostics_20260611.csv](review_packets/f16c_20260611/review_point_diagnostics_20260611.csv).
  The packet covers `10` nose, tail, beam, above, and below points; `6` are
  inside outer regions. `nose_axis_4m` is in `forward_fuselage`, nearest to
  `cockpit_crew_station` at `0.2 m`, with `6` candidate components. The
  `nose_axis_6m` point is in `nose_radome` and inside boxes such as
  `apg68_radar_array`.
- [fine_geometry_proxy_design_20260611.md](fine_geometry_proxy_design_20260611.md):
  TG-P6 first fine-geometry proxy design, defining the use, boundary, and
  runtime preconditions for `obb`, `thin_prism`, `convex_hull`, and
  `simplified_shell`.
- Fine-geometry proxy candidate:
  [fine_geometry_proxy_candidate_20260611.json](review_packets/f16c_20260611/fine_geometry_proxy_candidate_20260611.json),
  [fine_proxy_top.svg](review_packets/f16c_20260611/fine_proxy_top.svg),
  [fine_proxy_side.svg](review_packets/f16c_20260611/fine_proxy_side.svg),
  [fine_proxy_front.svg](review_packets/f16c_20260611/fine_proxy_front.svg).
  TG-P6-R3 generated top/side/front convex hull silhouettes from `13,415`
  audit glTF vertices for all `14` review-only proxies. `8` regions use source
  bounds directly; `6` regions use recorded inflated-bound fallback and remain
  high-priority manual review items before `TG-P7`.
- Human review dashboard:
  [fine_proxy_review_dashboard.html](review_packets/f16c_20260611/fine_proxy_review_dashboard.html).
  TG-P6-R4 adds per-region cards with local top/side/front zooms, component
  overlays, inflation metrics, hull point counts, review flags, and
  candidate/review/hold status.
- `pytest -q tests/tools/test_airframe_geometry_review.py`: `2 passed`.

## Acceptance Gate

This subproject can be marked accepted only when:

- The F-16 review packet opens offline and shows outer shape, legacy hitboxes,
  component boxes, and test points together.
- The manifest records GLB/glTF dual-model roles, source, hashes, axes, scale,
  and public-dimension error.
- Nose, tail, beam, above, and below test points report nearest outer-shape
  distance, nearest component distance, and candidate-component count.
- The 4 m nose close-to-shape case is explained as a concrete geometry,
  direction, or candidate-component issue instead of an unexplained zero-damage
  result.
- Docs continue to reject true F-16 engineering geometry, true Pk, structural
  breakup, debris/wreck, or weapon-specific kill claims.

## Residuals And Next Steps

- MQ-9 geometry is a later reuse target; the first round is F-16 only.
- Runtime near-fuze projection should consume outer-shape proxies only after the
  review packet, distance diagnostics, and fine-proxy candidate review pass or
  are explicitly held in `TG-P7`.
- Structural breakup, wreck/debris, and Pk remain separate future subprojects.

## Archive

Historical or superseded status, dispatch, and review records move to
[archive/README.md](archive/README.md) after a closeout surface exists.
