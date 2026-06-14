from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.geometry import airframe_geometry_review


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_f16_geometry_manifest_records_dual_model_axis_and_scale() -> None:
  manifest = airframe_geometry_review.build_airframe_geometry_manifest()
  aircraft = airframe_geometry_review._load_json( # noqa: SLF001
    airframe_geometry_review.DEFAULT_AIRCRAFT
  )

  assert manifest["schema_version"] == "a2.target_geometry_manifest.v1"
  assert manifest["status"] == "target_geometry_manifest_generated_review_only"
  assert manifest["asset_source_status"] == "verified_redistributable_visual_reference"
  assert manifest["source"]["uid"] == "4bc2ff75dc584af2afd0aa6bd8b79015"
  assert manifest["source"]["author"] == "Carlos.Maciel"
  assert manifest["source"]["license"]["url"] == "http://creativecommons.org/licenses/by/4.0/"
  assert "Canopy01_1" in manifest["source_geometry_hints"][
    "metadata_notable_node_names"
  ]
  assert "EngineL01_17" in manifest["source_geometry_hints"][
    "metadata_notable_node_names"
  ]

  paths = manifest["paths"]
  assert paths["runtime_visual_glb"].endswith(
    "assets/air/f16_c_falcon_carlos_maciel/f16_c_falcon_carlos_maciel.glb"
  )
  assert paths["audit_scene_gltf"].endswith(
    "assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf"
  )

  axis = manifest["axis_alignment"]
  assert axis["asset_x"] == "sim_right"
  assert axis["asset_y"] == "sim_up"
  assert axis["asset_z_negative"] == "sim_forward"
  assert axis["nose_direction"] == "negative_asset_z"
  assert axis["runtime_registry_scale"] == 1.65

  gltf = manifest["gltf_summary"]
  assert gltf["triangle_count"] == 4504
  assert gltf["position_accessor_vertex_count"] == 13415
  assert gltf["node_count"] >= 40
  assert gltf["mesh_node_bounds"][0]["node_name"].startswith("Object_")

  dimension_check = manifest["public_dimension_check"]
  assert dimension_check["public_dimensions"]["length_m"] == 15.06
  assert dimension_check["public_dimensions"]["wingspan_m"] == 9.96
  assert dimension_check["public_dimensions"]["height_m"] == 4.88
  assert abs(dimension_check["scaled_dimension_error_percent"]["length_m"]) < 1.0
  assert abs(dimension_check["scaled_dimension_error_percent"]["wingspan_m"]) < 5.0
  assert abs(dimension_check["scaled_dimension_error_percent"]["height_m"]) < 6.0

  damage_geometry = manifest["current_damage_geometry"]
  assert damage_geometry["summary"]["hitbox_count"] >= 4
  assert damage_geometry["summary"]["component_count"] > 10
  assert damage_geometry["public_dimension_error_percent"]["height_m"] < -70.0
  assert manifest["authority_boundary"]["runtime_collision_mesh"] is False
  assert manifest["authority_boundary"]["real_weapon_pk_authority"] is False

  mapping = airframe_geometry_review.build_geometry_mapping_candidate(manifest)
  report = airframe_geometry_review.build_component_binding_report(aircraft, mapping)
  diagnostics = airframe_geometry_review.build_review_point_diagnostics(mapping, report)
  fine_proxy = airframe_geometry_review.build_fine_geometry_proxy_candidate(
    mapping, diagnostics, manifest=manifest
  )
  surface_report = airframe_geometry_review.build_surface_component_candidate_report(
    mapping, fine_proxy, report
  )
  semantic_report = airframe_geometry_review.build_semantic_damage_geometry_candidate(
    mapping, fine_proxy, surface_report
  )
  internal_prior_report = (
    airframe_geometry_review.build_internal_component_prior_candidate(
      mapping, fine_proxy, report, surface_report
    )
  )
  held_segment_report = (
    airframe_geometry_review.build_cross_region_held_component_segments_report(
      mapping, fine_proxy, internal_prior_report
    )
  )
  airframe_constraint_report = (
    airframe_geometry_review.build_airframe_constraint_correction_candidate_report(
      mapping, fine_proxy, internal_prior_report, held_segment_report
    )
  )
  ownership_split_report = (
    airframe_geometry_review.build_cross_region_ownership_split_candidate_report(
      mapping,
      internal_prior_report,
      held_segment_report,
      airframe_constraint_report,
    )
  )
  runtime_activation_report = (
    airframe_geometry_review.build_target_geometry_runtime_activation_candidate_report(
      mapping,
      ownership_split_report,
      aircraft=aircraft,
    )
  )
  runtime_behavior_report = (
    airframe_geometry_review.build_target_geometry_runtime_behavior_regression_report(
      aircraft,
      runtime_activation_report,
    )
  )
  training_proxy_aircraft, training_proxy_operations = (
    airframe_geometry_review.build_target_geometry_training_proxy_unit_candidate(
      aircraft,
      runtime_activation_report,
    )
  )
  training_proxy_report = (
    airframe_geometry_review.build_target_geometry_training_proxy_database_report(
      aircraft,
      runtime_activation_report,
      runtime_behavior_report,
      proxy_database_dir=(
        airframe_geometry_review.DEFAULT_OUTPUT_DIR
        / "target_geometry_training_proxy_database_20260613"
      ),
    )
  )
  shape_placement_report = (
    airframe_geometry_review.build_subcomponent_shape_placement_candidate_report(
      mapping, fine_proxy, airframe_constraint_report
    )
  )
  parent_child_layout_report = (
    airframe_geometry_review.build_semantic_parent_child_layout_candidate(
      mapping, semantic_report, internal_prior_report, held_segment_report
    )
  )
  assert report["schema_version"] == "a2.target_geometry_component_binding_report.v1"
  assert report["status"] == "component_binding_report_generated_review_only"
  assert report["summary"]["component_count"] == 26
  assert report["summary"]["bound_component_count"] == 26
  assert report["summary"]["needs_review_count"] == 0
  assert report["summary"]["side_sign_review_count"] == 0
  assert report["summary"]["hard_blocker_count"] == 0
  assert report["summary"]["cross_region_semantic_candidate_count"] == 2
  assert report["summary"]["geometry_review_required_count"] == 0
  rows = {row["component_name"]: row for row in report["rows"]}
  assert rows["apg68_radar_array"]["bound_region_id"] == "nose_radome"
  assert rows["apg68_radar_array"]["review_status"] == "candidate_binding"
  assert rows["cockpit_crew_station"]["bound_region_id"] in {
    "nose_radome",
    "forward_fuselage",
  }
  assert rows["engine_core"]["bound_region_id"] == "aft_fuselage_engine"
  assert rows["engine_core"]["review_status"] == (
    "review_only_cross_region_boundary_candidate"
  )
  assert rows["engine_core"]["review_semantics"] == (
    "cross_region_boundary_candidate_review_only"
  )
  assert "low_outer_region_overlap" in rows["engine_core"]["geometry_observations"]
  assert "low_outer_region_overlap" in rows["engine_core"]["suppressed_anomalies"]
  assert rows["wing_spar_center"]["review_status"] == (
    "review_only_cross_region_semantic_hold"
  )
  assert rows["wing_spar_center"]["review_semantics"] == (
    "cross_region_structural_semantic_hold"
  )
  assert "low_outer_region_overlap" in rows["wing_spar_center"][
    "geometry_observations"
  ]
  assert "low_outer_region_overlap" in rows["wing_spar_center"][
    "suppressed_anomalies"
  ]
  assert rows["afterburner_nozzle"]["bound_region_id"] == "engine_nozzle"
  assert rows["afterburner_nozzle"]["blocked_region_binding"]["blocked"] is False
  assert rows["dedicated_canopy_surface_component"]["bound_region_id"] == "canopy"
  assert rows["dedicated_intake_lip_or_duct_component"]["bound_region_id"] == "intake"
  assert rows["left_horizontal_tail_actuator_or_surface_component"][
    "bound_region_id"
  ] == "left_horizontal_tail"
  assert rows["right_horizontal_tail_actuator_or_surface_component"][
    "bound_region_id"
  ] == "right_horizontal_tail"
  assert rows["left_wing_fuel_cell"]["bound_region_id"] == "left_wing"
  assert rows["right_wing_fuel_cell"]["bound_region_id"] == "right_wing"
  assert rows["left_wing_fuel_cell"]["review_status"] == "candidate_binding"
  assert rows["right_wing_fuel_cell"]["review_status"] == "candidate_binding"
  assert rows["left_wing_fuel_cell"]["side_sign_relation"][
    "side_sign_mismatch"
  ] is False

  assert diagnostics["schema_version"] == (
    "a2.target_geometry_review_point_diagnostics.v1"
  )
  assert diagnostics["summary"]["review_point_count"] >= 10
  points = {row["point_id"]: row for row in diagnostics["rows"]}
  assert points["nose_axis_4m"]["nearest_outer_region_id"] == "forward_fuselage"
  assert points["nose_axis_4m"]["nearest_outer_distance_m"] == 0.0
  assert points["nose_axis_4m"]["candidate_component_count"] > 0
  assert points["nose_axis_6m"]["nearest_outer_region_id"] == "nose_radome"
  assert points["tail_axis_6m"]["nearest_component_name"] in {
    "afterburner_nozzle",
    "engine_core",
    "rudder_actuator",
  }

  assert fine_proxy["schema_version"] == "a2.target_geometry_fine_proxy_candidate.v1"
  assert fine_proxy["status"] == "fine_geometry_proxy_candidate_generated_review_only"
  assert fine_proxy["summary"]["source_outer_region_count"] == 14
  assert fine_proxy["summary"]["proxy_count"] == 14
  assert fine_proxy["summary"]["held_region_count"] == 0
  assert fine_proxy["summary"]["mesh_source_vertex_count"] == 13415
  assert fine_proxy["summary"]["mesh_derived_silhouette_count"] == 14
  assert fine_proxy["summary"]["inflated_fallback_count"] == 0
  assert fine_proxy["summary"]["proxy_kind_counts"]["thin_prism"] >= 5
  assert fine_proxy["summary"]["proxy_kind_counts"]["convex_hull"] >= 4
  assert fine_proxy["summary"]["total_proxy_support_volume_ratio"] < 0.75
  proxies = {proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]}
  assert proxies["left_wing"]["proxy_kind"] == "thin_prism"
  assert proxies["vertical_tail"]["thin_prism"]["thin_axis"] == "y"
  assert proxies["nose_radome"]["proxy_kind"] == "convex_hull"
  assert "runtime_collision_mesh" in proxies["nose_radome"]["runtime_prohibited_use"]
  for proxy in proxies.values():
    geometry = proxy["mesh_derived_review_geometry"]
    assert geometry["fallback_policy"] == "disabled_no_bounds_expansion"
    assert "selection_inflation_factor" not in geometry
    assert geometry["status"] == "mesh_silhouette_extracted_from_curated_mesh_nodes"
    assert geometry["region_vertex_count"] > 0
  assert proxies["nose_radome"]["mesh_derived_review_geometry"]["region_vertex_count"] >= 90
  assert proxies["left_wing"]["mesh_derived_review_geometry"]["region_vertex_count"] >= 100
  assert proxies["right_wing"]["mesh_derived_review_geometry"]["region_vertex_count"] >= 100
  assert proxies["canopy"]["mesh_derived_review_geometry"]["source_node_names"] == [
    "Object_16",
    "Object_6",
    "Object_8",
  ]
  assert (
    proxies["nose_radome"]["mesh_derived_review_geometry"]["hulls"]["top"][
      "point_count"
    ]
    >= 3
  )
  fine_rows = {row["point_id"]: row for row in fine_proxy["review_point_distance_deltas"]}
  assert fine_rows["nose_axis_4m"]["nearest_fine_proxy_region_id"]
  assert "fine_minus_source_distance_delta_m" in fine_rows["above_4m"]

  assert surface_report["schema_version"] == (
    "a2.target_geometry_surface_component_candidate.v1"
  )
  assert surface_report["status"] == (
    "surface_component_candidate_generated_review_only"
  )
  assert surface_report["summary"]["surface_component_count"] == 14
  assert surface_report["summary"]["missing_existing_runtime_component_relation_count"] == 0
  assert surface_report["summary"]["missing_runtime_link_held_count"] == 0
  assert surface_report["summary"]["side_sign_hard_blocker_count"] == 0
  assert surface_report["summary"]["cross_region_semantic_hold_count"] == 8
  assert surface_report["summary"]["needs_review_count"] == 0
  surface_rows = {
    row["surface_component_id"]: row for row in surface_report["rows"]
  }
  nose_surface = surface_rows["surface_nose_radome"]
  assert nose_surface["source_region_id"] == "nose_radome"
  assert nose_surface["review_status"] == "candidate_surface_component"
  assert nose_surface["review_flags"] == ["candidate_surface_component"]
  assert nose_surface["clean_direct_component_names"] == [
    "apg68_radar_array",
    "iff_interrogator",
  ]
  assert {
    link["component_name"] for link in nose_surface["linked_internal_components"]
  } >= {"apg68_radar_array", "iff_interrogator"}
  left_wing_surface = surface_rows["surface_left_wing_skin"]
  assert "surface_area_loss" in left_wing_surface["expected_damage_modes"]
  assert "side_sign_review" not in left_wing_surface["review_flags"]
  assert left_wing_surface["review_status"] == "review_only_cross_region_semantic_hold"
  assert left_wing_surface["review_semantics"] == "cross_region_semantic_hold"
  assert {
    link["component_name"] for link in left_wing_surface["linked_internal_components"]
  } >= {"left_wing_fuel_cell", "left_aileron_actuator", "wing_spar_center"}
  assert set(left_wing_surface["clean_direct_component_names"]) >= {
    "left_wing_fuel_cell",
    "left_aileron_actuator",
  }
  center_surface = surface_rows["surface_center_fuselage_skin"]
  assert center_surface["review_status"] == "review_only_cross_region_semantic_hold"
  assert center_surface["review_semantics"] == "cross_region_semantic_hold"
  assert "wing_spar_center" in center_surface[
    "cross_region_semantic_component_names"
  ]
  assert set(center_surface["clean_direct_component_names"]) >= {
    "center_fuselage_fuel_cell",
    "data_link_terminal",
    "flight_control_computer",
    "mission_computer",
  }
  aft_engine_surface = surface_rows["surface_aft_engine_bay_skin"]
  assert aft_engine_surface["review_status"] == (
    "review_only_cross_region_boundary_candidate"
  )
  assert aft_engine_surface["review_semantics"] == (
    "cross_region_boundary_candidate_review_only"
  )
  assert "engine_core" in aft_engine_surface[
    "cross_region_semantic_component_names"
  ]
  forward_surface = surface_rows["surface_forward_fuselage_skin"]
  assert forward_surface["review_status"] == "candidate_surface_component"
  assert forward_surface["clean_direct_link_count"] == 3
  intake_surface = surface_rows["surface_intake_lip_and_duct"]
  assert intake_surface["review_semantics"] == (
    "cross_region_boundary_candidate_review_only"
  )
  assert intake_surface["runtime_relation_status"] == (
    "runtime_relation_review_only_candidate"
  )
  assert intake_surface["missing_existing_runtime_component_relations"] == []
  assert intake_surface["clean_direct_component_names"] == [
    "dedicated_intake_lip_or_duct_component",
  ]
  canopy_surface = surface_rows["surface_canopy"]
  assert canopy_surface["review_status"] == "candidate_surface_component"
  assert canopy_surface["review_semantics"] == "candidate_surface_component"
  assert canopy_surface["missing_existing_runtime_component_relations"] == []
  assert canopy_surface["clean_direct_component_names"] == [
    "dedicated_canopy_surface_component",
  ]
  horizontal_tail_surface = surface_rows["surface_left_horizontal_tail_skin"]
  assert horizontal_tail_surface["linked_internal_component_count"] == 1
  assert horizontal_tail_surface["review_status"] == "candidate_surface_component"
  assert horizontal_tail_surface["review_semantics"] == "candidate_surface_component"
  assert horizontal_tail_surface["clean_direct_component_names"] == [
    "left_horizontal_tail_actuator_or_surface_component",
  ]
  right_tail_surface = surface_rows["surface_right_horizontal_tail_skin"]
  assert right_tail_surface["review_status"] == "candidate_surface_component"
  assert right_tail_surface["review_semantics"] == "candidate_surface_component"
  assert right_tail_surface["clean_direct_component_names"] == [
    "right_horizontal_tail_actuator_or_surface_component",
  ]
  assert surface_report["authority_boundary"]["runtime_damage_model"] is False
  assert surface_report["authority_boundary"]["true_surface_component_boundaries"] is False

  assert semantic_report["schema_version"] == (
    "a2.target_geometry_semantic_damage_geometry_candidate.v1"
  )
  assert semantic_report["status"] == (
    "semantic_damage_geometry_candidate_generated_review_only"
  )
  assert semantic_report["summary"]["semantic_volume_component_count"] == 14
  assert semantic_report["summary"]["runtime_parse_ready_component_count"] == 14
  assert semantic_report["summary"]["runtime_active_component_count"] == 0
  assert semantic_report["summary"]["cross_region_handoff_held_count"] == 8
  assert semantic_report["summary"]["blocked_receiver_count"] == 0
  assert semantic_report["summary"]["bad_geometry_receiver_count"] == 0
  assert semantic_report["summary"]["geometry_primitive_counts"]["thin_prism"] >= 5
  assert semantic_report["summary"]["geometry_primitive_counts"]["convex_hull"] >= 4
  semantic_rows = {
    row["semantic_component_id"]: row for row in semantic_report["rows"]
  }
  nose_volume = semantic_rows["semantic_nose_radome_volume"]
  assert nose_volume["source_region_id"] == "nose_radome"
  assert nose_volume["geometry_primitive"] == "convex_hull"
  assert nose_volume["direct_receiver_components"] == [
    "apg68_radar_array",
    "iff_interrogator",
  ]
  assert nose_volume["cross_region_receiver_components"] == []
  assert nose_volume["runtime_component_json_candidate"]["geometry_primitive"] == (
    "convex_hull"
  )
  assert nose_volume["runtime_component_json_candidate"]["geometry"][
    "surface_component_id"
  ] == "surface_nose_radome"
  assert len(nose_volume["runtime_geometry"]["vertices_m"]) >= 7
  left_wing_volume = semantic_rows["semantic_left_wing_skin_volume"]
  assert left_wing_volume["geometry_primitive"] == "thin_prism"
  assert left_wing_volume["direct_receiver_components"] == [
    "left_aileron_actuator",
    "left_wing_fuel_cell",
  ]
  assert left_wing_volume["cross_region_receiver_components"] == [
    "wing_spar_center"
  ]
  assert left_wing_volume["receiver_handoff_status"] == (
    "direct_receivers_parse_ready_cross_region_receivers_held"
  )
  assert semantic_report["authority_boundary"][
    "runtime_schema_parse_ready_candidate"
  ] is True
  assert semantic_report["authority_boundary"]["runtime_active_component"] is False

  assert internal_prior_report["schema_version"] == (
    "a2.target_geometry_internal_component_prior_candidate.v1"
  )
  assert internal_prior_report["status"] == (
    "internal_component_prior_candidate_generated_review_only"
  )
  assert internal_prior_report["summary"]["internal_component_prior_count"] == 26
  assert internal_prior_report["summary"]["runtime_active_component_count"] == 0
  assert internal_prior_report["summary"]["post_constraint_outside_count"] == 0
  assert internal_prior_report["summary"]["constrained_inside_count"] == 26
  assert internal_prior_report["summary"]["nominal_size_fit_issue_count"] == 0
  assert internal_prior_report["summary"]["parent_shell_exceed_review_count"] == 7
  assert internal_prior_report["summary"]["cross_region_held_prior_count"] == 2
  assert internal_prior_report["whole_airframe_bounds"]["span"][0] > 14.0
  assert internal_prior_report["summary"]["shape_counts"] == {
    "capsule": 9,
    "ellipsoid": 7,
    "frustum": 1,
    "obb": 6,
    "thin_prism": 3,
  }
  assert internal_prior_report["summary"]["shape_promotion_count"] == 9
  assert internal_prior_report["summary"]["shape_promotion_status_counts"] == {
    "not_promoted_from_subcomponent_shape_candidate": 17,
    "r18_promoted_from_subcomponent_shape_candidate": 2,
    "r21_promoted_from_latest_subcomponent_candidate": 7,
  }
  assert internal_prior_report["summary"]["size_evidence_level_counts"][
    "public_lru_dimension"
  ] >= 2
  prior_rows = {
    row["component_name"]: row for row in internal_prior_report["rows"]
  }
  radar_prior = prior_rows["apg68_radar_array"]
  assert radar_prior["prior_shape"] == "ellipsoid"
  assert radar_prior["shape_promotion_status"] == (
    "r21_promoted_from_latest_subcomponent_candidate"
  )
  assert radar_prior["size_evidence_level"] == (
    "public_related_family_dimension_not_apg68_exact"
  )
  assert radar_prior["nominal_dimensions_m"] == [0.1016, 0.7366, 0.4826]
  assert radar_prior["constraint_adjustment"]["size_preserved"] is True
  assert radar_prior["constraint_region_ids"] == [
    "nose_radome",
    "forward_fuselage",
  ]
  assert radar_prior["constraint_adjustment"]["post_constraint_outside_fraction"] == 0.0
  assert radar_prior["aabb_runtime_fallback_candidate"]["geometry"][
    "prior_shape"
  ] == "ellipsoid"
  iff_prior = prior_rows["iff_interrogator"]
  assert iff_prior["prior_shape"] == "ellipsoid"
  assert iff_prior["shape_promotion_status"] == (
    "r18_promoted_from_subcomponent_shape_candidate"
  )
  inertial_prior = prior_rows["inertial_navigation_unit"]
  assert inertial_prior["prior_shape"] == "ellipsoid"
  assert inertial_prior["shape_promotion_status"] == (
    "r18_promoted_from_subcomponent_shape_candidate"
  )
  assert inertial_prior["constrained_geometry"]["center_m"] == [2.6, 0.0, -0.1]
  cockpit_prior = prior_rows["cockpit_crew_station"]
  assert cockpit_prior["constrained_geometry"]["center_m"] == [
    3.787559,
    0.0,
    -0.67538,
  ]
  afterburner_prior = prior_rows["afterburner_nozzle"]
  assert afterburner_prior["prior_shape"] == "frustum"
  assert afterburner_prior["prior_axis"] == "x"
  assert afterburner_prior["constrained_geometry"]["negative_axis_radius_m"] == 0.45
  assert afterburner_prior["constrained_geometry"]["positive_axis_radius_m"] == (
    0.59055
  )
  assert afterburner_prior["constrained_geometry"]["center_m"] == [
    -5.75,
    0.0,
    -0.75,
  ]
  engine_prior = prior_rows["engine_core"]
  assert engine_prior["prior_shape"] == "capsule"
  assert engine_prior["shape_promotion_status"] == (
    "r21_promoted_from_latest_subcomponent_candidate"
  )
  assert engine_prior["size_evidence_level"] == "public_engine_dimension"
  assert engine_prior["nominal_dimensions_m"] == [4.62026, 1.1811, 1.1811]
  assert engine_prior["constraint_adjustment"]["size_preserved"] is True
  assert engine_prior["constrained_geometry"]["center_m"] == [
    -3.693053,
    0.0,
    -0.904381,
  ]
  assert engine_prior["constraint_adjustment"][
    "airframe_projection_center_shift_m"
  ] == 0.0
  assert set(engine_prior["constraint_region_ids"]) == {
    "aft_fuselage_engine",
    "engine_nozzle",
    "intake",
  }
  assert engine_prior["constraint_status"] == (
    "cross_region_prior_constrained_inside_airframe_held"
  )
  wing_spar_prior = prior_rows["wing_spar_center"]
  assert wing_spar_prior["prior_shape"] == "thin_prism"
  assert set(wing_spar_prior["constraint_region_ids"]) >= {
    "center_fuselage",
    "left_wing",
    "right_wing",
  }
  assert wing_spar_prior["constraint_status"] == (
    "cross_region_prior_constrained_inside_airframe_held"
  )
  assert wing_spar_prior["nominal_dimensions_m"] == [0.5, 5.8, 0.18]
  assert wing_spar_prior["constrained_geometry"]["center_m"] == [
    -1.2,
    0.0,
    -0.985043,
  ]
  assert wing_spar_prior["constrained_geometry"]["footprint_points_m"] == [
    [-1.45, -2.9],
    [-0.95, -2.9],
    [-0.95, 2.9],
    [-1.45, 2.9],
  ]
  assert wing_spar_prior["constraint_adjustment"][
    "airframe_projection_center_shift_m"
  ] == 0.0
  left_wing_fuel_prior = prior_rows["left_wing_fuel_cell"]
  assert left_wing_fuel_prior["prior_shape"] == "thin_prism"
  assert left_wing_fuel_prior["shape_promotion_status"] == (
    "r21_promoted_from_latest_subcomponent_candidate"
  )
  assert left_wing_fuel_prior["constraint_region_ids"] == ["left_wing"]
  assert left_wing_fuel_prior["size_evidence_level"] == (
    "public_total_capacity_partition_estimate"
  )
  assert left_wing_fuel_prior["nominal_dimensions_m"] == [1.85, 1.73, 0.15]
  assert left_wing_fuel_prior["constrained_geometry"]["center_m"] == [
    -2.075,
    -1.685,
    -0.985,
  ]
  assert left_wing_fuel_prior["constrained_geometry"]["footprint_points_m"] == [
    [-3.0, -2.55],
    [-2.95, -1.05],
    [-1.25, -0.82],
    [-1.15, -1.95],
  ]
  assert left_wing_fuel_prior["constraint_adjustment"]["size_preserved"] is True
  assert left_wing_fuel_prior["constraint_adjustment"][
    "post_constraint_outside_fraction"
  ] == 0.0
  assert internal_prior_report["authority_boundary"][
    "true_internal_component_geometry"
  ] is False

  assert held_segment_report["schema_version"] == (
    "a2.target_geometry_cross_region_held_component_segments.v1"
  )
  assert held_segment_report["status"] == (
    "cross_region_held_component_segments_generated_review_only"
  )
  assert held_segment_report["summary"]["held_parent_component_count"] == 2
  assert held_segment_report["summary"]["held_segment_count"] == 8
  assert held_segment_report["summary"]["engine_core_segment_count"] == 3
  assert held_segment_report["summary"]["wing_spar_center_segment_count"] == 5
  assert held_segment_report["summary"][
    "outside_whole_airframe_segment_count"
  ] == 0
  assert held_segment_report["summary"]["shape_promotion_segment_count"] == 5
  assert held_segment_report["summary"]["shape_promotion_status_counts"] == {
    "inherited_parent_prior_shape": 3,
    "r18_promoted_from_subcomponent_shape_candidate": 2,
    "r21_promoted_from_latest_subcomponent_candidate": 3,
  }
  assert held_segment_report["summary"]["runtime_active_segment_count"] == 0
  segment_rows = {
    row["segment_id"]: row for row in held_segment_report["rows"]
  }
  afterburner_segment = segment_rows["engine_core_afterburner_segment"]
  assert afterburner_segment["parent_component_name"] == "engine_core"
  assert afterburner_segment["segment_shape"] == "capsule"
  assert afterburner_segment["segment_axis"] == "x"
  assert afterburner_segment["source_parent_segment_shape"] == "capsule"
  assert afterburner_segment["shape_promotion_status"] == (
    "r18_promoted_from_subcomponent_shape_candidate"
  )
  assert afterburner_segment["center_offset_m"] == [0.207628, 0.0, 0.0]
  assert afterburner_segment["owner_region_ids"] == [
    "aft_fuselage_engine",
    "engine_nozzle",
  ]
  assert afterburner_segment["inside_whole_airframe_bounds"] is True
  assert afterburner_segment["geometry"]["bounds"]["span"][0] == 1.540087
  assert afterburner_segment["geometry"]["center_m"] == [
    -5.025512,
    0.0,
    -0.904381,
  ]
  hot_segment = segment_rows["engine_core_hot_section_segment"]
  assert hot_segment["segment_shape"] == "ellipsoid"
  assert hot_segment["source_parent_segment_shape"] == "capsule"
  assert hot_segment["shape_promotion_status"] == (
    "r18_promoted_from_subcomponent_shape_candidate"
  )
  compressor_segment = segment_rows["engine_core_forward_compressor_segment"]
  assert compressor_segment["segment_shape"] == "ellipsoid"
  assert compressor_segment["center_offset_m"] == [-0.2, 0.0, 0.0]
  assert compressor_segment["shape_promotion_status"] == (
    "r21_promoted_from_latest_subcomponent_candidate"
  )
  carrythrough_segment = segment_rows["wing_spar_center_carrythrough_segment"]
  assert carrythrough_segment["parent_component_name"] == "wing_spar_center"
  assert carrythrough_segment["segment_shape"] == "thin_prism"
  assert carrythrough_segment["segment_axis"] == ""
  assert carrythrough_segment["source_parent_segment_shape"] == "thin_prism"
  assert carrythrough_segment["owner_region_ids"] == ["center_fuselage"]
  assert carrythrough_segment["nominal_dimensions_m"] == [0.5, 1.7, 0.18]
  assert carrythrough_segment["geometry"]["center_m"] == [
    -1.2,
    0.0,
    -0.985043,
  ]
  assert carrythrough_segment["geometry"]["footprint_points_m"] == [
    [-1.45, -0.85],
    [-0.95, -0.85],
    [-0.95, 0.85],
    [-1.45, 0.85],
  ]
  assert carrythrough_segment["inside_whole_airframe_bounds"] is True
  assert segment_rows["wing_spar_center_left_inner_wing_segment"][
    "owner_region_ids"
  ] == ["left_wing"]
  assert segment_rows["wing_spar_center_right_inner_wing_segment"][
    "owner_region_ids"
  ] == ["right_wing"]

  assert airframe_constraint_report["schema_version"] == (
    "a2.target_geometry_airframe_constraint_correction_candidate.v1"
  )
  assert airframe_constraint_report["status"] == (
    "airframe_constraint_correction_candidate_generated_review_only"
  )
  assert airframe_constraint_report["summary"]["item_count"] == 34
  assert airframe_constraint_report["summary"]["receiver_prior_count"] == 26
  assert airframe_constraint_report["summary"]["held_split_segment_count"] == 8
  # The whole-airframe containment contour projects the audit glTF mesh
  # triangles into each view and unions the projected faces. The R22 thin-prism
  # and frustum geometry corrections clear the previous top-view protrusions.
  exposure_items = {
    row["item_id"]
    for row in airframe_constraint_report["rows"]
    if row["current_silhouette"]["outside_sample_count"] > 0
  }
  assert exposure_items == set()
  assert airframe_constraint_report["summary"][
    "silhouette_exposure_item_count"
  ] == 0
  assert airframe_constraint_report["summary"][
    "center_shift_reduces_item_count"
  ] == 0
  assert airframe_constraint_report["summary"][
    "size_or_shape_review_item_count"
  ] == 0
  assert airframe_constraint_report["summary"][
    "low_confidence_inside_item_count"
  ] == 9
  correction_rows = {
    row["item_id"]: row for row in airframe_constraint_report["rows"]
  }
  radar_constraint = correction_rows["apg68_radar_array"]
  assert radar_constraint["current_silhouette"]["outside_views"] == []
  assert radar_constraint["current_silhouette"]["outside_sample_count"] == 0
  assert radar_constraint["triage_status"] == "inside_airframe_candidate"
  wing_spar_constraint = correction_rows["wing_spar_center"]
  assert wing_spar_constraint["triage_status"] == (
    "inside_airframe_cross_region_ownership_held"
  )
  afterburner_segment_constraint = correction_rows[
    "engine_core_afterburner_segment"
  ]
  assert afterburner_segment_constraint["triage_status"] == (
    "inside_airframe_cross_region_ownership_held"
  )
  assert afterburner_segment_constraint["current_silhouette"][
    "outside_sample_count"
  ] == 0
  assert {
    row["item_id"]
    for row in airframe_constraint_report["rows"]
    if row["current_silhouette"]["outside_sample_count"] > 0
  } == exposure_items
  assert airframe_constraint_report["authority_boundary"][
    "center_shift_candidate_not_applied"
  ] is True

  assert ownership_split_report["schema_version"] == (
    "a2.target_geometry_cross_region_ownership_split_candidate.v1"
  )
  assert ownership_split_report["status"] == (
    "cross_region_ownership_split_candidate_generated_review_only"
  )
  assert ownership_split_report["summary"]["parent_decision_count"] == 2
  assert ownership_split_report["summary"]["split_candidate_parent_count"] == 2
  assert ownership_split_report["summary"]["split_receiver_candidate_count"] == 8
  assert ownership_split_report["summary"][
    "engine_core_split_receiver_candidate_count"
  ] == 3
  assert ownership_split_report["summary"][
    "wing_spar_center_split_receiver_candidate_count"
  ] == 5
  assert ownership_split_report["summary"][
    "zero_silhouette_exposure_split_candidate_count"
  ] == 8
  assert ownership_split_report["summary"][
    "outside_whole_airframe_split_candidate_count"
  ] == 0
  assert ownership_split_report["summary"][
    "parent_receiver_retirement_required_count"
  ] == 2
  assert ownership_split_report["summary"][
    "runtime_parse_ready_split_candidate_count"
  ] == 8
  assert ownership_split_report["summary"][
    "runtime_active_split_component_count"
  ] == 0
  ownership_rows = {
    row["parent_component_name"]: row for row in ownership_split_report["rows"]
  }
  engine_ownership = ownership_rows["engine_core"]
  assert engine_ownership["recommended_ownership_decision"] == (
    "split_into_engine_section_receivers_and_keep_intake_duct_receiver_separate"
  )
  assert engine_ownership["segment_count"] == 3
  assert engine_ownership["parent_receiver_retirement_required_before_activation"] is True
  engine_candidates = {
    candidate["name"]: candidate
    for entry in engine_ownership["segment_entries"]
    for candidate in [entry["runtime_component_json_candidate"]]
  }
  afterburner_candidate = engine_candidates["engine_core_afterburner_segment"]
  assert afterburner_candidate["geometry_primitive"] == "aabb"
  assert afterburner_candidate["offset"] == afterburner_segment["geometry"][
    "bounds"
  ]["center"]
  assert afterburner_candidate["geometry"]["prior_shape"] == "capsule"
  assert afterburner_candidate["geometry"]["source_segment_id"] == (
    "engine_core_afterburner_segment"
  )
  wing_ownership = ownership_rows["wing_spar_center"]
  assert wing_ownership["recommended_ownership_decision"] == (
    "split_into_center_carrythrough_root_and_inner_wing_spar_receivers"
  )
  assert wing_ownership["segment_count"] == 5
  assert "wing_spar_center_carrythrough_segment" in wing_ownership[
    "candidate_runtime_component_names"
  ]
  assert ownership_split_report["authority_boundary"][
    "runtime_split_receiver_activation"
  ] is False

  assert runtime_activation_report["schema_version"] == (
    "a2.target_geometry_runtime_activation_candidate.v1"
  )
  assert runtime_activation_report["status"] == (
    "target_geometry_runtime_activation_candidate_generated_tg_p7_r1"
  )
  assert runtime_activation_report["activation_policy"]["target_unit"] == (
    "F-16C_Block50"
  )
  assert runtime_activation_report["activation_policy"]["target_path"] == (
    "damage_model.hitboxes[].components"
  )
  assert runtime_activation_report["activation_policy"][
    "requires_feature_flag"
  ] is True
  assert runtime_activation_report["summary"]["candidate_component_count"] == 8
  assert runtime_activation_report["summary"][
    "runtime_schema_parse_ready_component_count"
  ] == 8
  assert runtime_activation_report["summary"][
    "runtime_active_component_count"
  ] == 0
  assert runtime_activation_report["summary"][
    "parent_receiver_retirement_candidate_count"
  ] == 2
  assert runtime_activation_report["summary"][
    "parent_receiver_retirement_applied_count"
  ] == 0
  assert runtime_activation_report["summary"][
    "aabb_fallback_component_count"
  ] == 8
  assert runtime_activation_report["summary"][
    "unit_database_patch_component_count"
  ] == 8
  assert runtime_activation_report["summary"]["behavior_test_required_count"] == 8
  assert runtime_activation_report["summary"]["activation_blocker_count"] == 0
  assert runtime_activation_report["authority_boundary"][
    "unit_database_modified"
  ] is False
  assert runtime_activation_report["authority_boundary"][
    "runtime_activation_candidate"
  ] is True
  assert runtime_activation_report["authority_boundary"][
    "training_proxy_feature_flag_required"
  ] is True
  assert len(runtime_activation_report["parent_receiver_retirement_plan"]) == 2
  assert len(runtime_activation_report["unit_database_patch_candidate"]["add"]) == 8
  assert (
    len(runtime_activation_report["unit_database_patch_candidate"]["remove"]) == 2
  )
  assert (
    len(runtime_activation_report["unit_database_patch_candidate"]["add_components"])
    == 8
  )
  activation_rows = {
    row["candidate_component_name"]: row
    for row in runtime_activation_report["rows"]
  }
  afterburner_activation = activation_rows["engine_core_afterburner_segment"]
  assert afterburner_activation["target_hitbox_index"] == 2
  assert afterburner_activation["unit_database_patch_path"] == (
    "damage_model.hitboxes[2].components"
  )
  assert afterburner_activation["runtime_loader_contract_status"] == (
    "parse_ready_existing_loader_fields"
  )
  assert afterburner_activation["runtime_component_json_candidate"][
    "geometry_primitive"
  ] == "aabb"
  assert afterburner_activation["runtime_component_json_candidate"]["offset"] == (
    afterburner_candidate["offset"]
  )
  assert afterburner_activation["runtime_component_json_candidate"]["geometry"][
    "activation_feature_flag"
  ] == "A2_TARGET_GEOMETRY_PROXY_F16C_R22"
  assert all(
    row["runtime_activation_status"] == "not_applied_to_unit_database"
    for row in runtime_activation_report["rows"]
  )

  assert runtime_behavior_report["schema_version"] == (
    "a2.target_geometry_runtime_behavior_regression.v1"
  )
  assert runtime_behavior_report["status"] == (
    "target_geometry_runtime_behavior_regression_generated_tg_p7_r2"
  )
  assert runtime_behavior_report["summary"]["base_component_count"] == 26
  assert runtime_behavior_report["summary"][
    "expected_projected_component_count"
  ] == 32
  assert runtime_behavior_report["summary"]["projected_component_count"] == 32
  assert runtime_behavior_report["summary"][
    "retired_parent_component_count"
  ] == 2
  assert runtime_behavior_report["summary"]["split_component_added_count"] == 8
  assert runtime_behavior_report["summary"]["duplicate_component_name_count"] == 0
  assert runtime_behavior_report["summary"][
    "parent_retirement_behavior_pass_count"
  ] == 2
  assert runtime_behavior_report["summary"]["behavior_regression_pass"] is True
  assert runtime_behavior_report["summary"]["runtime_active_component_count"] == 0
  assert runtime_behavior_report["summary"]["unit_database_modified"] is False
  assert runtime_behavior_report["authority_boundary"][
    "runtime_behavior_regression_candidate"
  ] is True
  assert runtime_behavior_report["authority_boundary"]["training_path_wired"] is False
  behavior_rows = {
    row["parent_component_name"]: row for row in runtime_behavior_report["rows"]
  }
  assert behavior_rows["engine_core"]["target_hitbox_index"] == 2
  assert behavior_rows["engine_core"]["base_hitbox_component_count"] == 7
  assert behavior_rows["engine_core"]["patched_hitbox_component_count"] == 9
  assert behavior_rows["engine_core"]["parent_absent_after_patch"] is True
  assert behavior_rows["engine_core"]["split_component_present_count"] == 3
  assert behavior_rows["wing_spar_center"]["target_hitbox_index"] == 3
  assert behavior_rows["wing_spar_center"]["base_hitbox_component_count"] == 7
  assert behavior_rows["wing_spar_center"]["patched_hitbox_component_count"] == 11
  assert behavior_rows["wing_spar_center"]["split_component_present_count"] == 5
  assert "engine_core" not in runtime_behavior_report["projected_component_names"]
  assert "wing_spar_center" not in runtime_behavior_report[
    "projected_component_names"
  ]
  assert "engine_core_afterburner_segment" in runtime_behavior_report[
    "projected_component_names"
  ]

  assert training_proxy_report["schema_version"] == (
    "a2.target_geometry_training_proxy_database.v1"
  )
  assert training_proxy_report["status"] == (
    "target_geometry_training_proxy_database_generated_tg_p7_r3"
  )
  assert training_proxy_report["summary"]["default_database_component_count"] == 26
  assert training_proxy_report["summary"]["proxy_database_component_count"] == 32
  assert training_proxy_report["summary"]["component_count_delta"] == 6
  assert training_proxy_report["summary"]["retired_parent_component_count"] == 2
  assert training_proxy_report["summary"]["split_receiver_component_count"] == 8
  assert training_proxy_report["summary"]["duplicate_component_name_count"] == 0
  assert training_proxy_report["summary"]["behavior_regression_pass"] is True
  assert training_proxy_report["summary"]["proxy_database_materialized"] is True
  assert training_proxy_report["summary"]["repository_unit_database_modified"] is False
  assert (
    training_proxy_report["summary"]["default_runtime_split_receiver_active_count"]
    == 0
  )
  assert (
    training_proxy_report["summary"]["proxy_runtime_split_receiver_active_count"]
    == 8
  )
  assert training_proxy_report["training_runtime_contract"][
    "runtime_config_key"
  ] == "runtime.database_path"
  assert training_proxy_report["training_runtime_contract"][
    "opt_in_training_config_path"
  ].endswith(
    "air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_v1.json"
  )
  assert training_proxy_report["training_runtime_contract"][
    "training_path_wired"
  ] is True
  assert training_proxy_report["runtime_database"]["proxy_database_path"].endswith(
    "target_geometry_training_proxy_database_20260613"
  )
  assert training_proxy_report["authority_boundary"][
    "default_runtime_active_component"
  ] is False
  assert training_proxy_report["authority_boundary"][
    "training_proxy_runtime_active_component"
  ] is True
  assert training_proxy_report["authority_boundary"]["training_path_wired"] is True
  proxy_component_names = airframe_geometry_review._damage_component_names( # noqa: SLF001
    training_proxy_aircraft
  )
  assert len(proxy_component_names) == 32
  assert "engine_core" not in proxy_component_names
  assert "wing_spar_center" not in proxy_component_names
  assert "engine_core_afterburner_segment" in proxy_component_names
  assert "wing_spar_center_carrythrough_segment" in proxy_component_names
  assert len(training_proxy_operations) == 10

  assert shape_placement_report["schema_version"] == (
    "a2.target_geometry_subcomponent_shape_placement_candidate.v1"
  )
  assert shape_placement_report["status"] == (
    "subcomponent_shape_placement_candidate_generated_review_only"
  )
  assert shape_placement_report["summary"]["source_constraint_item_count"] == 34
  # The shape-aware thin-prism/frustum updates leave no source exposure items,
  # so the shape-placement follow-up queue is empty.
  assert shape_placement_report["summary"][
    "source_silhouette_exposure_item_count"
  ] == 0
  summary = shape_placement_report["summary"]
  assert summary["shape_placement_candidate_count"] == summary[
    "source_silhouette_exposure_item_count"
  ]
  assert summary["nominal_dimension_preserved_count"] == summary[
    "shape_placement_candidate_count"
  ]
  # Each candidate is evaluated against the same contour; the resolves /
  # unresolved split is exhaustive along the "did it clear the contour"
  # axis, and the reduces / no-improvement split is exhaustive along the
  # "did outside-sample count drop" axis. The two axes are independent, so
  # we assert each partition sums to the candidate count.
  assert summary["candidate_resolves_exposure_count"] + summary[
    "candidate_unresolved_exposure_count"
  ] == summary["shape_placement_candidate_count"]
  assert summary["candidate_reduces_exposure_count"] + summary[
    "candidate_no_improvement_count"
  ] == summary["shape_placement_candidate_count"]
  assert summary["candidate_total_outside_sample_count"] <= summary[
    "current_total_outside_sample_count"
  ]
  assert summary["candidate_total_outside_sample_reduction"] >= 0
  # Centerline candidates are generated for every shape-placement item.
  assert summary["centerline_candidate_count"] == summary[
    "shape_placement_candidate_count"
  ]
  assert summary["centerline_candidate_resolves_exposure_count"] + summary[
    "centerline_candidate_unresolved_exposure_count"
  ] == summary["centerline_candidate_count"]
  assert summary["centerline_candidate_total_outside_sample_reduction"] >= 0
  # Latest candidates are generated for every shape-placement item; the
  # latest placement rule is the final word before promotion, so unresolved
  # here means the geometry model itself needs work, not a placement tweak.
  assert summary["latest_candidate_count"] == summary[
    "shape_placement_candidate_count"
  ]
  assert summary["latest_candidate_resolves_exposure_count"] + summary[
    "latest_candidate_unresolved_exposure_count"
  ] == summary["latest_candidate_count"]
  assert summary["latest_candidate_total_outside_sample_reduction"] >= 0
  assert len(shape_placement_report["rows"]) == summary[
    "source_silhouette_exposure_item_count"
  ]
  placement_item_ids = {
    row["item_id"] for row in shape_placement_report["rows"]
  }
  assert placement_item_ids == set()
  assert "left_wing_fuel_cell" not in placement_item_ids
  assert "right_wing_fuel_cell" not in placement_item_ids
  assert "wing_spar_center" not in placement_item_ids
  assert "afterburner_nozzle" not in placement_item_ids
  assert "engine_core" not in placement_item_ids
  assert "cockpit_crew_station" not in placement_item_ids
  assert "inertial_navigation_unit" not in placement_item_ids
  assert shape_placement_report["authority_boundary"][
    "shape_candidate_not_applied_to_internal_prior_rules"
  ] is False
  assert shape_placement_report["authority_boundary"][
    "centerline_candidate_not_applied_to_internal_prior_rules"
  ] is False
  assert shape_placement_report["authority_boundary"][
    "latest_candidate_not_applied_to_internal_prior_rules"
  ] is False
  assert shape_placement_report["authority_boundary"][
    "latest_candidate_promoted_to_internal_prior_or_segment_rules"
  ] is True

  assert parent_child_layout_report["schema_version"] == (
    "a2.target_geometry_semantic_parent_child_layout_candidate.v1"
  )
  assert parent_child_layout_report["status"] == (
    "semantic_parent_child_layout_candidate_generated_review_only"
  )
  assert parent_child_layout_report["summary"][
    "parent_semantic_component_count"
  ] == 14
  assert parent_child_layout_report["summary"][
    "bound_receiver_component_count"
  ] == 26
  assert parent_child_layout_report["summary"]["extra_receiver_slot_count"] == 12
  assert parent_child_layout_report["summary"][
    "cross_region_held_receiver_count"
  ] == 2
  assert parent_child_layout_report["summary"][
    "cross_region_held_segment_count"
  ] == 8
  assert parent_child_layout_report["summary"][
    "cross_region_held_segment_overlay_count"
  ] == 5
  assert parent_child_layout_report["summary"]["runtime_active_component_count"] == 0
  layout_rows = {
    row["parent_semantic_component_id"]: row
    for row in parent_child_layout_report["rows"]
  }
  nose_layout = layout_rows["semantic_nose_radome_volume"]
  assert nose_layout["source_region_id"] == "nose_radome"
  assert nose_layout["bound_receiver_count"] == 2
  assert nose_layout["extra_receiver_slot_count"] == 1
  assert {
    child["component_name"] for child in nose_layout["child_receiver_priors"]
  } == {"apg68_radar_array", "iff_interrogator"}
  center_layout = layout_rows["semantic_center_fuselage_skin_volume"]
  assert center_layout["bound_receiver_count"] == 5
  assert center_layout["extra_receiver_slot_count"] == 4
  assert "wing_spar_center" in center_layout["cross_region_held_receiver_names"]
  center_wing_spar_child = [
    child
    for child in center_layout["child_receiver_priors"]
    if child["component_name"] == "wing_spar_center"
  ][0]
  assert center_wing_spar_child["held_segment_count"] == 5
  assert {
    segment["segment_id"]
    for segment in center_wing_spar_child["held_segments"]
  } >= {
    "wing_spar_center_carrythrough_segment",
    "wing_spar_center_left_root_segment",
    "wing_spar_center_right_root_segment",
  }
  left_wing_layout = layout_rows["semantic_left_wing_skin_volume"]
  assert left_wing_layout["bound_receiver_count"] == 2
  assert left_wing_layout["extra_receiver_slot_count"] == 1
  assert {
    child["component_name"] for child in left_wing_layout["child_receiver_priors"]
  } == {"left_aileron_actuator", "left_wing_fuel_cell"}
  assert [
    segment["segment_id"]
    for segment in left_wing_layout["cross_region_held_segment_overlays"]
  ] == ["wing_spar_center_left_inner_wing_segment"]
  assert parent_child_layout_report["authority_boundary"][
    "parent_child_damage_ownership"
  ] is False


