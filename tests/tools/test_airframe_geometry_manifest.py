from __future__ import annotations

from typing import Any

import pytest

from tools.geometry.airframe_review import component_model
from tests.tools.airframe_review_fixtures import (
  build_airframe_review_bundle,
  require_airframe_geometry_extra,
)


ReviewBundle = dict[str, Any]


@pytest.fixture(scope="module")
def airframe_review_bundle() -> ReviewBundle:
  require_airframe_geometry_extra()
  return build_airframe_review_bundle()


def test_f16_geometry_manifest_records_source_axis_and_damage_bounds(
  airframe_review_bundle: ReviewBundle,
) -> None:
  manifest = airframe_review_bundle["manifest"]

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
  assert -60.0 < damage_geometry["public_dimension_error_percent"]["height_m"] < -50.0
  assert manifest["authority_boundary"]["runtime_collision_mesh"] is False
  assert manifest["authority_boundary"]["real_weapon_pk_authority"] is False


def test_f16_component_binding_report_tracks_review_states(
  airframe_review_bundle: ReviewBundle,
) -> None:
  report = airframe_review_bundle["component_binding_report"]

  assert report["schema_version"] == "a2.target_geometry_component_binding_report.v1"
  assert report["status"] == "component_binding_report_generated_review_only"
  assert report["summary"]["component_count"] == 26
  assert report["summary"]["bound_component_count"] == 19
  assert report["summary"]["needs_review_count"] == 7
  assert report["summary"]["side_sign_review_count"] == 0
  assert report["summary"]["hard_blocker_count"] == 0
  assert report["summary"]["cross_region_semantic_candidate_count"] == 2
  assert report["summary"]["geometry_review_required_count"] == 7
  assert report["summary"]["review_status"] == "manual_review_required"
  rows = {row["component_name"]: row for row in report["rows"]}
  assert rows["apg68_radar_array"]["bound_region_id"] == "nose_radome"
  assert rows["apg68_radar_array"]["review_status"] == "needs_review"
  assert rows["apg68_radar_array"]["review_semantics"] == "geometry_review_required"
  assert "no_outer_region_overlap" in rows["apg68_radar_array"]["anomalies"]
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
  assert rows["dedicated_intake_lip_or_duct_component"]["bound_region_id"] == (
    "forward_fuselage"
  )
  assert rows["left_horizontal_tail_actuator_or_surface_component"][
    "bound_region_id"
  ] == "left_horizontal_tail"
  assert rows["right_horizontal_tail_actuator_or_surface_component"][
    "bound_region_id"
  ] == "right_horizontal_tail"
  assert rows["left_wing_fuel_cell"]["bound_region_id"] == "left_wing"
  assert rows["right_wing_fuel_cell"]["bound_region_id"] == "right_wing"
  assert rows["left_wing_fuel_cell"]["review_status"] == "needs_review"
  assert rows["right_wing_fuel_cell"]["review_status"] == "needs_review"
  assert "no_outer_region_overlap" in rows["left_wing_fuel_cell"]["anomalies"]
  assert "no_outer_region_overlap" in rows["right_wing_fuel_cell"]["anomalies"]
  assert rows["left_wing_fuel_cell"]["side_sign_relation"][
    "side_sign_mismatch"
  ] is False


def test_f16_review_point_diagnostics_keep_axis_landmarks(
  airframe_review_bundle: ReviewBundle,
) -> None:
  diagnostics = airframe_review_bundle["diagnostics"]

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


def test_f16_fine_proxy_candidates_preserve_mesh_silhouettes(
  airframe_review_bundle: ReviewBundle,
) -> None:
  fine_proxy = airframe_review_bundle["fine_proxy"]

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


