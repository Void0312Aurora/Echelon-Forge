# A2 Target Outer-Shape And Component Geometry

Status: `2026-06-14` accepted / retained. The F-16C fine-geometry engineering
proxy is closed against the geometry-only acceptance gate, with the closeout
record under
[archive/tg_f16c_fine_geometry_accepted_20260614](archive/tg_f16c_fine_geometry_accepted_20260614/README.md); default unit database replacement, default runtime-path replacement, policy/reward diagnostics, and training benefit are not acceptance gates for this subproject. This
subproject promotes the
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

This subproject builds an engineering geometry proxy that can feed later
lethality-chain work: source-traced, scale-checked, audit-mesh aligned,
human-reviewable, and constrained by an outer shell. It does not promote that
proxy into true F-16C manufacturer geometry, true internal equipment
boundaries, true Pk, or weapon-specific lethality.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| F-16 visual asset | active candidate | Sketchfab CC-BY-4.0 GLB is in the registry | Runtime visualization only; not a per-frame collision mesh |
| F-16 audit asset | active candidate | glTF source package, extracted files, hashes, and attribution are retained | Supports outer-shape review, not true internal component boundaries |
| Old FlightGear F-16 | rejected for mainline derivation | Archived under `assets/archive`; strong GPLv2 FlightGear source candidate | Must not enter mainline derived geometry |
| Current hitboxes | known gap | The issue records 4 m nose-aspect near miss with no component damage | Must not be treated as true outer shape or true component layout |
| Geometry acceptance | accepted / retained | [archive/tg_f16c_fine_geometry_accepted_20260614/target_geometry_acceptance_20260614.md](archive/tg_f16c_fine_geometry_accepted_20260614/target_geometry_acceptance_20260614.md) | Accepts only the F-16C fine-geometry engineering proxy; not default runtime replacement, training benefit, structural breakup, debris, Pk, or weapon-specific conclusions |
| Downstream opt-in proxy | retained handoff evidence | TG-P7-R1 through R6 generated the opt-in proxy database, trace, and training-comparison artifacts | Not a closure gate for this subproject; the default database and main projection path remain the control path |

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
| `P7 Runtime Interface Decision` | Decide whether the outer proxy enters near-fuze projection. | P6 proxy passes review or is explicitly held. | A tested runtime integration or held decision exists. | retained downstream handoff; not a geometry closure gate |

## Task Clusters

- Task cluster plan:
  [missile_lethality_target_geometry_task_clusters_20260611.md](missile_lethality_target_geometry_task_clusters_20260611.md)
- Current status:
  [missile_lethality_target_geometry_current_status_20260611.md](missile_lethality_target_geometry_current_status_20260611.md)
- Geometry acceptance closeout:
  [archive/tg_f16c_fine_geometry_accepted_20260614/target_geometry_acceptance_20260614.md](archive/tg_f16c_fine_geometry_accepted_20260614/target_geometry_acceptance_20260614.md)
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
- Cross-region ownership split candidate:
  [cross_region_ownership_split_results_20260613.md](cross_region_ownership_split_results_20260613.md)
- Runtime activation candidate:
  [target_geometry_runtime_activation_results_20260613.md](target_geometry_runtime_activation_results_20260613.md)
- Runtime behavior regression:
  [target_geometry_runtime_behavior_regression_results_20260613.md](target_geometry_runtime_behavior_regression_results_20260613.md)
- Training proxy database:
  [target_geometry_training_proxy_results_20260613.md](target_geometry_training_proxy_results_20260613.md)
- Active training probe:
  [target_geometry_training_probe_results_20260614.md](target_geometry_training_probe_results_20260614.md)
- Damage-event trace:
  [target_geometry_damage_event_trace_results_20260614.md](target_geometry_damage_event_trace_results_20260614.md)
- 32k opt-in training probe:
  [target_geometry_training_probe_32k_results_20260614.md](target_geometry_training_probe_32k_results_20260614.md)
- Whole-airframe projected mesh contour containment (tooling upgrade):
  [whole_airframe_contour_containment_results_20260614.md](whole_airframe_contour_containment_results_20260614.md)
  ([Chinese canonical](whole_airframe_contour_containment_results_20260614.zh.md))

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
- Retired three-view drafts: the old current-packet draft SVGs were removed
  during final-result contraction. Use
  [scene.html](review_packets/f16c_20260611/scene.html) and
  [whole_airframe_contour_dashboard.html](review_packets/f16c_20260611/whole_airframe_contour_dashboard.html)
  as the current visual entrypoints.
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
  [fine_geometry_proxy_candidate_20260611.json](review_packets/f16c_20260611/fine_geometry_proxy_candidate_20260611.json).
  TG-P6-R3 generated top/side/front convex hull silhouettes from `13,415`
  audit glTF vertices for all `14` review-only proxies. Nose, canopy, wing, and
  horizontal-tail regions are corrected against audit-mesh placement and use
  explicit source-node whitelists. `inflated_fallback_count=0`; missing vertices
  now fail review instead of expanding the region bounds.