def test_airframe_geometry_review_cli_writes_manifest(tmp_path: Path) -> None:
  stale_isolated_page = (
    tmp_path
    / "component_review_views"
    / "surface_links"
    / "surface-vertical-tail-skin-afterburner-nozzle.html"
  )
  stale_isolated_page.parent.mkdir(parents=True)
  stale_isolated_page.write_text("stale view from prior generation", encoding="utf-8")
  for stale_dir in (
    "semantic_damage_geometry_views",
    "internal_component_prior_views",
    "semantic_parent_child_layout_views",
    "subcomponent_shape_placement_views",
  ):
    stale_path = tmp_path / stale_dir / "stale.html"
    stale_path.parent.mkdir(parents=True)
    stale_path.write_text("stale intermediate view", encoding="utf-8")
  for stale_file in (
    "top.svg",
    "side.svg",
    "front.svg",
    "fine_proxy_top.svg",
    "fine_proxy_side.svg",
    "fine_proxy_front.svg",
    "fine_proxy_review_dashboard.html",
    "human_review_triage.html",
  ):
    (tmp_path / stale_file).write_text("stale intermediate visual", encoding="utf-8")

  result = subprocess.run(
    [
      sys.executable,
      "tools/geometry/airframe_geometry_review.py",
      "--out",
      str(tmp_path),
    ],
    cwd=REPO_ROOT,
    check=True,
    capture_output=True,
    text=True,
  )

  summary = json.loads(result.stdout)
  assert summary["status"] == "target_geometry_manifest_generated_review_only"
  assert summary["triangle_count"] == 4504
  assert summary["component_count"] == 26
  assert summary["review_point_count"] >= 10
  assert summary["inside_outer_region_point_count"] > 0
  assert summary["inflated_fallback_count"] == 0
  assert summary["cross_region_held_segment_count"] == 8
  assert summary["cross_region_held_segment_outside_airframe_count"] == 0
  assert summary["cross_region_held_segment_shape_promotion_count"] == 5
  assert summary["internal_component_prior_shape_promotion_count"] == 9
  assert (
    summary["semantic_parent_child_layout_cross_region_held_segment_count"] == 8
  )
  assert summary["airframe_constraint_item_count"] == 34
  # Projected audit-mesh triangle union + shape-aware sampling now leaves no
  # receiver prior outside the whole-airframe contour.
  assert summary["airframe_constraint_silhouette_exposure_item_count"] == 0
  assert summary["airframe_constraint_center_shift_resolves_item_count"] == 0
  assert summary["airframe_constraint_size_or_shape_review_item_count"] == 0
  # Whole-airframe projected mesh contour containment diagnostic.
  assert summary["whole_airframe_contour_method"] == (
    "projected_mesh_triangle_union"
  )
  assert summary["whole_airframe_contour_tolerance_m"] == 0.05
  assert summary["whole_airframe_contour_item_count"] == 26
  assert (
    summary["whole_airframe_contour_excluded_review_only_split_segment_count"]
    == 8
  )
  assert summary["whole_airframe_contour_exceeds_tolerance_item_count"] == 0
  assert summary["whole_airframe_contour_max_outside_distance_m"] == 0.0
  assert summary["whole_airframe_contour_exceeding_item_ids"] == []
  for view in ("top", "side", "front"):
    assert summary["whole_airframe_contour_contours"][view]["status"] == (
      "projected_mesh_triangle_union"
    )
    assert summary["whole_airframe_contour_contours"][view][
      "source_triangle_count"
    ] == 4504
    assert summary["whole_airframe_contour_contours"][view]["polygon_count"] == 1
    assert summary["whole_airframe_contour_contours"][view][
      "contour_point_count"
    ] >= 100
  assert summary["cross_region_ownership_parent_decision_count"] == 2
  assert summary["cross_region_ownership_split_receiver_candidate_count"] == 8
  assert (
    summary["cross_region_ownership_zero_silhouette_exposure_split_candidate_count"]
    == 8
  )
  assert summary["cross_region_ownership_runtime_active_split_component_count"] == 0
  assert summary["target_geometry_runtime_activation_candidate_count"] == 8
  assert summary["target_geometry_runtime_activation_parse_ready_count"] == 8
  assert summary["target_geometry_runtime_activation_patch_component_count"] == 8
  assert (
    summary[
      "target_geometry_runtime_activation_parent_retirement_candidate_count"
    ]
    == 2
  )
  assert summary["target_geometry_runtime_activation_runtime_active_count"] == 0
  assert summary["target_geometry_runtime_behavior_base_component_count"] == 26
  assert (
    summary["target_geometry_runtime_behavior_projected_component_count"] == 32
  )
  assert (
    summary["target_geometry_runtime_behavior_retired_parent_component_count"] == 2
  )
  assert (
    summary["target_geometry_runtime_behavior_split_component_added_count"] == 8
  )
  assert (
    summary["target_geometry_runtime_behavior_duplicate_component_name_count"] == 0
  )
  assert summary["target_geometry_runtime_behavior_regression_pass"] is True
  assert (
    summary["target_geometry_training_proxy_default_database_component_count"]
    == 26
  )
  assert summary["target_geometry_training_proxy_database_component_count"] == 32
  assert (
    summary["target_geometry_training_proxy_split_receiver_component_count"] == 8
  )
  assert summary["target_geometry_training_proxy_database_materialized"] is True
  assert summary["subcomponent_shape_placement_candidate_count"] == 0
  assert summary["subcomponent_shape_placement_resolves_count"] == 0
  assert summary["subcomponent_shape_placement_unresolved_count"] == 0
  assert summary["subcomponent_centerline_resolves_count"] == 0
  assert summary["subcomponent_centerline_unresolved_count"] == 0
  assert summary["subcomponent_latest_resolves_count"] == 0
  assert summary["subcomponent_latest_unresolved_count"] == 0

  manifest_path = tmp_path / "manifest.json"
  assert manifest_path.is_file()
  manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
  assert manifest["paths"]["audit_scene_gltf"].endswith("gltf/scene.gltf")
  assert len(manifest["file_hashes"]["runtime_visual_glb_sha256"]) == 64

  mapping_path = tmp_path / "f16c_geometry_mapping_candidate_20260611.json"
  assert mapping_path.is_file()
  mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
  assert mapping["schema_version"] == "a2.target_geometry_mapping_candidate.v1"
  assert mapping["status"] == "outer_region_candidate_generated_review_only"
  assert mapping["mesh_node_name_quality"]["decision"] == (
    "do_not_auto_classify_regions_from_node_names_only"
  )
  region_ids = {region["id"] for region in mapping["outer_regions"]}
  assert {
    "nose_radome",
    "forward_fuselage",
    "canopy",
    "intake",
    "left_wing",
    "right_wing",
    "vertical_tail",
  }.issubset(region_ids)
  forward = next(
    region for region in mapping["outer_regions"] if region["id"] == "forward_fuselage"
  )
  assert forward["bounds"]["min"][0] < 4.0 < forward["bounds"]["max"][0]
  assert forward["manual_review_required"] is True
  assert forward["source_mesh_node_candidates"]

  for svg_name in ("top.svg", "side.svg", "front.svg"):
    assert not (tmp_path / svg_name).exists()

  # Whole-airframe projected mesh contour containment artifacts.
  contour_json_path = tmp_path / "whole_airframe_contour_containment_20260614.json"
  contour_csv_path = tmp_path / "whole_airframe_contour_containment_20260614.csv"
  assert contour_json_path.is_file()
  assert contour_csv_path.is_file()
  contour_report = json.loads(contour_json_path.read_text(encoding="utf-8"))
  assert contour_report["schema_version"] == (
    "a2.target_geometry_whole_airframe_contour_containment.v1"
  )
  assert contour_report["contour_method"] == "projected_mesh_triangle_union"
  assert contour_report["tolerance_m"] == 0.05
  assert contour_report["summary"]["item_count"] == 26
  assert contour_report["summary"]["excluded_review_only_split_segment_count"] == 8
  assert contour_report["summary"]["exceeds_tolerance_item_count"] == 0
  assert contour_report["authority_boundary"][
    "projected_mesh_contour_diagnostic_only"
  ] is True
  assert contour_report["authority_boundary"]["not_runtime_collision_mesh"] is True
  contour_csv = contour_csv_path.read_text(encoding="utf-8")
  assert "left_wing_fuel_cell" in contour_csv
  assert "max_outside_distance_m" in contour_csv
  for view in ("top", "side", "front"):
    contour_svg = tmp_path / f"whole_airframe_contour_{view}.svg"
    assert contour_svg.is_file()
    svg_text = contour_svg.read_text(encoding="utf-8")
    assert "projected audit-mesh contour" in svg_text
    assert "projected_mesh_triangle_union" in svg_text
    assert "review-only" in svg_text
  contour_dashboard = tmp_path / "whole_airframe_contour_dashboard.html"
  assert contour_dashboard.is_file()
  dashboard_text = contour_dashboard.read_text(encoding="utf-8")
  assert "Whole-Airframe Projected Mesh Contour Containment" in dashboard_text
  assert "wing_spar_center" in dashboard_text

  component_json_path = tmp_path / "component_binding_report_20260611.json"
  component_csv_path = tmp_path / "component_binding_report_20260611.csv"
  assert component_json_path.is_file()
  assert component_csv_path.is_file()
  report = json.loads(component_json_path.read_text(encoding="utf-8"))
  assert report["summary"]["component_count"] == 26
  assert "component_name,bound_region_id" not in component_csv_path.read_text(
    encoding="utf-8"
  )
  assert "apg68_radar_array" in component_csv_path.read_text(encoding="utf-8")

  diagnostics_json_path = tmp_path / "review_point_diagnostics_20260611.json"
  diagnostics_csv_path = tmp_path / "review_point_diagnostics_20260611.csv"
  assert diagnostics_json_path.is_file()
  assert diagnostics_csv_path.is_file()
  diagnostics = json.loads(diagnostics_json_path.read_text(encoding="utf-8"))
  point_rows = {row["point_id"]: row for row in diagnostics["rows"]}
  assert point_rows["nose_axis_4m"]["nearest_outer_distance_m"] == 0.0
  assert "nose_axis_4m" in diagnostics_csv_path.read_text(encoding="utf-8")

  fine_proxy_path = tmp_path / "fine_geometry_proxy_candidate_20260611.json"
  assert fine_proxy_path.is_file()
  fine_proxy = json.loads(fine_proxy_path.read_text(encoding="utf-8"))
  assert fine_proxy["schema_version"] == "a2.target_geometry_fine_proxy_candidate.v1"
  assert fine_proxy["summary"]["proxy_count"] == len(mapping["outer_regions"])
  assert fine_proxy["summary"]["total_proxy_support_volume_ratio"] < 0.75
  assert fine_proxy["summary"]["mesh_derived_silhouette_count"] == 14
  assert fine_proxy["summary"]["inflated_fallback_count"] == 0
  assert result.stdout.find("fine_proxy_count") >= 0
  assert result.stdout.find("mesh_derived_silhouette_count") >= 0
  assert result.stdout.find("inflated_fallback_count") >= 0
  assert result.stdout.find("fine_proxy_support_volume_ratio") >= 0
  assert result.stdout.find("current_visual_result") >= 0
  assert result.stdout.find("fine_proxy_review_dashboard") == -1
  assert result.stdout.find("human_review_triage") == -1
  assert result.stdout.find("isolated_component_review_index") == -1
  assert result.stdout.find("isolated_component_review_manifest") == -1
  assert result.stdout.find("surface_component_count") >= 0
  assert result.stdout.find("semantic_damage_volume_count") >= 0
  assert result.stdout.find("semantic_damage_geometry_review_index") == -1
  assert result.stdout.find("internal_component_prior_count") >= 0
  assert result.stdout.find("internal_component_prior_review_index") == -1
  assert result.stdout.find("semantic_parent_child_layout_parent_count") >= 0
  assert result.stdout.find("semantic_parent_child_layout_review_index") == -1
  assert result.stdout.find("cross_region_ownership_split_json") >= 0
  assert result.stdout.find("cross_region_ownership_split_receiver_candidate_count") >= 0
  assert result.stdout.find("target_geometry_training_proxy_database") >= 0
  assert (
    result.stdout.find("target_geometry_training_proxy_database_component_count")
    >= 0
  )

  assert not stale_isolated_page.exists()
  for retired_path in (
    "component_review_views",
    "semantic_damage_geometry_views",
    "internal_component_prior_views",
    "semantic_parent_child_layout_views",
    "subcomponent_shape_placement_views",
    "fine_proxy_top.svg",
    "fine_proxy_side.svg",
    "fine_proxy_front.svg",
    "fine_proxy_review_dashboard.html",
    "human_review_triage.html",
  ):
    assert not (tmp_path / retired_path).exists()

  surface_json_path = tmp_path / "surface_component_candidate_20260611.json"
  surface_csv_path = tmp_path / "surface_component_candidate_20260611.csv"
  assert surface_json_path.is_file()
  assert surface_csv_path.is_file()
  surface_report = json.loads(surface_json_path.read_text(encoding="utf-8"))
  assert surface_report["schema_version"] == (
    "a2.target_geometry_surface_component_candidate.v1"
  )
  assert surface_report["summary"]["surface_component_count"] == 14
  assert "surface_left_wing_skin" in surface_csv_path.read_text(encoding="utf-8")
  assert "dedicated_intake_lip_or_duct_component" in surface_csv_path.read_text(
    encoding="utf-8"
  )

  semantic_json_path = tmp_path / "semantic_damage_geometry_candidate_20260611.json"
  semantic_csv_path = tmp_path / "semantic_damage_geometry_candidate_20260611.csv"
  assert semantic_json_path.is_file()
  assert semantic_csv_path.is_file()
  semantic_report = json.loads(semantic_json_path.read_text(encoding="utf-8"))
  assert semantic_report["schema_version"] == (
    "a2.target_geometry_semantic_damage_geometry_candidate.v1"
  )
  assert semantic_report["summary"]["semantic_volume_component_count"] == 14
  assert semantic_report["summary"]["runtime_parse_ready_component_count"] == 14
  assert semantic_report["summary"]["runtime_active_component_count"] == 0
  assert "semantic_left_wing_skin_volume" in semantic_csv_path.read_text(
    encoding="utf-8"
  )
  assert "direct_receivers_parse_ready_cross_region_receivers_held" in (
    semantic_csv_path.read_text(encoding="utf-8")
  )

  internal_prior_json_path = (
    tmp_path / "internal_component_prior_candidate_20260611.json"
  )
  internal_prior_csv_path = (
    tmp_path / "internal_component_prior_candidate_20260611.csv"
  )
  assert internal_prior_json_path.is_file()
  assert internal_prior_csv_path.is_file()
  internal_prior_report = json.loads(
    internal_prior_json_path.read_text(encoding="utf-8")
  )
  assert internal_prior_report["schema_version"] == (
    "a2.target_geometry_internal_component_prior_candidate.v1"
  )
  assert internal_prior_report["summary"]["internal_component_prior_count"] == 26
  assert internal_prior_report["summary"]["post_constraint_outside_count"] == 0
  assert internal_prior_report["summary"]["cross_region_held_prior_count"] == 2
  assert internal_prior_report["summary"]["shape_promotion_count"] == 9
  assert "left_wing_fuel_cell" in internal_prior_csv_path.read_text(
    encoding="utf-8"
  )
  assert "r18_promoted_from_subcomponent_shape_candidate" in (
    internal_prior_csv_path.read_text(encoding="utf-8")
  )
  assert "placed_inside_airframe_exceeds_parent_shell_review" in internal_prior_csv_path.read_text(
    encoding="utf-8"
  )
  assert "whole_airframe_source_region_union_bounds" in (
    internal_prior_csv_path.read_text(encoding="utf-8")
  )

  held_segment_json_path = (
    tmp_path / "cross_region_held_component_segments_20260611.json"
  )
  held_segment_csv_path = (
    tmp_path / "cross_region_held_component_segments_20260611.csv"
  )
  assert held_segment_json_path.is_file()
  assert held_segment_csv_path.is_file()
  held_segment_report = json.loads(
    held_segment_json_path.read_text(encoding="utf-8")
  )
  assert held_segment_report["schema_version"] == (
    "a2.target_geometry_cross_region_held_component_segments.v1"
  )
  assert held_segment_report["summary"]["held_segment_count"] == 8
  assert held_segment_report["summary"][
    "outside_whole_airframe_segment_count"
  ] == 0
  assert held_segment_report["summary"]["shape_promotion_segment_count"] == 5
  assert "wing_spar_center_carrythrough_segment" in (
    held_segment_csv_path.read_text(encoding="utf-8")
  )
  assert "engine_core_afterburner_segment" in held_segment_csv_path.read_text(
    encoding="utf-8"
  )
  assert "R18_promoted_R17_segmented_engine_afterburner_capsule" in (
    held_segment_csv_path.read_text(encoding="utf-8")
  )

  airframe_constraint_json_path = (
    tmp_path / "airframe_constraint_correction_candidate_20260611.json"
  )
  airframe_constraint_csv_path = (
    tmp_path / "airframe_constraint_correction_candidate_20260611.csv"
  )
  assert airframe_constraint_json_path.is_file()
  assert airframe_constraint_csv_path.is_file()
  airframe_constraint_report = json.loads(
    airframe_constraint_json_path.read_text(encoding="utf-8")
  )
  assert airframe_constraint_report["schema_version"] == (
    "a2.target_geometry_airframe_constraint_correction_candidate.v1"
  )
  assert airframe_constraint_report["summary"]["item_count"] == 34
  assert airframe_constraint_report["summary"][
    "silhouette_exposure_item_count"
  ] == 0
  assert "apg68_radar_array" in airframe_constraint_csv_path.read_text(
    encoding="utf-8"
  )
  assert "inside_airframe_cross_region_ownership_held" in (
    airframe_constraint_csv_path.read_text(encoding="utf-8")
  )

  ownership_split_json_path = (
    tmp_path / "cross_region_ownership_split_candidate_20260611.json"
  )
  ownership_split_csv_path = (
    tmp_path / "cross_region_ownership_split_candidate_20260611.csv"
  )
  assert ownership_split_json_path.is_file()
  assert ownership_split_csv_path.is_file()
  ownership_split_report = json.loads(
    ownership_split_json_path.read_text(encoding="utf-8")
  )
  assert ownership_split_report["schema_version"] == (
    "a2.target_geometry_cross_region_ownership_split_candidate.v1"
  )
  assert ownership_split_report["summary"]["split_receiver_candidate_count"] == 8
  assert ownership_split_report["summary"][
    "runtime_active_split_component_count"
  ] == 0
  ownership_split_csv = ownership_split_csv_path.read_text(encoding="utf-8")
  assert (
    "split_into_engine_section_receivers_and_keep_intake_duct_receiver_separate"
    in ownership_split_csv
  )
  assert "wing_spar_center_carrythrough_segment" in ownership_split_csv

  runtime_activation_json_path = (
    tmp_path / "target_geometry_runtime_activation_candidate_20260613.json"
  )
  runtime_activation_csv_path = (
    tmp_path / "target_geometry_runtime_activation_candidate_20260613.csv"
  )
  assert runtime_activation_json_path.is_file()
  assert runtime_activation_csv_path.is_file()
  runtime_activation_report = json.loads(
    runtime_activation_json_path.read_text(encoding="utf-8")
  )
  assert runtime_activation_report["schema_version"] == (
    "a2.target_geometry_runtime_activation_candidate.v1"
  )
  assert runtime_activation_report["summary"]["candidate_component_count"] == 8
  assert runtime_activation_report["summary"][
    "runtime_schema_parse_ready_component_count"
  ] == 8
  assert runtime_activation_report["summary"][
    "runtime_active_component_count"
  ] == 0
  assert len(runtime_activation_report["unit_database_patch_candidate"]["add"]) == 8
  assert runtime_activation_report["activation_policy"]["target_path"] == (
    "damage_model.hitboxes[].components"
  )
  assert runtime_activation_report["rows"][0]["unit_database_patch_path"] == (
    "damage_model.hitboxes[2].components"
  )
  runtime_activation_csv = runtime_activation_csv_path.read_text(encoding="utf-8")
  assert "parse_ready_existing_loader_fields" in runtime_activation_csv
  assert "A2_TARGET_GEOMETRY_PROXY_F16C_R22" in runtime_activation_csv
  assert "damage_model.hitboxes[2].components" in runtime_activation_csv

  runtime_behavior_json_path = (
    tmp_path / "target_geometry_runtime_behavior_regression_20260613.json"
  )
  runtime_behavior_csv_path = (
    tmp_path / "target_geometry_runtime_behavior_regression_20260613.csv"
  )
  assert runtime_behavior_json_path.is_file()
  assert runtime_behavior_csv_path.is_file()
  runtime_behavior_report = json.loads(
    runtime_behavior_json_path.read_text(encoding="utf-8")
  )
  assert runtime_behavior_report["schema_version"] == (
    "a2.target_geometry_runtime_behavior_regression.v1"
  )
  assert runtime_behavior_report["summary"]["base_component_count"] == 26
  assert runtime_behavior_report["summary"]["projected_component_count"] == 32
  assert runtime_behavior_report["summary"][
    "retired_parent_component_count"
  ] == 2
  assert runtime_behavior_report["summary"]["split_component_added_count"] == 8
  assert runtime_behavior_report["summary"]["duplicate_component_name_count"] == 0
  assert runtime_behavior_report["summary"]["behavior_regression_pass"] is True
  runtime_behavior_csv = runtime_behavior_csv_path.read_text(encoding="utf-8")
  assert "engine_core,2,damage_model.hitboxes[2].components" in (
    runtime_behavior_csv
  )
  assert "wing_spar_center,3,damage_model.hitboxes[3].components" in (
    runtime_behavior_csv
  )

  training_proxy_json_path = (
    tmp_path / "target_geometry_training_proxy_database_20260613.json"
  )
  training_proxy_database_dir = (
    tmp_path / "target_geometry_training_proxy_database_20260613"
  )
  training_proxy_unit_path = (
    training_proxy_database_dir / "aircraft" / "units" / "f16c_block50.json"
  )
  assert training_proxy_json_path.is_file()
  assert training_proxy_database_dir.is_dir()
  assert training_proxy_unit_path.is_file()
  training_proxy_report = json.loads(
    training_proxy_json_path.read_text(encoding="utf-8")
  )
  assert training_proxy_report["schema_version"] == (
    "a2.target_geometry_training_proxy_database.v1"
  )
  assert (
    training_proxy_report["runtime_database"]["proxy_f16c_unit_sha256"]
    and len(training_proxy_report["runtime_database"]["proxy_f16c_unit_sha256"])
    == 64
  )
  assert (
    training_proxy_report["summary"]["default_database_component_count"] == 26
  )
  assert training_proxy_report["summary"]["proxy_database_component_count"] == 32
  assert training_proxy_report["summary"]["split_receiver_component_count"] == 8
  assert training_proxy_report["summary"]["retired_parent_component_count"] == 2
  assert training_proxy_report["summary"]["duplicate_component_name_count"] == 0
  assert training_proxy_report["summary"]["behavior_regression_pass"] is True
  assert training_proxy_report["training_runtime_contract"][
    "training_path_wired"
  ] is True
  assert training_proxy_report["authority_boundary"]["training_path_wired"] is True
  proxy_unit = json.loads(training_proxy_unit_path.read_text(encoding="utf-8"))
  proxy_component_names = airframe_geometry_review._damage_component_names( # noqa: SLF001
    proxy_unit
  )
  default_component_names = airframe_geometry_review._damage_component_names( # noqa: SLF001
    airframe_geometry_review._load_json(airframe_geometry_review.DEFAULT_AIRCRAFT) # noqa: SLF001
  )
  assert len(default_component_names) == 26
  assert len(proxy_component_names) == 32
  assert "engine_core" in default_component_names
  assert "wing_spar_center" in default_component_names
  assert "engine_core" not in proxy_component_names
  assert "wing_spar_center" not in proxy_component_names
  assert "engine_core_afterburner_segment" in proxy_component_names
  assert "wing_spar_center_carrythrough_segment" in proxy_component_names

  shape_placement_json_path = (
    tmp_path / "subcomponent_shape_placement_candidate_20260611.json"
  )
  shape_placement_csv_path = (
    tmp_path / "subcomponent_shape_placement_candidate_20260611.csv"
  )
  assert shape_placement_json_path.is_file()
  assert shape_placement_csv_path.is_file()
  shape_placement_report = json.loads(
    shape_placement_json_path.read_text(encoding="utf-8")
  )
  assert shape_placement_report["schema_version"] == (
    "a2.target_geometry_subcomponent_shape_placement_candidate.v1"
  )
  # The R22 thin-prism/frustum shape updates clear the source exposure queue,
  # so shape placement has no rows to process.
  assert shape_placement_report["summary"][
    "shape_placement_candidate_count"
  ] == 0
  assert shape_placement_report["summary"][
    "source_silhouette_exposure_item_count"
  ] == 0
  assert (
    shape_placement_report["summary"]["candidate_resolves_exposure_count"]
    + shape_placement_report["summary"]["candidate_unresolved_exposure_count"]
    == 0
  )
  assert shape_placement_report["summary"][
    "candidate_total_outside_sample_reduction"
  ] >= 0
  assert (
    shape_placement_report["summary"]["centerline_candidate_resolves_exposure_count"]
    + shape_placement_report["summary"][
      "centerline_candidate_unresolved_exposure_count"
    ]
    == 0
  )
  assert shape_placement_report["summary"][
    "centerline_candidate_total_outside_sample_count"
  ] >= 0
  assert (
    shape_placement_report["summary"]["latest_candidate_resolves_exposure_count"]
    + shape_placement_report["summary"]["latest_candidate_unresolved_exposure_count"]
    == 0
  )
  assert shape_placement_report["summary"][
    "latest_candidate_total_outside_sample_count"
  ] >= 0
  assert len(shape_placement_report["rows"]) == 0
  shape_placement_csv_text = shape_placement_csv_path.read_text(encoding="utf-8")
  # Previously exposed receivers are now cleared and absent from the
  # shape-placement rows.
  for item_id in (
    "left_wing_fuel_cell",
    "right_wing_fuel_cell",
    "wing_spar_center",
  ):
    assert item_id not in shape_placement_csv_text
  # Receivers that stay inside the contour are not shape-placement rows.
  assert "apg68_radar_array" not in shape_placement_csv_text
  assert "afterburner_nozzle" not in shape_placement_csv_text
  assert "engine_core" not in shape_placement_csv_text
  assert "cockpit_crew_station" not in shape_placement_csv_text
  assert "inertial_navigation_unit" not in shape_placement_csv_text

  parent_child_json_path = (
    tmp_path / "semantic_parent_child_layout_candidate_20260611.json"
  )
  parent_child_csv_path = (
    tmp_path / "semantic_parent_child_layout_candidate_20260611.csv"
  )
  assert parent_child_json_path.is_file()
  assert parent_child_csv_path.is_file()
  parent_child_report = json.loads(
    parent_child_json_path.read_text(encoding="utf-8")
  )
  assert parent_child_report["schema_version"] == (
    "a2.target_geometry_semantic_parent_child_layout_candidate.v1"
  )
  assert parent_child_report["summary"]["parent_semantic_component_count"] == 14
  assert parent_child_report["summary"]["bound_receiver_component_count"] == 26
  assert parent_child_report["summary"]["extra_receiver_slot_count"] == 12
  assert parent_child_report["summary"]["cross_region_held_segment_count"] == 8
  assert parent_child_report["summary"][
    "cross_region_held_segment_overlay_count"
  ] == 5
  assert "semantic_left_wing_skin_volume" in parent_child_csv_path.read_text(
    encoding="utf-8"
  )
  assert "segments=5" in parent_child_csv_path.read_text(encoding="utf-8")

  for retired_view_dir in (
    "semantic_damage_geometry_views",
    "internal_component_prior_views",
    "semantic_parent_child_layout_views",
    "subcomponent_shape_placement_views",
  ):
    assert not (tmp_path / retired_view_dir).exists()

  scene_path = tmp_path / "scene.html"
  assert scene_path.is_file()
  scene = scene_path.read_text(encoding="utf-8")
  assert "F-16 Final Geometry Contour Result" in scene
  assert "Current final visual result only" in scene
  assert "fine_proxy_review_dashboard.html" not in scene
  assert "human_review_triage.html" not in scene
  assert "component_review_views/index.html" not in scene
  assert "Fine Geometry Proxy Overlay" not in scene
  assert "Surface Component Candidates" not in scene
  assert "Semantic Damage Geometry Volumes" not in scene
  assert "semantic_damage_geometry_views/index.html" not in scene
  assert "Internal Component Prior Geometry" not in scene
  assert "internal_component_prior_views/index.html" not in scene
  assert "Cross-Region Held Split Segments" not in scene
  assert "Airframe Constraint Correction Candidates" not in scene
  assert "Cross-Region Ownership Split Candidates" not in scene
  assert "TG-P7 Runtime Activation Candidate" not in scene
  assert "TG-P7 Runtime Behavior Regression Candidate" not in scene
  assert "TG-P7 Training Proxy Database" not in scene
  assert "Subcomponent Shape Placement Candidates" not in scene
  assert "subcomponent_shape_placement_views/index.html" not in scene
  assert "Semantic Parent-Child Component Layout" not in scene
  assert "semantic_parent_child_layout_views/index.html" not in scene
  assert "Whole-Airframe Projected Mesh Contour Containment" in scene
  assert "whole_airframe_contour_dashboard.html" in scene
  assert "whole_airframe_contour_top.svg" in scene
  assert "projecting triangle faces" in scene
  assert "engineering review margin" in scene


