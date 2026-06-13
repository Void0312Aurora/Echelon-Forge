# A2 Target Geometry Current Status

Status: `2026-06-13` TG-P7-R3 opt-in training proxy database passes; default
runtime projection and the maintained F-16 unit database remain unchanged. The
parent entry and issue have moved F-16 geometry
refinement from issue tracking into an executable subproject; the first
source/axis/scale manifest, outer-region candidate, component-binding report,
offline review page, test-point distance diagnostics, fine-proxy candidate
packet with mesh-derived silhouettes, a per-region review dashboard, the
surface-component handoff table, visual human-review triage page, isolated
component views, first visual findings record, independent subagent findings,
R10 correction snapshot, R11 repair result, R12 semantic damage geometry
candidate packet, R13 internal receiver prior constraint packet, R18
subcomponent shape promotion packet, R19 subcomponent centerline placement
packet, R20 latest subcomponent placement packet, R21 latest subcomponent
promotion packet, R22 cross-region ownership split candidate packet,
TG-P7-R1 runtime activation candidate packet, TG-P7-R2 runtime behavior
regression packet, and TG-P7-R3 training proxy database packet are
generated. The latest packet has repaired side-sign
mapping, runtime receiver components, wing component placement, radar/IFF, and
nozzle source boxes; it now emits parse-ready semantic outer-shell volume
component candidates, constrained internal receiver priors, promoted
review-only subcomponent shape rules, local centerline placement candidates,
latest subcomponent placement candidates, promoted R21 latest placement rules,
R22 parse-ready split receiver candidates, a TG-P7-R1 feature-flagged
`damage_model.hitboxes[].components` patch candidate, a TG-P7-R2 in-memory
behavior regression, and a TG-P7-R3 opt-in proxy runtime database, but default
active runtime projection remains unchanged.

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
| TG-P3 component binding | [component_binding_report_20260611.json](review_packets/f16c_20260611/component_binding_report_20260611.json), [component_binding_report_20260611.csv](review_packets/f16c_20260611/component_binding_report_20260611.csv) | After the R11 repair, `26` of `26` components are bound, `0` remain `needs_review`, `0` remain side-sign blockers, `2` are review-only cross-region semantics, and `0` are geometry-review-required bad boxes |
| TG-P5 distance diagnostics | [review_point_diagnostics_20260611.json](review_packets/f16c_20260611/review_point_diagnostics_20260611.json), [review_point_diagnostics_20260611.csv](review_packets/f16c_20260611/review_point_diagnostics_20260611.csv) | Covers `10` review points; `2` are inside corrected outer regions; `nose_axis_4m` is `0.125 m` from `dedicated_canopy_surface_component` with `7` candidate components |
| TG-P6 design draft | [fine_geometry_proxy_design_20260611.md](fine_geometry_proxy_design_20260611.md) | Defines the order for moving from boxes to oriented boxes, thin prisms, convex hulls, and simplified shell meshes |
| TG-P6 mesh-derived fine-proxy silhouettes | [fine_geometry_proxy_candidate_20260611.json](review_packets/f16c_20260611/fine_geometry_proxy_candidate_20260611.json), [fine_proxy_top.svg](review_packets/f16c_20260611/fine_proxy_top.svg), [fine_proxy_side.svg](review_packets/f16c_20260611/fine_proxy_side.svg), [fine_proxy_front.svg](review_packets/f16c_20260611/fine_proxy_front.svg) | Generated `14` review-only proxies with top/side/front convex hull silhouettes from `13,415` audit glTF vertices; nose, canopy, wing, and horizontal-tail regions now use audit-mesh placement and source-node whitelists; `inflated_fallback_count=0`, support volume ratio is `0.55404` |
| TG-P6 human review dashboard | [fine_proxy_review_dashboard.html](review_packets/f16c_20260611/fine_proxy_review_dashboard.html) | Per-region cards show local top/side/front views with source bounds, support bounds, mesh silhouette, component boxes, node-selection strategy, disabled fallback policy, flags, and candidate/review status |
| TG-P6 surface component candidates | [surface_component_candidate_20260611.json](review_packets/f16c_20260611/surface_component_candidate_20260611.json), [surface_component_candidate_20260611.csv](review_packets/f16c_20260611/surface_component_candidate_20260611.csv) | The `14` outer regions now have review-only surface components; `0` need human review, `0` runtime receiver links remain missing, `0` surfaces are blocked by side-sign mismatch, and `8` carry cross-region semantic holds/candidates |
| TG-P6 visual triage | [human_review_triage.html](review_packets/f16c_20260611/human_review_triage.html) | Groups review items by coordinate sign, component placement, surface handoff, and review-point sanity; each item states the review question, what to inspect, and the decision needed before showing local top/side/front overlays |
| TG-P6 isolated component review views | [component_review_views/index.html](review_packets/f16c_20260611/component_review_views/index.html), [component_review_views/manifest.json](review_packets/f16c_20260611/component_review_views/manifest.json) | Regenerated `75` isolated pages with top/side/front SVGs: `26` components, `29` surface handoffs, and `20` review-point candidates; subagents can review by group without crowded overlays |
| TG-P6 semantic damage geometry candidates | [semantic_damage_geometry_candidate_20260611.json](review_packets/f16c_20260611/semantic_damage_geometry_candidate_20260611.json), [semantic_damage_geometry_candidate_20260611.csv](review_packets/f16c_20260611/semantic_damage_geometry_candidate_20260611.csv), [semantic_damage_geometry_views/index.html](review_packets/f16c_20260611/semantic_damage_geometry_views/index.html) | R12 emits `14` semantic outer-shell volume candidates and `14` `runtime_component_json_candidate` records; runtime schema/loader can parse the geometry fields, `8` handoffs remain cross-region held, and `runtime_active_component_count=0` |
| TG-P6 internal receiver prior geometry | [internal_component_prior_candidate_20260611.json](review_packets/f16c_20260611/internal_component_prior_candidate_20260611.json), [internal_component_prior_candidate_20260611.csv](review_packets/f16c_20260611/internal_component_prior_candidate_20260611.csv), [internal_component_prior_views/index.html](review_packets/f16c_20260611/internal_component_prior_views/index.html), [manifest](review_packets/f16c_20260611/internal_component_prior_views/manifest.json) | R13 generates sphere/cylinder/capsule/ellipsoid priors for all `26` current receivers and constrains them by parent shell support bounds or cross-region unions; `post_constraint_outside_count=0`, `cross_region_held_prior_count=2`, `runtime_active_component_count=0`; current entrypoints are HTML/SVG pages plus manifest |
| TG-P6 semantic parent-child layout | [semantic_parent_child_layout_candidate_20260611.json](review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.json), [semantic_parent_child_layout_candidate_20260611.csv](review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.csv), [semantic_parent_child_layout_views/index.html](review_packets/f16c_20260611/semantic_parent_child_layout_views/index.html), [manifest](review_packets/f16c_20260611/semantic_parent_child_layout_views/manifest.json) | R14 makes the `14` parent shell parts the primary review views and overlays all `26` receiver priors on their parent pages; R15 draws cross-region held receivers as split red segments instead of monolithic held blocks; current entrypoints are HTML/SVG pages plus manifest |
| TG-P6 cross-region held segment split | [cross_region_held_component_segments_20260611.json](review_packets/f16c_20260611/cross_region_held_component_segments_20260611.json), [cross_region_held_component_segments_20260611.csv](review_packets/f16c_20260611/cross_region_held_component_segments_20260611.csv), [semantic_parent_child_layout_views/index.html](review_packets/f16c_20260611/semantic_parent_child_layout_views/index.html) | R15 splits `engine_core` into `3` review-only engine segments and `wing_spar_center` into `5` review-only spar segments; `held_segment_count=8`, `outside_whole_airframe_segment_count=0`, `runtime_active_segment_count=0`, and cross-region ownership remains held |
| TG-P6 cross-region ownership split candidates | [cross_region_ownership_split_candidate_20260611.json](review_packets/f16c_20260611/cross_region_ownership_split_candidate_20260611.json), [cross_region_ownership_split_candidate_20260611.csv](review_packets/f16c_20260611/cross_region_ownership_split_candidate_20260611.csv), [scene.html](review_packets/f16c_20260611/scene.html) | R22 proposes retiring the parent `engine_core` and `wing_spar_center` receivers only if their `8` split receiver candidates are explicitly accepted and tested; `runtime_parse_ready_split_candidate_count=8`, `runtime_active_split_component_count=0`, and ownership acceptance remains false |
| TG-P6 airframe constraint correction candidates | [airframe_constraint_correction_candidate_20260611.json](review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.json), [airframe_constraint_correction_candidate_20260611.csv](review_packets/f16c_20260611/airframe_constraint_correction_candidate_20260611.csv), [overview_latest_triptych.svg](review_packets/f16c_20260611/subcomponent_shape_placement_views/overview_latest_triptych.svg) | R16/R18 checks all `34` receiver priors / held split segments against shape-aware top/side/front whole-airframe silhouettes; after R21 latest placement promotion, `silhouette_exposure_item_count=0`, `size_or_shape_review_item_count=0`, and `runtime_active_component_count=0` |
| TG-P6 subcomponent shape-placement candidates | [subcomponent_shape_placement_candidate_20260611.json](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.json), [subcomponent_shape_placement_candidate_20260611.csv](review_packets/f16c_20260611/subcomponent_shape_placement_candidate_20260611.csv), [subcomponent_shape_placement_views/index.html](review_packets/f16c_20260611/subcomponent_shape_placement_views/index.html) | R17 creates nominal-dimension-preserving candidate shape families; R18 promotes the first `4` zero-exposure candidates; R19 adds local centerline candidates; R20 resolves the radar/cockpit leftovers; R21 promotes the accepted latest placements into review-only rules, leaving `subcomponent_shape_placement_candidate_count=0` and `latest_candidate_total_outside_sample_count=0` |
| TG-P6 human review findings | [human_review_findings_20260612.md](human_review_findings_20260612.md) | R7 historical snapshot: side-sign convention, nose radar/IFF boxes, engine/nozzle boxes, and surface-to-runtime-component handoff blocked `TG-P7` before R9/R10 refinement and R11 repair |
| TG-P6 independent subagent findings | [subagent_independent_review_findings_20260612.md](subagent_independent_review_findings_20260612.md) | Five read-only group reviews are complete; the R9 snapshot refined `engine_core` and `wing_spar_center` into cross-region semantic holds or conditional candidates and identified side-sign, radar/IFF, afterburner/nozzle, and missing runtime relations as repair targets |
| TG-P6 subagent correction results | [subagent_correction_results_20260612.md](subagent_correction_results_20260612.md) | R10 historical snapshot: two write-scoped subagents repaired `apg68_radar_array`, `iff_interrogator`, and `afterburner_nozzle`, added cross-region review semantics, and regenerated the packet; the remaining R10 side-sign and missing-receiver blockers are superseded by R11 |
| TG-P6 geometry repair results | [geometry_repair_results_20260612.md](geometry_repair_results_20260612.md) | R11 repaired left/right region mapping, wing and wing-root component placement, explicit canopy/intake/horizontal-tail receivers, and direct surface handoff rules; component and surface `needs_review` counts are now `0` |
| TG-P6 semantic damage geometry implementation | [semantic_damage_geometry_results_20260612.md](semantic_damage_geometry_results_20260612.md) | R12 adds semantic volume candidate generation, isolated semantic volume review pages, and runtime component geometry schema parsing while keeping active runtime behavior held |
| TG-P6 internal component prior implementation | [internal_component_prior_results_20260612.md](internal_component_prior_results_20260612.md) | R13 adds simple-shape internal receiver priors, shell constraints, and isolated review pages; this layer is review-only and not true internal engineering geometry |
| TG-P6 semantic parent-child layout implementation | [semantic_parent_child_layout_results_20260612.md](semantic_parent_child_layout_results_20260612.md) | R14 adds the `14` parent geometry part review surface and shows the `12` extra receiver slots as child overlays instead of independent top-level review views |
| TG-P6 cross-region held segment implementation | [cross_region_held_segment_results_20260612.md](cross_region_held_segment_results_20260612.md) | R15 splits the two red held receivers into smaller owner-region segments for visual review while keeping runtime activation and ownership acceptance false |
| TG-P6 airframe constraint correction implementation | [airframe_constraint_correction_results_20260612.md](airframe_constraint_correction_results_20260612.md) | R16 adds shape-aware whole-airframe silhouette diagnostics and center-shift candidates before applying further size/shape corrections |
| TG-P6 subcomponent shape-placement implementation | [subcomponent_shape_placement_results_20260613.md](subcomponent_shape_placement_results_20260613.md) | R17 adds candidate shape families and three-view review pages for the `14` still-exposed subcomponents while preserving nominal dimensions and keeping unresolved items held for true-size, tapered/cross-section, or cross-region centerline modeling |
| TG-P6 subcomponent shape promotion implementation | [subcomponent_shape_promotion_results_20260613.md](subcomponent_shape_promotion_results_20260613.md) | R18 promotes `iff_interrogator`, `inertial_navigation_unit`, `engine_core_afterburner_segment`, and `engine_core_hot_section_segment` into review-only generation rules; remaining shape-placement review items are `10` and runtime activation remains `0` |
| TG-P6 subcomponent centerline placement implementation | [subcomponent_centerline_placement_results_20260613.md](subcomponent_centerline_placement_results_20260613.md) | R19 adds dimension-preserving local centerline candidates for the `10` remaining shape-placement items; `8` clear sampled exposure and `2` remain unresolved |
| TG-P6 latest subcomponent placement implementation | [subcomponent_latest_placement_results_20260613.md](subcomponent_latest_placement_results_20260613.md) | R20 resolves the radar and cockpit leftovers and changes the main review legend to only gray whole-airframe wireframe plus blue latest subcomponent candidate |
| TG-P6 latest subcomponent promotion implementation | [subcomponent_latest_promotion_results_20260613.md](subcomponent_latest_promotion_results_20260613.md) | R21 promotes the latest accepted placements into review-only prior and held-segment generation rules: `internal_component_prior_shape_promotion_count=9`, `cross_region_held_segment_shape_promotion_count=5`, `airframe_constraint_silhouette_exposure_item_count=0`, and runtime activation remains `0` |
| TG-P6 cross-region ownership split implementation | [cross_region_ownership_split_results_20260613.md](cross_region_ownership_split_results_20260613.md) | R22 emits review-only ownership decisions and parse-ready AABB fallback split receiver records for the two remaining cross-region held parents; parent receiver retirement and runtime activation remain unaccepted |
| TG-P7 runtime activation candidate implementation | [target_geometry_runtime_activation_results_20260613.md](target_geometry_runtime_activation_results_20260613.md), [target_geometry_runtime_activation_candidate_20260613.json](review_packets/f16c_20260611/target_geometry_runtime_activation_candidate_20260613.json), [target_geometry_runtime_activation_candidate_20260613.csv](review_packets/f16c_20260611/target_geometry_runtime_activation_candidate_20260613.csv) | TG-P7-R1 converts the R22 split payload into a feature-flagged `damage_model.hitboxes[].components` patch candidate: `candidate_component_count=8`, `runtime_schema_parse_ready_component_count=8`, `unit_database_patch_component_count=8`, `parent_receiver_retirement_candidate_count=2`, `runtime_active_component_count=0`, and C++ unit-definition loader parse smoke passes |
| TG-P7 runtime behavior regression implementation | [target_geometry_runtime_behavior_regression_results_20260613.md](target_geometry_runtime_behavior_regression_results_20260613.md), [target_geometry_runtime_behavior_regression_20260613.json](review_packets/f16c_20260611/target_geometry_runtime_behavior_regression_20260613.json), [target_geometry_runtime_behavior_regression_20260613.csv](review_packets/f16c_20260611/target_geometry_runtime_behavior_regression_20260613.csv) | TG-P7-R2 applies the component patch in memory only and verifies `base_component_count=26`, `projected_component_count=32`, `retired_parent_component_count=2`, `split_component_added_count=8`, `duplicate_component_name_count=0`, and `behavior_regression_pass=true` |
| TG-P7 training proxy database implementation | [target_geometry_training_proxy_results_20260613.md](target_geometry_training_proxy_results_20260613.md), [target_geometry_training_proxy_database_20260613.json](review_packets/f16c_20260611/target_geometry_training_proxy_database_20260613.json), [target_geometry_training_proxy_database_20260613/](review_packets/f16c_20260611/target_geometry_training_proxy_database_20260613/) | TG-P7-R3 materializes a full opt-in proxy runtime database and active training config: default database components `26`, proxy database components `32`, split receivers active in proxy `8`, duplicate names `0`, `runtime.database_path` wired through training bootstrap and `train.py`, repository unit database modified `false`, RuntimeFacade proxy database load passes, and local `64`-step CPU training smoke completes |
| Stage-C guard alignment | [component_probability_surface_probe.py](../../../../../tools/maintenance/candidate_artifacts/component_probability_surface_probe.py) | The repaired beam-side component geometry now yields `surface_incidence_cos=0.0`; the Stage-C surface probe gate was synchronized so component-specific rows are selected instead of `global-fallback` |

