# A2 Target Outer-Shape And Component Geometry

Status: `2026-06-13` active follow-on / TG-P6-R21 latest subcomponent
placement promotion applied and TG-P7 runtime activation held for
cross-region ownership. This subproject promotes the
[Lethality Hitbox Geometry Fidelity Gap](../../../issues/lethality_hitbox_geometry_fidelity_gap/README.md)
into the maintained A2 follow-on surface for F-16 outer-shape, surface-component,
legacy internal-component link, and distance-diagnostic work.

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
- Turn each outer region into a review-only surface component and list the
  current internal components, drift flags, and missing links that a hit on that
  surface may hand off to.
- Emit semantic outer-shell volume component candidates with parse-ready runtime
  component JSON, isolated per-volume views, and explicit direct-vs-cross-region
  receiver handoff status.
- Generate sphere, cylinder, capsule, and ellipsoid priors for current
  internal/system receivers and constrain them by parent shell support bounds
  so old receiver AABBs no longer protrude outside the shell.
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
| `P6 Fine Geometry Proxy` | Advance coarse boxes into shape-closer proxies and add the review-only handoff layer from outer hits to component damage. | P4/P5 review and diagnostics pass. | Review-only OBB, thin-prism, convex-hull candidates, mesh-derived silhouettes, surface-component candidates, semantic volume component candidates, constrained internal receiver priors, visual triage cards, distance deltas, and overlays exist. | pass as parse-ready candidate |
| `P7 Runtime Interface Decision` | Decide whether the outer proxy enters near-fuze projection. | P6 proxy passes review or is explicitly held. | A tested runtime integration or held decision exists. | planned / activation held |

## Task Clusters

- Task cluster plan:
  [missile_lethality_target_geometry_task_clusters_20260611.md](missile_lethality_target_geometry_task_clusters_20260611.md)
- Current status:
  [missile_lethality_target_geometry_current_status_20260611.md](missile_lethality_target_geometry_current_status_20260611.md)
- First dispatch queue:
  [missile_lethality_target_geometry_dispatch_queue_20260611.md](missile_lethality_target_geometry_dispatch_queue_20260611.md)
- Fine geometry proxy design draft:
  [fine_geometry_proxy_design_20260611.md](fine_geometry_proxy_design_20260611.md)
- Human review findings:
  [human_review_findings_20260612.md](human_review_findings_20260612.md)
- Geometry repair results:
  [geometry_repair_results_20260612.md](geometry_repair_results_20260612.md)
- Semantic damage geometry implementation:
  [semantic_damage_geometry_results_20260612.md](semantic_damage_geometry_results_20260612.md)
- Internal component prior constraints:
  [internal_component_prior_results_20260612.md](internal_component_prior_results_20260612.md)
- Semantic parent-child component layout:
  [semantic_parent_child_layout_results_20260612.md](semantic_parent_child_layout_results_20260612.md)
- Latest subcomponent promotion:
  [subcomponent_latest_promotion_results_20260613.md](subcomponent_latest_promotion_results_20260613.md)

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
  After the R11 repair, `26` of `26` current components are bound, `0` remain
  `needs_review`, `0` remain side-sign blockers, `2` are review-only
  cross-region semantics, and `0` remain geometry-review-required bad boxes.
- Offline review page: [scene.html](review_packets/f16c_20260611/scene.html).
  The three views now overlay outer regions, legacy hitboxes, component boxes,
  and numbered review points.
- Review-point distance diagnostics:
  [review_point_diagnostics_20260611.json](review_packets/f16c_20260611/review_point_diagnostics_20260611.json),
  [review_point_diagnostics_20260611.csv](review_packets/f16c_20260611/review_point_diagnostics_20260611.csv).
  The packet covers `10` nose, tail, beam, above, and below points; `2` are
  inside corrected outer regions. `nose_axis_4m` is in `forward_fuselage`,
  nearest to `dedicated_canopy_surface_component` at `0.125 m`, with `7`
  candidate components. `nose_axis_6m` is about `0.35 m` from `nose_radome` and
  now has `5` candidate components after the receiver and component-box repair.
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
  audit glTF vertices for all `14` review-only proxies. Nose, canopy, wing, and
  horizontal-tail regions are corrected against audit-mesh placement and use
  explicit source-node whitelists. `inflated_fallback_count=0`; missing vertices
  now fail review instead of expanding the region bounds.