def test_alpha_shape_2d_preserves_concavities_and_degrades_gracefully() -> None:
  """The whole-airframe contour builder must keep real concavities (the whole
  point of choosing alpha-shape over convex hull) and must fall back to the
  convex hull when there are too few points or no triangle survives the
  circumradius filter."""
  import math

  # A dense "dumbbell": two disks joined by a narrow neck. A convex hull
  # would span both disks as a single blob; an alpha-shape should carve the
  # neck concavity and produce more boundary points than the convex hull.
  dumbbell: list[tuple[float, float]] = []
  for cx in (-4.0, 4.0):
    for i in range(64):
      angle = i / 64.0 * 2.0 * math.pi
      dumbbell.append((cx + 2.5 * math.cos(angle), 2.5 * math.sin(angle)))
  alpha = 1.0 / (13.0 * 0.35)
  ring, status = airframe_geometry_review._alpha_shape_2d(dumbbell, alpha)
  assert status == "alpha_shape"
  convex = airframe_geometry_review._convex_hull_2d(dumbbell)
  # The alpha-shape must keep strictly more boundary detail than the convex
  # hull (the hull collapses the neck).
  assert len(ring) > len(convex)

  # Too few points => graceful convex-hull fallback, never an exception.
  ring_few, status_few = airframe_geometry_review._alpha_shape_2d(
    [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)], alpha
  )
  assert status_few == "convex_hull"
  assert len(ring_few) >= 3

  # Empty input is rejected by the whole-airframe builder, not by the
  # alpha-shape helper (which returns an empty hull).
  ring_empty, status_empty = airframe_geometry_review._alpha_shape_2d(
    [], alpha
  )
  assert status_empty == "convex_hull"
  assert ring_empty == []