## Current Boundary

- This status proves only that the TG-P1 source/scale manifest, TG-P2
  outer-region candidate, TG-P3 component-binding report, TG-P4 review packet,
  TG-P5 test-point distance diagnostics, and TG-P6 review-only mesh-derived
  fine proxy silhouettes plus surface component candidates, visual triage,
  isolated component review views, first visual findings, five subagent
  independent reviews, the first subagent correction pass, the R11 geometry
  repair, R12 semantic damage geometry candidate generation, R13 internal
  receiver prior constraint generation, R14 semantic parent-child layout, R15
  cross-region held segment split, R16 airframe silhouette diagnostics, R17
  shape-placement candidates, R18 zero-exposure shape promotion, R19
  centerline placement candidates, R20 latest placement candidates, R21
  latest placement promotion, R22 ownership split candidate packet, TG-P7-R1
  runtime activation candidate packet, TG-P7-R2 in-memory behavior
  regression packet, and TG-P7-R3 opt-in training proxy database packet are
  complete; it does not prove default runtime activation is applied.
- The Sketchfab model is an outer-review candidate, not a source of true
  internal component boundaries.
- The old FlightGear F-16 is archived as a strong GPLv2 source candidate and
  must not enter mainline derived geometry.
- Runtime near-fuze projection remains unchanged on the default path. TG-P7-R3
  makes the feature-flagged `damage_model.hitboxes[].components` projection
  selectable through `runtime.database_path`; the repository unit database is
  not modified, the default path remains at `26` components, and the proxy path
  has `32` components.