def test_f16_surface_component_candidates_keep_runtime_boundaries(
  airframe_review_bundle: ReviewBundle,
) -> None:
  surface_report = airframe_review_bundle["surface_report"]

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
  assert surface_report["summary"]["cross_region_semantic_hold_count"] == 4
  assert surface_report["summary"]["needs_review_count"] == 5
  assert surface_report["summary"]["review_status"] == "manual_review_required"
  surface_rows = {
    row["surface_component_id"]: row for row in surface_report["rows"]
  }
  nose_surface = surface_rows["surface_nose_radome"]
  assert nose_surface["source_region_id"] == "nose_radome"
  assert nose_surface["review_status"] == "needs_human_review"
  assert nose_surface["review_semantics"] == "linked_component_geometry_needs_review"
  assert "linked_component_needs_review" in nose_surface["review_flags"]
  assert nose_surface["clean_direct_component_names"] == ["iff_interrogator"]
  assert {
    link["component_name"] for link in nose_surface["linked_internal_components"]
  } >= {"apg68_radar_array", "iff_interrogator"}
  left_wing_surface = surface_rows["surface_left_wing_skin"]
  assert "surface_area_loss" in left_wing_surface["expected_damage_modes"]
  assert "side_sign_review" not in left_wing_surface["review_flags"]
  assert left_wing_surface["review_status"] == "needs_human_review"
  assert left_wing_surface["review_semantics"] == "linked_component_geometry_needs_review"
  assert "linked_component_needs_review" in left_wing_surface["review_flags"]
  assert {
    link["component_name"] for link in left_wing_surface["linked_internal_components"]
  } >= {"left_wing_fuel_cell", "left_aileron_actuator", "wing_spar_center"}
  assert left_wing_surface["clean_direct_component_names"] == []
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
  assert forward_surface["clean_direct_link_count"] == 4
  intake_surface = surface_rows["surface_intake_lip_and_duct"]
  assert intake_surface["review_semantics"] == (
    "cross_region_boundary_candidate_review_only"
  )
  assert intake_surface["runtime_relation_status"] == (
    "runtime_relation_review_only_candidate"
  )
  assert intake_surface["missing_existing_runtime_component_relations"] == []
  assert intake_surface["clean_direct_component_names"] == []
  assert "expected_component_bound_elsewhere" in intake_surface["review_flags"]
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


def test_f16_semantic_damage_geometry_candidates_stay_parse_ready_only(
  airframe_review_bundle: ReviewBundle,
) -> None:
  semantic_report = airframe_review_bundle["semantic_report"]

  assert semantic_report["schema_version"] == (
    "a2.target_geometry_semantic_damage_geometry_candidate.v1"
  )
  assert semantic_report["status"] == (
    "semantic_damage_geometry_candidate_generated_review_only"
  )
  assert semantic_report["summary"]["semantic_volume_component_count"] == 14
  assert semantic_report["summary"]["runtime_parse_ready_component_count"] == 14
  assert semantic_report["summary"]["runtime_active_component_count"] == 0
  assert semantic_report["summary"]["cross_region_handoff_held_count"] == 4
  assert semantic_report["summary"]["blocked_receiver_count"] == 0
  assert semantic_report["summary"]["bad_geometry_receiver_count"] == 11
  assert semantic_report["summary"]["review_status"] == "manual_review_required_before_activation"
  assert semantic_report["summary"]["geometry_primitive_counts"]["thin_prism"] >= 5
  assert semantic_report["summary"]["geometry_primitive_counts"]["convex_hull"] >= 4
  semantic_rows = {
    row["semantic_component_id"]: row for row in semantic_report["rows"]
  }
  nose_volume = semantic_rows["semantic_nose_radome_volume"]
  assert nose_volume["source_region_id"] == "nose_radome"
  assert nose_volume["geometry_primitive"] == "convex_hull"
  assert nose_volume["direct_receiver_components"] == ["iff_interrogator"]
  assert nose_volume["cross_region_receiver_components"] == []
  assert nose_volume["receiver_handoff_status"] == "blocked_receiver_review_required"
  assert nose_volume["runtime_component_json_candidate"]["geometry_primitive"] == (
    "convex_hull"
  )
  assert nose_volume["runtime_component_json_candidate"]["geometry"][
    "surface_component_id"
  ] == "surface_nose_radome"
  assert len(nose_volume["runtime_geometry"]["vertices_m"]) >= 7
  left_wing_volume = semantic_rows["semantic_left_wing_skin_volume"]
  assert left_wing_volume["geometry_primitive"] == "thin_prism"
  assert left_wing_volume["direct_receiver_components"] == []
  assert left_wing_volume["cross_region_receiver_components"] == [
    "wing_spar_center"
  ]
  assert left_wing_volume["receiver_handoff_status"] == "blocked_receiver_review_required"
  assert semantic_report["authority_boundary"][
    "runtime_schema_parse_ready_candidate"
  ] is True
  assert semantic_report["authority_boundary"]["runtime_active_component"] is False