def test_whole_airframe_contour_report_structure() -> None:
  """The whole-airframe contour containment report records the contour method,
  tolerance, per-view contour metadata, and per-item outside distances built
  on top of the airframe constraint report."""
  manifest = airframe_geometry_review.build_airframe_geometry_manifest()
  aircraft = airframe_geometry_review._load_json(  # noqa: SLF001
    airframe_geometry_review.DEFAULT_AIRCRAFT
  )
  mapping = airframe_geometry_review.build_geometry_mapping_candidate(manifest)
  report = airframe_geometry_review.build_component_binding_report(
    aircraft, mapping
  )
  diagnostics = airframe_geometry_review.build_review_point_diagnostics(
    mapping, report
  )
  fine_proxy = airframe_geometry_review.build_fine_geometry_proxy_candidate(
    mapping, diagnostics, manifest=manifest
  )
  surface_report = (
    airframe_geometry_review.build_surface_component_candidate_report(
      mapping, fine_proxy, report
    )
  )
  semantic_report = (
    airframe_geometry_review.build_semantic_damage_geometry_candidate(
      mapping, fine_proxy, surface_report
    )
  )
  internal_prior_report = (
    airframe_geometry_review.build_internal_component_prior_candidate(
      mapping, fine_proxy, report, surface_report
    )
  )
  held_segment_report = (
    airframe_geometry_review.build_cross_region_held_component_segments_report(
      mapping, fine_proxy, internal_prior_report
    )
  )
  airframe_constraint_report = (
    airframe_geometry_review.build_airframe_constraint_correction_candidate_report(
      mapping, fine_proxy, internal_prior_report, held_segment_report
    )
  )
  contour_report = (
    airframe_geometry_review.build_whole_airframe_contour_containment_report(
      fine_proxy, airframe_constraint_report
    )
  )
  assert contour_report["schema_version"] == (
    "a2.target_geometry_whole_airframe_contour_containment.v1"
  )
  assert contour_report["contour_method"] == "projected_mesh_triangle_union"
  assert contour_report["tolerance_m"] == 0.05
  assert contour_report["summary"]["item_count"] == 26
  assert contour_report["summary"]["excluded_review_only_split_segment_count"] == 8
  # Shape-aware thin-prism/frustum receiver projections now fit inside the
  # projected mesh contour. Review-only split segments are still excluded from
  # this final-result surface.
  assert contour_report["summary"]["exceeds_tolerance_item_count"] == 0
  assert contour_report["summary"]["exceeding_item_ids"] == []
  assert contour_report["summary"]["max_outside_distance_m"] == 0.0
  # Every view produced a triangle-union contour from the audit mesh.
  for view in ("top", "side", "front"):
    meta = contour_report["summary"]["contours"][view]
    assert meta["status"] == "projected_mesh_triangle_union"
    assert meta["source_triangle_count"] == 4504
    assert meta["polygon_count"] == 1
    assert meta["contour_point_count"] >= 100
    assert len(contour_report["contours"][view]["points_m"]) == meta[
      "contour_point_count"
    ]
  # The rows stay deterministic even with no exceeders.
  row_ids = [row["item_id"] for row in contour_report["rows"]]
  assert row_ids[0] == "afterburner_nozzle"
  exceeder_ids = {
    row["item_id"] for row in contour_report["rows"] if row["exceeds_tolerance"]
  }
  assert exceeder_ids == set()
  assert "engine_core_afterburner_segment" not in row_ids
  assert contour_report["authority_boundary"][
    "projected_mesh_contour_diagnostic_only"
  ] is True
  assert contour_report["authority_boundary"][
    "tolerance_is_engineering_review_margin_not_physical_clearance"
  ] is True


def test_geometry_optional_dependencies_advertised() -> None:
  """The geometry dependency group must be declared so contour diagnostics are
  installable from a fresh checkout."""
  pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
  assert 'geometry = [' in pyproject
  assert '"scipy"' in pyproject
  assert '"shapely"' in pyproject