- Human review dashboard:
  [fine_proxy_review_dashboard.html](review_packets/f16c_20260611/fine_proxy_review_dashboard.html).
  TG-P6-R4 adds per-region cards with local top/side/front zooms, component
  overlays, mesh-node selection strategy, disabled fallback policy, hull point
  counts, review flags, and candidate/review status.
- Surface component candidates:
  [surface_component_candidate_20260611.json](review_packets/f16c_20260611/surface_component_candidate_20260611.json),
  [surface_component_candidate_20260611.csv](review_packets/f16c_20260611/surface_component_candidate_20260611.csv).
  TG-P6-R5 turns the `14` outer regions into review-only surface components and
  lists which current internal components each surface may hand off to. After
  R11, `0` surface components need human review, `0` runtime receiver links are
  missing, `0` surface rows are blocked by side-sign mismatch, and `8` carry
  cross-region semantic holds/candidates.
- Visual human-review triage:
  [human_review_triage.html](review_packets/f16c_20260611/human_review_triage.html).
  TG-P6-R6 groups the manual-review queue into visual cards for coordinate-sign,
  component-placement, surface-handoff, and review-point sanity issues. Each card
  states the review question, what to look at, and the decision needed, then
  shows local top/side/front overlays so review no longer depends on reading CSV
  rows by eye.
- Isolated component review views:
  [component_review_views/index.html](review_packets/f16c_20260611/component_review_views/index.html),
  [component_review_views/manifest.json](review_packets/f16c_20260611/component_review_views/manifest.json).
  TG-P6-R8 now regenerates `75` review-only pages: `26` current
  component-binding views, `29` surface-to-single-component handoff views, and
  `20` review-point candidate-component views. Each page has its own
  top/side/front SVGs, so independent review no longer has to read crowded
  overview cards.
- Semantic damage geometry candidates:
  [semantic_damage_geometry_candidate_20260611.json](review_packets/f16c_20260611/semantic_damage_geometry_candidate_20260611.json),
  [semantic_damage_geometry_candidate_20260611.csv](review_packets/f16c_20260611/semantic_damage_geometry_candidate_20260611.csv),
  [semantic_damage_geometry_views/index.html](review_packets/f16c_20260611/semantic_damage_geometry_views/index.html).
  TG-P6-R12 emits `14` semantic outer-shell volume components and `14`
  `runtime_component_json_candidate` records. The runtime schema and loader now
  parse the geometry fields, but `runtime_active_component_count=0`; active
  lethality behavior is unchanged until `TG-P7`.
- Internal receiver prior geometry candidates:
  [internal_component_prior_candidate_20260611.json](review_packets/f16c_20260611/internal_component_prior_candidate_20260611.json),
  [internal_component_prior_candidate_20260611.csv](review_packets/f16c_20260611/internal_component_prior_candidate_20260611.csv),
  [internal_component_prior_views/index.html](review_packets/f16c_20260611/internal_component_prior_views/index.html).
  TG-P6-R13 generates sphere/cylinder/capsule/ellipsoid priors for all `26`
  current receivers and constrains them by parent shell support bounds or
  cross-region unions. `post_constraint_outside_count=0`,
  `cross_region_held_prior_count=2`, and `runtime_active_component_count=0`.
  Current HTML/SVG entrypoints:
  [index](review_packets/f16c_20260611/internal_component_prior_views/index.html),
  [manifest](review_packets/f16c_20260611/internal_component_prior_views/manifest.json).
