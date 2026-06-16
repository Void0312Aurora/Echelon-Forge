# A2 TG F-16C Fine-Geometry Proxy Acceptance Record

Status: `2026-06-14` accepted. The acceptance gate is narrowed back to fine geometry modeling itself; TG-P7 runtime and training artifacts are retained only as downstream handoff evidence, not as closure requirements for this subproject.

## Acceptance Judgment

Conclusion: the F-16C fine-geometry engineering proxy in this subproject is closed and may be archived as a retained archive record.

This engineering proxy keeps an explicit evidence grade. It is suitable as an engineering proxy input for later near-fuze, continuous-rod, fragmentation, and component-handoff modeling; it is not a claim of true F-16C manufacturer geometry, true internal equipment boundaries, true Pk, or weapon-specific lethality.

## Acceptance Items

| Gate | Evidence | Judgment |
| --- | --- | --- |
| Source, scale, and axes are traceable | [manifest.json](../../review_packets/f16c_20260611/manifest.json) records the Sketchfab CC-BY-4.0 source, hashes, axis map, and public-dimension errors; scaled length error is `+0.09%`, wingspan `-3.37%`, height `-4.50%` | pass |
| Legacy hitbox gap is quantified | The manifest records current hitbox height error near `-75.41%` and retains the `26` legacy components plus `4` hitboxes as the baseline | pass |
| Outer regions and visualization exist | [f16c_geometry_mapping_candidate_20260611.json](../../review_packets/f16c_20260611/f16c_geometry_mapping_candidate_20260611.json), [scene.html](../../review_packets/f16c_20260611/scene.html), and three-view SVGs | pass |
| Legacy component binding is closed | [component_binding_report_20260611.json](../../review_packets/f16c_20260611/component_binding_report_20260611.json): `component_count=26`, `bound_component_count=26`, `needs_review_count=0`, `hard_blocker_count=0`, `geometry_review_required_count=0` | pass |
| Review-point distance diagnostics are closed | [review_point_diagnostics_20260611.json](../../review_packets/f16c_20260611/review_point_diagnostics_20260611.json): `review_point_count=10`, `zero_outer_distance_without_component_candidate_count=0`; `nose_axis_4m` has geometry and candidate-component explanation | pass |
| Fine proxy does not rely on inflated fallback | [fine_geometry_proxy_candidate_20260611.json](../../review_packets/f16c_20260611/fine_geometry_proxy_candidate_20260611.json): `proxy_count=14`, `mesh_derived_silhouette_count=14`, `mesh_source_vertex_count=13415`, `inflated_fallback_count=0`, `total_proxy_support_volume_ratio=0.55404` | pass |
| Surface component candidates are closed | [surface_component_candidate_20260611.json](../../review_packets/f16c_20260611/surface_component_candidate_20260611.json): `surface_component_count=14`, `needs_review_count=0`, `missing_existing_runtime_component_relation_count=0`, `side_sign_hard_blocker_count=0` | pass |
| Semantic shell-volume candidates are closed | [semantic_damage_geometry_candidate_20260611.json](../../review_packets/f16c_20260611/semantic_damage_geometry_candidate_20260611.json): `semantic_volume_component_count=14`, `runtime_parse_ready_component_count=14`, `runtime_active_component_count=0` | pass |
| Internal receiver priors are constrained | [internal_component_prior_candidate_20260611.json](../../review_packets/f16c_20260611/internal_component_prior_candidate_20260611.json): `internal_component_prior_count=26`, `constrained_inside_count=26`, `post_constraint_outside_count=0`, `shape_promotion_count=9` | pass |
| Parent-child layout and cross-region held records are reviewable | [semantic_parent_child_layout_candidate_20260611.json](../../review_packets/f16c_20260611/semantic_parent_child_layout_candidate_20260611.json), [cross_region_held_component_segments_20260611.json](../../review_packets/f16c_20260611/cross_region_held_component_segments_20260611.json): `parent_semantic_component_count=14`, `bound_receiver_component_count=26`, `held_segment_count=8`, `outside_whole_airframe_segment_count=0` | pass |
| R22 cross-region ownership candidates are handoff-ready | [cross_region_ownership_split_candidate_20260611.json](../../review_packets/f16c_20260611/cross_region_ownership_split_candidate_20260611.json): `parent_decision_count=2`, `split_receiver_candidate_count=8`, `runtime_parse_ready_split_candidate_count=8`, `runtime_active_split_component_count=0` | pass |
| Whole-airframe projected mesh diagnostic records follow-up protrusions without changing geometry acceptance | [whole_airframe_contour_containment_20260614.json](../../review_packets/f16c_20260611/whole_airframe_contour_containment_20260614.json), [whole_airframe_contour_containment_results_20260614.md](../../whole_airframe_contour_containment_results_20260614.md): `contour_method=projected_mesh_triangle_union`, `exceeds_tolerance_item_count=10`, `runtime_active_component_count=0`; these are retained review-only follow-up items, not a default runtime change or acceptance rollback | pass with retained follow-up |
| Final review evidence is concentrated | Whole-airframe projected mesh contour plus semantic volume, internal prior, parent-child, and follow-up placement views remain; the old `75`-page component-review intermediate packet is retired from the current result surface | pass |
| Focused tests pass | `.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests/tools/test_airframe_geometry_review.py` | pass, `5 passed` |
| Diff whitespace check passes | `git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry tools/geometry/airframe_geometry_review.py tests/tools/test_airframe_geometry_review.py` | pass, no output |

## Not Closure Gates

The following artifacts remain downstream handoff evidence and are no longer acceptance gates for fine geometry modeling:

- `target_geometry_runtime_activation_candidate_20260613.*`
- `target_geometry_runtime_behavior_regression_20260613.*`
- `target_geometry_training_proxy_database_20260613*`
- `target_geometry_damage_event_trace_20260614.json`
- `target_geometry_training_probe_32k_20260614.json`

They show that the split-receiver proxy can be consumed through an explicit opt-in path. They do not prove default-path replacement, policy/reward consumption, training benefit, target kill, or structural consequence.

## Archive Boundary

This subproject is closed here. Future default runtime replacement, policy/reward diagnostics, lethality probability, structural breakup, debris, Pk, or other-airframe reuse must enter separate or appropriate downstream subprojects instead of adding new acceptance gates to this geometry package.