- Retired human review dashboard:
  TG-P6-R4 added per-region cards with local top/side/front zooms, component
  overlays, mesh-node selection strategy, disabled fallback policy, hull point
  counts, review flags, and candidate/review status. This was an intermediate
  QA surface and is no longer a current result entrypoint after final-result
  contraction.
- Surface component candidates:
  [surface_component_candidate_20260611.json](review_packets/f16c_20260611/surface_component_candidate_20260611.json),
  [surface_component_candidate_20260611.csv](review_packets/f16c_20260611/surface_component_candidate_20260611.csv).
  TG-P6-R5 turns the `14` outer regions into review-only surface components and
  lists which current internal components each surface may hand off to. After
  R11, `0` surface components need human review, `0` runtime receiver links are
  missing, `0` surface rows are blocked by side-sign mismatch, and `8` carry
  cross-region semantic holds/candidates.
- Retired visual human-review triage:
  TG-P6-R6 grouped the manual-review queue into visual cards for coordinate-sign,
  component-placement, surface-handoff, and review-point sanity issues. Each card
  states the review question, what to look at, and the decision needed, then
  shows local top/side/front overlays so review no longer depends on reading CSV
  rows by eye. This intermediate HTML view is no longer a current result
  entrypoint.
- Semantic damage geometry candidates:
  [semantic_damage_geometry_candidate_20260611.json](review_packets/f16c_20260611/semantic_damage_geometry_candidate_20260611.json),
  [semantic_damage_geometry_candidate_20260611.csv](review_packets/f16c_20260611/semantic_damage_geometry_candidate_20260611.csv).
  TG-P6-R12 emits `14` semantic outer-shell volume components and `14`
  `runtime_component_json_candidate` records. The runtime schema and loader now
  parse the geometry fields, but `runtime_active_component_count=0`; active
  lethality behavior is unchanged until `TG-P7`.
- Internal receiver prior geometry candidates:
  [internal_component_prior_candidate_20260611.json](review_packets/f16c_20260611/internal_component_prior_candidate_20260611.json),
  [internal_component_prior_candidate_20260611.csv](review_packets/f16c_20260611/internal_component_prior_candidate_20260611.csv).
  TG-P6-R13 generates sphere/cylinder/capsule/ellipsoid priors for all `26`
  current receivers and constrains them by parent shell support bounds or
  cross-region unions. `post_constraint_outside_count=0`,
  `cross_region_held_prior_count=2`, and `runtime_active_component_count=0`.
  The generated HTML/SVG pages are raw intermediate evidence, not current result
  entrypoints.
- Semantic parent-child component layout:
  [semantic_parent_child_layout_candidate_20260611.json](review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.json),
  [semantic_parent_child_layout_candidate_20260611.csv](review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.csv).
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
  The generated HTML/SVG pages are raw intermediate evidence, not current result
  entrypoints.
- Cross-region ownership split candidates:
  [cross_region_ownership_split_candidate_20260611.json](review_packets/f16c_20260611/cross_region_ownership_split_candidate_20260611.json),
  [cross_region_ownership_split_candidate_20260611.csv](review_packets/f16c_20260611/cross_region_ownership_split_candidate_20260611.csv),
  [cross_region_ownership_split_results_20260613.md](cross_region_ownership_split_results_20260613.md).
  TG-P6-R22 proposes parent receiver retirement decisions for `engine_core` and
  `wing_spar_center` and emits `8` parse-ready split receiver candidates. The
  payloads remain AABB fallback records, `runtime_active_split_component_count=0`,
  and ownership acceptance remains false.
- TG-P7 runtime activation candidate:
  [target_geometry_runtime_activation_candidate_20260613.json](review_packets/f16c_20260611/target_geometry_runtime_activation_candidate_20260613.json),
  [target_geometry_runtime_activation_candidate_20260613.csv](review_packets/f16c_20260611/target_geometry_runtime_activation_candidate_20260613.csv),
  [target_geometry_runtime_activation_results_20260613.md](target_geometry_runtime_activation_results_20260613.md).
  TG-P7-R1 converts the R22 split payload into a unit-database component patch
  candidate for `F-16C_Block50.damage_model.hitboxes[].components`:
  `candidate_component_count=8`,
  `runtime_schema_parse_ready_component_count=8`,
  `unit_database_patch_component_count=8`,
  `parent_receiver_retirement_candidate_count=2`, and
  `runtime_active_component_count=0`; the C++ unit-definition loader smoke test
  parses the same split receiver geometry shape.