- Semantic parent-child component layout:
  [semantic_parent_child_layout_candidate_20260611.json](review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.json),
  [semantic_parent_child_layout_candidate_20260611.csv](review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.csv),
  [semantic_parent_child_layout_views/index.html](review_packets/f16c_20260611/semantic_parent_child_layout_views/index.html).
  TG-P6-R14 makes the `14` geometry-modeled parent shell parts the primary
  review surface and overlays all `26` receiver priors on those parent views.
  The packet records `extra_receiver_slot_count=12`,
  `cross_region_held_receiver_count=2`, and `runtime_active_component_count=0`.
  TG-P6-R15 also adds review-only split segments for the two red held receivers:
  [cross_region_held_component_segments_20260611.json](review_packets/f16c_20260611/cross_region_held_component_segments_20260611.json),
  [cross_region_held_component_segments_20260611.csv](review_packets/f16c_20260611/cross_region_held_component_segments_20260611.csv).
  It splits `engine_core` into `3` engine segments and `wing_spar_center` into
  `5` spar segments; `held_segment_count=8`,
  `outside_whole_airframe_segment_count=0`, and runtime ownership remains held.
  Current HTML/SVG entrypoints:
  [index](review_packets/f16c_20260611/semantic_parent_child_layout_views/index.html),
  [manifest](review_packets/f16c_20260611/semantic_parent_child_layout_views/manifest.json).
- Airframe silhouette constraint correction candidates:
  [airframe_constraint_correction_candidate_20260611.json](review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.json),
  [airframe_constraint_correction_candidate_20260611.csv](review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.csv).
  TG-P6-R16 checks all `34` receiver priors and held split segments with
  shape-aware top/side/front whole-airframe silhouette samples. After R21 latest
  placement promotion, the packet records
  `silhouette_exposure_item_count=0`,
  `center_shift_reduces_item_count=0`, `size_or_shape_review_item_count=0`,
  and `runtime_active_component_count=0`. Current latest-placement overview:
  [overview_latest_triptych.svg](review_packets/f16c_20260611/subcomponent_shape_placement_views/overview_latest_triptych.svg).
- Subcomponent shape-placement candidates:
  [subcomponent_shape_placement_candidate_20260611.json](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json),
  [subcomponent_shape_placement_candidate_20260611.csv](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.csv),
  [subcomponent_shape_placement_views/index.html](review_packets/f16c_20260611/subcomponent_shape_placement_views/index.html).
  TG-P6-R17 generated candidate shape families and placement candidates for the
  `14` R16 exposed subcomponents while preserving nominal dimensions. TG-P6-R18
  promotes the first `4` zero-exposure candidates into review-only
  prior/held-segment generation rules; TG-P6-R19 adds local centerline
  candidates; TG-P6-R20 resolves the remaining radar and cockpit placement
  issues. TG-P6-R21 promotes the latest accepted placements into the
  review-only generation rules, so the current packet now records
  `shape_placement_candidate_count=0`,
  `latest_candidate_total_outside_sample_count=0`, and
  `runtime_active_component_count=0`. The shape-placement view index remains as
  an empty-queue audit trace.
- Subcomponent shape-promotion results:
  [subcomponent_shape_promotion_results_20260613.md](subcomponent_shape_promotion_results_20260613.md).
  TG-P6-R18 promotes `iff_interrogator`, `inertial_navigation_unit`,
  `engine_core_afterburner_segment`, and `engine_core_hot_section_segment` from
  the R17 candidate layer into review-only generation rules. Runtime activation
  remains `0`.
- Subcomponent centerline-placement results:
  [subcomponent_centerline_placement_results_20260613.md](subcomponent_centerline_placement_results_20260613.md).
  TG-P6-R19 adds dimension-preserving centerline candidates for the `10`
  remaining shape-placement items; `8` clear sampled whole-airframe exposure and
  `apg68_radar_array` plus `cockpit_crew_station` remain unresolved.
- Latest subcomponent placement results:
  [subcomponent_latest_placement_results_20260613.md](subcomponent_latest_placement_results_20260613.md).
  TG-P6-R20 resolves the remaining radar and cockpit placement issues and makes
  the main review views show only gray whole-airframe wireframe plus blue latest
  subcomponent candidates.
- Latest subcomponent promotion results:
  [subcomponent_latest_promotion_results_20260613.md](subcomponent_latest_promotion_results_20260613.md).
  TG-P6-R21 promotes the R20 latest placements into review-only prior and
  held-segment generation rules. Current counts are
  `internal_component_prior_shape_promotion_count=9`,
  `cross_region_held_segment_shape_promotion_count=5`, and
  `subcomponent_shape_placement_candidate_count=0`.