## Next Step

1. Run the maintained active 8k TG-P7 proxy probe.
2. Run the matching baseline world-batch probe.
3. Compare stability, event flow, and damage-component selection, with the
   proxy path at `32` components and the default path at `26`.

## Validation Reminder

Each round should at least run:

```bash
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry
```

Current focused test:

```bash
python -m py_compile tools/geometry/airframe_geometry_review.py python/training/bootstrap.py train.py tests/tools/test_airframe_geometry_review.py tests/training/test_training_bootstrap_contracts.py tests/training/test_air_combat_training_entry_contracts.py
pytest -q tests/tools/test_airframe_geometry_review.py
pytest -q tests/training/test_training_bootstrap_contracts.py tests/training/test_air_combat_training_entry_contracts.py
python tools/geometry/airframe_geometry_review.py --out docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611
cmake --build build-workshop --target ef_test -j2
./build-workshop/ef_test --test-suite=components_basic
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry tools/geometry/airframe_geometry_review.py python/training/bootstrap.py train.py tests/tools/test_airframe_geometry_review.py tests/training/test_training_bootstrap_contracts.py tests/training/test_air_combat_training_entry_contracts.py examples/config/training/active/air_combat
```

Broader runtime checks before any default-path replacement:

```bash
cmake --build build-workshop --target ef_test -j2
./build-workshop/ef_test --test-suite=components_basic
pytest -q tests/architecture/damage_model
```

Current TG-P7-R3 focused result: Python geometry review tests `2 passed`;
training bootstrap and entry contracts `28 passed`; C++ loader smoke `24
passed`; review packet regeneration completed; RuntimeFacade proxy database
load returned `runtime_load_ok=true`; local 64-step CPU proxy training smoke
completed and wrote `/tmp/cmo_tg_p7_proxy_train_smoke/tg_p7_proxy_train_smoke_64/final_model.zip`.