def test_f16_internal_component_prior_summary_preserves_review_boundaries(
  airframe_review_bundle: ReviewBundle,
) -> None:
  internal_prior_report = airframe_review_bundle["internal_prior_report"]

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
  assert internal_prior_report["summary"]["parent_shell_exceed_review_count"] == 12
  assert internal_prior_report["summary"]["cross_region_held_prior_count"] == 2
  assert internal_prior_report["summary"]["review_status"] == "manual_review_required_before_activation"
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


def test_f16_internal_component_prior_promotes_avionics_shapes(
  airframe_review_bundle: ReviewBundle,
) -> None:
  internal_prior_report = airframe_review_bundle["internal_prior_report"]

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


def test_f16_internal_component_prior_constrains_engine_spar_and_fuel(
  airframe_review_bundle: ReviewBundle,
) -> None:
  internal_prior_report = airframe_review_bundle["internal_prior_report"]
  prior_rows = {
    row["component_name"]: row for row in internal_prior_report["rows"]
  }

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


def test_f16_held_cross_region_segments_stay_inside_airframe_bounds(
  airframe_review_bundle: ReviewBundle,
) -> None:
  held_segment_report = airframe_review_bundle["held_segment_report"]

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


def test_f16_airframe_constraint_corrections_clear_silhouette_exposure(
  airframe_review_bundle: ReviewBundle,
) -> None:
  airframe_constraint_report = airframe_review_bundle["airframe_constraint_report"]

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


def test_f16_cross_region_ownership_split_candidates_retire_parents(
  airframe_review_bundle: ReviewBundle,
) -> None:
  ownership_split_report = airframe_review_bundle["ownership_split_report"]
  held_segment_report = airframe_review_bundle["held_segment_report"]
  segment_rows = {
    row["segment_id"]: row for row in held_segment_report["rows"]
  }
  afterburner_segment = segment_rows["engine_core_afterburner_segment"]

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


def test_f16_runtime_activation_candidate_remains_feature_flagged(
  airframe_review_bundle: ReviewBundle,
) -> None:
  runtime_activation_report = airframe_review_bundle["runtime_activation_report"]
  ownership_split_report = airframe_review_bundle["ownership_split_report"]
  ownership_rows = {
    row["parent_component_name"]: row for row in ownership_split_report["rows"]
  }
  engine_ownership = ownership_rows["engine_core"]
  engine_candidates = {
    candidate["name"]: candidate
    for entry in engine_ownership["segment_entries"]
    for candidate in [entry["runtime_component_json_candidate"]]
  }
  afterburner_candidate = engine_candidates["engine_core_afterburner_segment"]

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


def test_f16_runtime_behavior_projection_replaces_cross_region_parents(
  airframe_review_bundle: ReviewBundle,
) -> None:
  runtime_behavior_report = airframe_review_bundle["runtime_behavior_report"]

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


def test_f16_training_proxy_database_materializes_split_receivers(
  airframe_review_bundle: ReviewBundle,
) -> None:
  training_proxy_aircraft = airframe_review_bundle["training_proxy_aircraft"]
  training_proxy_operations = airframe_review_bundle["training_proxy_operations"]
  training_proxy_report = airframe_review_bundle["training_proxy_report"]

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
  proxy_component_names = component_model.damage_component_names(
    training_proxy_aircraft
  )
  assert len(proxy_component_names) == 32
  assert "engine_core" not in proxy_component_names
  assert "wing_spar_center" not in proxy_component_names
  assert "engine_core_afterburner_segment" in proxy_component_names
  assert "wing_spar_center_carrythrough_segment" in proxy_component_names
  assert len(training_proxy_operations) == 10


def test_f16_shape_placement_queue_is_empty_after_promoted_geometry_rules(
  airframe_review_bundle: ReviewBundle,
) -> None:
  shape_placement_report = airframe_review_bundle["shape_placement_report"]

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


def test_f16_parent_child_layout_retains_receiver_overlay_boundaries(
  airframe_review_bundle: ReviewBundle,
) -> None:
  parent_child_layout_report = airframe_review_bundle["parent_child_layout_report"]

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
  assert parent_child_layout_report["summary"]["extra_receiver_slot_count"] == 13
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
  assert parent_child_layout_report["summary"]["review_status"] == (
    "manual_review_required_before_activation"
  )
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