- Human review findings:
  [human_review_findings_20260612.md](human_review_findings_20260612.md).
  R7 historical snapshot: the first visual review kept TG-P6 artifacts as
  review-only evidence and held `TG-P7` for side-sign, nose radar/IFF,
  engine/nozzle, and surface-to-runtime-component handoff blockers later refined
  by R9/R10 and superseded by R11.
- Independent subagent review findings:
  [subagent_independent_review_findings_20260612.md](subagent_independent_review_findings_20260612.md).
  Five read-only subagents reviewed side-sign, nose, engine/nozzle, missing
  receiver components, and center-fuselage cross-region slices. The review
  refines the first findings: `engine_core` and `wing_spar_center` should first
  be handled as cross-region semantics; at the R9 snapshot, side-sign,
  radar/IFF, afterburner/nozzle, and missing runtime relations were still hard
  blockers.
- Subagent correction results:
  [subagent_correction_results_20260612.md](subagent_correction_results_20260612.md).
  Two write-scoped subagents repaired the `apg68_radar_array`,
  `iff_interrogator`, and `afterburner_nozzle` source boxes, added explicit
  review semantics for cross-region components and missing runtime links, and
  regenerated the packet. This is the R10 historical correction snapshot.
- Geometry repair results:
  [geometry_repair_results_20260612.md](geometry_repair_results_20260612.md).
  R11 repaired the left/right region mapping, wing and wing-root component
  placements, explicit canopy/intake/horizontal-tail receiver components, and
  direct surface handoff rules. Component and surface `needs_review` counts are
  now `0`; `TG-P7` remains held only for explicit ownership of `engine_core` and
  `wing_spar_center` cross-region semantics.
- `pytest -q tests/tools/test_airframe_geometry_review.py`: `2 passed`.
- `./build-workshop/ef_test --test-suite=components_basic`: `23` cases passed
  after building `ef_test`.
- `pytest -q tests/architecture/damage_model`: `177 passed`; this includes the
  repaired Stage-C component-probability surface probe selecting component rows
  rather than `global-fallback`.

## Acceptance Gate

This subproject can be marked accepted only when:

- The F-16 review packet opens offline and shows outer shape, legacy hitboxes,
  component boxes, and test points together.
- The manifest records GLB/glTF dual-model roles, source, hashes, axes, scale,
  and public-dimension error.
- Nose, tail, beam, above, and below test points report nearest outer-shape
  distance, nearest component distance, and candidate-component count.
- Every outer region has a review-only surface component candidate and a clear
  statement of whether its link to current internal components is reliable.
- Every current component and high-risk handoff has an isolated top/side/front
  review view instead of sharing a crowded mini-view with unrelated components.
- Every semantic outer-shell volume candidate has an isolated top/side/front
  review view and an explicit direct-vs-cross-region receiver handoff status.
- Every current internal/system receiver has prior geometry, parent shell
  constraints, pre/post protrusion fractions, and isolated top/side/front review
  views; this layer must not be treated as true internal engineering geometry.
- The 4 m nose close-to-shape case is explained as a concrete geometry,
  direction, or candidate-component issue instead of an unexplained zero-damage
  result.
- Docs continue to reject true F-16 engineering geometry, true Pk, structural
  breakup, debris/wreck, or weapon-specific kill claims.

## Residuals And Next Steps

- MQ-9 geometry is a later reuse target; the first round is F-16 only.
- Runtime near-fuze projection should consume outer-shape proxies only after
  explicit ownership is accepted, split, or deliberately held for cross-region
  `engine_core` / `wing_spar_center` semantics. R12/R13 provide parse-ready
  semantic shell component candidates and review-only internal receiver prior
  candidates, but do not activate them in the F-16 unit damage model; `TG-P7`
  is still explicitly held for the remaining ownership decision and activation
  test.
- Structural breakup, wreck/debris, and Pk remain separate future subprojects.

## Archive

Historical or superseded status, dispatch, and review records move to
[archive/README.md](archive/README.md) after a closeout surface exists.