- TG-P7 runtime behavior regression:
  [target_geometry_runtime_behavior_regression_20260613.json](review_packets/f16c_20260611/target_geometry_runtime_behavior_regression_20260613.json),
  [target_geometry_runtime_behavior_regression_20260613.csv](review_packets/f16c_20260611/target_geometry_runtime_behavior_regression_20260613.csv),
  [target_geometry_runtime_behavior_regression_results_20260613.md](target_geometry_runtime_behavior_regression_results_20260613.md).
  TG-P7-R2 applies the component patch in memory only: base components `26`,
  projected components `32`, retired parent components `2`, split additions
  `8`, duplicate component names `0`, and `behavior_regression_pass=true`.
- TG-P7 training proxy database:
  [target_geometry_training_proxy_database_20260613.json](review_packets/f16c_20260611/target_geometry_training_proxy_database_20260613.json),
  [target_geometry_training_proxy_database_20260613/](review_packets/f16c_20260611/target_geometry_training_proxy_database_20260613/),
  [target_geometry_training_proxy_results_20260613.md](target_geometry_training_proxy_results_20260613.md).
  TG-P7-R3 materializes a full opt-in proxy runtime database with `32`
  F-16 components, keeps the default database at `26`, wires
  `runtime.database_path` through training bootstrap and `train.py`, and adds an
  active world-batch probe config for `A2_TARGET_GEOMETRY_PROXY_F16C_R22`. A
  local `64`-step CPU world-batch smoke completed against that proxy path.
- TG-P7 active training probe:
  [target_geometry_training_probe_results_20260614.md](target_geometry_training_probe_results_20260614.md).
  TG-P7-R4 runs the active `8192`-step CUDA world-batch proxy probe and the
  matching default-database baseline. Both finish and write checkpoints; the
  proxy run selects `target_geometry_training_proxy_database_20260613`, while
  the baseline remains on the default database.
- TG-P7 damage-event trace:
  [target_geometry_damage_event_trace_20260614.json](review_packets/f16c_20260611/target_geometry_damage_event_trace_20260614.json),
  [target_geometry_damage_event_trace_results_20260614.md](target_geometry_damage_event_trace_results_20260614.md).
  TG-P7-R5 applies fixed synthetic blast-fragmentation debug hits against the
  default and proxy databases. The proxy event surface observes all `8` split
  receivers, the default event surface observes `0` split receiver names, and
  proxy events do not fall back to retired parent receiver names.
- TG-P7 32k opt-in training probe:
  [target_geometry_training_probe_32k_20260614.json](review_packets/f16c_20260611/target_geometry_training_probe_32k_20260614.json),
  [target_geometry_training_probe_32k_results_20260614.md](target_geometry_training_probe_32k_results_20260614.md).
  TG-P7-R6 adds 32k proxy/baseline active configs and completes two
  `32768`-step CUDA `WorldBatchVecEnv` runs. The proxy run selects
  `target_geometry_training_proxy_database_20260613` through
  `runtime.database_path`, while the baseline run has no database override; both
  runs write four checkpoints plus a final model.
- Airframe silhouette constraint correction candidates:
  [airframe_constraint_correction_candidate_20260611.json](review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.json),
  [airframe_constraint_correction_candidate_20260611.csv](review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.csv).
  TG-P6-R16 checks all `34` receiver priors and held split segments as a raw
  shape-aware top/side/front whole-airframe silhouette diagnostic. The
  silhouette test was since upgraded to a whole-airframe projected mesh contour
  with shape-aware projected sampling (see the whole-airframe contour containment
  entry below). After the R22 thin-prism/frustum shape corrections the packet
  now records `silhouette_exposure_item_count=0`,
  `center_shift_reduces_item_count=0`, `size_or_shape_review_item_count=0`, and
  `runtime_active_component_count=0`. Held split segments are no longer part of
  the final result surface; current containment is reported through the
  whole-airframe contour dashboard below.
- Whole-airframe projected mesh contour containment:
  [whole_airframe_contour_containment_20260614.json](review_packets/f16c_20260611/whole_airframe_contour_containment_20260614.json),
  [whole_airframe_contour_containment_20260614.csv](review_packets/f16c_20260611/whole_airframe_contour_containment_20260614.csv),
  [whole_airframe_contour_top.svg](review_packets/f16c_20260611/whole_airframe_contour_top.svg),
  [whole_airframe_contour_side.svg](review_packets/f16c_20260611/whole_airframe_contour_side.svg),
  [whole_airframe_contour_front.svg](review_packets/f16c_20260611/whole_airframe_contour_front.svg),
  [whole_airframe_contour_dashboard.html](review_packets/f16c_20260611/whole_airframe_contour_dashboard.html),
  [whole_airframe_contour_containment_results_20260614.md](whole_airframe_contour_containment_results_20260614.md).
  Upgrades the silhouette-containment test from a per-region convex-hull
  union with sparse 9-point sampling to per-view projected audit-mesh triangle
  union over `4504` glTF triangles with shape-aware projected sampling and a
  `0.05 m` engineering review margin. The final result surface contains only
  the `26` current receiver priors, excludes the `8` review-only held split
  segments, and records `0` items exceeding tolerance
  (`max_outside_distance_m=0.0`).
- Subcomponent shape-placement candidates:
  [subcomponent_shape_placement_candidate_20260611.json](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json),
  [subcomponent_shape_placement_candidate_20260611.csv](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.csv).
  TG-P6-R17 generated candidate shape families and placement candidates for the
  `14` R16 exposed subcomponents while preserving nominal dimensions. TG-P6-R18
  promotes the first `4` zero-exposure candidates into review-only
  prior/held-segment generation rules; TG-P6-R19 adds local centerline
  candidates; TG-P6-R20 resolves the remaining radar and cockpit placement
  issues. TG-P6-R21 promotes the latest accepted placements into the
  review-only generation rules. After the R22 thin-prism/frustum shape
  corrections the source exposure queue is empty, so the packet now records
  `shape_placement_candidate_count=0`,
  `source_silhouette_exposure_item_count=0`, and
  `runtime_active_component_count=0`.
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
  held-segment generation rules. At the R21 promotion snapshot, counts were
  `internal_component_prior_shape_promotion_count=9`,
  `cross_region_held_segment_shape_promotion_count=5`, and
  `subcomponent_shape_placement_candidate_count=0`; the later whole-airframe
  projected mesh contour diagnostic supersedes the current containment queue and
  records `10` review-only follow-up candidates.
- Cross-region ownership split results:
  [cross_region_ownership_split_results_20260613.md](cross_region_ownership_split_results_20260613.md).
  TG-P6-R22 turns the two remaining ownership blockers into explicit accept /
  reject / keep-held decisions before `TG-P7`; parent receiver retirement and
  runtime activation remain unaccepted.
- Runtime activation candidate results:
  [target_geometry_runtime_activation_results_20260613.md](target_geometry_runtime_activation_results_20260613.md).
  TG-P7-R1 creates a feature-flagged patch candidate with `8` parse-ready split
  receiver records; the repository unit database is not modified and behavior
  regression is still required before activation.
- Runtime behavior regression results:
  [target_geometry_runtime_behavior_regression_results_20260613.md](target_geometry_runtime_behavior_regression_results_20260613.md).
  TG-P7-R2 corrects the patch target to
  `damage_model.hitboxes[].components` and verifies the parent-retirement plus
  split-addition projection in memory.
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
- `.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/tools/test_airframe_geometry_manifest.py tests/tools/test_airframe_geometry_review_cli.py`: `5 passed`.
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
- Every semantic outer-shell volume candidate has an isolated top/side/front
  review view and an explicit direct-vs-cross-region receiver handoff status.
- Every current internal/system receiver has prior geometry, parent shell
  constraints, pre/post protrusion fractions, and isolated top/side/front review
  views; this layer must not be treated as true internal engineering geometry.
- The semantic parent-child layout, cross-region held segments, R22 split
  receiver candidates, whole-airframe silhouette constraints, and subcomponent
  placement repairs form traceable handoff evidence.
- The TG-P7 opt-in proxy database, damage-event trace, and 32k proxy/baseline
  training probe are retained only as downstream handoff evidence; they are no
  longer closure gates for this subproject.
- The 4 m nose close-to-shape case is explained as a concrete geometry,
  direction, or candidate-component issue instead of an unexplained zero-damage
  result.
- Docs continue to reject true F-16 engineering geometry, true Pk, structural
  breakup, debris/wreck, or weapon-specific kill claims.

## Residuals And Next Steps

- MQ-9 geometry is a later reuse target; the first round is F-16 only.
- Runtime near-fuze projection still does not consume the proxy in the default
  F-16 unit damage model; default-path replacement is a later standalone
  acceptance decision, not a closure gate for this geometry subproject.
  TG-P7-R6 provides an opt-in training proxy database
  with `8` event-observable split receiver records and a default-path control
  that remains at `26` components; local `64`-step training smoke, active
  `8192`-step proxy/baseline probes, targeted damage-event trace, and
  `32768`-step proxy/baseline probes pass. These artifacts are retained as
  downstream handoff evidence.
- Structural breakup, wreck/debris, and Pk remain separate future subprojects.

## Archive

Current geometry acceptance package:
[archive/tg_f16c_fine_geometry_accepted_20260614/README.md](archive/tg_f16c_fine_geometry_accepted_20260614/README.md).

Archive index: [archive/README.md](archive/README.md). The
`review_packets/f16c_20260611/` path remains a stable retained evidence surface
for maintained tools, tests, and opt-in configs.
